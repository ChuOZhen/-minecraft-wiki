# 我的世界物品百科 — 合并红石大类 + 修复中文名 提示词 V5

> **当前状态**：1612 物品，10 大类，分类结构健康，中文名覆盖率 80.3%
> **本次目标**：① 红石并入功能方块（10大类→9大类）② 中文名覆盖率从 80.3% 提升至 ≥95%

---

## 一、任务一：合并红石到功能方块

### 1.1 目标

将 `redstone` 大类整体并入 `functional_blocks`，作为其子类。大类从 10 个减为 **9 个**。

### 1.2 操作步骤

**Step 1：修改所有红石物品的 category 字段**

对 `docs/data/data.json` 中所有 `"category": "redstone"` 的物品，改为 `"category": "functional_blocks"`。subcategory（power / transmission / action / minecart）保持不变。

受影响物品数：39 个（当前 redstone 大类下的全部物品）。

**Step 2：更新 secondary_categories 中的 "redstone" 引用**

所有物品的 `secondary_categories` 数组中，将 `"redstone"` 替换为 `"functional_blocks"`。

受影响物品数：52 个（buttons, campfire, soul_campfire, trapped_chest, lectern, daylight_detector, iron_door, iron_trapdoor, note_block, bell 等）。

注意：如果替换后 `secondary_categories` 与 `category` 相同（例如某物品 category 已是 `functional_blocks` 且 secondary 也是 `functional_blocks`），则从 secondary 数组中移除该项，避免自己引用自己。

**Step 3：修复 secondary_categories 中的坏值 "enchanting"**

`chiseled_bookshelf` 的 `secondary_categories` 中有 `"enchanting"`，这不是有效大类名。改为 `"functional_blocks"`。

**Step 4：重建 categories 数组**

从 items 重新聚合生成 categories 数组：

```
functional_blocks 的子类合并后为：
  door_trapdoor, enchanting, light, rail, storage, technical, utility, workstation
  + action, minecart, power, transmission（原 redstone 子类）
  = 12 个子类
```

大类顺序（9个）：
1. building_blocks
2. colored_blocks
3. natural_blocks
4. functional_blocks
5. tools
6. combat
7. food
8. materials
9. miscellaneous

**Step 5：验证**

```
✅ items 总数仍为 1612
✅ 无 "category": "redstone" 的物品
✅ 无 secondary_categories 含 "redstone"
✅ 无 secondary_categories 含 "enchanting"
✅ 无 category == secondary 任一值的情况
✅ functional_blocks 大类物品数 = 133 + 39 = 172
✅ functional_blocks 含 12 个子类
```

---

## 二、任务二：批量修复中文名

### 2.1 当前问题

317 个物品标记了 `zh_fallback: true`，中文名直接使用英文名。覆盖率仅 80.3%，远低于 95% 目标。

### 2.2 修复策略

**优先级分三档**：

| 优先级 | 特征 | 数量 | 方法 |
|--------|------|------|------|
| P1 高 | 常见物品，中文名明确（axe→斧、hoe→锄等） | ~80 | 内置硬编码映射表直接替换 |
| P2 中 | 中文名可从英文名推断（pattern 明确） | ~150 | 规则引擎批量生成 |
| P3 低 | 需要查 zh.minecraft.wiki 确认 | ~87 | AI API 批量翻译 |

### 2.3 P1：硬编码映射表（直接替换）

以下映射表覆盖常见 zh_fallback 物品，脚本直接替换，不走 AI：

```python
FALLBACK_FIX_MAP = {
    # 工具
    "axe": "斧", "hoe": "锄", "pickaxe": "镐", "shovel": "锹",
    "wooden_axe": "木斧", "wooden_hoe": "木锄", "wooden_pickaxe": "木镐", "wooden_shovel": "木锹",
    "stone_axe": "石斧", "stone_hoe": "石锄", "stone_pickaxe": "石镐", "stone_shovel": "石锹",
    "iron_axe": "铁斧", "iron_hoe": "铁锄", "iron_pickaxe": "铁镐", "iron_shovel": "铁锹",
    "golden_axe": "金斧", "golden_hoe": "金锄", "golden_pickaxe": "金镐", "golden_shovel": "金锹",
    "diamond_axe": "钻石斧", "diamond_hoe": "钻石锄", "diamond_pickaxe": "钻石镐", "diamond_shovel": "钻石锹",
    "netherite_axe": "下界合金斧", "netherite_hoe": "下界合金锄", "netherite_pickaxe": "下界合金镐", "netherite_shovel": "下界合金锹",
    # 武器/防具（通用名）
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
    # 功能方块
    "beehive": "蜂箱", "composter": "堆肥桶", "scaffolding": "脚手架",
    "loom": "织布机", "grindstone": "砂轮", "cartography_table": "制图台",
    "fletching_table": "制箭台", "smithing_table": "锻造台", "stonecutter": "切石机",
    "brewing_stand": "酿造台", "cauldron": "炼药锅", "bell": "钟",
    "jukebox": "唱片机", "lodestone": "磁石", "respawn_anchor": "重生锚",
    "ender_chest": "末影箱", "barrel": "木桶", "blast_furnace": "高炉", "smoker": "烟熏炉",
    # 材料
    "copper": "铜锭", "copper_nugget": "铜粒", "amethyst": "紫水晶",
    "netherite_scrap": "下界合金碎片", "echo_shard": "回响碎片",
    "armadillo_scute": "犰狳鳞甲", "breeze_rod": "旋风棒", "heavy_core": "重质核心",
    "ominous_bottle": "不祥之瓶", "ominous_trial_key": "不祥试炼钥匙",
    # 自然方块
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
    "shroomlight": "菌光体",
    "sweet_berry_bush": "甜浆果丛",
    "chorus_flower": "紫颂花", "chorus_plant": "紫颂植株",
    "brown_mushroom_block": "棕色蘑菇方块", "red_mushroom_block": "红色蘑菇方块",
    "mushroom_stem": "蘑菇柄",
    # 食物
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
    # 杂项
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
    # 彩色
    "white_dye": "白色染料", "orange_dye": "橙色染料",
    "magenta_dye": "品红色染料", "light_blue_dye": "淡蓝色染料",
    "yellow_dye": "黄色染料", "lime_dye": "黄绿色染料",
    "pink_dye": "粉色染料", "gray_dye": "灰色染料",
    "light_gray_dye": "淡灰色染料", "cyan_dye": "青色染料",
    "purple_dye": "紫色染料", "blue_dye": "蓝色染料",
    "brown_dye": "棕色染料", "green_dye": "绿色染料",
    "red_dye": "红色染料", "black_dye": "黑色染料",
    "ink_sac": "墨囊", "glow_ink_sac": "荧光墨囊", "bone_meal": "骨粉",
    # 红石 (并入 functional_blocks)
    "redstone_dust": "红石粉", "redstone_torch": "红石火把",
    "redstone_repeater": "红石中继器", "redstone_comparator": "红石比较器",
    "observer": "侦测器", "target": "标靶",
    "daylight_detector": "阳光探测器", "tripwire_hook": "绊线钩",
    "lever": "拉杆",
    "dispenser": "发射器", "dropper": "投掷器", "piston": "活塞",
    "sticky_piston": "黏性活塞",
    "note_block": "音符盒", "redstone_lamp": "红石灯",
    "sculk_sensor": "幽匿感测体", "calibrated_sculk_sensor": "校频幽匿感测体",
    # 远程武器
    "wind_charge": "风弹", "fire_charge": "火焰弹", "firework_rocket": "烟花火箭",
    "arrow": "箭", "spectral_arrow": "光灵箭", "tipped_arrow": "药箭",
    "trident": "三叉戟", "mace": "重锤",
    "fishing_rod": "钓鱼竿", "carrot_on_a_stick": "胡萝卜钓竿",
    "warped_fungus_on_a_stick": "诡异菌钓竿",
    "crossbow": "弩", "shield": "盾牌", "totem_of_undying": "不死图腾",
    # 材料-合成
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
    "brick": "砖(物品)", "nether_brick": "下界砖(物品)",
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
}
```

### 2.4 P2：规则引擎批量生成

以下模式可用规则自动生成中文名，无需 AI：

```python
def rule_based_translation(item_id, name_en):
    """Rule-based Chinese name generation for patterned items."""
    
    # 材质前缀 + 工具/武器名
    MATERIALS = {
        'wooden': '木', 'stone': '石', 'iron': '铁', 'golden': '金',
        'diamond': '钻石', 'netherite': '下界合金'
    }
    TOOLS = {'axe': '斧', 'hoe': '锄', 'pickaxe': '镐', 'shovel': '锹',
             'sword': '剑', 'helmet': '头盔', 'chestplate': '胸甲',
             'leggings': '护腿', 'boots': '靴子'}
    
    # 颜色前缀 + 类型（colored_blocks 颜色前缀补全）
    COLORS = {
        'white': '白色', 'orange': '橙色', 'magenta': '品红色',
        'light_blue': '淡蓝色', 'yellow': '黄色', 'lime': '黄绿色',
        'pink': '粉色', 'gray': '灰色', 'light_gray': '淡灰色',
        'cyan': '青色', 'purple': '紫色', 'blue': '蓝色',
        'brown': '棕色', 'green': '绿色', 'red': '红色', 'black': '黑色'
    }
    COLORED_TYPES = {
        'wool': '羊毛', 'carpet': '地毯', 'concrete': '混凝土',
        'concrete_powder': '混凝土粉末', 'terracotta': '陶瓦',
        'glazed_terracotta': '带釉陶瓦', 'stained_glass': '染色玻璃',
        'stained_glass_pane': '染色玻璃板', 'bed': '床',
        'candle': '蜡烛', 'shulker_box': '潜影盒', 'banner': '旗帜'
    }
    
    # 树种
    WOOD_TYPES = {
        'oak': '橡木', 'spruce': '云杉', 'birch': '白桦',
        'jungle': '丛林', 'acacia': '金合欢', 'dark_oak': '深色橡木',
        'mangrove': '红树', 'cherry': '樱花', 'pale_oak': '苍白橡木',
        'bamboo': '竹', 'crimson': '绯红', 'warped': '诡异'
    }
    WOOD_PARTS = {
        'log': '原木', 'stripped_log': '去皮原木', 'wood': '木头',
        'stripped_wood': '去皮木头', 'planks': '木板', 'slab': '台阶',
        'stairs': '楼梯', 'fence': '栅栏', 'fence_gate': '栅栏门',
        'door': '门', 'trapdoor': '活板门', 'button': '按钮',
        'pressure_plate': '压力板', 'sign': '告示牌',
        'hanging_sign': '悬挂式告示牌', 'mosaic': '马赛克',
        'mosaic_slab': '马赛克台阶', 'mosaic_stairs': '马赛克楼梯',
    }
    
    # 石头种类
    STONE_TYPES = {
        'stone': '石头', 'cobblestone': '圆石', 'granite': '花岗岩',
        'diorite': '闪长岩', 'andesite': '安山岩', 'sandstone': '砂岩',
        'red_sandstone': '红砂岩', 'blackstone': '黑石',
        'basalt': '玄武岩', 'deepslate': '深板岩', 'tuff': '凝灰岩',
        'calcite': '方解石', 'dripstone': '滴水石',
        'polished_granite': '磨制花岗岩', 'polished_diorite': '磨制闪长岩',
        'polished_andesite': '磨制安山岩', 'polished_deepslate': '磨制深板岩',
        'polished_blackstone': '磨制黑石', 'polished_tuff': '磨制凝灰岩',
        'cobbled_deepslate': '深板岩圆石',
    }
    STONE_PARTS = {'slab': '台阶', 'stairs': '楼梯', 'wall': '墙'}
    
    # 砖种类
    BRICK_TYPES = {
        'brick': '红砖', 'stone_brick': '石砖', 'nether_brick': '下界砖',
        'red_nether_brick': '红色下界砖', 'mud_brick': '泥砖',
        'deepslate_brick': '深板岩砖', 'tuff_brick': '凝灰岩砖',
        'prismarine_brick': '海晶石砖', 'end_stone_brick': '末地石砖',
        'blackstone_brick': '黑石砖', 'quartz_brick': '石英砖',
        'cracked_stone_brick': '裂纹石砖', 'cracked_deepslate_brick': '裂纹深板岩砖',
        'cracked_nether_brick': '裂纹下界砖', 'cracked_polished_blackstone_brick': '裂纹磨制黑石砖',
        'chiseled_stone_brick': '錾制石砖', 'chiseled_deepslate': '錾制深板岩',
        'chiseled_nether_brick': '錾制下界砖', 'chiseled_polished_blackstone': '錾制磨制黑石',
        'chiseled_tuff': '錾制凝灰岩', 'chiseled_tuff_brick': '錾制凝灰岩砖',
        'mossy_stone_brick': '苔石砖', 'mossy_cobblestone': '苔石',
    }
    
    # ... 规则匹配逻辑
    # （实际脚本中实现完整匹配链）
```

### 2.5 P3：AI API 批量翻译

对于 P1 映射表和 P2 规则引擎都未覆盖的 zh_fallback 物品，调用 DeepSeek API 翻译。

**System Prompt**:
```
你是Minecraft中文翻译专家。请将以下物品的英文名翻译为Minecraft官方简体中文译名。

要求：
1. 使用 Minecraft 简体中文官方译名风格（与 zh.minecraft.wiki 一致）
2. 物品ID会以 id 字段给出，可辅助判断
3. 每种物品返回：{"id": "..", "name_zh": "中文译名"}
4. 只返回 JSON 数组，不要解释
```

批次：每批 80-100 个，temperature=0.0，max_tokens=4096。

### 2.6 修正后的验证

```
✅ zh_fallback 从 317 降到 ≤ 80（覆盖率 ≥ 95%）
   - P1 硬编码：~200 个
   - P2 规则引擎：~40 个  
   - P3 AI 翻译：~77 个
   剩余 zh_fallback < 5% ≈ 80 个

✅ 59 个 colored_blocks 缺少颜色前缀 → 全部修正
✅ 所有 stripped_log 中文名格式正确
✅ name_zh 无与 name_en 相同且无 zh_fallback 标记的漏网之鱼
```

---

## 三、完整处理脚本大纲

```python
#!/usr/bin/env python3
"""
fix_v5.py — 合并红石 + 修复中文名
输出: docs/data/data.json (原地更新，先备份)
"""

import json, os, sys, time
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / 'docs' / 'data' / 'data.json'

def backup():
    """备份 data.json"""
    import shutil
    backup_path = DATA_PATH.with_suffix('.json.backup_v5')
    shutil.copy(DATA_PATH, backup_path)
    print(f"备份: {backup_path}")

def merge_redstone(data):
    """将红石大类并入功能方块"""
    print("\n=== 合并红石 → 功能方块 ===")
    items = data['items']
    changes = 0
    sec_changes = 0
    
    for item in items:
        # 1. category: redstone → functional_blocks
        if item.get('category') == 'redstone':
            item['category'] = 'functional_blocks'
            changes += 1
        
        # 2. secondary_categories: "redstone" → "functional_blocks"
        secs = item.get('secondary_categories', [])
        if 'redstone' in secs:
            new_secs = ['functional_blocks' if s == 'redstone' else s for s in secs]
            item['secondary_categories'] = new_secs
            sec_changes += 1
        
        # 3. Fix "enchanting" → "functional_blocks"
        if 'enchanting' in item.get('secondary_categories', []):
            new_secs = ['functional_blocks' if s == 'enchanting' else s for s in item.get('secondary_categories', [])]
            item['secondary_categories'] = new_secs
            sec_changes += 1
        
        # 4. Remove self-referencing secondary
        cat = item.get('category')
        secs = item.get('secondary_categories', [])
        if cat in secs:
            item['secondary_categories'] = [s for s in secs if s != cat]
    
    print(f"  category 变更: {changes} 个")
    print(f"  secondary 变更: {sec_changes} 个")
    
    # Rebuild categories
    rebuild_categories(data)
    return data

def apply_fallback_fix_map(items):
    """应用 P1 硬编码映射"""
    print("\n=== P1: 硬编码映射表 ===")
    # FALLBACK_FIX_MAP 从第二节 2.3 加载
    fixed = 0
    for item in items:
        if item.get('zh_fallback') and item['id'] in FALLBACK_FIX_MAP:
            item['name_zh'] = FALLBACK_FIX_MAP[item['id']]
            item['zh_fallback'] = False
            fixed += 1
    print(f"  修正: {fixed} 个")
    return fixed

def apply_rule_translations(items):
    """应用 P2 规则引擎"""
    print("\n=== P2: 规则引擎 ===")
    fixed = 0
    for item in items:
        if not item.get('zh_fallback'):
            continue
        zh = generate_rule_based_name(item['id'], item['name_en'])
        if zh and zh != item['name_en']:
            item['name_zh'] = zh
            item['zh_fallback'] = False
            fixed += 1
    print(f"  修正: {fixed} 个")
    return fixed

def ai_translate_remaining(items):
    """P3: AI 批量翻译剩余的 zh_fallback"""
    print("\n=== P3: AI 翻译 ===")
    remaining = [i for i in items if i.get('zh_fallback')]
    if not remaining:
        print("  无需翻译")
        return 0
    
    print(f"  剩余: {len(remaining)} 个")
    # 调用 DeepSeek API（每批 100 个）
    # ... 
    return fixed

def verify(data):
    """最终验证"""
    items = data['items']
    cats = data['categories']
    
    errors = []
    # 1. 总数
    if len(items) != 1612:
        errors.append(f"物品数: {len(items)} != 1612")
    
    # 2. 无 redstone 大类
    has_redstone_cat = any(c['id'] == 'redstone' for c in cats)
    if has_redstone_cat:
        errors.append("仍存在 redstone 大类")
    
    # 3. 无物品 category=redstone
    redstone_items = [i['id'] for i in items if i.get('category') == 'redstone']
    if redstone_items:
        errors.append(f"仍存在 category=redstone 的物品: {redstone_items}")
    
    # 4. 无 secondary 含 redstone/enchanting
    bad_sec = []
    for i in items:
        for s in i.get('secondary_categories', []):
            if s in ('redstone', 'enchanting'):
                bad_sec.append(i['id'])
                break
    if bad_sec:
        errors.append(f"secondary 仍含坏值: {bad_sec}")
    
    # 5. 中文名覆盖率
    fb = sum(1 for i in items if i.get('zh_fallback'))
    cov = (len(items) - fb) / len(items) * 100
    if cov < 95:
        errors.append(f"中文名覆盖率: {cov:.1f}% < 95% (剩余 fallback: {fb})")
    
    # 6. 颜色前缀
    missing_color = count_missing_color_prefix(items)
    if missing_color > 0:
        errors.append(f"colored_blocks 缺少颜色前缀: {missing_color}")
    
    # 7. 大类数量
    if len(cats) != 9:
        errors.append(f"大类数量: {len(cats)} != 9")
    
    if errors:
        print("\n=== 验证失败 ===")
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print(f"\n=== 验证通过 ===")
        print(f"  ✅ 物品总数: {len(items)}")
        print(f"  ✅ 大类: {len(cats)} 个")
        print(f"  ✅ 中文名覆盖率: {cov:.1f}%")
        print(f"  ✅ functional_blocks: {sum(1 for i in items if i.get('category')=='functional_blocks')} 物品, 12 子类")
    
    return len(errors) == 0

def main():
    backup()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Phase 1: 合并红石
    data = merge_redstone(data)
    
    # Phase 2: 中文名
    items = data['items']
    n1 = apply_fallback_fix_map(items)
    n2 = apply_rule_translations(items)
    n3 = ai_translate_remaining(items)
    print(f"\n中文名修复总计: {n1+n2+n3}")
    
    # Phase 3: 重建 categories + 排序
    rebuild_categories(data)
    
    # Phase 4: 保存
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    
    # Phase 5: 验证
    verify(data)

if __name__ == '__main__':
    main()
```

---

## 四、成功标准

```
✅ 大类从 10 减为 9（redstone 并入 functional_blocks）
✅ functional_blocks 含 12 子类（原 8 个 + redstone 的 4 个）
✅ 无 category="redstone" 的物品
✅ 无 secondary_categories 中 "redstone" 或 "enchanting" 坏值
✅ 物品总数保持 1612
✅ 中文名覆盖率 ≥ 95%（zh_fallback ≤ 80）
✅ colored_blocks 颜色前缀 59 个缺失全部修正
✅ 无 name_zh == name_en 的未标记条目
```
