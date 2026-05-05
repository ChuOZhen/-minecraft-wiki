#!/usr/bin/env python3
# ============================================
# main.py — 爬虫入口，协调全流程
# ============================================
#
# 用法: python scraper/main.py [--limit N] [--resume] [--no-cache]
#
# 流程:
#   Step 1: 获取物品 URL 列表
#   Step 2: 逐页抓取并解析
#   Step 3: 数据规范化
#   Step 4: 构建分类结构
#   Step 5: 质量验证
#   Step 6: 写入 data.json
# ============================================

import sys
import os
import argparse
import random
import json
import datetime

# 确保能 import 同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CACHE_DIR
from fetcher import fetch_html, clear_rate_limit
from parser_list import fetch_item_list, is_reject_page, parse_page_categories
from parser_item import parse_item_page
from variant_expander import extract_variants, extract_spawn_egg_variants
from normalizer import (normalize_items, build_categories, validate_quality, validate_quality_report,
    apply_zh_name, get_zh_name, detect_merge_issues, validate_variant_coverage,
    apply_final_fixes)
from writer import write_output, write_fallback_snapshot

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'data', 'data.json')
FALLBACK_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'data', 'data_fallback.json')
ERROR_LOG = os.path.join(os.path.dirname(__file__), 'error.log')
REJECT_LOG = os.path.join(os.path.dirname(__file__), 'reject.log')


def process_from_cache_only():
    """
    全量离线重建 data.json。
    - 仅读取 cache/ 目录下的 .html 文件
    - 禁止任何网络请求
    - 遍历全部缓存文件，逐一解析
    - 去重时优先保留有配方/有获取方式/中文名非 fallback 的版本
    """
    import glob as globmod

    cache_files = sorted(globmod.glob(os.path.join(CACHE_DIR, '*.html')))
    total_cache = len(cache_files)
    print("=" * 60)
    print(f"离线重建模式 (--from-cache-only)")
    print(f"  缓存目录: {CACHE_DIR}")
    print(f"  缓存文件数: {total_cache}")
    print("=" * 60)

    if total_cache == 0:
        print("ERROR: cache/ 目录为空，无数据可重建。")
        return 1

    errors = []
    rejected = []
    raw_items = []

    for idx, cache_path in enumerate(cache_files):
        fname = os.path.basename(cache_path)
        print(f"  [{idx + 1}/{total_cache}] {fname}...", end=' ', flush=True)

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                html = f.read()
        except Exception as e:
            print(f"READ ERROR: {e}")
            errors.append((fname, f"read error: {e}"))
            continue

        if not html or len(html) < 100:
            print("EMPTY")
            errors.append((fname, "empty or too short"))
            continue

        # 解析 item
        item = parse_item_page(html, cache_path)
        if item:
            # ---- 变体展开 ----
            variants = extract_variants(html, item)
            # Spawn Egg 特殊处理（从 wikitable 而非 infobox 提取）
            if item.get('id') == 'spawn_egg':
                variants = extract_spawn_egg_variants(html, item)
            for v in variants:
                raw_items.append(v)
            exp_str = f" → {len(variants)} variants" if len(variants) > 1 else ""
            print(f"OK (id={item.get('id','?')}, cat={item.get('category','?')}){exp_str}")
        else:
            # 检查是被过滤还是解析失败 - parse_item_page 内部打印了 SKIP 原因
            print("REJECTED/PARSE_FAILED")
            errors.append((fname, "parse returned None (likely rejected or parse error)"))

    print(f"\n  --- 第一轮解析完成 ---")
    print(f"  总 cache:       {total_cache}")
    print(f"  成功解析:       {len(raw_items)}")
    print(f"  失败/拒绝:      {len(errors)}")

    # ---- 合并检测（去重前）----
    print(f"\n[合并检测] 去重前...")
    pre_merge_warnings = detect_merge_issues(raw_items)

    # ---- 去重（优先保留高质量版本）----
    print(f"\n[去重] 按 item.id 去重，优先保留高质量版本...")
    deduped = _dedup_with_priority(raw_items)
    dup_count = len(raw_items) - len(deduped)
    print(f"  去重: {len(raw_items)} → {len(deduped)} (移除 {dup_count} 个重复)")

    # ---- 合并检测（去重后，确认无残留）----
    print(f"\n[合并检测] 去重后...")
    post_merge_warnings = detect_merge_issues(deduped)
    error_merges = [w for w in post_merge_warnings if w['level'] == 'ERROR']
    if error_merges:
        print(f"  WARNING: 去重后仍有 {len(error_merges)} 个错误合并！")

    # ---- 数据规范化 ----
    print(f"\n[规范化] 应用 ZH_MAP + 清洗...")
    items = normalize_items(deduped)

    # ---- 分离被 reject 的项（第二轮：基于解析后数据）----
    # 在 normalize 之后，重新检查 is_reject_page
    rejected_in_normalize = len(deduped) - len(items)

    final_items = items

    # ---- 终局数据修复（分类修正 + 中文补全 + 变体补丁 + 一致性检查）----
    fix_report = apply_final_fixes(final_items)

    # ---- 构建分类（修复后重建）----
    print(f"\n[构建分类]...")
    categories = build_categories(final_items)

    # ---- 质量验证 ----
    print(f"\n[质量验证]...")
    passed, issues = validate_quality(final_items)
    for issue in issues:
        print(f"  [ISSUE] {issue}")
    print(f"  验证结果: {'PASS' if passed else 'ISSUES FOUND'}")

    # ---- 中文名覆盖率统计 ----
    zh_fallback_count = sum(1 for i in final_items if i.get('name_zh') == i.get('name_en'))
    zh_cov = (len(final_items) - zh_fallback_count) / max(len(final_items), 1) * 100
    zh_missing_count = sum(1 for i in final_items if i.get('name_zh') == i.get('name_en'))

    # ---- 写日志 ----
    _write_log(ERROR_LOG, errors, header="解析失败/被拒绝页面")
    _write_log(REJECT_LOG, [], header="过滤日志 (详见 error.log)")

    # ---- 统计 (精确计算) ----
    # 注意：raw_items 包含变体展开后的所有 item（可能 > total_cache）
    base_parsed = total_cache - len(errors)
    variants_generated = len(raw_items) - base_parsed
    parse_failed = len(errors)
    duplicates_removed = dup_count
    non_items_filtered = rejected_in_normalize
    total_rejected = parse_failed + non_items_filtered
    stats = {
        "total_cache": total_cache,
        "base_parsed": base_parsed,
        "variants_expanded": variants_generated,
        "parse_failed": parse_failed,
        "duplicates_removed": duplicates_removed,
        "non_items_filtered": non_items_filtered,
        "accepted": len(final_items),
        "zh_coverage_pct": round(zh_cov, 1),
        "zh_missing_count": zh_missing_count,
    }

    print("\n" + "=" * 60)
    print("离线重建统计")
    print("=" * 60)
    print(f"  总 cache 文件:     {stats['total_cache']}")
    print(f"  基础解析成功:      {stats['base_parsed']}")
    print(f"  变体展开新增:      {stats['variants_expanded']}")
    print(f"  解析失败/跳过:     {stats['parse_failed']}")
    print(f"  去重移除:          {stats['duplicates_removed']}")
    print(f"  非物品过滤:        {stats['non_items_filtered']}")
    print(f"  ─────────────────────")
    print(f"  最终物品数:        {stats['accepted']}")
    print(f"  中文覆盖率:        {stats['zh_coverage_pct']}% ({stats['zh_missing_count']} 项 fallback)")
    print(f"  大类覆盖:          {len(categories)}/8")

    # ---- 写入 data.json ----
    print(f"\n[写入] data.json...")
    meta = {
        "version": "1.21.11",
        "generated_at": datetime.date.today().isoformat(),
        "total_items": len(final_items),
        "source": "minecraft.wiki",
        "build_stats": stats,
    }
    output = {
        "meta": meta,
        "categories": categories,
        "items": final_items,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    file_size = os.path.getsize(OUTPUT_PATH)
    print(f"  输出: {OUTPUT_PATH}")
    print(f"  大小: {file_size / 1024:.1f} KB")
    write_fallback_snapshot(OUTPUT_PATH, FALLBACK_PATH)

    # ---- 验证报告（对齐 plan.md §8.1）----
    validate_quality_report(final_items)

    # ---- 变体覆盖验证 ----
    print(f"\n[变体覆盖验证]...")
    var_passed, var_missing = validate_variant_coverage(final_items)

    # ---- 自动验证判定 ----
    print()
    if len(final_items) < 300:
        print("FATAL: 物品数 < 300，不满足最低要求！")
        return 1
    if zh_cov < 90:
        print(f"WARNING: 中文覆盖率 {zh_cov:.1f}% < 90%，请补充 ZH_MAP")
        # 不中断

    print(f"\n日志文件:")
    print(f"  {ERROR_LOG}")
    print(f"  {REJECT_LOG}")

    return 0 if len(final_items) >= 300 else 1


def _dedup_with_priority(items):
    """
    按 item.id 去重，优先保留高质量版本。
    优先级: 有 crafting > 有 acquisition.methods > 中文名非 fallback > 保留先遇到的
    """
    def _score(item):
        s = 0
        if item.get('crafting') and len(item.get('crafting', [])) > 0:
            s += 100
        acq = item.get('acquisition', {})
        if isinstance(acq, dict):
            methods = acq.get('methods', [])
            if methods and methods != ['未知']:
                s += 50
        name_zh = item.get('name_zh', '')
        name_en = item.get('name_en', '')
        if name_zh and name_zh != name_en:
            s += 30
        return s

    best = {}
    for item in items:
        item_id = item.get('id', '')
        if not item_id:
            continue
        if item_id not in best:
            best[item_id] = item
        else:
            if _score(item) > _score(best[item_id]):
                best[item_id] = item
    return list(best.values())


def _write_log(filepath, entries, header="Log"):
    """写日志文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {header}\n")
        f.write(f"# Generated: {datetime.datetime.now().isoformat()}\n")
        f.write(f"# Total: {len(entries)}\n\n")
        for name, reason in entries:
            f.write(f"{name}\t{reason}\n")
    print(f"  日志已写入: {filepath} ({len(entries)} 条)")


def main():
    parser = argparse.ArgumentParser(description='Minecraft Wiki 物品数据爬虫')
    parser.add_argument('--limit', '-n', type=int, default=0,
                        help='最多抓取 N 个物品（0 = 不限）')
    parser.add_argument('--resume', action='store_true',
                        help='从缓存恢复（跳过已缓存的页面）')
    parser.add_argument('--no-cache', action='store_true',
                        help='不使用缓存，全部重新请求')
    parser.add_argument('--from-cache-only', action='store_true',
                        help='仅从 cache/ 目录全量重建 data.json，禁止网络请求')
    args = parser.parse_args()

    # 离线重建模式：不使用网络，直接从 cache 全量生成
    if args.from_cache_only:
        return process_from_cache_only()

    print("=" * 60)
    print("Minecraft Wiki 物品数据爬虫")
    print("=" * 60)

    # ---- Step 1: 获取物品列表 ----
    print("\n[Step 1] 获取物品 URL 列表...")
    item_urls = fetch_item_list()
    if not item_urls:
        print("ERROR: 未能获取任何物品 URL，退出。")
        sys.exit(1)

    # 大小写去重（wiki URL 大小写不敏感）
    seen_slugs = set()
    deduped = []
    for url in item_urls:
        slug = url.rstrip('/').split('/')[-1].lower()
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            deduped.append(url)
    item_urls = deduped
    print(f"  获取到 {len(item_urls)} 个物品 URL（去重后）")

    # 随机打乱（避免只抓同一字母开头的）
    random.shuffle(item_urls)

    if args.limit > 0:
        item_urls = item_urls[:args.limit]
        print(f"  随机抽取 {args.limit} 个")

    # ---- Step 2: 逐页抓取 ----
    print(f"\n[Step 2] 逐页抓取（{len(item_urls)} 个页面）...")
    items = []
    failed = 0
    cached = 0

    for i, url in enumerate(item_urls):
        slug = url.rstrip('/').split('/')[-1]
        print(f"  [{i + 1}/{len(item_urls)}] {slug}...", end=' ', flush=True)

        html = fetch_html(url, use_cache=not args.no_cache)
        if not html:
            print("FAILED")
            failed += 1
            continue

        # 检查是否使用缓存
        from utils import load_cache
        if load_cache(url) and not args.no_cache:
            cached += 1

        item = parse_item_page(html, url)
        if item:
            items.append(item)
            print(f"OK (crafting: {len(item.get('crafting', []))})")
        else:
            print("PARSE FAILED")
            failed += 1

    print(f"\n  抓取完成: {len(items)} 成功, {failed} 失败, {cached} 来自缓存")

    if len(items) == 0:
        print("ERROR: 未能解析任何物品数据，退出。")
        sys.exit(1)

    # ---- Step 3: 数据规范化 ----
    print("\n[Step 3] 数据规范化...")
    items = normalize_items(items)

    # ---- Step 4: 构建分类结构 ----
    print("\n[Step 4] 构建分类结构...")
    categories = build_categories(items)

    # ---- Step 5: 质量验证 ----
    print("\n[Step 5] 质量验证...")
    passed, issues = validate_quality(items)
    if issues:
        for issue in issues:
            print(f"  [ISSUE] {issue}")
    print(f"  验证结果: {'PASS' if passed else 'ISSUES FOUND (see above)'}")

    # ---- Step 6: 写入 JSON ----
    print("\n[Step 6] 写入 JSON...")
    write_output(items, categories, OUTPUT_PATH)
    write_fallback_snapshot(OUTPUT_PATH, FALLBACK_PATH)

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("完成摘要")
    print("=" * 60)

    craft_count = sum(1 for i in items if i.get('crafting'))
    smelt_count = sum(1 for i in items if i.get('acquisition', {}).get('smelting'))
    print(f"  总物品:       {len(items)}")
    print(f"  含合成配方:   {craft_count}")
    print(f"  含烧炼配方:   {smelt_count}")
    print(f"  输出文件:     {OUTPUT_PATH}")
    print(f"  兜底同步:     {FALLBACK_PATH}")

    if not passed:
        print("\n  WARNING: 质量验证未全部通过，请检查上方 ISSUES。")

    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
