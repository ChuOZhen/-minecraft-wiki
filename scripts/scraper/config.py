# ============================================
# config.py — 爬虫常量与配置
# ============================================

import os

BASE_URL = "https://minecraft.wiki"
ITEM_LIST_URL = f"{BASE_URL}/w/Item"
WIKI_API = f"{BASE_URL}/api/rest_v1/page/html"

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MinecraftWikiResearch/1.0; +https://github.com/minecraft-items-wiki)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = [5, 10, 20]  # seconds
MIN_DELAY = 3.0
MAX_DELAY = 5.0

# Category keywords → classification
CATEGORY_KEYWORDS = {
    "building_blocks": [
        "block", "brick", "plank", "log", "stone", "concrete", "terracotta",
        "glass", "wool", "clay", "sand", "gravel", "dirt", "ice", "obsidian",
        "ore", "netherrack", "end stone", "purpur", "prismarine", "quartz",
        "slab", "stair", "wall", "fence", "gate", "door", "trapdoor",
        "Building block", "building block", "Construction",
    ],
    "natural_blocks": [
        "grass", "leaves", "sapling", "flower", "mushroom", "vine", "cactus",
        "sugar cane", "bamboo", "kelp", "coral", "seagrass", "roots",
        "Natural block", "plant", "tree", "vegetation", "crop",
    ],
    "functional_blocks": [
        "crafting table", "furnace", "chest", "barrel", "bed", "beacon",
        "enchanting table", "anvil", "brewing stand", "cauldron", "hopper",
        "dispenser", "dropper", "observer", "piston", "note block", "jukebox",
        "lectern", "loom", "grindstone", "smithing table", "cartography",
        "campfire", "conduit", "lodestone", "respawn anchor", "sculk",
        "Functional block", "Utility block", "mechanism",
    ],
    "tools": [
        "pickaxe", "axe", "shovel", "hoe", "shears", "flint and steel",
        "fishing rod", "brush", "lead", "saddle", "bucket",
        "Tool", "tool", "Equipment",
    ],
    "combat": [
        "sword", "bow", "crossbow", "arrow", "armor", "helmet", "chestplate",
        "leggings", "boots", "shield", "trident", "mace", "totem",
        "Weapon", "weapon", "Armor", "armor", "Combat",
    ],
    "food": [
        "apple", "bread", "meat", "beef", "porkchop", "chicken", "mutton",
        "rabbit", "fish", "salmon", "cod", "cake", "pie", "cookie", "soup",
        "stew", "carrot", "potato", "beetroot", "melon", "berries",
        "Food", "food", "edible", "drink", "potion",
    ],
    "materials": [
        "ingot", "diamond", "emerald", "coal", "dust", "nugget", "gem",
        "shard", "crystal", "scrap", "leather", "paper", "feather",
        "string", "bone", "slime", "gunpowder", "glowstone", "blaze",
        "Material", "material", "Ingredient",
    ],
    "miscellaneous": [
        "disc", "banner", "pattern", "dye", "book", "map", "compass",
        "clock", "bottle", "bucket", "saddle", "name tag", "spawn egg",
        "boat", "minecart", "rail", "firework", "painting", "frame",
        "Misc", "misc", "Decor", "decor",
    ],
}

# Item name → (subcategory ID, subcategory zh)
# Used as fallback when wiki categories can't be determined
SUBCATEGORY_FALLBACK = {
    "stone": ("stone_blocks", "石质方块"),
    "cobblestone": ("stone_blocks", "石质方块"),
    "granite": ("stone_blocks", "石质方块"),
    "diorite": ("stone_blocks", "石质方块"),
    "andesite": ("stone_blocks", "石质方块"),
    "stone_bricks": ("stone_blocks", "石质方块"),
    "bricks": ("stone_blocks", "石质方块"),
    "oak_log": ("wood_blocks", "木质方块"),
    "oak_planks": ("wood_blocks", "木质方块"),
    "glass": ("glass_blocks", "玻璃"),
    "grass_block": ("surface", "地表方块"),
    "dirt": ("surface", "地表方块"),
    "oak_leaves": ("vegetation", "植被"),
    "oak_sapling": ("vegetation", "植被"),
}

# Pages to skip (not items)
SKIP_PATTERNS = [
    "/Category:", "/Template:", "/Module:", "/Talk:",
    "/File:", "/Special:", "/User:", "/Help:",
    "/Java_Edition", "/Bedrock_Edition", "/Tutorial",
    "/Update", "/Planned", "/Upcoming",
    "/Gallery", "/Achievement", "/Advancement",
    "/Effect", "/Enchanting", "/Status_effect",
    # Education Edition
    "/Education_Edition", "/MinecraftEdu", "/Minecraft_Education",
    # April Fools
    "/April_Fools", "/Poisonous_Potato_",
    "/Swaggiest", "/A_Very_Fine_Item",
    # Disambiguation / entities
    "/List_of", "/Comparison",
    "/Villager", "/Pillager", "/Wandering_Trader",
]
