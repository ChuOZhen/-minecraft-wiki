# ============================================
# variant_expander.py — 变体展开引擎
# ============================================
#
# 从概览页（Wool, Sign, Bed, Planks 等）提取多个独立 variant item。
# 这些页面在 Wiki 上将多个变体折叠展示，变体 URL 会 302 重定向至此。
#
# 策略:
#   1. 检查页面是否为"多变量概览页"
#   2. 从 infobox BlockSprite 图片 alt 文本中提取 variant 名称
#   3. 生成独立 item（继承 base_item 字段）
#
# ============================================

import re
from bs4 import BeautifulSoup
from utils import normalize_id, icon_url_from_img_src

# 已知颜色 → 中文名映射
_COLOR_ZH = {
    'white': '白色', 'orange': '橙色', 'magenta': '品红色',
    'light_blue': '淡蓝色', 'yellow': '黄色', 'lime': '黄绿色',
    'pink': '粉色', 'gray': '灰色', 'light_gray': '淡灰色',
    'cyan': '青色', 'purple': '紫色', 'blue': '蓝色',
    'brown': '棕色', 'green': '绿色', 'red': '红色', 'black': '黑色',
}

# 已知木材 → 中文名映射
_WOOD_ZH = {
    'oak': '橡木', 'spruce': '云杉', 'birch': '白桦',
    'jungle': '丛林', 'acacia': '金合欢', 'dark-oak': '深色橡木',
    'dark_oak': '深色橡木', 'mangrove': '红树', 'cherry': '樱花',
    'pale-oak': '苍白橡木', 'pale_oak': '苍白橡木',
    'bamboo': '竹', 'crimson': '绯红', 'warped': '诡异',
}

# 概览页标题 → 变体类别
_OVERVIEW_PAGES = {
    'wool', 'bed', 'carpet', 'concrete', 'concrete powder',
    'terracotta', 'glazed terracotta', 'stained glass', 'stained glass pane',
    'sign', 'hanging sign', 'planks', 'log', 'wood',
    'door', 'trapdoor', 'fence', 'fence gate', 'slab', 'stairs',
    'button', 'pressure plate', 'boat', 'banner', 'candle',
    'shulker box', 'spawn egg', 'bundle',
}

# 需要排除的非变体 sprite 关键词
_SPRITE_SKIP = {
    'shears', 'axe_required', 'pickaxe_required', 'shovel_required',
    'hoe_required', 'sword_required', 'slot', 'invicon',
    'rainbow', 'all-', 'heart', 'hunger', 'armor', 'helmet',
    'chestplate', 'leggings', 'boots',
}


def extract_variants(html, base_item):
    """
    从概览页 HTML 中提取变体物品列表。

    参数:
      html: 原始 HTML 字符串
      base_item: parse_item_page 返回的 base item dict

    返回:
      List[dict]: 变体 item 列表（包含 base_item 本身和所有 variant）
    """
    item_id = base_item.get('id', '')
    name_en = base_item.get('name_en', '')

    # 判断是否为概览页
    if not _is_overview_page(item_id, name_en):
        return [base_item]

    soup = BeautifulSoup(html, 'lxml')
    variants = _extract_from_infobox(soup, base_item)

    if len(variants) <= 1:
        return [base_item]

    # 日志
    print(f"  [VARIANT_EXPANSION]")
    print(f"    base: {item_id}")
    print(f"    generated: {len(variants)} items")

    return variants


def _is_overview_page(item_id, name_en):
    """判断 item 是否为概览页（需要展开变体）"""
    # 标准化名称（空格 → 下划线）
    id_lower = item_id.lower()
    name_lower = name_en.lower()
    id_spaces = id_lower.replace('_', ' ')
    name_spaces = name_lower.replace('_', ' ')

    # 直接匹配已知概览页（同时检查空格和下划线两种形式）
    for ov in _OVERVIEW_PAGES:
        if id_lower == ov or id_spaces == ov or name_lower == ov or name_spaces == ov:
            return True

    # id 已经是具体项（含颜色/木材前缀）→ 不需要展开
    parts = id_lower.split('_')
    if len(parts) >= 2 and parts[0] in _COLOR_ZH:
        return False
    if len(parts) >= 2 and parts[0] in _WOOD_ZH:
        return False
    if len(parts) >= 3:
        prefix2 = '_'.join(parts[:2])
        if prefix2 in _COLOR_ZH or prefix2 in _WOOD_ZH:
            return False
    return False


def _extract_from_infobox(soup, base_item):
    """
    从 infobox 的 BlockSprite/ItemSprite 图片 alt 文本中提取变体。

    解析 alt 文本格式:
      "BlockSprite white-wool.png: Sprite image for white-wool in Minecraft"
      "BlockSprite oak-sign.png: Sprite image for oak-sign in Minecraft"
      "BlockSprite white-bed-top-foot.png: Sprite image for white-bed-top-foot in Minecraft"
    """
    content = soup.find('div', id='mw-content-text') or soup.find('div', class_='mw-parser-output')
    if not content:
        return [base_item]

    # 查找 infobox
    infobox = None
    for cls in ['infobox', 'notaninfobox']:
        infobox = content.find('table', class_=re.compile(cls))
        if infobox:
            break
    base_name = base_item.get('name_en', '').lower()
    base_id = base_item.get('id', '')

    # 收集所有变体候选
    variant_candidates = {}  # {variant_key: icon_url}

    def _scan_images(container):
        for img in container.find_all('img'):
            alt = img.get('alt', '').strip()
            src = img.get('src', '') or img.get('data-src', '')
            if not alt or not src:
                continue
            if src.endswith('.svg'):
                continue
            if any(x in src.lower() for x in ['pixel', 'spacer']):
                continue
            variant_name = _parse_variant_from_alt(alt, base_name, base_id)
            if variant_name:
                icon_url = icon_url_from_img_src(src)
                if variant_name not in variant_candidates:
                    variant_candidates[variant_name] = icon_url

    # 优先从 infobox 扫描
    if infobox:
        _scan_images(infobox)

    # 回退：扫描全页内容
    if len(variant_candidates) <= 1:
        _scan_images(content)

    if len(variant_candidates) <= 1:
        return [base_item]

    # 生成 variant items
    result = []
    for var_name, icon_url in variant_candidates.items():
        var_item = _build_variant_item(base_item, var_name, icon_url)
        result.append(var_item)

    return result if result else [base_item]


def _parse_variant_from_alt(alt_text, base_name, base_id):
    """
    从 img alt 文本中提取 variant 名称。
    支持两种 Wiki sprite 格式:

    格式 A (BlockSprite):
      "BlockSprite white-wool.png: Sprite image for white-wool in Minecraft"
      "BlockSprite oak-sign.png: Sprite image for oak-sign in Minecraft"

    格式 B (Invicon):
      "Invicon White Carpet.png: Sprite image for White Carpet in Minecraft"
      "Invicon Red Carpet.png: Sprite image for Red Carpet in Minecraft"

    返回: variant 名称如 "white_wool", "oak_sign", "white_bed", "white_carpet"
    """
    alt_lower = alt_text.lower()

    # 跳过 UI 元素 sprite（不是 item 变体）
    _ui_skip = {'shears', 'axe_required', 'pickaxe_required', 'shovel_required',
                'hoe_required', 'sword_required', 'slot', 'rainbow', 'all-',
                'heart', 'hunger', 'armor', 'helmet', 'chestplate', 'leggings', 'boots'}
    skip_this = False
    for ui in _ui_skip:
        if ui in alt_lower:
            skip_this = True
            break
    if skip_this:
        return None

    # --- 格式 A: BlockSprite / ItemSprite ---
    m = re.search(r'(?:blocksprite|itemsprite)\s+([a-zA-Z][-\w]*)', alt_lower)
    if m:
        filename = m.group(1).replace('.png', '').strip()
        filename = filename.replace('-', '_')

        # 去掉方向/部位后缀
        for suffix in ['_top_foot', '_top_head', '_top', '_side', '_front', '_back', '_bottom']:
            if filename.endswith(suffix):
                filename = filename[:-len(suffix)]
                break

        base_key = base_name.replace('-', '_').replace(' ', '_')
        if filename and base_key in filename:
            return filename

    # --- 格式 B: Invicon (Minecraft Wiki inventory sprites) ---
    m = re.search(r'invicon\s+([a-zA-Z][\w\s]*?)(?:\.png)?\s*:', alt_lower)
    if m:
        # "Invicon White Carpet.png:" → "White Carpet"
        name = m.group(1).replace('.png', '').strip()
        # 检查是否与 base 相关
        if base_name.lower() in name.lower():
            return normalize_id(name)

    return None


def _build_variant_item(base_item, var_name, icon_url):
    """
    根据 variant 名称构建独立 item。

    var_name: "white_wool" → id="white_wool", name_en="White Wool"
    """
    # 解析 variant 名称: 确定前缀（color/wood）和 base
    parts = var_name.split('_')

    # 识别颜色/木材前缀
    prefix = None
    prefix_zh = None
    prefix_type = None

    # 尝试 3-word prefix: "light_blue", "dark_oak", "pale_oak", "light_gray"
    if len(parts) >= 3:
        three = '_'.join(parts[:2])
        if three in _COLOR_ZH:
            prefix = three
            prefix_zh = _COLOR_ZH[three]
            prefix_type = 'color'
        elif three in _WOOD_ZH:
            prefix = three
            prefix_zh = _WOOD_ZH[three]
            prefix_type = 'wood'

    if not prefix and len(parts) >= 2:
        two = parts[0]
        if two in _COLOR_ZH:
            prefix = two
            prefix_zh = _COLOR_ZH[two]
            prefix_type = 'color'
        elif two in _WOOD_ZH:
            prefix = two
            prefix_zh = _WOOD_ZH[two]
            prefix_type = 'wood'

    if not prefix:
        # 不确定前缀类型，仍生成 variant
        prefix = parts[0]
        prefix_zh = prefix.title()
        prefix_type = 'unknown'

    # 构建英文名
    name_parts = var_name.split('_')
    name_en = ' '.join(w.capitalize() for w in name_parts)

    # 构建 item
    base = base_item.copy()
    base['id'] = normalize_id(var_name)
    base['name_en'] = name_en

    # 优先使用 Special:FilePath（Wiki 重定向到正确版本图片）
    # 回退到 sprite URL
    safe_name = name_en.replace(' ', '_')
    base['icon_url'] = f"https://minecraft.wiki/w/Special:FilePath/{safe_name}.png"

    # name_zh: 清除（让 normalizer 重新分配）
    base['name_zh'] = name_en

    # 不继承 crafting（概览页的配方属于通用配方，不一定适用每个变体）
    # 变体通常与 base 集合共享配方
    if base.get('crafting'):
        base['crafting'] = []  # 变体页面无独立配方

    # 清空 related_items（让后续重新生成）
    base['related_items'] = []

    # 不继承 stonecutting/smithing（变体不适用）
    base['stonecutting'] = []
    base['smithing'] = []

    return base


# ============================================
# Spawn Egg 变体提取（从 wikitable 而非 infobox）
# ============================================

def extract_spawn_egg_variants(html, base_item):
    """
    Spawn Egg 页面使用 wikitable 展示所有生物变体。
    从页面中找到"可生成实体"表格，提取每个 entity → spawn egg item。
    """
    if not base_item.get('id') == 'spawn_egg':
        return [base_item]

    soup = BeautifulSoup(html, 'lxml')
    content = soup.find('div', id='mw-content-text') or soup.find('div', class_='mw-parser-output')
    if not content:
        return [base_item]

    variants = {}
    known_entities = {
        'bat': '蝙蝠', 'blaze': '烈焰人', 'bee': '蜜蜂',
        'cat': '猫', 'cave spider': '洞穴蜘蛛', 'chicken': '鸡',
        'cod': '鳕鱼', 'cow': '牛', 'creeper': '苦力怕',
        'dolphin': '海豚', 'donkey': '驴', 'drowned': '溺尸',
        'elder guardian': '远古守卫者', 'enderman': '末影人',
        'endermite': '末影螨', 'evoker': '唤魔者', 'fox': '狐狸',
        'ghast': '恶魂', 'glow squid': '发光鱿鱼', 'goat': '山羊',
        'guardian': '守卫者', 'hoglin': '疣猪兽', 'horse': '马',
        'husk': '尸壳', 'iron golem': '铁傀儡', 'llama': '羊驼',
        'magma cube': '岩浆怪', 'mooshroom': '哞菇', 'mule': '骡',
        'ocelot': '豹猫', 'panda': '熊猫', 'parrot': '鹦鹉',
        'phantom': '幻翼', 'pig': '猪', 'piglin': '猪灵',
        'piglin brute': '猪灵蛮兵', 'pillager': '掠夺者',
        'polar bear': '北极熊', 'pufferfish': '河豚',
        'rabbit': '兔子', 'ravager': '劫掠兽',
        'salmon': '鲑鱼', 'sheep': '羊', 'shulker': '潜影贝',
        'silverfish': '蠹虫', 'skeleton': '骷髅',
        'skeleton horse': '骷髅马', 'slime': '史莱姆',
        'snow golem': '雪傀儡', 'spider': '蜘蛛',
        'squid': '鱿鱼', 'stray': '流浪者', 'strider': '炽足兽',
        'tadpole': '蝌蚪', 'trader llama': '商贩羊驼',
        'tropical fish': '热带鱼', 'turtle': '海龟',
        'vex': '恼鬼', 'villager': '村民', 'vindicator': '卫道士',
        'wandering trader': '流浪商人', 'warden': '监守者',
        'witch': '女巫', 'wither skeleton': '凋灵骷髅',
        'wolf': '狼', 'zoglin': '僵尸疣猪兽',
        'zombie': '僵尸', 'zombie villager': '僵尸村民',
        'zombified piglin': '僵尸猪灵',
        'armadillo': '犰狳', 'bogged': '沼泽骷髅',
        'breeze': '旋风人', 'creaking': '嘎吱怪',
        'sniffer': '嗅探兽', 'camel': '骆驼',
        'allay': '悦灵', 'frog': '青蛙',
        'wither': '凋灵', 'ender dragon': '末影龙',
    }

    # 搜索 wikitable 中包含 entity/spawn 的行
    for table in content.find_all('table', class_='wikitable'):
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            # 找包含图片的单元格
            row_text = row.get_text(' ', strip=True).lower()
            has_entity = any(e in row_text for e in ['spawn', 'egg', 'entity', 'creature', 'mob'])

            img = row.find('img')
            if img and has_entity:
                src = img.get('src', '') or img.get('data-src', '')
                alt = img.get('alt', '')
                if src and 'sprite' in alt.lower():
                    # 从 alt 提取 entity 名
                    entity = _parse_entity_from_alt(alt, known_entities)
                    if entity and entity not in variants:
                        icon_url = icon_url_from_img_src(src)
                        variants[entity] = icon_url

    if len(variants) <= 1:
        return [base_item]

    result = []
    for entity, _icon_url in variants.items():
        entity_id = normalize_id(entity.replace(' ', '_'))
        var_id = f'{entity_id}_spawn_egg'
        var_name_en = f'{entity.title()} Spawn Egg'

        # 使用 Special:FilePath 获取实际图片（而非 Invicon 精灵）
        safe_name = var_name_en.replace(' ', '_')
        icon_url = f'https://minecraft.wiki/w/Special:FilePath/{safe_name}.png'

        var_item = base_item.copy()
        var_item['id'] = var_id
        var_item['name_en'] = var_name_en
        var_item['name_zh'] = var_name_en
        var_item['icon_url'] = icon_url
        var_item['crafting'] = []
        var_item['stonecutting'] = []
        var_item['smithing'] = []
        var_item['related_items'] = []

        result.append(var_item)

    if len(result) > 1:
        print(f"  [VARIANT_EXPANSION]")
        print(f"    base: spawn_egg")
        print(f"    generated: {len(result)} items")

    return result if result else [base_item]


def _parse_entity_from_alt(alt_text, known_entities):
    """
    从 Spawn Egg 的 img alt 文本提取 entity 名称。

    输入示例:
      "ItemSprite creeper-spawn-egg.png: Sprite image for creeper-spawn-egg in Minecraft"
      "Invicon Bat Spawn Egg.png: Sprite image for Bat Spawn Egg in Minecraft"
    """
    alt_lower = alt_text.lower()

    # 尝试从已知实体中匹配
    for entity in sorted(known_entities.keys(), key=len, reverse=True):
        if entity in alt_lower:
            return entity

    # 尝试正则匹配 {entity}-spawn-egg 或 {entity}_spawn_egg
    m = re.search(r'(?:itemsprite|invicon)\s+([a-z][a-z_]+)[\s\-]spawn[\s\-]egg', alt_lower)
    if m:
        entity = m.group(1).replace('_', ' ').replace('-', ' ').strip()
        if entity:
            return entity

    return None
