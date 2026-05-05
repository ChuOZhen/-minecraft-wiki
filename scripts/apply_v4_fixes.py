#!/usr/bin/env python3
"""apply_v4_fixes.py — Phase 4-6: hidden修正、中文名、排序、重建categories"""
import json, os
from collections import defaultdict

with open('docs/data/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']

# === Phase 4: Fix hidden ===
SPEC_HIDDEN = {
    'command_block', 'chain_command_block', 'repeating_command_block',
    'structure_block', 'structure_void', 'barrier', 'light_block', 'jigsaw_block',
    'spawner', 'knowledge_book', 'debug_stick',
    'grass_carried', 'mysterious_frame_slot', 'air', 'bubble_column',
    'trial_spawner', 'vault',
}

NON_ITEMS = {
    'animal', 'balloon', 'bedrock_editor', 'block', 'education_edition_180',
    'fluid', 'invalid_data_value_hay_bale', 'item', 'mentioned_features',
    'minecraft', 'minecraftedu_0985', 'technical_blocks', 'water_breathing',
    'weapon', 'weaving', 'the_copper_age', 'banners', 'copper', 'acacia',
    'birch', 'cherry', 'dark_oak', 'jungle', 'mangrove', 'oak', 'spruce',
    'crimson', 'warped', 'bamboo', 'pale_oak',
}

hidden_fixed = 0
hidden_final = 0
for item in items:
    iid = item['id']
    should_hide = iid in SPEC_HIDDEN or iid in NON_ITEMS
    if item.get('hidden') != should_hide:
        hidden_fixed += 1
    item['hidden'] = should_hide
    if should_hide:
        hidden_final += 1

print(f"Hidden fixed: {hidden_fixed}, total: {hidden_final}")

# === Phase 5: Chinese name fixes ===
COLORS = {
    'white': '白', 'orange': '橙', 'magenta': '品红', 'light_blue': '淡蓝',
    'yellow': '黄', 'lime': '黄绿', 'pink': '粉红', 'gray': '灰',
    'light_gray': '淡灰', 'cyan': '青', 'purple': '紫', 'blue': '蓝',
    'brown': '棕', 'green': '绿', 'red': '红', 'black': '黑',
}

WOOD_TYPES = {
    'oak': '橡木', 'spruce': '云杉', 'birch': '白桦', 'jungle': '丛林',
    'acacia': '金合欢', 'dark_oak': '深色橡木', 'mangrove': '红树',
    'cherry': '樱花', 'pale_oak': '苍白橡木', 'bamboo': '竹',
    'crimson': '绯红', 'warped': '诡异',
}

SUFFIX_ZH = {
    'door': '门', 'trapdoor': '活板门', 'fence': '栅栏', 'fence_gate': '栅栏门',
    'button': '按钮', 'pressure_plate': '压力板', 'slab': '台阶', 'stairs': '楼梯',
    'planks': '木板', 'log': '原木', 'wood': '木块', 'stripped_log': '去皮原木',
    'stripped_wood': '去皮木块', 'leaves': '树叶', 'sapling': '树苗',
    'sign': '告示牌', 'boat': '船', 'chest_boat': '运输船',
    'hanging_sign': '悬挂告示牌', 'raft': '竹筏',
}

T5_FIXES = {
    'dragon_egg': '龙蛋', 'eyeblossom': '眼眸花',
    'bamboo_stripped_log': '去皮竹原木', 'cherry_stripped_log': '去皮樱花木原木',
    'golden_dandelion': '金色蒲公英', 'dirt_path': '泥土小径',
    'purpur_stairs': '紫珀楼梯', 'end_portal_frame': '末地传送门框架',
    'decorated_pot': '纹饰陶罐', 'detector_rail': '探测铁轨',
    'powered_rail': '动力铁轨', 'rail': '铁轨', 'activator_rail': '激活铁轨',
    'cinnabar_brick_slab': '朱砂砖台阶', 'mud_brick_slab': '泥砖台阶',
    'tuff_brick_slab': '凝灰岩砖台阶', 'quartz_bricks': '石英砖',
}

zh_fixes = 0
for item in items:
    iid = item['id']
    current_zh = item.get('name_zh', '')

    # T5 known fixes
    if iid in T5_FIXES:
        item['name_zh'] = T5_FIXES[iid]
        item['zh_fallback'] = False
        zh_fixes += 1
        continue

    # Color-prefixed items
    for color_en, color_zh in COLORS.items():
        if iid.startswith(f'{color_en}_'):
            suffix_id = iid[len(color_en)+1:]
            suffix_zh = SUFFIX_ZH.get(suffix_id, '')
            if suffix_zh:
                item['name_zh'] = color_zh + '色' + suffix_zh
                item['zh_fallback'] = False
                zh_fixes += 1
            break

    # Wood-prefixed items
    for wood_en, wood_zh in WOOD_TYPES.items():
        if iid.startswith(f'{wood_en}_'):
            suffix_id = iid[len(wood_en)+1:]
            if suffix_id in SUFFIX_ZH:
                item['name_zh'] = wood_zh + SUFFIX_ZH[suffix_id]
                item['zh_fallback'] = False
                zh_fixes += 1
            elif suffix_id == 'stripped_log':
                item['name_zh'] = '去皮' + wood_zh + '原木'
                item['zh_fallback'] = False
                zh_fixes += 1
            elif suffix_id == 'stripped_wood':
                item['name_zh'] = '去皮' + wood_zh + '木块'
                item['zh_fallback'] = False
                zh_fixes += 1
            elif suffix_id == 'hanging_sign':
                item['name_zh'] = wood_zh + '悬挂告示牌'
                item['zh_fallback'] = False
                zh_fixes += 1
            break

# Fix zh_fallback
for item in items:
    if item.get('name_zh') == item.get('name_en') or not item.get('name_zh'):
        item['zh_fallback'] = True
    else:
        item['zh_fallback'] = False

fb_count = sum(1 for i in items if i.get('zh_fallback'))
print(f"Chinese name fixes: {zh_fixes}, zh_fallback: {fb_count}")

# === Phase 6: Rebuild categories ===
def sort_key_item(item_id):
    MATERIAL = {'wooden': 1, 'stone': 2, 'iron': 3, 'golden': 4, 'gold': 4, 'diamond': 5, 'netherite': 6}
    for mat, order in MATERIAL.items():
        if item_id.startswith(mat + '_'):
            return (order, item_id)
    COLOR_ORDER = {c: i for i, c in enumerate(COLORS.keys())}
    for color, order in COLOR_ORDER.items():
        if item_id.startswith(color + '_'):
            return (100 + order, item_id)
    WOOD_ORDER = {w: i for i, w in enumerate(WOOD_TYPES.keys())}
    for wood, order in WOOD_ORDER.items():
        if item_id.startswith(wood + '_'):
            return (400 + order, item_id)
    return (500, item_id)

tree = defaultdict(lambda: defaultdict(list))
for item in items:
    if item.get('hidden'):
        continue
    cat = item.get('category', 'miscellaneous')
    sub = item.get('subcategory', 'general')
    tree[cat][sub].append(item['id'])

CAT_ORDER = [
    'building_blocks', 'colored_blocks', 'natural_blocks', 'functional_blocks',
    'redstone', 'tools', 'combat', 'food', 'materials', 'miscellaneous'
]

CAT_NAMES = {
    'building_blocks': '建筑方块', 'colored_blocks': '彩色方块', 'natural_blocks': '自然方块',
    'functional_blocks': '功能方块', 'redstone': '红石', 'tools': '工具',
    'combat': '战斗', 'food': '食物', 'materials': '材料', 'miscellaneous': '杂项',
}

SUB_NAMES = {
    'stone': '石类', 'wood': '木材', 'bricks': '砖类', 'ore': '矿石', 'metal': '金属块',
    'sand': '沙类', 'dirt': '泥土类', 'ice': '冰雪类', 'glass': '玻璃类', 'end': '末地类',
    'nether': '下界类', 'ocean': '海洋类', 'other_building': '其他建筑',
    'wool': '羊毛', 'carpet': '地毯', 'concrete': '混凝土', 'concrete_powder': '混凝土粉末',
    'terracotta': '陶瓦', 'glazed_terracotta': '带釉陶瓦', 'stained_glass': '染色玻璃',
    'stained_glass_pane': '染色玻璃板', 'bed': '床', 'candle': '蜡烛', 'shulker_box': '潜影盒', 'banner': '旗帜',
    'vegetation': '植被', 'leaves': '树叶', 'sapling': '树苗', 'mushroom': '菌类',
    'flower': '花', 'crop': '农作物', 'wood_natural': '自然木材', 'natural_other': '其他自然',
    'workstation': '工作台', 'storage': '存储', 'enchanting': '附魔', 'light': '光源',
    'door_trapdoor': '门与活板门', 'rail': '铁轨', 'utility': '实用功能', 'technical': '技术方块',
    'power': '电源', 'transmission': '传输', 'action': '执行', 'minecart': '矿车', 'door_redstone': '红石门',
    'pickaxe': '镐', 'axe': '斧', 'shovel': '锹', 'hoe': '锄', 'fishing': '钓鱼',
    'utility_tool': '实用工具', 'ranged': '远程',
    'sword': '剑', 'axe_combat': '战斧', 'helmet': '头盔', 'chestplate': '胸甲',
    'leggings': '护腿', 'boots': '靴子', 'shield': '盾牌', 'horse_armor': '马铠',
    'meat': '肉类', 'fish': '鱼类', 'crop_food': '农作物食物', 'effect_food': '特效食物',
    'drink': '饮品', 'ingredient_food': '食材',
    'ingot': '锭', 'gem': '宝石', 'dye': '染料', 'mineral': '矿物原料',
    'mob_drop': '生物掉落', 'craft_material': '合成材料', 'spawn_egg': '刷怪蛋',
    'music_disc': '音乐唱片', 'other_material': '其他材料',
    'banner_pattern_item': '旗帜图案', 'pottery_sherd_item': '陶片',
    'smithing_template': '锻造模板', 'music_disc_item': '唱片',
    'boat': '船', 'minecart_item': '矿车物品', 'painting': '画',
    'item_frame': '物品展示框', 'pot': '饰纹陶罐', 'armor_stand': '盔甲架', 'hidden_misc': '隐藏杂项',
}

categories = []
for cat_id in CAT_ORDER:
    if cat_id not in tree:
        continue
    subcats = []
    for sub_id in sorted(tree[cat_id].keys()):
        sorted_items = sorted(tree[cat_id][sub_id], key=sort_key_item)
        subcats.append({
            'id': sub_id,
            'name_zh': SUB_NAMES.get(sub_id, sub_id),
            'name_en': sub_id.replace('_', ' ').title(),
            'items': sorted_items,
        })
    icon_item = ''
    if subcats and subcats[0].get('items'):
        icon_item = subcats[0]['items'][0]
    categories.append({
        'id': cat_id,
        'name_zh': CAT_NAMES.get(cat_id, cat_id),
        'name_en': cat_id.replace('_', ' ').title(),
        'icon_item': icon_item,
        'subcategories': subcats,
    })

data['categories'] = categories
data['meta']['total_items'] = len(items)
data['meta']['generated_at'] = '2026-05-05-v4-final'

with open('docs/data/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Stats
visible = sum(1 for i in items if not i.get('hidden'))
cat_count = sum(len(s.get('items',[])) for c in categories for s in c.get('subcategories',[]))
has_zh = sum(1 for i in items if i.get('name_zh') and i.get('name_zh') != i.get('name_en') and not i.get('zh_fallback'))
has_sec = sum(1 for i in items if i.get('secondary_categories'))

print(f"\n=== Final Stats ===")
print(f"Total: {len(items)}, Visible: {visible}, Hidden: {hidden_final}, In cats: {cat_count}")
print(f"Categories: {len(categories)}")
for c in categories:
    ic = sum(len(s.get('items',[])) for s in c['subcategories'])
    print(f"  {c['name_zh']} ({c['id']}): {len(c['subcategories'])} subcats, {ic} items")
print(f"Chinese name: {has_zh}/{len(items)} ({has_zh/len(items)*100:.1f}%)")
print(f"Secondary categories: {has_sec}")
print(f"data.json: {os.path.getsize('docs/data/data.json')/1024:.0f} KB")
