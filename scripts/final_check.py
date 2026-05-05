import json
from collections import Counter

with open('docs/data/data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

items = d['items']
categories = d['categories']

print('=' * 60)
print('FINAL STATUS CHECK')
print('=' * 60)
print('')
print('Total items:', len(items))
print('Total categories:', len(categories))
print('')

# Category breakdown
for c in categories:
    cat_total = sum(len(s['items']) for s in c['subcategories'])
    print('Category: ' + c['id'] + ' (' + c['name_zh'] + ')')
    print('  subcategories: ' + str(len(c['subcategories'])))
    print('  items: ' + str(cat_total))
    for s in c['subcategories']:
        print('    - ' + s['id'] + ' (' + s['name_zh'] + '): ' + str(len(s['items'])))
    print('')

# Cross-check: items referenced in categories vs items list
all_cat_items = set()
for c in categories:
    for s in c['subcategories']:
        all_cat_items.update(s['items'])

item_ids = set(i['id'] for i in items)

orphan = item_ids - all_cat_items
phantom = all_cat_items - item_ids

print('---')
print('Items in list but not in any category: ' + str(len(orphan)))
print('Items in categories but not in list: ' + str(len(phantom)))

# Source breakdown
sources = Counter(i.get('source', 'unknown') for i in items)
print('')
print('Source breakdown:')
for src, cnt in sources.most_common():
    print('  ' + src + ': ' + str(cnt))

# Check category/subcategory field consistency
mismatch = 0
for item in items:
    item_id = item['id']
    cat = item.get('category', '')
    subcat = item.get('subcategory', '')
    found = False
    for c in categories:
        if c['id'] == cat:
            for s in c['subcategories']:
                if s['id'] == subcat and item_id in s['items']:
                    found = True
                    break
            break
    if not found and cat and subcat:
        mismatch += 1

print('')
print('Category/subcategory field mismatches: ' + str(mismatch))

print('')
print('=' * 60)
print('CHECK COMPLETE')
print('=' * 60)
