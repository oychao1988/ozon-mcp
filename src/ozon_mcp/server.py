"""MCP Server main entry for OZON browser automation."""

import asyncio
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from mcp.server import Server, NotificationOptions
from mcp.types import Tool, TextContent

from . import browser as browser_module
from . import mail as mail_module
from . import ozon_selectors as selectors
from . import data_exporter
from ._selectors import SelectorConfig

# Selector configuration (loads from selectors.yaml with hot-reload support)
_selector_config: SelectorConfig | None = None

def get_selectors() -> SelectorConfig:
    """Get or create the global SelectorConfig instance."""
    global _selector_config
    if _selector_config is None:
        _selector_config = SelectorConfig()
    return _selector_config


# Load environment variables at module level
load_dotenv()

# OZON login URL (fixed)
OZON_LOGIN_URL = "https://sso.ozon.ru/auth/ozonid?localization_language_code=zh-Hans&__rr=1&abt_att=1"

# MCP Server instance
app = Server("ozon")


def list_tools() -> List[Tool]:
    """List available tools for the MCP server."""
    return [
        Tool(
            name="login-with-email-code",
            description="登录 OZON 卖家后台，使用 QQ 邮箱接收验证码",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get-marketing-actions",
            description="获取营销活动数据（产品名称、SKU、当前价格、最低价）",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "number",
                        "description": "页码（从 1 开始）",
                        "default": 1,
                    },
                    "page_size": {
                        "type": "number",
                        "description": "每页产品数量",
                        "default": 20,
                    },
                    "all_pages": {
                        "type": "boolean",
                        "description": "是否获取所有页面数据",
                        "default": False,
                    },
                    "max_scrolls": {
                        "type": "number",
                        "description": "滚动加载最大次数",
                        "default": 20,
                    },
                    "scroll_delay": {
                        "type": "number",
                        "description": "每次滚动之间的等待时间（秒）",
                        "default": 1.0,
                    },
                },
            },
        ),
    ]


@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Handle list tools request."""
    return list_tools()


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool call request."""
    args = arguments or {}

    if name == "login-with-email-code":
        result = await handle_login_with_email_code(args)
    elif name == "get-marketing-actions":
        result = await handle_get_marketing_actions(args)
    else:
        result = {"success": False, "error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=str(result))]


async def _bypass_captcha(page) -> bool:
    """Bypass CAPTCHA/challenge page by injecting JavaScript."""
    try:
        await page.evaluate("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });
        """)
        return True
    except Exception as e:
        print(f"CAPTCHA bypass error: {e}")
        return False


async def handle_login_with_email_code(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle login with email code."""
    # Get environment variables
    ozon_username = os.getenv("ozon_username")
    qq_imap_auth_code = os.getenv("qq_imap_auth_code")

    if not ozon_username or not qq_imap_auth_code:
        return {
            "success": False,
            "error": "Missing required environment variables",
        }

    browser_manager = None
    headless = args.get("headless", False)

    try:
        # Initialize browser manager - use Chrome profile if available
        browser_manager = browser_module.BrowserManager(
            profile_path="./chrome-profile",
            headless=headless,
            use_profile=True,
            auto_detect_profile=True,
        )

        # Start browser
        page = await browser_manager.start()

        # Navigate to login page
        await browser_manager.navigate(OZON_LOGIN_URL)
        await asyncio.sleep(3)

        # Check for CAPTCHA page
        title = await page.title()
        print(f"Initial page title: {title}")

        # If CAPTCHA detected, bypass and wait
        if any(ct in title.lower() for ct in ['доступ ограничен', 'access denied', 'antibot', 'challenge']):
            print("CAPTCHA detected, bypassing...")
            await _bypass_captcha(page)
            # Don't reload - just wait for the page to possibly change
            await asyncio.sleep(5)
            title = await page.title()
            print(f"Page title after waiting: {title}")

        # Wait for page to stabilize
        await asyncio.sleep(1)

        # Check if we need to click email login button (support both Chinese and Russian)
        email_btn_selectors = [
            'button:has-text("使用邮箱登录")',
            'button:has-text("Войти по почте")',
            'button:has-text("Войти по электронной почте")',
            'button:has-text("Email")',
            'button:has-text("Почта")',
        ]
        for email_sel in email_btn_selectors:
            try:
                email_btn = await page.wait_for_selector(email_sel, timeout=3000)
                if email_btn:
                    print(f"Found email login button: {email_sel}, clicking...")
                    await email_btn.click()
                    await asyncio.sleep(2)
                    break
            except Exception:
                continue

        # Wait for email input
        email_input = None
        for sel in ['input[autocomplete="email"]', 'input[type="email"]', 'input[name="email"]']:
            try:
                email_input = await page.wait_for_selector(sel, timeout=5000)
                if email_input:
                    print(f"Found email input with selector: {sel}")
                    break
            except Exception:
                continue

        if not email_input:
            return {
                "success": False,
                "error": "Email input not found on page",
                "page_title": await page.title(),
                "current_url": page.url,
            }

        # Fill email
        await email_input.fill(ozon_username)
        await asyncio.sleep(0.5)

        # Click login/continue button (support Chinese, Russian, and generic submit)
        login_btn_selectors = [
            'button:has-text("登录")',
            'button:has-text("Далее")',
            'button:has-text("Войти")',
            'button[type="submit"]',
        ]
        login_btn = None
        for login_sel in login_btn_selectors:
            try:
                login_btn = await page.wait_for_selector(login_sel, timeout=3000)
                if login_btn:
                    print(f"Found login button: {login_sel}")
                    break
            except Exception:
                continue

        if not login_btn:
            return {
                "success": False,
                "error": "Login button not found on page",
                "page_title": await page.title(),
                "current_url": page.url,
            }

        await login_btn.click()
        
        # Wait for OTP page to load
        print("Waiting for OTP page...")
        await asyncio.sleep(3)
        
        # Check if URL changed to OTP page
        current_url = page.url
        print(f"Current URL after login click: {current_url}")
        
        # If still on login page, wait more
        if "otp" not in current_url.lower():
            print("Waiting more for OTP page to load...")
            await asyncio.sleep(3)

        # Initialize mail reader
        mail_reader = mail_module.QQMailReader(
            email_addr=ozon_username,
            auth_code=qq_imap_auth_code,
        )

        if not mail_reader.connect():
            return {
                "success": False,
                "error": "Failed to connect to QQ mail server",
            }

        # Wait for email code
        code = mail_reader.wait_for_code(subject_keyword="OZON", timeout=120)

        if not code:
            mail_reader.disconnect()
            return {
                "success": False,
                "error": "Timeout waiting for verification code from QQ mail",
            }

        # Wait for OTP code input to appear
        print("Looking for OTP code input...")
        code_input = None
        
        # First check if there's any text input on the page (OTP code input)
        try:
            code_input = await page.wait_for_selector(selectors.LoginPage.CODE_INPUT, timeout=5000)
            if code_input:
                print(f"Found code input")
        except Exception:
            pass
        
        # Try other selectors
        otp_selectors = [
            'input[name="code"]',
            'input[name="otp"]',
            'input[placeholder*="验证码"]',
            'input[placeholder*="код"]',
            'input[placeholder*="code"]',
            'input[autocomplete="one-time-code"]',
        ]
        
        if not code_input:
            for sel in otp_selectors:
                try:
                    print(f"Trying selector: {sel}")
                    code_input = await page.wait_for_selector(sel, timeout=5000)
                    if code_input:
                        print(f"Found code input with selector: {sel}")
                        break
                except Exception as e:
                    print(f"Selector {sel} not found")
                    continue

        if not code_input:
            mail_reader.disconnect()
            return {
                "success": False,
                "error": "Code input not found after sending code",
                "code_received": code,
            }

        # Fill in the code
        await code_input.fill(code)

        # Click submit button after filling OTP code
        login_cfg = get_selectors().get_login_selectors()
        otp_submit_selectors = login_cfg.get("otp_submit_buttons", [
            'button:has-text("Подтвердить")',
            'button:has-text("Войти")',
            'button[type="submit"]',
        ])
        submit_clicked = False
        for submit_sel in otp_submit_selectors:
            try:
                await page.wait_for_selector(submit_sel, timeout=3000)
                await page.click(submit_sel)
                submit_clicked = True
                print(f"Clicked OTP submit button: {submit_sel}")
                break
            except Exception:
                continue

        if not submit_clicked:
            # Fallback: press Enter on the focused input
            await page.press("input", "Enter")
            print("No explicit OTP submit button found, pressed Enter as fallback")

        await asyncio.sleep(3)

        # Check result
        current_url = page.url
        title = await page.title()

        # Check for error
        if "代码不正确" in title or "incorrect" in title.lower():
            mail_reader.disconnect()
            return {
                "success": False,
                "error": "Login failed - code may be incorrect",
                "code_received": code,
            }

        mail_reader.disconnect()

        return {
            "success": True,
            "message": "Login successful",
            "code_received": code,
            "current_url": current_url,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Login error: {str(e)}",
        }
    finally:
        if browser_manager:
            await browser_manager.stop()


async def _scroll_to_load(page, max_scrolls: int, scroll_delay: float):
    """Scroll page to trigger lazy loading of all content."""
    # 首先滚动到顶部确保从头开始
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(0.3)

    # 更小的步长逐步滚动，确保表格中间的产品也被加载
    for i in range(max_scrolls * 3):  # 增加滚动次数
        scroll_position = (i + 1) * 300  # 每次滚动 300px
        await page.evaluate(f"window.scrollTo(0, {scroll_position})")
        await asyncio.sleep(scroll_delay * 0.8)  # 稍短的单次延迟，但更多次数

        # 检查是否到底
        current_height = await page.evaluate("window.scrollY + window.innerHeight")
        total_height = await page.evaluate("document.body.scrollHeight")
        if current_height >= total_height:
            break

    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(0.5)


async def _click_page_button(page, target_page: int) -> bool:
    """Click a page number button. Returns True if clicked, False if not found."""
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(0.5)
    # Try clicking "Next page" button first (most reliable fallback)
    next_button_selectors = [
        'button[aria-label*="ледующ"], button[aria-label*="Next"], button[aria-label*="下一页"], button[aria-label*="下一页"]',
        'button:has-text("›"), button:has-text("→"), button:has-text("»")',
        'button:has-text("Следующая"), button:has-text("Next page"), button:has-text("下一页"), button:has-text("下一页")',
    ]
    for sel in next_button_selectors:
        try:
            btn = await page.wait_for_selector(sel, timeout=2000)
            if btn:
                await btn.click()
                # 增加更长的等待时间，确保表格内容完全加载
                await asyncio.sleep(3)
                await page.wait_for_load_state("networkidle", timeout=10000)
                # 额外等待表格行出现
                try:
                    await page.wait_for_selector('table tbody tr, tr[class*="product"], tr[class*="item"]', timeout=5000)
                except Exception:
                    pass
                await asyncio.sleep(1)
                return True
        except Exception:
            continue
    # Then try finding the specific page number button within pagination container
    all_buttons = await page.query_selector_all('button')
    for btn in all_buttons:
        text = (await btn.inner_text()).strip()
        if text.isdigit() and int(text) == target_page:
            await btn.click()
            # 增加更长的等待时间，确保表格内容完全加载
            await asyncio.sleep(3)
            await page.wait_for_load_state("networkidle", timeout=10000)
            # 额外等待表格行出现
            try:
                await page.wait_for_selector('table tbody tr, tr[class*="product"], tr[class*="item"]', timeout=5000)
            except Exception:
                pass
            await asyncio.sleep(1)
            return True
    return False


async def _extract_products_from_page(page, max_scrolls: int, scroll_delay: float, limit: int, min_products: int = None) -> list[dict]:
    """Extract product data from the current page, up to `limit` products.

    Args:
        min_products: 期望的最小产品数量，如果设置了会等待直到达到该数量或超时
    """
    # 先滚动加载
    await _scroll_to_load(page, max_scrolls, scroll_delay)

    # 等待表格加载 - 增加等待逻辑确保数据已加载
    rows = []
    max_wait_attempts = 10  # 增加重试次数
    wait_interval = 3  # 每次等待时间增加到 3 秒

    for attempt in range(max_wait_attempts):
        rows = await page.query_selector_all('table tbody tr')
        if not rows:
            rows = await page.query_selector_all('tr[class*="product"], tr[class*="item"]')

        # 如果设置了最小产品数量要求，检查是否满足
        target_count = min_products if min_products else (limit if limit > 0 else 1)
        if len(rows) >= target_count:
            print(f"Loaded {len(rows)} rows (meets target {target_count})")
            break

        # 最后一次尝试，不再等待
        if attempt == max_wait_attempts - 1:
            break

        # 等待后重试
        print(f"Waiting for products to load... (attempt {attempt + 1}/{max_wait_attempts}, found {len(rows)} rows, target {target_count})")
        await asyncio.sleep(wait_interval)

        # 再次滚动触发加载 - 模拟真实用户行为，逐步滚动
        scroll_steps = 3
        for step in range(scroll_steps):
            scroll_pos = (step + 1) * (await page.evaluate("window.innerHeight")) * 0.8
            await page.evaluate(f"window.scrollTo(0, {scroll_pos})")
            await asyncio.sleep(0.5)

    products = []
    for row in rows:
        if len(products) >= limit:
            break

        try:
            cells = await row.query_selector_all('td')
            if len(cells) < 4:
                continue

            product = {}
            for i, cell in enumerate(cells):
                text = (await cell.inner_text()).strip()
                if not text:
                    continue

                lines = [l.strip() for l in text.split('\n') if l.strip()]

                # Cell 1: product name + SKU
                if i == 1:
                    if lines:
                        product["name"] = lines[0]
                        for line in reversed(lines):
                            if line.replace(' ', '').isdigit():
                                product["sku"] = line
                                break

                # Cell 2: SKU (sometimes separate)
                elif i == 2:
                    if not product.get("sku") and lines:
                        for line in lines:
                            if line.replace(' ', '').isdigit():
                                product["sku"] = line
                                break

                # Cell 3: your price
                elif i == 3:
                    for line in lines:
                        if '¥' in line:
                            product["your_price"] = line
                            break

                # Cell 4: price for buyers
                elif i == 4:
                    for line in lines:
                        if '¥' in line:
                            product["buyer_price"] = line
                            break

                # Cell 5: min price
                elif i == 5:
                    for line in lines:
                        if '¥' in line or line == '未指定':
                            product["min_price"] = line
                            break

                # Cell 6: price status
                elif i == 6:
                    for line in lines:
                        if any(s in line for s in ['有利', '不利', '中等']):
                            product["price_status"] = line
                            break

            if product.get("name") or product.get("sku"):
                products.append(product)

        except Exception:
            continue

    return products


async def handle_get_marketing_actions(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle marketing actions data extraction."""
    page_num = args.get("page", 1)
    page_size = args.get("page_size", 50)
    all_pages = args.get("all_pages", False)
    headless = args.get("headless", False)

    scroll_cfg = get_selectors().get_scroll_config()
    max_scrolls = args.get("max_scrolls", scroll_cfg["max_iterations"])
    scroll_delay = args.get("scroll_delay", scroll_cfg["delay_seconds"])

    browser_manager = None

    try:
        browser_manager = browser_module.BrowserManager(
            profile_path="./chrome-profile",
            headless=headless,
        )

        page = await browser_manager.start()
        marketing_url = "https://seller.ozon.ru/app/prices/control?tab=marketing_actions"
        await browser_manager.navigate(marketing_url)

        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        # Check if redirected to login
        if "login" in page.url.lower() or "auth" in page.url.lower():
            return {
                "success": False,
                "error": "Not logged in - please use login-with-email-code first",
            }

        products = []

        if all_pages:
            # Navigate to starting page first
            if page_num > 1:
                found = await _click_page_button(page, page_num)
                if not found:
                    return {
                        "success": False,
                        "error": f"Page {page_num} not found",
                        "products": [],
                    }

            # Extract all pages starting from page_num
            current_page = page_num
            while True:

                page_products = await _extract_products_from_page(
                    page, max_scrolls, scroll_delay, page_size, min_products=page_size
                )

                if not page_products:
                    print(f"No products on page {current_page}, stopping.")
                    break

                # 检查是否部分加载
                partial_warning = ""
                if len(page_products) < page_size:
                    partial_warning = f" (部分加载: {len(page_products)}/{page_size})"

                products.extend(page_products)
                print(f"Page {current_page}: {len(page_products)} products, total: {len(products)}{partial_warning}")
                current_page += 1
                found = await _click_page_button(page, current_page)
                if not found:
                    print(f"No page {current_page} button found, stopping.")
                    break

        else:
            # Single page: navigate to target page if needed
            if page_num > 1:
                print(f"Navigating to page {page_num}...")
                found = await _click_page_button(page, page_num)
                if not found:
                    return {
                        "success": False,
                        "error": f"Page {page_num} not found",
                        "products": [],
                    }

            products = await _extract_products_from_page(
                page, max_scrolls, scroll_delay, page_size
            )
            print(f"Extracted {len(products)} products from page {page_num}")

        # 检查是否需要保存到文件
        output_path = args.get("output")
        if output_path:
            result = data_exporter.save_products(products, output_path)
            if result["success"]:
                return {
                    "success": True,
                    "data_saved": True,
                    "file": result["file"],
                    "format": result["format"],
                    "total_products": len(products),
                    "note": f"数据已保存到文件: {result['file']}",
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "保存失败"),
                    "products": products[:10],  # 返回前10个作为备用
                }

        return {
            "success": True,
            "products": products,
            "total": len(products),
            "page": page_num,
            "page_size": page_size,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error extracting marketing actions: {str(e)}",
            "products": [],
        }
    finally:
        if browser_manager:
            await browser_manager.stop()


async def main():
    """Main entry point for the MCP server."""
    from mcp.server.stdio import stdio_server
    from mcp.server import InitializationOptions

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ozon",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


def cli_main():
    """CLI entry point for uv tool install."""
    asyncio.run(main())
