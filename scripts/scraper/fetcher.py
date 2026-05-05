# ============================================
# fetcher.py — HTTP 请求（curl_cffi + 重试 + 限速）
# ============================================

import time
import random
from curl_cffi import requests
from utils import load_cache, save_cache

# 浏览器指纹伪装（Chrome 124 TLS 指纹）
IMPERSONATE = "chrome124"

# 轮换 UA 列表（作为后备）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

_last_request_time = 0
_stats = {"success": 0, "retry": 0, "blocked": 0, "fail": 0}

# robots.txt 缓存
_robots_disallowed = None


def check_robots(base_url="https://minecraft.wiki"):
    """
    下载并缓存 robots.txt，提取 Disallow 规则。
    plan.md §9 安全限制 #3
    """
    global _robots_disallowed
    if _robots_disallowed is not None:
        return _robots_disallowed

    _robots_disallowed = []
    try:
        robots_url = f"{base_url}/robots.txt"
        res = requests.get(robots_url, headers={"User-Agent": USER_AGENTS[0]}, timeout=10)
        if res.status_code == 200:
            for line in res.text.splitlines():
                line = line.strip()
                if line.lower().startswith('disallow:'):
                    path = line.split(':', 1)[1].strip()
                    if path:
                        _robots_disallowed.append(path)
            print(f"[ROBOTS] Loaded {len(_robots_disallowed)} disallow rules from {robots_url}")
    except Exception as e:
        print(f"[ROBOTS] Failed to fetch: {e} — proceeding without restrictions")
    return _robots_disallowed


def is_url_allowed(url):
    """检查 URL 是否被 robots.txt 禁止"""
    disallowed = check_robots()
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path
    for rule in disallowed:
        if path.startswith(rule):
            print(f"[ROBOTS] BLOCKED by rule '{rule}': {path}")
            return False
    return True


def rate_limit():
    global _last_request_time
    from config import MIN_DELAY, MAX_DELAY
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    elapsed = time.time() - _last_request_time
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_request_time = time.time()


def fetch_html(url, use_cache=True):
    """
    获取页面 HTML。
    优先读缓存，否则 curl_cffi 请求（Chrome TLS 指纹伪装）。
    最多 3 次重试，指数退避。返回 HTML 字符串，失败返回 None。
    """
    if use_cache:
        cached = load_cache(url)
        if cached:
            return cached

    slug = url.rstrip('/').split('/')[-1]
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    for attempt in range(3):
        try:
            rate_limit()
            res = requests.get(
                url,
                impersonate=IMPERSONATE,
                headers=headers,
                timeout=15,
            )

            if res.status_code == 200:
                html = res.text

                # Cloudflare 二次验证检测
                if "cf-browser-verification" in html or "cf-challenge" in html.lower():
                    _stats["blocked"] += 1
                    wait = (attempt + 1) * 5
                    print(f"[FETCH] BLOCKED (CF): /{slug} (attempt {attempt + 1}/3, wait {wait}s)")
                    time.sleep(wait)
                    continue

                _stats["success"] += 1
                print(f"[FETCH] OK 200: /{slug}")
                save_cache(url, html)
                return html

            elif res.status_code in (403, 429):
                wait = (attempt + 1) * 5
                print(f"[FETCH] {res.status_code}: /{slug} (attempt {attempt + 1}/3, wait {wait}s)")
                _stats["retry"] += 1
                time.sleep(wait)

            elif res.status_code == 404:
                print(f"[FETCH] 404 SKIP: /{slug}")
                return None

            else:
                wait = (attempt + 1) * 2
                print(f"[FETCH] {res.status_code}: /{slug} (attempt {attempt + 1}/3, wait {wait}s)")
                time.sleep(wait)

        except Exception as e:
            wait = (attempt + 1) * 3
            print(f"[FETCH] RETRY {attempt + 1}/3: /{slug} ({e})")
            time.sleep(wait)

    _stats["fail"] += 1
    print(f"[FETCH] FAIL: /{slug} (3 attempts exhausted)")
    return None


def fetch_page_by_slug(slug, use_cache=True):
    url = f"https://minecraft.wiki/w/{slug}"
    return fetch_html(url, use_cache)


def fetch_raw_page(slug, use_cache=True):
    url = f"https://minecraft.wiki/w/{slug}?action=raw"
    return fetch_html(url, use_cache)


def fetch_api_page(slug, use_cache=True):
    url = f"https://minecraft.wiki/api/rest_v1/page/html/{slug}"
    return fetch_html(url, use_cache)


def clear_rate_limit():
    global _last_request_time
    _last_request_time = 0


def get_stats():
    return dict(_stats)


def reset_stats():
    for k in _stats:
        _stats[k] = 0
