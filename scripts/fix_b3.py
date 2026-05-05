#!/usr/bin/env python3
"""fix_b3.py — 补全 acquisition.methods（Phase1规则引擎 + Phase2 AI）"""
import json, shutil, re, time, os

DATA_PATH = 'docs/data/data.json'
API_KEY = "sk-76594786aa964c729d170f418db1d70a"
API_URL = "https://api.deepseek.com/v1/chat/completions"

shutil.copy(DATA_PATH, 'docs/data/data_backup_b3.json')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
items = data['items']

# ============================================================
# Phase 1: Rule Engine
# ============================================================
def infer_acquisition_methods(item):
    cid = item['id']
    cat = item.get('category', '')
    sub = item.get('subcategory', '')
    tags = item.get('tags', [])
    sec = item.get('secondary_categories', [])
    has_crafting = bool(item.get('crafting'))

    methods = []

    # --- 合成 (has crafting recipes) ---
    if has_crafting:
        methods.append('合成')

    # --- 合成 patterns (even without explicit crafting data, ID implies it) ---
    if '合成' not in methods:
        CRAFT_PATTERNS = [
            '_slab', '_stairs', '_wall', '_fence', '_fence_gate', '_door', '_trapdoor',
            '_button', '_pressure_plate', '_sign', '_hanging_sign',
            '_planks', '_boat', '_chest_boat',
            '_pickaxe', '_axe', '_shovel', '_hoe', '_sword',
            '_helmet', '_chestplate', '_leggings', '_boots',
            'crafting_table', 'furnace', 'chest', 'barrel',
            'book', 'bookshelf', 'enchanting_table',
            'anvil', 'loom', 'stonecutter', 'grindstone',
            'composter', 'note_block', 'jukebox',
            'painting', 'item_frame', 'armor_stand',
            'rail', 'powered_rail', 'detector_rail', 'activator_rail',
            'minecart', 'chest_minecart', 'hopper_minecart',
            'lever', 'dispenser', 'dropper', 'hopper', 'piston', 'observer',
            'daylight_detector', 'comparator', 'repeater',
            'beacon', 'conduit', 'end_crystal', 'shield',
            'lantern', 'soul_lantern', 'torch', 'soul_torch', 'campfire', 'soul_campfire',
            'stick', 'bowl', 'bucket', 'paper', 'book',
            'iron_block', 'gold_block', 'diamond_block', 'emerald_block',
            'netherite_block', 'copper_block', 'coal_block',
            'brick_block', 'lapis_block', 'redstone_block', 'quartz_block',
            'mossy_cobblestone', 'mossy_stone_brick', 'chiseled_stone_brick',
        ]
        for pat in CRAFT_PATTERNS:
            if pat in cid or cid == pat:
                methods.append('合成')
                break

    # --- 切石 ---
    if sub in ('stone', 'bricks', 'metal', 'sand', 'end', 'nether', 'ocean'):
        STONECUT_ENDINGS = ['_slab', '_stairs', '_wall', '_chiseled']
        if any(cid.endswith(p) for p in STONECUT_ENDINGS):
            if '合成' not in methods: methods.append('合成')
            methods.append('切石')

    # --- 自然生成 ---
    NATURAL_PATTERNS = [
        '_log', '_leaves', '_sapling', 'grass_block', 'dirt', 'sand',
        '_ore', 'deepslate_ore', 'ancient_debris',
        'cactus', 'sugar_cane', 'kelp', 'seagrass', 'vine',
        'brown_mushroom', 'red_mushroom', 'brown_mushroom_block', 'red_mushroom_block',
        'dandelion', 'poppy', 'tulip', 'orchid', 'daisy',
        'sunflower', 'lilac', 'peony', 'rose_bush',
        'dead_bush', 'fern', 'tall_grass',
        'cobblestone', 'stone', 'gravel',
        'ice', 'snow', 'obsidian',
        'clay', 'moss', 'dripstone', 'calcite', 'tuff',
        'bee_nest', 'spawner',
        'granite', 'diorite', 'andesite',
        'netherrack', 'soul_sand', 'soul_soil', 'magma_block', 'glowstone',
        'basalt', 'blackstone',
        'end_stone', 'chorus_plant', 'chorus_flower',
        'mycelium', 'podzol', 'coarse_dirt', 'rooted_dirt',
        'mud', 'packed_mud',
        'pumpkin', 'melon',
        'bamboo',  # bamboo plant
        'crimson_fungus', 'warped_fungus',
        'crimson_roots', 'warped_roots', 'nether_sprouts',
        'weeping_vines', 'twisting_vines',
        'shroomlight', 'froglight',
        'sculk', 'sculk_vein', 'sculk_shrieker', 'sculk_catalyst', 'sculk_sensor',
        'amethyst_block', 'budding_amethyst', 'amethyst_cluster',
        'calcite', 'dripstone_block', 'pointed_dripstone',
    ]
    for pat in NATURAL_PATTERNS:
        if pat in cid or cid == pat:
            methods.append('自然生成')
            break

    # --- 掉落 ---
    DROP_PATTERNS = [
        'string', 'feather', 'leather', 'bone', 'rotten_flesh',
        'gunpowder', 'ender_pearl', 'blaze_rod', 'ghast_tear',
        'slime_ball', 'spider_eye', 'phantom_membrane',
        'rabbit_hide', 'rabbit_foot', 'scute', 'armadillo_scute',
        'prismarine_shard', 'prismarine_crystal',
        'dragon_egg', 'nether_star', 'shulker_shell',
        'coal', 'raw_iron', 'raw_copper', 'raw_gold',
        'diamond', 'emerald',
        'trident', 'bow', 'fishing_rod',
        'wither_skeleton_skull', 'skeleton_skull', 'zombie_head',
        'creeper_head', 'dragon_head', 'piglin_head',
        'goat_horn', 'echo_shard', 'disc_fragment',
        'breeze_rod', 'wind_charge',
        'ink_sac', 'glow_ink_sac',
        'nautilus_shell', 'heart_of_the_sea',
        'totem_of_undying', 'netherite_scrap',
        'heavy_core', 'ominous_trial_key', 'trial_key',
    ]
    for pat in DROP_PATTERNS:
        if pat in cid or cid == pat:
            methods.append('掉落')
            break

    # --- 烧炼 ---
    SMELT_PATTERNS = ['smooth_stone', 'smooth_sandstone', 'smooth_red_sandstone',
        'cracked_', 'terracotta', 'glazed_terracotta',
        'glass', 'glass_pane', 'charcoal', 'nether_brick',
        'popped_chorus_fruit', 'dried_kelp',
        'green_dye', 'lime_dye',
        'iron_ingot', 'gold_ingot', 'copper_ingot',
        'cooked_', 'baked_potato', 'bread',
        'stone_brick', 'deepslate_brick',
    ]
    if '烧炼' not in methods:
        for pat in SMELT_PATTERNS:
            if pat in cid:
                methods.append('烧炼')
                break

    # --- 交易 ---
    TRADE_PATTERNS = ['bell', 'saddle', 'name_tag', 'lead', 'enchanted_book', 'bundle',
        '_banner_pattern', 'music_disc_']
    for pat in TRADE_PATTERNS:
        if pat in cid or cid.startswith(pat):
            methods.append('交易')
            break

    # --- 酿造 ---
    if 'potion' in cid or cid in ('glass_bottle','dragon_breath','fermented_spider_eye',
        'blaze_powder','magma_cream','glistering_melon_slice','golden_carrot',
        'sugar','rabbit_foot','pufferfish','ghast_tear','phantom_membrane','turtle_helmet'):
        methods.append('酿造')

    # --- 锻造 ---
    if cid.startswith('netherite_') and not cid.endswith('_block') and not cid.endswith('_ingot'):
        methods.append('锻造')

    # --- 钓鱼 ---
    if cid in ('cod', 'salmon', 'pufferfish', 'tropical_fish', 'fishing_rod',
        'enchanted_book', 'name_tag', 'saddle', 'lily_pad', 'bowl'):
        methods.append('钓鱼')

    # ---- SPECIAL CASES ----
    SPECIAL = {
        'chain': ['合成', '自然生成'],
        'ladder': ['合成', '自然生成'],
        'flower_pot': ['合成'],
        'decorated_pot': ['合成', '自然生成'],
        'bucket': ['合成'],
        'water_bucket': ['合成', '自然生成'],
        'lava_bucket': ['合成', '自然生成'],
        'powder_snow_bucket': ['合成', '自然生成'],
        'milk_bucket': ['合成'],
        'map': ['合成'], 'empty_map': ['合成', '交易'],
        'clock': ['合成', '交易'], 'compass': ['合成', '交易'],
        'recovery_compass': ['合成'], 'spyglass': ['合成'],
        'brush': ['合成'], 'firework_rocket': ['合成'], 'fire_charge': ['合成'],
        'snowball': ['掉落'], 'egg': ['掉落'],
        'book_and_quill': ['合成'], 'written_book': ['合成'], 'writable_book': ['合成'],
        'firework_star': ['合成'],
        'tnt': ['合成', '自然生成'],
        'cauldron': ['合成'],
        'brewing_stand': ['合成', '自然生成'],
        'flowering_azalea': ['自然生成'], 'azalea': ['自然生成'],
        'moss_block': ['自然生成', '交易'], 'moss_carpet': ['自然生成', '合成'],
        'hanging_roots': ['自然生成'], 'spore_blossom': ['自然生成'],
        'small_dripleaf': ['自然生成', '交易'], 'big_dripleaf': ['自然生成'],
        'glow_lichen': ['自然生成'], 'candle': ['合成'],
        'cobweb': ['自然生成'],
        'shroomlight': ['自然生成'],
        'glowstone': ['自然生成', '合成'],
        'sea_lantern': ['合成', '自然生成'],
        'jack_o_lantern': ['合成', '自然生成'],
        'shulker_box': ['合成'], 'ender_chest': ['合成'], 'trapped_chest': ['合成'],
        'lodestone': ['合成', '自然生成'], 'respawn_anchor': ['合成'],
        'beehive': ['合成'], 'lightning_rod': ['合成'],
        'scaffolding': ['合成'],
        'end_rod': ['合成', '自然生成'],
        'sponge': ['自然生成', '掉落'], 'wet_sponge': ['自然生成', '掉落'],
        'obsidian': ['自然生成', '合成'], 'crying_obsidian': ['自然生成'],
        'cobblestone': ['自然生成', '掉落'], 'stone': ['自然生成', '烧炼'],
        'flint': ['掉落'], 'wheat_seeds': ['掉落', '交易'],
        'carrot': ['自然生成', '掉落'], 'potato': ['自然生成', '掉落'],
        'apple': ['掉落', '自然生成'],
        'sweet_berries': ['自然生成'], 'glow_berries': ['自然生成'],
        'cocoa_beans': ['自然生成', '掉落'],
        'brown_mushroom': ['自然生成'], 'red_mushroom': ['自然生成'],
        'nether_wart': ['自然生成', '掉落'],
        'chorus_fruit': ['掉落'],
        'turtle_egg': ['自然生成'],
        'sniffer_egg': ['自然生成'],
        'dragon_egg': ['掉落'],
        'frogspawn': ['自然生成'],
        'suspicious_gravel': ['自然生成'],
        'suspicious_sand': ['自然生成'],
        'experience_bottle': ['交易', '自然生成'],
        'enchanted_book': ['交易', '钓鱼', '自然生成'],
        'ominous_bottle': ['掉落'],
        'golden_apple': ['合成', '自然生成'],
        'enchanted_golden_apple': ['合成', '自然生成'],
        'nautilus_shell': ['钓鱼', '掉落'],
        'heart_of_the_sea': ['自然生成'],
        'slime_ball': ['掉落', '合成'],
        'slimeball': ['掉落', '合成'],
        'honeycomb': ['掉落'], 'honey_bottle': ['合成'],
        'beetroot_seeds': ['自然生成', '交易'],
        'melon_seeds': ['自然生成', '合成'],
        'pumpkin_seeds': ['自然生成', '合成'],
        'torchflower_seeds': ['自然生成'], 'pitcher_pod': ['自然生成'],
        'ice': ['自然生成', '精准采集'], 'packed_ice': ['自然生成', '合成'],
        'blue_ice': ['自然生成', '合成'],
        'amethyst_shard': ['掉落', '自然生成'],
        'echo_shard': ['自然生成'],
        'copper_ingot': ['烧炼', '合成', '掉落'],
        'iron_ingot': ['烧炼', '合成', '掉落', '自然生成'],
        'gold_ingot': ['烧炼', '合成', '掉落', '自然生成'],
        'netherite_ingot': ['合成'],
        'diamond': ['掉落', '自然生成'],
        'emerald': ['掉落', '自然生成', '交易'],
        'coal': ['掉落', '自然生成', '烧炼'],
        'charcoal': ['烧炼'],
        'quartz': ['掉落', '自然生成', '烧炼'],
        'lapis_lazuli': ['掉落', '自然生成', '交易'],
        'redstone': ['掉落', '自然生成', '交易'],
        'raw_iron': ['掉落'], 'raw_copper': ['掉落'], 'raw_gold': ['掉落'],
        'leather': ['掉落'], 'feather': ['掉落'], 'rabbit_hide': ['掉落'],
        'bone_meal': ['合成', '掉落'], 'ink_sac': ['掉落'], 'glow_ink_sac': ['掉落'],
        'string': ['掉落', '合成'], 'cobweb': ['自然生成'],
        'saddle': ['自然生成', '交易', '钓鱼'],
        'name_tag': ['自然生成', '交易', '钓鱼'],
        'horse_armor': ['自然生成', '交易', '合成'],
        'lead': ['合成', '自然生成'],
        'flower_pot': ['合成'],
        'melobloom': ['自然生成'],  # 1.21 new
    }
    if cid in SPECIAL:
        return SPECIAL[cid]

    # Deduplicate
    seen = set()
    result = []
    for m in methods:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result if result else ['未知']

# Apply Phase 1
p1_fixed = 0
still_unknown = []
for item in items:
    current = item.get('acquisition', {}).get('methods', [])
    if '未知' in current or not current:
        new_m = infer_acquisition_methods(item)
        if new_m != ['未知']:
            item['acquisition']['methods'] = new_m
            p1_fixed += 1
        else:
            still_unknown.append(item)

print(f"Phase 1 (规则引擎): {p1_fixed} 个修复")
print(f"剩余未知: {len(still_unknown)}")

# ============================================================
# Phase 2: AI API for remaining (if any)
# ============================================================
p2_fixed = 0
if still_unknown:
    print(f"\nPhase 2 (AI): {len(still_unknown)} 个待处理")
    BATCH = 100
    for bi in range(0, len(still_unknown), BATCH):
        batch = still_unknown[bi:bi+BATCH]
        descs = [f"id={i['id']}, name_zh={i.get('name_zh','')}, name_en={i.get('name_en','')}, cat={i.get('category','')}/{i.get('subcategory','')}" for i in batch]

        prompt = "请补充以下Minecraft物品的获取方式：\n" + "\n".join(descs)
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是Minecraft获取方式专家。补充物品的获取方式列表。取值范围（仅用这些中文）：合成、自然生成、掉落、烧炼、交易、切石、锻造、酿造、钓鱼、考古、探险、精准采集、命令。返回JSON数组：[{\"id\":\"..\",\"methods\":[\"方式1\",\"方式2\"]}]。只返回JSON，不要解释。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0, "max_tokens": 4096
        }
        try:
            import requests
            resp = requests.post(API_URL, json=payload,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            content = result['choices'][0]['message']['content']
            m = re.search(r'\[.*\]', content, re.DOTALL)
            if m:
                results = json.loads(m.group())
                for r in results:
                    iid = r['id']
                    new_m = r.get('methods', [])
                    if new_m and new_m != ['未知']:
                        for item in items:
                            if item['id'] == iid:
                                item['acquisition']['methods'] = new_m
                                p2_fixed += 1
                                break
                print(f"  batch {bi//BATCH + 1}: {len(results)} done")
        except Exception as e:
            print(f"  batch {bi//BATCH + 1}: ERROR {e}")
        time.sleep(1.5)

print(f"Phase 2 (AI): {p2_fixed} 个修复")

# ============================================================
# Save & Verify
# ============================================================
data['meta']['generated_at'] = '2026-05-05-b3'
data['items'] = items

with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

unknown = sum(1 for i in items if '未知' in i.get('acquisition',{}).get('methods',[]))
empty_m = sum(1 for i in items if not i.get('acquisition',{}).get('methods'))
total = len(items)

print(f"\n=== 验证 ===")
print(f"物品总数: {total}")
print(f"含'未知': {unknown} ({unknown/total*100:.1f}%)")
print(f"获取方式为空: {empty_m}")
print(f"修复总计: {p1_fixed + p2_fixed}")
print("Done.")
