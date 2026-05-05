# ============================================
# writer.py — 写入 JSON 输出文件
# ============================================

import json
import os
import datetime


def write_output(items, categories, output_path):
    """
    将物品和分类数据写入 data.json。

    同时写入 meta 信息，确保格式与 P0 兼容。
    """
    meta = {
        "version": "1.21.11",
        "generated_at": datetime.date.today().isoformat(),
        "total_items": len(items),
        "source": "minecraft.wiki",
    }

    output = {
        "meta": meta,
        "categories": categories,
        "items": items,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(output_path)
    print(f"\nOutput written: {output_path}")
    print(f"  Items: {len(items)}")
    print(f"  Categories: {len(categories)}")
    print(f"  File size: {file_size / 1024:.1f} KB")


def write_fallback_snapshot(output_path, fallback_path):
    """同步写入兜底数据副本"""
    import shutil
    if os.path.exists(output_path):
        shutil.copy(output_path, fallback_path)
        print(f"  Fallback synced: {fallback_path}")
