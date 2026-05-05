# ============================================
# utils.py — 工具函数
# ============================================

import re
import os
import hashlib
from config import CACHE_DIR

def normalize_id(name):
    """
    最小规范化：仅做格式统一，不做语义合并。

    规则:
      1. 去掉 namespace 前缀（File:, Template:, Category:, minecraft:）
      2. 去掉 URL 锚点 (#...)
      3. 去掉括号说明 ONLY IF 属于非物品描述
         (block) (item) (disambiguation) — 去掉
         保留有语义的括号内容
      4. 空格 / 连字符 → 下划线
      5. 全小写

    严格禁止:
      - 不允许删除颜色前缀 (white_, red_, blue_, ...)
      - 不允许删除木种 (oak_, spruce_, birch_, ...)
      - 不允许语义归类 (如所有 wool 归为 wool)
    """
    if not name:
        return ''
    s = name.strip()

    # 1. 去掉 namespace 前缀
    for ns in ('minecraft:', 'file:', 'template:', 'category:', 'module:', 'special:'):
        if s.lower().startswith(ns):
            s = s[len(ns):]

    # 2. 去掉锚点
    if '#' in s:
        s = s.split('#')[0]

    # 3. 仅去除非物品描述型括号
    #    "(block)", "(item)", "(disambiguation)", "(disambiguation page)", "(material)" etc.
    _non_item_parens = [
        r'\s*\(block\)', r'\s*\(item\)', r'\s*\(disambiguation\)',
        r'\s*\(disambiguation page\)', r'\s*\(material\)', r'\s*\(substance\)',
        r'\s*\(mechanic\)', r'\s*\(status effect\)', r'\s*\(effect\)',
        r'\s*\(achievement\)', r'\s*\(advancement\)', r'\s*\(biome\)',
        r'\s*\(mob\)', r'\s*\(entity\)', r'\s*\(structure\)',
    ]
    for pat in _non_item_parens:
        s = re.sub(pat, '', s, flags=re.IGNORECASE)

    # 4. 空格 / 连字符 → 下划线
    s = re.sub(r'[\s\-]+', '_', s)

    # 5. 只保留字母数字和下划线
    s = re.sub(r'[^a-zA-Z0-9_]', '', s)

    # 6. 全小写
    return s.lower()

def slugify(title):
    """从页面 title 生成 URL slug"""
    return title.strip().replace(' ', '_')

def cache_path(url_or_slug):
    """生成缓存文件路径"""
    h = hashlib.md5(url_or_slug.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{h}.html")

def load_cache(url_or_slug):
    """读取缓存的 HTML"""
    path = cache_path(url_or_slug)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def save_cache(url_or_slug, html):
    """写入缓存"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = cache_path(url_or_slug)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

def icon_url_from_name(item_name):
    """根据物品英文名构造图标 URL"""
    name = item_name.strip()
    name = name.replace(' ', '_')
    # 首字母大写（每词）
    parts = name.split('_')
    parts = [p[0].upper() + p[1:] if p else p for p in parts]
    filename = '_'.join(parts)
    return f"https://minecraft.wiki/images/{filename}.png"

def icon_url_from_img_src(src):
    """从 img src 属性构造完整 URL（含 thumb 标准化）"""
    if not src:
        return None
    url = src.strip()

    # 处理 data-src（lazy load）
    if url.startswith('data:'):
        return None

    # /thumb/ 标准化 → 去掉缩略图路径
    url = normalize_icon(url)

    if url.startswith('//'):
        return f"https:{url}"
    if url.startswith('/'):
        return f"https://minecraft.wiki{url}"
    if url.startswith('http'):
        return url
    return f"https://minecraft.wiki/images/{url}"


def normalize_icon(url):
    """
    标准化 Wiki 图片 URL — 将缩略图/archive路径还原为原始图片，保留 CDN hash 目录。

    规则:
      /images/thumb/X/XX/File.png/NNpx-File.png  → /images/X/XX/File.png   (保留 hash)
      /images/thumb/File.png/NNpx-File.png       → /images/File.png         (无 hash)
      /images/archive/X/XX/ts!File.png           → /images/X/XX/File.png    (保留 hash)
      /images/X/XX/File.png                       → 保持原样
      /images/File.png                            → 保持原样
    """
    if not url:
        return url

    # 保留 query string (cache buster)
    qs = ''
    if '?' in url:
        url, qs_part = url.split('?', 1)
        qs = '?' + qs_part
    if '#' in url:
        url = url.split('#')[0]

    # SVG / Special:FilePath / File: 保持原样
    if url.endswith('.svg'):
        return url + qs
    if 'Special:FilePath' in url or 'File:' in url:
        return url

    # --- 模式 1: /thumb/ 缩略图路径 ---
    if '/thumb/' in url:
        # /images/thumb/[HASH/]File.png/NNpx-File.png
        after = url.split('/thumb/')[1]
        parts = after.split('/')

        # 找到实际文件名（第一个带扩展名的非 px 部分）
        hash_parts = []
        filename = None
        for part in parts:
            has_ext = any(ext in part.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'])
            is_thumb = 'px' in part.lower()

            if has_ext and not is_thumb:
                filename = part
                break
            elif not has_ext and len(part) <= 2:
                # 单/双字符 → hash 目录
                hash_parts.append(part)
            # has_ext and is_thumb → 跳过（如 "150px-Stone.png"）

        if filename:
            if hash_parts:
                return '/images/' + '/'.join(hash_parts) + '/' + filename + qs
            return '/images/' + filename + qs

        # 回退：找第一个带扩展名的
        for part in parts:
            if any(ext in part.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                if 'px' not in part.lower():
                    return '/images/' + part + qs
        # 实在找不到
        return url + qs

    # --- 模式 2: /archive/ 归档路径 ---
    if '/archive/' in url:
        # /images/archive/[HASH/]timestamp!File.png
        after = url.split('/archive/')[1]
        parts = after.split('/')
        hash_parts = []
        filename = None
        for part in parts:
            if '!' in part:
                filename = part.split('!')[-1]
                break
            elif len(part) <= 2:
                hash_parts.append(part)
        if filename:
            if hash_parts:
                return '/images/' + '/'.join(hash_parts) + '/' + filename + qs
            return '/images/' + filename + qs

    # --- 模式 3: 已有 /images/ 路径 → 保持原样 ---
    if url.startswith('/images/'):
        return url + qs

    # 不做改动
    return url + qs

def extract_page_title_from_url(url):
    """从 URL 提取页面标题"""
    # https://minecraft.wiki/w/Stone → Stone
    parts = url.rstrip('/').split('/')
    title = parts[-1] if parts else ''
    return title.replace('_', ' ')

def is_item_url(url):
    """判断 URL 是否为物品页面"""
    from config import SKIP_PATTERNS
    if not url or not isinstance(url, str):
        return False
    if '/w/' not in url:
        return False
    for pattern in SKIP_PATTERNS:
        if pattern in url:
            return False
    # Must have a path component after /w/
    parts = url.rstrip('/').split('/')
    slug = parts[-1] if parts else ''
    if not slug or len(slug) < 2:
        return False
    # Skip pages with these keywords in slug
    skip_keywords = ['edition', 'update', 'tutorial', 'guide', 'list', 'comparison']
    slug_lower = slug.lower()
    for kw in skip_keywords:
        if kw in slug_lower:
            return False
    return True

def smart_truncate(text, max_len=100):
    """智能截断文本"""
    if not text or len(text) <= max_len:
        return text
    return text[:max_len] + '...'
