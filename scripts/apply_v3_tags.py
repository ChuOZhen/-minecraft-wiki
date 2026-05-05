#!/usr/bin/env python3
"""
apply_v3_tags.py — V3.1 规则引擎：排序 + 标签 + 子类命名
当前数据: 1531 items, 9大类, 24标签
用法: python apply_v3_tags.py (在 ai_classify.py 之后运行)
"""
import json, os
from collections import Counter, defaultdict

DATA_PATH = 'docs/data/data.json'

# ============================================================
# 排序规则
# ============================================================
FORM_ORDER = [
    '', 'log', 'stripped_log', 'wood', 'stripped_wood',
    'planks', 'slab', 'stairs', 'wall',
    'fence', 'fence_gate', 'door', 'trapdoor',
    'button', 'pressure_plate', 'sign', 'hanging_sign',
    'bricks', 'mosaic', 'mosaic_slab', 'mosaic_stairs',
]
COLOR_ORDER = ['white','orange','magenta','light_blue','yellow','lime','pink','gray','light_gray','cyan','purple','blue','brown','green','red','black']
WOOD_ORDER = ['oak','spruce','birch','jungle','acacia','dark_oak','mangrove','cherry','bamboo','crimson','warped','pale_oak']
METAL_ORDER = ['copper','exposed_copper','weathered_copper','oxidized_copper','waxed_copper','waxed_exposed_copper','waxed_weathered_copper','waxed_oxidized_copper','iron','gold','golden','diamond','netherite']

FORM_SUFFIXES = ['_slab','_stairs','_wall','_fence','_fence_gate','_door','_trapdoor','_button','_pressure_plate','_sign','_hanging_sign']

def sort_key(iid):
    ci = next((idx for idx, c in enumerate(COLOR_ORDER) if iid.startswith(c + '_')), 99)
    wi = next((idx for idx, w in enumerate(WOOD_ORDER) if iid.startswith(w + '_')), 99)
    mi = next((idx for idx, m in enumerate(METAL_ORDER) if iid.startswith(m + '_') or m in iid), 99)
    # Base block first (0), variants after (1)
    is_variant = any(iid.endswith(f) for f in FORM_SUFFIXES)
    return (ci, wi, mi, 1 if is_variant else 0, iid)

# ============================================================
# 标签规则
# ============================================================
REDSTONE_IDS = [
    'redstone','redstone_torch','redstone_repeater','redstone_comparator',
    'piston','sticky_piston','dispenser','dropper','observer','tnt',
    'note_block','target','daylight_detector','lever','tripwire_hook',
    'calibrated_sculk_sensor','heavy_weighted_pressure_plate','light_weighted_pressure_plate',
    'redstone_lamp','hopper',
]
SWORD_IDS = ['wooden_sword','stone_sword','iron_sword','golden_sword','diamond_sword','netherite_sword']
AXE_IDS   = ['wooden_axe','stone_axe','iron_axe','golden_axe','diamond_axe','netherite_axe']
PICK_IDS  = ['wooden_pickaxe','stone_pickaxe','iron_pickaxe','golden_pickaxe','diamond_pickaxe','netherite_pickaxe']
SHOVEL_IDS= ['wooden_shovel','stone_shovel','iron_shovel','golden_shovel','diamond_shovel','netherite_shovel']
HOE_IDS   = ['wooden_hoe','stone_hoe','iron_hoe','golden_hoe','diamond_hoe','netherite_hoe']

WOODS = ['oak','spruce','birch','jungle','acacia','dark_oak','mangrove','cherry','bamboo','crimson','warped','pale_oak']
WOOD_VARIANTS = ['door','trapdoor','button','pressure_plate','sign','hanging_sign','fence_gate']

# ============================================================
# 子类中文名
# ============================================================
SUB_ZH = {
    # blocks
    'stone': '石类', 'wood': '木材', 'bricks': '砖类', 'ore': '矿石',
    'metal': '金属', 'dirt': '泥土', 'flora': '植物', 'ice': '冰雪',
    'sand': '沙子', 'magnetic': '磁性', 'other_blocks': '其他方块', 'light': '照明',
    # colored_blocks
    'wool': '羊毛', 'carpet': '地毯', 'bed': '床类', 'concrete': '混凝土',
    'terracotta': '陶瓦', 'stained_glass': '染色玻璃', 'candle': '蜡烛',
    'shulker_box': '潜影盒', 'banner': '旗帜',
    # functional_blocks
    'storage': '存储', 'workstation': '工作台', 'enchanting': '附魔',
    'door': '门与活板门', 'rail': '交通',
    # redstone
    'power': '电源', 'transmission': '传导', 'action': '执行', 'sound': '声音',
    # items
    'dye': '染料', 'potion': '药水', 'spawn_egg': '刷怪蛋',
    'enchanted_book': '附魔书', 'disc': '音乐唱片',
    'pottery_sherd': '陶片', 'banner_pattern': '旗帜图案',
    'transport': '交通', 'misc': '杂项',
    # tools
    'pickaxe': '镐类', 'axe': '斧类', 'shovel': '锹类', 'hoe': '锄类',
    'ranged': '远程', 'utility': '实用',
    # combat
    'sword': '剑类', 'shield': '盾牌', 'helmet': '头盔',
    'chestplate': '胸甲', 'leggings': '护腿', 'boots': '靴子',
    # food
    'meat': '肉类', 'fish': '鱼类', 'crop': '农作物', 'effect_food': '特效食物',
    # materials
    'ingot': '金属锭', 'gem': '宝石', 'fiber': '纤维',
    'nether': '下界材料', 'other_material': '其他材料',
}


def assign_tags(item):
    iid = item['id']
    cat = item.get('category','')
    sub = item.get('subcategory','')
    tags = set()

    # --- function ---
    if cat in ('blocks','colored_blocks'): tags.add('building')
    elif cat == 'functional_blocks': tags.add('functional')
    elif cat == 'redstone': tags.add('redstone')
    elif cat == 'combat': tags.add('combat')
    elif cat == 'tools': tags.add('tool')
    elif cat == 'food': tags.add('food')
    elif cat == 'items':
        if sub == 'transport': tags.add('transport')
        elif sub == 'dye': tags.add('dye')
        elif sub in ('spawn_egg','misc','disc','pottery_sherd','banner_pattern'): tags.add('decoration')
    elif cat == 'materials': tags.add('crafting')

    # --- material ---
    if any(iid.startswith(w + '_') for w in WOODS) or sub == 'wood': tags.add('wood')
    elif iid in ('stick','bowl','paper','book','bookshelf'): tags.add('wood')
    if sub in ('stone','bricks'): tags.add('stone')
    elif any(s in iid for s in ['stone','cobblestone','granite','diorite','andesite','deepslate','tuff','blackstone','basalt']): tags.add('stone')
    if sub == 'metal' or any(m in iid for m in ['iron_','golden_','copper_','netherite_']):
        if not iid.endswith('_ore'): tags.add('metal')
    if sub in ('ore','gem'): tags.add('mineral')
    elif any(g in iid for g in ['diamond','emerald','lapis','quartz','amethyst','redstone']): tags.add('mineral')
    if sub in ('flora','crop','meat','fish','food'): tags.add('organic')
    if sub in ('wool','carpet','fiber'): tags.add('fabric')

    # --- dimension ---
    if any(n in iid for n in ['nether','crimson','warped','soul','blaze','ghast','wither','piglin','hoglin','strider','basalt','blackstone','ancient_debris','netherite']): tags.add('nether')
    elif any(e in iid for e in ['end_','ender','chorus','purpur','shulker','elytra','dragon']): tags.add('end')
    elif any(a in iid for a in ['prismarine','sea_','turtle','cod','salmon','tropical','pufferfish','dolphin','guardian','elder','squid','drowned','trident','conduit','nautilus','kelp']): tags.add('aquatic')
    else: tags.add('overworld')

    # --- source ---
    if sub in ('wood','bricks','colored','wool','carpet','concrete','stained_glass','candle','bed','shulker_box','storage','workstation','light','door','rail','transport','tools','weapons','armor','pickaxe','axe','shovel','hoe','sword','shield','helmet','chestplate','leggings','boots','ranged','utility','dye','ingot','food'): tags.add('crafted')
    if cat in ('tools','combat'): tags.add('crafted')
    if sub in ('ore','stone','metal','gem','dirt','sand','ice'): tags.add('mined')
    if sub in ('dye','gem') or any(t in iid for t in ['emerald','_trade','villager']): tags.add('traded')
    if sub in ('meat','fish','fiber'): tags.add('dropped')
    elif any(d in iid for d in ['_hide','_scute','_membrane','_foot','feather','leather','bone','string','spider_eye','rotten','gunpowder','ender_pearl','blaze_rod','ghast_tear','slime','honeycomb']): tags.add('dropped')

    # --- cross-category ---
    if iid in REDSTONE_IDS: tags.update(['mineral','redstone'])
    if iid in SWORD_IDS: tags.update(['combat','tool'])
    if iid in AXE_IDS: tags.update(['tool','combat'])
    if iid in PICK_IDS: tags.add('tool')
    if iid in SHOVEL_IDS: tags.add('tool')
    if iid in HOE_IDS: tags.add('tool')
    for w in WOODS:
        for v in WOOD_VARIANTS:
            if iid == f'{w}_{v}': tags.update(['wood','functional'])
    if sub == 'ore': tags.update(['mineral','mined'])
    if sub == 'dye': tags.update(['dye','organic'])
    if cat == 'food': tags.add('food')

    # WAX
    if 'waxed' in iid: tags.add('crafted')

    return sorted(tags)


def main():
    print('=' * 60)
    print('V3.1 Tags Engine: Sort + Tags + Naming')
    print('=' * 60)

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']
    print(f'\n[1] {len(items)} items')

    # Sort
    cat_order = ['blocks','colored_blocks','functional_blocks','redstone','items','tools','combat','food','materials']
    ci_map = {c: i for i, c in enumerate(cat_order)}
    items.sort(key=lambda i: (ci_map.get(i.get('category','zzz'), 99), sort_key(i.get('id',''))))
    print(f'[2] Sorted')

    # Tags
    for item in items:
        item['tags'] = assign_tags(item)
    print(f'[3] Tags assigned')

    # Rebuild categories
    cat_zh = {'blocks':'方块','colored_blocks':'彩色方块','functional_blocks':'功能方块','redstone':'红石','items':'物品','tools':'工具','combat':'战斗','food':'食物','materials':'材料'}
    cat_icons = {'blocks':'stone','colored_blocks':'white_wool','functional_blocks':'crafting_table','redstone':'redstone','items':'stick','tools':'iron_pickaxe','combat':'iron_sword','food':'bread','materials':'iron_ingot'}

    cat_map = defaultdict(lambda: defaultdict(list))
    for item in items:
        cat_map[item['category']][item['subcategory']].append(item['id'])

    new_cats = []
    for cid in cat_order:
        if cid not in cat_map: continue
        subs = []
        for sid in sorted(cat_map[cid].keys()):
            ids = sorted(cat_map[cid][sid], key=sort_key)
            zh = SUB_ZH.get(sid, sid)
            subs.append({'id': sid, 'name_zh': zh, 'name_en': sid.replace('_',' ').title(), 'items': ids})
        new_cats.append({'id': cid, 'name_zh': cat_zh[cid], 'name_en': cid.replace('_',' ').title(), 'icon_item': cat_icons.get(cid,''), 'subcategories': subs})

    data['categories'] = new_cats
    data['meta']['total_items'] = len(items)

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    # Validate
    sort_issues = 0
    for cat_entry in new_cats:
        for sub in cat_entry['subcategories']:
            slist = sub['items']
            for i, iid in enumerate(slist):
                for suffix in ['_slab','_stairs','_wall','_fence','_fence_gate','_door','_trapdoor','_button','_pressure_plate']:
                    if iid.endswith(suffix):
                        base = iid[:-len(suffix)]
                        if base in slist and slist.index(base) > i and 'mosaic' not in iid:
                            sort_issues += 1

    no_tags = sum(1 for i in items if not i.get('tags'))
    redstone_check = sum(1 for i in items if i.get('category')=='redstone' and 'mineral' not in i.get('tags',[]))
    sword_check = sum(1 for i in items if i['id'].endswith('_sword') and not ('combat' in i.get('tags',[]) and 'tool' in i.get('tags',[])))

    cats = Counter(i['category'] for i in items)
    all_tags = Counter()
    for item in items:
        for t in item.get('tags', []): all_tags[t] += 1

    print(f'\n=== Validate ===')
    print(f'Sort issues: {sort_issues}')
    print(f'No tags: {no_tags}')
    print(f'Redstone no mineral: {redstone_check}')
    print(f'Sword tags incomplete: {sword_check}')
    ok = sort_issues==0 and no_tags==0 and redstone_check==0 and sword_check==0
    print(f'Result: {"PASS" if ok else "NEEDS FIX"}')

    print(f'\n=== Stats ===')
    print(f'Items: {len(items)}')
    for cid in cat_order:
        if cid in cats: print(f'  {cat_zh.get(cid,cid)}: {cats[cid]}')
    print(f'Tags: {len(all_tags)} types')
    for t, n in all_tags.most_common(12): print(f'  {t}: {n}')
    print(f'data.json: {os.path.getsize(DATA_PATH)/1024:.0f} KB')


if __name__ == '__main__':
    main()
