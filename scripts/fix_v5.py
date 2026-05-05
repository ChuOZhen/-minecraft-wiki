#!/usr/bin/env python3
"""
fix_v5.py — V5: 合并红石大类 + 修复中文名 ≥95%
按 agent_prompt_v5.md 规格执行
"""
import json, os, shutil, re, time
from pathlib import Path
from collections import Counter, defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / 'docs' / 'data' / 'data.json'
API_KEY = "sk-76594786aa964c729d170f418db1d70a"
API_URL = "https://api.deepseek.com/v1/chat/completions"

# ============================================================
# P1: 硬编码映射表
# ============================================================
FALLBACK_FIX_MAP = {
    "axe": "斧", "hoe": "锄", "pickaxe": "镐", "shovel": "锹",
    "wooden_axe": "木斧", "wooden_hoe": "木锄", "wooden_pickaxe": "木镐", "wooden_shovel": "木锹",
    "stone_axe": "石斧", "stone_hoe": "石锄", "stone_pickaxe": "石镐", "stone_shovel": "石锹",
    "iron_axe": "铁斧", "iron_hoe": "铁锄", "iron_pickaxe": "铁镐", "iron_shovel": "铁锹",
    "golden_axe": "金斧", "golden_hoe": "金锄", "golden_pickaxe": "金镐", "golden_shovel": "金锹",
    "diamond_axe": "钻石斧", "diamond_hoe": "钻石锄", "diamond_pickaxe": "钻石镐", "diamond_shovel": "钻石锹",
    "netherite_axe": "下界合金斧", "netherite_hoe": "下界合金锄", "netherite_pickaxe": "下界合金镐", "netherite_shovel": "下界合金锹",
    "sword": "剑", "boots": "靴子", "helmet": "头盔", "chestplate": "胸甲", "leggings": "护腿",
    "wooden_sword": "木剑", "stone_sword": "石剑", "iron_sword": "铁剑",
    "golden_sword": "金剑", "diamond_sword": "钻石剑", "netherite_sword": "下界合金剑",
    "leather_helmet": "皮革头盔", "leather_chestplate": "皮革胸甲", "leather_leggings": "皮革护腿", "leather_boots": "皮革靴子",
    "chainmail_helmet": "锁链头盔", "chainmail_chestplate": "锁链胸甲", "chainmail_leggings": "锁链护腿", "chainmail_boots": "锁链靴子",
    "iron_helmet": "铁头盔", "iron_chestplate": "铁胸甲", "iron_leggings": "铁护腿", "iron_boots": "铁靴子",
    "golden_helmet": "金头盔", "golden_chestplate": "金胸甲", "golden_leggings": "金护腿", "golden_boots": "金靴子",
    "diamond_helmet": "钻石头盔", "diamond_chestplate": "钻石胸甲", "diamond_leggings": "钻石护腿", "diamond_boots": "钻石靴子",
    "netherite_helmet": "下界合金头盔", "netherite_chestplate": "下界合金胸甲", "netherite_leggings": "下界合金护腿", "netherite_boots": "下界合金靴子",
    "turtle_helmet": "海龟壳",
    "leather_horse_armor": "皮革马铠", "iron_horse_armor": "铁马铠", "golden_horse_armor": "金马铠", "diamond_horse_armor": "钻石马铠",
    "beehive": "蜂箱", "composter": "堆肥桶", "scaffolding": "脚手架",
    "loom": "织布机", "grindstone": "砂轮", "cartography_table": "制图台",
    "fletching_table": "制箭台", "smithing_table": "锻造台", "stonecutter": "切石机",
    "brewing_stand": "酿造台", "cauldron": "炼药锅", "bell": "钟",
    "jukebox": "唱片机", "lodestone": "磁石", "respawn_anchor": "重生锚",
    "ender_chest": "末影箱", "barrel": "木桶", "blast_furnace": "高炉", "smoker": "烟熏炉",
    "copper": "铜锭", "copper_nugget": "铜粒", "amethyst": "紫水晶",
    "netherite_scrap": "下界合金碎片", "echo_shard": "回响碎片",
    "armadillo_scute": "犰狳鳞甲", "breeze_rod": "旋风棒", "heavy_core": "重质核心",
    "ominous_bottle": "不祥之瓶", "ominous_trial_key": "不祥试炼钥匙",
    "acacia": "金合欢树苗", "birch": "白桦树苗", "spruce": "云杉树苗",
    "jungle": "丛林树苗", "dark_oak": "深色橡树苗",
    "cherry": "樱花树苗", "mangrove": "红树胎生苗", "pale_oak": "苍白橡树苗",
    "azalea": "杜鹃花丛", "flowering_azalea": "盛开的杜鹃花丛",
    "bamboo": "竹子", "cactus": "仙人掌",
    "sunflower": "向日葵", "lilac": "丁香", "peony": "牡丹",
    "rose_bush": "玫瑰丛", "pitcher_plant": "瓶子草", "torchflower": "火把花",
    "eyeblossom": "眼眸花", "open_eyeblossom": "盛开的眼眸花",
    "spore_blossom": "孢子花", "hanging_roots": "垂根",
    "glow_lichen": "发光地衣", "moss_carpet": "苔藓地毯",
    "small_dripleaf": "小型垂滴叶", "big_dripleaf": "大型垂滴叶",
    "sea_pickle": "海泡菜", "kelp": "海带", "seagrass": "海草",
    "crimson_fungus": "绯红菌", "warped_fungus": "诡异菌",
    "crimson_roots": "绯红菌索", "warped_roots": "诡异菌索",
    "nether_sprouts": "下界苗", "weeping_vines": "垂泪藤", "twisting_vines": "缠怨藤",
    "shroomlight": "菌光体", "sweet_berry_bush": "甜浆果丛",
    "chorus_flower": "紫颂花", "chorus_plant": "紫颂植株",
    "brown_mushroom_block": "棕色蘑菇方块", "red_mushroom_block": "红色蘑菇方块",
    "mushroom_stem": "蘑菇柄",
    "baked_potato": "烤马铃薯", "beetroot_soup": "甜菜汤", "mushroom_stew": "蘑菇煲",
    "rabbit_stew": "兔肉煲", "dried_kelp": "干海带",
    "popped_chorus_fruit": "爆裂紫颂果",
    "suspicious_stew": "迷之炖菜", "honey_bottle": "蜂蜜瓶",
    "pumpkin_pie": "南瓜派", "cookie": "曲奇",
    "beef": "生牛肉", "cooked_beef": "熟牛肉",
    "porkchop": "生猪排", "cooked_porkchop": "熟猪排",
    "mutton": "生羊肉", "cooked_mutton": "熟羊肉",
    "chicken": "生鸡肉", "cooked_chicken": "熟鸡肉",
    "rabbit": "生兔肉", "cooked_rabbit": "熟兔肉",
    "cod": "生鳕鱼", "cooked_cod": "熟鳕鱼",
    "salmon": "生鲑鱼", "cooked_salmon": "熟鲑鱼",
    "tropical_fish": "热带鱼", "pufferfish": "河豚",
    "rotten_flesh": "腐肉", "spider_eye": "蜘蛛眼",
    "glow_berries": "发光浆果", "sweet_berries": "甜浆果",
    "wheat_seeds": "小麦种子", "pumpkin_seeds": "南瓜种子",
    "melon_seeds": "西瓜种子", "beetroot_seeds": "甜菜种子",
    "torchflower_seeds": "火把花种子", "pitcher_pod": "瓶子草荚果",
    "cocoa_beans": "可可豆", "nether_wart": "下界疣",
    "banners": "旗帜", "painting": "画",
    "item_frame": "物品展示框", "glow_item_frame": "荧光物品展示框",
    "armor_stand": "盔甲架", "decorated_pot": "纹饰陶罐",
    "flower_pot": "花盆",
    "minecart": "矿车", "chest_minecart": "箱子矿车",
    "furnace_minecart": "动力矿车", "hopper_minecart": "漏斗矿车",
    "tnt_minecart": "TNT矿车",
    "oak_boat": "橡木船", "spruce_boat": "云杉船", "birch_boat": "白桦船",
    "jungle_boat": "丛林木船", "acacia_boat": "金合欢木船",
    "dark_oak_boat": "深色橡木船", "mangrove_boat": "红树木船",
    "cherry_boat": "樱花木船", "pale_oak_boat": "苍白橡木船", "bamboo_raft": "竹筏",
    "oak_chest_boat": "橡木运输船", "spruce_chest_boat": "云杉运输船",
    "birch_chest_boat": "白桦运输船", "jungle_chest_boat": "丛林木运输船",
    "dark_oak_chest_boat": "深色橡木运输船", "mangrove_chest_boat": "红树木运输船",
    "cherry_chest_boat": "樱花木运输船", "pale_oak_chest_boat": "苍白橡木运输船",
    "bamboo_chest_raft": "竹运输筏",
    "white_dye": "白色染料", "orange_dye": "橙色染料",
    "magenta_dye": "品红色染料", "light_blue_dye": "淡蓝色染料",
    "yellow_dye": "黄色染料", "lime_dye": "黄绿色染料",
    "pink_dye": "粉色染料", "gray_dye": "灰色染料",
    "light_gray_dye": "淡灰色染料", "cyan_dye": "青色染料",
    "purple_dye": "紫色染料", "blue_dye": "蓝色染料",
    "brown_dye": "棕色染料", "green_dye": "绿色染料",
    "red_dye": "红色染料", "black_dye": "黑色染料",
    "ink_sac": "墨囊", "glow_ink_sac": "荧光墨囊", "bone_meal": "骨粉",
    "redstone_dust": "红石粉", "redstone_torch": "红石火把",
    "redstone_repeater": "红石中继器", "redstone_comparator": "红石比较器",
    "observer": "侦测器", "target": "标靶",
    "daylight_detector": "阳光探测器", "tripwire_hook": "绊线钩",
    "lever": "拉杆",
    "dispenser": "发射器", "dropper": "投掷器", "piston": "活塞",
    "sticky_piston": "黏性活塞",
    "note_block": "音符盒", "redstone_lamp": "红石灯",
    "sculk_sensor": "幽匿感测体", "calibrated_sculk_sensor": "校频幽匿感测体",
    "wind_charge": "风弹", "fire_charge": "火焰弹", "firework_rocket": "烟花火箭",
    "arrow": "箭", "spectral_arrow": "光灵箭", "tipped_arrow": "药箭",
    "trident": "三叉戟", "mace": "重锤",
    "fishing_rod": "钓鱼竿", "carrot_on_a_stick": "胡萝卜钓竿",
    "warped_fungus_on_a_stick": "诡异菌钓竿",
    "crossbow": "弩", "shield": "盾牌", "totem_of_undying": "不死图腾",
    "firework_star": "烟火之星", "book_and_quill": "书与笔",
    "writable_book": "书与笔", "written_book": "成书", "enchanted_book": "附魔书",
    "music_disc": "音乐唱片", "disc_fragment_5": "唱片残片",
    "chain": "锁链", "lantern": "灯笼", "soul_lantern": "灵魂灯笼",
    "end_rod": "末地烛", "torch": "火把", "soul_torch": "灵魂火把",
    "campfire": "营火", "soul_campfire": "灵魂营火",
    "saddle": "鞍", "name_tag": "命名牌", "lead": "拴绳",
    "brush": "刷子", "spyglass": "望远镜", "recovery_compass": "追溯指针",
    "clock": "钟(物品)", "compass": "指南针", "empty_map": "空地图", "map": "地图",
    "shears": "剪刀", "flint_and_steel": "打火石",
    "bowl": "碗", "stick": "木棍", "paper": "纸", "book": "书",
    "string": "线", "feather": "羽毛", "leather": "皮革",
    "brick": "砖", "nether_brick": "下界砖",
    "clay_ball": "黏土球", "flint": "燧石",
    "gunpowder": "火药", "glowstone_dust": "荧石粉",
    "blaze_powder": "烈焰粉", "blaze_rod": "烈焰棒",
    "ghast_tear": "恶魂之泪", "magma_cream": "岩浆膏",
    "slime_ball": "黏液球", "honeycomb": "蜜脾",
    "rabbit_hide": "兔子皮", "rabbit_foot": "兔子脚",
    "phantom_membrane": "幻翼膜", "scute": "鳞甲",
    "nautilus_shell": "鹦鹉螺壳", "heart_of_the_sea": "海洋之心",
    "shulker_shell": "潜影壳",
    "prismarine_shard": "海晶碎片", "prismarine_crystal": "海晶砂粒",
    "nether_star": "下界之星",
    "ender_pearl": "末影珍珠", "ender_eye": "末影之眼",
    "fermented_spider_eye": "发酵蛛眼",
    "golden_apple": "金苹果", "enchanted_golden_apple": "附魔金苹果",
    "golden_carrot": "金胡萝卜",
    "snowball": "雪球", "egg": "鸡蛋", "sugar": "糖",
    "xp_bottle": "附魔之瓶", "dragon_breath": "龙息",
    "glass_bottle": "玻璃瓶", "water_bottle": "水瓶",
    "potion": "药水", "splash_potion": "喷溅药水", "lingering_potion": "滞留药水",
    "milk_bucket": "牛奶桶", "water_bucket": "水桶", "lava_bucket": "熔岩桶",
    "bucket": "桶", "powder_snow_bucket": "细雪桶",
    "cod_bucket": "鳕鱼桶", "salmon_bucket": "鲑鱼桶",
    "tropical_fish_bucket": "热带鱼桶", "pufferfish_bucket": "河豚桶",
    "axolotl_bucket": "美西螈桶", "tadpole_bucket": "蝌蚪桶",
    "goat_horn": "山羊角", "trial_key": "试炼钥匙",
    "vault": "宝库", "trial_spawner": "试炼刷怪笼",
    "cherry_grove": "樱花树林", "old_growth_birch_forest": "原始白桦林",
    "dark_forest": "黑森林", "mushroom_fields": "蘑菇地",
    "snowy_slopes": "雪坡", "jagged_peaks": "尖削山峰",
    "frozen_peaks": "冰封山峰", "stony_peaks": "裸岩山峰",
    "meadow": "草甸", "grove": "雪林",
    "dripstone_caves": "溶洞", "lush_caves": "繁茂洞穴",
    "deep_dark": "深暗之域", "basalt_deltas": "玄武岩三角洲",
    "crimson_forest": "绯红森林", "warped_forest": "诡异森林",
    "soul_sand_valley": "灵魂沙峡谷",
    "small_end_islands": "末地小型岛屿", "end_midlands": "末地中型岛屿",
    "end_highlands": "末地高地", "end_barrens": "末地荒地",
    "the_end": "末地", "the_nether": "下界", "overworld": "主世界",
    "piglin": "猪灵", "hoglin": "疣猪兽", "zoglin": "僵尸疣猪兽",
    "zombified_piglin": "僵尸猪灵", "piglin_brute": "猪灵蛮兵",
    "strider": "炽足兽", "ghast": "恶魂", "blaze": "烈焰人",
    "wither_skeleton": "凋灵骷髅", "magma_cube": "岩浆怪",
    "enderman": "末影人", "endermite": "末影螨", "shulker": "潜影贝",
    "silverfish": "蠹虫", "slime": "史莱姆", "phantom": "幻翼",
    "vex": "恼鬼", "allay": "悦灵", "breeze": "旋风人", "bogged": "沼泽骷髅",
    "camel": "骆驼", "sniffer": "嗅探兽", "armadillo": "犰狳",
    "axolotl": "美西螈", "glow_squid": "发光鱿鱼", "squid": "鱿鱼",
    "turtle": "海龟", "tadpole": "蝌蚪", "frog": "青蛙",
    "warden": "循声守卫", "iron_golem": "铁傀儡", "snow_golem": "雪傀儡",
    "villager": "村民", "wandering_trader": "流浪商人",
    "evoker": "唤魔者", "pillager": "掠夺者", "vindicator": "卫道士",
    "ravager": "劫掠兽", "witch": "女巫", "vindicator": "卫道士",
    "creeper": "苦力怕", "skeleton": "骷髅", "zombie": "僵尸",
    "spider": "蜘蛛", "cave_spider": "洞穴蜘蛛",
    "drowned": "溺尸", "husk": "尸壳", "stray": "流浪者",
    "guardian": "守卫者", "elder_guardian": "远古守卫者",
    "wolf": "狼", "cat": "猫", "ocelot": "豹猫",
    "parrot": "鹦鹉", "fox": "狐狸", "panda": "熊猫",
    "polar_bear": "北极熊", "llama": "羊驼", "trader_llama": "商队羊驼",
    "horse": "马", "donkey": "驴", "mule": "骡",
    "skeleton_horse": "骷髅马", "zombie_horse": "僵尸马",
    "bat": "蝙蝠", "chicken_jockey": "鸡骑士",
    "bee": "蜜蜂", "dolphin": "海豚", "cod_fish": "鳕鱼",
    "salmon_fish": "鲑鱼", "pufferfish_fish": "河豚", "tropical_fish_fish": "热带鱼",
    "mooshroom": "哞菇", "brown_mooshroom": "棕色哞菇",
    "rabbit_creature": "兔子", "polar_bear_creature": "北极熊",
    "bow": "弓", "fishing_rod_tool": "钓鱼竿",
    "nether_portal": "下界传送门", "end_portal": "末地传送门",
    "end_gateway": "末地折跃门",
    "horse_saddle": "马鞍",
    "creeper_head": "苦力怕头颅", "zombie_head": "僵尸头颅",
    "skeleton_skull": "骷髅头颅", "wither_skeleton_skull": "凋灵骷髅头颅",
    "player_head": "玩家头颅", "dragon_head": "龙首", "piglin_head": "猪灵头颅",
    "vex_armor_trim": "恼鬼纹饰", "wild_armor_trim": "荒野纹饰",
    "coast_armor_trim": "海岸纹饰", "sentry_armor_trim": "哨兵纹饰",
    "ward_armor_trim": "监守纹饰", "eye_armor_trim": "眼眸纹饰",
    "tide_armor_trim": "潮汐纹饰", "rib_armor_trim": "肋骨纹饰",
    "snout_armor_trim": "猪鼻纹饰", "spire_armor_trim": "塔尖纹饰",
    "dune_armor_trim": "沙丘纹饰", "host_armor_trim": "主人纹饰",
    "raiser_armor_trim": "牧民纹饰", "shaper_armor_trim": "塑形纹饰",
    "silence_armor_trim": "静谧纹饰", "wayfinder_armor_trim": "向导纹饰",
    "flow_armor_trim": "涡流纹饰", "bolt_armor_trim": "霹雳纹饰",
    "netherite_upgrade_smithing_template": "下界合金升级锻造模板",
    "music_disc_11": "音乐唱片11", "music_disc_13": "音乐唱片13",
    "music_disc_5": "音乐唱片5", "music_disc_blocks": "音乐唱片blocks",
    "music_disc_cat": "音乐唱片cat", "music_disc_chirp": "音乐唱片chirp",
    "music_disc_creator": "音乐唱片creator", "music_disc_creator_music_box": "音乐唱片creator_music_box",
    "music_disc_far": "音乐唱片far", "music_disc_mall": "音乐唱片mall",
    "music_disc_mellohi": "音乐唱片mellohi", "music_disc_otherside": "音乐唱片otherside",
    "music_disc_pigstep": "音乐唱片Pigstep", "music_disc_precipice": "音乐唱片precipice",
    "music_disc_relic": "音乐唱片relic", "music_disc_stal": "音乐唱片stal",
    "music_disc_strad": "音乐唱片strad", "music_disc_wait": "音乐唱片wait",
    "music_disc_ward": "音乐唱片ward",
}

# ============================================================
# P2: 规则引擎
# ============================================================
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

WOOD_PARTS = {
    'log': '原木', 'stripped_log': '去皮原木', 'wood': '木头', 'stripped_wood': '去皮木头',
    'planks': '木板', 'slab': '台阶', 'stairs': '楼梯', 'fence': '栅栏',
    'fence_gate': '栅栏门', 'door': '门', 'trapdoor': '活板门', 'button': '按钮',
    'pressure_plate': '压力板', 'sign': '告示牌', 'hanging_sign': '悬挂告示牌',
    'mosaic': '马赛克', 'mosaic_slab': '马赛克台阶', 'mosaic_stairs': '马赛克楼梯',
    'boat': '船', 'chest_boat': '运输船', 'raft': '竹筏', 'chest_raft': '运输竹筏',
}

MATERIALS = {'wooden': '木', 'stone': '石', 'iron': '铁', 'golden': '金', 'diamond': '钻石', 'netherite': '下界合金'}
TOOLS = {'axe': '斧', 'hoe': '锄', 'pickaxe': '镐', 'shovel': '锹', 'sword': '剑'}
ARMOR = {'helmet': '头盔', 'chestplate': '胸甲', 'leggings': '护腿', 'boots': '靴子'}

STONE_TYPES = {
    'stone': '石头', 'cobblestone': '圆石', 'granite': '花岗岩', 'diorite': '闪长岩',
    'andesite': '安山岩', 'sandstone': '砂岩', 'red_sandstone': '红砂岩',
    'blackstone': '黑石', 'deepslate': '深板岩', 'tuff': '凝灰岩', 'calcite': '方解石',
    'dripstone': '滴水石', 'basalt': '玄武岩', 'prismarine': '海晶石',
    'dark_prismarine': '暗海晶石', 'end_stone': '末地石',
    'polished_granite': '磨制花岗岩', 'polished_diorite': '磨制闪长岩',
    'polished_andesite': '磨制安山岩', 'polished_deepslate': '磨制深板岩',
    'polished_blackstone': '磨制黑石', 'polished_tuff': '磨制凝灰岩',
    'cobbled_deepslate': '深板岩圆石', 'smooth_stone': '平滑石头',
    'smooth_sandstone': '平滑砂岩', 'smooth_red_sandstone': '平滑红砂岩',
    'smooth_basalt': '平滑玄武岩', 'smooth_quartz': '平滑石英',
    'chiseled_sandstone': '錾制砂岩', 'chiseled_red_sandstone': '錾制红砂岩',
    'cut_sandstone': '切制砂岩', 'cut_red_sandstone': '切制红砂岩',
}
STONE_PARTS = {'slab': '台阶', 'stairs': '楼梯', 'wall': '墙'}

BRICK_TYPES = {
    'brick': '红砖', 'stone_brick': '石砖', 'nether_brick': '下界砖',
    'red_nether_brick': '红色下界砖', 'mud_brick': '泥砖', 'deepslate_brick': '深板岩砖',
    'tuff_brick': '凝灰岩砖', 'prismarine_brick': '海晶石砖', 'end_stone_brick': '末地石砖',
    'polished_blackstone_brick': '磨制黑石砖', 'quartz_brick': '石英砖',
    'cracked_stone_brick': '裂纹石砖', 'cracked_deepslate_brick': '裂纹深板岩砖',
    'cracked_nether_brick': '裂纹下界砖', 'cracked_polished_blackstone_brick': '裂纹磨制黑石砖',
    'chiseled_stone_brick': '錾制石砖', 'chiseled_deepslate': '錾制深板岩',
    'chiseled_nether_brick': '錾制下界砖', 'chiseled_polished_blackstone': '錾制磨制黑石',
    'chiseled_tuff': '錾制凝灰岩', 'chiseled_tuff_brick': '錾制凝灰岩砖',
    'mossy_stone_brick': '苔石砖', 'mossy_cobblestone': '苔石',
    'cracked_tuff_brick': '裂纹凝灰岩砖', 'chiseled_resin_brick': '錾制树脂砖',
    'resin_brick': '树脂砖', 'cinnabar_brick': '朱砂砖',
    'mud_brick': '泥砖', 'packed_mud': '泥坯',
}

def rule_based_translation(item_id, name_en):
    """P2: Rule-based Chinese name generation"""
    # 1. Color + type
    for color_en, color_zh in COLORS.items():
        if item_id.startswith(f'{color_en}_'):
            suffix = item_id[len(color_en)+1:]
            # Try colored types
            colored_types = {
                'wool': '羊毛', 'carpet': '地毯', 'concrete': '混凝土',
                'concrete_powder': '混凝土粉末', 'terracotta': '陶瓦',
                'glazed_terracotta': '带釉陶瓦', 'stained_glass': '染色玻璃',
                'stained_glass_pane': '染色玻璃板', 'bed': '床', 'candle': '蜡烛',
                'shulker_box': '潜影盒', 'banner': '旗帜', 'bundle': '收纳袋',
            }
            if suffix in colored_types:
                return color_zh + '色' + colored_types[suffix]
            if suffix in WOOD_PARTS:
                return color_zh + '色' + WOOD_PARTS[suffix]
            if suffix in STONE_PARTS:
                return color_zh + '色' + STONE_PARTS[suffix]
            # dye case
            if suffix == 'dye':
                return color_zh + '色染料'
            break

    # 2. Wood + part
    for wood_en, wood_zh in WOOD_TYPES.items():
        if item_id.startswith(f'{wood_en}_'):
            suffix = item_id[len(wood_en)+1:]
            if suffix in WOOD_PARTS:
                return wood_zh + WOOD_PARTS[suffix]
            if suffix == 'stripped_log':
                return '去皮' + wood_zh + '原木'
            if suffix == 'stripped_wood':
                return '去皮' + wood_zh + '木块'
            if suffix == 'leaves':
                return wood_zh + '树叶'
            if suffix == 'sapling':
                return wood_zh + '树苗'
            break

    # 3. Stone/Brick + part
    for stone_en, stone_zh in STONE_TYPES.items():
        if item_id == stone_en:
            return stone_zh
        if item_id.startswith(f'{stone_en}_'):
            suffix = item_id[len(stone_en)+1:]
            if suffix in STONE_PARTS:
                return stone_zh + STONE_PARTS[suffix]
            break

    # Check brick types
    for brick_en, brick_zh in BRICK_TYPES.items():
        if item_id == brick_en:
            return brick_zh
        if item_id.startswith(f'{brick_en}_'):
            suffix = item_id[len(brick_en)+1:]
            if suffix in STONE_PARTS:
                return brick_zh + STONE_PARTS[suffix]
            break

    # 4. Material tool/weapon
    for mat_en, mat_zh in MATERIALS.items():
        if item_id.startswith(f'{mat_en}_'):
            suffix = item_id[len(mat_en)+1:]
            if suffix in TOOLS:
                return mat_zh + TOOLS[suffix]
            if suffix in ARMOR:
                return mat_zh + ARMOR[suffix]
            if suffix == 'horse_armor':
                return mat_zh + '马铠'
            break

    # 5. Copper oxidation variants
    if item_id.startswith('waxed_'):
        base = item_id[6:]
        base_zh = rule_based_translation(base, '')
        if base_zh:
            return '涂蜡' + base_zh

    copper_parts = {
        'copper_block': '铜块', 'cut_copper': '切制铜块', 'chiseled_copper': '錾制铜块',
        'copper_grate': '铜格栅', 'copper_door': '铜门', 'copper_trapdoor': '铜活板门',
        'copper_bulb': '铜灯',
    }
    for prefix, zh in copper_parts.items():
        for ox_state, ox_zh in [('exposed_', '斑驳'), ('weathered_', '锈蚀'), ('oxidized_', '氧化')]:
            full = ox_state + prefix
            if item_id == full:
                return ox_zh + zh

    if item_id in copper_parts:
        return copper_parts[item_id]
    # copper slab/stairs variants
    for ox_state, ox_zh in [('exposed_', '斑驳'), ('weathered_', '锈蚀'), ('oxidized_', '氧化')]:
        for base_name, base_zh in [('cut_copper', '切制铜'), ('copper', '铜')]:
            full = ox_state + base_name
            if item_id.startswith(full + '_'):
                suffix = item_id[len(full)+1:]
                if suffix in STONE_PARTS:
                    return ox_zh + base_zh + STONE_PARTS[suffix]

    # 6. Waxed copper variants
    for ox_state in ['exposed_', 'weathered_', 'oxidized_', '']:
        for base_name, base_zh in copper_parts.items():
            full = 'waxed_' + ox_state + base_name
            if item_id == full:
                return '涂蜡' + (ox_state.replace('_','') + base_zh if ox_state else base_zh)

    # 7. Smithing templates
    if item_id.endswith('_smithing_template'):
        base = item_id.replace('_smithing_template', '')
        if base in FALLBACK_FIX_MAP:
            return FALLBACK_FIX_MAP[base] + '锻造模板'

    # 8. Pottery sherds
    if item_id.endswith('_pottery_sherd'):
        base = item_id.replace('_pottery_sherd', '')
        base_zh_map = {
            'angler': '渔夫', 'archer': '弓箭', 'arms_up': '举臂', 'blade': '利刃',
            'brewer': '酿造', 'burn': '烈焰', 'danger': '危险', 'explorer': '探险',
            'friend': '朋友', 'heart': '心形', 'heartbreak': '心碎', 'howl': '狼嚎',
            'miner': '矿工', 'mourner': '哀悼', 'plenty': '丰收', 'prize': '珍宝',
            'sheaf': '麦束', 'shelter': '庇护', 'skull': '头颅', 'snort': '猪鼻',
        }
        if base in base_zh_map:
            return base_zh_map[base] + '纹样陶片'

    # 9. Potion variants
    if item_id.startswith('potion_of_') or item_id.startswith('lingering_potion_of_') or item_id.startswith('splash_potion_of_'):
        prefix_map = {'potion_of_': '药水', 'lingering_potion_of_': '滞留药水', 'splash_potion_of_': '喷溅药水'}
        for pfx, pfx_zh in prefix_map.items():
            if item_id.startswith(pfx):
                effect_id = item_id[len(pfx):]
                effect_map = {
                    'fire_resistance': '抗火', 'healing': '治疗', 'invisibility': '隐身',
                    'leaping': '跳跃', 'night_vision': '夜视', 'poison': '剧毒',
                    'regeneration': '再生', 'slow_falling': '缓降', 'slowness': '缓慢',
                    'strength': '力量', 'swiftness': '迅捷', 'turtle_master': '神龟',
                    'water_breathing': '水肺', 'weakness': '虚弱',
                }
                if effect_id in effect_map:
                    if 'strong' in effect_id or 'long' in effect_id:
                        return pfx_zh + '(' + effect_id.replace('_', ' ') + ')'
                    return effect_map[effect_id] + pfx_zh
                # Uncommon variants - use effect name directly
                zh = effect_id.replace('_', ' ').title()
                return zh + pfx_zh

    return None


# ============================================================
# CATEGORY/SUB NAMES
# ============================================================
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


def sort_key_item(item_id):
    MATERIAL = {'wooden': 1, 'stone': 2, 'iron': 3, 'golden': 4, 'gold': 4, 'diamond': 5, 'netherite': 6}
    for mat, order in MATERIAL.items():
        if item_id.startswith(mat + '_'): return (order, item_id)
    COLOR_ORDER = {c: i for i, c in enumerate(COLORS.keys())}
    for color, order in COLOR_ORDER.items():
        if item_id.startswith(color + '_'): return (100 + order, item_id)
    WOOD_ORDER = {w: i for i, w in enumerate(WOOD_TYPES.keys())}
    for wood, order in WOOD_ORDER.items():
        if item_id.startswith(wood + '_'): return (400 + order, item_id)
    return (500, item_id)


def rebuild_categories(data):
    items = data['items']
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
            sorted_items = sorted(tree[cat_id][sub_id], key=sort_key_item)
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


# ============================================================
# MAIN
# ============================================================
def main():
    # Backup
    backup_path = DATA_PATH.with_name('data_backup_v5.json')
    shutil.copy(DATA_PATH, backup_path)
    print(f"Backup: {backup_path}")

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data['items']

    # ---- Task 1: Merge redstone → functional_blocks ----
    print("\n=== Task 1: 合并红石 → 功能方块 ===")
    cat_changes = 0
    sec_changes = 0
    self_ref_removed = 0
    enchanting_fixed = 0

    for item in items:
        # 1. category redstone → functional_blocks
        if item.get('category') == 'redstone':
            item['category'] = 'functional_blocks'
            cat_changes += 1

        # 2. secondary_categories: redstone → functional_blocks
        secs = item.get('secondary_categories', [])
        new_secs = []
        for s in secs:
            if s == 'redstone':
                new_secs.append('functional_blocks')
                sec_changes += 1
            elif s == 'enchanting':
                new_secs.append('functional_blocks')
                enchanting_fixed += 1
            else:
                new_secs.append(s)

        # 3. Remove self-reference
        cat = item.get('category')
        filtered = [s for s in new_secs if s != cat]
        if len(filtered) != len(new_secs):
            self_ref_removed += len(new_secs) - len(filtered)
        item['secondary_categories'] = filtered

    print(f"  category 变更: {cat_changes}")
    print(f"  secondary redstone→functional_blocks: {sec_changes}")
    print(f"  secondary enchanting→functional_blocks: {enchanting_fixed}")
    print(f"  self-reference removed: {self_ref_removed}")

    # ---- Task 2: Fix Chinese names ----
    print("\n=== Task 2: 修复中文名 ===")

    # P1: Hardcoded map
    p1 = 0
    for item in items:
        iid = item['id']
        if item.get('zh_fallback') and iid in FALLBACK_FIX_MAP:
            item['name_zh'] = FALLBACK_FIX_MAP[iid]
            item['zh_fallback'] = False
            p1 += 1
    # Also fix items with zh_fallback=False but name_zh==name_en
    for item in items:
        iid = item['id']
        if not item.get('zh_fallback') and item.get('name_zh') == item.get('name_en'):
            if iid in FALLBACK_FIX_MAP:
                item['name_zh'] = FALLBACK_FIX_MAP[iid]
                p1 += 1
    print(f"P1 (硬编码): {p1}")

    # P2: Rule engine
    p2 = 0
    for item in items:
        if not item.get('zh_fallback'):
            continue
        zh = rule_based_translation(item['id'], item.get('name_en', ''))
        if zh and zh != item.get('name_en') and zh != item.get('name_zh'):
            item['name_zh'] = zh
            item['zh_fallback'] = False
            p2 += 1
    print(f"P2 (规则引擎): {p2}")

    # P3: AI translation for remaining
    remaining = [i for i in items if i.get('zh_fallback')]
    print(f"P3 剩余: {len(remaining)}")
    p3 = 0
    if remaining:
        print("  调用 DeepSeek API...")
        BATCH = 100
        for batch_num in range(0, len(remaining), BATCH):
            batch = remaining[batch_num:batch_num+BATCH]
            descs = [f"id={i['id']}, name_en=\"{i.get('name_en','')}\", category={i.get('category','')}" for i in batch]
            prompt = "请将以下Minecraft物品英文名翻译为官方简体中文名：\n" + "\n".join(descs)

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是Minecraft中文翻译专家。将物品英文名翻译为Minecraft简体中文官方译名风格（与zh.minecraft.wiki一致）。每种物品返回：{\"id\":\"..\",\"name_zh\":\"中文译名\"}。只返回JSON数组，不要解释。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.0, "max_tokens": 4096
            }
            try:
                import requests as req
                resp = req.post(API_URL, json=payload, headers={
                    "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"
                }, timeout=120)
                resp.raise_for_status()
                result = resp.json()
                content = result['choices'][0]['message']['content']
                m = re.search(r'\[.*\]', content, re.DOTALL)
                if m:
                    translations = json.loads(m.group())
                    for t in translations:
                        iid = t['id']
                        zh = t.get('name_zh', '')
                        if zh:
                            for item in items:
                                if item['id'] == iid:
                                    if zh != item.get('name_en'):
                                        item['name_zh'] = zh
                                        item['zh_fallback'] = False
                                        p3 += 1
                                    break
                print(f"  batch {batch_num//BATCH + 1}: {len(translations)} translated")
            except Exception as e:
                print(f"  batch {batch_num//BATCH + 1}: ERROR {e}")
            time.sleep(1.5)
    print(f"P3 (AI): {p3}")
    print(f"Total fixed: {p1+p2+p3}")

    # Re-check zh_fallback
    for item in items:
        if item.get('name_zh') != item.get('name_en') and item.get('name_zh'):
            item['zh_fallback'] = False
        elif item.get('name_zh') == item.get('name_en') or not item.get('name_zh'):
            item['zh_fallback'] = True

    # ---- Rebuild categories ----
    print("\n=== 重建 categories ===")
    rebuild_categories(data)

    # ---- Save ----
    data['meta']['generated_at'] = '2026-05-05-v5'
    data['meta']['total_items'] = len(items)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ---- Verify ----
    print("\n=== 验证 ===")
    errs = []
    if len(items) != 1612:
        errs.append(f"物品数: {len(items)} != 1612")
    cats = data['categories']
    if len(cats) != 9:
        errs.append(f"大类: {len(cats)} != 9")
    redstone_items = [i['id'] for i in items if i.get('category') == 'redstone']
    if redstone_items:
        errs.append(f"category=redstone: {redstone_items}")
    bad_sec = [(i['id'], [s for s in i.get('secondary_categories',[]) if s in ('redstone','enchanting')]) for i in items]
    bad_sec = [(iid, secs) for iid, secs in bad_sec if secs]
    if bad_sec:
        errs.append(f"secondary坏值: {bad_sec[:5]}")
    self_ref = [(i['id'], i['category']) for i in items if i['category'] in i.get('secondary_categories',[])]
    if self_ref:
        errs.append(f"self-ref: {self_ref[:5]}")

    fb = sum(1 for i in items if i.get('zh_fallback'))
    cov = (len(items) - fb) / len(items) * 100
    if cov < 95:
        errs.append(f"中文名覆盖率: {cov:.1f}% < 95% (剩余: {fb})")

    func_count = sum(1 for i in items if i.get('category') == 'functional_blocks')
    func_subs = len(data['categories'][3]['subcategories']) if len(cats) > 3 else 0

    if errs:
        print("FAIL:")
        for e in errs: print(f"  {e}")
    else:
        print("PASS:")
    print(f"  物品: {len(items)}")
    print(f"  大类: {len(cats)}")
    print(f"  中文名覆盖率: {cov:.1f}% (fallback: {fb})")
    print(f"  functional_blocks: {func_count} 物品, {func_subs} 子类")

    for c in cats:
        ic = sum(len(s.get('items',[])) for s in c['subcategories'])
        print(f"    {c['name_zh']}: {ic} 物品")

    print(f"\ndata.json: {os.path.getsize(DATA_PATH)/1024:.0f} KB")
    return len(errs) == 0

if __name__ == '__main__':
    main()
