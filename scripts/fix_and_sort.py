#!/usr/bin/env python3
"""
fix_and_sort.py — 翻译修正 + 脏数据清洗 + 分类修正 + 规则排序
"""
import json, os, re, time
import requests
from collections import Counter

API_KEY = "sk-75d38daa88e64e6697285ed5d68f62bf"
API_URL = "https://api.deepseek.com/v1/chat/completions"

# ============================================================
# 1. 已知翻译修正表
# ============================================================
ZH_FIXES = {
    # 用户指出的错误翻译
    'cinnabar_brick_slab': '朱砂砖台阶',
    'cinnabar_brick_stairs': '朱砂砖楼梯',
    'cinnabar_brick_wall': '朱砂砖墙',
    'cinnabar_bricks': '朱砂砖',
    'mud_brick_slab': '泥砖台阶',
    'mud_brick_stairs': '泥砖楼梯',
    'mud_brick_wall': '泥砖墙',
    'tuff_brick_slab': '凝灰岩砖台阶',
    'tuff_brick_stairs': '凝灰岩砖楼梯',
    'tuff_brick_wall': '凝灰岩砖墙',
    'dirt_path': '土径',
    'copper_torch': '铜火把',
    'copper_lantern': '铜灯笼',
    'glow_stick': '荧光棒',
    'leather_cap': '皮革帽子',
    'leather_tunic': '皮革外套',
    'sulfur_brick_slab': '硫磺砖台阶',
    'sulfur_brick_stairs': '硫磺砖楼梯',
    'sulfur_brick_wall': '硫磺砖墙',
    'sulfur_bricks': '硫磺砖',
    'bucket_of_sulfur_cube': '硫磺立方体桶',
    'hardened_stained_glass_pane': '硬化染色玻璃板',
    'hardened_stained_glass': '硬化染色玻璃',
    'hardened_glass': '硬化玻璃',
    # Heads
    'creeper_head': '苦力怕的头',
    'skeleton_skull': '骷髅头颅',
    'wither_skeleton_skull': '凋零骷髅头颅',
    'zombie_head': '僵尸的头',
    'dragon_head': '龙首',
    'piglin_head': '猪灵的头',
    # Copper oxidized
    'exposed_copper': '斑驳的铜块',
    'weathered_copper': '锈蚀的铜块',
    'oxidized_copper': '氧化的铜块',
    'exposed_cut_copper': '斑驳的切制铜块',
    'weathered_cut_copper': '锈蚀的切制铜块',
    'oxidized_cut_copper': '氧化的切制铜块',
    'exposed_chiseled_copper': '斑驳的錾制铜块',
    'weathered_chiseled_copper': '锈蚀的錾制铜块',
    'oxidized_chiseled_copper': '氧化的錾制铜块',
    'exposed_copper_grate': '斑驳的铜格栅',
    'weathered_copper_grate': '锈蚀的铜格栅',
    'oxidized_copper_grate': '氧化的铜格栅',
    'exposed_copper_door': '斑驳的铜门',
    'weathered_copper_door': '锈蚀的铜门',
    'oxidized_copper_door': '氧化的铜门',
    'exposed_copper_trapdoor': '斑驳的铜活板门',
    'weathered_copper_trapdoor': '锈蚀的铜活板门',
    'oxidized_copper_trapdoor': '氧化的铜活板门',
    'exposed_copper_bulb': '斑驳的铜灯',
    'weathered_copper_bulb': '锈蚀的铜灯',
    'oxidized_copper_bulb': '氧化的铜灯',
}

# ============================================================
# 2. 脏数据列表 — 直接删除
# ============================================================
DIRTY_IDS = [
    'slowness', 'water_breathing', 'item', 'block', 'armor', 'weapon',
    'chestplate', 'stripped_log', 'stripped_wood',
]

# ============================================================
# 3. 分类修正表
# ============================================================
CAT_FIXES = {
    # Copper variants → blocks/metal
    'exposed_copper': ('blocks', 'metal'), 'weathered_copper': ('blocks', 'metal'), 'oxidized_copper': ('blocks', 'metal'),
    'exposed_cut_copper': ('blocks', 'metal'), 'weathered_cut_copper': ('blocks', 'metal'), 'oxidized_cut_copper': ('blocks', 'metal'),
    'exposed_chiseled_copper': ('blocks', 'metal'), 'weathered_chiseled_copper': ('blocks', 'metal'), 'oxidized_chiseled_copper': ('blocks', 'metal'),
    # Copper grate/door/trapdoor → functional_blocks
    'copper_grate': ('functional_blocks', 'door'), 'exposed_copper_grate': ('functional_blocks', 'door'),
    'weathered_copper_grate': ('functional_blocks', 'door'), 'oxidized_copper_grate': ('functional_blocks', 'door'),
    'copper_door': ('functional_blocks', 'door'), 'exposed_copper_door': ('functional_blocks', 'door'),
    'weathered_copper_door': ('functional_blocks', 'door'), 'oxidized_copper_door': ('functional_blocks', 'door'),
    'copper_trapdoor': ('functional_blocks', 'door'), 'exposed_copper_trapdoor': ('functional_blocks', 'door'),
    'weathered_copper_trapdoor': ('functional_blocks', 'door'), 'oxidized_copper_trapdoor': ('functional_blocks', 'door'),
    'copper_bulb': ('functional_blocks', 'light'), 'exposed_copper_bulb': ('functional_blocks', 'light'),
    'weathered_copper_bulb': ('functional_blocks', 'light'), 'oxidized_copper_bulb': ('functional_blocks', 'light'),
    # Heads → blocks/other_blocks
    'creeper_head': ('blocks', 'other_blocks'), 'skeleton_skull': ('blocks', 'other_blocks'),
    'wither_skeleton_skull': ('blocks', 'other_blocks'), 'zombie_head': ('blocks', 'other_blocks'),
    'dragon_head': ('blocks', 'other_blocks'), 'piglin_head': ('blocks', 'other_blocks'),
    # Banners → blocks/other_blocks
    'white_banner': ('blocks', 'other_blocks'), 'orange_banner': ('blocks', 'other_blocks'),
    'magenta_banner': ('blocks', 'other_blocks'), 'light_blue_banner': ('blocks', 'other_blocks'),
    'yellow_banner': ('blocks', 'other_blocks'), 'lime_banner': ('blocks', 'other_blocks'),
    'pink_banner': ('blocks', 'other_blocks'), 'gray_banner': ('blocks', 'other_blocks'),
    'light_gray_banner': ('blocks', 'other_blocks'), 'cyan_banner': ('blocks', 'other_blocks'),
    'purple_banner': ('blocks', 'other_blocks'), 'blue_banner': ('blocks', 'other_blocks'),
    'brown_banner': ('blocks', 'other_blocks'), 'green_banner': ('blocks', 'other_blocks'),
    'red_banner': ('blocks', 'other_blocks'), 'black_banner': ('blocks', 'other_blocks'),
    'banner': ('blocks', 'other_blocks'),
    # Hardened glass → blocks/other_blocks
    'hardened_stained_glass': ('blocks', 'other_blocks'),
    'hardened_stained_glass_pane': ('blocks', 'other_blocks'),
    'hardened_glass': ('blocks', 'other_blocks'),
}

# ============================================================
# 4. 排序规则
# ============================================================

CAT_ORDER = ['blocks','colored_blocks','functional_blocks','redstone','items','tools','combat','food','materials']

SUB_ORDER = {
    'blocks': ['wood','stone','bricks','dirt','sand','ore','metal','ice','flora','magnetic','other_blocks'],
    'colored_blocks': ['wool','carpet','bed','concrete','terracotta','stained_glass','candle','shulker_box'],
    'functional_blocks': ['storage','workstation','enchanting','light','door','rail'],
    'redstone': ['power','transmission','action','sound'],
    'items': ['dye','potion','spawn_egg','enchanted_book','disc','pottery_sherd','banner_pattern','transport','misc'],
    'tools': ['pickaxe','axe','shovel','hoe','ranged','utility'],
    'combat': ['sword','shield','helmet','chestplate','leggings','boots'],
    'food': ['meat','fish','crop','effect_food'],
    'materials': ['ingot','gem','fiber','nether','other_material'],
}

COLOR_ORDER = ['white','orange','magenta','light_blue','yellow','lime','pink','gray','light_gray','cyan','purple','blue','brown','green','red','black']
WOOD_ORDER = ['oak','spruce','birch','jungle','acacia','dark_oak','mangrove','cherry','bamboo','crimson','warped','pale_oak']
METAL_ORDER = ['iron','copper','exposed_copper','weathered_copper','oxidized_copper','gold','golden','diamond','netherite']
FORM_ORDER = ['log','stripped_log','wood','stripped_wood','planks','slab','stairs','wall','fence','fence_gate','door','trapdoor','button','pressure_plate','sign','hanging_sign']

def sort_key(item):
    iid = item['id']
    c = item.get('category','zzz')
    s = item.get('subcategory','')

    ci = CAT_ORDER.index(c) if c in CAT_ORDER else 99
    si = SUB_ORDER.get(c, []).index(s) if s in SUB_ORDER.get(c, []) else 99

    # Color priority
    color_rank = 99
    for idx, color in enumerate(COLOR_ORDER):
        if iid.startswith(color + '_'):
            color_rank = idx
            break

    # Wood priority
    wood_rank = 99
    for idx, wood in enumerate(WOOD_ORDER):
        if iid.startswith(wood + '_'):
            wood_rank = idx
            break

    # Metal priority
    metal_rank = 99
    for idx, metal in enumerate(METAL_ORDER):
        if iid.startswith(metal + '_') or metal in iid:
            metal_rank = idx
            break

    # Form priority
    form_rank = 99
    for idx, form in enumerate(FORM_ORDER):
        if iid.endswith('_' + form) or iid.endswith('_' + form + 's'):
            form_rank = idx
            break

    return (ci, si, color_rank, wood_rank, metal_rank, form_rank, iid)


# ============================================================
# 5. AI 批量翻译英文名
# ============================================================
def translate_batch(items_batch):
    """Send batch to DeepSeek for Chinese translation."""
    item_list = []
    for item in items_batch:
        item_list.append({
            "id": item['id'],
            "name_en": item.get('name_en', ''),
        })

    prompt = "请将以下Minecraft物品英文名翻译为官方简体中文。只返回JSON数组，格式: [{\"id\":\"...\",\"name_zh\":\"...\"}]\n" + json.dumps(item_list, ensure_ascii=False)

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是Minecraft中文Wiki翻译专家。必须使用官方简体中文译名。\n规则: oak=橡木, spruce=云杉木, birch=白桦木, jungle=丛林木, acacia=金合欢木, dark_oak=深色橡木, mangrove=红树木, cherry=樱花木, bamboo=竹\n copper→铜, exposed→斑驳的, weathered→锈蚀的, oxidized→氧化的\n slab→台阶, stairs→楼梯, wall→墙, fence→栅栏, fence_gate→栅栏门\n planks→木板, log→原木, stripped_log→去皮原木\n brick/bricks→砖, tile/tiles→砖\n polished→磨制, chiseled→錾制, cracked→裂纹, mossy→苔\n ingot→锭, nugget→粒, ore→矿石, block→块\n只返回JSON数组，不要任何解释。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 4096,
    }

    for attempt in range(3):
        try:
            resp = requests.post(API_URL,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json=payload, timeout=60)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                if content.startswith("```"): content = content.split("\n", 1)[1].rstrip("`")
                try:
                    return json.loads(content)
                except:
                    m = re.search(r'\[.*\]', content, re.DOTALL)
                    if m: return json.loads(m.group(0))
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            print(f"  API error: {e}")
            time.sleep(3)
    return []


def main():
    print("=" * 60)
    print("Fix & Sort: 翻译修正 + 清洗 + 排序")
    print("=" * 60)

    with open('docs/data/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']
    print(f"\n[1] 加载 {len(items)} 项")

    # Step 1: Remove dirty data
    removed_ids = set(DIRTY_IDS)
    items = [i for i in items if i['id'] not in removed_ids]
    print(f"[2] 删除脏数据 {len(removed_ids)} 项: {', '.join(DIRTY_IDS)}")

    # Step 2: Apply known fixes
    fix_count = 0
    cat_fix_count = 0
    for item in items:
        iid = item['id']
        if iid in ZH_FIXES:
            old = item.get('name_zh','')
            item['name_zh'] = ZH_FIXES[iid]
            if old != ZH_FIXES[iid]:
                fix_count += 1
        if iid in CAT_FIXES:
            item['category'], item['subcategory'] = CAT_FIXES[iid]
            cat_fix_count += 1
    print(f"[3] 已知翻译修正: {fix_count} 项")
    print(f"[4] 分类修正: {cat_fix_count} 项")

    # Step 3: AI translate remaining English names
    en_only = [i for i in items if i.get('name_zh','') == i.get('name_en','') or not i.get('name_zh')]
    # Exclude items already in ZH_FIXES
    en_only = [i for i in en_only if i['id'] not in ZH_FIXES]
    print(f"[5] 英文名待翻译: {len(en_only)} 项")

    if en_only:
        BATCH = 30
        translated = {}
        for bi in range(0, len(en_only), BATCH):
            batch = en_only[bi:bi+BATCH]
            result = translate_batch(batch)
            if result:
                for entry in result:
                    if isinstance(entry, dict) and 'id' in entry and 'name_zh' in entry:
                        translated[entry['id']] = entry['name_zh']
            print(f"  批次 {bi//BATCH + 1}: 翻译 {len(result) if result else 0} 项")
            time.sleep(0.8)

        trans_count = 0
        for item in items:
            if item['id'] in translated:
                item['name_zh'] = translated[item['id']]
                trans_count += 1
        print(f"  AI翻译完成: {trans_count} 项")

    # Step 4: Sort
    print(f"[6] 排序...")
    items.sort(key=sort_key)

    # Step 5: Rebuild categories
    cat_map = {}
    for item in items:
        c, s = item['category'], item['subcategory']
        cat_map.setdefault(c, {}).setdefault(s, []).append(item['id'])

    new_cats = []
    for cid in CAT_ORDER:
        if cid in cat_map:
            cat_data = cat_map[cid]
            sub_order = SUB_ORDER.get(cid, list(cat_data.keys()))
            subs = []
            for sid in sub_order:
                if sid in cat_data:
                    cat_data[sid].sort(key=lambda x: sort_key(next(i for i in items if i['id']==x)))
                    SUB_ZH_DICT = {
                        'wood':'木材','stone':'石类','bricks':'砖类','dirt':'泥土','sand':'沙子',
                        'ore':'矿石','metal':'金属','ice':'冰雪','flora':'植物','magnetic':'磁性',
                        'other_blocks':'其他方块','wool':'羊毛','carpet':'地毯','bed':'床',
                        'concrete':'混凝土','terracotta':'陶瓦','stained_glass':'染色玻璃',
                        'candle':'蜡烛','shulker_box':'潜影盒','storage':'存储','workstation':'工作台',
                        'enchanting':'附魔','light':'照明','door':'门窗栅栏','rail':'交通',
                        'power':'电源','transmission':'传导','action':'执行','sound':'声音',
                        'dye':'染料','potion':'药水','spawn_egg':'刷怪蛋','enchanted_book':'附魔书',
                        'disc':'音乐唱片','pottery_sherd':'陶片','banner_pattern':'旗帜图案',
                        'transport':'交通','misc':'杂项','pickaxe':'镐','axe':'斧','shovel':'锹',
                        'hoe':'锄','ranged':'远程','utility':'实用','sword':'剑','shield':'盾牌',
                        'helmet':'头盔','chestplate':'胸甲','leggings':'护腿','boots':'靴子',
                        'meat':'肉类','fish':'鱼类','crop':'农作物','effect_food':'特效食物',
                        'ingot':'锭','gem':'宝石','fiber':'纤维','nether':'下界材料',
                        'other_material':'其他材料',
                    }
                    subs.append({
                        'id': sid, 'name_zh': SUB_ZH_DICT.get(sid, sid), 'name_en': sid.replace('_',' ').title(),
                        'items': cat_data[sid],
                    })
            # Add any remaining subs not in predefined order
            for sid in sorted(cat_data.keys()):
                if sid not in sub_order:
                    SUB_ZH_DICT = {
                        'wood':'木材','stone':'石类','bricks':'砖类','dirt':'泥土','sand':'沙子',
                        'ore':'矿石','metal':'金属','ice':'冰雪','flora':'植物','magnetic':'磁性',
                        'other_blocks':'其他方块','wool':'羊毛','carpet':'地毯','bed':'床',
                        'concrete':'混凝土','terracotta':'陶瓦','stained_glass':'染色玻璃',
                        'candle':'蜡烛','shulker_box':'潜影盒','storage':'存储','workstation':'工作台',
                        'enchanting':'附魔','light':'照明','door':'门窗栅栏','rail':'交通',
                        'power':'电源','transmission':'传导','action':'执行','sound':'声音',
                        'dye':'染料','potion':'药水','spawn_egg':'刷怪蛋','enchanted_book':'附魔书',
                        'disc':'音乐唱片','pottery_sherd':'陶片','banner_pattern':'旗帜图案',
                        'transport':'交通','misc':'杂项','pickaxe':'镐','axe':'斧','shovel':'锹',
                        'hoe':'锄','ranged':'远程','utility':'实用','sword':'剑','shield':'盾牌',
                        'helmet':'头盔','chestplate':'胸甲','leggings':'护腿','boots':'靴子',
                        'meat':'肉类','fish':'鱼类','crop':'农作物','effect_food':'特效食物',
                        'ingot':'锭','gem':'宝石','fiber':'纤维','nether':'下界材料',
                        'other_material':'其他材料',
                    }
                    subs.append({
                        'id': sid, 'name_zh': SUB_ZH_DICT.get(sid, sid), 'name_en': sid.replace('_',' ').title(),
                        'items': cat_data[sid],
                    })
            new_cats.append({
                'id': cid,
                'name_zh': {'blocks':'方块','colored_blocks':'彩色方块','functional_blocks':'功能方块','redstone':'红石','items':'物品','tools':'工具','combat':'战斗','food':'食物','materials':'材料'}[cid],
                'name_en': cid.replace('_',' ').title(),
                'icon_item': subs[0]['items'][0] if subs and subs[0]['items'] else '',
                'subcategories': subs,
            })

    data['items'] = items
    data['categories'] = new_cats
    data['meta']['total_items'] = len(items)
    data['meta']['generated_at'] = '2026-05-04'

    with open('docs/data/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    # Stats
    cats = Counter(i['category'] for i in items)
    print(f"\n=== 完成 ===")
    print(f"物品: {len(items)}")
    for cid in CAT_ORDER:
        if cid in cats:
            print(f"  {cid}: {cats[cid]}")
    print(f"文件: {os.path.getsize('docs/data/data.json')/1024:.0f} KB")


if __name__ == '__main__':
    main()
