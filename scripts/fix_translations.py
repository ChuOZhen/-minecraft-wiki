#!/usr/bin/env python3
"""fix_translations.py — 修正官方中文翻译：后缀/颜色前缀/药水/物品名"""
import json, os, shutil, re

DATA_PATH = 'docs/data/data.json'
shutil.copy(DATA_PATH, 'docs/data/data_backup_translation_fix.json')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']
item_map = {i['id']: i for i in items}

fixes = 0

# ============================================================
# 【1】Stone/Brick 后缀修正 (slab/stairs/wall)
# ============================================================
STONE_FIXES = {
    # Stone base
    'stone_slab': '石头台阶', 'stone_stairs': '石头楼梯',
    'stone_brick_slab': '石砖台阶', 'stone_brick_stairs': '石砖楼梯', 'stone_brick_wall': '石砖墙',
    'mossy_stone_brick_slab': '苔石砖台阶', 'mossy_stone_brick_stairs': '苔石砖楼梯', 'mossy_stone_brick_wall': '苔石砖墙',
    'mossy_cobblestone_slab': '苔石台阶', 'mossy_cobblestone_stairs': '苔石楼梯', 'mossy_cobblestone_wall': '苔石墙',
    # Cobblestone
    'cobblestone_slab': '圆石台阶', 'cobblestone_stairs': '圆石楼梯', 'cobblestone_wall': '圆石墙',
    # Deepslate
    'cobbled_deepslate_slab': '深板岩圆石台阶', 'cobbled_deepslate_stairs': '深板岩圆石楼梯', 'cobbled_deepslate_wall': '深板岩圆石墙',
    'deepslate_brick_slab': '深板岩砖台阶', 'deepslate_brick_stairs': '深板岩砖楼梯', 'deepslate_brick_wall': '深板岩砖墙',
    'deepslate_tile_slab': '深板岩瓦台阶', 'deepslate_tile_stairs': '深板岩瓦楼梯', 'deepslate_tile_wall': '深板岩瓦墙',
    'polished_deepslate_slab': '磨制深板岩台阶', 'polished_deepslate_stairs': '磨制深板岩楼梯', 'polished_deepslate_wall': '磨制深板岩墙',
    # Andesite
    'andesite_slab': '安山岩台阶', 'andesite_stairs': '安山岩楼梯', 'andesite_wall': '安山岩墙',
    # Diorite
    'diorite_slab': '闪长岩台阶', 'diorite_stairs': '闪长岩楼梯', 'diorite_wall': '闪长岩墙',
    'polished_diorite_slab': '磨制闪长岩台阶', 'polished_diorite_stairs': '磨制闪长岩楼梯',
    # Granite
    'granite_slab': '花岗岩台阶', 'granite_stairs': '花岗岩楼梯', 'granite_wall': '花岗岩墙',
    'polished_granite_slab': '磨制花岗岩台阶', 'polished_granite_stairs': '磨制花岗岩楼梯',
    # Andesite
    'polished_andesite_slab': '磨制安山岩台阶', 'polished_andesite_stairs': '磨制安山岩楼梯',
    # Brick
    'brick_slab': '红砖台阶', 'brick_stairs': '红砖楼梯', 'brick_wall': '红砖墙',
    # Mud brick
    'mud_brick_slab': '泥砖台阶', 'mud_brick_stairs': '泥砖楼梯', 'mud_brick_wall': '泥砖墙',
    # End stone
    'end_stone_brick_slab': '末地石砖台阶', 'end_stone_brick_stairs': '末地石砖楼梯', 'end_stone_brick_wall': '末地石砖墙',
    # Prismarine
    'prismarine_slab': '海晶石台阶', 'prismarine_stairs': '海晶石楼梯', 'prismarine_wall': '海晶石墙',
    'prismarine_brick_slab': '海晶石砖台阶', 'prismarine_brick_stairs': '海晶石砖楼梯',
    'dark_prismarine_slab': '暗海晶石台阶', 'dark_prismarine_stairs': '暗海晶石楼梯',
    # Quartz
    'quartz_slab': '石英台阶', 'quartz_stairs': '石英楼梯',
    'smooth_quartz_slab': '平滑石英台阶', 'smooth_quartz_stairs': '平滑石英楼梯',
    # Blackstone
    'blackstone_slab': '黑石台阶', 'blackstone_stairs': '黑石楼梯', 'blackstone_wall': '黑石墙',
    'polished_blackstone_slab': '磨制黑石台阶', 'polished_blackstone_stairs': '磨制黑石楼梯', 'polished_blackstone_wall': '磨制黑石墙',
    'polished_blackstone_brick_slab': '磨制黑石砖台阶', 'polished_blackstone_brick_stairs': '磨制黑石砖楼梯', 'polished_blackstone_brick_wall': '磨制黑石砖墙',
    # Sandstone
    'sandstone_slab': '砂岩台阶', 'sandstone_stairs': '砂岩楼梯', 'sandstone_wall': '砂岩墙',
    'red_sandstone_slab': '红砂岩台阶', 'red_sandstone_stairs': '红砂岩楼梯', 'red_sandstone_wall': '红砂岩墙',
    'smooth_sandstone_slab': '平滑砂岩台阶', 'smooth_sandstone_stairs': '平滑砂岩楼梯',
    'smooth_red_sandstone_slab': '平滑红砂岩台阶', 'smooth_red_sandstone_stairs': '平滑红砂岩楼梯',
    'cut_sandstone_slab': '切制砂岩台阶',
    'cut_red_sandstone_slab': '切制红砂岩台阶',
    # Nether brick
    'nether_brick_slab': '下界砖台阶', 'nether_brick_stairs': '下界砖楼梯', 'nether_brick_wall': '下界砖墙',
    'red_nether_brick_slab': '红色下界砖台阶', 'red_nether_brick_stairs': '红色下界砖楼梯', 'red_nether_brick_wall': '红色下界砖墙',
    # Tuff
    'tuff_slab': '凝灰岩台阶', 'tuff_stairs': '凝灰岩楼梯', 'tuff_wall': '凝灰岩墙',
    'tuff_brick_slab': '凝灰岩砖台阶', 'tuff_brick_stairs': '凝灰岩砖楼梯', 'tuff_brick_wall': '凝灰岩砖墙',
    'polished_tuff_slab': '磨制凝灰岩台阶', 'polished_tuff_stairs': '磨制凝灰岩楼梯', 'polished_tuff_wall': '磨制凝灰岩墙',
    'chiseled_tuff': '錾制凝灰岩', 'chiseled_tuff_bricks': '錾制凝灰岩砖',
    # Purpur
    'purpur_slab': '紫珀台阶', 'purpur_stairs': '紫珀楼梯',
    # Resin brick
    'resin_brick_slab': '树脂砖台阶', 'resin_brick_stairs': '树脂砖楼梯', 'resin_brick_wall': '树脂砖墙',
    'chiseled_resin_bricks': '錾制树脂砖',
    # Other
    'cut_copper_slab': '切制铜台阶', 'cut_copper_stairs': '切制铜楼梯',
    'exposed_cut_copper_slab': '斑驳切制铜台阶', 'exposed_cut_copper_stairs': '斑驳切制铜楼梯',
    'weathered_cut_copper_slab': '锈蚀切制铜台阶', 'weathered_cut_copper_stairs': '锈蚀切制铜楼梯',
    'oxidized_cut_copper_slab': '氧化切制铜台阶', 'oxidized_cut_copper_stairs': '氧化切制铜楼梯',
}

for iid, zh in STONE_FIXES.items():
    if iid in item_map:
        item_map[iid]['name_zh'] = zh
        item_map[iid]['zh_fallback'] = False
        fixes += 1

print(f"Stone/brick suffix fixes: {fixes}")
stone_fixes = fixes

# ============================================================
# 【2】Wood item fixes
# ============================================================
WOOD_FIXES = {
    'oak_door': '橡木门', 'oak_fence': '橡木栅栏', 'oak_slab': '橡木台阶', 'oak_stairs': '橡木楼梯',
    'spruce_door': '云杉木门', 'spruce_fence': '云杉木栅栏',
    'birch_door': '白桦木门', 'birch_fence': '白桦木栅栏',
    'jungle_door': '丛林木门', 'jungle_fence': '丛林木栅栏',
    'acacia_door': '金合欢木门', 'acacia_fence': '金合欢木栅栏',
    'dark_oak_door': '深色橡木门', 'dark_oak_fence': '深色橡木栅栏',
    'mangrove_door': '红树木门', 'mangrove_fence': '红树木栅栏',
    'cherry_door': '樱花木门', 'cherry_fence': '樱花木栅栏',
    'pale_oak_door': '苍白橡木门', 'pale_oak_fence': '苍白橡木栅栏',
    'bamboo_door': '竹门', 'bamboo_fence': '竹栅栏',
    'crimson_door': '绯红木门', 'crimson_fence': '绯红木栅栏',
    'warped_door': '诡异木门', 'warped_fence': '诡异木栅栏',
    'mangrove_propagule': '红树胎生苗',
}

w = 0
for iid, zh in WOOD_FIXES.items():
    if iid in item_map:
        item_map[iid]['name_zh'] = zh
        item_map[iid]['zh_fallback'] = False
        w += 1
fixes += w
print(f"Wood fixes: {w}")

# ============================================================
# 【3】Natural block fixes
# ============================================================
NATURAL_FIXES = {
    'bee_nest': '蜂巢',
    'block_of_raw_copper': '粗铜块',
    'block_of_raw_gold': '粗金块',
    'block_of_raw_iron': '粗铁块',
    'infested_block': '虫蚀方块（通用）',
    'cherry_stripped_log': '去皮樱花木原木',
    'bamboo_stripped_log': '去皮竹原木',
    'pale_oak_stripped_log': '去皮苍白橡木原木',
    'ocelot_spawn_egg': '豹猫刷怪蛋',
}

n = 0
for iid, zh in NATURAL_FIXES.items():
    if iid in item_map:
        item_map[iid]['name_zh'] = zh
        item_map[iid]['zh_fallback'] = False
        n += 1
fixes += n
print(f"Natural fixes: {n}")

# ============================================================
# 【4】Combat fixes
# ============================================================
COMBAT_FIXES = {
    'nautilus_armor': '鹦鹉螺盔甲',
    'iron_nautilus_armor': '铁鹦鹉螺盔甲',
    'golden_nautilus_armor': '金鹦鹉螺盔甲',
    'leather_cap': '皮革帽子',
    'leather_tunic': '皮革外套',
    'leather_pants': '皮革裤子',
    'leather_boots': '皮革靴子',
    'leather_helmet': '皮革头盔',
    'leather_chestplate': '皮革胸甲',
    'leather_leggings': '皮革护腿',
    'chainmail_helmet': '锁链头盔',
    'chainmail_chestplate': '锁链胸甲',
    'chainmail_leggings': '锁链护腿',
    'chainmail_boots': '锁链靴子',
    'crossbow': '弩',
    'wither_skeleton_spawn_egg': '凋灵骷髅刷怪蛋',
    'tnt': 'TNT',
}

c = 0
for iid, zh in COMBAT_FIXES.items():
    if iid in item_map:
        item_map[iid]['name_zh'] = zh
        item_map[iid]['zh_fallback'] = False
        c += 1
fixes += c
print(f"Combat fixes: {c}")

# ============================================================
# 【5】Food/Misc fixes
# ============================================================
FOOD_FIXES = {
    'bamboo_raft': '竹筏',
    'boat_with_chest': '运输船',
    'obsidian_boat': '黑曜石船',
    'slimeball': '黏液球',
    'steak': '牛排',
    'prismarine_crystals': '海晶砂粒',
    'prismarine_shard': '海晶碎片',
    'prismarine_crystal': '海晶砂粒',
    'golden_apple': '金苹果',
    'enchanted_golden_apple': '附魔金苹果',
    'xp_bottle': '附魔之瓶',
    'dragon_breath': '龙息',
    'fermented_spider_eye': '发酵蛛眼',
    'spider_eye': '蜘蛛眼',
    'glow_berries': '发光浆果',
    'sweet_berries': '甜浆果',
    'honey_bottle': '蜂蜜瓶',
}

f = 0
for iid, zh in FOOD_FIXES.items():
    if iid in item_map:
        item_map[iid]['name_zh'] = zh
        item_map[iid]['zh_fallback'] = False
        f += 1
fixes += f
print(f"Food/Misc fixes: {f}")

# ============================================================
# 【6】Potion naming - FULL fix
# ============================================================
EFFECT_ZH = {
    'fire_resistance': '抗火', 'healing': '治疗', 'harming': '伤害',
    'invisibility': '隐身', 'leaping': '跳跃', 'night_vision': '夜视',
    'poison': '剧毒', 'regeneration': '再生', 'slow_falling': '缓降',
    'slowness': '缓慢', 'strength': '力量', 'swiftness': '迅捷',
    'turtle_master': '神龟', 'water_breathing': '水肺', 'weakness': '虚弱',
    'decay': '衰变', 'infested': '寄生', 'oozing': '渗浆',
    'weaving': '盘丝', 'wind_charged': '蓄风', 'luck': '幸运',
    'strong_poison': '剧毒', 'strong_harming': '伤害', 'strong_healing': '治疗',
    'strong_regeneration': '再生', 'strong_strength': '力量', 'strong_swiftness': '迅捷',
    'strong_leaping': '跳跃', 'strong_slowness': '缓慢', 'strong_turtle_master': '神龟',
}
MOD_ZH = {'long': '长效', 'strong': '强效'}

p = 0
for item in items:
    iid = item['id']
    name_zh = item.get('name_zh', '')

    # Check if potion name has English words
    has_eng = bool(re.search(r'[A-Z][a-z]', name_zh))
    if not has_eng:
        continue

    # lingering_potion_of_long_fire_resistance → 长效抗火滞留药水
    match = re.match(r'(lingering|splash|potion)_of_(long_|strong_)?(.+)', iid)
    if not match:
        match = re.match(r'(lingering_potion|splash_potion|potion)_of_(long_|strong_)?(.+)', iid)
    if not match:
        continue

    pfx = match.group(1)
    mod = match.group(2) or ''
    eff = match.group(3) if not mod else match.group(3)

    # Clean up prefix
    if pfx == 'lingering_potion' or pfx == 'lingering':
        pfx_zh = '滞留型'
    elif pfx == 'splash_potion' or pfx == 'splash':
        pfx_zh = '喷溅型'
    else:
        pfx_zh = ''

    # Clean modifier
    mod_zh = ''
    clean_eff = eff
    for mkey, mval in MOD_ZH.items():
        if eff.startswith(mkey + '_'):
            clean_eff = eff[len(mkey)+1:]
            mod_zh = mval
            break

    if clean_eff in EFFECT_ZH:
        eff_zh = EFFECT_ZH[clean_eff]
        if mod_zh:
            if pfx_zh:
                item['name_zh'] = f'{mod_zh}{eff_zh}{pfx_zh}药水'
            else:
                item['name_zh'] = f'{mod_zh}{eff_zh}药水'
        else:
            if pfx_zh:
                item['name_zh'] = f'{pfx_zh}{eff_zh}药水'
            else:
                item['name_zh'] = f'{eff_zh}药水'
        item['zh_fallback'] = False
        p += 1

fixes += p
print(f"Potion fixes: {p}")

# ============================================================
# 【7】Colored blocks - apply color prefix
# ============================================================
COLORS_ZH = {
    'white': '白色', 'orange': '橙色', 'magenta': '品红色', 'light_blue': '淡蓝色',
    'yellow': '黄色', 'lime': '黄绿色', 'pink': '粉色', 'gray': '灰色',
    'light_gray': '淡灰色', 'cyan': '青色', 'purple': '紫色', 'blue': '蓝色',
    'brown': '棕色', 'green': '绿色', 'red': '红色', 'black': '黑色',
}
COLORED_TYPES = {
    'wool': '羊毛', 'carpet': '地毯', 'concrete': '混凝土',
    'concrete_powder': '混凝土粉末', 'terracotta': '陶瓦',
    'glazed_terracotta': '带釉陶瓦', 'stained_glass': '染色玻璃',
    'stained_glass_pane': '染色玻璃板', 'bed': '床',
    'candle': '蜡烛', 'shulker_box': '潜影盒', 'banner': '旗帜',
    'bundle': '束口袋',
}

clr = 0
for item in items:
    iid = item['id']
    if item.get('category') != 'colored_blocks':
        continue
    for color_en, color_zh in COLORS_ZH.items():
        if iid.startswith(f'{color_en}_'):
            suffix = iid[len(color_en)+1:]
            if suffix in COLORED_TYPES:
                expected = color_zh + COLORED_TYPES[suffix]
                if item.get('name_zh') != expected:
                    item['name_zh'] = expected
                    item['zh_fallback'] = False
                    clr += 1
            break

fixes += clr
print(f"Colored prefix fixes: {clr}")

# ============================================================
# 【8】Boat naming
# ============================================================
for wood_en, wood_zh in [('oak','橡木'),('spruce','云杉'),('birch','白桦'),('jungle','丛林'),
    ('acacia','金合欢'),('dark_oak','深色橡木'),('mangrove','红树'),('cherry','樱花'),('pale_oak','苍白橡木')]:
    for suffix, suffix_zh in [('_boat_with_chest','运输船'),('_boat','船')]:
        iid = f'{wood_en}{suffix}'
        expected = wood_zh + suffix_zh
        if iid in item_map and item_map[iid].get('name_zh') != expected:
            item_map[iid]['name_zh'] = expected
            item_map[iid]['zh_fallback'] = False
            fixes += 1

# ============================================================
# 【9】Handle duplicates
# ============================================================
# Merge slime_ball → slimeball (keep slimeball as canonical)
# cooked_beef vs steak → keep both, they ARE different (生牛肉vs牛排)
# bucket_of_axolotl → axolotl_bucket (keep axolotl_bucket)
DUPLICATE_MERGE = [
    ('slime_ball', 'slimeball', '黏液球'),
    ('bucket_of_axolotl', 'axolotl_bucket', '美西螈桶'),
    ('bucket_of_pufferfish', 'pufferfish_bucket', '河豚桶'),
    ('bucket_of_salmon', 'salmon_bucket', '鲑鱼桶'),
    ('bucket_of_cod', 'cod_bucket', '鳕鱼桶'),
    ('bucket_of_tropical_fish', 'tropical_fish_bucket', '热带鱼桶'),
    ('bucket_of_tadpole', 'tadpole_bucket', '蝌蚪桶'),
]
dup_merged = 0
for old_id, keep_id, zh_name in DUPLICATE_MERGE:
    if old_id in item_map and keep_id in item_map:
        # Keep the one with better data
        old_item = item_map[old_id]
        keep_item = item_map[keep_id]
        # Merge crafting data
        if not keep_item.get('crafting') and old_item.get('crafting'):
            keep_item['crafting'] = old_item['crafting']
        keep_item['name_zh'] = zh_name
        keep_item['zh_fallback'] = False
        del item_map[old_id]
        dup_merged += 1

print(f"Duplicates merged: {dup_merged}")

# ============================================================
# 【10】Clean up ID: 'slowness' → check if it's a real item
# ============================================================
# Remove invalid items
INVALID_IDS = {'slowness', 'fire_resistance', 'invisibility', 'leaping',
    'night_vision', 'water_breathing', 'weaving', 'oozing', 'infested',
    'wind_charged', 'turtle_master', 'swiftness', 'weakness', 'strength',
    'slow_falling', 'poison'}
# These are effect IDs, not items. The real items are potion_of_*.
removed_invalid = 0
for iid in INVALID_IDS:
    if iid in item_map:
        del item_map[iid]
        removed_invalid += 1
print(f"Invalid effect-as-item removed: {removed_invalid}")

# ============================================================
# Rebuild items list + categories
# ============================================================
items = list(item_map.values())
data['items'] = items
data['meta']['total_items'] = len(items)

# Rebuild categories
from collections import defaultdict, Counter
CAT_ORDER = ['building_blocks','colored_blocks','natural_blocks','functional_blocks',
    'tools','combat','food','materials','miscellaneous']
CAT_NAMES = {
    'building_blocks':'建筑方块','colored_blocks':'彩色方块','natural_blocks':'自然方块',
    'functional_blocks':'功能方块','tools':'工具','combat':'战斗',
    'food':'食物','materials':'材料','miscellaneous':'杂项',
}
SUB_NAMES = {
    'stone':'石类','wood':'木材','bricks':'砖类','ore':'矿石','metal':'金属块',
    'sand':'沙类','dirt':'泥土类','ice':'冰雪类','glass':'玻璃类','end':'末地类',
    'nether':'下界类','ocean':'海洋类','other_building':'其他建筑',
    'wool':'羊毛','carpet':'地毯','concrete':'混凝土','concrete_powder':'混凝土粉末',
    'terracotta':'陶瓦','glazed_terracotta':'带釉陶瓦','stained_glass':'染色玻璃',
    'stained_glass_pane':'染色玻璃板','bed':'床','candle':'蜡烛','shulker_box':'潜影盒','banner':'旗帜',
    'vegetation':'植被','leaves':'树叶','sapling':'树苗','mushroom':'菌类',
    'flower':'花','crop':'农作物','wood_natural':'自然木材','natural_other':'其他自然',
    'workstation':'工作台','storage':'存储','enchanting':'附魔','light':'光源',
    'door_trapdoor':'门与活板门','rail':'铁轨','utility':'实用功能','technical':'技术方块',
    'power':'电源','transmission':'传输','action':'执行','minecart':'矿车','door_redstone':'红石门',
    'pickaxe':'镐','axe':'斧','shovel':'锹','hoe':'锄','fishing':'钓鱼',
    'utility_tool':'实用工具','ranged':'远程',
    'sword':'剑','axe_combat':'战斧','helmet':'头盔','chestplate':'胸甲',
    'leggings':'护腿','boots':'靴子','shield':'盾牌','horse_armor':'马铠',
    'meat':'肉类','fish':'鱼类','crop_food':'农作物食物','effect_food':'特效食物',
    'drink':'饮品','ingredient_food':'食材',
    'ingot':'锭','gem':'宝石','dye':'染料','mineral':'矿物原料',
    'mob_drop':'生物掉落','craft_material':'合成材料','spawn_egg':'刷怪蛋',
    'music_disc':'音乐唱片','other_material':'其他材料',
    'banner_pattern_item':'旗帜图案','pottery_sherd_item':'陶片',
    'smithing_template':'锻造模板','music_disc_item':'唱片',
    'boat':'船','minecart_item':'矿车物品','painting':'画',
    'item_frame':'物品展示框','pot':'饰纹陶罐','armor_stand':'盔甲架','hidden_misc':'隐藏杂项',
}

def sort_key(iid):
    MAT = {'wooden':1,'stone':2,'iron':3,'golden':4,'gold':4,'diamond':5,'netherite':6}
    for m,o in MAT.items():
        if iid.startswith(m+'_'): return (o,iid)
    CO = {c:i for i,c in enumerate(COLORS_ZH.keys())}
    for c,o in CO.items():
        if iid.startswith(c+'_'): return (100+o,iid)
    WO = {w:i for i,w in enumerate(['oak','spruce','birch','jungle','acacia','dark_oak','mangrove','cherry','pale_oak','bamboo','crimson','warped'])}
    for w,o in WO.items():
        if iid.startswith(w+'_'): return (400+o,iid)
    return (500,iid)

tree = defaultdict(lambda: defaultdict(list))
for item in items:
    if item.get('hidden'): continue
    cat = item.get('category','miscellaneous')
    sub = item.get('subcategory','general')
    tree[cat][sub].append(item['id'])

categories = []
for cat_id in CAT_ORDER:
    if cat_id not in tree: continue
    subcats = []
    for sub_id in sorted(tree[cat_id].keys()):
        s_items = sorted(tree[cat_id][sub_id], key=sort_key)
        subcats.append({'id':sub_id,'name_zh':SUB_NAMES.get(sub_id,sub_id),
            'name_en':sub_id.replace('_',' ').title(),'items':s_items})
    icon = subcats[0]['items'][0] if subcats and subcats[0].get('items') else ''
    categories.append({'id':cat_id,'name_zh':CAT_NAMES.get(cat_id,cat_id),
        'name_en':cat_id.replace('_',' ').title(),'icon_item':icon,'subcategories':subcats})
data['categories'] = categories

# Save
data['meta']['generated_at'] = '2026-05-05-translation-fix'
with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Final stats
fb = sum(1 for i in items if i.get('zh_fallback'))
total = len(items)
print(f"\n=== Final ===")
print(f"Total fixes: {fixes}")
print(f"Duplicates merged: {dup_merged}")
print(f"Invalid removed: {removed_invalid}")
print(f"Items: {total}")
print(f"zh_fallback: {fb}")
print(f"Coverage: {(total-fb)/total*100:.1f}%")
print(f"Size: {os.path.getsize(DATA_PATH)/1024:.0f} KB")
PYEOF