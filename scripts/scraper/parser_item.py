# ============================================
# parser_item.py — 解析单个物品页面（mcui/invslot aware）
# ============================================

import re
from bs4 import BeautifulSoup, Tag
from utils import (
    normalize_id, icon_url_from_name, icon_url_from_img_src,
    extract_page_title_from_url
)
from parser_list import parse_page_categories, get_category_from_wiki_cats, get_subcategory_from_wiki_cats, is_reject_page


def parse_item_page(html, url):
    """解析单个物品页面，返回结构化数据 dict。失败返回 None。"""
    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')
    content = soup.find('div', id='mw-content-text')
    if not content:
        content = soup.find('div', class_='mw-parser-output')
    if not content:
        content = soup

    title = extract_page_title(soup)
    item_id = normalize_id(title)
    name_en = clean_name(title)

    icon_url = extract_icon_url(soup, content, name_en)

    wiki_cats = parse_page_categories(soup)

    # 过滤非标准物品（愚人节、教育版、实体页等）
    reject, reject_reason = is_reject_page(wiki_cats)
    if reject:
        print(f"  [SKIP] Rejected '{name_en}': {reject_reason}")
        return None

    category = get_category_from_wiki_cats(wiki_cats)
    subcategory = get_subcategory_from_wiki_cats(wiki_cats)
    # 如果规则匹配失败, 回退到旧的关键词方式
    if not subcategory or subcategory == "general":
        subcategory = guess_subcategory(category, name_en, item_id)

    crafting = extract_crafting_recipes(content, item_id)
    stonecutting = extract_stonecutting_recipes(content, item_id)
    smithing = extract_smithing_recipes(content, item_id)
    smelting_list = extract_smelting_recipes(content, item_id)
    acquisition = extract_acquisition(content, smelting_list, stonecutting, smithing)
    natural_gen = extract_natural_generation(content)

    if natural_gen:
        acquisition['natural_generation'] = natural_gen
    if smelting_list:
        acquisition['smelting'] = smelting_list

    return {
        "id": item_id,
        "name_zh": name_en,
        "name_en": name_en,
        "category": category,
        "subcategory": subcategory,
        "icon_url": icon_url,
        "source": "wiki",
        "acquisition": acquisition,
        "crafting": crafting,
        "stonecutting": stonecutting,
        "smithing": smithing,
        "related_items": generate_related_items(crafting, stonecutting, smithing),
    }


# ============================================
# 标题/名称
# ============================================

def extract_page_title(soup):
    h1 = soup.find('h1', id='firstHeading')
    if h1:
        return h1.get_text(strip=True)
    title_tag = soup.find('title')
    if title_tag:
        text = title_tag.get_text(strip=True)
        for sep in ['– Minecraft Wiki', ' - Minecraft Wiki', '– Official', ' - Official']:
            if sep in text:
                text = text.split(sep)[0].strip()
        return text
    return "Unknown"


def clean_name(name):
    return re.sub(r'\s*\([^)]*\)\s*', '', name).strip()


# ============================================
# 图标 URL
# ============================================

def _get_img_src(img):
    """从 img 标签获取最佳 URL（优先 data-src，回退 src）"""
    src = img.get('data-src') or img.get('src') or ''
    if not src or src.startswith('data:'):
        return ''
    if any(x in src.lower() for x in ['pixel', 'spacer', 'placeholder']):
        return ''
    return src


def _parse_ingredient_name(link, img):
    """从 link 或 img 提取原料英文名（避免 alt 描述文本污染）"""
    # 策略 1: link title（最可靠）
    if link:
        title = link.get('title', '').strip()
        if title and ':' not in title and 'sprite' not in title.lower():
            return title

    # 策略 2: img alt 但需要清理 Invicon 前缀和描述
    if img:
        alt = img.get('alt', '').strip()
        if alt:
            # "Invicon Oak Planks.png: Inventory sprite..." → "Oak Planks"
            # "Invicon Stone.png: Inventory sprite for Stone..." → "Stone"
            if alt.startswith('Invicon '):
                # 去掉 Invicon 前缀
                name = alt[8:]
                # 去掉 .png 和后面的描述
                if '.png' in name:
                    name = name.split('.png')[0]
                return name.strip()

    # 策略 3: link text
    if link:
        text = link.get_text(strip=True)
        if text and len(text) > 1 and len(text) < 50:
            return text

    return ''


def extract_icon_url(soup, content, name_en):
    """从页面提取物品图标。按优先级：infobox 非sprite图 → 页面正文大图 → Special:FilePath"""

    name_slug = name_en.replace(' ', '_')
    name_lower = name_en.lower()

    # Invicon = valid item sprite (keep). BlockSprite/SlotSprite/Hunger/heart = UI element (reject).
    sprite_keywords = ['slotsprite', 'blocksprite', 'itemsprite',
                       'heart', 'hunger', 'axe_required',
                       'pickaxe_required', 'shovel_required', 'disambig', 'armor_', 'half_',
                       'required', 'icon_(', '_(icon)']

    # ---- 第一阶段：搜索 infobox ----
    infobox = None
    for cls in ['infobox', 'notaninfobox']:
        infobox = content.find('table', class_=re.compile(cls))
        if infobox:
            break
    if not infobox:
        infobox = content.find('table')

    best_src = None
    best_area = 0

    if infobox:
        for img in infobox.find_all('img'):
            src = _get_img_src(img)
            if not src:
                continue
            if any(x in src.lower() for x in ['pixel', 'spacer']):
                continue
            if src.endswith('.svg'):
                continue
            w = int(img.get('width', 0) or 0)
            h = int(img.get('height', 0) or 0)
            area = w * h
            is_sprite = any(kw in src.lower() for kw in sprite_keywords)
            if not is_sprite and area > best_area:
                best_src = src
                best_area = area

    # ---- 第二阶段：页面正文搜索（目标：物品主图）----
    if not best_src:
        # 物品主图通常在 content 顶部，是一个大尺寸缩略图
        for img in content.find_all('img'):
            src = _get_img_src(img)
            if not src:
                continue
            if any(x in src.lower() for x in ['pixel', 'spacer']):
                continue
            alt = (img.get('alt') or '').lower()
            # 从 src 提取文件名，判断是否匹配物品名
            src_lower = src.lower()
            filename_hint = name_slug.lower().replace('_', '-')  # Wiki uses hyphens

            # 匹配条件：
            #   1. 是 thumb 图片（含 /thumb/ 路径）
            #   2. 文件名包含物品名
            #   3. 不是 sprite / svg
            is_thumb = '/thumb/' in src_lower
            name_match = (name_lower.replace(' ', '_') in src_lower.replace('-', '_') or
                         name_lower.replace(' ', '-') in src_lower.replace('_', '-'))
            is_svg = src.endswith('.svg')
            is_sprite = any(kw in src_lower for kw in sprite_keywords)

            if is_thumb and name_match and not is_svg and not is_sprite:
                w = int(img.get('width', 0) or 0)
                h = int(img.get('height', 0) or 0)
                area = w * h
                # 优先大图
                if area > best_area:
                    best_src = src
                    best_area = area

    # ---- 第三阶段：任意非 sprite 大图 ----
    if not best_src:
        for img in content.find_all('img'):
            src = _get_img_src(img)
            if not src:
                continue
            if src.endswith('.svg'):
                continue
            sl = src.lower()
            if any(kw in sl for kw in sprite_keywords):
                continue
            if any(x in sl for x in ['pixel', 'spacer']):
                continue
            w = int(img.get('width', 0) or 0)
            h = int(img.get('height', 0) or 0)
            if (w * h) > best_area:
                best_src = src
                best_area = w * h

    # ---- 构建最终 URL ----
    if best_src:
        final_url = icon_url_from_img_src(best_src)
        # 如果最终 URL 是 sprite（BlockSprite/Invicon），改用 Special:FilePath
        url_lower = final_url.lower() if final_url else ''
        if any(kw in url_lower for kw in ['blocksprite', 'itemsprite', 'invicon', 'slotsprite']):
            safe_name = name_en.replace(' ', '_')
            return f"https://minecraft.wiki/w/Special:FilePath/{safe_name}.png"
        return final_url

    # ---- 兜底：Special:FilePath ----
    safe_name = name_en.replace(' ', '_')
    return f"https://minecraft.wiki/w/Special:FilePath/{safe_name}.png"


# ============================================
# 合成配方解析（mcui-Crafting_Table + invslot）
# ============================================

def extract_crafting_recipes(content, item_id):
    """从 mcui-Crafting_Table / invslot 结构解析合成配方（全文搜索，不限于节区）"""
    recipes = []
    seen_keys = set()

    # 全文搜索：避免节区边界判断错误导致丢失配方
    mcui_blocks = content.find_all('span', class_=re.compile(r'mcui-Crafting_Table'))

    for mcui in mcui_blocks:
        recipe = parse_mcui_crafting(mcui, item_id)
        if recipe:
            # 去重：相同 pattern + result_id 视为同一配方
            key = (recipe['result_id'], recipe['result_count'],
                   tuple(tuple(row) for row in recipe['pattern']))
            if key not in seen_keys:
                seen_keys.add(key)
                recipes.append(recipe)

    return recipes


def parse_mcui_crafting(mcui, item_id):
    """解析单个 mcui-Crafting_Table 组件"""
    try:
        # 获取 3×3 输入格
        slots = mcui.find_all('span', class_='invslot')
        if not slots:
            return None

        # 只取前 9 个（3×3 网格）
        grid_slots = slots[:9]

        # 检测 shapeless: mcui 类名中包含 Shapeless
        mcui_classes = mcui.get('class', [])
        is_shapeless = any('shapeless' in c.lower() for c in mcui_classes)

        # 构建 3×3 pattern 和 ingredients
        pattern = [['', '', ''], ['', '', ''], ['', '', '']]
        ingredients = {}

        for idx, slot in enumerate(grid_slots):
            row = idx // 3
            col = idx % 3
            if row >= 3:
                break

            # 取 slot 内的第一个物品（处理 animated 多选情况取第一个）
            item_spans = slot.find_all('span', class_='invslot-item')
            if not item_spans:
                continue

            first_item = item_spans[0]
            link = first_item.find('a')
            img = first_item.find('img')

            if not link and not img:
                continue

            # 确定原料 ID 和名称
            ing_name = _parse_ingredient_name(link, img)
            if not ing_name:
                continue

            ing_id = normalize_id(ing_name)

            # 图标 URL：优先 data-src（Wiki 懒加载），回退 src
            ing_icon = ''
            src = _get_img_src(img) if img else ''
            if src:
                ing_icon = icon_url_from_img_src(src)
            if not ing_icon and link:
                ing_icon = icon_url_from_name(ing_name)

            pattern[row][col] = ing_id

            if ing_id not in ingredients:
                ingredients[ing_id] = {
                    "id": ing_id,
                    "name_zh": clean_name(ing_name),
                    "icon_url": ing_icon,
                }

        # 验证至少有一个非空格
        has_any = any(cell != '' for row in pattern for cell in row)
        if not has_any:
            return None

        # 结果：从 mcui-output 提取
        output = mcui.find('span', class_='mcui-output')
        result_icon = ''
        result_count = 1
        result_name = ''

        if output:
            result_img = output.find('img')
            result_link = output.find('a')
            if result_img:
                result_icon = icon_url_from_img_src(_get_img_src(result_img) or result_img.get('src', ''))
                # 从 output 区域的 link/img 提取结果物品名
                result_name = _parse_ingredient_name(result_link, result_img)

            # 数量：输出区域的文字 "×N" 或数字
            output_text = output.get_text(strip=True)
            count_match = re.search(r'[×x]\s*(\d+)', output_text)
            if count_match:
                result_count = int(count_match.group(1))

        # 确定实际结果 ID
        actual_result_id = normalize_id(result_name) if result_name else item_id

        # 保留所有配方 — UI 层负责筛选
        if not result_icon:
            result_icon = icon_url_from_name(actual_result_id.replace('_', ' '))

        return {
            "type": "crafting_table",
            "shaped": not is_shapeless,
            "pattern": pattern,
            "ingredients": ingredients,
            "result_id": actual_result_id,
            "result_icon": result_icon,
            "result_count": result_count,
            # 元数据：用于 UI 筛选
            "result_match": actual_result_id == item_id,
            "is_primary_recipe": actual_result_id == item_id,
        }

    except Exception as e:
        print(f"    [PARSE-ERR] mcui crafting: {e}")
        return None


# ============================================
# 烧炼配方（支持多配方 + 经验/时间提取）
# ============================================

def extract_smelting_recipes(content, item_id):
    """从页面提取所有烧炼配方（熔炉/高炉/烟熏炉），返回列表（全文搜索）"""
    recipes = []
    seen_keys = set()

    for mcui_cls in ['mcui-Furnace', 'mcui-Blast_Furnace', 'mcui-Smoker']:
        mcui_blocks = content.find_all('span', class_=re.compile(mcui_cls))
        for mcui in mcui_blocks:
            recipe = _parse_mcui_smelting(mcui, item_id)
            if recipe:
                key = (recipe['type'], recipe['input_id'], recipe['output_id'])
                if key not in seen_keys:
                    seen_keys.add(key)
                    recipes.append(recipe)

    return recipes if recipes else None


def _parse_mcui_smelting(mcui, item_id):
    """解析单个 mcui 烧炼组件"""
    try:
        input_slot = mcui.find('span', class_='mcui-input')
        if not input_slot:
            return None

        input_link = input_slot.find('a')
        input_img = input_slot.find('img')
        input_src = _get_img_src(input_img) if input_img else ''
        input_name = _parse_ingredient_name(input_link, input_img)
        input_id = normalize_id(input_name) if input_name else 'unknown'

        # 燃料
        fuel_slot = mcui.find('span', class_='mcui-fuel')
        fuel_name = '任意燃料'
        fuel_icon = ''
        if fuel_slot:
            fuel_link = fuel_slot.find('a')
            fuel_img = fuel_slot.find('img')
            if fuel_link:
                fuel_name = fuel_link.get('title', fuel_link.get_text(strip=True)) or fuel_name
            if fuel_img:
                fuel_icon = icon_url_from_img_src(_get_img_src(fuel_img) or fuel_img.get('src', ''))

        # 输出
        output_slot = mcui.find('span', class_='mcui-output')
        output_name = ''
        output_icon = ''
        output_count = 1
        if output_slot:
            out_link = output_slot.find('a')
            out_img = output_slot.find('img')
            output_name = _parse_ingredient_name(out_link, out_img)
            if out_img:
                output_icon = icon_url_from_img_src(_get_img_src(out_img) or out_img.get('src', ''))
            out_text = output_slot.get_text(strip=True)
            m = re.search(r'[×x]\s*(\d+)', out_text)
            if m:
                output_count = int(m.group(1))

        actual_output_id = normalize_id(output_name) if output_name else item_id
        if not output_icon:
            output_icon = icon_url_from_name(actual_output_id.replace('_', ' '))

        # 从 mcui 类名推断炉子类型
        mcui_classes = ' '.join(mcui.get('class', []))
        if 'Blast' in mcui_classes:
            furnace_type = 'blast_furnace'
            cook_time = 5  # 高炉速度是熔炉2倍
        elif 'Smoker' in mcui_classes:
            furnace_type = 'smoker'
            cook_time = 5
        else:
            furnace_type = 'furnace'
            cook_time = 10

        # 尝试从标题文字提取经验值
        experience = 0.1
        parent_text = ''
        parent = mcui.parent
        if parent:
            parent_text = parent.get_text(' ', strip=True)[:500]
            exp_match = re.search(r'(\d+\.?\d*)\s*(?:经验|experience|xp)', parent_text, re.IGNORECASE)
            if exp_match:
                experience = float(exp_match.group(1))

        return {
            "type": furnace_type,
            "input_id": input_id,
            "input_icon": icon_url_from_img_src(input_src) if input_src else '',
            "fuel": fuel_name,
            "fuel_icon": fuel_icon,
            "output_id": actual_output_id,
            "output_icon": output_icon,
            "output_count": output_count,
            "experience": experience,
            "cook_time_seconds": cook_time,
        }
    except Exception as e:
        print(f"    [PARSE-ERR] mcui smelting: {e}")
        return None


# ============================================
# 切石机配方（mcui-Stonecutter）
# ============================================

def extract_stonecutting_recipes(content, item_id):
    """从页面提取切石机配方（全文搜索）"""
    recipes = []
    seen_keys = set()

    mcui_blocks = content.find_all('span', class_=re.compile(r'mcui-Stonecutter'))
    for mcui in mcui_blocks:
        recipe = _parse_mcui_stonecutting(mcui, item_id)
        if recipe:
            key = (recipe['input_id'], recipe['output_id'])
            if key not in seen_keys:
                seen_keys.add(key)
                recipes.append(recipe)

    return recipes


def _parse_mcui_stonecutting(mcui, item_id):
    """解析单个 mcui-Stonecutter 组件"""
    try:
        input_slot = mcui.find('span', class_='mcui-input')
        if not input_slot:
            return None

        input_link = input_slot.find('a')
        input_img = input_slot.find('img')
        input_src = _get_img_src(input_img) if input_img else ''
        input_name = _parse_ingredient_name(input_link, input_img)
        input_id = normalize_id(input_name) if input_name else 'unknown'
        input_icon = icon_url_from_img_src(input_src) if input_src else ''

        output_slot = mcui.find('span', class_='mcui-output')
        output_name = ''
        output_icon = ''
        output_count = 1
        if output_slot:
            out_link = output_slot.find('a')
            out_img = output_slot.find('img')
            output_name = _parse_ingredient_name(out_link, out_img)
            if out_img:
                output_icon = icon_url_from_img_src(_get_img_src(out_img) or out_img.get('src', ''))
            out_text = output_slot.get_text(strip=True)
            m = re.search(r'[×x]\s*(\d+)', out_text)
            if m:
                output_count = int(m.group(1))

        actual_output_id = normalize_id(output_name) if output_name else item_id
        if not output_icon:
            output_icon = icon_url_from_name(actual_output_id.replace('_', ' '))

        return {
            "type": "stonecutting",
            "input_id": input_id,
            "input_icon": input_icon,
            "output_id": actual_output_id,
            "output_icon": output_icon,
            "output_count": output_count,
        }
    except Exception as e:
        print(f"    [PARSE-ERR] mcui stonecutting: {e}")
        return None


# ============================================
# 锻造台配方（mcui-Smithing_Table / Smithing）
# ============================================

def extract_smithing_recipes(content, item_id):
    """从页面提取锻造台配方（全文搜索）"""
    recipes = []
    seen_keys = set()

    mcui_blocks = content.find_all('span', class_=re.compile(r'mcui-Smithing'))
    for mcui in mcui_blocks:
        recipe = _parse_mcui_smithing(mcui, item_id)
        if recipe:
            key = (recipe.get('template_id'), recipe.get('base_id'),
                   recipe.get('addition_id'), recipe.get('output_id'))
            if key not in seen_keys:
                seen_keys.add(key)
                recipes.append(recipe)

    return recipes


def _parse_mcui_smithing(mcui, item_id):
    """
    解析单个 mcui-Smithing 组件。
    锻造台有3个输入槽：template + base + addition → result
    """
    try:
        slots = mcui.find_all('span', class_='invslot')
        if len(slots) < 3:
            return None

        def _extract_slot(slot_elem):
            link = slot_elem.find('a')
            img = slot_elem.find('img')
            name = _parse_ingredient_name(link, img)
            src = _get_img_src(img) if img else ''
            icon = icon_url_from_img_src(src) if src else ''
            return normalize_id(name) if name else '', name or '', icon

        # 3个输入槽（顺序：template, base, addition）
        template_id, template_name, template_icon = _extract_slot(slots[0])
        base_id, base_name, base_icon = _extract_slot(slots[1])
        addition_id, addition_name, addition_icon = _extract_slot(slots[2])

        if not any([template_id, base_id, addition_id]):
            return None

        # 输出
        output_slot = mcui.find('span', class_='mcui-output')
        output_name = ''
        output_icon = ''
        output_count = 1
        if output_slot:
            out_link = output_slot.find('a')
            out_img = output_slot.find('img')
            output_name = _parse_ingredient_name(out_link, out_img)
            if out_img:
                output_icon = icon_url_from_img_src(_get_img_src(out_img) or out_img.get('src', ''))
            out_text = output_slot.get_text(strip=True)
            m = re.search(r'[×x]\s*(\d+)', out_text)
            if m:
                output_count = int(m.group(1))

        actual_output_id = normalize_id(output_name) if output_name else item_id
        if not output_icon:
            output_icon = icon_url_from_name(actual_output_id.replace('_', ' '))

        return {
            "type": "smithing",
            "template_id": template_id,
            "template_icon": template_icon,
            "base_id": base_id,
            "base_icon": base_icon,
            "addition_id": addition_id,
            "addition_icon": addition_icon,
            "output_id": actual_output_id,
            "output_icon": output_icon,
            "output_count": output_count,
        }
    except Exception as e:
        print(f"    [PARSE-ERR] mcui smithing: {e}")
        return None


# ============================================
# 获取方式
# ============================================

def extract_acquisition(content, smelting_list=None, stonecutting=None, smithing=None):
    """
    从页面提取获取方式。
    优先查询各功能节区的标题是否存在，再回退到正文关键词匹配。
    """
    methods = []

    # 按节区标题精确判断（优先级高于关键词）
    section_titles = {
        '合成': ['Crafting', 'Crafting recipe', 'Crafting ingredient'],
        '自然生成': ['Natural generation', 'Generation', 'Occurrence'],
        '烧炼': ['Smelting', 'Blasting', 'Smoker', 'Cooking'],
        '切石': ['Stonecutting', 'Stonecutter'],
        '锻造': ['Smithing', 'Smithing recipe', 'Upgrading'],
        '交易': ['Trading', 'Bartering', 'Villager trades', 'Wandering trader'],
        '掉落': ['Drops', 'Loot', 'Breaking'],
        '宝箱': ['Chest loot', 'Generated loot', 'Natural generation'],
        '钓鱼': ['Fishing'],
    }

    for method_name, titles in section_titles.items():
        if find_section(content, titles):
            methods.append(method_name)

    # 补充正文关键词（处理部分页面结构异常的情况）
    text = content.get_text(' ', strip=True)[:5000].lower()

    if '合成' not in methods:
        if any(kw in text for kw in ['crafting recipe', 'shapeless crafting', 'shaped crafting']):
            methods.append('合成')

    if '自然生成' not in methods:
        if any(kw in text for kw in ['natural generation', 'naturally generated',
                                       'generates in', 'biome']):
            methods.append('自然生成')

    if '烧炼' not in methods and smelting_list:
        methods.append('烧炼')

    if '切石' not in methods and stonecutting:
        methods.append('切石')

    if '锻造' not in methods and smithing:
        methods.append('锻造')

    if '交易' not in methods:
        if any(kw in text for kw in ['trading', 'villager', 'bartering', 'piglin',
                                       'wandering trader', 'traded for']):
            methods.append('交易')

    if '宝箱' not in methods:
        if any(kw in text for kw in ['chest loot', 'dungeon', 'stronghold',
                                       'mineshaft', 'bastion', 'ruined portal']):
            methods.append('宝箱')

    if '钓鱼' not in methods:
        if any(kw in text for kw in ['fishing', 'fished', 'fishing rod']):
            methods.append('钓鱼')

    if not methods:
        methods.append('未知')

    return {"methods": methods}


def extract_natural_generation(content):
    section = find_section(content, ['Natural generation', 'Generation', 'Occurrence'])
    if not section:
        return []
    section_content = get_section_content(section)
    items = []
    for li in section_content.find_all('li'):
        text = li.get_text(strip=True)
        if 5 < len(text) < 200:
            items.append(text)
    return items[:5]


def generate_related_items(crafting, stonecutting=None, smithing=None):
    seen = set()
    related = []
    for recipe in (crafting or []):
        for ing_id in recipe.get('ingredients', {}):
            if ing_id not in seen:
                related.append(ing_id)
                seen.add(ing_id)
    for recipe in (stonecutting or []):
        ing = recipe.get('input_id', '')
        if ing and ing not in seen:
            related.append(ing)
            seen.add(ing)
    for recipe in (smithing or []):
        for key in ('template_id', 'base_id', 'addition_id'):
            ing = recipe.get(key, '')
            if ing and ing not in seen:
                related.append(ing)
                seen.add(ing)
    return related


# ============================================
# 子分类推断
# ============================================

def guess_subcategory(category, name_en, item_id):
    name_lower = name_en.lower()
    item_id_lower = item_id.lower()

    sub_map = {
        "building_blocks": [
            ("stone_blocks", ["stone", "cobblestone", "granite", "diorite", "andesite", "brick", "concrete", "terracotta", "sandstone"]),
            ("wood_blocks", ["plank", "log", "wood", "stem", "hyphae"]),
            ("glass_blocks", ["glass", "pane"]),
            ("colored_blocks", ["wool", "carpet", "concrete", "glazed", "stained"]),
        ],
        "natural_blocks": [
            ("surface", ["grass", "dirt", "sand", "gravel", "clay", "mycelium", "podzol"]),
            ("vegetation", ["leaves", "sapling", "grass", "flower", "mushroom", "vine", "crop"]),
        ],
        "functional_blocks": [
            ("workstations", ["crafting_table", "furnace", "enchant", "anvil", "brewing", "smithing", "loom", "grindstone", "cartography"]),
            ("storage", ["chest", "barrel", "shulker", "ender"]),
            ("utility", ["torch", "ladder", "bed", "door", "trapdoor", "fence_gate", "button", "sign", "bell"]),
            ("mechanisms", ["piston", "dispenser", "dropper", "observer", "hopper", "redstone"]),
        ],
        "tools": [
            ("pickaxes", ["pickaxe"]),
            ("axes", ["axe"]),
            ("shovels", ["shovel"]),
            ("hoes", ["hoe"]),
            ("other_tools", ["shears", "flint", "fishing_rod", "brush", "lead", "bucket"]),
        ],
        "combat": [
            ("swords", ["sword", "mace"]),
            ("ranged", ["bow", "crossbow", "arrow", "trident"]),
            ("armor", ["helmet", "chestplate", "leggings", "boots", "shield"]),
        ],
        "food": [
            ("crops", ["apple", "carrot", "potato", "beetroot", "melon", "berries", "wheat", "bread"]),
            ("meat", ["beef", "porkchop", "chicken", "mutton", "rabbit", "fish", "salmon", "cod"]),
            ("prepared", ["cake", "pie", "soup", "stew", "cooked"]),
        ],
        "materials": [
            ("ores_ingots", ["ore", "ingot", "diamond", "emerald", "coal", "nugget", "gem"]),
            ("organic", ["leather", "paper", "feather", "string", "bone", "slime", "gunpowder"]),
        ],
        "miscellaneous": [
            ("discs", ["music_disc", "disc"]),
            ("decor", ["banner", "pattern", "frame", "painting"]),
            ("transport", ["boat", "minecart", "rail"]),
            ("utility_items", ["book", "map", "compass", "clock", "bottle", "bucket", "saddle", "name_tag"]),
        ],
    }

    options = sub_map.get(category, [("general", [])])

    best_match = None
    best_len = 0
    for sub_id, keywords in options:
        for kw in keywords:
            if kw in item_id_lower and len(kw) > best_len:
                best_match = sub_id
                best_len = len(kw)

    if best_match:
        return best_match
    return "general"


# ============================================
# 节区导航
# ============================================

def find_section(content, titles):
    """查找匹配标题的节区。返回 (heading_element, parent_div_or_heading)"""
    for tag in content.find_all(['h2', 'h3', 'h4']):
        if not tag.get('id'):
            continue
        span = tag.find('span', class_='mw-headline')
        text = (span or tag).get_text(strip=True)
        if not text:
            continue
        for t in titles:
            if t.lower() in text.lower():
                return tag
    return None


def get_section_content(heading):
    """
    获取节区标题后的所有内容（直到下一个同级或更高级标题）。
    兼容新旧 MediaWiki DOM 结构：
    - 旧：h2/h3 直接是兄弟节点
    - 新：div.mw-heading 包裹 h2/h3，内容在 div 之后
    """
    container = BeautifulSoup('', 'lxml')
    h_level = int(heading.name[1])

    # 判断是否在新版 mw-heading 结构中
    parent = heading.parent
    in_mw_heading = parent and parent.name == 'div' and 'mw-heading' in ' '.join(parent.get('class', []))

    if in_mw_heading:
        # 新版结构：内容紧跟 mw-heading div
        start_tag = parent
    else:
        # 旧版结构：内容紧跟 heading 自身
        start_tag = heading

    tag = start_tag.find_next_sibling()
    while tag:
        if not hasattr(tag, 'name') or not tag.name:
            tag = tag.find_next_sibling()
            continue

        # 检测新版的 mw-heading div
        tag_classes = ' '.join(tag.get('class', []))
        tag_level = None
        if tag.name == 'div' and 'mw-heading' in tag_classes:
            # 提取级别：mw-heading2 → 2, mw-heading3 → 3
            import re
            m = re.search(r'mw-heading(\d)', tag_classes)
            if m:
                tag_level = int(m.group(1))
        elif tag.name in ('h2', 'h3', 'h4'):
            tag_level = int(tag.name[1])

        if tag_level is not None and tag_level <= h_level:
            break

        container.append(tag)
        tag = tag.find_next_sibling()

    return container
