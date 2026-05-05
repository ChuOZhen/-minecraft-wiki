import json
from collections import defaultdict, Counter

with open('docs/data/data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

items = d['items']
categories = d['categories']

print('=== 基础统计 ===')
print('Total items:', len(items))
print('Total categories:', len(categories))

# Category stats
for c in categories:
    total_in_cat = sum(len(s['items']) for s in c['subcategories'])
    print('Category:', c['id'], '|', c['name_zh'], '| subcats:', len(c['subcategories']), '| items:', total_in_cat)
    for s in c['subcategories']:
        print('  Subcat:', s['id'], '|', s['name_zh'], '| items:', len(s['items']))

# Build reverse lookup: item_id -> [categories]
item_to_cats = defaultdict(list)
item_to_subcats = defaultdict(list)
for c in categories:
    for s in c['subcategories']:
        for item_id in s['items']:
            item_to_cats[item_id].append(c['id'])
            item_to_subcats[item_id].append(s['id'])

# Check cross-category items
cross_cat = {k: v for k, v in item_to_cats.items() if len(v) > 1}
print('\n=== 跨类别物品 ===')
print('Items in multiple categories:', len(cross_cat))
for item_id, cats in sorted(cross_cat.items())[:30]:
    item = next((i for i in items if i['id']==item_id), None)
    print(' ', item_id, '->', cats, '|', item['name_zh'] if item else '?')

# Check items not in any category
item_ids = {i['id'] for i in items}
cat_item_ids = set(item_to_cats.keys())
orphan = item_ids - cat_item_ids
print('\n=== 孤儿物品（不在任何类别中） ===')
print('Count:', len(orphan))
for oid in sorted(orphan)[:30]:
    item = next((i for i in items if i['id']==oid), None)
    print(' ', oid, '|', item['name_zh'] if item else '?', '| cat:', item.get('category'), '| subcat:', item.get('subcategory'))

# Check phantom items (in category but not in items list)
phantom = cat_item_ids - item_ids
print('\n=== 幽灵物品（在类别中但不在items列表） ===')
print('Count:', len(phantom))
for pid in sorted(phantom)[:30]:
    print(' ', pid)

# Sorting check within subcategories
print('\n=== 排序问题检测 ===')
sorting_issues = []
for c in categories:
    for s in c['subcategories']:
        sub_items = s['items']
        for i, item_id in enumerate(sub_items):
            # Check if variant comes before base
            for suffix in ['_slab', '_stairs', '_wall', '_fence', '_button', '_pressure_plate', '_trapdoor', '_door']:
                if item_id.endswith(suffix):
                    base = item_id[:-len(suffix)]
                    if base in sub_items and sub_items.index(base) > i:
                        sorting_issues.append({
                            'category': c['name_zh'],
                            'subcategory': s['name_zh'],
                            'item': item_id,
                            'base': base,
                            'type': suffix + ' before base'
                        })
                        break
            if 'stripped_' in item_id:
                base = item_id.replace('stripped_', '')
                if base in sub_items and sub_items.index(base) > i:
                    sorting_issues.append({
                        'category': c['name_zh'],
                        'subcategory': s['name_zh'],
                        'item': item_id,
                        'base': base,
                        'type': 'stripped before base'
                    })

print('Total sorting issues:', len(sorting_issues))
for issue in sorting_issues[:20]:
    print(' ', issue['category'], '>', issue['subcategory'], ':', issue['item'], 'before', issue['base'])

# Propose new classification: items that logically belong to multiple categories
print('\n=== 应跨类别的物品分析 ===')

# Redstone items that are also ores/minerals
redstone_items = [i['id'] for i in items if i.get('category') == 'redstone']
print('Redstone items that could also be materials:', len(redstone_items))

# Tools that could also be combat
combat_tools = []
for item in items:
    en = item['name_en'].lower()
    if 'sword' in en or 'axe' in en:
        if item.get('category') == 'tools':
            combat_tools.append(item['id'])
print('Tools that could also be combat (sword/axe):', len(combat_tools))

# Wood items that are also functional (doors, trapdoors, signs)
wood_functional = []
for item in items:
    item_id = item['id']
    woods = ['oak', 'spruce', 'birch', 'jungle', 'acacia', 'dark_oak', 'mangrove', 'cherry', 'bamboo', 'crimson', 'warped', 'pale_oak']
    is_wood = any(w in item_id for w in woods)
    if is_wood and any(x in item_id for x in ['_door', '_trapdoor', '_sign', '_button', '_pressure_plate']):
        if item.get('category') != 'functional_blocks' and item.get('subcategory') != 'door':
            wood_functional.append(item_id)
print('Wood items that could also be functional:', len(wood_functional))

# Ores that are also blocks
ore_blocks = []
for item in items:
    if item.get('category') == 'materials' and 'ore' in item['id']:
        ore_blocks.append(item['id'])
print('Ores that could also be blocks:', len(ore_blocks))

# Food items in other categories
food_items_misc = []
for item in items:
    en = item['name_en'].lower()
    food_keywords = ['apple', 'bread', 'beef', 'porkchop', 'chicken', 'mutton', 'rabbit', 'cod', 'salmon', 'melon', 'berries', 'cookie', 'pie', 'stew', 'soup', 'carrot', 'potato', 'beetroot', 'honey', 'cake']
    if any(kw in en for kw in food_keywords) or 'cooked_' in item['id']:
        if item.get('category') != 'food':
            food_items_misc.append(item['id'])
print('Food-like items not in food category:', len(food_items_misc))

with open('analysis_current.json', 'w', encoding='utf-8') as f:
    json.dump({
        'total_items': len(items),
        'total_categories': len(categories),
        'cross_category_items': cross_cat,
        'orphan_items': list(orphan),
        'phantom_items': list(phantom),
        'sorting_issues': sorting_issues,
        'should_be_cross_category': {
            'redstone_as_materials': redstone_items,
            'tools_as_combat': combat_tools,
            'wood_as_functional': wood_functional,
            'ores_as_blocks': ore_blocks,
            'food_miscategorized': food_items_misc
        }
    }, f, ensure_ascii=False, indent=2)

print('\nSaved to analysis_current.json')
