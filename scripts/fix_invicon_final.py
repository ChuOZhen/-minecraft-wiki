#!/usr/bin/env python3
"""fix_invicon_final.py — 最终 Invicon_ 清理：映射 + 从URL提取 + 降级"""
import json, re, os

DATA_PATH = 'docs/data/data.json'
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']
img_dir = 'docs/images'
existing_imgs = set(os.listdir(img_dir))

# Build ALL possible mappings
id_to_icon = {}
for i in items:
    icon = i.get('icon_url','')
    if icon.startswith('images/'):
        iid = i['id']
        id_to_icon[iid] = icon
        # Normalized versions
        id_to_icon[iid.replace('_','')] = icon
        id_to_icon[iid.lower()] = icon

# Comprehensive invicon_name → item_id mapping
INV_MAP = {}
for i in items:
    iid = i['id']
    INV_MAP[iid.lower()] = iid
    INV_MAP[iid.replace('_','')] = iid

# Add reverse mappings using known patterns
REVERSE = {}
for i in items:
    iid = i['id']
    # X_block → block_of_X
    if iid.endswith('_block') and not iid.startswith('block_of_'):
        base = iid[:-6]
        REVERSE[f'block_of_{base}'] = iid
    # stripped_X_log → X_stripped_log
    for pfx in ['stripped_']:
        if iid.startswith(pfx):
            rest = iid[len(pfx):]
            REVERSE[rest] = iid
    # X_planks → X_planks (identity)
    REVERSE[iid.lower().replace('_','')] = iid

INV_MAP.update(REVERSE)

# Known manual mappings
MANUAL = {
    'allium': 'allium', 'bamboo': 'bamboo', 'cactus': 'cactus',
    'clay': 'clay', 'dandelion': 'dandelion', 'glowstone': 'glowstone',
    'lilac': 'lilac', 'melon': 'melon', 'netherrack': 'netherrack',
    'pumpkin': 'pumpkin', 'snow': 'snow', 'sponge': 'sponge',
    'terracotta': 'terracotta', 'sugar_cane': 'sugar_cane',
    'vines': 'vine', 'moss_carpet': 'moss_carpet',
    'pale_moss_carpet': 'pale_moss_carpet',
    'rose_bush': 'rose_bush', 'blue_orchid': 'blue_orchid',
    'orange_tulip': 'orange_tulip', 'pink_tulip': 'pink_tulip',
    'red_tulip': 'red_tulip', 'white_tulip': 'white_tulip',
    'oxeye_daisy': 'oxeye_daisy',
    'sea_lantern': 'sea_lantern', 'soul_sand': 'soul_sand',
    'soul_soil': 'soul_soil',
    'closed_eyeblossom': 'closed_eyeblossom',
    'open_eyeblossom': 'open_eyeblossom',
    'mangrove_roots': 'mangrove_roots',
    'muddy_mangrove_roots': 'muddy_mangrove_roots',
    'red_mushroom': 'red_mushroom', 'brown_mushroom': 'brown_mushroom',
    'popped_chorus_fruit': 'popped_chorus_fruit',
    'jack_o_lantern': 'jack_o_lantern',
    'white_shield': 'shield',
    'player_head': 'player_head', 'ominous_shield': 'shield',
    'netherite_horse_armor': 'netherite_horse_armor',
    'coal_block': 'coal_block',
    'polished_cinnabar_stairs': None,
    'polished_sulfur': None, 'sulfur': None, 'sulfur_bricks': None, 'sulfur_%28element%29': None,
    'cinnabar': None, 'cinnabar_bricks': None,
    'copper_axe': None, 'copper_sword': None, 'copper_hoe': None,
    'copper_pickaxe': None, 'copper_shovel': None,
    'copper_helmet': None, 'copper_boots': None,
    'copper_nautilus_armor': None, 'diamond_nautilus_armor': None,
    'netherite_nautilus_armor': None,
    'hay_bale': 'hay_block',
    'muudy_mangrove_roots': 'muddy_mangrove_roots',
}

for k, v in MANUAL.items():
    if v:
        INV_MAP[k.lower()] = v
    elif k.lower() in INV_MAP:
        pass  # already mapped

def norm(s):
    return s.lower().replace(' ','_').replace('-','_').replace('(','').replace(')','').replace('%28','').replace('%29','')

def fix_url(url):
    if not url or 'Invicon_' not in url: return url, False
    m = re.search(r'Invicon_(.+?)\.(?:png|PNG|gif)', url)
    if not m: return url, False

    inv_name = m.group(1)
    inv_norm = norm(inv_name)

    # 1. Try direct mapping
    item_id = INV_MAP.get(inv_norm)

    # 2. Try block_of_X → X_block
    if not item_id and inv_norm.startswith('block_of_'):
        mat = inv_norm[9:]
        item_id = INV_MAP.get(mat + '_block') or INV_MAP.get(mat)

    # 3. Try stripped_X_log → X_stripped_log
    if not item_id and inv_norm.startswith('stripped_'):
        rest = inv_norm[9:]
        item_id = INV_MAP.get(rest + '_stripped_log') or INV_MAP.get(rest + '_stripped_wood')

    # 4. Try Minecart_with_X → X_minecart
    if not item_id and inv_norm.startswith('minecart_with_'):
        x = inv_norm[14:]
        item_id = INV_MAP.get(x + '_minecart')

    # 5. Try smooth_X_slab → smooth_X_slab
    if not item_id and 'smooth' in inv_norm:
        item_id = INV_MAP.get(inv_norm.replace('_slab',''))
        if not item_id:
            item_id = INV_MAP.get(inv_norm)

    # 6. Try mossy_X_slab
    if not item_id and inv_norm.startswith('mossy_'):
        item_id = INV_MAP.get(inv_norm)

    # 7. Try netherrack → netherrack
    if not item_id:
        # Try as-is in lower case
        for i in items:
            if i['id'].lower().replace('_','') == inv_norm.replace('_',''):
                item_id = i['id']
                break

    if not item_id:
        return url, False

    # Look up local icon
    icon = id_to_icon.get(item_id) or id_to_icon.get(item_id.lower())
    if icon:
        return icon, True

    # Check if image exists
    fname = f'{item_id}.png'
    if fname in existing_imgs:
        return f'images/{fname}', True

    return url, False

# APPLY
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
        for ik in ['input_icon','output_icon']:
            new, ch = fix_url(sc.get(ik, ''))
            if ch: sc[ik] = new; total += 1
    for sm in (item.get('smithing') or []):
        if not isinstance(sm, dict): continue
        for ik in ['template_icon','base_icon','addition_icon','output_icon']:
            new, ch = fix_url(sm.get(ik, ''))
            if ch: sm[ik] = new; total += 1
    for sm in (item.get('acquisition',{}).get('smelting') or []):
        if not isinstance(sm, dict): continue
        for ik in ['input_icon','output_icon']:
            new, ch = fix_url(sm.get(ik, ''))
            if ch: sm[ik] = new; total += 1

raw = json.dumps(data, ensure_ascii=False)
inv_left = raw.count('Invicon_')
print(f"Fixed: {total}")
print(f"Remaining Invicon_: {inv_left}")

# Show remaining unique
if inv_left > 0:
    uniq = set()
    for m in re.finditer(r'Invicon_(.+?)\.(?:png|PNG|gif)', raw):
        uniq.add(m.group(1))
    print(f"Unique remaining: {len(uniq)}")
    for s in sorted(uniq)[:20]:
        print(f"  {s}")

data['meta']['generated_at'] = '2026-05-05-b4.2-final'
with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Done.")
