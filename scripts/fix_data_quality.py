#!/usr/bin/env python3
"""
fix_data_quality.py — 工业级数据质量修复
【1】中文翻译修正 【2】数据清洗 【3】ID修正 【4】分类重构 【5】去重
"""
import json, os, shutil
from collections import defaultdict

DATA_PATH = 'docs/data/data.json'
BACKUP_PATH = 'docs/data/data_backup_quality.json'
shutil.copy(DATA_PATH, BACKUP_PATH)
print(f"Backup: {BACKUP_PATH}")

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']
item_map = {i['id']: i for i in items}

# ============================================================
# 【1】中文翻译修正
# ============================================================
ZH_FIXES = {
    # bundle
    'bundle': '束口袋',
    'white_bundle': '白色束口袋', 'orange_bundle': '橙色束口袋',
    'magenta_bundle': '品红色束口袋', 'light_blue_bundle': '淡蓝色束口袋',
    'yellow_bundle': '黄色束口袋', 'lime_bundle': '黄绿色束口袋',
    'pink_bundle': '粉色束口袋', 'gray_bundle': '灰色束口袋',
    'light_gray_bundle': '淡灰色束口袋', 'cyan_bundle': '青色束口袋',
    'purple_bundle': '紫色束口袋', 'blue_bundle': '蓝色束口袋',
    'brown_bundle': '棕色束口袋', 'green_bundle': '绿色束口袋',
    'red_bundle': '红色束口袋', 'black_bundle': '黑色束口袋',
    # spawn eggs - official names
    'spawn_egg': '刷怪蛋',
    # potions - full official naming
    'potion': '药水', 'splash_potion': '喷溅型药水', 'lingering_potion': '滞留型药水',
    'water_bottle': '水瓶', 'awkward_potion': '粗制的药水',
    'mundane_potion': '平凡的药水', 'thick_potion': '浓稠的药水',
    # critical fixes
    'bow': '弓', 'crossbow': '弩',
    'heavy_core': '重质核心',
    'copper_horn': '铜质号角',
    'ominous_bottle': '不祥之瓶',
    # boat naming fix
    'oak_boat_with_chest': '橡木运输船', 'spruce_boat_with_chest': '云杉运输船',
    'birch_boat_with_chest': '白桦运输船', 'jungle_boat_with_chest': '丛林木运输船',
    'acacia_boat_with_chest': '金合欢木运输船', 'dark_oak_boat_with_chest': '深色橡木运输船',
    'mangrove_boat_with_chest': '红树木运输船', 'cherry_boat_with_chest': '樱花木运输船',
    'pale_oak_boat_with_chest': '苍白橡木运输船', 'bamboo_chest_raft': '竹运输筏',
}

potion_effects = {
    'fire_resistance': '抗火', 'healing': '治疗', 'harming': '伤害',
    'invisibility': '隐身', 'leaping': '跳跃', 'night_vision': '夜视',
    'poison': '剧毒', 'regeneration': '再生', 'slow_falling': '缓降',
    'slowness': '缓慢', 'strength': '力量', 'swiftness': '迅捷',
    'turtle_master': '神龟', 'water_breathing': '水肺', 'weakness': '虚弱',
    'decay': '衰变', 'infested': '寄生', 'oozing': '渗浆',
    'weaving': '盘丝', 'wind_charged': '蓄风',
}
potion_modifiers = {'long': '延长版', 'strong': '加强版'}

zh_fixed = 0
for item in items:
    iid = item['id']
    if iid in ZH_FIXES:
        old = item.get('name_zh','')
        item['name_zh'] = ZH_FIXES[iid]
        item['zh_fallback'] = False
        zh_fixed += 1
        continue

    # Fix potion naming
    for pfx, pfx_zh in [('lingering_potion_of_', '滞留型'), ('splash_potion_of_', '喷溅型'), ('potion_of_', '')]:
        if iid.startswith(pfx):
            eff = iid[len(pfx):]
            for mod_suffix, mod_zh in potion_modifiers.items():
                if eff.endswith('_' + mod_suffix):
                    base_eff = eff[:-(len(mod_suffix)+1)]
                    if base_eff in potion_effects:
                        item['name_zh'] = pfx_zh + potion_effects[base_eff] + '药水(' + mod_zh + ')'
                        item['zh_fallback'] = False
                        zh_fixed += 1
                    break
            else:
                if eff in potion_effects:
                    if pfx_zh:
                        item['name_zh'] = pfx_zh + potion_effects[eff] + '药水'
                    else:
                        item['name_zh'] = potion_effects[eff] + '药水'
                    item['zh_fallback'] = False
                    zh_fixed += 1
            break

    # Fix spawn_egg naming: "*_spawn_egg" → "生物名刷怪蛋"
    if iid.endswith('_spawn_egg') and iid != 'spawn_egg':
        mob_id = iid[:-10]
        if item.get('name_zh','').endswith('刷怪蛋') and not item['name_zh'].startswith('刷怪蛋'):
            # already fixed
            pass

print(f"ZH fixes: {zh_fixed}")

# ============================================================
# 【2】数据清洗 - 删除非原版 + 抽象占位物品
# ============================================================

# Non-vanilla items to DELETE
NON_VANILLA = {
    # cinnabar series
    'cinnabar_brick', 'cinnabar_brick_slab', 'cinnabar_brick_stairs', 'cinnabar_brick_wall',
    # sulfur series
    'sulfur_spike', 'sulfur_block', 'sulfur_ore',
    # ruby
    'ruby',
    # copper golem
    'copper_golem_statue',
    # hardened glass
    'hardened_glass', 'hardened_stained_glass',
    # colored torch
    'colored_torch',
    # nether reactor
    'nether_reactor_core',
    # spears (not vanilla)
    'copper_spear', 'diamond_spear', 'golden_spear', 'iron_spear', 'stone_spear', 'wooden_spear',
    # copper armor (not vanilla)
    'copper_leggings', 'copper_helmet', 'copper_chestplate', 'copper_boots',
    # studded armor
    'studded_armor', 'studded_helmet', 'studded_chestplate', 'studded_leggings', 'studded_boots',
    # Education Edition
    'sparkler', 'orange_sparkler', 'blue_sparkler', 'red_sparkler', 'purple_sparkler', 'green_sparkler',
    'glow_stick', 'balloon', 'medicine', 'ice_bomb', 'bleach', 'antidote', 'elixir', 'eye_drops', 'tonic',
    'hardened_glass_pane',
    # sea pickle is vanilla! (renamed to sea_pickle in 1.13+)
    'harness',
    # pottery_sherd as a standalone item (not a specific sherd)
    'pottery_sherd',
    # shapeless recipes
    'shaper_smithing_template',
    # non-vanilla copper items
    'copper_torch', 'copper_lantern', 'copper_soul_lantern', 'copper_pressure_plate', 'copper_button',
    # more Education / non-vanilla
    'colored_torch_bp', 'colored_torch_rp', 'colored_torch_bg', 'colored_torch_rg',
    'colored_torch_by', 'colored_torch_ry', 'colored_torch_bw', 'colored_torch_rw',
    # non-vanilla buckets
    'tropical_fish_bucket_item',
}

# Abstract placeholder items to DELETE
ABSTRACT_PLACEHOLDERS = {
    'axe', 'hoe', 'pickaxe', 'shovel',
    'sword', 'boots', 'helmet', 'chestplate', 'leggings',
    'tool', 'armor', 'weapon',
    'banners', 'animal', 'item', 'block',
    'technical_blocks', 'fluid',
    'horse_armor', 'shield_generic',
    'copper',  # this should be copper_ingot
    'acacia', 'birch', 'cherry', 'dark_oak', 'jungle', 'mangrove', 'oak', 'spruce', 'pale_oak',
    'crimson', 'warped', 'bamboo',
    'music_disc',  # generic, not a real disc
    'minecraft', 'minecraftedu_0985', 'education_edition_180',
    'bedrock_editor', 'the_copper_age', 'mentioned_features',
    'invalid_data_value_hay_bale',
}

ALL_DELETE = NON_VANILLA | ABSTRACT_PLACEHOLDERS

# Also: remove "heavy_core" per user request
ALL_DELETE.add('heavy_core')

deleted = []
new_items = []
for item in items:
    if item['id'] in ALL_DELETE:
        deleted.append(item['id'])
    else:
        new_items.append(item)

print(f"Deleted: {len(deleted)} items")
print(f"  Non-vanilla: {[d for d in deleted if d in NON_VANILLA]}")
print(f"  Abstract: {[d for d in deleted if d in ABSTRACT_PLACEHOLDERS]}")
items = new_items

# ============================================================
# 【3】ID 修正 + 合并去重
# ============================================================
item_map = {i['id']: i for i in items}

# Rename ender_eye → eye_of_ender
if 'ender_eye' in item_map:
    item_map['ender_eye']['id'] = 'eye_of_ender'
    print("Renamed: ender_eye → eye_of_ender")

# Merge *_chest_boat → *_boat_with_chest (keep boat_with_chest naming)
WOODS = ['oak', 'spruce', 'birch', 'jungle', 'acacia', 'dark_oak', 'mangrove', 'cherry', 'pale_oak']
merged = 0
for wood in WOODS:
    chest_id = f'{wood}_chest_boat'
    boat_id = f'{wood}_boat_with_chest'
    if chest_id in item_map and boat_id in item_map:
        # Keep boat_with_chest, merge crafting data from chest_boat if needed
        chest_item = item_map[chest_id]
        boat_item = item_map[boat_id]
        # Transfer crafting recipes if boat version has none
        if not boat_item.get('crafting') and chest_item.get('crafting'):
            boat_item['crafting'] = chest_item['crafting']
        # Delete chest_boat
        del item_map[chest_id]
        merged += 1
    elif chest_id in item_map:
        # Rename to boat_with_chest
        item_map[chest_id]['id'] = boat_id
        renamed += 1

# Also handle bamboo
if 'bamboo_chest_raft' in item_map and 'bamboo_raft_with_chest' in item_map:
    del item_map['bamboo_chest_raft']
    merged += 1

# Rebuild items list
items = list(item_map.values())
print(f"Merged {merged} chest_boat → boat_with_chest duplicates")

# ============================================================
# 【4】分类重构
# ============================================================

# Fix ore category: all ores → natural_blocks/ore
ore_fixed = 0
for item in items:
    iid = item['id']
    if (iid.endswith('_ore') or iid == 'ancient_debris') and item.get('category') != 'natural_blocks':
        if item.get('subcategory') != 'ore':
            item['category'] = 'natural_blocks'
            item['subcategory'] = 'ore'
            ore_fixed += 1
print(f"Ore category fixed: {ore_fixed}")

# Fix spawn_egg category: ensure materials/spawn_egg
sp_fixed = 0
for item in items:
    if item['id'].endswith('_spawn_egg') and item.get('subcategory') != 'spawn_egg':
        item['category'] = 'materials'
        item['subcategory'] = 'spawn_egg'
        sp_fixed += 1
print(f"Spawn egg category fixed: {sp_fixed}")

# Fix heavy items - moved to materials
for item in items:
    if item['id'] in ('nether_star', 'dragon_egg', 'heart_of_the_sea', 'netherite_scrap'):
        if item.get('category') in ('building_blocks', 'miscellaneous'):
            item['category'] = 'materials'

# Fix boat category
for item in items:
    if item['id'].endswith('_boat') or item['id'].endswith('_boat_with_chest') or item['id'].endswith('_raft') or item['id'].endswith('_chest_raft'):
        if item.get('category') == 'miscellaneous':
            pass  # keep in miscellaneous/boat

# ============================================================
# 【5】Final: fix all icon_url to local path
# ============================================================
img_dir = 'docs/images'
existing_imgs = set(os.listdir(img_dir)) if os.path.isdir(img_dir) else set()

icon_fixed = 0
for item in items:
    iid = item['id']
    local_path = f'images/{iid}.png'
    current = item.get('icon_url', '')
    if not current.startswith('images/') or current != local_path:
        if f'{iid}.png' in existing_imgs:
            item['icon_url'] = local_path
            icon_fixed += 1
        elif current.startswith('images/') and current != local_path:
            # Keep existing local path even if name changed
            pass

print(f"Icon paths fixed: {icon_fixed}")

# ============================================================
# 【6】Rebuild data
# ============================================================
data['items'] = items
data['meta']['total_items'] = len(items)
data['meta']['generated_at'] = '2026-05-05-quality'

# Rebuild categories
CAT_ORDER = [
    'building_blocks', 'colored_blocks', 'natural_blocks', 'functional_blocks',
    'tools', 'combat', 'food', 'materials', 'miscellaneous'
]
CAT_NAMES = {
    'building_blocks': '建筑方块', 'colored_blocks': '彩色方块', 'natural_blocks': '自然方块',
    'functional_blocks': '功能方块', 'tools': '工具', 'combat': '战斗',
    'food': '食物', 'materials': '材料', 'miscellaneous': '杂项',
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

def sort_key(item_id):
    MATERIAL = {'wooden': 1, 'stone': 2, 'iron': 3, 'golden': 4, 'gold': 4, 'diamond': 5, 'netherite': 6}
    for mat, order in MATERIAL.items():
        if item_id.startswith(mat + '_'): return (order, item_id)
    COLORS_ZH = {'white':0,'orange':1,'magenta':2,'light_blue':3,'yellow':4,'lime':5,'pink':6,'gray':7,'light_gray':8,'cyan':9,'purple':10,'blue':11,'brown':12,'green':13,'red':14,'black':15}
    for color, order in COLORS_ZH.items():
        if item_id.startswith(color + '_'): return (100 + order, item_id)
    WOODS_ZH = {'oak':0,'spruce':1,'birch':2,'jungle':3,'acacia':4,'dark_oak':5,'mangrove':6,'cherry':7,'pale_oak':8,'bamboo':9,'crimson':10,'warped':11}
    for wood, order in WOODS_ZH.items():
        if item_id.startswith(wood + '_'): return (400 + order, item_id)
    return (500, item_id)

tree = defaultdict(lambda: defaultdict(list))
for item in items:
    if item.get('hidden'): continue
    cat = item.get('category', 'miscellaneous')
    sub = item.get('subcategory', 'general')
    tree[cat][sub].append(item['id'])

categories = []
for cat_id in CAT_ORDER:
    if cat_id not in tree: continue
    subcats = []
    for sub_id in sorted(tree[cat_id].keys()):
        sorted_items = sorted(tree[cat_id][sub_id], key=sort_key)
        subcats.append({
            'id': sub_id, 'name_zh': SUB_NAMES.get(sub_id, sub_id),
            'name_en': sub_id.replace('_', ' ').title(), 'items': sorted_items,
        })
    icon_item = subcats[0]['items'][0] if subcats and subcats[0].get('items') else ''
    categories.append({
        'id': cat_id, 'name_zh': CAT_NAMES.get(cat_id, cat_id),
        'name_en': cat_id.replace('_', ' ').title(),
        'icon_item': icon_item, 'subcategories': subcats,
    })
data['categories'] = categories

# Save
with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# Report
# ============================================================
from collections import Counter
cat_counts = Counter(i.get('category','?') for i in items)
fb = sum(1 for i in items if i.get('zh_fallback'))
has_local = sum(1 for i in items if i.get('icon_url','').startswith('images/'))
has_sec = sum(1 for i in items if i.get('secondary_categories'))

print(f"\n{'='*50}")
print(f"=== 最终报告 ===")
print(f"总物品: {len(items)} (删除: {len(deleted)})")
print(f"中文名覆盖率: {len(items)-fb}/{len(items)} ({(len(items)-fb)/len(items)*100:.1f}%)")
print(f"本地图片: {has_local}/{len(items)} ({has_local/len(items)*100:.1f}%)")
print(f"多分类: {has_sec}")
print(f"大类: {len(categories)}")
for c in categories:
    ic = sum(len(s.get('items',[])) for s in c['subcategories'])
    print(f"  {c['name_zh']}: {ic} 物品, {len(c['subcategories'])} 子类")
print(f"data.json: {os.path.getsize(DATA_PATH)/1024:.0f} KB")
PYEOF