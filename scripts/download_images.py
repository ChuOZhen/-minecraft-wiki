#!/usr/bin/env python3
"""
download_images.py — 批量下载所有 icon_url 到 docs/images/，彻底消除跨域依赖。

用法: python download_images.py
输出: docs/images/ 目录 + 更新后的 data.json + image_map.json
"""
import json
import os
import sys
import time
import hashlib
import subprocess
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH   = SCRIPT_DIR / 'docs' / 'data' / 'data.json'
IMAGES_DIR  = SCRIPT_DIR / 'docs' / 'images'
MAP_PATH    = SCRIPT_DIR / 'docs' / 'data' / 'image_map.json'
FAILED_LOG  = SCRIPT_DIR / 'download_failed.log'

IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def url_to_filename(url):
    """从 URL 提取稳定文件名。去掉 query、转小写、空格→下划线。"""
    # 去掉 query string
    clean = url.split('?')[0]
    # 提取最后一段文件名
    filename = clean.rstrip('/').split('/')[-1]
    if not filename:
        return None
    # 转小写，空格→_
    filename = filename.lower().replace(' ', '_')
    # 去掉非 ASCII 兼容字符（保留字母数字 . _ -）
    filename = re.sub(r'[^a-z0-9._\-]', '', filename)
    # 去掉连续的点/下划线
    filename = re.sub(r'\.+', '.', filename)
    filename = re.sub(r'_+', '_', filename)
    if not filename or len(filename) < 3:
        return None
    return filename


def ensure_unique(name, used_names):
    """如果文件名冲突，追加短 hash。"""
    if name not in used_names:
        used_names.add(name)
        return name
    # 用原始 URL 的 hash 区分
    base, ext = os.path.splitext(name)
    # 尝试加计数器
    for i in range(1, 100):
        candidate = f'{base}_{i}{ext}'
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
    # fallback: hash
    h = hashlib.md5(name.encode()).hexdigest()[:6]
    candidate = f'{base}_{h}{ext}'
    used_names.add(candidate)
    return candidate


def is_image_file(path):
    """检查文件是否为真实图片（非 HTML/错误页）。"""
    try:
        with open(path, 'rb') as f:
            header = f.read(16)
        # PNG
        if header[:8] == b'\x89PNG\r\n\x1a\n': return True
        # JPEG
        if header[:3] == b'\xff\xd8\xff': return True
        # GIF
        if header[:6] in (b'GIF87a', b'GIF89a'): return True
        # WebP
        if header[:4] == b'RIFF' and header[8:12] == b'WEBP': return True
        # SVG (text)
        if b'<svg' in header.lower() or b'<?xml' in header: return True
        return False
    except Exception:
        return False


def download_one(url, dest_path):
    """用 curl 下载，验证图片真实性，最多重试 4 次（递增延迟）。"""
    delays = [0, 2, 5, 10]
    for attempt in range(len(delays)):
        if attempt > 0:
            time.sleep(delays[attempt])
        try:
            # FIX: 不设自定义 UA。裸 curl UA 不会被 Cloudflare 拦截，伪装 Chrome 反而 403
            result = subprocess.run([
                'curl', '-s', '-o', str(dest_path), '-w', '%{http_code}',
                '-L', '--max-time', '20',
                url
            ], capture_output=True, text=True, timeout=30)

            http_code = result.stdout.strip()
            if http_code == '200' and dest_path.stat().st_size > 100 and is_image_file(dest_path):
                return True
            # 删除无效文件
            if dest_path.exists():
                dest_path.unlink()
        except Exception:
            if dest_path.exists():
                try: dest_path.unlink()
                except: pass
    return False


def collect_all_urls(data):
    """收集所有 icon URL 及其来源信息。"""
    url_map = {}  # url → [item_ids]

    for item in data.get('items', []):
        item_id = item.get('id', '?')
        urls = []

        # 主图标
        u = item.get('icon_url')
        if u: urls.append(('icon', u))

        # 合成配方
        for ci, recipe in enumerate(item.get('crafting') or []):
            u = recipe.get('result_icon')
            if u: urls.append((f'crafting[{ci}].result', u))
            for key, ing in (recipe.get('ingredients') or {}).items():
                u = ing.get('icon_url')
                if u: urls.append((f'crafting[{ci}].ingredients.{key}', u))

        for field, url in urls:
            if url not in url_map:
                url_map[url] = []
            url_map[url].append(f'{item_id}:{field}')

    return url_map


def replace_urls_in_data(data, url_to_local):
    """将 data 中所有 icon_url 替换为本地路径。"""
    changes = 0
    for item in data.get('items', []):
        old = item.get('icon_url')
        if old and old in url_to_local:
            item['icon_url'] = url_to_local[old]
            changes += 1

        for recipe in (item.get('crafting') or []):
            old = recipe.get('result_icon')
            if old and old in url_to_local:
                recipe['result_icon'] = url_to_local[old]
                changes += 1
            for ing in (recipe.get('ingredients') or {}).values():
                old = ing.get('icon_url')
                if old and old in url_to_local:
                    ing['icon_url'] = url_to_local[old]
                    changes += 1
    return changes


def main():
    print('=' * 60)
    print('Minecraft Items — 图片本地化下载')
    print('=' * 60)

    # 1. 加载数据
    print(f'\n[1] 加载 {DATA_PATH} ...')
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. 收集所有 URL
    print('[2] 收集所有 icon_url ...')
    url_map = collect_all_urls(data)
    unique_urls = list(url_map.keys())
    print(f'    唯一 URL: {len(unique_urls)}')

    # 3. URL → 本地文件名映射
    print('[3] 生成 URL → 本地文件名映射 ...')
    used_names = set()
    # 先扫描已有文件
    if IMAGES_DIR.exists():
        for f in IMAGES_DIR.iterdir():
            if f.is_file():
                used_names.add(f.name.lower())

    url_to_local = {}
    name_conflicts = 0

    for url in unique_urls:
        name = url_to_filename(url)
        if not name:
            name = f'image_{hashlib.md5(url.encode()).hexdigest()[:8]}.png'

        unique_name = ensure_unique(name, used_names)
        if unique_name != name:
            name_conflicts += 1

        url_to_local[url] = f'images/{unique_name}'

    print(f'    文件名冲突: {name_conflicts}')

    # 4. 下载
    print(f'[4] 下载 {len(unique_urls)} 个图片到 {IMAGES_DIR} ...')
    print(f'    (预计 {len(unique_urls) // 30} 分钟，限速 1s/请求)')

    success = 0
    failed_urls = []

    for i, url in enumerate(unique_urls, 1):
        local_path_rel = url_to_local[url]
        dest = IMAGES_DIR / os.path.basename(local_path_rel)

        # 跳过已成功下载的
        if dest.exists() and dest.stat().st_size > 100 and is_image_file(dest):
            success += 1
            if i % 200 == 0:
                print(f'    [{i}/{len(unique_urls)}] 成功={success} (已缓存)', flush=True)
            continue

        ok = download_one(url, dest)
        if ok:
            success += 1
        else:
            failed_urls.append(url)
            if dest.exists():
                dest.unlink()

        if i % 50 == 0:
            print(f'    [{i}/{len(unique_urls)}] 成功={success} 失败={len(failed_urls)}', flush=True)

        # 限速
        time.sleep(1.0)

    print(f'\n    下载完成: 成功={success} 失败={len(failed_urls)}')

    # 5. 记录失败
    if failed_urls:
        with open(FAILED_LOG, 'w', encoding='utf-8') as f:
            for url in failed_urls:
                f.write(f'{url}\n')
                # 也写来源
                for src in url_map.get(url, []):
                    f.write(f'  used by: {src}\n')
        print(f'    失败日志: {FAILED_LOG}')

    # 6. 生成 image_map.json
    print('[5] 生成 image_map.json ...')
    with open(MAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(url_to_local, f, ensure_ascii=False, indent=2)
    print(f'    映射表: {MAP_PATH} ({len(url_to_local)} 条)')

    # 7. 更新 data.json
    print('[6] 更新 data.json → 本地路径 ...')
    changes = replace_urls_in_data(data, url_to_local)
    print(f'    替换字段: {changes}')

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    # 8. 最终统计
    total_files = sum(1 for _ in IMAGES_DIR.iterdir() if _.is_file())
    total_size = sum(_.stat().st_size for _ in IMAGES_DIR.iterdir() if _.is_file())
    print(f'\n    docs/images/: {total_files} 文件, {total_size / 1024 / 1024:.1f} MB')
    print(f'    data.json: {os.path.getsize(DATA_PATH) / 1024:.0f} KB')

    # 9. 验证
    print('\n[7] 验证 ...')
    sample_ok = 0
    sample_total = 0
    for item in data.get('items', [])[:20]:
        url = item.get('icon_url', '')
        if url.startswith('images/'):
            fpath = IMAGES_DIR / os.path.basename(url)
            if fpath.exists() and fpath.stat().st_size > 100:
                sample_ok += 1
            sample_total += 1
    print(f'    前 20 项本地图片可达: {sample_ok}/{sample_total}')

    # 检查是否还有远程 URL
    remote_count = 0
    for item in data.get('items', []):
        if item.get('icon_url', '').startswith('http'):
            remote_count += 1
    print(f'    残留远程 URL: {remote_count}')

    print('\n' + '=' * 60)
    print('完成。刷新 http://localhost:8080 查看效果。')
    print('=' * 60)


if __name__ == '__main__':
    main()
