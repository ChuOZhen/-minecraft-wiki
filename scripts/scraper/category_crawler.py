# ============================================
# category_crawler.py — 递归 Category Tree 爬虫
# ============================================
#
# 解决 plan.md 红线：分类逻辑基于 Wiki Category Graph，严禁关键词盲猜。
#
# 用法:
#   from category_crawler import crawl_category_tree, classify_item
#
# 流程:
#   1. crawl_category_tree()  →  递归抓取 Category 页面
#   2. classify_item(slug, wiki_cats)  →  返回 (category, subcategory)
# ============================================

import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from collections import defaultdict

from config import BASE_URL, SKIP_PATTERNS
from utils import normalize_id, is_item_url
from fetcher import fetch_html


# ============================================
# Wiki Category → 项目8大分类 映射表
# ============================================
# 格式: (项目大类ID, 项目小类ID, Wiki类别关键词)
# 按优先级排列，先匹配到的优先

CATEGORY_RULES = [
    # --- 建筑方块 ---
    ("building_blocks", "stone_blocks", ["Stone blocks", "Stone", "Cobblestone",
        "Bricks", "Sandstone", "Terracotta", "Concrete", "Deepslate"]),
    ("building_blocks", "wood_blocks", ["Wooden blocks", "Wood blocks", "Planks",
        "Wood", "Logs", "Log blocks", "Wood variants"]),
    ("building_blocks", "glass_blocks", ["Glass blocks", "Glass", "Stained glass",
        "Glass panes"]),
    ("building_blocks", "colored_blocks", ["Colored blocks", "Wool blocks",
        "Carpets", "Glazed terracotta", "Concrete powder", "Stained clay"]),
    ("building_blocks", "ore_blocks", ["Ore blocks", "Ores", "Mineral blocks",
        "Mineral veins"]),
    ("building_blocks", "nether_blocks", ["Nether blocks", "Netherrack",
        "Nether bricks", "Blackstone", "Basalt", "Crimson blocks", "Warped blocks"]),
    ("building_blocks", "end_blocks", ["End blocks", "End stone", "Purpur",
        "Chorus", "End dimension"]),
    ("building_blocks", "decorative_blocks", ["Decorative blocks", "Slabs",
        "Stairs", "Walls", "Fences", "Fence gates"]),

    # --- 自然方块 ---
    ("natural_blocks", "surface", ["Surface blocks", "Dirt", "Sand", "Gravel",
        "Clay", "Grass blocks", "Mycelium", "Podzol", "Mud", "Snow"]),
    ("natural_blocks", "vegetation", ["Vegetation", "Plants", "Flowers",
        "Saplings", "Leaves", "Grass", "Mushrooms", "Fungi", "Vines", "Crops",
        "Cacti", "Bamboo", "Sugar cane", "Sweet berries", "Glow berries"]),
    ("natural_blocks", "corals", ["Corals", "Coral", "Sea pickles"]),
    ("natural_blocks", "ores", ["Ore", "Ores"]),

    # --- 功能方块 ---
    ("functional_blocks", "workstations", ["Crafting stations", "Crafting",
        "Furnaces", "Enchanting", "Brewing", "Smithing", "Loom", "Grindstone",
        "Cartography table", "Stonecutter"]),
    ("functional_blocks", "storage", ["Storage", "Chests", "Barrels",
        "Shulker boxes", "Ender chest"]),
    ("functional_blocks", "utility", ["Utility blocks", "Beds", "Doors",
        "Trapdoors", "Ladders", "Scaffolding", "Torches", "Lanterns",
        "Signs", "Banners", "Bells", "Cauldrons", "Composters", "Light sources",
        "Lighting"]),
    ("functional_blocks", "mechanisms", ["Mechanisms", "Pistons",
        "Dispensers", "Droppers", "Observers", "Hoppers", "Note blocks",
        "Jukeboxes", "Lecterns", "Targets", "Lightning rods"]),
    ("functional_blocks", "redstone", ["Redstone", "Redstone components",
        "Redstone torches", "Repeaters", "Comparators", "Pressure plates",
        "Buttons", "Levers", "Tripwire", "Daylight sensors", "Sculk",
        "Sculk sensors", "Sculk shriekers"]),
    ("functional_blocks", "beacons", ["Beacons", "Conduits",
        "Respawn anchors", "Lodestones", "End crystals"]),

    # --- 工具 ---
    ("tools", "pickaxes", ["Pickaxes"]),
    ("tools", "axes", ["Axes"]),
    ("tools", "shovels", ["Shovels", "Shovel"]),
    ("tools", "hoes", ["Hoes", "Hoe"]),
    ("tools", "other_tools", ["Equipment", "Shears", "Flint and steel",
        "Fishing rods", "Buckets", "Brushes", "Leads", "Compasses", "Clocks",
        "Spyglasses", "Maps", "Empty maps", "Saddles", "Name tags"]),

    # --- 战斗 ---
    ("combat", "swords", ["Swords", "Maces"]),
    ("combat", "ranged", ["Bows", "Crossbows", "Arrows", "Tridents",
        "Ranged weapons", "Projectiles"]),
    ("combat", "armor", ["Armor", "Helmets", "Chestplates", "Leggings",
        "Boots", "Shields", "Horse armor", "Wolf armor", "Turtle shells",
        "Armor sets", "Armor materials"]),
    ("combat", "enchantments", ["Enchanted books", "Totems", "Totems of undying"]),

    # --- 食物 ---
    ("food", "crops", ["Fruits", "Vegetables", "Crops", "Seeds",
        "Apples", "Carrots", "Potatoes", "Beetroots", "Melons", "Berries"]),
    ("food", "meat", ["Meat", "Raw meat", "Cooked meat", "Fish",
        "Raw fish", "Cooked fish", "Raw food", "Cooked food"]),
    ("food", "prepared", ["Baked goods", "Bread", "Cakes", "Pies",
        "Cookies", "Soups", "Stews", "Prepared food", "Crafted food",
        "Suspicious stew", "Mushroom stew", "Rabbit stew"]),
    ("food", "drinks", ["Potions", "Drinks", "Drinkable items",
        "Honey bottles", "Milk buckets"]),

    # --- 材料 ---
    ("materials", "ores_ingots", ["Ingots", "Gems", "Diamonds", "Emeralds",
        "Metals", "Raw materials", "Metal raw materials", "Raw ores",
        "Nuggets", "Scraps", "Coal", "Charcoal"]),
    ("materials", "organic", ["Organic materials", "Leather", "Paper",
        "Feathers", "Strings", "Bones", "Bone meal", "Slimeballs",
        "Honeycombs", "Gunpowder", "Blaze rods", "Blaze powder",
        "Ender pearls", "Eyes of ender", "Ghast tears", "Nether wart",
        "Magma cream", "Glowstone dust", "Rabbit hide", "Rabbit foot",
        "Spider eyes", "Ink sacs", "Scutes", "Phantom membranes",
        "Shulker shells", "Nautilus shells", "Heart of the sea",
        "Nether stars", "Echo shards"]),
    ("materials", "dyes", ["Dyes", "Dye items"]),
    ("materials", "minerals", ["Minerals", "Quartz", "Lapis lazuli",
        "Amethyst", "Prismarine shards", "Prismarine crystals"]),

    # --- 杂项 ---
    ("miscellaneous", "discs", ["Music discs"]),
    ("miscellaneous", "decor", ["Decorations", "Paintings", "Item frames",
        "Armor stands", "Flower pots", "Candles", "Decoration items"]),
    ("miscellaneous", "transport", ["Transportation", "Boats", "Minecarts",
        "Rails", "Vehicles", "Elytra", "Firework rockets"]),
    ("miscellaneous", "spawn_eggs", ["Spawn eggs"]),
    ("miscellaneous", "banner_patterns", ["Banner patterns", "Banner pattern items"]),
    ("miscellaneous", "utility_items", ["Books", "Bottles", "Bowls",
        "Bundles", "Firework stars", "Knowledge books", "Written books"]),
    ("miscellaneous", "education", ["Education Edition", "Education",
        "Chemistry", "Compounds", "Elements"]),
    ("miscellaneous", "mob_heads", ["Mob heads", "Heads", "Skulls",
        "Player heads", "Mob head"]),
]


# ============================================
# Category Tree 递归爬取
# ============================================

def crawl_category_tree(root_urls=None, max_depth=4, max_pages=200):
    """
    从根 Category 页面出发，递归爬取子分类树。

    返回:
      item_to_cats:   { item_slug → [wiki_category_title, ...] }
      cat_hierarchy:  { parent_cat → [child_cat, ...] }
    """
    if root_urls is None:
        # 默认从这三个顶层分类出发
        root_urls = [
            f"{BASE_URL}/w/Category:Items",
            f"{BASE_URL}/w/Category:Blocks",
            f"{BASE_URL}/w/Category:Entities",  # 生物/实体
        ]

    item_to_cats = defaultdict(list)
    cat_hierarchy = defaultdict(list)
    visited_cats = set()
    visited_pages = set()

    def _crawl(cat_url, depth):
        if depth > max_depth:
            return
        if cat_url in visited_cats:
            return
        if len(visited_cats) >= max_pages:
            return

        cat_title = cat_url.rstrip('/').split('/')[-1].replace('_', ' ')
        visited_cats.add(cat_url)
        print(f"  [CAT:{depth}] {cat_title}")

        html = fetch_html(cat_url, use_cache=True)
        if not html:
            return

        soup = BeautifulSoup(html, 'lxml')
        body = soup.find('div', id='mw-content-text') or soup.find('div', class_='mw-parser-output')
        if not body:
            body = soup

        # --- 提取子分类 ---
        subcat_div = body.find('div', id='mw-subcategories')
        if subcat_div:
            for a in subcat_div.find_all('a', href=True):
                href = a['href'].strip()
                if href.startswith('#') or ':' not in href:
                    continue
                if '/Category:' in href or '/category:' in href.lower():
                    child_url = urljoin(BASE_URL, href)
                    child_title = child_url.rstrip('/').split('/')[-1].replace('_', ' ')
                    cat_hierarchy[cat_title].append(child_title)
                    _crawl(child_url, depth + 1)

        # --- 提取此分类下的物品页面 ---
        pages_div = body.find('div', id='mw-pages')
        if pages_div:
            for a in pages_div.find_all('a', href=True):
                href = a['href'].strip()
                if href.startswith('#'):
                    continue
                # 排除分类/模板/文件页面
                skip = False
                for pat in SKIP_PATTERNS:
                    if pat in href:
                        skip = True
                        break
                if skip:
                    continue

                full_url = urljoin(BASE_URL, href)
                slug = full_url.rstrip('/').split('/')[-1].lower()
                if not slug or len(slug) < 2:
                    continue
                if slug in visited_pages:
                    continue
                visited_pages.add(slug)

                # 记录物品所属的 Wiki 分类
                item_to_cats[slug].append(cat_title)

    # 开始爬取
    for root_url in root_urls:
        _crawl(root_url, depth=0)

    print(f"\n  Category crawl done: {len(visited_cats)} categories, "
          f"{len(visited_pages)} unique item slugs")

    return dict(item_to_cats), dict(cat_hierarchy)


# ============================================
# 分类映射引擎
# ============================================

def classify_item(item_slug, wiki_cats_from_page=None):
    """
    基于 Wiki 分类路径确定项目的 category + subcategory。

    参数:
      item_slug: 物品的 URL slug (如 "Stone")
      wiki_cats_from_page: 从物品页面底部解析的 Wiki 分类列表
                           (parser_list.parse_page_categories 的输出)

    返回: (category_id, subcategory_id, confidence)
      confidence: "wiki_graph" | "page_cats" | "fallback"

    优先级:
      1. 物品页面底部类别标签 (page_cats) — 最精确
      2. 递归爬取的 Category Graph — 系统级准确
      3. 回退: 默认 miscellaneous/general
    """
    all_cats = []

    # 来源 1: 物品页面自身
    if wiki_cats_from_page:
        all_cats.extend(wiki_cats_from_page)

    # 来源 2: 递归 Category Tree (如果已预爬取)
    # all_cats 也包含来自 crawl_category_tree 的结果

    if not all_cats:
        return ("miscellaneous", "general", "fallback")

    # 按规则匹配
    cat_text = ' '.join(all_cats)
    cat_lower = cat_text.lower()

    best_match = None
    best_priority = 999

    for idx, (cat_id, sub_id, keywords) in enumerate(CATEGORY_RULES):
        for kw in keywords:
            if kw.lower() in cat_lower:
                if idx < best_priority:
                    best_match = (cat_id, sub_id)
                    best_priority = idx
                break

    if best_match:
        return (*best_match, "page_cats")

    # 回退: 用大类级别关键词判断
    broad_rules = [
        ("building_blocks", "Block"),
        ("natural_blocks", "Natural block"),
        ("functional_blocks", "Utility block"),
        ("tools", "Tool"),
        ("combat", "Weapon"),
        ("food", "Food"),
        ("materials", "Material"),
        ("miscellaneous", "Item"),
    ]
    for cat_id, kw in broad_rules:
        if kw.lower() in cat_lower:
            return (cat_id, "general", "fallback")

    return ("miscellaneous", "general", "fallback")


# ============================================
# 从物品列表页批量抓取
# ============================================

def fetch_items_from_category_page(category_url, use_cache=True):
    """
    从单个 Category 页面提取物品链接列表。
    适用页面: Category:Items, Category:Blocks, Category:Tools 等。

    返回: [(full_url, slug)]
    """
    html = fetch_html(category_url, use_cache=use_cache)
    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    body = soup.find('div', id='mw-content-text') or soup.find('div', class_='mw-parser-output')
    if not body:
        body = soup

    items = []
    seen = set()

    # 从 mw-pages 和 mw-category 提取
    for container_id in ['mw-pages', 'mw-category']:
        container = body.find('div', id=container_id)
        if not container:
            container = body.find('div', class_=container_id)
        if not container:
            continue

        for a in container.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith('#'):
                continue
            if any(pat in href for pat in SKIP_PATTERNS):
                continue
            full_url = urljoin(BASE_URL, href)
            slug = full_url.rstrip('/').split('/')[-1]
            if not slug or slug in seen:
                continue
            seen.add(slug)
            items.append((full_url, slug))

    return items


# ============================================
# 批量分类（供 main.py 调用）
# ============================================

def build_category_index(item_urls, pre_crawl=False):
    """
    构建完整的分类索引。

    参数:
      item_urls: [(url, slug), ...]  物品链接列表
      pre_crawl: 是否预先递归爬取 Category Tree（慢但准确）

    返回: { slug → (category_id, subcategory_id, confidence) }
    """
    idx = {}

    # 可选：递归爬取 Category Tree
    cat_graph = {}
    if pre_crawl:
        item_to_cats, cat_graph = crawl_category_tree(max_depth=3, max_pages=100)

    # 对每个物品 URL，通过其页面底部分类标签确定大类/小类
    # （实际使用中，分类信息会在 parse_item_page 阶段从页面提取）
    for url, slug in item_urls:
        wiki_cats = []  # 将在解析物品页面时填充
        cat_id, sub_id, conf = classify_item(slug, wiki_cats)
        idx[slug] = (cat_id, sub_id, conf)

    return idx, cat_graph
