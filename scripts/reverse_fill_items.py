#!/usr/bin/env python3
"""
reverse_fill_items.py — 基于图片反推补全缺失物品
扫描 docs/images/ 中未录入 data.json 的图片，清洗文件名后生成物品数据。
"""
import json, os, re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / 'docs' / 'data' / 'data.json'
IMAGES_DIR = SCRIPT_DIR / 'docs' / 'images'

# ============================================================
# 文件名清洗：去除 Wiki CDN 版本后缀
# ============================================================
VERSION_PATTERNS = [
    r'_je\d+_be\d+$',    # acacia_boat_je3_be2
    r'_be\d+$',           # agent_spawn_egg_be2
    r'_je\d+$',           # amethyst_shard_je1
    r'_28[su]n?d?29$',    # acacia_log_28ud29 (URL-encoded (UD))
    r'_28\d+29$',         # acacia_sign_28029
    r'_28pre-release29$', # armadillo_scute_28pre-release29
    r'_\d+x\d+$',         # grid_3x3 (unlikely but possible)
    r'_28[sn]29$',        # activator_rail_28ns29 (NS)
    r'_\d+px$',           # some_image_32px
    r'_sm$',              # small variant
]

KNOWN_PREFIXES_TO_DROP = [
    'achievementsprite_',   # achievementsprite_bake-bread → bread
    'advancement-plain-',   # advancement-plain-raw → raw
    'invicon_',             # invicon_stone → stone (already handled by rename)
]

SPECIAL_MAPPINGS = {
    # Direct mappings for items with weird filenames
    '25w31a_shelf_priority': None,  # Snapshot indicator, not an item
    'all-paintings-1-21': None,     # Composite image
    'armor_emoji': None,            # UI element
    'arrowshotintree': None,        # Not an item
    'bake-bread': 'bread',          # Achievement icon
    'item_sprite': None,            # Sprite sheet
    'all_portal_colors': None,      # Composite
    'axes': None,                   # Composite
}

def clean_filename(filename):
    """Remove version suffixes and prefixes to get base item ID."""
    name = filename.replace('.png', '').lower()

    # Check special mappings
    if name in SPECIAL_MAPPINGS:
        return SPECIAL_MAPPINGS[name]

    # Remove known prefixes
    for prefix in KNOWN_PREFIXES_TO_DROP:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    # Remove version suffixes (try each pattern)
    changed = True
    while changed:
        changed = False
        for pattern in VERSION_PATTERNS:
            m = re.search(pattern, name)
            if m:
                name = name[:m.start()]
                changed = True

    # Clean URL-encoded chars that might remain
    name = re.sub(r'_28[^2]*29', '', name)  # Remove any remaining URL-encoded
    name = re.sub(r'%28.*?%29', '', name, flags=re.IGNORECASE)

    # Remove trailing garbage
    name = name.strip('_')

    # Skip non-items
    if len(name) < 2:
        return None

    # Skip obvious non-items
    skip_patterns = ['emoji', 'portalframe', 'paintings', 'grid_', 'sprite_',
                     'all_portal', 'crafting-table_', 'furnace_', 'chest_',
                     'banner_pattern_', 'bossbar', 'experience_orb']
    for sp in skip_patterns:
        if sp in name:
            return None

    return name


# ============================================================
# 中文名生成
# ============================================================
ZH_COLORS = {
    'white': '白色', 'orange': '橙色', 'magenta': '品红色',
    'light_blue': '淡蓝色', 'yellow': '黄色', 'lime': '黄绿色',
    'pink': '粉红色', 'gray': '灰色', 'light_gray': '淡灰色',
    'cyan': '青色', 'purple': '紫色', 'blue': '蓝色',
    'brown': '棕色', 'green': '绿色', 'red': '红色', 'black': '黑色',
}

ZH_WOODS = {
    'oak': '橡木', 'spruce': '云杉木', 'birch': '白桦木',
    'jungle': '丛林木', 'acacia': '金合欢木', 'dark_oak': '深色橡木',
    'mangrove': '红树木', 'cherry': '樱花木', 'bamboo': '竹',
    'crimson': '绯红木', 'warped': '诡异木', 'pale_oak': '苍白橡木',
}

ZH_BASES = {
    'wool': '羊毛', 'carpet': '地毯', 'bed': '床',
    'stained_glass': '染色玻璃', 'stained_glass_pane': '染色玻璃板',
    'terracotta': '陶瓦', 'glazed_terracotta': '带釉陶瓦',
    'concrete': '混凝土', 'concrete_powder': '混凝土粉末',
    'dye': '染料', 'candle': '蜡烛', 'banner': '旗帜',
    'log': '原木', 'stripped_log': '去皮原木',
    'planks': '木板', 'stairs': '楼梯', 'slab': '台阶',
    'door': '门', 'fence': '栅栏', 'fence_gate': '栅栏门',
    'trapdoor': '活板门', 'button': '按钮', 'pressure_plate': '压力板',
    'sign': '告示牌', 'hanging_sign': '悬挂式告示牌',
    'boat': '船', 'chest_boat': '运输船', 'raft': '竹筏',
    'leaves': '树叶', 'sapling': '树苗',
    'shulker_box': '潜影盒', 'bundle': '收纳袋',
    'spawn_egg': '刷怪蛋',
    'sword': '剑', 'pickaxe': '镐', 'axe': '斧', 'shovel': '锹', 'hoe': '锄',
    'helmet': '头盔', 'chestplate': '胸甲', 'leggings': '护腿', 'boots': '靴子',
    'horse_armor': '马铠',
    'music_disc': '音乐唱片',
    'boat_with_chest': '运输船',
}

# Well-known item names
ZH_KNOWN = {
    'stone': '石头', 'cobblestone': '圆石', 'stone_bricks': '石砖',
    'granite': '花岗岩', 'diorite': '闪长岩', 'andesite': '安山岩',
    'sand': '沙子', 'gravel': '沙砾', 'sandstone': '砂岩',
    'obsidian': '黑曜石', 'glass': '玻璃', 'bricks': '砖块',
    'dirt': '泥土', 'grass_block': '草方块', 'clay': '黏土块',
    'ice': '冰', 'snow': '雪', 'snow_block': '雪块',
    'crafting_table': '工作台', 'furnace': '熔炉', 'chest': '箱子',
    'iron_ingot': '铁锭', 'gold_ingot': '金锭', 'diamond': '钻石',
    'emerald': '绿宝石', 'netherite_ingot': '下界合金锭',
    'stick': '木棍', 'string': '线', 'feather': '羽毛', 'flint': '燧石',
    'leather': '皮革', 'paper': '纸', 'book': '书', 'slime_ball': '黏液球',
    'bone_meal': '骨粉', 'gunpowder': '火药', 'sugar': '糖',
    'arrow': '箭', 'bow': '弓', 'crossbow': '弩', 'shield': '盾牌',
    'apple': '苹果', 'bread': '面包', 'cookie': '曲奇', 'cake': '蛋糕',
    'carrot': '胡萝卜', 'potato': '马铃薯', 'beetroot': '甜菜根',
    'beef': '生牛肉', 'chicken': '生鸡肉', 'porkchop': '生猪排',
    'mutton': '生羊肉', 'cod': '生鳕鱼', 'salmon': '生鲑鱼',
    'cooked_beef': '牛排', 'cooked_chicken': '熟鸡肉', 'cooked_porkchop': '熟猪排',
    'cooked_mutton': '熟羊肉', 'cooked_cod': '熟鳕鱼', 'cooked_salmon': '熟鲑鱼',
    'egg': '鸡蛋', 'wheat': '小麦', 'milk_bucket': '牛奶桶',
    'torch': '火把', 'ladder': '梯子', 'rail': '铁轨',
    'tnt': 'TNT', 'piston': '活塞', 'sticky_piston': '黏性活塞',
    'hopper': '漏斗', 'dropper': '投掷器', 'dispenser': '发射器',
    'redstone': '红石粉', 'glowstone_dust': '荧石粉',
    'blaze_rod': '烈焰棒', 'ender_pearl': '末影珍珠',
    'nether_star': '下界之星', 'beacon': '信标',
    'enchanting_table': '附魔台', 'anvil': '铁砧', 'brewing_stand': '酿造台',
    'cauldron': '炼药锅', 'flower_pot': '花盆', 'painting': '画',
    'item_frame': '物品展示框', 'armor_stand': '盔甲架',
    'name_tag': '命名牌', 'lead': '拴绳', 'saddle': '鞍',
    'compass': '指南针', 'clock': '时钟', 'map': '空地图',
    'fishing_rod': '钓鱼竿', 'shears': '剪刀', 'flint_and_steel': '打火石',
    'bucket': '桶', 'water_bucket': '水桶', 'lava_bucket': '熔岩桶',
    'snowball': '雪球', 'fire_charge': '火焰弹',
    'ender_eye': '末影之眼', 'ender_chest': '末影箱',
    'enchanting_table': '附魔台', 'jukebox': '唱片机', 'note_block': '音符盒',
    'bookshelf': '书架', 'cobweb': '蜘蛛网',
    'skeleton_skull': '骷髅头颅', 'wither_skeleton_skull': '凋零骷髅头颅',
    'zombie_head': '僵尸的头', 'creeper_head': '苦力怕的头',
    'dragon_head': '龙首', 'piglin_head': '猪灵的头',
    'netherite_upgrade_smithing_template': '下界合金升级锻造模板',
    'trial_key': '试炼钥匙', 'ominous_trial_key': '不祥试炼钥匙',
    'wind_charge': '风弹', 'breeze_rod': '旋风棒',
    'heavy_core': '重质核心', 'mace': '重锤',
    'armadillo_scute': '犰狳鳞甲', 'wolf_armor': '狼铠',
    'ominous_bottle': '不祥之瓶', 'trial_spawner': '试炼刷怪笼',
    'vault': '宝库', 'crafter': '合成器',
    'copper_grate': '铜格栅', 'copper_door': '铜门', 'copper_trapdoor': '铜活板门',
    'copper_bulb': '铜灯', 'tuff_slab': '凝灰岩台阶', 'tuff_stairs': '凝灰岩楼梯',
    'polished_tuff': '磨制凝灰岩', 'chiseled_tuff': '錾制凝灰岩', 'tuff_bricks': '凝灰岩砖',
    'chiseled_copper': '錾制铜块', 'copper_grate': '铜格栅',
}


def generate_name_zh(item_id):
    """Generate Chinese name from item ID."""
    if item_id in ZH_KNOWN:
        return ZH_KNOWN[item_id]

    # Color + base pattern
    for color_en, color_zh in ZH_COLORS.items():
        if item_id.startswith(color_en + '_'):
            base = item_id[len(color_en) + 1:]
            if base in ZH_BASES:
                return color_zh + ZH_BASES[base]
            # Special: glazed_terracotta
            if base.startswith('glazed_'):
                inner = base[len('glazed_'):]
                if inner in ZH_BASES:
                    return color_zh + ZH_BASES[inner]

    # Wood + base pattern
    for wood_en, wood_zh in ZH_WOODS.items():
        if item_id.startswith(wood_en + '_'):
            base = item_id[len(wood_en) + 1:]
            if base in ZH_BASES:
                return wood_zh + ZH_BASES[base]

    # Material + equipment
    for mat, mat_zh in [('wooden','木'),('stone','石'),('iron','铁'),('golden','金'),('diamond','钻石'),('netherite','下界合金')]:
        if item_id.startswith(mat + '_'):
            base = item_id[len(mat) + 1:]
            if base in ZH_BASES:
                return mat_zh + ZH_BASES[base]

    # Leather/chainmail armor
    for mat, mat_zh in [('leather','皮革'),('chainmail','锁链')]:
        for slot, slot_zh in [('helmet','头盔'),('chestplate','胸甲'),('leggings','护腿'),('boots','靴子')]:
            if item_id == f'{mat}_{slot}':
                return mat_zh + slot_zh

    # Spawn eggs
    if item_id.endswith('_spawn_egg'):
        entity = item_id[:-10].replace('_', ' ')
        return entity.title() + '刷怪蛋'

    # Shulker boxes
    for color_en, color_zh in ZH_COLORS.items():
        if item_id == f'{color_en}_shulker_box':
            return color_zh + '潜影盒'

    # Music discs
    if item_id.startswith('music_disc_'):
        disc = item_id[len('music_disc_'):].replace('_', ' ')
        return f'音乐唱片（{disc}）'

    # Banner patterns
    if item_id.endswith('_banner_pattern'):
        pattern = item_id[:-15].replace('_', ' ')
        return pattern.title() + '旗帜图案'

    # Pottery sherds
    if item_id.endswith('_pottery_sherd'):
        name = item_id[:-14].replace('_', ' ')
        return name.title() + '纹样陶片'

    # Smithing templates
    if item_id.endswith('_smithing_template'):
        name = item_id[:-18].replace('_', ' ')
        return name.title() + '锻造模板'

    return None


def classify_item(item_id):
    """Infer category and subcategory from item ID."""
    # Blocks
    if any(item_id.endswith('_' + s) for s in ['wool','carpet','concrete','concrete_powder','terracotta','glazed_terracotta','stained_glass','stained_glass_pane']):
        return 'blocks', 'colored'
    if any(item_id.endswith('_' + s) for s in ['log','stripped_log','planks','stairs','slab','fence','fence_gate','door','trapdoor','button','pressure_plate','sign','hanging_sign']):
        return 'blocks', 'wood'
    if any(s in item_id for s in ['stone','cobblestone','granite','diorite','andesite','sandstone','deepslate','bricks','obsidian','prismarine','purpur','quartz','blackstone','basalt','tuff','calcite','copper_block','iron_block','gold_block','diamond_block','emerald_block','netherite_block','coal_block','redstone_block','lapis_block']):
        if not any(item_id.startswith(s + '_') for s in ['iron_','gold_','diamond_','netherite_']):
            return 'blocks', 'stone'
    if any(item_id.endswith('_' + s) or s in item_id for s in ['glass','glass_pane','tinted_glass']):
        return 'blocks', 'glass'
    if any(s in item_id for s in ['crafting_table','furnace','chest','ender_chest','shulker_box','barrel','hopper','dropper','dispenser','observer','piston','note_block','jukebox','beacon','enchanting_table','anvil','brewing_stand','cauldron','flower_pot','painting','item_frame','armor_stand','bookshelf','lectern','bell','scaffolding','ladder','torch','lantern','campfire','rail','tnt','slime_block','honey_block']):
        return 'blocks', 'functional'

    # Tools
    if any(item_id.endswith('_' + s) for s in ['pickaxe','axe','shovel','hoe']):
        return 'tools', 'tools'
    if item_id in ['shears','fishing_rod','flint_and_steel','compass','clock','lead','name_tag','saddle','spyglass','brush','carrot_on_a_stick','warped_fungus_on_a_stick']:
        return 'tools', 'tools'

    # Combat
    if any(item_id.endswith('_' + s) for s in ['sword','bow','crossbow']):
        return 'combat', 'weapons'
    if any(item_id.endswith('_' + s) for s in ['helmet','chestplate','leggings','boots','horse_armor']):
        return 'combat', 'armor'
    if item_id in ['shield','arrow','spectral_arrow','tipped_arrow','trident','mace','totem_of_undying','wolf_armor']:
        return 'combat', 'weapons'

    # Food
    if any(s in item_id for s in ['apple','bread','cookie','cake','pie','stew','soup','beetroot','carrot','potato','beef','chicken','porkchop','mutton','rabbit','cod','salmon','tropical_fish','pufferfish','dried_kelp','honey_bottle','chorus_fruit','berry','glow_berry','melon']):
        return 'food', 'food'
    if item_id.startswith('cooked_') or item_id.startswith('golden_carrot') or item_id.startswith('golden_apple') or item_id.startswith('enchanted_golden_apple'):
        return 'food', 'food'

    # Materials
    if any(item_id.endswith('_' + s) for s in ['ingot','nugget','gem']):
        return 'materials', 'ingredients'
    if any(s in item_id for s in ['coal','charcoal','diamond','emerald','quartz','lapis','raw_iron','raw_gold','raw_copper','netherite_scrap']):
        if not any(item_id.startswith(s + '_') for s in ['coal_','diamond_']):
            return 'materials', 'ingredients'
    if any(item_id.endswith('_' + s) for s in ['dye','dust','shard','crystal','tear','pearl','star','shell','scute']):
        return 'materials', 'ingredients'
    if item_id in ['stick','string','feather','flint','leather','paper','book','slime_ball','honeycomb','bone_meal','gunpowder','sugar','clay_ball','brick','nether_brick','blaze_rod','blaze_powder','ghast_tear','magma_cream','spider_eye','fermented_spider_eye','phantom_membrane','rabbit_foot','rabbit_hide','turtle_scute','armadillo_scute','echo_shard','nautilus_shell','heart_of_the_sea','prismarine_shard','prismarine_crystals','shulker_shell','nether_wart','glow_ink_sac','ink_sac','fire_charge','firework_rocket','firework_star','experience_bottle','enchanted_book','goat_horn','wind_charge','breeze_rod','heavy_core','ominous_bottle']:
        return 'materials', 'ingredients'

    # Items - music discs
    if item_id.startswith('music_disc_'):
        return 'items', 'music_discs'
    # Items - spawn eggs
    if item_id.endswith('_spawn_egg'):
        return 'items', 'spawn_eggs'
    # Items - boats
    if item_id.endswith('_boat') or item_id.endswith('_chest_boat') or item_id.endswith('_raft'):
        return 'items', 'transport'
    # Items - banner patterns
    if item_id.endswith('_banner_pattern') or item_id.endswith('_pottery_sherd') or item_id.endswith('_smithing_template'):
        return 'items', 'misc'
    # Items - potions
    if 'potion' in item_id:
        return 'items', 'potions'

    # Default
    return 'items', 'misc'


def main():
    print('=' * 60)
    print('Reverse Fill: 从图片反推补全物品')
    print('=' * 60)

    # Load data
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    existing_ids = {i['id'] for i in data['items']}

    # Scan images
    img_files = [f for f in os.listdir(IMAGES_DIR)
                 if f.endswith('.png') and os.path.getsize(os.path.join(IMAGES_DIR, f)) > 100]

    # Clean filenames → candidate item IDs
    candidates = {}
    skipped = []
    for f in img_files:
        cid = clean_filename(f)
        if cid and cid not in existing_ids:
            if cid not in candidates:
                candidates[cid] = f
        elif cid is None and f not in ['placeholder.png']:
            if not any(f.startswith(s) for s in ['all-','grid_','sprite_','emoji','paintings_']):
                skipped.append(f)

    print(f'\nImages scanned: {len(img_files)}')
    print(f'Existing items: {len(existing_ids)}')
    print(f'Candidate new IDs: {len(candidates)}')
    print(f'Skipped (composite/UI): {len(skipped)}')

    # Generate items
    added = []
    unable_to_name = []

    for cid in sorted(candidates.keys()):
        name_zh = generate_name_zh(cid)
        cat, sub = classify_item(cid)

        if not name_zh:
            unable_to_name.append(cid)
            continue

        item = {
            'id': cid,
            'name_zh': name_zh,
            'name_en': cid.replace('_', ' ').title(),
            'category': cat,
            'subcategory': sub,
            'icon_url': f'images/{cid}.png',
            'acquisition': {
                'methods': ['未知'],
                'natural_generation': [],
                'smelting': [],
                'trading': None,
                'drops_from': [],
            },
            'crafting': [],
            'stonecutting': None,
            'smithing': None,
            'related_items': [],
            'source': 'image_reverse',
        }
        data['items'].append(item)
        added.append(cid)

    data['meta']['total_items'] = len(data['items'])

    # Save
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    print(f'\n=== Results ===')
    print(f'Items added: {len(added)}')
    print(f'Total items now: {len(data["items"])}')
    print(f'Unable to name: {len(unable_to_name)}')

    if len(unable_to_name) <= 50:
        print(f'\nUnable to name:')
        for u in sorted(unable_to_name):
            print(f'  {u}')

    # Stats
    cats = {}
    for i in data['items']:
        c = i.get('category', '?')
        cats[c] = cats.get(c, 0) + 1
    print(f'\nCategory distribution:')
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f'  {c}: {n}')

    print(f'\nData file: {os.path.getsize(DATA_PATH) / 1024:.0f} KB')


if __name__ == '__main__':
    main()
