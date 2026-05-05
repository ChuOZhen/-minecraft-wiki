#!/usr/bin/env python3
"""fix_invicon_r3.py — R3: 全量 Invicon_ CDN URL → 本地路径"""
import json, re, os

DATA_PATH = 'docs/data/data.json'
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']
img_dir = 'docs/images'
existing_imgs = set(os.listdir(img_dir))

# Build invicon → item_id mapping from all item data
def norm(s):
    return s.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')

inv_to_item = {}
for i in items:
    iid = i['id']
    inv_to_item[norm(iid)] = iid
    inv_to_item[norm(i.get('name_en', ''))] = iid
    if iid.endswith('_block'):
        base = iid[:-6]
        inv_to_item[f'block_of_{base}'] = iid

# Read all remaining Invicon_ IDs from data and try to match
raw = json.dumps(data, ensure_ascii=False)
all_invicons = set()
for m in re.finditer(r'Invicon_(.+?)\.(?:png|PNG)', raw):
    all_invicons.add(m.group(1))

print(f"Unique Invicon_ names: {len(all_invicons)}")

# For each unmatched, try to find matching item by fuzzy match
item_ids_set = {i['id'] for i in items}
item_names = {norm(i.get('name_en', '')): i['id'] for i in items}

for inv_name in sorted(all_invicons):
    inv_norm = norm(inv_name)
    if inv_norm in inv_to_item:
        continue  # already mapped

    # Fuzzy match
    # 1. Try as direct item ID
    if inv_norm in item_ids_set:
        inv_to_item[inv_norm] = inv_norm
        continue

    # 2. Try block_of_X → X_block
    if inv_norm.startswith('block_of_'):
        material = inv_norm[9:]
        block_id = material + '_block'
        if block_id in item_ids_set:
            inv_to_item[inv_norm] = block_id
            continue

    # 3. Try without suffixes
    for suffix in ['_block', '_item', '_spawn_egg', '_bucket']:
        if inv_norm.endswith(suffix):
            base = inv_norm[:-len(suffix)]
            if base in inv_to_item:
                inv_to_item[inv_norm] = inv_to_item[base]
                break

    # 4. Try bamboo variants
    if inv_norm.startswith('bamboo') and inv_norm != 'bamboo':
        if 'bamboo' in inv_to_item:
            inv_to_item[inv_norm] = inv_to_item['bamboo']

unmapped = sum(1 for inv in all_invicons if norm(inv) not in inv_to_item)
print(f"Mapped: {len(all_invicons) - unmapped}, Unmapped: {unmapped}")

# Show unmapped
for inv in sorted(all_invicons):
    if norm(inv) not in inv_to_item:
        print(f"  UNMAPPED: {inv}")

# Now fix all URLs
def fix_url(url):
    if not url or 'Invicon_' not in url: return url, False
    m = re.search(r'Invicon_(.+?)\.(?:png|PNG)', url)
    if not m: return url, False

    inv_name = m.group(1)
    item_id = inv_to_item.get(norm(inv_name))

    if not item_id:
        return url, False

    for i in items:
        if i['id'] == item_id:
            icon = i.get('icon_url', '')
            if icon.startswith('images/'):
                return icon, True
            break

    return url, False

total = 0
for item in items:
    for craft in item.get('crafting', []):
        for ing in craft.get('ingredients', {}).values():
            if isinstance(ing, dict):
                new, ch = fix_url(ing.get('icon_url', ''))
                if ch: ing['icon_url'] = new; total += 1
        new, ch = fix_url(craft.get('result_icon', ''))
        if ch: craft['result_icon'] = new; total += 1
    for sc in (item.get('stonecutting') or []):
        if not isinstance(sc, dict): continue
        for ik in ['input_icon', 'output_icon']:
            new, ch = fix_url(sc.get(ik, ''))
            if ch: sc[ik] = new; total += 1
    for sm in (item.get('smithing') or []):
        if not isinstance(sm, dict): continue
        for ik in ['template_icon', 'base_icon', 'addition_icon', 'output_icon']:
            new, ch = fix_url(sm.get(ik, ''))
            if ch: sm[ik] = new; total += 1
    for sm in (item.get('acquisition', {}).get('smelting') or []):
        if not isinstance(sm, dict): continue
        for ik in ['input_icon', 'output_icon']:
            new, ch = fix_url(sm.get(ik, ''))
            if ch: sm[ik] = new; total += 1

raw2 = json.dumps(data, ensure_ascii=False)
inv_left = raw2.count('Invicon_')
print(f"\nFixed: {total}")
print(f"Remaining Invicon_: {inv_left}")

data['meta']['generated_at'] = '2026-05-05-b4.2-r3'
with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Done.")
