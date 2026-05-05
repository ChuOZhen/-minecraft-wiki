# ============================================
# parser_list.py — 从 Item 列表页解析物品链接
# ============================================

import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from config import ITEM_LIST_URL, BASE_URL, CATEGORY_KEYWORDS
from utils import is_item_url, extract_page_title_from_url
from fetcher import fetch_html


def fetch_item_list():
    """从 Item 页面抓取所有物品链接"""
    html = fetch_html(ITEM_LIST_URL)
    if not html:
        print("Failed to fetch item list page")
        return []

    soup = BeautifulSoup(html, 'lxml')
    links = set()

    # 查找主内容区所有链接
    content = soup.find('div', id='mw-content-text')
    if not content:
        content = soup.find('div', class_='mw-parser-output')
    if not content:
        content = soup

    for a in content.find_all('a', href=True):
        href = a['href'].strip()
        # 跳过片段和外部链接
        if href.startswith('#') or href.startswith('http') and 'minecraft.wiki' not in href:
            continue
        # 转为绝对 URL
        full_url = urljoin(BASE_URL, href)
        if is_item_url(full_url):
            links.add(full_url)

    items = sorted(links)
    print(f"Found {len(items)} potential item URLs")
    return items


def categorize_by_keywords(text):
    """根据文本关键词推断分类"""
    text_lower = text.lower()
    scores = {}
    for cat_id, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text_lower:
                score += 1
        if score > 0:
            scores[cat_id] = score
    if scores:
        return max(scores, key=scores.get)
    return "miscellaneous"


def parse_page_categories(soup):
    """解析页面底部的分类标签"""
    cats = []
    catlinks = soup.find('div', id='mw-normal-catlinks')
    if not catlinks:
        catlinks = soup.find('div', id='catlinks')
    if catlinks:
        for a in catlinks.find_all('a'):
            text = a.get_text(strip=True)
            if text and not text.startswith('Pages using'):
                cats.append(text)
    return cats


def get_category_from_wiki_cats(wiki_cats):
    """将 Wiki 分类映射到项目大类 — 基于 Category Graph 规则"""
    from category_crawler import classify_item
    if not wiki_cats:
        return "miscellaneous"
    cat_id, sub_id, conf = classify_item('', wiki_cats)
    return cat_id


def get_subcategory_from_wiki_cats(wiki_cats):
    """将 Wiki 分类映射到项目小类"""
    from category_crawler import classify_item
    if not wiki_cats:
        return "general"
    cat_id, sub_id, conf = classify_item('', wiki_cats)
    return sub_id


# Wiki 分类黑名单 — 仅拒绝明确非物品页面
# 策略调整 (2026-05-03): 先解析再判断，仅保留三类拦截:
#   1. April Fools / 玩笑内容
#   2. 消歧义页面
#   3. 明确非物品页面（命令、教程、版本页等）
# historical, bedrock, entities 等不再直接拒绝，改为在解析后按实际数据质量过滤
_REJECT_CATEGORIES = [
    # April Fools / Joke
    'april fools', 'april fools joke', 'joke features', 'joke feature',
    'april fools 2025', 'april fools 2024', 'april fools 2023',
    'poisonous potato dimension', 'potato dimension',
    'cinnabar', 'sulfur',
    'golden nautilus armor', 'nautilus armor',
    'hash browns',
    # Disambiguation
    'disambiguation', 'disambiguation pages',
    # Non-item: commands
    'commands', 'command blocks only',
    # Non-item: tutorials / guides / version pages (these are not items)
    'tutorials', 'guides',
    # World generation UI / non-item
    'biome vote', 'mob vote',
    'single biome', 'buffet', 'custom world',
    'superflat', 'flat world',
]


def is_reject_page(wiki_cats):
    """
    检查 Wiki 分类是否属于应过滤的页面类型。
    返回 (should_reject: bool, reason: str)

    三级过滤:
      1. 黑名单关键词匹配（April Fools / disambiguation / commands / guides）
      2. 实体/概念页检测：在 Entities/Mobs 分类但不在 Items/Blocks/Food 分类 → 拒绝
      3. 无任何物品分类标签 → 可疑，但仍放行（让 parse_item_page 尝试解析）
    """
    if not wiki_cats:
        return (False, '')

    cat_text = ' '.join(wiki_cats).lower()

    # 第 1 层：黑名单关键词
    for kw in _REJECT_CATEGORIES:
        if kw in cat_text:
            return (True, kw)

    # 第 2 层：实体/概念页检测
    # 如果页面在 Entities/Mobs/Game mechanics/Environment 分类，但不在 Items/Blocks/Food 分类 → 拒绝
    entity_kw = ['entities', 'mobs', 'hostile creatures', 'passive creatures',
                 'neutral creatures', 'boss creatures', 'animal', 'villager',
                 'game mechanics', 'gameplay', 'environment', 'weather', 'dimensions',
                 'the nether', 'the end', 'overworld', 'biomes']
    item_kw = ['items', 'blocks', 'food', 'tools', 'weapons', 'armor',
               'materials', 'dyes', 'spawn eggs', 'music discs', 'potions']

    has_entity = any(kw in cat_text for kw in entity_kw)
    has_item = any(kw in cat_text for kw in item_kw)

    if has_entity and not has_item:
        return (True, 'entity/concept page (no item/block/food category)')

    return (False, '')
