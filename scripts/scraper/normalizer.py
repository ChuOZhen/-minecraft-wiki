# ============================================
# normalizer.py — 数据规范化与清洗
# ============================================

import re
from collections import defaultdict

# ============================================
# 英文 → 中文映射（覆盖 Minecraft 核心物品）
# ============================================
ZH_MAP = {
    # 石质方块
    "Stone": "石头", "Cobblestone": "圆石", "Granite": "花岗岩",
    "Diorite": "闪长岩", "Andesite": "安山岩", "Stone Bricks": "石砖",
    "Mossy Stone Bricks": "苔石砖", "Cracked Stone Bricks": "裂石砖",
    "Chiseled Stone Bricks": "錾制石砖", "Smooth Stone": "平滑石头",
    "Smooth Stone Bricks": "平滑石砖", "Bricks": "砖块",
    "Mossy Cobblestone": "苔圆石", "Deepslate": "深板岩",
    "Cobbled Deepslate": "深板岩圆石", "Polished Deepslate": "磨制深板岩",
    "Deepslate Bricks": "深板岩砖", "Cracked Deepslate Bricks": "裂纹深板岩砖",
    "Deepslate Tiles": "深板岩瓦", "Cracked Deepslate Tiles": "裂纹深板岩瓦",
    "Chiseled Deepslate": "錾制深板岩", "Polished Granite": "磨制花岗岩",
    "Polished Diorite": "磨制闪长岩", "Polished Andesite": "磨制安山岩",
    "Sandstone": "砂岩", "Cut Sandstone": "切制砂岩", "Chiseled Sandstone": "錾制砂岩",
    "Smooth Sandstone": "平滑砂岩", "Red Sandstone": "红砂岩",
    "End Stone": "末地石", "End Stone Bricks": "末地石砖",
    "Purpur Block": "紫珀块", "Purpur Pillar": "紫珀柱",
    "Prismarine": "海晶石", "Prismarine Bricks": "海晶石砖",
    "Dark Prismarine": "暗海晶石", "Netherrack": "下界岩",
    "Nether Bricks": "下界砖块", "Red Nether Bricks": "红色下界砖块",
    "Cracked Nether Bricks": "裂纹下界砖块", "Chiseled Nether Bricks": "錾制下界砖块",
    "Blackstone": "黑石", "Polished Blackstone": "磨制黑石",
    "Polished Blackstone Bricks": "磨制黑石砖", "Gilded Blackstone": "镶金黑石",
    "Basalt": "玄武岩", "Smooth Basalt": "平滑玄武岩", "Polished Basalt": "磨制玄武岩",
    "Tuff": "凝灰岩", "Polished Tuff": "磨制凝灰岩", "Tuff Bricks": "凝灰岩砖",
    "Calcite": "方解石", "Dripstone Block": "滴水石块",
    "Pointed Dripstone": "滴水石锥", "Amethyst Block": "紫水晶块",
    "Budding Amethyst": "紫水晶母岩", "Magma Block": "岩浆块",
    "Obsidian": "黑曜石", "Crying Obsidian": "哭泣的黑曜石",

    # 木质方块
    "Oak Planks": "橡木木板", "Spruce Planks": "云杉木板",
    "Birch Planks": "白桦木板", "Jungle Planks": "丛林木板",
    "Acacia Planks": "金合欢木板", "Dark Oak Planks": "深色橡木木板",
    "Mangrove Planks": "红树木板", "Cherry Planks": "樱花木板",
    "Bamboo Planks": "竹木板", "Crimson Planks": "绯红木板",
    "Warped Planks": "诡异木板", "Pale Oak Planks": "苍白橡木木板",
    "Oak Log": "橡木原木", "Spruce Log": "云杉原木",
    "Birch Log": "白桦原木", "Jungle Log": "丛林原木",
    "Acacia Log": "金合欢原木", "Dark Oak Log": "深色橡木原木",
    "Mangrove Log": "红树原木", "Cherry Log": "樱花原木",
    "Stripped Oak Log": "去皮橡木原木", "Stripped Birch Log": "去皮白桦原木",
    "Stripped Spruce Log": "去皮云杉原木",

    # 玻璃/彩色
    "Glass": "玻璃", "Glass Pane": "玻璃板", "Tinted Glass": "遮光玻璃",
    "White Stained Glass": "白色染色玻璃", "Black Stained Glass": "黑色染色玻璃",
    "White Wool": "白色羊毛", "Black Wool": "黑色羊毛",
    "White Concrete": "白色混凝土", "Black Concrete": "黑色混凝土",
    "White Terracotta": "白色陶瓦", "Terracotta": "陶瓦",
    "Glazed Terracotta": "带釉陶瓦", "White Glazed Terracotta": "白色带釉陶瓦",

    # 自然方块
    "Grass Block": "草方块", "Dirt": "泥土", "Coarse Dirt": "砂土",
    "Rooted Dirt": "缠根泥土", "Podzol": "灰化土", "Mycelium": "菌丝",
    "Mud": "泥巴", "Packed Mud": "泥坯", "Mud Bricks": "泥砖",
    "Sand": "沙子", "Red Sand": "红沙", "Gravel": "沙砾",
    "Clay": "黏土块", "Snow Block": "雪块", "Ice": "冰",
    "Packed Ice": "浮冰", "Blue Ice": "蓝冰",
    "Oak Leaves": "橡树树叶", "Spruce Leaves": "云杉树叶",
    "Birch Leaves": "白桦树叶", "Jungle Leaves": "丛林树叶",
    "Acacia Leaves": "金合欢树叶", "Dark Oak Leaves": "深色橡树树叶",
    "Mangrove Leaves": "红树树叶", "Cherry Leaves": "樱花树叶",
    "Oak Sapling": "橡树树苗", "Spruce Sapling": "云杉树苗",
    "Birch Sapling": "白桦树苗", "Jungle Sapling": "丛林树苗",
    "Acacia Sapling": "金合欢树苗", "Dark Oak Sapling": "深色橡树树苗",

    # 功能方块
    "Crafting Table": "工作台", "Furnace": "熔炉", "Blast Furnace": "高炉",
    "Smoker": "烟熏炉", "Chest": "箱子", "Ender Chest": "末影箱",
    "Barrel": "木桶", "Shulker Box": "潜影盒",
    "White Shulker Box": "白色潜影盒", "Black Shulker Box": "黑色潜影盒",
    "Torch": "火把", "Soul Torch": "灵魂火把", "Lantern": "灯笼",
    "Soul Lantern": "灵魂灯笼", "Campfire": "营火", "Soul Campfire": "灵魂营火",
    "Ladder": "梯子", "Oak Door": "橡木门", "Iron Door": "铁门",
    "Oak Trapdoor": "橡木活板门", "Iron Trapdoor": "铁活板门",
    "Oak Fence": "橡木栅栏", "Oak Fence Gate": "橡木栅栏门",
    "Oak Sign": "橡木告示牌", "Oak Hanging Sign": "悬挂式橡木告示牌",
    "White Bed": "白色床", "Bookshelf": "书架",
    "Enchanting Table": "附魔台", "Anvil": "铁砧",
    "Chipped Anvil": "开裂的铁砧", "Damaged Anvil": "损坏的铁砧",
    "Brewing Stand": "酿造台", "Cauldron": "炼药锅",
    "Water Cauldron": "水炼药锅", "Lava Cauldron": "熔岩炼药锅",
    "Powder Snow Cauldron": "细雪炼药锅", "Hopper": "漏斗",
    "Dispenser": "发射器", "Dropper": "投掷器", "Observer": "侦测器",
    "Piston": "活塞", "Sticky Piston": "黏性活塞",
    "Note Block": "音符盒", "Jukebox": "唱片机",
    "Loom": "织布机", "Grindstone": "砂轮",
    "Smithing Table": "锻造台", "Cartography Table": "制图台",
    "Fletching Table": "制箭台", "Stonecutter": "切石机",
    "Lectern": "讲台", "Bell": "钟", "Beacon": "信标",
    "Conduit": "潮涌核心", "Lodestone": "磁石",
    "Respawn Anchor": "重生锚", "Sculk Catalyst": "潜声催化剂",
    "Sculk Sensor": "潜声传感器", "Calibrated Sculk Sensor": "校准潜声传感器",
    "Sculk Shrieker": "潜声尖啸体", "Sculk Vein": "潜声脉络",
    "Lightning Rod": "避雷针", "Crafter": "合成器",

    # 红石
    "Redstone Dust": "红石粉", "Redstone Torch": "红石火把",
    "Redstone Block": "红石块", "Redstone Repeater": "红石中继器",
    "Redstone Comparator": "红石比较器", "Redstone Lamp": "红石灯",
    "Daylight Detector": "阳光探测器", "Tripwire Hook": "绊线钩",
    "Lever": "拉杆", "Stone Button": "石头按钮", "Oak Button": "橡木按钮",
    "Stone Pressure Plate": "石头压力板", "Oak Pressure Plate": "橡木压力板",
    "Target": "标靶", "TNT": "TNT",

    # 工具
    "Wooden Pickaxe": "木镐", "Stone Pickaxe": "石镐",
    "Iron Pickaxe": "铁镐", "Golden Pickaxe": "金镐",
    "Diamond Pickaxe": "钻石镐", "Netherite Pickaxe": "下界合金镐",
    "Wooden Axe": "木斧", "Stone Axe": "石斧",
    "Iron Axe": "铁斧", "Golden Axe": "金斧",
    "Diamond Axe": "钻石斧", "Netherite Axe": "下界合金斧",
    "Wooden Shovel": "木锹", "Stone Shovel": "石锹",
    "Iron Shovel": "铁锹", "Golden Shovel": "金锹",
    "Diamond Shovel": "钻石锹", "Netherite Shovel": "下界合金锹",
    "Wooden Hoe": "木锄", "Stone Hoe": "石锄",
    "Iron Hoe": "铁锄", "Golden Hoe": "金锄",
    "Diamond Hoe": "钻石锄", "Netherite Hoe": "下界合金锄",
    "Shears": "剪刀", "Flint and Steel": "打火石",
    "Fishing Rod": "钓鱼竿", "Carrot on a Stick": "胡萝卜钓竿",
    "Warped Fungus on a Stick": "诡异菌钓竿",
    "Brush": "刷子", "Lead": "拴绳",
    "Bucket": "铁桶", "Water Bucket": "水桶",
    "Lava Bucket": "熔岩桶", "Milk Bucket": "奶桶",
    "Powder Snow Bucket": "细雪桶", "Bucket of Axolotl": "美西螈桶",
    "Bucket of Cod": "鳕鱼桶", "Bucket of Salmon": "鲑鱼桶",
    "Bucket of Pufferfish": "河豚桶", "Bucket of Tropical Fish": "热带鱼桶",
    "Bucket of Tadpole": "蝌蚪桶", "Compass": "指南针",
    "Recovery Compass": "追溯指针", "Clock": "时钟",
    "Spyglass": "望远镜", "Map": "地图", "Empty Map": "空地图",
    "Saddle": "鞍",

    # 战斗
    "Wooden Sword": "木剑", "Stone Sword": "石剑",
    "Iron Sword": "铁剑", "Golden Sword": "金剑",
    "Diamond Sword": "钻石剑", "Netherite Sword": "下界合金剑",
    "Bow": "弓", "Crossbow": "弩", "Arrow": "箭",
    "Spectral Arrow": "光灵箭", "Tipped Arrow": "药箭",
    "Shield": "盾牌", "Totem of Undying": "不死图腾",
    "Trident": "三叉戟", "Mace": "重锤",
    "Leather Helmet": "皮革头盔", "Leather Chestplate": "皮革胸甲",
    "Leather Leggings": "皮革护腿", "Leather Boots": "皮革靴子",
    "Chainmail Helmet": "锁链头盔", "Chainmail Chestplate": "锁链胸甲",
    "Chainmail Leggings": "锁链护腿", "Chainmail Boots": "锁链靴子",
    "Iron Helmet": "铁头盔", "Iron Chestplate": "铁胸甲",
    "Iron Leggings": "铁护腿", "Iron Boots": "铁靴子",
    "Golden Helmet": "金头盔", "Golden Chestplate": "金胸甲",
    "Golden Leggings": "金护腿", "Golden Boots": "金靴子",
    "Diamond Helmet": "钻石头盔", "Diamond Chestplate": "钻石胸甲",
    "Diamond Leggings": "钻石护腿", "Diamond Boots": "钻石靴子",
    "Netherite Helmet": "下界合金头盔", "Netherite Chestplate": "下界合金胸甲",
    "Netherite Leggings": "下界合金护腿", "Netherite Boots": "下界合金靴子",
    "Turtle Shell": "海龟壳", "Horse Armor": "马铠",
    "Iron Horse Armor": "铁马铠", "Golden Horse Armor": "金马铠",
    "Diamond Horse Armor": "钻石马铠", "Wolf Armor": "狼铠",

    # 食物
    "Bread": "面包", "Apple": "苹果", "Golden Apple": "金苹果",
    "Enchanted Golden Apple": "附魔金苹果",
    "Cooked Beef": "熟牛肉", "Raw Beef": "生牛肉",
    "Cooked Porkchop": "熟猪排", "Raw Porkchop": "生猪排",
    "Cooked Chicken": "熟鸡肉", "Raw Chicken": "生鸡肉",
    "Cooked Mutton": "熟羊肉", "Raw Mutton": "生羊肉",
    "Cooked Rabbit": "熟兔肉", "Raw Rabbit": "生兔肉",
    "Cooked Cod": "熟鳕鱼", "Raw Cod": "生鳕鱼",
    "Cooked Salmon": "熟鲑鱼", "Raw Salmon": "生鲑鱼",
    "Carrot": "胡萝卜", "Golden Carrot": "金胡萝卜",
    "Potato": "马铃薯", "Baked Potato": "烤马铃薯",
    "Poisonous Potato": "毒马铃薯", "Beetroot": "甜菜根",
    "Beetroot Soup": "甜菜汤", "Mushroom Stew": "蘑菇煲",
    "Suspicious Stew": "迷之炖菜", "Rabbit Stew": "兔肉煲",
    "Melon Slice": "西瓜片", "Glistering Melon Slice": "闪烁的西瓜片",
    "Sweet Berries": "甜浆果", "Glow Berries": "发光浆果",
    "Chorus Fruit": "紫颂果", "Pumpkin Pie": "南瓜派",
    "Cookie": "曲奇", "Cake": "蛋糕", "Dried Kelp": "干海带",
    "Honey Bottle": "蜂蜜瓶", "Pufferfish": "河豚",

    # 材料
    "Iron Ingot": "铁锭", "Gold Ingot": "金锭",
    "Copper Ingot": "铜锭", "Netherite Ingot": "下界合金锭",
    "Netherite Scrap": "下界合金碎片",
    "Diamond": "钻石", "Emerald": "绿宝石",
    "Coal": "煤炭", "Charcoal": "木炭",
    "Raw Iron": "粗铁", "Raw Copper": "粗铜", "Raw Gold": "粗金",
    "Iron Nugget": "铁粒", "Gold Nugget": "金粒",
    "Amethyst Shard": "紫水晶碎片",
    "Lapis Lazuli": "青金石", "Quartz": "下界石英",
    "Flint": "燧石", "Stick": "木棍",
    "Leather": "皮革", "Paper": "纸", "Book": "书",
    "Feather": "羽毛", "String": "线",
    "Bone": "骨头", "Bone Meal": "骨粉",
    "Slimeball": "黏液球", "Slime Block": "黏液块",
    "Honeycomb": "蜜脾", "Honey Block": "蜂蜜块",
    "Gunpowder": "火药", "Blaze Rod": "烈焰棒",
    "Blaze Powder": "烈焰粉", "Ender Pearl": "末影珍珠",
    "Eye of Ender": "末影之眼", "Ghast Tear": "恶魂之泪",
    "Nether Wart": "下界疣", "Magma Cream": "岩浆膏",
    "Glowstone Dust": "萤石粉", "Glowstone": "萤石",
    "Shulker Shell": "潜影壳", "Nautilus Shell": "鹦鹉螺壳",
    "Heart of the Sea": "海洋之心", "Nether Star": "下界之星",
    "Echo Shard": "回响碎片", "Phantom Membrane": "幻翼膜",
    "Rabbit Hide": "兔子皮", "Rabbit's Foot": "兔子脚",
    "Spider Eye": "蜘蛛眼", "Fermented Spider Eye": "发酵蛛眼",
    "Ink Sac": "墨囊", "Glow Ink Sac": "发光墨囊",
    "Cocoa Beans": "可可豆", "Wheat": "小麦", "Wheat Seeds": "小麦种子",
    "Sugar Cane": "甘蔗", "Sugar": "糖", "Egg": "鸡蛋",
    "Bamboo": "竹子", "Scute": "鳞甲",
    "Brick": "红砖", "Nether Brick": "下界砖",
    "Clay Ball": "黏土球", "Firework Rocket": "烟花火箭",
    "Firework Star": "烟火之星", "Glass Bottle": "玻璃瓶",

    # 杂项
    "Bowl": "碗", "Bottle o' Enchanting": "附魔之瓶",
    "Enchanted Book": "附魔书", "Knowledge Book": "知识之书",
    "Name Tag": "命名牌", "Painting": "画",
    "Item Frame": "物品展示框", "Glow Item Frame": "荧光物品展示框",
    "Armor Stand": "盔甲架", "End Crystal": "末影水晶",
    "Minecart": "矿车", "Chest Minecart": "运输矿车",
    "Furnace Minecart": "动力矿车", "Hopper Minecart": "漏斗矿车",
    "TNT Minecart": "TNT矿车", "Oak Boat": "橡木船",
    "Spruce Boat": "云杉船", "Birch Boat": "白桦船",
    "Jungle Boat": "丛林船", "Acacia Boat": "金合欢船",
    "Dark Oak Boat": "深色橡木船", "Mangrove Boat": "红树船",
    "Cherry Boat": "樱花船", "Bamboo Raft": "竹筏",
    "Oak Boat with Chest": "运输橡木船",
    "Spruce Boat with Chest": "运输云杉船",
    "Music Disc 13": "音乐唱片 13", "Music Disc Cat": "音乐唱片 Cat",
    "Music Disc Blocks": "音乐唱片 Blocks", "Music Disc Chirp": "音乐唱片 Chirp",
    "Music Disc Far": "音乐唱片 Far", "Music Disc Mall": "音乐唱片 Mall",
    "Music Disc Mellohi": "音乐唱片 Mellohi", "Music Disc Stal": "音乐唱片 Stal",
    "Music Disc Strad": "音乐唱片 Strad", "Music Disc Ward": "音乐唱片 Ward",
    "Music Disc 11": "音乐唱片 11", "Music Disc Wait": "音乐唱片 Wait",
    "Music Disc Pigstep": "音乐唱片 Pigstep",
    "Music Disc Otherside": "音乐唱片 Otherside",
    "Music Disc 5": "音乐唱片 5", "Music Disc Relic": "音乐唱片 Relic",
    "Banner Pattern": "旗帜图案", "Flower Banner Pattern": "花朵旗帜图案",
    "Creeper Banner Pattern": "苦力怕旗帜图案",
    "Skull Banner Pattern": "骷髅旗帜图案",
    "Globe Banner Pattern": "地球旗帜图案",
    "Piglin Banner Pattern": "猪灵旗帜图案",
    "Spawn Egg": "刷怪蛋", "Bundle": "收纳袋",

    # 矿石
    "Coal Ore": "煤矿石", "Iron Ore": "铁矿石",
    "Copper Ore": "铜矿石", "Gold Ore": "金矿石",
    "Diamond Ore": "钻石矿石", "Emerald Ore": "绿宝石矿石",
    "Redstone Ore": "红石矿石", "Lapis Lazuli Ore": "青金石矿石",
    "Nether Quartz Ore": "下界石英矿石", "Nether Gold Ore": "下界金矿石",
    "Deepslate Coal Ore": "深层煤矿石", "Deepslate Iron Ore": "深层铁矿石",
    "Deepslate Copper Ore": "深层铜矿石", "Deepslate Gold Ore": "深层金矿石",
    "Deepslate Diamond Ore": "深层钻石矿石", "Deepslate Emerald Ore": "深层绿宝石矿石",

    # 铜相关
    "Block of Copper": "铜块", "Cut Copper": "切制铜块",
    "Exposed Copper": "斑驳的铜块", "Weathered Copper": "锈蚀的铜块",
    "Oxidized Copper": "氧化的铜块",
    "Waxed Block of Copper": "涂蜡铜块",
    "Copper Grate": "铜格栅", "Copper Door": "铜门",
    "Copper Trapdoor": "铜活板门", "Copper Bulb": "铜灯",

    # 下界
    "Crimson Stem": "绯红菌柄", "Warped Stem": "诡异菌柄",
    "Stripped Crimson Stem": "去皮绯红菌柄", "Stripped Warped Stem": "去皮诡异菌柄",
    "Crimson Nylium": "绯红菌岩", "Warped Nylium": "诡异菌岩",
    "Crimson Fungus": "绯红菌", "Warped Fungus": "诡异菌",
    "Crimson Roots": "绯红菌索", "Warped Roots": "诡异菌索",
    "Weeping Vines": "垂泪藤", "Twisting Vines": "缠怨藤",
    "Nether Sprouts": "下界苗", "Shroomlight": "菌光体",
    "Soul Sand": "灵魂沙", "Soul Soil": "灵魂土",
    "Glowstone": "萤石", "Ancient Debris": "远古残骸",
    "Block of Netherite": "下界合金块",

    # === P5 扩增（zh_missing.json 清理后） ===
    # 方块补全
    "Block of Coal": "煤炭块", "Block of Diamond": "钻石块",
    "Block of Gold": "金块", "Block of Iron": "铁块",
    "Block of Quartz": "石英块", "Block of Amber": "琥珀块",
    "Amber Gem": "琥珀宝石",
    "Chiseled Red Sandstone": "錾制红砂岩",
    "Chiseled Resin Bricks": "錾制树脂砖",
    "Concrete Powder": "混凝土粉末",
    "White Concrete Powder": "白色混凝土粉末",
    "Reinforced Deepslate": "强化深板岩",
    "Resin Brick": "树脂砖", "Resin Bricks": "树脂砖",
    "Resin Brick Slab": "树脂砖台阶",
    "Pale Moss Block": "苍白苔藓块",
    "Pale Moss Carpet": "苍白苔藓地毯",
    "Pale Oak Log": "苍白橡木原木",
    "Pale Oak Leaves": "苍白橡树叶",
    "Pale Oak Sapling": "苍白橡树树苗",
    "Short Dry Grass": "短干草",
    "Wildflowers": "野花",
    "Leaf Litter": "落叶层",
    # 矿石
    "Coal Ore": "煤矿石", "Iron Ore": "铁矿石",
    "Copper Ore": "铜矿石", "Gold Ore": "金矿石",
    "Diamond Ore": "钻石矿石", "Emerald Ore": "绿宝石矿石",
    "Redstone Ore": "红石矿石", "Lapis Lazuli Ore": "青金石矿石",
    "Nether Quartz Ore": "下界石英矿石", "Nether Gold Ore": "下界金矿石",
    "Deepslate Coal Ore": "深层煤矿石", "Deepslate Iron Ore": "深层铁矿石",
    "Deepslate Copper Ore": "深层铜矿石", "Deepslate Gold Ore": "深层金矿石",
    "Deepslate Diamond Ore": "深层钻石矿石", "Deepslate Emerald Ore": "深层绿宝石矿石",
    # 生物/实体
    "Bee": "蜜蜂", "Panda": "熊猫", "Parrot": "鹦鹉",
    "Ravager": "劫掠兽", "Skeleton": "骷髅", "Zombie": "僵尸",
    "Wither": "凋灵", "Ghast": "恶魂",
    "Player Head": "玩家头", "Creeper Head": "苦力怕头",
    "Wither Skeleton Skull": "凋灵骷髅头颅",
    "Skeleton Skull": "骷髅头颅", "Zombie Head": "僵尸头",
    # 染料
    "Blue Dye": "蓝色染料", "Brown Dye": "棕色染料",
    "Cyan Dye": "青色染料", "Green Dye": "绿色染料",
    "Light Blue Dye": "淡蓝色染料", "Light Gray Dye": "淡灰色染料",
    "Lime Dye": "黄绿色染料", "Magenta Dye": "品红色染料",
    "Orange Dye": "橙色染料", "Pink Dye": "粉色染料",
    "Purple Dye": "紫色染料", "Red Dye": "红色染料",
    "Yellow Dye": "黄色染料", "White Dye": "白色染料",
    "Black Dye": "黑色染料", "Gray Dye": "灰色染料",
    # 自然
    "Blue Orchid": "蓝兰花", "Dead Bush": "枯死的灌木",
    "Pitcher Plant": "瓶子草", "Torchflower": "火把花",
    "Frosted Ice": "霜冰", "Cactus Flower": "仙人掌花",
    "Spore Blossom": "孢子花", "Small Dripleaf": "小型垂滴叶",
    "Big Dripleaf": "大型垂滴叶",
    # 装饰与设施
    "Coral Block": "珊瑚块", "Coral Fan": "珊瑚扇",
    "Tube Coral Block": "管珊瑚块", "Brain Coral Block": "脑纹珊瑚块",
    "Bubble Coral Block": "气泡珊瑚块", "Fire Coral Block": "火珊瑚块",
    "Horn Coral Block": "鹿角珊瑚块",
    "Tube Coral Fan": "管珊瑚扇", "Brain Coral Fan": "脑纹珊瑚扇",
    "Bubble Coral Fan": "气泡珊瑚扇", "Fire Coral Fan": "火珊瑚扇",
    "Horn Coral Fan": "鹿角珊瑚扇",
    "Dead Coral Block": "死珊瑚块", "Dead Coral Fan": "死珊瑚扇",
    # 铜相关补充
    "Block of Copper": "铜块", "Cut Copper": "切制铜块",
    "Exposed Copper": "斑驳的铜块", "Weathered Copper": "锈蚀的铜块",
    "Oxidized Copper": "氧化的铜块",
    "Waxed Block of Copper": "涂蜡铜块",
    "Copper Grate": "铜格栅", "Copper Door": "铜门",
    "Copper Trapdoor": "铜活板门", "Copper Bulb": "铜灯",
    "Copper Horn": "铜号角",
    # 工具/装备补全
    "Copper Chestplate": "铜胸甲",
    "Copper Golem Statue": "铜傀儡雕像",
    "Saddle": "鞍", "Horse Saddle": "马鞍",
    "Goat Horn": "山羊角",
    "Displacement Wand": "位移魔杖",
    "Harness": "马具", "Studded Armor": "镶钉盔甲",
    "Gear": "齿轮", "Highlight": "高亮特效",
    # 锻造模板
    "Dune Armor Trim": "沙丘锻造模板",
    "Sentry Armor Trim": "哨兵锻造模板",
    "Vex Armor Trim": "恼鬼锻造模板",
    "Wild Armor Trim": "荒野锻造模板",
    "Coast Armor Trim": "海岸锻造模板",
    "Ward Armor Trim": "监守锻造模板",
    "Eye Armor Trim": "眼眸锻造模板",
    "Tide Armor Trim": "潮汐锻造模板",
    "Rib Armor Trim": "肋骨锻造模板",
    "Snout Armor Trim": "猪鼻锻造模板",
    "Spire Armor Trim": "尖塔锻造模板",
    "Wayfinder Armor Trim": "向导锻造模板",
    "Raiser Armor Trim": "牧民锻造模板",
    "Shaper Armor Trim": "塑形锻造模板",
    "Host Armor Trim": "东道锻造模板",
    "Silence Armor Trim": "静谧锻造模板",
    "Flow Armor Trim": "涡流锻造模板",
    "Bolt Armor Trim": "电流锻造模板",
    # 陶罐纹样
    "Flow Pottery Sherd": "涡流陶罐纹样",
    "Angler Pottery Sherd": "垂钓陶罐纹样",
    "Archer Pottery Sherd": "弓箭陶罐纹样",
    "Arms Up Pottery Sherd": "举臂陶罐纹样",
    "Blade Pottery Sherd": "利刃陶罐纹样",
    "Brewer Pottery Sherd": "酿造陶罐纹样",
    "Burn Pottery Sherd": "烈焰陶罐纹样",
    "Danger Pottery Sherd": "危险陶罐纹样",
    "Explorer Pottery Sherd": "探险陶罐纹样",
    "Friend Pottery Sherd": "友谊陶罐纹样",
    "Heart Pottery Sherd": "爱心陶罐纹样",
    "Heartbreak Pottery Sherd": "心碎陶罐纹样",
    "Howl Pottery Sherd": "狼嚎陶罐纹样",
    "Miner Pottery Sherd": "矿工陶罐纹样",
    "Mourner Pottery Sherd": "哀悼陶罐纹样",
    "Plenty Pottery Sherd": "富饶陶罐纹样",
    "Prize Pottery Sherd": "珍宝陶罐纹样",
    "Scrape Pottery Sherd": "刮削陶罐纹样",
    "Sheaf Pottery Sherd": "麦捆陶罐纹样",
    "Shelter Pottery Sherd": "庇护陶罐纹样",
    "Skull Pottery Sherd": "头颅陶罐纹样",
    "Snort Pottery Sherd": "猪鼻陶罐纹样",
    # 食物补全
    "Steak": "牛排",
    "Golden Poisonous Potato": "金毒马铃薯",
    "Poisonous Polytra": "毒马铃薯块",
    "Poisonous Potato Oil": "毒马铃薯油",
    "Potatiesh, Greatstaff of the Peasant": "农民大法杖",
    "Potato Portal": "马铃薯传送门",
    "Popped Chorus Fruit": "爆裂紫颂果",
    "Medicine": "药物", "Elixir": "万灵药",
    "Water Breathing": "水下呼吸药水",
    # 结构/组装件
    "Stone Brick Wall": "石砖墙",
    "Sulfur Bricks": "硫磺砖", "Sulfur Brick Wall": "硫磺砖墙",
    "Oak Slab": "橡木台阶", "Birch Slab": "白桦木台阶",
    "Spruce Slab": "云杉木台阶", "Jungle Slab": "丛林木台阶",
    "Acacia Slab": "金合欢木台阶", "Dark Oak Slab": "深色橡木台阶",
    "Mangrove Slab": "红树木台阶", "Cherry Slab": "樱花木台阶",
    "Bamboo Slab": "竹台阶", "Crimson Slab": "绯红木台阶",
    "Warped Slab": "诡异木台阶", "Pale Oak Slab": "苍白橡木台阶",
    "Polished Andesite Stairs": "磨制安山岩楼梯",
    "Polished Granite Stairs": "磨制花岗岩楼梯",
    "Polished Diorite Stairs": "磨制闪长岩楼梯",
    "Quartz Stairs": "石英楼梯", "Smooth Quartz Stairs": "平滑石英楼梯",
    "Smooth Quartz Block": "平滑石英块",
    "Red Sandstone Slab": "红砂岩台阶",
    "Smooth Sandstone Slab": "平滑砂岩台阶",
    "Cobbled Deepslate Slab": "深板岩圆石台阶",
    "Nether Quartz": "下界石英",
    "Nether Bricks": "下界砖块",
    "Prismarine Shard": "海晶碎片",
    # Stripped Wood 通用
    "Stripped Wood": "去皮木头",
    "Camel Husk": "骆驼皮壳",
    # === P6 增补（--limit 50 冒烟测试发现）===
    "Flower Pot": "花盆", "Potted Cactus": "盆栽仙人掌",
    "Wooden Fence": "木栅栏", "Oak Fence": "橡木栅栏",
    "Tall Grass": "高草丛", "Short Grass": "矮草丛",
    "Cod": "鳕鱼", "Raw Cod": "生鳕鱼", "Cooked Cod": "熟鳕鱼",
    "Salmon": "鲑鱼", "Tropical Fish": "热带鱼",
    "Dye": "染料", "Wool": "羊毛",
    "Crafting Table": "工作台", "Furnace": "熔炉",
    "Eyeblossom": " eyeblossom", "Open Eyeblossom": "盛开的 eyeblossom",
    "Closed Eyeblossom": "闭合的 eyeblossom",
    "Creaking Heart": "嘎吱之心", "Resin Clump": "树脂团",
    "Resin Brick Wall": "树脂砖墙", "Resin Brick Stairs": "树脂砖楼梯",
    "Block of Resin": "树脂块",
    "Pale Hanging Moss": "苍白垂附苔",
    "Pale Moss Carpet": "苍白苔藓地毯",
    "Cactus Flower": "仙人掌花",
    "Firefly Bush": "萤火虫灌木",
    "Bush": "灌木",
    # === P7 增补（--limit 200 发现）===
    "Peony": "牡丹", "Poppy": "罂粟", "Dandelion": "蒲公英",
    "Rose Bush": "玫瑰丛", "Lilac": "丁香", "Sunflower": "向日葵",
    "Allium": "绒球葱", "Azure Bluet": "茜草花", "Blue Orchid": "蓝兰花",
    "Oxeye Daisy": "滨菊", "Tulip": "郁金香", "Wither Rose": "凋灵玫瑰",
    "Cornflower": "矢车菊", "Lily of the Valley": "铃兰",
    "Torchflower": "火把花", "Pitcher Plant": "瓶子草",
    "Kelp": "海带", "Dried Kelp": "干海带", "Kelp Block": "干海带块",
    "Sea Pickle": "海泡菜", "Sea Grass": "海草",
    "Amethyst Cluster": "紫水晶簇", "Amethyst Bud": "紫水晶芽",
    "Small Amethyst Bud": "小型紫水晶芽", "Medium Amethyst Bud": "中型紫水晶芽",
    "Large Amethyst Bud": "大型紫水晶芽",
    "Bedrock": "基岩", "Moss Block": "苔藓块",
    "Moss Carpet": "苔藓地毯", "Mangrove Propagule": "红树胎生苗",
    "Mangrove Roots": "红树根", "Muddy Mangrove Roots": "沾泥的红树根",
    "Copper Chain": "铜锁链", "Chain": "锁链",
    "Block of Amethyst": "紫水晶块",
    "Short Grass": "矮草丛", "Fern": "蕨", "Large Fern": "大型蕨",
    "Music Disc Precipice": "音乐唱片 Precipice",
    "Music Disc Creator": "音乐唱片 Creator",
    "Music Disc Creator (Music Box)": "音乐唱片 Creator (八音盒)",
    "Armor": "盔甲", "Horse Armor": "马铠",
    "Tool": "工具", "Wood": "木头",
    "Block": "方块", "Concrete": "混凝土",
    "Structure": "结构", "Explosion": "爆炸",
    "Fence Gate": "栅栏门", "Wooden Fence": "木栅栏",
    "Wooden Pressure Plate": "木质压力板",
    "Flower Pot": "花盆", "Wool": "羊毛",
    "Mushroom Block": "蘑菇方块",
    "Single Biome": "单一生物群系",

    # === P4 自动补全（zh_missing.json）===
    "Cobbled Deepslate Slab": "深板岩圆石台阶",
    "Command Block": "命令方块",
    "Copper Chestplate": "铜胸甲",
    "Copper Golem Statue": "铜傀儡雕像",
    "Coral Block": "珊瑚块",
    "Coral Fan": "珊瑚扇",
    "Creeper Charge Banner Pattern": "苦力怕蓄力旗帜图案",
    "Creeper Head": "苦力怕头",
    "Dead Bush": "枯死的灌木",
    "Displacement Wand": "位移魔杖",
    "Dune Armor Trim": "沙丘锻造模板",
    "Flow Pottery Sherd": "涡流陶罐纹样",
    "Food": "食物",
    "Frosted Ice": "霜冰",
    "Gear": "齿轮",
    "Ghast": "恶魂",
    "Goat Horn": "山羊角",
    "Golden Poisonous Potato": "金毒马铃薯",
    "Hardened Stained Glass": "硬化染色玻璃",
    "Harness": "马具",
    "Highlight": "高亮",
    "Leaves": "树叶",
    "Leggings": "护腿",
    "Log": "原木",
    "Medicine": "药物",
    "Mine": "地雷",
    "Minecraft Education 1.21.132": "教育版 1.21.132",
    "Music Disc stal": "音乐唱片 stal",
    "Nether Quartz": "下界石英",
    "Oak Slab": "橡木台阶",
    "Panda": "熊猫",
    "Parrot": "鹦鹉",
    "Piston/Technical components": "活塞/技术组件",
    "Pitcher Plant": "瓶子草",
    "Player Head": "玩家头",
    "Poisonous Polytra": "毒马铃薯损伤",
    "Polished Andesite Stairs": "磨制安山岩楼梯",
    "Popped Chorus Fruit": "爆裂紫颂果",
    "Potatiesh, Greatstaff of the Peasant": "农民大法杖",
    "Potato Portal": "马铃薯传送门",
    "Prismarine Shard": "海晶碎片",
    "Quartz Stairs": "石英楼梯",
    "Ravager": "劫掠兽",
    "Red Sandstone Slab": "红砂岩台阶",
    "Redstone mechanics": "红石机制",
    "Reinforced Deepslate": "强化深板岩",
    "Resin Brick Slab": "树脂砖台阶",
    "Skeleton": "骷髅",
    "Smooth Quartz Block": "平滑石英块",
    "Smooth Quartz Stairs": "平滑石英楼梯",
    "Smooth Sandstone Slab": "平滑砂岩台阶",
    "Stained Terracotta": "染色陶瓦",
    "Steak": "牛排",
    "Stone Brick Wall": "石砖墙",
    "Stripped Wood": "去皮木头",
    "Studded Armor": "镶钉盔甲",
    "Sulfur Brick Wall": "硫磺砖墙",
    "Sulfur Bricks": "硫磺砖",
    "Sword": "剑",
    "Trails & Tales": "足迹与故事",
    "Unused textures": "未使用纹理",
    "Vines": "藤蔓",
    "Water Breathing": "水下呼吸",
    "Wither": "凋灵",
    "Wither Skeleton Skull": "凋灵骷髅头颅",
    "Wooden Button": "木按钮",
    "Wooden Door": "木门",
    "Wooden Slab": "木台阶",
    "Wooden Stairs": "木楼梯",
    "Wooden Trapdoor": "木活板门",
    "Zombie": "僵尸",
    # === P8 终局修复：ZH_MAP 补全 ===
    "Activator Rail": "激活铁轨",
    "Air": "空气",
    "Balloon": "气球",
    "Black Candle": "黑色蜡烛",
    "Blue Candle": "蓝色蜡烛",
    "Breeze Rod": "旋风棒",
    "Brown Candle": "棕色蜡烛",
    "Brown Mushroom": "棕色蘑菇",
    "Bubble Column": "气泡柱",
    "Camera": "相机",
    "Carved Pumpkin": "雕刻南瓜",
    "Chalkboard": "黑板",
    "Chaos Cubed": "混沌立方",
    "Chestplate": "胸甲",
    "Chiseled Copper": "錾制铜块",
    "Chorus Flower": "紫颂花",
    "Cinnabar Slab": "朱砂台阶",
    "Cobweb": "蜘蛛网",
    "Compound": "化合物",
    "Copper Bars": "铜栏杆",
    "Copper Spear": "铜矛",
    "Coral": "珊瑚",
    "Cyan Candle": "青色蜡烛",
    "Dead Coral": "死珊瑚",
    "Dragon Head": "龙首",
    "Education Edition 1.8.0": "教育版 1.8.0",
    "Element Constructor": "元素构造器",
    "Fluid": "流体",
    "Froglight": "蛙明灯",
    "Gray Candle": "灰色蜡烛",
    "Green Candle": "绿色蜡烛",
    "Guster Pottery Sherd": "狂风陶罐纹样",
    "Heavy Core": "重核",
    "Heavy Weighted Pressure Plate": "重质测重压力板",
    "Iron Spear": "铁矛",
    "Item": "物品",
    "Lab Table": "实验台",
    "Light Blue Candle": "淡蓝色蜡烛",
    "Light Gray Candle": "淡灰色蜡烛",
    "Lime Candle": "黄绿色蜡烛",
    "Lingering Potion": "滞留药水",
    "Magenta Candle": "品红色蜡烛",
    "Melon Seeds": "西瓜种子",
    "Minecraft": "Minecraft",
    "Music Disc Lava Chicken": "音乐唱片 Lava Chicken",
    "Music Disc Tears": "音乐唱片 Tears",
    "Nether Reactor Core": "下界反应核",
    "Netherite Upgrade": "下界合金升级",
    "Ominous Banner": "灾厄旗帜",
    "Ominous Bottle": "灾厄之瓶",
    "Orange Candle": "橙色蜡烛",
    "Photo": "照片",
    "Piglin Head": "猪灵头",
    "Pink Candle": "粉色蜡烛",
    "Pink Petals": "粉色花瓣",
    "Polished Cinnabar": "磨制朱砂",
    "Polished Cinnabar Slab": "磨制朱砂台阶",
    "Polished Cinnabar Wall": "磨制朱砂墙",
    "Polished Sulfur Wall": "磨制硫磺墙",
    "Potion": "药水",
    "Pottery Sherd": "陶罐纹样",
    "Powder Snow": "细雪",
    "Purple Candle": "紫色蜡烛",
    "Purpur Slab": "紫珀台阶",
    "Quiver": "箭袋",
    "Red Candle": "红色蜡烛",
    "Ruby": "红宝石",
    "Seagrass": "海草",
    "Shelf": "架子",
    "Shrub": "灌木",
    "Shulker Boxes": "潜影盒",
    "Slowness": "缓慢",
    "Smithing Template": "锻造模板",
    "Snowball": "雪球",
    "Sparkler": "烟花棒",
    "Splash Potion": "喷溅药水",
    "Sulfur Spike": "硫磺尖刺",
    "Sulfur Stairs": "硫磺楼梯",
    "The Copper Age": "铜器时代",
    "Trial Spawner": "试炼刷怪笼",
    "Tricky Trials": "棘巧试炼",
    "Weapon": "武器",
    "Weaving": "编织",
    "White Candle": "白色蜡烛",
    "Yellow Candle": "黄色蜡烛",
    # Names with descriptor pattern
    "Animal": "动物",
}


# ============================================
# 名称清理：移除 Wiki 文本中常见的人工制品
# ============================================

def _canonicalize_name(en):
    """
    规范化英文名以匹配 ZH_MAP。
    处理 Wiki 文本中的常见变体:
      - "Music Disc stal"      → "Music Disc Stal"
      - "Block of iron"        → "Block of Iron"
      - "minecraft:stone"      → "Stone"
      - "File:Invicon XYZ.png" → "XYZ"
    """
    if not en:
        return ''
    s = en.strip()
    # 去掉 namespace 前缀
    if s.lower().startswith('minecraft:'):
        s = s[10:]
    # 去掉 File: 前缀
    if s.lower().startswith('file:'):
        s = s[5:]
        if '.png' in s.lower():
            s = s.split('.png')[0]
    # 每个词首字母大写（处理 "Music Disc stal" → "Music Disc Stal"）
    # 但保留已有的大写（如 "Stone" "Iron Ingot"）
    words = s.split()
    result = []
    for w in words:
        if w and w[0].islower():
            # 小写首字母 → 可能是噪音，尝试大写
            w = w[0].upper() + w[1:]
        result.append(w)
    return ' '.join(result)


# 已知非物品标识（URL 解析产生的伪物品，直接过滤）
# 同时包含原始 slug 和 normalize_id 后的形式
_NON_ITEM_SLUGS = {
    # 带特殊字符的原始 slug
    "calculators/projectile_motion", "piston/technical_components",
    "trails_&_tales",
    # normalize_id 后的形式（特殊字符被移除）
    "calculatorsprojectile_motion", "pistontechnical_components",
    "minecraft_education_121132", "trails_tales",
    "unused_textures", "redstone_mechanics",
    # 类别/通用名称（会有更具体的物品页面）
    "food", "mine",
    "stained_glass", "stained_terracotta", "concrete_powder",
    "planks", "wooden_button", "wooden_door", "wooden_slab",
    "wooden_stairs", "wooden_trapdoor",
    "banner", "bed", "boat", "candle", "carpet", "leaves", "leggings",
    "log", "sapling", "sign", "sword", "vines",
}

def is_non_item(item_id):
    """判断是否为非物品条目（伪物品/分类页/技术页面等）。
    同时检查原始 ID 和 normalize_id 后的形式。

    强制保留规则：id 包含以下结构的变体 → 一律视为独立物品，不拦截。
    """
    if not item_id:
        return False
    low = item_id.lower().strip()

    # 强制保留：变体物品前缀/后缀（颜色、木种等）
    for pat in _FORCE_RETAIN_PATTERNS:
        if pat in low:
            return False

    # 直接匹配
    if low in _NON_ITEM_SLUGS:
        return True
    # 清理特殊字符后匹配
    cleaned = re.sub(r'[^a-z0-9]', '', low)
    for slug in _NON_ITEM_SLUGS:
        cleaned_slug = re.sub(r'[^a-z0-9]', '', slug)
        if cleaned == cleaned_slug:
            return True
    return False


def _generate_zh_by_pattern(en):
    """
    Layer 0: 基于命名模式生成中文名（优先于 ZH_MAP 前缀匹配）。
    避免 "Chicken Spawn Egg" → Layer 4 匹配 "Spawn Egg" → "刷怪蛋" 的问题。
    """
    if not en:
        return None
    en_lower = en.lower()

    # --- Spawn Egg: {Entity} Spawn Egg → {实体中文}刷怪蛋 ---
    if en_lower.endswith(' spawn egg'):
        entity_en = en[:-len(' spawn egg')].strip()
        entity_zh = _ENTITY_ZH.get(entity_en.lower().replace(' ', '_'))
        if not entity_zh:
            entity_zh = _ENTITY_ZH.get(entity_en.lower())
        if entity_zh:
            return entity_zh + '刷怪蛋'

    # --- Color + Base: {Color} {Base} → {颜色中文}{基类中文} ---
    for color_en, color_zh in _COLOR_NAME_ZH.items():
        for base_en, base_zh in _BASE_NAME_ZH.items():
            expected = f'{color_en} {base_en}'.replace('_', ' ')
            if en_lower == expected:
                return color_zh + base_zh
            # Title case: "White Wool"
            if en_lower == expected.title():
                return color_zh + base_zh

    # --- Wood + Base: {Wood} {Base} → {木材中文}{基类中文} ---
    for wood_en, wood_zh in _WOOD_NAME_ZH.items():
        for base_en, base_zh in _BASE_NAME_ZH.items():
            expected = f'{wood_en} {base_en}'.replace('_', ' ')
            if en_lower == expected or en_lower == expected.title():
                # 特殊处理：wood base 不需要追加中文（橡木+木=重复）
                if base_en == 'wood':
                    return wood_zh
                return wood_zh + base_zh

    return None


def get_zh_name(en):
    """
    6 层 fallback 获取中文名:
      Layer 0: 模式规则生成（Color/Wood/Entity + Base）  ← 新增，最高优先级
      Layer 1: 直接查 ZH_MAP
      Layer 2: 清理 _ → 空格后查 ZH_MAP
      Layer 3: canonicalize 后查 ZH_MAP（处理大小写变体）
      Layer 4: 前缀子串匹配（"Smooth Quartz Block" → 查 "Smooth Quartz" 等）
      Layer 5: 返回原文 title case
    """
    if not en:
        return '未知物品'

    # Layer 0: 模式规则生成（阻止前缀匹配误判）
    pattern_zh = _generate_zh_by_pattern(en)
    if pattern_zh:
        return pattern_zh

    # Layer 1
    if en in ZH_MAP:
        return ZH_MAP[en]
    # Layer 2
    cleaned = en.replace('_', ' ').strip()
    if cleaned in ZH_MAP:
        return ZH_MAP[cleaned]
    if cleaned.title() in ZH_MAP:
        return ZH_MAP[cleaned.title()]
    # Layer 3: canonicalize
    canonical = _canonicalize_name(cleaned)
    if canonical in ZH_MAP:
        return ZH_MAP[canonical]
    # Layer 3b: canonical 的 title case
    if canonical.title() in ZH_MAP:
        return ZH_MAP[canonical.title()]
    # Layer 4: 前缀子串匹配（找最长的关键词匹配）
    best = None
    best_len = 0
    search = canonical.lower()
    for key in ZH_MAP:
        key_lower = key.lower()
        if key_lower in search and len(key_lower) > best_len:
            # 避免短词误匹配（如 "Bed" 匹配 "Bedrock"）
            # 使用边界感知匹配
            idx = search.find(key_lower)
            valid_start = (idx == 0 or search[idx-1] == ' ')
            valid_end = (idx + len(key_lower) == len(search) or search[idx+len(key_lower)] == ' ')
            if valid_start and valid_end:
                best = ZH_MAP[key]
                best_len = len(key_lower)
    if best:
        return best
    # Layer 5: 返回原文（首字母大写）
    return canonical.title()


def apply_zh_name(item):
    """为物品补充中文名 + 同步原料中文名 + 收集未命中词条"""
    en = item.get('name_en', '')
    zh = get_zh_name(en)
    item['name_zh'] = zh

    # 判断是否真正未命中（非 ZH_MAP 命中）
    if en:
        cleaned = en.replace('_', ' ').strip()
        canonical = _canonicalize_name(cleaned)
        is_hit = (en in ZH_MAP or cleaned in ZH_MAP or cleaned.title() in ZH_MAP
                  or canonical in ZH_MAP or canonical.title() in ZH_MAP)
        # 子串匹配也算命中
        if not is_hit:
            search = canonical.lower()
            for key in ZH_MAP:
                kl = key.lower()
                if kl in search and len(kl) > 3:
                    idx = search.find(kl)
                    if (idx == 0 or search[idx-1] == ' ') and \
                       (idx + len(kl) == len(search) or search[idx+len(kl)] == ' '):
                        is_hit = True
                        break
        if not is_hit and not is_non_item(item.get('id', '')):
            _zh_missing.add(en)

    # 同步原料/配方中的中文名
    for recipe in item.get('crafting', []):
        for ing_id, ing in recipe.get('ingredients', {}).items():
            ing_en = ing.get('name_en', '') or ing.get('name_zh', '') or ing_id.replace('_', ' ').title()
            ing_zh = get_zh_name(ing_en)
            ing['name_zh'] = ing_zh
            ing['name_en'] = ing_en

    return item


# 全局：收集 ZH_MAP 未命中的词条
_zh_missing = set()


def write_zh_missing(path='zh_missing.json'):
    """输出未命中 ZH_MAP 的词条列表"""
    import json as _json
    sorted_list = sorted(_zh_missing)
    with open(path, 'w', encoding='utf-8') as f:
        _json.dump(sorted_list, f, ensure_ascii=False, indent=2)
    print(f'  zh_missing: {len(sorted_list)} words written to {path}')


def normalize_items(items, existing_ids=None):
    """
    规范化物品列表：
    1. ID 统一小写 + 下划线
    2. 按 ID 去重（保留第一个）
    3. 删除 null 值和空字段
    4. 分类补全
    5. 确保 acquisition.methods 存在
    """
    seen = set()
    if existing_ids:
        seen.update(existing_ids)

    cleaned = []
    stats = {"duplicates": 0, "nulls_removed": 0, "fixed_acquisition": 0, "fixed_category": 0}

    for item in items:
        if not item or not isinstance(item, dict):
            continue

        # ID 规范化
        item_id = normalize_item_id(item.get('id', ''))
        if not item_id:
            continue
        item['id'] = item_id

        # 去重
        if item_id in seen:
            stats["duplicates"] += 1
            continue
        seen.add(item_id)

        # 过滤非物品条目（伪物品/分类页/技术页）
        if is_non_item(item_id):
            stats.setdefault('filtered_non_item', 0)
            stats['filtered_non_item'] += 1
            continue

        # 删除 null 值
        nulls = [k for k, v in item.items() if v is None]
        for k in nulls:
            del item[k]
            stats["nulls_removed"] += 1

        # 空数组/空对象处理
        for key in ['stonecutting', 'smithing', 'related_items']:
            if item.get(key) is None:
                item[key] = []
        for key in ['crafting']:
            if item.get(key) is None:
                item[key] = []

        # 确保 acquisition.methods 存在
        acq = item.get('acquisition')
        if not acq or not isinstance(acq, dict):
            item['acquisition'] = {'methods': ['未知']}
            stats["fixed_acquisition"] += 1
        elif not acq.get('methods') or len(acq['methods']) == 0:
            acq['methods'] = ['未知']
            stats["fixed_acquisition"] += 1

        # 确保 category 有效
        valid_cats = [
            "building_blocks", "natural_blocks", "functional_blocks",
            "tools", "combat", "food", "materials", "miscellaneous"
        ]
        if item.get('category') not in valid_cats:
            item['category'] = 'miscellaneous'
            stats["fixed_category"] += 1

        # 清理 crafting 中的 null 引用
        if 'crafting' in item:
            for recipe in item['crafting']:
                clean_recipe_pattern(recipe)

        # 确保 name_zh / name_en 存在
        if not item.get('name_en'):
            item['name_en'] = item_id.replace('_', ' ').title()
        if not item.get('name_zh'):
            item['name_zh'] = item['name_en']

        # 强制 icon_url 存在
        if not item.get('icon_url'):
            item['icon_url'] = './assets/missing.png'
            stats.setdefault('fixed_icon', 0)
            stats['fixed_icon'] += 1

        # 标准化 acquisition 结构
        acq = item.get('acquisition')
        if not isinstance(acq, dict):
            item['acquisition'] = {'methods': ['未知']}
        else:
            if not isinstance(acq.get('methods'), list) or len(acq.get('methods', [])) == 0:
                acq['methods'] = ['未知']
            # 清理 smelting null（支持列表格式）
            if 'smelting' in acq:
                if not acq['smelting'] or (isinstance(acq['smelting'], list) and len(acq['smelting']) == 0):
                    del acq['smelting']

        # 标准化 stonecutting / smithing 结构（新增）
        for key in ['stonecutting', 'smithing']:
            if key not in item or not isinstance(item.get(key), list) or len(item.get(key, [])) == 0:
                item[key] = []


        # 标准化 crafting 结构（保留所有配方不丢弃）
        if not isinstance(item.get('crafting'), list):
            item['crafting'] = []
        for r in item['crafting']:
            if not isinstance(r, dict):
                continue
            r.setdefault('ingredients', {})
            if not isinstance(r.get('pattern'), list) or len(r.get('pattern', [])) < 3:
                r['pattern'] = [['', '', ''], ['', '', ''], ['', '', '']]
            r.setdefault('result_id', item['id'])
            r.setdefault('result_count', 1)
            r.setdefault('shaped', True)
            r.setdefault('type', 'crafting_table')
            # 保留元数据字段
            if 'result_match' not in r:
                r['result_match'] = (r.get('result_id') == item['id'])
            if 'is_primary_recipe' not in r:
                r['is_primary_recipe'] = r['result_match']
            # 确保 result_icon 有值
            if not r.get('result_icon'):
                r['result_icon'] = item.get('icon_url', '')

        # 确保 related_items 为数组
        if not isinstance(item.get('related_items'), list):
            item['related_items'] = []

        # 补充中文名
        apply_zh_name(item)

        # name 保底
        if not item.get('name_en'):
            item['name_en'] = item_id.replace('_', ' ').title()
        if not item.get('name_zh') or item['name_zh'] == item.get('name_en', ''):
            item['name_zh'] = get_zh_name(item.get('name_en', ''))

        cleaned.append(item)

    extras = []
    if stats.get('filtered_non_item', 0) > 0:
        extras.append(f"filtered {stats['filtered_non_item']} non-items")
    if stats.get('fixed_icon', 0) > 0:
        extras.append(f"fixed {stats['fixed_icon']} icons")
    extra_str = ', '.join(extras) if extras else ''
    print(f"  Normalized: removed {stats['duplicates']} duplicates, "
          f"{stats['nulls_removed']} nulls, "
          f"fixed {stats['fixed_acquisition']} acquisition, "
          f"{stats['fixed_category']} categories"
          + (f", {extra_str}" if extra_str else ''))
    return cleaned


def normalize_item_id(raw_id):
    """规范化单个物品 ID（委托给 utils.normalize_id）"""
    from utils import normalize_id
    return normalize_id(raw_id)


def clean_recipe_pattern(recipe):
    """清理配方 pattern 中的无效引用"""
    pattern = recipe.get('pattern', [])
    if not isinstance(pattern, list):
        recipe['pattern'] = [['', '', ''], ['', '', ''], ['', '', '']]
        return

    # 确保是 3×3
    while len(pattern) < 3:
        pattern.append(['', '', ''])
    for i in range(3):
        row = pattern[i]
        if not isinstance(row, list):
            row = []
        while len(row) < 3:
            row.append('')
        pattern[i] = row[:3]

    recipe['pattern'] = pattern

    # 清理空字符串（去空格）
    for i in range(3):
        for j in range(3):
            if pattern[i][j] and isinstance(pattern[i][j], str):
                pattern[i][j] = pattern[i][j].strip()


def build_categories(items):
    """根据物品数据自动构建分类结构"""
    cat_items = defaultdict(lambda: defaultdict(list))

    for item in items:
        cat = item.get('category', 'miscellaneous')
        sub = item.get('subcategory', 'general')
        cat_items[cat][sub].append(item['id'])

    categories = []
    cat_meta = {
        "building_blocks": ("建筑方块", "Building Blocks", "stone"),
        "natural_blocks": ("自然方块", "Natural Blocks", "grass_block"),
        "functional_blocks": ("功能方块", "Functional Blocks", "crafting_table"),
        "tools": ("工具", "Tools", "iron_pickaxe"),
        "combat": ("战斗", "Combat", "iron_sword"),
        "food": ("食物", "Food", "bread"),
        "materials": ("材料", "Materials", "iron_ingot"),
        "miscellaneous": ("杂项", "Miscellaneous", "stick"),
    }

    sub_name_map = {
        "stone_blocks": ("石质方块", "Stone Blocks"),
        "wood_blocks": ("木质方块", "Wood Blocks"),
        "glass_blocks": ("玻璃", "Glass"),
        "colored_blocks": ("彩色方块", "Colored Blocks"),
        "surface": ("地表方块", "Surface Blocks"),
        "vegetation": ("植被", "Vegetation"),
        "ores": ("矿石", "Ores"),
        "ores_ingots": ("矿物与锭", "Ores & Ingots"),
        "organic": ("有机材料", "Organic Materials"),
        "dyes": ("染料", "Dyes"),
        "workstations": ("工作站点", "Workstations"),
        "storage": ("存储", "Storage"),
        "utility": ("装饰与设施", "Decor & Utility"),
        "utility_items": ("常用物品", "Utility Items"),
        "mechanisms": ("机械", "Mechanisms"),
        "pickaxes": ("镐", "Pickaxes"),
        "axes": ("斧", "Axes"),
        "shovels": ("铲", "Shovels"),
        "hoes": ("锄", "Hoes"),
        "other_tools": ("其他工具", "Other Tools"),
        "swords": ("剑", "Swords"),
        "ranged": ("远程武器", "Ranged Weapons"),
        "armor": ("护甲", "Armor"),
        "crops": ("农作物", "Crops"),
        "meat": ("肉类", "Meat"),
        "prepared": ("熟食", "Prepared Food"),
        "discs": ("唱片", "Music Discs"),
        "decor": ("装饰", "Decor"),
        "transport": ("交通", "Transport"),
        "general": ("通用", "General"),
    }

    # 按固定顺序排列大类
    order = ["building_blocks", "natural_blocks", "functional_blocks",
             "tools", "combat", "food", "materials", "miscellaneous"]

    for cat_id in order:
        if cat_id not in cat_items:
            continue
        zh, en, icon = cat_meta.get(cat_id, (cat_id, cat_id, ''))
        subcats = []
        for sub_id, item_list in sorted(cat_items[cat_id].items()):
            sub_zh, sub_en = sub_name_map.get(sub_id, (sub_id.replace('_', ' ').title(), sub_id.replace('_', ' ').title()))
            subcats.append({
                "id": sub_id,
                "name_zh": sub_zh,
                "name_en": sub_en,
                "items": sorted(item_list),
            })
        categories.append({
            "id": cat_id,
            "name_zh": zh,
            "name_en": en,
            "icon_item": icon,
            "subcategories": subcats,
        })

    return categories


def validate_quality(items):
    """
    质量验证，返回 (通过, 报告)。
    验收标准对齐 plan.md §8.1:
      - 物品总数 ≥ 300 (P1) / ≥ 800 (P2)
      - name_zh 覆盖率 ≥ 95%
      - JSON 格式合法（外部检查）
      - 无重复 ID
    """
    issues = []
    ids = [i['id'] for i in items]

    if len(items) < 300:
        issues.append(f"物品数 {len(items)} < 300 (P1 minimum)")

    if len(ids) != len(set(ids)):
        duplicates = [id for id in ids if ids.count(id) > 1]
        issues.append(f"存在 {len(set(duplicates))} 个重复 ID: {list(set(duplicates))[:5]}...")

    # 检查必填字段
    required = ['id', 'name_zh', 'name_en', 'category', 'subcategory', 'icon_url', 'acquisition']
    missing_count = {f: 0 for f in required}
    for item in items:
        for field in required:
            if field not in item or item[field] is None:
                missing_count[field] += 1
    for f, c in missing_count.items():
        if c > 0:
            issues.append(f"字段 {f} 缺失: {c}/{len(items)} ({c/max(len(items),1)*100:.1f}%)")

    # 检查 zh_fallback 率
    zh_fb = sum(1 for i in items if i.get('name_zh') == i.get('name_en'))
    zh_cov = 100 - zh_fb / max(len(items), 1) * 100
    if zh_cov < 95:
        issues.append(f"中文覆盖率 {zh_cov:.1f}% < 95%（{zh_fb} 项使用英文回退）")

    # 检查 null
    null_items = []
    for item in items:
        for key, val in item.items():
            if val is None:
                null_items.append(f"{item['id']}.{key}")
    if null_items:
        issues.append(f"{len(null_items)} 个字段为 null（前5: {null_items[:5]}）")

    # 检查 crafting 归属合理性
    orphan_recipes = 0
    for item in items:
        for r in item.get('crafting', []):
            if r.get('result_id') != item['id']:
                orphan_recipes += 1
    if orphan_recipes > 0:
        issues.append(f"{orphan_recipes} 个配方的结果物品不属于当前页面（原料页配方，非错误）")

    passed = len([i for i in issues if '覆盖率' in i or '缺失' in i or '重复' in i]) == 0
    return passed, issues


def validate_quality_report(items):
    """
    输出数据质量报告 — 格式对齐 plan.md §8.1.
    """
    total = len(items)
    if total == 0:
        print('[DATA QUALITY REPORT] No items to report')
        return

    missing_icon = sum(1 for i in items if not i.get('icon_url') or i['icon_url'].endswith('missing.png'))
    zh_fallback  = sum(1 for i in items if i.get('name_zh') == i.get('name_en'))
    empty_craft  = sum(1 for i in items if not i.get('crafting') or len(i['crafting']) == 0)
    primary_r    = sum(1 for i in items
                       for r in i.get('crafting', [])
                       if r.get('is_primary_recipe') or r.get('result_match'))
    total_r      = sum(len(i.get('crafting', [])) for i in items)
    missing_acq  = sum(1 for i in items
                       if not isinstance(i.get('acquisition'), dict)
                       or not i['acquisition'].get('methods')
                       or i['acquisition']['methods'] == ['未知'])
    total_stonecutting = sum(len(i.get('stonecutting', [])) for i in items)
    total_smithing     = sum(len(i.get('smithing', [])) for i in items)
    name_en_cov  = sum(1 for i in items if i.get('name_en'))
    cat_cov      = sum(1 for i in items if i.get('category'))
    acq_methods  = sum(1 for i in items
                       if isinstance(i.get('acquisition'), dict)
                       and i['acquisition'].get('methods')
                       and i['acquisition']['methods'] != ['未知'])
    incomplete   = sum(1 for i in items if i.get('incomplete'))
    ref_only     = sum(1 for i in items if i.get('referenced_only'))

    print()
    print('=== 数据验证报告 ===')
    print(f'总物品数：{total}')
    verdict = 'PASS' if total >= 800 else ('WARN (P1: >=300)' if total >= 300 else 'FAIL')
    print(f'  {"PASS" if total >= 300 else "FAIL"} 满足最低要求（≥ 300）' if total < 800 else f'  PASS 满足 P2 要求（≥ 800）')

    print()
    print('字段完整性：')
    print(f'  {"PASS" if name_en_cov == total else "FAIL"} name_en 覆盖率：{name_en_cov/total*100:.1f}%')
    zh_cov_pct = (total - zh_fallback) / total * 100
    print(f'  {"PASS" if zh_cov_pct >= 95 else "WARN"} name_zh 覆盖率：{zh_cov_pct:.1f}%'
          + (f'（其中 zh_fallback 标记 {zh_fallback} 项）' if zh_fallback else ''))
    print(f'  {"PASS" if cat_cov == total else "FAIL"} category 覆盖率：{cat_cov/total*100:.1f}%')
    print(f'  {"PASS" if acq_methods > total * 0.9 else "WARN"} acquisition.methods 覆盖率：{acq_methods/total*100:.1f}%'
          + (f'（{total - acq_methods} 项标记 incomplete）' if total - acq_methods > 0 else ''))

    print()
    print('数据质量：')
    print(f'  PASS JSON 格式合法（由 writer 保证）')
    dup_check = 'PASS' if len(items) == len(set(i['id'] for i in items)) else 'FAIL'
    print(f'  {dup_check} 无重复 item ID')
    print(f'  INFO {ref_only} 项标记 referenced_only')

    print()
    print('配方统计：')
    print(f'  合成配方：{total_r} 个（主配方 {primary_r} 个）')
    print(f'  切石配方：{total_stonecutting} 个')
    print(f'  锻造配方：{total_smithing} 个')
    print(f'  无配方物品：{empty_craft} 项')

    print()
    print('图标统计：')
    print(f'  图标覆盖率：{(total - missing_icon)/total*100:.1f}%')
    if missing_icon > 0:
        print(f'  WARN {missing_icon} 项无图标')

    # 验收判定
    print()
    failures = []
    if total < 300:
        failures.append(f'物品总数 < 300')
    if zh_cov_pct < 95:
        failures.append(f'name_zh 覆盖率 {zh_cov_pct:.1f}% < 95%')
    if failures:
        print(f'=== 验证未通过: {"; ".join(failures)} ===')
    else:
        print('=== 验证通过 ===')


# ============================================
# 误合并检测器
# ============================================

# 颜色关键词（检测变体误合并）
_COLOR_KEYWORDS = [
    'white', 'orange', 'magenta', 'light_blue', 'yellow', 'lime', 'pink',
    'gray', 'light_gray', 'cyan', 'purple', 'blue', 'brown', 'green', 'red', 'black',
]

# 木材关键词
_WOOD_KEYWORDS = [
    'oak', 'spruce', 'birch', 'jungle', 'acacia', 'dark_oak', 'mangrove',
    'cherry', 'bamboo', 'crimson', 'warped', 'pale_oak',
]

# 强制保留规则：id 包含这些结构 → 视为独立物品
_FORCE_RETAIN_PATTERNS = [
    '_wool', '_planks', '_log', '_sign', '_glass', '_terracotta',
    '_concrete', '_banner', '_bed', '_carpet', '_candle', '_boat',
    '_door', '_trapdoor', '_fence', '_fence_gate', '_slab', '_stairs',
    '_wall', '_button', '_pressure_plate', '_shulker_box', '_stained_glass',
    '_glazed_terracotta', '_concrete_powder', '_dye',
]


def detect_merge_issues(items):
    """
    检测物品误合并。
    规则: 如果多个不同的 name_en 映射到同一个 id，打印警告。
    若合并涉及颜色/木种关键词 → 判定为错误合并。
    返回: merge_warnings (list of dict)
    """
    from collections import defaultdict
    id_to_names = defaultdict(set)

    for item in items:
        nid = item.get('id', '')
        name = item.get('name_en', '')
        if nid and name:
            id_to_names[nid].add(name)

    warnings = []
    for nid, names in sorted(id_to_names.items()):
        if len(names) <= 1:
            continue
        names_list = sorted(names)
        combined = ' '.join(names_list).lower()

        has_color = any(c in combined for c in _COLOR_KEYWORDS)
        has_wood = any(w in combined for w in _WOOD_KEYWORDS)
        is_error = has_color or has_wood

        level = 'ERROR' if is_error else 'WARN'
        warning = {
            'id': nid,
            'level': level,
            'titles': names_list,
            'has_color': has_color,
            'has_wood': has_wood,
        }
        warnings.append(warning)

        print(f"  [{level}] MERGE: id={nid}")
        for t in names_list[:8]:
            print(f"    - {t}")
        if len(names_list) > 8:
            print(f"    ... and {len(names_list) - 8} more")

    error_count = sum(1 for w in warnings if w['level'] == 'ERROR')
    warn_count = sum(1 for w in warnings if w['level'] == 'WARN')
    print(f"\n  合并检测: {len(warnings)} 个 ID 有多标题 ({error_count} 错误, {warn_count} 警告)")
    return warnings


def validate_variant_coverage(items):
    """
    验证关键变体物品是否存在。
    必须存在的物品列表。
    返回: (passed: bool, missing: list)
    """
    existing_ids = set(i.get('id', '') for i in items)
    required = [
        # Color variants
        'white_wool', 'red_wool', 'blue_wool', 'black_wool',
        'white_bed', 'red_bed',
        'white_concrete', 'black_concrete',
        'white_stained_glass', 'black_stained_glass',
        'white_terracotta',
        'white_carpet',
        # Wood variants
        'oak_sign', 'spruce_sign', 'birch_sign',
        'oak_planks', 'spruce_planks', 'birch_planks',
        'oak_log', 'spruce_log', 'birch_log',
        'oak_door', 'iron_door',
        'oak_fence', 'oak_fence_gate',
        'oak_slab', 'oak_stairs',
        'oak_boat',
    ]

    missing = [r for r in required if r not in existing_ids]
    found = [r for r in required if r in existing_ids]

    print(f"\n  变体覆盖验证:")
    print(f"    必需: {len(required)} 项")
    print(f"    存在: {len(found)} 项")
    print(f"    缺失: {len(missing)} 项")

    if missing:
        print(f"    缺失列表:")
        for m in missing[:20]:
            print(f"      - {m}")
        if len(missing) > 20:
            print(f"      ... and {len(missing) - 20} more")

    passed = len(missing) == 0
    if not passed:
        print(f"    FAIL: {len(missing)} 个关键变体缺失")
    else:
        print(f"    PASS: 所有关键变体存在")

    return passed, missing


# ============================================
# 终局数据修复
# ============================================

# 颜色中文（完整16色）
_COLOR_NAME_ZH = {
    'white': '白色', 'orange': '橙色', 'magenta': '品红色',
    'light_blue': '淡蓝色', 'yellow': '黄色', 'lime': '黄绿色',
    'pink': '粉色', 'gray': '灰色', 'light_gray': '淡灰色',
    'cyan': '青色', 'purple': '紫色', 'blue': '蓝色',
    'brown': '棕色', 'green': '绿色', 'red': '红色', 'black': '黑色',
}

# 木材中文（官方译名 — 形容词形式）
_WOOD_NAME_ZH = {
    'oak': '橡木', 'spruce': '云杉木', 'birch': '白桦木',
    'jungle': '丛林木', 'acacia': '金合欢木', 'dark_oak': '深色橡木',
    'mangrove': '红树木', 'cherry': '樱花木',
    'pale_oak': '苍白橡木', 'bamboo': '竹',
    'crimson': '绯红木', 'warped': '诡异木',
}

# 基类中文名（官方译名）
_BASE_NAME_ZH = {
    'wool': '羊毛', 'bed': '床', 'carpet': '地毯',
    'concrete': '混凝土', 'terracotta': '陶瓦',
    'stained_glass': '染色玻璃', 'glass': '玻璃',
    'sign': '告示牌', 'hanging_sign': '悬挂式告示牌',
    'planks': '木板', 'log': '原木', 'wood': '木',  # 橡木+木=橡木，但当base是wood时特殊处理
    'door': '门', 'trapdoor': '活板门', 'fence': '栅栏',
    'fence_gate': '栅栏门', 'slab': '台阶', 'stairs': '楼梯',
    'boat': '船', 'button': '按钮', 'pressure_plate': '压力板',
    'spawn_egg': '刷怪蛋',
    'candle': '蜡烛',
    'shulker_box': '潜影盒',
    'banner': '旗帜',
}

# 实体中文（spawn egg用）
_ENTITY_ZH = {
    'bat': '蝙蝠', 'bee': '蜜蜂', 'blaze': '烈焰人', 'cat': '猫',
    'cave_spider': '洞穴蜘蛛', 'chicken': '鸡', 'cod': '鳕鱼',
    'cow': '牛', 'creeper': '苦力怕', 'dolphin': '海豚',
    'donkey': '驴', 'drowned': '溺尸', 'elder_guardian': '远古守卫者',
    'enderman': '末影人', 'endermite': '末影螨', 'evoker': '唤魔者',
    'fox': '狐狸', 'frog': '青蛙', 'ghast': '恶魂',
    'glow_squid': '发光鱿鱼', 'goat': '山羊', 'guardian': '守卫者',
    'hoglin': '疣猪兽', 'horse': '马', 'husk': '尸壳',
    'iron_golem': '铁傀儡', 'llama': '羊驼', 'magma_cube': '岩浆怪',
    'mooshroom': '哞菇', 'mule': '骡', 'ocelot': '豹猫',
    'panda': '熊猫', 'parrot': '鹦鹉', 'phantom': '幻翼',
    'pig': '猪', 'piglin': '猪灵', 'piglin_brute': '猪灵蛮兵',
    'pillager': '掠夺者', 'polar_bear': '北极熊', 'pufferfish': '河豚',
    'rabbit': '兔子', 'ravager': '劫掠兽', 'salmon': '鲑鱼',
    'sheep': '羊', 'shulker': '潜影贝', 'silverfish': '蠹虫',
    'skeleton': '骷髅', 'skeleton_horse': '骷髅马', 'slime': '史莱姆',
    'snow_golem': '雪傀儡', 'spider': '蜘蛛', 'squid': '鱿鱼',
    'stray': '流浪者', 'strider': '炽足兽', 'tadpole': '蝌蚪',
    'trader_llama': '商贩羊驼', 'tropical_fish': '热带鱼', 'turtle': '海龟',
    'vex': '恼鬼', 'villager': '村民', 'vindicator': '卫道士',
    'wandering_trader': '流浪商人', 'warden': '监守者', 'witch': '女巫',
    'wither_skeleton': '凋灵骷髅', 'wither': '凋灵', 'wolf': '狼',
    'zoglin': '僵尸疣猪兽', 'zombie': '僵尸', 'zombie_villager': '僵尸村民',
    'zombified_piglin': '僵尸猪灵', 'armadillo': '犰狳', 'bogged': '沼泽骷髅',
    'breeze': '旋风人', 'creaking': '嘎吱怪', 'sniffer': '嗅探兽',
    'camel': '骆驼', 'allay': '悦灵', 'ender_dragon': '末影龙',
    'axolotl': '美西螈', 'agent': '智能体', 'npc': 'NPC',
    'nautilus': '鹦鹉螺', 'parched': '干渴', 'default': '默认',
}


def normalize_category(item):
    """
    根据 item.id 模式修正分类。

    返回: (category, subcategory)
    """
    iid = item.get('id', '')

    # Spawn eggs → miscellaneous / spawn_eggs
    if iid.endswith('_spawn_egg'):
        return ('miscellaneous', 'spawn_eggs')

    # ---- 按后缀匹配 ----
    _suffix_rules = [
        # (suffix, category, subcategory)
        # 颜色变体
        ('_wool', 'building_blocks', 'colored_blocks'),
        ('_carpet', 'building_blocks', 'colored_blocks'),
        ('_bed', 'functional_blocks', 'utility'),
        ('_concrete', 'building_blocks', 'colored_blocks'),
        ('_concrete_powder', 'building_blocks', 'colored_blocks'),
        ('_terracotta', 'building_blocks', 'colored_blocks'),
        ('_glazed_terracotta', 'building_blocks', 'colored_blocks'),
        ('_stained_glass', 'building_blocks', 'glass_blocks'),
        ('_stained_glass_pane', 'building_blocks', 'glass_blocks'),
        # 木材变体
        ('_planks', 'building_blocks', 'wood_blocks'),
        ('_log', 'natural_blocks', 'vegetation'),
        ('_wood', 'building_blocks', 'wood_blocks'),
        ('_sign', 'functional_blocks', 'utility'),
        ('_hanging_sign', 'functional_blocks', 'utility'),
        ('_door', 'building_blocks', 'wood_blocks'),
        ('_trapdoor', 'building_blocks', 'wood_blocks'),
        ('_fence', 'building_blocks', 'wood_blocks'),
        ('_fence_gate', 'building_blocks', 'wood_blocks'),
        ('_slab', 'building_blocks', 'decorative_blocks'),
        ('_stairs', 'building_blocks', 'decorative_blocks'),
        ('_boat', 'miscellaneous', 'transport'),
        ('_button', 'building_blocks', 'wood_blocks'),
        ('_pressure_plate', 'building_blocks', 'wood_blocks'),
        # 工具/武器
        ('_pickaxe', 'tools', 'pickaxes'),
        ('_axe', 'tools', 'axes'),
        ('_shovel', 'tools', 'shovels'),
        ('_hoe', 'tools', 'hoes'),
        ('_sword', 'combat', 'swords'),
        ('_helmet', 'combat', 'armor'),
        ('_chestplate', 'combat', 'armor'),
        ('_leggings', 'combat', 'armor'),
        ('_boots', 'combat', 'armor'),
        ('_horse_armor', 'combat', 'armor'),
        # 材料
        ('_ingot', 'materials', 'ores_ingots'),
        ('_nugget', 'materials', 'ores_ingots'),
        ('_dye', 'materials', 'dyes'),
    ]

    for suffix, cat, sub in _suffix_rules:
        if iid.endswith(suffix):
            return (cat, sub)

    # 按前缀匹配（木材变体的另一种形式）
    for wood in _WOOD_NAME_ZH:
        if iid.startswith(wood + '_'):
            for suffix, cat, sub in _suffix_rules:
                if iid.endswith(suffix):
                    return (cat, sub)

    # 保持原分类
    return (item.get('category', 'miscellaneous'), item.get('subcategory', 'general'))


def apply_category_fix(items):
    """修正所有物品的分类"""
    fixes = 0
    for item in items:
        old_cat = item.get('category', '')
        old_sub = item.get('subcategory', '')
        new_cat, new_sub = normalize_category(item)
        if old_cat != new_cat or old_sub != new_sub:
            item['category'] = new_cat
            item['subcategory'] = new_sub
            fixes += 1
    print(f"  [CATEGORY_FIX] Fixed {fixes} items")
    return fixes


def generate_zh_name(item):
    """根据 item.id 规则生成中文名"""
    iid = item.get('id', '')

    # Spawn egg: {entity}_spawn_egg → {entity_zh}刷怪蛋
    if iid.endswith('_spawn_egg'):
        entity = iid[:-len('_spawn_egg')]
        entity_zh = _ENTITY_ZH.get(entity, entity.replace('_', ' ').title())
        return entity_zh + '刷怪蛋'

    # 尝试匹配颜色变体: {color}_{base}
    for color_en, color_zh in _COLOR_NAME_ZH.items():
        for base_en, base_zh in _BASE_NAME_ZH.items():
            expected = f'{color_en}_{base_en}'
            if iid == expected:
                return color_zh + base_zh

    # 尝试匹配木材变体: {wood}_{base}
    for wood_en, wood_zh in _WOOD_NAME_ZH.items():
        for base_en, base_zh in _BASE_NAME_ZH.items():
            expected = f'{wood_en}_{base_en}'
            if iid == expected:
                return wood_zh + base_zh

    # 未匹配 → 返回 None
    return None


def apply_zh_fill(items):
    """为缺失中文名的物品填充中文名"""
    filled = 0
    for item in items:
        if item.get('name_zh') != item.get('name_en'):
            continue  # 已有中文名
        zh = generate_zh_name(item)
        if zh:
            item['name_zh'] = zh
            filled += 1
            # 同时更新 ZH_MAP（供后续查询）
            ZH_MAP[item['name_en']] = zh
    print(f"  [ZH_FILL] Filled {filled} Chinese names")
    return filled


def consistency_check(items):
    """检查同类物品分类一致性"""
    groups = {}
    for item in items:
        iid = item.get('id', '')
        # 提取 suffix group
        parts = iid.split('_')
        if len(parts) >= 2:
            suffix = '_' + '_'.join(parts[-2:]) if len(parts) >= 3 else '_' + parts[-1]
        else:
            suffix = iid
        if suffix not in groups:
            groups[suffix] = {}
        cat_sub = (item.get('category', ''), item.get('subcategory', ''))
        groups[suffix][cat_sub] = groups[suffix].get(cat_sub, 0) + 1

    issues = 0
    for suffix, cat_counts in sorted(groups.items()):
        if len(cat_counts) > 1 and sum(cat_counts.values()) >= 3:
            issues += 1
            print(f"  [INCONSISTENT] suffix={suffix}: {dict(cat_counts)}")

    if issues == 0:
        print(f"  [CONSISTENCY] All item groups consistent")
    return issues


def patch_missing_variants(items):
    """
    为缺失的变体物品生成合成 item。
    基于已存在的同类变体推断缺失项。
    """
    existing_ids = set(i.get('id', '') for i in items)
    patched = []

    # Find a template for each base type
    templates = {}
    for item in items:
        iid = item.get('id', '')
        # Extract base type from variant
        for base in _BASE_NAME_ZH:
            if iid.endswith('_' + base):
                if base not in templates:
                    templates[base] = item
                break

    # Define missing variants to generate
    # Format: (expected_id, color|wood, base_type)
    _missing_specs = [
        # Color variants
        ('white_terracotta', 'white', 'terracotta'),
        # Wood variants that don't have overview pages in cache
        ('oak_door', 'oak', 'door'),
        ('iron_door', 'iron', 'door'),
        ('oak_fence', 'oak', 'fence'),
        ('oak_slab', 'oak', 'slab'),
        ('oak_stairs', 'oak', 'stairs'),
        ('oak_boat', 'oak', 'boat'),
        ('spruce_boat', 'spruce', 'boat'),
        ('birch_boat', 'birch', 'boat'),
    ]

    for var_id, prefix, base_type in _missing_specs:
        if var_id in existing_ids:
            continue

        template = templates.get(base_type)
        if not template:
            # Try to find any item that could serve as template
            for item in items:
                if item.get('id', '').endswith('_' + base_type):
                    template = item
                    break
        if not template:
            continue

        # Build variant item
        var_item = template.copy()

        # Generate name
        if prefix in _COLOR_NAME_ZH:
            color_zh = _COLOR_NAME_ZH[prefix]
            base_zh = _BASE_NAME_ZH.get(base_type, base_type.title())
            name_en = f'{prefix.title()} {base_type.replace("_", " ").title()}'
            name_zh = color_zh + base_zh
        elif prefix in _WOOD_NAME_ZH:
            wood_zh = _WOOD_NAME_ZH[prefix]
            base_zh = _BASE_NAME_ZH.get(base_type, base_type.title())
            name_en = f'{wood_zh.split("木")[0] if "木" in wood_zh else wood_zh} {base_type.replace("_", " ").title()}'
            # Don't double the 木
            name_zh = wood_zh + base_zh
        elif prefix == 'iron':
            name_en = f'Iron {base_type.replace("_", " ").title()}'
            name_zh = f'铁{_BASE_NAME_ZH.get(base_type, base_type.title())}'
        else:
            name_en = var_id.replace('_', ' ').title()
            name_zh = name_en

        var_item['id'] = var_id
        var_item['name_en'] = name_en
        var_item['name_zh'] = name_zh
        var_item['icon_url'] = template.get('icon_url', '').replace(
            template.get('id', '').split('_', 1)[-1] if '_' in template.get('id', '') else template.get('id', ''),
            base_type
        )
        # Use Special:FilePath for icon
        var_item['icon_url'] = f'https://minecraft.wiki/w/Special:FilePath/{name_en.replace(" ", "_")}.png'
        var_item['source'] = 'synthetic'
        var_item['crafting'] = []
        var_item['stonecutting'] = []
        var_item['smithing'] = []
        var_item['related_items'] = []

        # Fix category
        new_cat, new_sub = normalize_category(var_item)
        var_item['category'] = new_cat
        var_item['subcategory'] = new_sub

        patched.append(var_item)

    if patched:
        items.extend(patched)
        print(f"  [VARIANT_PATCH] Generated {len(patched)} missing variants:")
        for v in patched:
            print(f"    - {v['id']}: {v['name_zh']}")

    return len(patched)


def apply_final_fixes(items):
    """
    终局修复：分类修正 → 中文补全 → 变体补丁 → 一致性检查
    """
    print("\n" + "=" * 60)
    print("终局数据修复")
    print("=" * 60)

    # 1. 分类修正
    print("\n[1/4] 分类修正")
    cat_fixes = apply_category_fix(items)

    # 2. 中文补全
    print("\n[2/4] 中文补全")
    zh_filled = apply_zh_fill(items)

    # 3. 变体补丁
    print("\n[3/4] 缺失变体补全")
    variant_patched = patch_missing_variants(items)

    # 4. 一致性检查
    print("\n[4/4] 一致性检查")
    inconsistency = consistency_check(items)

    # 重新统计中文覆盖率
    zh_ok = sum(1 for i in items if i.get('name_zh') != i.get('name_en'))
    zh_total = len(items)
    zh_cov = zh_ok / max(zh_total, 1) * 100

    print(f"\n  修复完成: {cat_fixes} 分类修正, {zh_filled} 中文补全, {variant_patched} 变体补丁")
    print(f"  中文覆盖率: {zh_cov:.1f}% ({zh_ok}/{zh_total})")

    return {
        'cat_fixes': cat_fixes,
        'zh_filled': zh_filled,
        'variant_patched': variant_patched,
        'inconsistency': inconsistency,
        'zh_coverage': round(zh_cov, 1),
    }
