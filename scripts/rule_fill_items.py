#!/usr/bin/env python3
"""
rule_fill_items.py — 按游戏体系规则补全所有缺失物品
覆盖：16色体系、木材体系、药水、附魔书、工具/盔甲材质等
"""
import json, os, re
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / 'docs' / 'data' / 'data.json'
IMAGES_DIR = SCRIPT_DIR / 'docs' / 'images'

COLORS = ['white','orange','magenta','light_blue','yellow','lime','pink','gray','light_gray','cyan','purple','blue','brown','green','red','black']
WOODS = ['oak','spruce','birch','jungle','acacia','dark_oak','mangrove','cherry','bamboo','crimson','warped']
TOOL_MATERIALS = ['wooden','stone','iron','golden','diamond','netherite']
ARMOR_MATERIALS = ['leather','chainmail','iron','golden','diamond','netherite']

# ============================================================
# Comprehensive item generation rules
# ============================================================
def generate_all_expected_ids():
    """Generate all expected item IDs by game system."""
    ids = set()

    # A. 16-Color items
    color_bases = [
        'wool', 'carpet', 'bed', 'stained_glass', 'stained_glass_pane',
        'terracotta', 'glazed_terracotta', 'concrete', 'concrete_powder',
        'dye', 'candle', 'banner', 'shulker_box', 'bundle',
    ]
    for color in COLORS:
        for base in color_bases:
            ids.add(f'{color}_{base}')

    # B. Wood items
    wood_bases = [
        'log', 'stripped_log', 'wood', 'stripped_wood',
        'planks', 'stairs', 'slab', 'door', 'fence', 'fence_gate',
        'trapdoor', 'button', 'pressure_plate',
        'sign', 'hanging_sign', 'boat', 'chest_boat',
        'leaves', 'sapling',
    ]
    for wood in WOODS:
        for base in wood_bases:
            ids.add(f'{wood}_{base}')

    # Bamboo specials
    for base in ['mosaic','mosaic_stairs','mosaic_slab']:
        ids.add(f'bamboo_{base}')
    ids.add('bamboo_raft')
    ids.add('bamboo_chest_raft')

    # C. Tools (all materials × all types)
    tool_types = ['sword','pickaxe','axe','shovel','hoe']
    for mat in TOOL_MATERIALS:
        for t in tool_types:
            ids.add(f'{mat}_{t}')

    # D. Armor
    armor_slots = ['helmet','chestplate','leggings','boots']
    for mat in ARMOR_MATERIALS:
        for slot in armor_slots:
            ids.add(f'{mat}_{slot}')

    # E. Stone block variants
    stone_blocks = [
        'stone','cobblestone','stone_bricks','cracked_stone_bricks',
        'mossy_stone_bricks','chiseled_stone_bricks','smooth_stone',
        'stone_stairs','cobblestone_stairs','stone_brick_stairs',
        'stone_slab','cobblestone_slab','stone_brick_slab',
        'cobblestone_wall','mossy_cobblestone_wall','stone_brick_wall',
        'mossy_stone_brick_wall','mossy_cobblestone',
        'granite','granite_stairs','granite_slab','granite_wall',
        'polished_granite','polished_granite_stairs','polished_granite_slab',
        'diorite','diorite_stairs','diorite_slab','diorite_wall',
        'polished_diorite','polished_diorite_stairs','polished_diorite_slab',
        'andesite','andesite_stairs','andesite_slab','andesite_wall',
        'polished_andesite','polished_andesite_stairs','polished_andesite_slab',
        'sandstone','cut_sandstone','chiseled_sandstone','smooth_sandstone',
        'sandstone_stairs','sandstone_slab','sandstone_wall',
        'red_sandstone','cut_red_sandstone','chiseled_red_sandstone','smooth_red_sandstone',
        'red_sandstone_stairs','red_sandstone_slab','red_sandstone_wall',
        'bricks','brick_stairs','brick_slab','brick_wall',
        'mud_bricks','mud_brick_stairs','mud_brick_slab','mud_brick_wall',
        'prismarine','prismarine_bricks','dark_prismarine',
        'prismarine_stairs','prismarine_brick_stairs','dark_prismarine_stairs',
        'prismarine_slab','prismarine_brick_slab','dark_prismarine_slab',
        'prismarine_wall',
        'nether_bricks','red_nether_bricks','cracked_nether_bricks','chiseled_nether_bricks',
        'nether_brick_stairs','red_nether_brick_stairs',
        'nether_brick_slab','red_nether_brick_slab',
        'nether_brick_wall','red_nether_brick_wall',
        'blackstone','polished_blackstone','chiseled_polished_blackstone',
        'blackstone_stairs','polished_blackstone_stairs',
        'blackstone_slab','polished_blackstone_slab',
        'blackstone_wall','polished_blackstone_wall',
        'end_stone_bricks','end_stone_brick_stairs','end_stone_brick_slab','end_stone_brick_wall',
        'purpur_block','purpur_pillar','purpur_stairs','purpur_slab',
        'quartz_block','quartz_pillar','chiseled_quartz_block','quartz_bricks',
        'smooth_quartz','quartz_stairs','smooth_quartz_stairs',
        'quartz_slab','smooth_quartz_slab',
        'deepslate','cobbled_deepslate','polished_deepslate',
        'deepslate_bricks','cracked_deepslate_bricks','deepslate_tiles','cracked_deepslate_tiles','chiseled_deepslate',
        'cobbled_deepslate_stairs','polished_deepslate_stairs','deepslate_brick_stairs','deepslate_tile_stairs',
        'cobbled_deepslate_slab','polished_deepslate_slab','deepslate_brick_slab','deepslate_tile_slab',
        'cobbled_deepslate_wall','polished_deepslate_wall','deepslate_brick_wall','deepslate_tile_wall',
        'tuff','polished_tuff','tuff_bricks','chiseled_tuff',
        'tuff_stairs','polished_tuff_stairs','tuff_brick_stairs',
        'tuff_slab','polished_tuff_slab','tuff_brick_slab',
        'tuff_wall','polished_tuff_wall','tuff_brick_wall',
        'calcite','dripstone_block','pointed_dripstone',
        'basalt','polished_basalt','smooth_basalt',
        'obsidian','crying_obsidian',
        'copper_block','exposed_copper','weathered_copper','oxidized_copper',
        'cut_copper','exposed_cut_copper','weathered_cut_copper','oxidized_cut_copper',
        'chiseled_copper','exposed_chiseled_copper','weathered_chiseled_copper','oxidized_chiseled_copper',
        'copper_grate','exposed_copper_grate','weathered_copper_grate','oxidized_copper_grate',
        'copper_door','exposed_copper_door','weathered_copper_door','oxidized_copper_door',
        'copper_trapdoor','exposed_copper_trapdoor','weathered_copper_trapdoor','oxidized_copper_trapdoor',
        'copper_bulb','exposed_copper_bulb','weathered_copper_bulb','oxidized_copper_bulb',
        'glass','tinted_glass','glass_pane',
    ]
    ids.update(stone_blocks)

    # F. Potions
    potion_bases = [
        'healing','strong_healing','regeneration','long_regeneration','strong_regeneration',
        'swiftness','long_swiftness','strong_swiftness',
        'fire_resistance','long_fire_resistance',
        'poison','long_poison','strong_poison',
        'water_breathing','long_water_breathing',
        'night_vision','long_night_vision',
        'strength','long_strength','strong_strength',
        'leaping','long_leaping','strong_leaping',
        'slow_falling','long_slow_falling',
        'turtle_master','long_turtle_master','strong_turtle_master',
        'invisibility','long_invisibility',
        'weakness','long_weakness',
        'slowness','long_slowness','strong_slowness',
        'harming','strong_harming',
        'luck',
        'decay',
        'infested','oozing','weaving','wind_charged',
    ]
    for base in potion_bases:
        ids.add(f'potion_of_{base}')
        ids.add(f'splash_potion_of_{base}')
        ids.add(f'lingering_potion_of_{base}')
    ids.add('potion')
    ids.add('splash_potion')
    ids.add('lingering_potion')
    ids.add('glass_bottle')
    ids.add('dragon_breath')
    ids.add('awkward_potion')
    ids.add('mundane_potion')
    ids.add('thick_potion')
    ids.add('water_bottle')

    # G. Enchanted books (common enchants)
    enchants = [
        'protection','fire_protection','feather_falling','blast_protection','projectile_protection',
        'respiration','aqua_affinity','thorns','depth_strider','frost_walker','swift_sneak','soul_speed',
        'sharpness','smite','bane_of_arthropods','knockback','fire_aspect','looting','sweeping_edge',
        'efficiency','silk_touch','fortune','power','punch','flame','infinity',
        'unbreaking','mending','lure','luck_of_the_sea','loyalty','impaling','riptide','channeling',
        'multishot','piercing','quick_charge','impaling','density','breach','wind_burst',
    ]
    for enc in enchants:
        ids.add(f'enchanted_book_{enc}')
    ids.add('enchanted_book')

    # H. Spawn eggs
    mobs = [
        'allay','armadillo','axolotl','bat','bee','blaze','bogged','breeze',
        'camel','cat','cave_spider','chicken','cod','cow','creeper',
        'dolphin','donkey','drowned','elder_guardian','enderman','endermite','evoker',
        'fox','frog','ghast','glow_squid','goat','guardian','hoglin',
        'horse','husk','iron_golem','llama','magma_cube','mooshroom','mule',
        'ocelot','panda','parrot','phantom','pig','piglin','piglin_brute',
        'pillager','polar_bear','pufferfish','rabbit','ravager','salmon',
        'sheep','shulker','silverfish','skeleton','skeleton_horse','slime','sniffer',
        'snow_golem','spider','squid','stray','strider','tadpole','trader_llama',
        'tropical_fish','turtle','vex','villager','vindicator','wandering_trader',
        'warden','witch','wither','wither_skeleton','wolf','zoglin',
        'zombie','zombie_horse','zombie_villager','zombified_piglin',
        'skeleton_horse','zombie_horse','illusioner',
    ]
    for mob in mobs:
        ids.add(f'{mob}_spawn_egg')

    # I. Music discs
    discs = ['13','cat','blocks','chirp','far','mall','mellohi','stal','strad','ward','11','wait','otherside','5','pigstep','relic','creator','creator_music_box','precipice']
    for d in discs:
        ids.add(f'music_disc_{d}')

    # J. Banner patterns
    patterns = ['flower','creeper','skull','mojang','globe','piglin','flow','guster']
    for p in patterns:
        ids.add(f'{p}_banner_pattern')

    # K. Pottery sherds
    sherds = ['angler','archer','arms_up','blade','brewer','burn','danger','explorer','friend','heart','heartbreak','howl','miner','mourner','plenty','prize','sheaf','shelter','skull','snort']
    for s in sherds:
        ids.add(f'{s}_pottery_sherd')

    # L. Smithing templates
    templates = ['netherite_upgrade','sentry','vex','wild','coast','dune','wayfinder','raiser','shaper','host','ward','silence','eye','spire','flow','bolt']
    for t in templates:
        ids.add(f'{t}_smithing_template')

    # M. Coral blocks (colored)
    coral_colors = ['tube','brain','bubble','fire','horn']
    for cc in coral_colors:
        ids.add(f'{cc}_coral')
        ids.add(f'{cc}_coral_block')
        ids.add(f'{cc}_coral_fan')
        ids.add(f'dead_{cc}_coral')
        ids.add(f'dead_{cc}_coral_block')
        ids.add(f'dead_{cc}_coral_fan')

    # N. Ore blocks
    ores = ['coal','copper','diamond','emerald','gold','iron','lapis','redstone','nether_quartz','nether_gold','ancient_debris']
    for o in ores:
        ids.add(f'{o}_ore')
    # Deepslate variants
    for o in ['coal','copper','diamond','emerald','gold','iron','lapis','redstone']:
        ids.add(f'deepslate_{o}_ore')
    # Raw blocks
    for o in ['iron','copper','gold']:
        ids.add(f'raw_{o}')
        ids.add(f'raw_{o}_block')

    # O. Functional blocks
    functional = [
        'crafting_table','furnace','blast_furnace','smoker',
        'enchanting_table','anvil','chipped_anvil','damaged_anvil',
        'brewing_stand','cauldron','water_cauldron','lava_cauldron','powder_snow_cauldron',
        'chest','trapped_chest','ender_chest','barrel',
        'loom','stonecutter','grindstone','smithing_table','cartography_table',
        'fletching_table','composter',
        'note_block','jukebox','beacon','conduit','lodestone','respawn_anchor',
        'bell','scaffolding','ladder','torch','soul_torch','lantern','soul_lantern',
        'campfire','soul_campfire','candle','end_rod',
        'rail','powered_rail','detector_rail','activator_rail',
        'tnt','piston','sticky_piston','slime_block','honey_block',
        'hopper','dropper','dispenser','observer',
        'redstone_lamp','daylight_detector','lever',
        'stone_button','stone_pressure_plate',
        'oak_button','oak_pressure_plate',
        'iron_door','iron_trapdoor',
        'tripwire_hook','lightning_rod',
        'beehive','bee_nest','flower_pot','decorated_pot',
        'armor_stand','item_frame','glow_item_frame',
        'painting','bookshelf','lectern',
        'spawner','dragon_egg','end_portal_frame',
        'crafter','vault','trial_spawner','ominous_trial_spawner',
        'calibrated_sculk_sensor',
    ]
    ids.update(functional)

    return ids


# ============================================================
# Name, category, acquisition generators
# ============================================================
ZH_COLORS = {
    'white':'白色','orange':'橙色','magenta':'品红色','light_blue':'淡蓝色',
    'yellow':'黄色','lime':'黄绿色','pink':'粉红色','gray':'灰色','light_gray':'淡灰色',
    'cyan':'青色','purple':'紫色','blue':'蓝色','brown':'棕色','green':'绿色','red':'红色','black':'黑色',
}
ZH_WOODS = {
    'oak':'橡木','spruce':'云杉木','birch':'白桦木','jungle':'丛林木','acacia':'金合欢木',
    'dark_oak':'深色橡木','mangrove':'红树木','cherry':'樱花木','bamboo':'竹',
    'crimson':'绯红木','warped':'诡异木',
}
ZH_BASES = {
    'wool':'羊毛','carpet':'地毯','bed':'床','stained_glass':'染色玻璃',
    'stained_glass_pane':'染色玻璃板','terracotta':'陶瓦','glazed_terracotta':'带釉陶瓦',
    'concrete':'混凝土','concrete_powder':'混凝土粉末','dye':'染料','candle':'蜡烛',
    'banner':'旗帜','shulker_box':'潜影盒','bundle':'收纳袋',
    'log':'原木','stripped_log':'去皮原木','wood':'木头','stripped_wood':'去皮木头',
    'planks':'木板','stairs':'楼梯','slab':'台阶','door':'门','fence':'栅栏',
    'fence_gate':'栅栏门','trapdoor':'活板门','button':'按钮','pressure_plate':'压力板',
    'sign':'告示牌','hanging_sign':'悬挂式告示牌','boat':'船','chest_boat':'运输船',
    'leaves':'树叶','sapling':'树苗',
}
TOOL_ZH = {'sword':'剑','pickaxe':'镐','axe':'斧','shovel':'锹','hoe':'锄'}
MAT_ZH = {'wooden':'木','stone':'石','iron':'铁','golden':'金','diamond':'钻石','netherite':'下界合金'}
ARMOR_SLOT_ZH = {'helmet':'头盔','chestplate':'胸甲','leggings':'护腿','boots':'靴子'}
ARMOR_MAT_ZH = {'leather':'皮革','chainmail':'锁链','iron':'铁','golden':'金','diamond':'钻石','netherite':'下界合金'}

MOB_ZH = {
    'allay':'悦灵','armadillo':'犰狳','axolotl':'美西螈','bat':'蝙蝠','bee':'蜜蜂',
    'blaze':'烈焰人','bogged':'沼骸','breeze':'旋风人','camel':'骆驼','cat':'猫',
    'cave_spider':'洞穴蜘蛛','chicken':'鸡','cod':'鳕鱼','cow':'牛','creeper':'苦力怕',
    'dolphin':'海豚','donkey':'驴','drowned':'溺尸','elder_guardian':'远古守卫者',
    'enderman':'末影人','endermite':'末影螨','evoker':'唤魔者','fox':'狐狸','frog':'青蛙',
    'ghast':'恶魂','glow_squid':'发光鱿鱼','goat':'山羊','guardian':'守卫者',
    'hoglin':'疣猪兽','horse':'马','husk':'尸壳','iron_golem':'铁傀儡','llama':'羊驼',
    'magma_cube':'岩浆怪','mooshroom':'哞菇','mule':'骡','ocelot':'豹猫','panda':'熊猫',
    'parrot':'鹦鹉','phantom':'幻翼','pig':'猪','piglin':'猪灵','piglin_brute':'猪灵蛮兵',
    'pillager':'掠夺者','polar_bear':'北极熊','pufferfish':'河豚','rabbit':'兔子',
    'ravager':'劫掠兽','salmon':'鲑鱼','sheep':'绵羊','shulker':'潜影贝',
    'silverfish':'蠹虫','skeleton':'骷髅','skeleton_horse':'骷髅马','slime':'史莱姆',
    'sniffer':'嗅探兽','snow_golem':'雪傀儡','spider':'蜘蛛','squid':'鱿鱼',
    'stray':'流浪者','strider':'炽足兽','tadpole':'蝌蚪','trader_llama':'行商羊驼',
    'tropical_fish':'热带鱼','turtle':'海龟','vex':'恼鬼','villager':'村民',
    'vindicator':'卫道士','wandering_trader':'流浪商人','warden':'监守者',
    'witch':'女巫','wither':'凋灵','wither_skeleton':'凋零骷髅','wolf':'狼',
    'zoglin':'僵尸疣猪兽','zombie':'僵尸','zombie_horse':'僵尸马',
    'zombie_villager':'僵尸村民','zombified_piglin':'僵尸猪灵',
    'illusioner':'幻术师',
}
POTION_ZH = {
    'healing':'治疗','strong_healing':'治疗II','regeneration':'再生','long_regeneration':'延长再生',
    'swiftness':'迅捷','long_swiftness':'延长迅捷','strong_swiftness':'迅捷II',
    'fire_resistance':'抗火','long_fire_resistance':'延长抗火',
    'poison':'剧毒','long_poison':'延长剧毒','strong_poison':'剧毒II',
    'water_breathing':'水肺','long_water_breathing':'延长水肺',
    'night_vision':'夜视','long_night_vision':'延长夜视',
    'strength':'力量','long_strength':'延长力量','strong_strength':'力量II',
    'leaping':'跳跃','long_leaping':'延长跳跃','strong_leaping':'跳跃II',
    'slow_falling':'缓降','long_slow_falling':'延长缓降',
    'turtle_master':'神龟','long_turtle_master':'延长神龟','strong_turtle_master':'神龟II',
    'invisibility':'隐身','long_invisibility':'延长隐身',
    'weakness':'虚弱','long_weakness':'延长虚弱',
    'slowness':'缓慢','long_slowness':'延长缓慢','strong_slowness':'缓慢II',
    'harming':'伤害','strong_harming':'伤害II',
    'luck':'幸运','decay':'衰变',
    'infested':'虫蚀','oozing':'渗浆','weaving':'盘丝','wind_charged':'蓄风',
}


def gen_name_zh(iid):
    # Existing in our known dict
    for color_en, color_zh in ZH_COLORS.items():
        if iid.startswith(color_en + '_'):
            base = iid[len(color_en)+1:]
            if base in ZH_BASES:
                return color_zh + ZH_BASES[base]
    for wood_en, wood_zh in ZH_WOODS.items():
        if iid.startswith(wood_en + '_'):
            base = iid[len(wood_en)+1:]
            if base in ZH_BASES:
                return wood_zh + ZH_BASES[base]
    # Tools
    for mat_short, mat_zh in MAT_ZH.items():
        if iid.startswith(mat_short + '_'):
            base = iid[len(mat_short)+1:]
            if base in TOOL_ZH:
                return mat_zh + TOOL_ZH[base]
    # Armor
    for mat_short, mat_zh in ARMOR_MAT_ZH.items():
        for slot, slot_zh in ARMOR_SLOT_ZH.items():
            if iid == f'{mat_short}_{slot}':
                return mat_zh + slot_zh
    # Spawn eggs
    if iid.endswith('_spawn_egg'):
        mob = iid[:-10]
        return MOB_ZH.get(mob, mob.replace('_',' ').title()) + '刷怪蛋'
    # Potions
    if iid.startswith('potion_of_'):
        base = iid[10:]
        return POTION_ZH.get(base, base.replace('_',' ')) + '药水'
    if iid.startswith('splash_potion_of_'):
        base = iid[17:]
        return '喷溅型' + POTION_ZH.get(base, base.replace('_',' ')) + '药水'
    if iid.startswith('lingering_potion_of_'):
        base = iid[20:]
        return '滞留型' + POTION_ZH.get(base, base.replace('_',' ')) + '药水'
    # Enchanted books
    if iid.startswith('enchanted_book_'):
        enc = iid[15:].replace('_',' ')
        return f'附魔书（{enc}）'
    # Music discs
    if iid.startswith('music_disc_'):
        disc = iid[11:]
        return f'音乐唱片（{disc}）'
    # Banner patterns
    if iid.endswith('_banner_pattern'):
        pat = iid[:-15].replace('_',' ').title()
        return f'{pat}旗帜图案'
    # Pottery sherds
    if iid.endswith('_pottery_sherd'):
        sh = iid[:-14].replace('_',' ').title()
        return f'{sh}纹样陶片'
    # Smithing templates
    if iid.endswith('_smithing_template'):
        t = iid[:-18].replace('_',' ').title()
        return f'{t}锻造模板'
    return None


def classify_item(iid):
    if any(iid.endswith('_' + s) for s in ['wool','carpet','concrete','concrete_powder','terracotta','glazed_terracotta','stained_glass','stained_glass_pane']):
        return 'blocks', 'colored'
    if any(iid.endswith('_' + s) for s in ['log','stripped_log','wood','stripped_wood','planks','stairs','slab','fence','fence_gate','door','trapdoor','button','pressure_plate','sign','hanging_sign']):
        return 'blocks', 'wood'
    if 'potion' in iid:
        return 'items', 'potions'
    if iid.endswith('_spawn_egg'):
        return 'items', 'spawn_eggs'
    if iid.startswith('music_disc_'):
        return 'items', 'music_discs'
    if iid.endswith('_banner_pattern'):
        return 'items', 'misc'
    if iid.endswith('_pottery_sherd') or iid.endswith('_smithing_template'):
        return 'items', 'misc'
    if iid.endswith('_boat') or iid.endswith('_chest_boat') or iid.endswith('_raft'):
        return 'items', 'transport'
    if iid.startswith('enchanted_book'):
        return 'items', 'misc'
    if any(iid.endswith('_' + s) for s in ['sword','bow','crossbow']):
        return 'combat', 'weapons'
    if any(iid.endswith('_' + s) for s in ['helmet','chestplate','leggings','boots','horse_armor']):
        return 'combat', 'armor'
    if any(iid.endswith('_' + s) for s in ['pickaxe','axe','shovel','hoe']):
        return 'tools', 'tools'
    if any(s in iid for s in ['_ore','raw_','_ingot','_nugget','_dust','dye']):
        return 'materials', 'ingredients'
    return 'items', 'misc'


def gen_acquisition(iid):
    if iid.endswith('_spawn_egg'):
        return ['创造模式物品栏']
    if 'potion' in iid or iid == 'glass_bottle' or iid.endswith('_bottle'):
        return ['酿造']
    if iid.startswith('enchanted_book'):
        return ['附魔', '战利品']
    if iid.endswith('_wool'):
        return ['剪羊毛', '合成']
    if iid.endswith('_carpet') or iid.endswith('_bed'):
        return ['合成']
    if iid.endswith('_concrete'):
        return ['合成', '水转化']
    if iid.endswith('_concrete_powder'):
        return ['合成']
    if iid.endswith('_glazed_terracotta'):
        return ['烧炼']
    if any(iid.endswith('_' + t) for t in ['pickaxe','axe','shovel','hoe','sword']):
        return ['合成']
    if any(iid.endswith('_' + s) for s in ['helmet','chestplate','leggings','boots']):
        return ['合成']
    if iid.endswith('_boat') or iid.endswith('_raft'):
        return ['合成']
    if iid.endswith('_planks') or iid.endswith('_slab') or iid.endswith('_stairs'):
        return ['合成']
    if iid in ['crafting_table','furnace','chest','anvil','enchanting_table','brewing_stand','cauldron']:
        return ['合成']
    return ['未知']


def main():
    print('=' * 60)
    print('Rule Fill: 按游戏体系规则补全物品')
    print('=' * 60)

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    existing_ids = {i['id'] for i in data['items']}
    expected_ids = generate_all_expected_ids()

    print(f'\nSystem-expected IDs: {len(expected_ids)}')
    print(f'Currently in data:  {len(existing_ids)}')
    print(f'Missing from data:  {len(expected_ids - existing_ids)}')

    # Add missing items
    added = []
    for iid in sorted(expected_ids - existing_ids):
        name_zh = gen_name_zh(iid)
        if not name_zh:
            name_zh = iid.replace('_', ' ').title()

        cat, sub = classify_item(iid)
        methods = gen_acquisition(iid)

        # Check if image exists
        img_path = IMAGES_DIR / f'{iid}.png'
        icon_url = f'images/{iid}.png'

        item = {
            'id': iid,
            'name_zh': name_zh,
            'name_en': iid.replace('_', ' ').title(),
            'category': cat,
            'subcategory': sub,
            'icon_url': icon_url,
            'acquisition': {
                'methods': methods,
                'natural_generation': [],
                'smelting': [],
                'trading': None,
                'drops_from': [],
            },
            'crafting': [],
            'stonecutting': None,
            'smithing': None,
            'related_items': [],
            'source': 'rule_generated',
        }
        data['items'].append(item)
        added.append(iid)

    data['meta']['total_items'] = len(data['items'])

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    print(f'\n=== Results ===')
    print(f'Items added: {len(added)}')
    print(f'Total items: {len(data["items"])}')

    cats = {}
    subs = {}
    for i in data['items']:
        c = i.get('category','?')
        cats[c] = cats.get(c,0)+1
        s = i.get('subcategory','?')
        subs[s] = subs.get(s,0)+1
    print(f'\nCategories:')
    for c,n in sorted(cats.items(), key=lambda x:-x[1]):
        print(f'  {c}: {n}')
    print(f'\nSubcategories:')
    for s,n in sorted(subs.items(), key=lambda x:-x[1]):
        print(f'  {s}: {n}')

    # Image coverage
    imgs = set(f.replace('.png','') for f in os.listdir(IMAGES_DIR) if f.endswith('.png'))
    with_img = sum(1 for i in data['items'] if i['id'] in imgs)
    print(f'\nImage coverage: {with_img}/{len(data["items"])} ({100*with_img//len(data["items"])}%)')
    print(f'File size: {os.path.getsize(DATA_PATH)/1024:.0f} KB')


if __name__ == '__main__':
    main()
