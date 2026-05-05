#!/usr/bin/env python3
"""
ai_classify_v4.py — 按 agent_prompt_v4.md 规格使用 DeepSeek API 智能分类
支持：10大类/45小类、多分类secondary_categories、hard rulings、hidden标记
"""
import json, os, sys, time, re
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / 'docs' / 'data' / 'data.json'
CACHE_PATH = SCRIPT_DIR / 'ai_classify_v4_cache.json'

API_KEY = ""
API_URL = "https://api.deepseek.com/v1/chat/completions"

BATCH_SIZE = 80  # items per API call

SYSTEM_PROMPT = """你是Minecraft物品分类器。必须严格使用以下分类体系：

大类 building_blocks 的小类: stone, wood, bricks, ore, metal, sand, dirt, ice, glass, end, nether, ocean, other_building
大类 colored_blocks 的小类: wool, carpet, concrete, concrete_powder, terracotta, glazed_terracotta, stained_glass, stained_glass_pane, bed, candle, shulker_box, banner
大类 natural_blocks 的小类: vegetation, leaves, sapling, mushroom, flower, crop, wood_natural, natural_other
大类 functional_blocks 的小类: workstation, storage, enchanting, light, door_trapdoor, rail, utility, technical
大类 redstone 的小类: power, transmission, action, minecart, door_redstone
大类 tools 的小类: pickaxe, axe, shovel, hoe, fishing, utility_tool, ranged
大类 combat 的小类: sword, axe_combat, helmet, chestplate, leggings, boots, shield, horse_armor
大类 food 的小类: meat, fish, crop_food, effect_food, drink, ingredient_food
大类 materials 的小类: ingot, gem, dye, mineral, mob_drop, craft_material, spawn_egg, music_disc, other_material
大类 miscellaneous 的小类: banner_pattern_item, pottery_sherd_item, smithing_template, music_disc_item, boat, minecart_item, painting, item_frame, pot, armor_stand, hidden_misc

=== 分类规则 ===
1. 功能优先：按主要功能分类，而非材质或外观
2. 食物独立：所有可食用物品归 food，不归 natural_blocks。食材(如brown_mushroom, red_mushroom, nether_wart, cocoa_beans, wheat, wheat_seeds及所有seeds)归 food/ingredient_food
3. 红石独立：所有红石元件归 redstone 大类
4. 彩色方块独立：所有16色变体（羊毛/地毯/混凝土/混凝土粉末/陶瓦/带釉陶瓦/染色玻璃/染色玻璃板/床/蜡烛/潜影盒）归 colored_blocks，无论颜色前缀是否存在
5. 木材制品统一：原木/木板/楼梯/台阶/栅栏/门/活板门/按钮/压力板/告示牌/船 → building_blocks/wood 或 natural_blocks/wood_natural（去皮/原木/木头→natural_blocks/wood_natural；加工木板/台阶/楼梯/栅栏等→building_blocks/wood）
6. 材质工具→tools/{工具类型}，材质武器→combat/sword
7. 骨粉(bone_meal)→materials/dye；可可豆(cocoa_beans)→materials/dye 且 secondary_categories: ["food"]
8. 所有矿石(coal_ore, iron_ore, *_ore, ancient_debris) → natural_blocks（矿石是自然方块），secondary_categories: ["materials"]
9. 龙蛋(dragon_egg)→natural_blocks/natural_other，NOT hidden
10. 所有树的树叶→natural_blocks/leaves；所有树苗→natural_blocks/sapling；所有去皮原木/木头→natural_blocks/wood_natural
11. 所有食物（可食用物品）→ food；所有农作物(小麦/wheat, 胡萝卜/carrot, 马铃薯/potato, 甜菜根/beetroot) → food/crop_food
12. spawn_egg→materials/spawn_egg；music_disc→materials/music_disc

=== 硬性裁决（以下物品必须精确按此归类，禁止自由裁量）===
shulker_box（无颜色shulker_box）   → functional_blocks / storage      次: colored_blocks
所有16色shulker_box(*_shulker_box) → colored_blocks / shulker_box    次: functional_blocks
redstone_lamp                       → redstone / action                次: functional_blocks
rail                                → functional_blocks / rail
powered_rail                        → functional_blocks / rail         次: redstone
detector_rail                       → functional_blocks / rail         次: redstone
activator_rail                      → functional_blocks / rail         次: redstone
iron_door                           → functional_blocks / door_trapdoor 次: redstone
iron_trapdoor                       → functional_blocks / door_trapdoor 次: redstone
glowstone                           → building_blocks / nether         次: functional_blocks
sea_lantern                         → building_blocks / ocean          次: functional_blocks
jack_o_lantern                      → building_blocks / other_building 次: functional_blocks
note_block                          → redstone / action                次: functional_blocks
bell                                → redstone / action                次: functional_blocks
bone_meal                           → materials / dye
cocoa_beans                         → materials / dye                  次: food
dragon_egg                          → natural_blocks / natural_other
minecart系列(chest/furnace/hopper/tnt_minecart) → redstone / minecart 次: functional_blocks
minecart（普通）                     → redstone / minecart              次: functional_blocks
observer                            → redstone / power
piston / sticky_piston              → redstone / action                次: functional_blocks
dispenser / dropper / hopper        → redstone / action                次: functional_blocks
tnt                                → redstone / action                次: functional_blocks
lectern                             → functional_blocks / enchanting   次: redstone
trapped_chest                       → functional_blocks / storage      次: redstone
daylight_detector                   → redstone / power                 次: functional_blocks
target                              → redstone / power                 次: functional_blocks
sculk_sensor                        → redstone / action                次: natural_blocks
calibrated_sculk_sensor             → redstone / action                次: natural_blocks
enchanting_table                    → functional_blocks / enchanting
beacon                              → functional_blocks / light
conduit                             → functional_blocks / light
ender_chest                         → functional_blocks / storage
barrel                              → functional_blocks / storage
bundle及所有颜色bundle(*)           → functional_blocks / storage
jukebox                             → functional_blocks / utility
lodestone                           → functional_blocks / utility
respawn_anchor                      → functional_blocks / utility

=== 非实体/技术方块（标记 hidden: true）===
command_block, chain_command_block, repeating_command_block
structure_block, structure_void, barrier, light_block, jigsaw_block
spawner, trial_spawner, vault
knowledge_book, debug_stick
grass_carried, mysterious_frame_slot
air, bubble_column

=== 输出格式 ===
对每个物品返回：
{"id":"物品ID","category":"大类","subcategory":"小类","secondary_categories":["次大类1","次大类2"],"hidden":false}
只返回JSON数组，不要任何解释。"""

def load_items():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data, data['items']

def load_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def classify_batch(batch_items, batch_num, total_batches):
    """Call DeepSeek API to classify a batch of items."""
    # Build item descriptions
    item_descs = []
    for item in batch_items:
        desc = f"id={item['id']}, name_en=\"{item.get('name_en','')}\", name_zh=\"{item.get('name_zh','')}\", current_cat={item.get('category','')}"
        if item.get('crafting'):
            desc += ", has_crafting=true"
        # Add hint about current category
        item_descs.append(desc)

    user_prompt = "请分类以下Minecraft物品：\n" + "\n".join(item_descs)

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 8192
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            content = result['choices'][0]['message']['content']

            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                classified = json.loads(json_match.group())
                print(f"  批次 {batch_num}/{total_batches}: {len(classified)}/{len(batch_items)} 个分类成功")
                return classified
            else:
                print(f"  批次 {batch_num}: 无法从响应中提取JSON，重试...")
                if attempt < max_retries - 1:
                    time.sleep(2)

        except Exception as e:
            print(f"  批次 {batch_num}: API错误 {e}，重试 {attempt+1}/{max_retries}...")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))

    print(f"  批次 {batch_num}: 全部重试失败！")
    return []

def main():
    print("=" * 60)
    print("AI Classify V4 — 按 agent_prompt_v4.md 规格分类")
    print("=" * 60)

    # Load
    data, items = load_items()
    total = len(items)
    print(f"物品总数: {total}")

    # Load cache
    cache = load_cache()
    cached_ids = set(cache.keys())
    print(f"已有缓存: {len(cached_ids)} 个物品")

    # Find uncached items
    uncached = [i for i in items if i['id'] not in cached_ids]
    print(f"待分类: {len(uncached)} 个物品")

    if not uncached:
        print("全部物品已缓存，跳过API调用。")
    else:
        # Batch processing
        batches = [uncached[i:i+BATCH_SIZE] for i in range(0, len(uncached), BATCH_SIZE)]
        total_batches = len(batches)
        print(f"分批: {total_batches} 批 (每批{BATCH_SIZE}个)")

        for i, batch in enumerate(batches, 1):
            print(f"\n[批次 {i}/{total_batches}] {len(batch)} 个物品...")

            results = classify_batch(batch, i, total_batches)

            # Save to cache
            for r in results:
                iid = r.get('id')
                if iid:
                    cache[iid] = {
                        'category': r.get('category', 'miscellaneous'),
                        'subcategory': r.get('subcategory', 'general'),
                        'secondary_categories': r.get('secondary_categories', []),
                        'hidden': r.get('hidden', False),
                    }

            save_cache(cache)
            print(f"  缓存已更新: {len(cache)} 个物品")

            if i < total_batches:
                time.sleep(2)  # Rate limiting

    # Apply results
    print(f"\n{'='*60}")
    print("应用分类结果...")

    applied = 0
    hidden_count = 0
    secondary_count = 0

    for item in items:
        iid = item['id']
        if iid in cache:
            cc = cache[iid]
            item['category'] = cc['category']
            item['subcategory'] = cc['subcategory']
            item['secondary_categories'] = cc.get('secondary_categories', [])
            item['hidden'] = cc.get('hidden', False)
            if item['hidden']:
                hidden_count += 1
            if item['secondary_categories']:
                secondary_count += 1
            applied += 1

    print(f"分类已应用: {applied}/{total}")
    print(f"标记hidden: {hidden_count}")
    print(f"有secondary_categories: {secondary_count}")

    # Fix zh_fallback flag
    zh_fallback_count = 0
    for item in items:
        if item.get('name_zh') == item.get('name_en') or not item.get('name_zh'):
            item['zh_fallback'] = True
            zh_fallback_count += 1
        else:
            item['zh_fallback'] = False
    print(f"zh_fallback标记: {zh_fallback_count}")

    # Apply T5 known fixes
    T5_FIXES = {
        'dragon_egg': '龙蛋',
        'eyeblossom': '眼眸花',
        'bamboo_stripped_log': '去皮竹原木',
        'cherry_stripped_log': '去皮樱花木原木',
        'golden_dandelion': '金色蒲公英',
        'dirt_path': '泥土小径',
        'purpur_stairs': '紫珀楼梯',
        'end_portal_frame': '末地传送门框架',
        'decorated_pot': '纹饰陶罐',
        'detector_rail': '探测铁轨',
        'powered_rail': '动力铁轨',
        'rail': '铁轨',
        'activator_rail': '激活铁轨',
    }
    t5_fixed = 0
    for item in items:
        iid = item['id']
        if iid in T5_FIXES:
            item['name_zh'] = T5_FIXES[iid]
            item['zh_fallback'] = False
            t5_fixed += 1
    print(f"T5已知修正: {t5_fixed}")

    # Update data
    data['items'] = items
    data['meta']['total_items'] = len(items)
    data['meta']['generated_at'] = '2026-05-05-v4'

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Category stats
    cats = Counter(i['category'] for i in items)
    print(f"\n大类分布:")
    for k, v in cats.most_common():
        print(f"  {k}: {v}")

    print(f"\ndata.json已更新 ({len(items)} 物品)")
    print(f"缓存: {len(cache)} 条")
    print("Phase 2 完成。")

if __name__ == '__main__':
    import requests
    main()
