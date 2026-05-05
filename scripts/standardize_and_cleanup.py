#!/usr/bin/env python3
"""
standardize_and_cleanup.py — 标准化中文名/分类 + 图片匹配 + 清理冗余
"""
import json, os, re, shutil
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / 'docs' / 'data' / 'data.json'
IMAGES_DIR = SCRIPT_DIR / 'docs' / 'images'


def is_image(path):
    try:
        with open(path, 'rb') as f:
            h = f.read(4)
        return h[:4] == b'\x89PNG' or h[:3] == b'\xff\xd8\xff'
    except:
        return False


def clean_filename_for_match(fname):
    """Aggressively clean any filename to get base ID for matching."""
    name = fname.replace('.png','').lower()
    name = name.replace('%28','_').replace('%29','_').replace('%2c','_')

    # Remove version suffixes
    for pat in [r'_je\d+_be\d+', r'_be\d+_je\d+', r'_je\d+', r'_be\d+',
                r'_alpha\d*', r'_beta\d*', r'_rc\d*', r'_28[^_]*29',
                r'_stage\d+', r'_age\d+', r'_\d+px', r'_sm$', r'_large$']:
        name = re.sub(pat, '', name, flags=re.IGNORECASE)

    name = name.strip('_-.').replace('__','_')
    return name


def match_images_to_items(item_ids, img_files):
    """For each item without an image, find the best matching image file."""
    matches = {}

    # Build index of cleaned image names
    img_index = {}
    for f in img_files:
        clean = clean_filename_for_match(f)
        if clean:
            img_index[f] = clean

    # For each item, find best match
    for iid in item_ids:
        # Priority 1: exact filename match
        if f'{iid}.png' in img_files:
            continue  # Already has image

        # Priority 2: cleaned name match
        best_match = None
        iid_parts = set(iid.split('_'))

        for fname, clean_name in img_index.items():
            if best_match:
                break
            # Direct match after cleaning
            if clean_name == iid:
                best_match = fname
                break
            # Contains match (item ID is substring of cleaned name)
            if iid in clean_name and len(iid) > 5:
                best_match = fname
                break

        # Priority 3: word-level match (all parts of item ID appear in cleaned name)
        if not best_match and len(iid_parts) >= 2:
            for fname, clean_name in img_index.items():
                if all(p in clean_name for p in iid_parts if len(p) > 2):
                    best_match = fname
                    break

        if best_match:
            matches[iid] = best_match

    return matches


def main():
    print('=' * 60)
    print('Standardize & Cleanup')
    print('=' * 60)

    # 1. Load data
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']
    existing_ids = {i['id'] for i in items}
    print(f'\n[1] Loaded: {len(items)} items')

    # 2. Standardize categories for items in wrong categories
    print('[2] Fixing categories...')
    cat_fixes = 0
    for item in items:
        iid = item['id']

        # Color items → blocks/colored
        for color_prefix in ['white_','orange_','magenta_','light_blue_','yellow_','lime_',
                              'pink_','gray_','light_gray_','cyan_','purple_','blue_',
                              'brown_','green_','red_','black_']:
            if iid.startswith(color_prefix):
                base = iid[len(color_prefix):]
                if any(base.endswith('_' + s) or base == s for s in ['wool','carpet','bed','stained_glass','stained_glass_pane','terracotta','glazed_terracotta','concrete','concrete_powder','shulker_box','bundle']):
                    if item.get('category') != 'blocks':
                        item['category'] = 'blocks'
                        item['subcategory'] = 'colored'
                        cat_fixes += 1
                elif base in ['dye','candle','banner']:
                    if item.get('category') != 'items':
                        item['category'] = 'items'
                        cat_fixes += 1

        # Wood items → blocks/wood
        for wood_prefix in ['oak_','spruce_','birch_','jungle_','acacia_','dark_oak_',
                             'mangrove_','cherry_','bamboo_','crimson_','warped_','pale_oak_']:
            if iid.startswith(wood_prefix):
                base = iid[len(wood_prefix):]
                if any(base.endswith('_' + s) or base == s for s in ['log','stripped_log','wood','stripped_wood','planks','stairs','slab','fence','fence_gate','door','trapdoor','button','pressure_plate','sign','hanging_sign']):
                    if item.get('category') != 'blocks':
                        item['category'] = 'blocks'
                        item['subcategory'] = 'wood'
                        cat_fixes += 1

    print(f'  Category fixes: {cat_fixes}')

    # 3. Fix name_zh standardization
    print('[3] Fixing Chinese names...')
    name_fixes = 0
    # Non-standard term replacements
    replacements = [
        ('�浅蓝', '淡蓝'), ('�浅灰', '淡灰'), ('�浅绿', '淡绿'),
        ('橡木木', '橡木'), ('云杉木木', '云杉木'),
    ]
    for item in items:
        old = item.get('name_zh','')
        for wrong, right in replacements:
            if wrong in old:
                item['name_zh'] = old.replace(wrong, right)
                name_fixes += 1

    print(f'  Name fixes: {name_fixes}')

    # 4. Match images to items
    print('[4] Matching images to items...')
    img_files = {f for f in os.listdir(IMAGES_DIR) if f.endswith('.png') and is_image(os.path.join(IMAGES_DIR, f))}
    print(f'  Valid images on disk: {len(img_files)}')

    # Find items without images
    without_img = [i for i in items if f'{i["id"]}.png' not in img_files]
    print(f'  Items without image: {len(without_img)}')

    matches = match_images_to_items([i['id'] for i in without_img], img_files)
    print(f'  Matchable: {len(matches)}')

    copied = 0
    for iid, src_fname in matches.items():
        src = IMAGES_DIR / src_fname
        dest = IMAGES_DIR / f'{iid}.png'
        if src.exists() and not dest.exists():
            shutil.copy2(src, dest)
            copied += 1

    print(f'  Images copied: {copied}')

    # 5. Update icon_url for all items
    print('[5] Updating icon_urls...')
    icon_fixes = 0
    for item in items:
        expected = f'images/{item["id"]}.png'
        if item.get('icon_url') != expected:
            item['icon_url'] = expected
            icon_fixes += 1
    print(f'  Icon fixes: {icon_fixes}')

    # 6. Remove unused images (not referenced by any item)
    print('[6] Cleaning unused images...')
    used_images = {f'{i["id"]}.png' for i in items}
    # Also keep images that are source copies
    unused = [f for f in img_files if f not in used_images and f != 'placeholder.png']

    removed = 0
    for f in unused:
        src = IMAGES_DIR / f
        if src.exists():
            src.unlink()
            removed += 1

    print(f'  Unused images removed: {removed}')

    # 7. Rebuild categories structure
    print('[7] Rebuilding categories...')
    cat_map = {}
    for item in items:
        c = item['category']
        s = item['subcategory']
        if c not in cat_map:
            cat_map[c] = {}
        if s not in cat_map[c]:
            cat_map[c][s] = []
        cat_map[c][s].append(item['id'])

    new_cats = []
    for cat_id in ['blocks', 'items', 'tools', 'combat', 'materials', 'food']:
        if cat_id in cat_map:
            subs = []
            for sub_id in sorted(cat_map[cat_id].keys()):
                cat_map[cat_id][sub_id].sort()
                subs.append({
                    'id': sub_id,
                    'name_zh': sub_id.replace('_',' ').title(),
                    'name_en': sub_id.replace('_',' ').title(),
                    'items': cat_map[cat_id][sub_id],
                })
            new_cats.append({
                'id': cat_id,
                'name_zh': {'blocks':'方块','items':'物品','tools':'工具','combat':'战斗','materials':'材料','food':'食物'}[cat_id],
                'name_en': {'blocks':'Blocks','items':'Items','tools':'Tools','combat':'Combat','materials':'Materials','food':'Food'}[cat_id],
                'icon_item': cat_map[cat_id][list(cat_map[cat_id].keys())[0]][0] if cat_map[cat_id] else '',
                'subcategories': subs,
            })

    data['categories'] = new_cats
    data['meta']['total_items'] = len(items)
    data['meta']['generated_at'] = '2026-05-04'

    # 8. Save
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    # 9. Final stats
    final_imgs = {f for f in os.listdir(IMAGES_DIR) if is_image(os.path.join(IMAGES_DIR, f))}
    with_img = sum(1 for i in items if f'{i["id"]}.png' in final_imgs)

    cats = Counter(i.get('category','?') for i in items)
    subs = Counter(i.get('subcategory','?') for i in items)

    print(f'\n=== FINAL STATE ===')
    print(f'Total items: {len(items)}')
    print(f'With image: {with_img} ({100*with_img//len(items)}%)')
    print(f'Images on disk: {len(final_imgs)}')
    print(f'data.json: {os.path.getsize(DATA_PATH)/1024:.0f} KB')
    print(f'Remote URLs: {sum(1 for i in items if i.get("icon_url","").startswith("http"))}')
    id_list = [i["id"] for i in items]
    dup_count = len(id_list) - len(set(id_list))
    print(f'Duplicate IDs: {dup_count}')
    print(f'\nCategories:')
    for c,n in cats.most_common():
        print(f'  {c}: {n}')
    print(f'\nTop subcategories:')
    for s,n in subs.most_common(12):
        print(f'  {s}: {n}')


if __name__ == '__main__':
    main()
