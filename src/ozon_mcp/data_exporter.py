"""数据导出模块 - 保存产品数据到文件。"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def save_to_csv(products: list[dict], filepath: Path) -> Path:
    """将产品数据保存为 CSV 文件。

    保持原始字段：name, sku, original_price, your_price, min_price, price_status
    """
    # 确保目录存在
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # 使用原始字段名
    fieldnames = ["name", "sku", "original_price", "your_price", "min_price", "price_status"]

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            row = {k: p.get(k, "") for k in fieldnames}
            writer.writerow(row)

    return filepath


def save_to_json(products: list[dict], filepath: Path) -> Path:
    """将产品数据保存为 JSON 文件，包含元数据。"""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "export_time": datetime.now().isoformat(),
        "total": len(products),
        "fields": ["name", "sku", "original_price", "your_price", "min_price", "price_status"],
        "products": products,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath


def save_products(products: list[dict], output_path: str) -> dict[str, Any]:
    """保存产品数据到文件。

    根据扩展名自动判断格式：.csv 或 .json
    """
    if not products:
        return {
            "success": False,
            "error": "没有产品数据可导出",
        }

    path = Path(output_path)

    # 根据扩展名选择格式，默认为 json
    if path.suffix.lower() == ".csv":
        saved_path = save_to_csv(products, path)
        format_type = "csv"
    else:
        if not path.suffix:
            path = path.with_suffix(".json")
        saved_path = save_to_json(products, path)
        format_type = "json"

    return {
        "success": True,
        "format": format_type,
        "file": str(saved_path.absolute()),
        "total_products": len(products),
    }
