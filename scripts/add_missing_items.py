#!/usr/bin/env python3
"""Add 122 missing items: generate data, crawl wiki, download images."""
import json, os, re, time, subprocess, hashlib
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / 'docs' / 'data' / 'data.json'
IMAGES_DIR = SCRIPT_DIR / 'docs' / 'images'
CACHE_DIR = SCRIPT_DIR / 'scraper' / 'cache'

# ============================================================
# Complete missing items with zh names, categories, subcategories
# ============================================================
NEW_ITEMS = [
    # Pale oak (10)
    ('pale_oak_sapling','苍白橡树苗','blocks','wood'),
    ('pale_oak_leaves','苍白橡树叶','blocks','wood'),
    ('pale_oak_slab','苍白橡木台阶','blocks','wood'),
    ('pale_oak_stairs','苍白橡木楼梯','blocks','wood'),
    ('pale_oak_fence','苍白橡木栅栏','blocks','wood'),
    ('pale_oak_door','苍白橡木门','blocks','wood'),
    ('pale_oak_trapdoor','苍白橡木活板门','blocks','wood'),
    ('pale_oak_pressure_plate','苍白橡木压力板','blocks','wood'),
    ('pale_oak_button','苍白橡木按钮','blocks','wood'),
    ('pale_oak_stripped_log','去皮苍白橡木原木','blocks','wood'),
    # Stone/Bricks (6)
    ('sand','沙子','blocks','sand'),
    ('mossy_stone_brick_stairs','苔石砖楼梯','blocks','bricks'),
    ('chiseled_tuff_bricks','錾制凝灰岩砖','blocks','bricks'),
    ('cracked_tuff_bricks','裂纹凝灰岩砖','blocks','bricks'),
    ('polished_blackstone_brick_stairs','磨制黑石砖楼梯','blocks','bricks'),
    ('nether_brick_fence','下界砖栅栏','blocks','bricks'),
    # Waxed copper (32)
    ('waxed_copper_block','涂蜡铜块','blocks','metal'),
    ('waxed_exposed_copper','涂蜡斑驳铜块','blocks','metal'),
    ('waxed_weathered_copper','涂蜡锈蚀铜块','blocks','metal'),
    ('waxed_oxidized_copper','涂蜡氧化铜块','blocks','metal'),
    ('waxed_cut_copper','涂蜡切制铜块','blocks','metal'),
    ('waxed_exposed_cut_copper','涂蜡斑驳切制铜块','blocks','metal'),
    ('waxed_weathered_cut_copper','涂蜡锈蚀切制铜块','blocks','metal'),
    ('waxed_oxidized_cut_copper','涂蜡氧化切制铜块','blocks','metal'),
    ('waxed_chiseled_copper','涂蜡錾制铜块','blocks','metal'),
    ('waxed_exposed_chiseled_copper','涂蜡斑驳錾制铜块','blocks','metal'),
    ('waxed_weathered_chiseled_copper','涂蜡锈蚀錾制铜块','blocks','metal'),
    ('waxed_oxidized_chiseled_copper','涂蜡氧化錾制铜块','blocks','metal'),
    ('waxed_copper_grate','涂蜡铜格栅','blocks','metal'),
    ('waxed_exposed_copper_grate','涂蜡斑驳铜格栅','blocks','metal'),
    ('waxed_weathered_copper_grate','涂蜡锈蚀铜格栅','blocks','metal'),
    ('waxed_oxidized_copper_grate','涂蜡氧化铜格栅','blocks','metal'),
    ('waxed_copper_door','涂蜡铜门','functional_blocks','door'),
    ('waxed_exposed_copper_door','涂蜡斑驳铜门','functional_blocks','door'),
    ('waxed_weathered_copper_door','涂蜡锈蚀铜门','functional_blocks','door'),
    ('waxed_oxidized_copper_door','涂蜡氧化铜门','functional_blocks','door'),
    ('waxed_copper_trapdoor','涂蜡铜活板门','functional_blocks','door'),
    ('waxed_exposed_copper_trapdoor','涂蜡斑驳铜活板门','functional_blocks','door'),
    ('waxed_weathered_copper_trapdoor','涂蜡锈蚀铜活板门','functional_blocks','door'),
    ('waxed_oxidized_copper_trapdoor','涂蜡氧化铜活板门','functional_blocks','door'),
    ('waxed_copper_bulb','涂蜡铜灯','functional_blocks','light'),
    ('waxed_exposed_copper_bulb','涂蜡斑驳铜灯','functional_blocks','light'),
    ('waxed_weathered_copper_bulb','涂蜡锈蚀铜灯','functional_blocks','light'),
    ('waxed_oxidized_copper_bulb','涂蜡氧化铜灯','functional_blocks','light'),
    ('waxed_cut_copper_stairs','涂蜡切制铜楼梯','blocks','metal'),
    ('waxed_exposed_cut_copper_stairs','涂蜡斑驳切制铜楼梯','blocks','metal'),
    ('waxed_weathered_cut_copper_stairs','涂蜡锈蚀切制铜楼梯','blocks','metal'),
    ('waxed_oxidized_cut_copper_stairs','涂蜡氧化切制铜楼梯','blocks','metal'),
    ('waxed_cut_copper_slab','涂蜡切制铜台阶','blocks','metal'),
    ('waxed_exposed_cut_copper_slab','涂蜡斑驳切制铜台阶','blocks','metal'),
    ('waxed_weathered_cut_copper_slab','涂蜡锈蚀切制铜台阶','blocks','metal'),
    ('waxed_oxidized_cut_copper_slab','涂蜡氧化切制铜台阶','blocks','metal'),
    # Technical (7)
    ('light','光源方块','functional_blocks','light'),
    ('structure_block','结构方块','functional_blocks','workstation'),
    ('command_block','命令方块','functional_blocks','workstation'),
    ('chain_command_block','连锁命令方块','functional_blocks','workstation'),
    ('repeating_command_block','循环命令方块','functional_blocks','workstation'),
    ('jigsaw','拼图方块','functional_blocks','workstation'),
    ('barrier','屏障','functional_blocks','workstation'),
    # Functional (3)
    ('chiseled_bookshelf','錾制书架','functional_blocks','storage'),
    ('suspicious_sand','可疑的沙子','blocks','sand'),
    ('suspicious_gravel','可疑的沙砾','blocks','sand'),
    # Tools (7)
    ('flint_and_steel','打火石','tools','utility'),
    ('clock','时钟','tools','utility'),
    ('name_tag','命名牌','tools','utility'),
    ('trident','三叉戟','combat','ranged'),
    ('shield','盾牌','combat','shield'),
    ('totem_of_undying','不死图腾','combat','shield'),
    ('experience_bottle','附魔之瓶','items','misc'),
    # Materials/Items (18)
    ('ender_eye','末影之眼','materials','other_material'),
    ('ender_pearl','末影珍珠','materials','other_material'),
    ('honeycomb','蜜脾','materials','other_material'),
    ('honey_bottle','蜂蜜瓶','food','effect_food'),
    ('bucket','桶','items','misc'),
    ('water_bucket','水桶','items','misc'),
    ('lava_bucket','熔岩桶','items','misc'),
    ('powder_snow_bucket','细雪桶','items','misc'),
    ('axolotl_bucket','美西螈桶','items','misc'),
    ('cod_bucket','鳕鱼桶','items','misc'),
    ('pufferfish_bucket','河豚桶','items','misc'),
    ('tadpole_bucket','蝌蚪桶','items','misc'),
    ('tropical_fish_bucket','热带鱼桶','items','misc'),
    ('coal','煤炭','materials','other_material'),
    ('ink_sac','墨囊','items','dye'),
    ('slime_ball','黏液球','materials','other_material'),
    ('rabbit_hide','兔子皮','materials','fiber'),
    ('rabbit_foot','兔子脚','materials','fiber'),
    # Food (17)
    ('baked_potato','烤马铃薯','food','crop'),
    ('poisonous_potato','毒马铃薯','food','crop'),
    ('pumpkin_pie','南瓜派','food','crop'),
    ('cooked_beef','牛排','food','meat'),
    ('cooked_porkchop','熟猪排','food','meat'),
    ('cooked_rabbit','熟兔肉','food','meat'),
    ('cooked_salmon','熟鲑鱼','food','fish'),
    ('pufferfish','河豚','food','fish'),
    ('tropical_fish','热带鱼','food','fish'),
    ('cod','鳕鱼','food','fish'),
    ('salmon','鲑鱼','food','fish'),
    ('mushroom_stew','蘑菇煲','food','crop'),
    ('rotten_flesh','腐肉','food','meat'),
    ('spider_eye','蜘蛛眼','materials','other_material'),
    ('fermented_spider_eye','发酵蛛眼','materials','other_material'),
    ('golden_carrot','金胡萝卜','food','effect_food'),
    ('enchanted_golden_apple','附魔金苹果','food','effect_food'),
    ('glow_berries','发光浆果','food','crop'),
    # Materials (16)
    ('heart_of_the_sea','海洋之心','materials','other_material'),
    ('prismarine_shard','海晶碎片','materials','other_material'),
    ('ghast_tear','恶魂之泪','materials','nether'),
    ('nether_star','下界之星','materials','nether'),
    ('elytra','鞘翅','combat','chestplate'),
    ('disc_fragment_5','唱片残片5','items','disc'),
    ('echo_shard','回响碎片','materials','gem'),
    ('resin_brick','树脂砖','materials','other_material'),
    ('copper_ingot','铜锭','materials','ingot'),
    ('gold_nugget','金粒','materials','ingot'),
    ('copper_nugget','铜粒','materials','ingot'),
    ('writable_book','书与笔','items','misc'),
    ('written_book','成书','items','misc'),
    ('filled_map','已填充的地图','items','misc'),
    ('nether_wart','下界疣','materials','nether'),
    ('resin_clump','树脂团','materials','other_material'),
    ('open_eyeblossom','盛开的眼眸花','blocks','flora'),
]


def title_case(name):
    return '_'.join(p.capitalize() for p in name.split('_'))

def assign_tags(iid, cat, sub):
    tags = set()
    if cat == 'blocks': tags.add('building')
    elif cat == 'colored_blocks': tags.add('building')
    elif cat == 'functional_blocks': tags.add('functional')
    elif cat == 'redstone': tags.add('redstone')
    elif cat == 'combat': tags.add('combat')
    elif cat == 'tools': tags.add('tool')
    elif cat == 'food': tags.add('food')
    elif cat == 'items': tags.add('decoration')
    elif cat == 'materials': tags.add('crafting')
    if sub in ('wood','planks','log'): tags.add('wood')
    elif sub in ('stone','bricks','sand'): tags.add('stone')
    elif sub in ('metal','ingot'): tags.add('metal')
    elif sub in ('ore','gem'): tags.add('mineral')
    elif sub in ('flora','crop','meat','fish'): tags.add('organic')
    elif sub in ('wool','carpet','fiber'): tags.add('fabric')
    if any(n in iid for n in ['nether','crimson','warped','soul','blaze','ghast','wither']):
        tags.add('nether')
    else: tags.add('overworld')
    if sub in ('meat','fish','fiber'): tags.add('dropped')
    elif sub in ('ore','stone','metal','gem'): tags.add('mined')
    else: tags.add('crafted')
    return sorted(tags)

def is_valid_image(path):
    try:
        with open(path,'rb') as f: h = f.read(8)
        return h[:4]==b'\x89PNG' or h[:3]==b'\xff\xd8\xff' or h[:6] in (b'GIF87a',b'GIF89a')
    except: return False

def download_image(iid):
    """Download Invicon_ image from wiki."""
    dest = IMAGES_DIR / f'{iid}.png'
    if dest.exists() and is_valid_image(dest):
        return True
    t = title_case(iid)
    urls = [
        f'https://minecraft.wiki/images/Invicon_{t}.png',
        f'https://minecraft.wiki/images/{t}.png',
    ]
    if 'waxed' in iid:
        base = t.replace('Waxed_','')
        urls.insert(0, f'https://minecraft.wiki/images/Invicon_{base}.png')
    for url in urls:
        r = subprocess.run(['curl','-s','-o',str(dest),'-w','%{http_code}','-L','--max-time','12',url],
                           capture_output=True, text=True, timeout=20)
        if r.stdout.strip()=='200' and dest.exists() and dest.stat().st_size>100:
            if is_valid_image(dest): return True
        if dest.exists(): dest.unlink()
    return False

def crawl_wiki(iid):
    """Cache wiki page for item."""
    t = title_case(iid)
    url = f'https://minecraft.wiki/w/{t}'
    fn = hashlib.md5(url.encode()).hexdigest() + '.html'
    cache_path = CACHE_DIR / fn
    if cache_path.exists() and cache_path.stat().st_size > 500:
        return True
    r = subprocess.run(['curl','-s','-o',str(cache_path),'-w','%{http_code}','-L','--max-time','15',url],
                       capture_output=True, text=True, timeout=25)
    ok = r.stdout.strip()=='200' and cache_path.exists() and cache_path.stat().st_size>500
    if not ok and cache_path.exists(): cache_path.unlink()
    return ok


def main():
    print('='*60)
    print('Add 122 Missing Items + Crawl + Download Images')
    print('='*60)

    with open(DATA_PATH,'r',encoding='utf-8') as f: data = json.load(f)
    existing = {i['id'] for i in data['items']}
    items = data['items']

    # Filter to truly missing
    to_add = [(iid,zh,cat,sub) for iid,zh,cat,sub in NEW_ITEMS if iid not in existing]
    print(f'\nAdding {len(to_add)} new items')

    added = []
    for iid, zh, cat, sub in to_add:
        item = {
            'id': iid,
            'name_zh': zh,
            'name_en': iid.replace('_',' ').title(),
            'category': cat,
            'subcategory': sub,
            'icon_url': f'images/{iid}.png',
            'acquisition': {'methods': ['未知'],'natural_generation':[],'smelting':[],'trading':None,'drops_from':[]},
            'crafting': [],
            'stonecutting': None, 'smithing': None, 'related_items': [],
            'source': 'rule_generated',
            'tags': assign_tags(iid, cat, sub),
        }
        items.append(item)
        added.append(iid)

    print(f'  Added: {len(added)}')

    # Crawl wiki pages
    print(f'\nCrawling wiki pages (est. {len(added)*1.5//60}min)...')
    crawl_ok = 0
    for i, iid in enumerate(added):
        if crawl_wiki(iid): crawl_ok += 1
        if (i+1)%30==0: print(f'  [{i+1}/{len(added)}] ok={crawl_ok}')
        time.sleep(1.5)
    print(f'  Crawled: {crawl_ok}/{len(added)}')

    # Download images
    print(f'\nDownloading images (est. {len(added)*0.5//60}min)...')
    img_ok = 0
    for i, iid in enumerate(added):
        if download_image(iid): img_ok += 1
        if (i+1)%30==0: print(f'  [{i+1}/{len(added)}] img={img_ok}')
        time.sleep(0.5)
    print(f'  Images: {img_ok}/{len(added)}')

    # Update icon_url for items that got images
    for item in items:
        iid = item['id']
        dest = IMAGES_DIR / f'{iid}.png'
        if dest.exists() and is_valid_image(dest):
            item['icon_url'] = f'images/{iid}.png'

    data['items'] = items
    data['meta']['total_items'] = len(items)

    # Rebuild categories
    cat_order = ['blocks','colored_blocks','functional_blocks','redstone','items','tools','combat','food','materials']
    cat_zh = {'blocks':'方块','colored_blocks':'彩色方块','functional_blocks':'功能方块','redstone':'红石','items':'物品','tools':'工具','combat':'战斗','food':'食物','materials':'材料'}
    cat_icons = {'blocks':'stone','colored_blocks':'white_wool','functional_blocks':'crafting_table','redstone':'redstone','items':'stick','tools':'iron_pickaxe','combat':'iron_sword','food':'bread','materials':'iron_ingot'}

    cat_map = {}
    for item in items:
        cat_map.setdefault(item['category'],{}).setdefault(item['subcategory'],[]).append(item['id'])

    new_cats = []
    for cid in cat_order:
        if cid not in cat_map: continue
        subs = []
        for sid in sorted(cat_map[cid].keys()):
            cat_map[cid][sid].sort()
            subs.append({'id':sid,'name_zh':sid,'name_en':sid.replace('_',' ').title(),'items':cat_map[cid][sid]})
        new_cats.append({'id':cid,'name_zh':cat_zh[cid],'name_en':cid.replace('_',' ').title(),'icon_item':cat_icons.get(cid,''),'subcategories':subs})
    data['categories'] = new_cats

    with open(DATA_PATH,'w',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    # Stats
    cats = Counter(i['category'] for i in items)
    imgs = len([f for f in os.listdir(IMAGES_DIR) if is_valid_image(IMAGES_DIR/f)])
    with_img = sum(1 for i in items if (IMAGES_DIR/f'{i["id"]}.png').exists() and is_valid_image(IMAGES_DIR/f'{i["id"]}.png'))

    print(f'\n=== Done ===')
    print(f'Total items: {len(items)}')
    print(f'Images on disk: {imgs}')
    print(f'With image: {with_img}')
    for c in cat_order:
        if c in cats: print(f'  {cat_zh.get(c,c)}: {cats[c]}')
    print(f'data.json: {os.path.getsize(DATA_PATH)/1024:.0f} KB')


if __name__ == '__main__':
    main()
