#!/usr/bin/env python3
"""
supplement_crawler.py — 为 674 个非 wiki-sourced 物品补充爬取 Wiki 页面
策略：
1. 爬取概览页面（Wool, Potion, Enchanted_Book 等）供变体展开器使用
2. 爬取独立物品页面（Iron_Ingot, Oak_Planks 等）
3. 缓存优先，不重复请求
"""
import json, os, sys, time, hashlib, random
import subprocess
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CACHE_DIR = SCRIPT_DIR / 'cache'
DATA_PATH = SCRIPT_DIR.parent / 'docs' / 'data' / 'data.json'
LOG_PATH = SCRIPT_DIR / 'supplement_crawl.log'
SKIP_LOG = SCRIPT_DIR / 'supplement_skip.log'

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# FIX: 不设自定义 UA！裸 curl UA 正常，伪装浏览器反而 403
UA = None

# ============================================================
# 概览页面 — 变体数据从这些页面提取
# ============================================================
OVERVIEW_PAGES = [
    'Wool', 'Carpet', 'Bed', 'Concrete', 'Glazed_Terracotta',
    'Stained_Glass', 'Candle', 'Shulker_Box', 'Banner',
    'Potion', 'Splash_Potion', 'Lingering_Potion', 'Tipped_Arrow',
    'Enchanted_Book', 'Spawn_Egg', 'Music_Disc',
    'Pottery_Sherd', 'Banner_Pattern', 'Smithing_Template',
    'Boat', 'Minecart', 'Dye',
    # Wood overviews
    'Oak', 'Spruce', 'Birch', 'Jungle', 'Acacia',
    'Dark_Oak', 'Mangrove', 'Cherry', 'Bamboo',
    'Crimson', 'Warped', 'Pale_Oak',
    # Block overviews
    'Copper', 'Block_of_Copper', 'Stone_Bricks', 'Prismarine',
    'Sandstone', 'Quartz', 'Purpur', 'Blackstone', 'Basalt',
    'Deepslate', 'Tuff', 'Mud', 'Resin', 'Nether_Bricks',
    # Tools/Armor sets
    'Pickaxe', 'Axe', 'Shovel', 'Hoe', 'Sword',
    'Helmet', 'Chestplate', 'Leggings', 'Boots',
    'Bow', 'Crossbow', 'Shield', 'Trident', 'Mace',
    # Food
    'Bread', 'Apple', 'Carrot', 'Potato', 'Beetroot',
    'Cooked_Beef', 'Cooked_Porkchop', 'Cooked_Mutton', 'Cooked_Chicken',
    'Cooked_Cod', 'Cooked_Salmon', 'Rabbit_Stew', 'Mushroom_Stew',
    'Suspicious_Stew', 'Cake', 'Cookie', 'Pumpkin_Pie',
    # Materials
    'Iron_Ingot', 'Gold_Ingot', 'Copper_Ingot', 'Diamond', 'Emerald',
    'Netherite_Ingot', 'Coal', 'Amethyst_Shard', 'Lapis_Lazuli',
    'Nether_Quartz', 'Echo_Shard', 'Nautilus_Shell', 'Heart_of_the_Sea',
    'Blaze_Rod', 'Ghast_Tear', 'Magma_Cream', 'Nether_Star',
    'Ender_Pearl', 'Ender_Eye', 'Spider_Eye', 'Fermented_Spider_Eye',
    'Slimeball', 'Honeycomb', 'Bone_Meal', 'Sugar', 'Gunpowder',
    'Stick', 'String', 'Feather', 'Flint', 'Leather',
    'Paper', 'Book', 'Brick', 'Nether_Brick', 'Clay_Ball',
    'Glowstone_Dust', 'Redstone_Dust', 'Fire_Charge',
    'Snowball', 'Egg', 'Wheat', 'Bucket', 'Water_Bucket', 'Lava_Bucket',
    # Functional
    'Chest', 'Furnace', 'Brewing_Stand', 'Crafting_Table',
    'Anvil', 'Enchanting_Table', 'Cauldron', 'Loom',
    'Stonecutter', 'Grindstone', 'Smithing_Table', 'Cartography_Table',
    'Fletching_Table', 'Composter', 'Barrel',
    'Torch', 'Lantern', 'Campfire', 'End_Rod',
    'Rail', 'Powered_Rail', 'Detector_Rail', 'Activator_Rail',
    'Hopper', 'Dropper', 'Dispenser', 'Observer', 'Piston', 'TNT',
    'Note_Block', 'Jukebox', 'Beacon', 'Conduit', 'Lodestone', 'Respawn_Anchor',
    'Bell', 'Scaffolding', 'Ladder', 'Daylight_Detector',
    'Beehive', 'Bee_Nest', 'Flower_Pot', 'Decorated_Pot',
    'Item_Frame', 'Glow_Item_Frame', 'Armor_Stand', 'Painting',
    'Bookshelf', 'Lectern', 'Spawner', 'Dragon_Egg',
    'Nether_Portal', 'End_Portal_Frame', 'End_Crystal',
    'Crafter', 'Vault', 'Trial_Spawner',
    'Lightning_Rod', 'Tripwire_Hook',
    # Redstone
    'Redstone', 'Redstone_Torch', 'Redstone_Repeater', 'Redstone_Comparator',
    'Lever', 'Button', 'Pressure_Plate',
    # Misc items
    'Compass', 'Recovery_Compass', 'Clock', 'Spyglass', 'Brush',
    'Lead', 'Name_Tag', 'Saddle', 'Bundle',
    'Fishing_Rod', 'Shears', 'Flint_and_Steel',
    'Carrot_on_a_Stick', 'Warped_Fungus_on_a_Stick',
    'Firework_Rocket', 'Firework_Star',
    'Map', 'Filled_Map', 'Book_and_Quill',
    'Goat_Horn', 'Wind_Charge', 'Breeze_Rod',
    'Heavy_Core', 'Ominous_Bottle', 'Trial_Key', 'Ominous_Trial_Key',
    'Experience_Bottle', 'Enchanted_Book',
    'Totem_of_Undying', 'Elytra', 'Wolf_Armor',
    'Armadillo_Scute', 'Turtle_Scute',
    'Glass_Bottle', 'Dragon_Breath',
]


def url_to_cache_path(url):
    h = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f'{h}.html'


def crawl_one(url, max_retries=2):
    """Download a single page using curl. Returns True if successful."""
    cache_path = url_to_cache_path(url)

    # Skip if already cached and seems valid
    if cache_path.exists() and cache_path.stat().st_size > 500:
        return True

    for attempt in range(max_retries + 1):
        try:
            cmd = ['curl', '-s', '-o', str(cache_path), '-w', '%{http_code}',
                '-L', '--max-time', '20']
            if UA:
                cmd += ['-H', f'User-Agent: {UA}']
            cmd.append(url)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            http_code = result.stdout.strip()

            if http_code == '200' and cache_path.stat().st_size > 500:
                # Check it's HTML, not an error page
                with open(cache_path, 'rb') as f:
                    first = f.read(100)
                if b'<!DOCTYPE html>' in first or b'<html' in first:
                    return True
                # Not HTML - delete
                cache_path.unlink(missing_ok=True)

            if http_code == '404':
                with open(SKIP_LOG, 'a', encoding='utf-8') as f:
                    f.write(f'404 {url}\n')
                return False

            if http_code == '429':
                wait = 10 * (attempt + 1)
                print(f'    Rate limited, waiting {wait}s...')
                time.sleep(wait)
                continue

            # Clean up bad file
            cache_path.unlink(missing_ok=True)
            if attempt < max_retries:
                time.sleep(3)

        except Exception as e:
            cache_path.unlink(missing_ok=True)
            if attempt < max_retries:
                time.sleep(3)

    return False


def main():
    print('=' * 60)
    print('Supplement Crawler — 补充爬取 Wiki 页面')
    print('=' * 60)

    # Load data to understand what we need
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    non_wiki = [i for i in data['items'] if i.get('source') != 'wiki']
    print(f'\nNon-wiki items: {len(non_wiki)}/{len(data["items"])}')

    # Collect all URLs in cache already
    existing_hashes = set()
    for f in CACHE_DIR.iterdir():
        if f.is_file() and f.suffix == '.html':
            existing_hashes.add(f.name)

    # Build URL list: overview pages + individual item pages
    urls_to_crawl = []

    # 1. Overview pages
    for page in OVERVIEW_PAGES:
        url = f'https://minecraft.wiki/w/{page}'
        if url_to_cache_path(url).name not in existing_hashes:
            urls_to_crawl.append(('overview', url))

    # 2. Individual item pages for non-wiki items
    for item in non_wiki:
        iid = item['id']
        # Skip items that should come from overview pages
        skip_subs = ['potion', 'spawn_egg', 'enchanted_book', 'disc', 'pottery_sherd',
                      'banner_pattern', 'dye', 'wool', 'carpet', 'bed', 'concrete',
                      'terracotta', 'stained_glass', 'candle', 'shulker_box']
        if item['subcategory'] in skip_subs:
            continue

        url_name = iid.replace('_', ' ').title().replace(' ', '_')
        url = f'https://minecraft.wiki/w/{url_name}'
        if url_to_cache_path(url).name not in existing_hashes:
            urls_to_crawl.append(('item', url))

    print(f'URLs to crawl: {len(urls_to_crawl)}')
    overview_count = sum(1 for t, _ in urls_to_crawl if t == 'overview')
    item_count = sum(1 for t, _ in urls_to_crawl if t == 'item')
    print(f'  Overview: {overview_count}')
    print(f'  Individual: {item_count}')

    if not urls_to_crawl:
        print('\nAll pages already cached!')
        return

    # Estimate time
    est_min = len(urls_to_crawl) * 4 / 60
    print(f'Estimated time: {est_min:.0f} min (at 4s/page)')

    # Crawl
    success = 0
    skipped = 0
    failed = 0

    print(f'\nCrawling...')
    for i, (typ, url) in enumerate(urls_to_crawl, 1):
        name = url.split('/')[-1]
        ok = crawl_one(url)

        if ok:
            success += 1
        elif cache_path := url_to_cache_path(url):
            if cache_path.exists():
                skipped += 1  # Was cached
            else:
                failed += 1

        if i % 50 == 0:
            print(f'  [{i}/{len(urls_to_crawl)}] ok={success} fail={failed}')

        # Rate limit: 3-5 seconds
        time.sleep(random.uniform(3.0, 5.0))

    print(f'\nDone!')
    print(f'  Success: {success}')
    print(f'  Failed: {failed}')

    # Count final cache
    final_cache = len([f for f in CACHE_DIR.iterdir() if f.is_file() and f.suffix == '.html'])
    print(f'  Cache pages: {final_cache}')

    # Log
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write(f'Supplement crawl completed\n')
        f.write(f'URLs attempted: {len(urls_to_crawl)}\n')
        f.write(f'Success: {success}\n')
        f.write(f'Failed: {failed}\n')
        f.write(f'Final cache: {final_cache}\n')
    print(f'  Log: {LOG_PATH}')
    if os.path.exists(SKIP_LOG):
        print(f'  Skip log: {SKIP_LOG}')


if __name__ == '__main__':
    main()
