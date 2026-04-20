#!/usr/bin/env python3
"""OZON CLI - 直接从命令行执行 OZON 操作，无需 MCP 协议。

用法:
    python cli.py login                     # 登录 OZON 卖家后台
    python cli.py marketing                 # 获取营销活动（第1页，20条）
    python cli.py marketing --page 2        # 获取第2页
    python cli.py marketing --all           # 获取所有页面
    python cli.py marketing --page-size 50  # 每页50条
    python cli.py marketing --headless      # 无头模式运行
    python cli.py check                     # 检查环境配置
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# 将 src 目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

# 加载 .env
load_dotenv(Path(__file__).parent / ".env")


def print_json(data: dict):
    """格式化输出 JSON。"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_table(products: list[dict]):
    """以表格形式输出产品列表。"""
    if not products:
        print("没有找到产品数据。")
        return

    # 计算列宽
    cols = {
        "name": "产品名称",
        "sku": "SKU",
        "your_price": "你的价格",
        "min_price": "最低价",
        "original_price": "原价",
        "price_status": "价格状态",
    }

    widths = {}
    for key, header in cols.items():
        widths[key] = len(header)
        for p in products:
            val = p.get(key, "-")
            widths[key] = max(widths[key], len(str(val)))

    # 打印表头
    header_line = " | ".join(
        f"{cols[k]:<{widths[k]}}" for k in cols
    )
    print(header_line)
    print("-" * len(header_line))

    # 打印数据行
    for p in products:
        row = " | ".join(
            f"{p.get(k, '-'):<{widths[k]}}" for k in cols
        )
        print(row)


def check_env() -> dict:
    """检查环境配置。"""
    checks = {}

    # 检查 .env 文件
    env_path = Path(__file__).parent / ".env"
    checks["env_file"] = env_path.exists()

    # 检查环境变量
    checks["ozon_username"] = bool(os.getenv("ozon_username"))
    checks["qq_imap_auth_code"] = bool(os.getenv("qq_imap_auth_code"))

    # 检查 chrome-profile 目录
    profile_path = Path(__file__).parent / "chrome-profile"
    checks["chrome_profile"] = profile_path.exists()

    # 检查 playwright
    try:
        from playwright.async_api import async_playwright
        checks["playwright"] = True
    except ImportError:
        checks["playwright"] = False

    return checks


async def cmd_login(args):
    """执行登录操作。"""
    from ozon_mcp.server import handle_login_with_email_code

    print("=" * 50)
    print("OZON 登录")
    print("=" * 50)

    # 检查环境
    if not os.getenv("ozon_username") or not os.getenv("qq_imap_auth_code"):
        print("错误: 缺少环境变量 ozon_username 或 qq_imap_auth_code")
        print("请在 .env 文件中配置:")
        print('  ozon_username="your_email@qq.com"')
        print('  qq_imap_auth_code="your_auth_code"')
        sys.exit(1)

    print(f"账号: {os.getenv('ozon_username')}")
    print("正在启动浏览器...")
    if args.headless:
        print("(无头模式)")

    result = await handle_login_with_email_code({})

    print()
    if result.get("success"):
        print(f"登录成功!")
        print(f"  验证码: {result.get('code_received')}")
        print(f"  当前URL: {result.get('current_url')}")
    else:
        print(f"登录失败: {result.get('error')}")
        if result.get("code_received"):
            print(f"  接收到的验证码: {result.get('code_received')}")

    return result


async def cmd_marketing(args):
    """获取营销活动数据。"""
    from ozon_mcp.server import handle_get_marketing_actions

    print("=" * 50)
    print("OZON 营销活动数据")
    print("=" * 50)

    call_args = {
        "page": args.page,
        "page_size": args.page_size,
        "all_pages": args.all,
        "max_scrolls": args.max_scrolls,
        "scroll_delay": args.scroll_delay,
    }

    if args.all:
        print("模式: 获取所有页面")
    else:
        print(f"模式: 第 {args.page} 页，每页 {args.page_size} 条")

    print("正在启动浏览器并导航到营销活动页面...")

    result = await handle_get_marketing_actions(call_args)

    print()
    if result.get("success"):
        products = result.get("products", [])
        print(f"成功获取 {len(products)} 个产品")
        print()

        if args.json:
            print_json(result)
        else:
            print_table(products)
            print()
            print(f"共 {result.get('total', len(products))} 条数据")
    else:
        print(f"获取失败: {result.get('error')}")
        if args.json:
            print_json(result)

    return result


async def cmd_check(args):
    """检查环境配置。"""
    print("=" * 50)
    print("OZON CLI 环境检查")
    print("=" * 50)

    checks = check_env()

    status_map = {True: "✓", False: "✗"}

    print(f"  {status_map[checks['env_file']]} .env 文件")
    print(f"  {status_map[checks['ozon_username']]} ozon_username 配置")
    print(f"  {status_map[checks['qq_imap_auth_code']]} qq_imap_auth_code 配置")
    print(f"  {status_map[checks['chrome_profile']]} chrome-profile 目录")
    print(f"  {status_map[checks['playwright']]} playwright 依赖")

    all_ok = all(checks.values())
    print()
    if all_ok:
        print("所有检查通过，可以正常使用。")
    else:
        print("部分检查未通过，请根据上方提示修复。")
        if not checks["playwright"]:
            print("  → 运行: uv run playwright install chromium")
        if not checks["chrome_profile"]:
            print("  → chrome-profile 目录不存在，首次运行会自动创建")

    return checks


def main():
    parser = argparse.ArgumentParser(
        description="OZON CLI - 命令行直接执行 OZON 操作",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行浏览器（不显示界面）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出结果",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # login 命令
    subparsers.add_parser("login", help="登录 OZON 卖家后台")

    # marketing 命令
    marketing_parser = subparsers.add_parser("marketing", help="获取营销活动数据")
    marketing_parser.add_argument("--page", type=int, default=1, help="页码（从1开始）")
    marketing_parser.add_argument("--page-size", type=int, default=20, help="每页产品数量")
    marketing_parser.add_argument("--all", action="store_true", help="获取所有页面")
    marketing_parser.add_argument("--max-scrolls", type=int, default=20, help="最大滚动次数")
    marketing_parser.add_argument("--scroll-delay", type=float, default=1.0, help="滚动延迟（秒）")

    # check 命令
    subparsers.add_parser("check", help="检查环境配置")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行对应的命令
    if args.command == "login":
        result = asyncio.run(cmd_login(args))
    elif args.command == "marketing":
        result = asyncio.run(cmd_marketing(args))
    elif args.command == "check":
        result = asyncio.run(cmd_check(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
