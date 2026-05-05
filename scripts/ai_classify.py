#!/usr/bin/env python3
"""
ai_classify.py — 使用 DeepSeek API 对所有物品进行智能分类
分类体系：9大类 + 38小类（Minecraft 物品百科专用）
"""
import json
import os
import sys
import time
import requests
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / 'docs' / 'data' / 'data.json'

API_KEY = ""
API_URL = "https://api.deepseek.com/v1/chat/completions"

CATEGORY_SYSTEM = """
请将以下 Minecraft 物品分类到最合适的子类别中。分类体系如下：

📦 blocks (方块)
  - stone (石类): 石头、圆石、花岗岩、闪长岩、安山岩、砂岩、黑石、玄武岩、深板岩、凝灰岩、方解石、滴水石、紫水晶块等天然石类方块及其磨制/切制/錾制/楼梯/台阶/墙变体
  - wood (木材): 橡木/云杉/白桦/丛林/金合欢/深色橡木/红树/樱花/竹/绯红/诡异木的原木、去皮原木、木头、去皮木头、木板、楼梯、台阶、栅栏、栅栏门、活板门、按钮、压力板、告示牌、悬挂式告示牌、竹马赛克等
  - bricks (砖类): 红砖、石砖、下界砖、红色下界砖、泥砖、深板岩砖、凝灰岩砖、裂纹/錾制/苔石变体及其楼梯/台阶/墙
  - ore (矿石): 煤矿、铁矿、金矿、钻石矿、绿宝石矿、红石矿、青金石矿、铜矿、下界石英矿、下界金矿、远古残骸、深板岩矿石变体、粗铁/粗铜/粗金块
  - metal (金属): 铁块、金块、铜块、钻石块、绿宝石块、下界合金块、青金石块、红石块、煤炭块、石英块、切制铜/斑驳/锈蚀/氧化变体及其楼梯/台阶、铜格栅、铜门、铜活板门、铜灯
  - dirt (泥土): 泥土、砂土、灰化土、菌丝、缠根泥土、泥巴、泥坯、草方块、菌丝体
  - flora (植物): 草、树叶、树苗、蘑菇、菌类、花、藤蔓、苔藓、杜鹃花丛、孢子花、垂滴叶、仙人掌、甘蔗、竹子、海带、睡莲
  - ice (冰雪): 冰、浮冰、蓝冰、雪块、雪
  - sand (沙子): 沙子、红沙、沙砾、砂岩/红砂岩及其切制/錾制/平滑/楼梯/台阶/墙
  - magnetic (磁性): 磁石、避雷针
  - other_blocks (其他): 玻璃、玻璃板、黑曜石、哭泣黑曜石、海晶石/海晶石砖/暗海晶石及其楼梯/台阶/墙、海晶灯、末地石、末地石砖、紫珀块/紫珀柱及其楼梯/台阶、骨块、蜘蛛网、黏液块、蜂蜜块

📦 colored_blocks (彩色方块)
  - wool (羊毛): 所有16色羊毛
  - carpet (地毯): 所有16色地毯
  - concrete (混凝土): 所有16色混凝土及混凝土粉末
  - terracotta (陶瓦): 所有16色陶瓦及带釉陶瓦
  - stained_glass (染色玻璃): 所有16色染色玻璃及染色玻璃板
  - bed (床): 所有16色床
  - candle (蜡烛): 所有16色蜡烛
  - shulker_box (潜影盒): 所有16色潜影盒

📦 functional_blocks (功能方块)
  - storage (存储): 箱子、陷阱箱、末影箱、木桶、收纳袋(所有颜色)
  - workstation (工作台): 工作台、熔炉、高炉、烟熏炉、锻造台、切石机、织布机、制图台、制箭台、砂轮、铁砧(含开裂/损坏)、堆肥桶
  - enchanting (附魔): 附魔台、书架、讲台
  - light (照明): 火把、灵魂火把、灯笼、灵魂灯笼、营火、灵魂营火、末地烛、信标、潮涌核心、蛙明灯(所有颜色)
  - door (门窗栅栏): 铁门、铁活板门
  - rail (交通): 铁轨、动力铁轨、探测铁轨、激活铁轨

📦 redstone (红石)
  - power (电源): 红石块、红石火把、按钮(所有木材)、压力板(所有木材)、测重压力板、拉杆、阳光探测器、绊线钩
  - transmission (传导): 红石粉、红石中继器、红石比较器、侦测器
  - action (执行): 活塞、黏性活塞、发射器、投掷器、漏斗、TNT、红石灯、钟
  - sound (声音): 音符盒、唱片机、幽匿感测体、校频幽匿感测体

📦 items (物品)
  - dye (染料): 所有16色染料、骨粉、墨囊、荧光墨囊
  - potion (药水): 所有常规/喷溅/滞留药水、水瓶、粗制药水、平凡药水、浓稠药水、玻璃瓶、龙息
  - spawn_egg (刷怪蛋): 所有生物刷怪蛋
  - enchanted_book (附魔书): 所有附魔书
  - disc (音乐唱片): 所有音乐唱片
  - pottery_sherd (陶片): 所有陶片
  - banner_pattern (旗帜图案): 所有旗帜图案
  - transport (交通): 船、运输船、竹筏、矿车(含箱子/熔炉/漏斗/TNT矿车)
  - misc (杂项): 画、物品展示框、荧光物品展示框、花盆、饰纹陶罐、盔甲架、刷怪笼、龙蛋、试炼刷怪笼、宝库、合成器

📦 tools (工具)
  - pickaxe (镐): 木/石/铁/金/钻石/下界合金镐
  - axe (斧): 各材质斧
  - shovel (锹): 各材质锹
  - hoe (锄): 各材质锄
  - ranged (远程): 弓、弩、三叉戟、重锤、钓鱼竿、胡萝卜钓竿、诡异菌钓竿
  - utility (实用): 打火石、剪刀、指南针、追溯指针、钟、望远镜、刷子、拴绳、命名牌、鞍、烟花火箭

📦 combat (战斗)
  - sword (剑): 各材质剑
  - shield (盾牌): 盾牌、不死图腾
  - helmet (头盔): 皮革/锁链/铁/金/钻石/下界合金头盔、海龟壳
  - chestplate (胸甲): 各材质胸甲、鞘翅
  - leggings (护腿): 各材质护腿
  - boots (靴子): 各材质靴子

📦 food (食物)
  - meat (肉类): 生/熟牛肉、猪肉、羊肉、鸡肉、兔肉
  - fish (鱼类): 生/熟鳕鱼、生/熟鲑鱼、热带鱼、河豚
  - crop (农作物): 面包、曲奇、蛋糕、南瓜派、西瓜片、甜浆果、发光浆果、苹果、胡萝卜、马铃薯、烤马铃薯、甜菜根、甜菜汤、蘑菇煲、兔肉煲、干海带
  - effect_food (特效食物): 金苹果、附魔金苹果、金胡萝卜、紫颂果、爆裂紫颂果、迷之炖菜、蜂蜜瓶

📦 materials (材料)
  - ingot (锭): 铁锭、金锭、铜锭、下界合金锭、下界合金碎片(锭半成品)、铁粒、金粒
  - gem (宝石): 钻石、绿宝石、青金石、紫水晶碎片、回响碎片
  - fiber (纤维): 线、羽毛、皮革、兔子皮、兔子脚、幻翼膜、鳞甲、犰狳鳞甲、鹦鹉螺壳
  - nether (下界): 烈焰棒、烈焰粉、恶魂之泪、岩浆膏、下界之星、下界疣
  - other_material (其他材料): 木棍、碗、燧石、砖(物品)、下界砖(物品)、黏土球、纸、书、书与笔、成书、黏液球、蜜脾、糖、火药、末影珍珠、末影之眼、蜘蛛眼、发酵蛛眼、荧石粉、红石粉、海晶碎片、海晶砂粒、潜影壳、海洋之心、火焰弹、烟火之星、附魔之瓶、雪球、鸡蛋、小麦、小麦种子、南瓜种子、西瓜种子、甜菜种子、火把花种子、瓶子草荚果、可可豆、海带、山羊角、风弹、旋风棒、重质核心、不祥之瓶、试炼钥匙、不祥试炼钥匙
"""

SYSTEM_PROMPT = """你是Minecraft物品分类器。必须严格使用以下子类别名称（不许自创）：

大类 blocks: stone, wood, bricks, ore, metal, dirt, flora, ice, sand, magnetic, other_blocks
大类 colored_blocks: wool, carpet, concrete, terracotta, stained_glass, bed, candle, shulker_box
大类 functional_blocks: storage, workstation, enchanting, light, door, rail
大类 redstone: power, transmission, action, sound
大类 items: dye, potion, spawn_egg, enchanted_book, disc, pottery_sherd, banner_pattern, transport, misc
大类 tools: pickaxe, axe, shovel, hoe, ranged, utility
大类 combat: sword, shield, helmet, chestplate, leggings, boots
大类 food: meat, fish, crop, effect_food
大类 materials: ingot, gem, fiber, nether, other_material

规则：
- 所有16色羊毛/地毯/混凝土/粉末/陶瓦/带釉陶瓦/染色玻璃/玻璃板/床/蜡烛/潜影盒 → colored_blocks/对应子类
- 所有木材制品(原木/木板/楼梯/台阶/栅栏/栅栏门/活板门/门/按钮/压力板/告示牌/悬挂告示牌) → blocks/wood
- {材质}_{工具} → tools/{工具类型}，{材质}_{剑} → combat/sword
- 刷怪蛋 → items/spawn_egg，药水 → items/potion，附魔书 → items/enchanted_book
- 生/熟肉鱼 → food/meat或food/fish

对每个物品返回: {"id":"..","category":"..","subcategory":".."}
只返回JSON数组，不要解释。"""


def classify_batch(items_batch):
    """Send a batch of items to DeepSeek API for classification."""
    item_list = "\n".join(
        f"  {{'id': '{item['id']}', 'name_zh': '{item.get('name_zh', '')}', 'name_en': '{item.get('name_en', '')}'}}"
        for item in items_batch
    )

    user_prompt = f"请分类以下 Minecraft 物品，只返回 JSON 数组：\n[{item_list}\n]"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 4096,
    }

    for attempt in range(3):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                # Extract JSON array from response
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1]
                    if content.endswith("```"):
                        content = content[:-3]
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Try to find JSON array in the response
                    import re
                    match = re.search(r'\[.*\]', content, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
                    print(f"  JSON parse error, raw: {content[:200]}")
                    return None
            elif resp.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  API error {resp.status_code}: {resp.text[:200]}")
                time.sleep(2)
        except Exception as e:
            print(f"  Request error: {e}")
            time.sleep(3)
    return None


def main():
    print("=" * 60)
    print("AI 分类: 使用 DeepSeek API 重新分类所有物品")
    print("=" * 60)

    # Load data
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']
    print(f"\n[1] 加载 {len(items)} 个物品")

    # For first run, test with a small batch
    BATCH_SIZE = 30
    batches = [items[i:i + BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]
    print(f"[2] 分 {len(batches)} 批，每批 {BATCH_SIZE} 个")

    # Check if we have a partial result
    results_cache_path = SCRIPT_DIR / 'ai_classify_cache.json'
    results = {}
    if results_cache_path.exists():
        with open(results_cache_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        print(f"[3] 从缓存恢复 {len(results)} 个结果")

    total = len(results)
    start_batch = total // BATCH_SIZE if total > 0 else 0

    print(f"[4] 从第 {start_batch + 1}/{len(batches)} 批开始...")

    for bi, batch in enumerate(batches[start_batch:], start_batch):
        # Filter out already classified items
        remaining = [item for item in batch if item['id'] not in results]
        if not remaining:
            continue

        print(f"\n  批次 {bi + 1}/{len(batches)} ({len(remaining)} 个待分类)...")

        classified = classify_batch(remaining)
        if classified:
            for entry in classified:
                if isinstance(entry, dict) and 'id' in entry:
                    results[entry['id']] = {
                        'category': entry.get('category', 'items'),
                        'subcategory': entry.get('subcategory', 'misc'),
                    }

        # Save cache
        with open(results_cache_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False)

        total = len(results)
        print(f"  已分类: {total}/{len(items)}")

        # Rate limiting
        time.sleep(1)

    # Apply results
    print(f"\n[5] 应用 {len(results)} 个分类结果...")
    changes = 0
    cats = Counter()
    subs = Counter()

    for item in items:
        iid = item['id']
        if iid in results:
            new_cat = results[iid]['category']
            new_sub = results[iid]['subcategory']
            old_cat = item.get('category', '')
            old_sub = item.get('subcategory', '')

            if new_cat != old_cat or new_sub != old_sub:
                item['category'] = new_cat
                item['subcategory'] = new_sub
                changes += 1

            cats[new_cat] += 1
            subs[new_sub] += 1
        else:
            cats[item.get('category', '?')] += 1
            subs[item.get('subcategory', '?')] += 1

    data['meta']['total_items'] = len(items)

    # Update categories structure
    cat_order = ['blocks', 'colored_blocks', 'functional_blocks', 'redstone',
                 'items', 'tools', 'combat', 'food', 'materials']
    cat_names = {
        'blocks': '方块', 'colored_blocks': '彩色方块', 'functional_blocks': '功能方块',
        'redstone': '红石', 'items': '物品', 'tools': '工具',
        'combat': '战斗', 'food': '食物', 'materials': '材料',
    }
    cat_icons = {
        'blocks': 'stone', 'colored_blocks': 'white_wool', 'functional_blocks': 'crafting_table',
        'redstone': 'redstone', 'items': 'stick', 'tools': 'iron_pickaxe',
        'combat': 'iron_sword', 'food': 'bread', 'materials': 'iron_ingot',
    }

    new_categories = []
    for cid in cat_order:
        sub_map = {}
        for item in items:
            if item.get('category') == cid:
                s = item.get('subcategory', 'other')
                if s not in sub_map:
                    sub_map[s] = []
                sub_map[s].append(item['id'])

        if sub_map:
            sub_list = []
            for sid in sorted(sub_map.keys()):
                sub_map[sid].sort()
                sub_list.append({
                    'id': sid,
                    'name_zh': sid,
                    'name_en': sid.replace('_', ' ').title(),
                    'items': sub_map[sid],
                })

            new_categories.append({
                'id': cid,
                'name_zh': cat_names.get(cid, cid),
                'name_en': cid.replace('_', ' ').title(),
                'icon_item': cat_icons.get(cid, ''),
                'subcategories': sub_list,
            })

    data['categories'] = new_categories

    # Save
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"\n=== 完成 ===")
    print(f"分类更改: {changes}/{len(items)}")
    print(f"未分类: {len(items) - len(results)}")
    print(f"\n大类分布:")
    for c, n in cats.most_common():
        print(f"  {c}: {n}")
    print(f"\n文件: {os.path.getsize(DATA_PATH) / 1024:.0f} KB")

    # Remove cache if complete
    if len(results) >= len(items):
        results_cache_path.unlink(missing_ok=True)
        print("缓存已清理")


if __name__ == '__main__':
    main()
