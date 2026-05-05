#!/usr/bin/env python3
"""
repair_data.py — 全面修复 data.json
1. 中文名称标准化（Minecraft 官方简体中文）
2. 补全缺失物品（16色/木材/基础方块/工具）
3. 分类系统重构（blocks/items/tools/materials/food）
4. 错误数据清理
5. acquisition 自动修复
6. 图片路径标准化为 images/{id}.png
"""
import json
import os
import re
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, 'docs', 'data', 'data.json')
IMAGES_DIR = os.path.join(SCRIPT_DIR, 'docs', 'images')
BACKUP_PATH = DATA_PATH + '.repair_bak'

# ============================================================
# 1. 官方简体中文名称映射
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
    'mangrove': '红树木', 'cherry': '樱花木', 'bamboo': '竹子',
    'crimson': '绯红木', 'warped': '诡异木',
}

ZH_BASES = {
    'wool': '羊毛', 'carpet': '地毯', 'bed': '床',
    'stained_glass': '染色玻璃', 'stained_glass_pane': '染色玻璃板',
    'terracotta': '陶瓦', 'glazed_terracotta': '带釉陶瓦',
    'concrete': '混凝土', 'concrete_powder': '混凝土粉末',
    'dye': '染料', 'banner': '旗帜', 'candle': '蜡烛',
    'log': '原木', 'stripped_log': '去皮原木',
    'planks': '木板', 'stairs': '楼梯', 'slab': '台阶',
    'door': '门', 'fence': '栅栏', 'fence_gate': '栅栏门',
    'trapdoor': '活板门', 'button': '按钮', 'pressure_plate': '压力板',
    'sign': '告示牌', 'hanging_sign': '悬挂式告示牌',
    'boat': '船', 'chest_boat': '运输船',
    'leaves': '树叶', 'sapling': '树苗',
}

ZH_ITEMS = {
    # 基础方块
    'stone': '石头', 'cobblestone': '圆石', 'stone_bricks': '石砖',
    'cracked_stone_bricks': '裂纹石砖', 'mossy_stone_bricks': '苔石砖',
    'chiseled_stone_bricks': '錾制石砖', 'smooth_stone': '平滑石头',
    'stone_slab': '石台阶', 'cobblestone_slab': '圆石台阶',
    'stone_brick_slab': '石砖台阶', 'stone_stairs': '石楼梯',
    'cobblestone_stairs': '圆石楼梯', 'stone_brick_stairs': '石砖楼梯',
    'cobblestone_wall': '圆石墙', 'mossy_cobblestone': '苔石',
    'mossy_cobblestone_wall': '苔石墙', 'mossy_stone_brick_wall': '苔石砖墙',
    'stone_brick_wall': '石砖墙',
    'granite': '花岗岩', 'diorite': '闪长岩', 'andesite': '安山岩',
    'polished_granite': '磨制花岗岩', 'polished_diorite': '磨制闪长岩',
    'polished_andesite': '磨制安山岩',
    'granite_slab': '花岗岩台阶', 'diorite_slab': '闪长岩台阶', 'andesite_slab': '安山岩台阶',
    'granite_stairs': '花岗岩楼梯', 'diorite_stairs': '闪长岩楼梯', 'andesite_stairs': '安山岩楼梯',
    'granite_wall': '花岗岩墙', 'diorite_wall': '闪长岩墙', 'andesite_wall': '安山岩墙',
    'sand': '沙子', 'red_sand': '红沙', 'gravel': '沙砾',
    'sandstone': '砂岩', 'red_sandstone': '红砂岩',
    'cut_sandstone': '切制砂岩', 'cut_red_sandstone': '切制红砂岩',
    'chiseled_sandstone': '錾制砂岩', 'chiseled_red_sandstone': '錾制红砂岩',
    'smooth_sandstone': '平滑砂岩', 'smooth_red_sandstone': '平滑红砂岩',
    'sandstone_slab': '砂岩台阶', 'sandstone_stairs': '砂岩楼梯', 'sandstone_wall': '砂岩墙',
    'obsidian': '黑曜石', 'crying_obsidian': '哭泣的黑曜石',
    'glass': '玻璃', 'glass_pane': '玻璃板',
    'tinted_glass': '遮光玻璃',
    'bricks': '砖块', 'brick_slab': '砖台阶', 'brick_stairs': '砖楼梯', 'brick_wall': '砖墙',
    'dirt': '泥土', 'grass_block': '草方块', 'podzol': '灰化土',
    'mycelium': '菌丝', 'coarse_dirt': '砂土', 'rooted_dirt': '缠根泥土',
    'mud': '泥巴', 'packed_mud': '泥坯', 'mud_bricks': '泥砖',
    'clay': '黏土块', 'terracotta': '陶瓦',
    'snow': '雪', 'snow_block': '雪块', 'ice': '冰', 'packed_ice': '浮冰', 'blue_ice': '蓝冰',
    'netherrack': '下界岩', 'nether_bricks': '下界砖块', 'red_nether_bricks': '红色下界砖块',
    'nether_wart_block': '下界疣块', 'warped_wart_block': '诡异疣块',
    'soul_sand': '灵魂沙', 'soul_soil': '灵魂土',
    'basalt': '玄武岩', 'polished_basalt': '磨制玄武岩', 'smooth_basalt': '平滑玄武岩',
    'blackstone': '黑石', 'polished_blackstone': '磨制黑石',
    'end_stone': '末地石', 'end_stone_bricks': '末地石砖',
    'purpur_block': '紫珀块', 'purpur_pillar': '紫珀柱',
    'purpur_slab': '紫珀台阶', 'purpur_stairs': '紫珀楼梯',
    'prismarine': '海晶石', 'prismarine_bricks': '海晶石砖', 'dark_prismarine': '暗海晶石',
    'sea_lantern': '海晶灯',
    'deepslate': '深板岩', 'cobbled_deepslate': '深板岩圆石',
    'tuff': '凝灰岩', 'calcite': '方解石', 'dripstone_block': '滴水石块',
    'amethyst_block': '紫水晶块', 'budding_amethyst': '紫水晶母岩',
    'moss_block': '苔藓块', 'sculk': '幽匿块',
    'copper_block': '铜块', 'exposed_copper': '斑驳的铜块',
    'weathered_copper': '锈蚀的铜块', 'oxidized_copper': '氧化的铜块',
    'cut_copper': '切制铜块', 'exposed_cut_copper': '斑驳的切制铜块',
    'weathered_cut_copper': '锈蚀的切制铜块', 'oxidized_cut_copper': '氧化的切制铜块',
    'raw_iron_block': '粗铁块', 'raw_copper_block': '粗铜块', 'raw_gold_block': '粗金块',
    'iron_block': '铁块', 'gold_block': '金块', 'diamond_block': '钻石块',
    'emerald_block': '绿宝石块', 'netherite_block': '下界合金块',
    'coal_block': '煤炭块', 'lapis_block': '青金石块', 'redstone_block': '红石块',
    'quartz_block': '石英块', 'smooth_quartz': '平滑石英块',
    'quartz_slab': '石英台阶', 'quartz_stairs': '石英楼梯',
    'bone_block': '骨块',
    # 功能方块
    'crafting_table': '工作台', 'furnace': '熔炉', 'blast_furnace': '高炉',
    'smoker': '烟熏炉', 'enchanting_table': '附魔台', 'anvil': '铁砧',
    'brewing_stand': '酿造台', 'cauldron': '炼药锅',
    'chest': '箱子', 'ender_chest': '末影箱', 'barrel': '木桶',
    'shulker_box': '潜影盒', 'trapped_chest': '陷阱箱',
    'crafting_table': '工作台', 'loom': '织布机', 'stonecutter': '切石机',
    'grindstone': '砂轮', 'smithing_table': '锻造台', 'cartography_table': '制图台',
    'fletching_table': '制箭台', 'composter': '堆肥桶',
    'note_block': '音符盒', 'jukebox': '唱片机',
    'beacon': '信标', 'conduit': '潮涌核心', 'lodestone': '磁石',
    'respawn_anchor': '重生锚', 'bell': '钟', 'scaffolding': '脚手架',
    'ladder': '梯子', 'torch': '火把', 'soul_torch': '灵魂火把',
    'lantern': '灯笼', 'soul_lantern': '灵魂灯笼',
    'campfire': '营火', 'soul_campfire': '灵魂营火',
    'candle': '蜡烛', 'end_rod': '末地烛',
    'rail': '铁轨', 'powered_rail': '动力铁轨', 'detector_rail': '探测铁轨', 'activator_rail': '激活铁轨',
    'tnt': 'TNT', 'piston': '活塞', 'sticky_piston': '黏性活塞',
    'slime_block': '黏液块', 'honey_block': '蜂蜜块',
    'hopper': '漏斗', 'dropper': '投掷器', 'dispenser': '发射器', 'observer': '侦测器',
    'redstone_lamp': '红石灯', 'daylight_detector': '阳光探测器',
    'lever': '拉杆', 'stone_button': '石按钮',
    'stone_pressure_plate': '石压力板',
    'tripwire_hook': '绊线钩', 'lightning_rod': '避雷针',
    'iron_door': '铁门', 'iron_trapdoor': '铁活板门',
    'beehive': '蜂箱', 'bee_nest': '蜂巢',
    'flower_pot': '花盆', 'decorated_pot': '饰纹陶罐',
    'armor_stand': '盔甲架', 'item_frame': '物品展示框', 'glow_item_frame': '荧光物品展示框',
    'painting': '画', 'bookshelf': '书架', 'lectern': '讲台',
    'spawner': '刷怪笼', 'dragon_egg': '龙蛋',
    # 工具
    'wooden_shovel': '木锹', 'stone_shovel': '石锹', 'iron_shovel': '铁锹',
    'golden_shovel': '金锹', 'diamond_shovel': '钻石锹', 'netherite_shovel': '下界合金锹',
    'wooden_pickaxe': '木镐', 'stone_pickaxe': '石镐', 'iron_pickaxe': '铁镐',
    'golden_pickaxe': '金镐', 'diamond_pickaxe': '钻石镐', 'netherite_pickaxe': '下界合金镐',
    'wooden_axe': '木斧', 'stone_axe': '石斧', 'iron_axe': '铁斧',
    'golden_axe': '金斧', 'diamond_axe': '钻石斧', 'netherite_axe': '下界合金斧',
    'wooden_hoe': '木锄', 'stone_hoe': '石锄', 'iron_hoe': '铁锄',
    'golden_hoe': '金锄', 'diamond_hoe': '钻石锄', 'netherite_hoe': '下界合金锄',
    'shears': '剪刀', 'flint_and_steel': '打火石', 'fishing_rod': '钓鱼竿',
    'carrot_on_a_stick': '胡萝卜钓竿', 'warped_fungus_on_a_stick': '诡异菌钓竿',
    'compass': ' compass', 'recovery_compass': '追溯指针',
    'clock': '时钟', 'spyglass': '望远镜', 'brush': '刷子',
    'lead': '拴绳', 'name_tag': '命名牌', 'saddle': '鞍',
    'bundle': '收纳袋',
    # 武器
    'wooden_sword': '木剑', 'stone_sword': '石剑', 'iron_sword': '铁剑',
    'golden_sword': '金剑', 'diamond_sword': '钻石剑', 'netherite_sword': '下界合金剑',
    'bow': '弓', 'crossbow': '弩', 'arrow': '箭', 'spectral_arrow': '光灵箭',
    'tipped_arrow': '药箭', 'shield': '盾牌', 'totem_of_undying': '不死图腾',
    'trident': '三叉戟', 'mace': '重锤',
    # 盔甲
    'leather_helmet': '皮革帽子', 'leather_chestplate': '皮革外套', 'leather_leggings': '皮革裤子', 'leather_boots': '皮革靴子',
    'chainmail_helmet': '锁链头盔', 'chainmail_chestplate': '锁链胸甲', 'chainmail_leggings': '锁链护腿', 'chainmail_boots': '锁链靴子',
    'iron_helmet': '铁头盔', 'iron_chestplate': '铁胸甲', 'iron_leggings': '铁护腿', 'iron_boots': '铁靴子',
    'golden_helmet': '金头盔', 'golden_chestplate': '金胸甲', 'golden_leggings': '金护腿', 'golden_boots': '金靴子',
    'diamond_helmet': '钻石头盔', 'diamond_chestplate': '钻石胸甲', 'diamond_leggings': '钻石护腿', 'diamond_boots': '钻石靴子',
    'netherite_helmet': '下界合金头盔', 'netherite_chestplate': '下界合金胸甲', 'netherite_leggings': '下界合金护腿', 'netherite_boots': '下界合金靴子',
    'turtle_helmet': '海龟壳', 'elytra': '鞘翅',
    # 食物
    'apple': '苹果', 'golden_apple': '金苹果', 'enchanted_golden_apple': '附魔金苹果',
    'bread': '面包', 'cookie': '曲奇', 'cake': '蛋糕', 'pumpkin_pie': '南瓜派',
    'melon_slice': '西瓜片', 'sweet_berries': '甜浆果', 'glow_berries': '发光浆果',
    'chorus_fruit': '紫颂果', 'popped_chorus_fruit': '爆裂紫颂果',
    'beetroot': '甜菜根', 'beetroot_soup': '甜菜汤',
    'carrot': '胡萝卜', 'golden_carrot': '金胡萝卜',
    'potato': '马铃薯', 'baked_potato': '烤马铃薯', 'poisonous_potato': '毒马铃薯',
    'mushroom_stew': '蘑菇煲', 'rabbit_stew': '兔肉煲', 'suspicious_stew': '迷之炖菜',
    'beef': '生牛肉', 'cooked_beef': '牛排',
    'porkchop': '生猪排', 'cooked_porkchop': '熟猪排',
    'chicken': '生鸡肉', 'cooked_chicken': '熟鸡肉',
    'mutton': '生羊肉', 'cooked_mutton': '熟羊肉',
    'rabbit': '生兔肉', 'cooked_rabbit': '熟兔肉',
    'cod': '生鳕鱼', 'cooked_cod': '熟鳕鱼', 'salmon': '生鲑鱼', 'cooked_salmon': '熟鲑鱼',
    'tropical_fish': '热带鱼', 'pufferfish': '河豚',
    'dried_kelp': '干海带', 'honey_bottle': '蜂蜜瓶',
    'milk_bucket': '牛奶桶', 'water_bucket': '水桶', 'lava_bucket': '熔岩桶',
    # 材料
    'stick': '木棍', 'bowl': '碗', 'string': '线', 'feather': '羽毛',
    'flint': '燧石', 'leather': '皮革', 'rabbit_hide': '兔皮',
    'brick': '砖', 'nether_brick': '下界砖', 'clay_ball': '黏土球',
    'paper': '纸', 'book': '书', 'writable_book': '书与笔', 'written_book': '成书',
    'slime_ball': '黏液球', 'honeycomb': '蜜脾', 'honey_bottle': '蜂蜜瓶',
    'ink_sac': '墨囊', 'glow_ink_sac': '荧光墨囊',
    'bone_meal': '骨粉', 'sugar': '糖', 'gunpowder': '火药',
    'blaze_rod': '烈焰棒', 'blaze_powder': '烈焰粉',
    'ender_pearl': '末影珍珠', 'ender_eye': '末影之眼',
    'ghast_tear': '恶魂之泪', 'magma_cream': '岩浆膏',
    'spider_eye': '蜘蛛眼', 'fermented_spider_eye': '发酵蛛眼',
    'glowstone_dust': '荧石粉', 'redstone': '红石粉',
    'iron_ingot': '铁锭', 'gold_ingot': '金锭', 'copper_ingot': '铜锭',
    'netherite_ingot': '下界合金锭', 'netherite_scrap': '下界合金碎片',
    'diamond': '钻石', 'emerald': '绿宝石', 'lapis_lazuli': '青金石',
    'quartz': '下界石英', 'amethyst_shard': '紫水晶碎片',
    'coal': '煤炭', 'charcoal': '木炭',
    'raw_iron': '粗铁', 'raw_copper': '粗铜', 'raw_gold': '粗金',
    'iron_nugget': '铁粒', 'gold_nugget': '金粒',
    'echo_shard': '回响碎片', 'nautilus_shell': '鹦鹉螺壳',
    'heart_of_the_sea': '海洋之心', 'nether_star': '下界之星',
    'prismarine_shard': '海晶碎片', 'prismarine_crystals': '海晶砂粒',
    'phantom_membrane': '幻翼膜', 'rabbit_foot': '兔子脚',
    'shulker_shell': '潜影壳', 'turtle_scute': '鳞甲', 'armadillo_scute': '犰狳鳞甲',
    'fire_charge': '火焰弹', 'firework_rocket': '烟花火箭', 'firework_star': '烟火之星',
    'map': '空地图', 'filled_map': '地图',
    'goat_horn': '山羊角', 'wind_charge': '风弹', 'breeze_rod': '旋风棒',
    'heavy_core': '重质核心', 'ominous_bottle': '不祥之瓶',
    'trial_key': '试炼钥匙', 'ominous_trial_key': '不祥试炼钥匙',
    'experience_bottle': '附魔之瓶', 'enchanted_book': '附魔书',
    'snowball': '雪球', 'egg': '鸡蛋', 'wheat': '小麦', 'wheat_seeds': '小麦种子',
    'pumpkin_seeds': '南瓜种子', 'melon_seeds': '西瓜种子', 'beetroot_seeds': '甜菜种子',
    'torchflower_seeds': '火把花种子', 'pitcher_plant': '瓶子草',
    'nether_wart': '下界疣', 'cocoa_beans': '可可豆',
    'kelp': '海带', 'sea_pickle': '海泡菜',
    'bamboo': '竹子', 'sugar_cane': '甘蔗', 'cactus': '仙人掌',
    'lily_pad': '睡莲', 'vine': '藤蔓', 'glow_lichen': '发光地衣',
    'moss_carpet': '苔藓地毯', 'small_dripleaf': '小型垂滴叶', 'big_dripleaf': '大型垂滴叶',
    'spore_blossom': '孢子花', 'hanging_roots': '垂根', 'twisting_vines': '缠怨藤',
    'weeping_vines': '垂泪藤', 'crimson_roots': '绯红菌索', 'warped_roots': '诡异菌索',
    'crimson_fungus': '绯红菌', 'warped_fungus': '诡异菌',
    'red_mushroom': '红色蘑菇', 'brown_mushroom': '棕色蘑菇',
    'cobweb': '蜘蛛网', 'dead_bush': '枯死的灌木',
    'fern': '蕨', 'large_fern': '大型蕨', 'tall_grass': '高草丛', 'grass': '草',
    'dandelion': '蒲公英', 'poppy': '虞美人', 'blue_orchid': '兰花',
    'allium': '绒球葱', 'azure_bluet': '滨菊', 'red_tulip': '红色郁金香',
    'orange_tulip': '橙色郁金香', 'white_tulip': '白色郁金香', 'pink_tulip': '粉红色郁金香',
    'oxeye_daisy': '滨菊', 'cornflower': '矢车菊', 'lily_of_the_valley': '铃兰',
    'wither_rose': '凋零玫瑰', 'sunflower': '向日葵', 'lilac': '丁香',
    'rose_bush': '玫瑰丛', 'peony': '牡丹',
    'torchflower': '火把花', 'pitcher_pod': '瓶子草荚果',
    'pink_petals': '粉红色花簇', 'cherry_leaves': '樱花树叶',
    # 船
    'oak_boat': '橡木船', 'spruce_boat': '云杉木船', 'birch_boat': '白桦木船',
    'jungle_boat': '丛林木船', 'acacia_boat': '金合欢木船',
    'dark_oak_boat': '深色橡木船', 'mangrove_boat': '红树木船',
    'cherry_boat': '樱花木船', 'bamboo_raft': '竹筏',
    'oak_chest_boat': '橡木运输船', 'spruce_chest_boat': '云杉木运输船',
    'birch_chest_boat': '白桦木运输船', 'jungle_chest_boat': '丛林木运输船',
    'acacia_chest_boat': '金合欢木运输船', 'dark_oak_chest_boat': '深色橡木运输船',
    'mangrove_chest_boat': '红树木运输船', 'cherry_chest_boat': '樱花木运输船',
    'bamboo_chest_raft': '竹运输筏',
    # 唱片
    'music_disc_13': '音乐唱片(13)',
    'music_disc_cat': '音乐唱片(cat)',
    'music_disc_blocks': '音乐唱片(blocks)',
    'music_disc_chirp': '音乐唱片(chirp)',
    'music_disc_far': '音乐唱片(far)',
    'music_disc_mall': '音乐唱片(mall)',
    'music_disc_mellohi': '音乐唱片(mellohi)',
    'music_disc_stal': '音乐唱片(stal)',
    'music_disc_strad': '音乐唱片(strad)',
    'music_disc_ward': '音乐唱片(ward)',
    'music_disc_11': '音乐唱片(11)',
    'music_disc_wait': '音乐唱片(wait)',
    'music_disc_otherside': '音乐唱片(otherside)',
    'music_disc_5': '音乐唱片(5)',
    'music_disc_pigstep': '音乐唱片(Pigstep)',
    'music_disc_relic': '音乐唱片(Relic)',
    'music_disc_creator': '音乐唱片(Creator)',
    'music_disc_creator_music_box': '音乐唱片(Creator)',
    'music_disc_precipice': '音乐唱片(Precipice)',
}

# ============================================================
# 2. 分类系统
# ============================================================

CATEGORY_MAP = {
    # blocks
    'wool': ('blocks', 'wool'),
    'carpet': ('blocks', 'wool'),
    'bed': ('blocks', 'colored'),
    'stained_glass': ('blocks', 'glass'),
    'stained_glass_pane': ('blocks', 'glass'),
    'terracotta': ('blocks', 'terracotta'),
    'glazed_terracotta': ('blocks', 'terracotta'),
    'concrete': ('blocks', 'concrete'),
    'concrete_powder': ('blocks', 'concrete'),
    'log': ('blocks', 'wood'),
    'stripped_log': ('blocks', 'wood'),
    'planks': ('blocks', 'wood'),
    'stairs': ('blocks', 'wood'),
    'slab': ('blocks', 'wood'),
    'door': ('blocks', 'wood'),
    'fence': ('blocks', 'wood'),
    'fence_gate': ('blocks', 'wood'),
    'trapdoor': ('blocks', 'wood'),
    'button': ('blocks', 'wood'),
    'pressure_plate': ('blocks', 'wood'),
    'sign': ('blocks', 'wood'),
    'hanging_sign': ('blocks', 'wood'),
    'leaves': ('blocks', 'natural'),
    'sapling': ('blocks', 'natural'),
    'planks': ('blocks', 'wood'),
    # items
    'boat': ('items', 'transport'),
    'chest_boat': ('items', 'transport'),
    'chest_raft': ('items', 'transport'),
    'raft': ('items', 'transport'),
    'minecart': ('items', 'transport'),
    'spawn_egg': ('items', 'spawn_eggs'),
    'banner_pattern': ('items', 'misc'),
    'music_disc': ('items', 'music_discs'),
    'dye': ('materials', 'dyes'),
    # tools
    'shovel': ('tools', 'tools'),
    'pickaxe': ('tools', 'tools'),
    'axe': ('tools', 'tools'),
    'hoe': ('tools', 'tools'),
    'shears': ('tools', 'tools'),
    'fishing_rod': ('tools', 'tools'),
    # combat
    'sword': ('combat', 'weapons'),
    'bow': ('combat', 'weapons'),
    'crossbow': ('combat', 'weapons'),
    'helmet': ('combat', 'armor'),
    'chestplate': ('combat', 'armor'),
    'leggings': ('combat', 'armor'),
    'boots': ('combat', 'armor'),
    'horse_armor': ('combat', 'armor'),
    # food
    'apple': ('food', 'food'),
    'beef': ('food', 'food'),
    'chicken': ('food', 'food'),
    'porkchop': ('food', 'food'),
    'mutton': ('food', 'food'),
    'rabbit': ('food', 'food'),
    'cod': ('food', 'food'),
    'salmon': ('food', 'food'),
    'bread': ('food', 'food'),
    'cookie': ('food', 'food'),
    'cake': ('food', 'food'),
    'stew': ('food', 'food'),
    'soup': ('food', 'food'),
    'pie': ('food', 'food'),
}

# ============================================================
# 3. 需要补全的缺失物品
# ============================================================

COLORS = ['white','orange','magenta','light_blue','yellow','lime','pink','gray','light_gray','cyan','purple','blue','brown','green','red','black']
WOODS = ['oak','spruce','birch','jungle','acacia','dark_oak','mangrove','cherry','bamboo']

# 16色必须覆盖的物品类型
COLOR_ITEMS = ['wool','carpet','bed','stained_glass','concrete','concrete_powder']
# terracotta: MC 1.21 中只有白色陶瓦有单独 ID，其他颜色通过 stained_terracotta + 颜色状态
# dye: 只补全确实存在且不在 data 中的

# 木材必须覆盖的物品类型
WOOD_ITEMS = ['stairs','slab','door','fence']

# 明确缺失的工具/武器
MISSING_TOOLS = [
    'iron_sword', 'iron_pickaxe', 'wooden_pickaxe', 'golden_pickaxe',
    'netherite_pickaxe', 'iron_hoe',
]

# ============================================================
# 4. 核心处理逻辑
# ============================================================

def classify_item(item_id):
    """根据 ID 推断分类。"""
    for pattern, (cat, sub) in CATEGORY_MAP.items():
        if pattern in item_id:
            return cat, sub

    # 默认规则
    if any(item_id.endswith('_' + s) for s in ['log','planks','stairs','slab','door','fence','fence_gate','trapdoor','button','pressure_plate']):
        return 'blocks', 'wood'
    if any(item_id.endswith('_' + s) for s in ['wool','carpet','concrete','concrete_powder','terracotta','stained_glass','glazed_terracotta']):
        return 'blocks', 'colored'
    if 'bed' in item_id:
        return 'blocks', 'colored'
    if any(item_id.startswith(s + '_') for s in WOODS) and any(s in item_id for s in ['sign','boat']):
        return 'items', 'transport' if 'boat' in item_id else 'misc'

    return 'items', 'misc'


def gen_name_zh(item_id):
    """规则生成中文名。"""
    if item_id in ZH_ITEMS:
        return ZH_ITEMS[item_id]

    # 颜色+物品模式
    for color_en, color_zh in ZH_COLORS.items():
        if item_id.startswith(color_en + '_'):
            base = item_id[len(color_en)+1:]
            if base in ZH_BASES:
                return color_zh + ZH_BASES[base]
            # 特殊处理
            for bkey, bzh in ZH_BASES.items():
                if base == bkey:
                    return color_zh + bzh

    # 木材+物品模式
    for wood_en, wood_zh in ZH_WOODS.items():
        if item_id.startswith(wood_en + '_'):
            base = item_id[len(wood_en)+1:]
            if base in ZH_BASES:
                return wood_zh + ZH_BASES[base]

    # 盔甲
    for mat, mat_zh in [('leather','皮革'),('chainmail','锁链'),('iron','铁'),('golden','金'),('diamond','钻石'),('netherite','下界合金')]:
        for slot, slot_zh in [('helmet','头盔'),('chestplate','胸甲'),('leggings','护腿'),('boots','靴子')]:
            if item_id == f'{mat}_{slot}':
                return mat_zh + slot_zh

    # 工具
    for mat, mat_zh in [('wooden','木'),('stone','石'),('iron','铁'),('golden','金'),('diamond','钻石'),('netherite','下界合金')]:
        for tool, tool_zh in [('shovel','锹'),('pickaxe','镐'),('axe','斧'),('hoe','锄'),('sword','剑')]:
            if item_id == f'{mat}_{tool}':
                return mat_zh + tool_zh

    # 船
    for w, wzh in ZH_WOODS.items():
        if item_id == f'{w}_boat': return wzh + '船'
        if item_id == f'{w}_chest_boat': return wzh + '运输船'
    if item_id == 'bamboo_raft': return '竹筏'
    if item_id == 'bamboo_chest_raft': return '竹运输筏'

    return None


def gen_acquisition(item_id):
    """根据 ID 生成获取方式。"""
    methods = []
    if item_id.endswith('_wool'):
        methods = ['羊毛修剪', '合成']
    elif item_id.endswith('_carpet'):
        methods = ['合成']
    elif item_id.endswith('_concrete'):
        methods = ['合成', '水转化']
    elif item_id.endswith('_concrete_powder'):
        methods = ['合成']
    elif item_id.endswith('_stained_glass'):
        methods = ['合成']
    elif item_id.endswith('_dye'):
        methods = ['合成', '自然获取']
    elif item_id.endswith('_bed'):
        methods = ['合成']
    elif item_id.endswith('_terracotta') or item_id.endswith('_glazed_terracotta'):
        methods = ['合成', '烧炼']
    elif any(item_id.endswith('_' + t) for t in ['pickaxe','axe','shovel','hoe','sword']):
        methods = ['合成']
    elif any(item_id.startswith(m + '_') for m in ['leather','chainmail','iron','golden','diamond','netherite']):
        methods = ['合成']
    elif item_id.endswith('_boat') or item_id.endswith('_raft'):
        methods = ['合成']
    elif item_id.endswith('_planks') or item_id.endswith('_slab') or item_id.endswith('_stairs'):
        methods = ['合成']
    elif item_id.endswith('_door') or item_id.endswith('_fence') or item_id.endswith('_fence_gate'):
        methods = ['合成']
    elif item_id.endswith('_log') or item_id.endswith('_stripped_log'):
        methods = ['自然生成', '采集']
    else:
        methods = ['未知']
    return methods


def create_item(item_id, name_zh=None, name_en=None, icon_url=None):
    """创建一个新的物品条目。"""
    cat, sub = classify_item(item_id)
    zh = name_zh or gen_name_zh(item_id) or item_id
    en = name_en or item_id.replace('_', ' ').title()
    icon = icon_url or f'images/{item_id}.png'

    return {
        'id': item_id,
        'name_zh': zh,
        'name_en': en,
        'category': cat,
        'subcategory': sub,
        'icon_url': icon,
        'acquisition': {
            'methods': gen_acquisition(item_id),
            'natural_generation': [],
            'smelting': [],
            'trading': None,
            'drops_from': [],
        },
        'crafting': [],
        'stonecutting': None,
        'smithing': None,
        'related_items': [],
        'source': 'generated',
    }


def main():
    print('=' * 60)
    print('Data Repair Tool v1.0')
    print('=' * 60)

    # 1. 加载
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 备份
    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f'Backup: {BACKUP_PATH}')

    items = data['items']
    existing_ids = {i['id'] for i in items}
    print(f'\n[1] Loaded: {len(items)} items')

    # 2. 修复现有物品
    print('[2] Fixing existing items...')
    fixes = {'name_zh': 0, 'category': 0, 'icon_url': 0, 'acquisition': 0}

    for item in items:
        iid = item['id']

        # 修复中文名
        old_zh = item.get('name_zh', '')
        new_zh = ZH_ITEMS.get(iid) or gen_name_zh(iid)
        if new_zh and old_zh != new_zh:
            # 检查是否比当前更好
            if len(new_zh) >= len(old_zh) or old_zh == iid:
                item['name_zh'] = new_zh
                fixes['name_zh'] += 1

        # 修复分类
        new_cat, new_sub = classify_item(iid)
        if new_cat != item.get('category') or new_sub != item.get('subcategory'):
            item['category'] = new_cat
            item['subcategory'] = new_sub
            fixes['category'] += 1

        # 修复 icon_url
        old_icon = item.get('icon_url', '')
        expected = f'images/{iid}.png'
        if old_icon != expected:
            item['icon_url'] = expected
            fixes['icon_url'] += 1

        # 修复 acquisition
        methods = item.get('acquisition', {}).get('methods', [])
        if not methods or methods == ['未知']:
            item['acquisition'] = item.get('acquisition', {})
            item['acquisition']['methods'] = gen_acquisition(iid)
            fixes['acquisition'] += 1

    print(f'  name_zh: {fixes["name_zh"]}')
    print(f'  category: {fixes["category"]}')
    print(f'  icon_url: {fixes["icon_url"]}')
    print(f'  acquisition: {fixes["acquisition"]}')

    # 3. 补全缺失物品
    print('[3] Adding missing items...')
    added = []

    # 16色物品
    for base in COLOR_ITEMS:
        for color in COLORS:
            iid = f'{color}_{base}'
            if iid not in existing_ids:
                item = create_item(iid)
                items.append(item)
                added.append(iid)
                existing_ids.add(iid)

    # 木材物品
    for base in WOOD_ITEMS:
        for wood in WOODS:
            iid = f'{wood}_{base}'
            if iid not in existing_ids:
                item = create_item(iid)
                items.append(item)
                added.append(iid)
                existing_ids.add(iid)

    # 缺失工具
    for iid in MISSING_TOOLS:
        if iid not in existing_ids:
            item = create_item(iid)
            items.append(item)
            added.append(iid)
            existing_ids.add(iid)

    print(f'  Added: {len(added)}')
    if len(added) <= 50:
        for a in added:
            print(f'    + {a}')

    # 4. 删除无效数据
    print('[4] Cleaning invalid items...')
    removed = []
    to_keep = []

    for item in items:
        iid = item['id']

        # 非 snake_case
        if not re.match(r'^[a-z0-9_]+$', iid):
            removed.append(iid)
            continue

        # 空字段检查
        if not iid or not item.get('name_zh'):
            removed.append(iid)
            continue

        to_keep.append(item)

    data['items'] = to_keep
    print(f'  Removed: {len(removed)}')
    for r in removed:
        print(f'    - {r}')

    # 5. 去重
    seen = {}
    deduped = []
    dup_count = 0
    for item in to_keep:
        iid = item['id']
        if iid in seen:
            dup_count += 1
            # 保留更完整的条目
            existing = seen[iid]
            if len(item.get('crafting', [])) > len(existing.get('crafting', [])):
                deduped[deduped.index(existing)] = item
                seen[iid] = item
        else:
            seen[iid] = item
            deduped.append(item)

    data['items'] = deduped
    print(f'  Duplicates removed: {dup_count}')

    # 6. 更新 meta
    data['meta']['total_items'] = len(deduped)
    data['meta']['generated_at'] = '2026-05-04'

    # 7. 重建 categories
    cat_map = {}
    for item in deduped:
        cat = item['category']
        sub = item['subcategory']
        if cat not in cat_map:
            cat_map[cat] = {}
        if sub not in cat_map[cat]:
            cat_map[cat][sub] = []
        cat_map[cat][sub].append(item['id'])

    new_cats = []
    cat_names = {
        'blocks': ('方块', 'Blocks'),
        'items': ('物品', 'Items'),
        'tools': ('工具', 'Tools'),
        'combat': ('战斗', 'Combat'),
        'materials': ('材料', 'Materials'),
        'food': ('食物', 'Food'),
    }

    for cat_id in ['blocks', 'items', 'tools', 'combat', 'materials', 'food']:
        if cat_id in cat_map:
            subs = []
            for sub_id, sub_items in sorted(cat_map[cat_id].items()):
                first_item = sub_items[0] if sub_items else ''
                subs.append({
                    'id': sub_id,
                    'name_zh': sub_id,
                    'name_en': sub_id.replace('_', ' ').title(),
                    'items': sorted(sub_items),
                })
            new_cats.append({
                'id': cat_id,
                'name_zh': cat_names[cat_id][0],
                'name_en': cat_names[cat_id][1],
                'icon_item': cat_map[cat_id].get(list(cat_map[cat_id].keys())[0], [''])[0] if cat_map[cat_id] else '',
                'subcategories': subs,
            })

    data['categories'] = new_cats

    # 8. 保存
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    # 9. 统计
    final_count = len(deduped)
    cats = {}
    for item in deduped:
        c = item.get('category', '?')
        cats[c] = cats.get(c, 0) + 1

    print(f'\n[5] Final stats:')
    print(f'  Total items: {final_count} (was {len(items)})')
    print(f'  Added: +{len(added)}')
    print(f'  Removed: -{len(removed)}')
    print(f'  Categories:')
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f'    {c}: {n}')

    # 10. 完整性检查
    print(f'\n[6] Integrity checks:')
    # 16色检查
    color_ok = True
    for base in COLOR_ITEMS:
        missing = [f'{c}_{base}' for c in COLORS if f'{c}_{base}' not in seen]
        if missing:
            print(f'  MISSING {base}: {missing}')
            color_ok = False
    if color_ok:
        print(f'  16-color: COMPLETE ({len(COLOR_ITEMS)} types x {len(COLORS)} colors = {len(COLOR_ITEMS)*len(COLORS)})')

    # 图片检查
    remote_icons = sum(1 for i in deduped if i.get('icon_url', '').startswith('http'))
    expected_icons = sum(1 for i in deduped if i.get('icon_url', '').startswith('images/'))
    print(f'  Remote URLs: {remote_icons}')
    print(f'  Local paths: {expected_icons}')

    # ID 唯一性
    all_ids = [i['id'] for i in deduped]
    id_dupes = len(all_ids) - len(set(all_ids))
    print(f'  Duplicate IDs: {id_dupes}')

    # 空字段
    empty_name = sum(1 for i in deduped if not i.get('name_zh'))
    empty_icon = sum(1 for i in deduped if not i.get('icon_url'))
    print(f'  Empty name_zh: {empty_name}')
    print(f'  Empty icon_url: {empty_icon}')

    print(f'\n  File size: {os.path.getsize(DATA_PATH) / 1024:.0f} KB')
    print('\nDone.')


if __name__ == '__main__':
    main()
