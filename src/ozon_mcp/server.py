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

    try:
        # Initialize browser manager - use Chrome profile if available
        browser_manager = browser_module.BrowserManager(
            profile_path="./chrome-profile",
            headless=False,
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

        # Check if we need to click email login button
        try:
            email_btn = await page.wait_for_selector('button:has-text("使用邮箱登录")', timeout=3000)
            if email_btn:
                print("Found email login button, clicking...")
                await email_btn.click()
                await asyncio.sleep(2)
        except Exception:
            pass

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

        # Click login button
        login_btn = await page.wait_for_selector('button:has-text("登录")', timeout=5000)
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


async def handle_get_marketing_actions(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle marketing actions data extraction."""
    page_num = args.get("page", 1)
    page_size = args.get("page_size", 20)
    all_pages = args.get("all_pages", False)

    browser_manager = None

    try:
        browser_manager = browser_module.BrowserManager(
            profile_path="./chrome-profile",
            headless=False,
        )

        page = await browser_manager.start()
        marketing_url = "https://seller.ozon.ru/app/prices/control?tab=marketing_actions"
        await browser_manager.navigate(marketing_url)
        
        # Wait for page to fully load
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)  # Extra wait for dynamic content

        # Check if redirected to login
        if "login" in page.url.lower() or "auth" in page.url.lower():
            return {
                "success": False,
                "error": "Not logged in - please use login-with-email-code first",
            }

        products = []

        # Scroll helper — defined once at function level, used by all callers
        scroll_cfg = get_selectors().get_scroll_config()
        max_scrolls = args.get("max_scrolls", scroll_cfg["max_iterations"])
        scroll_delay = args.get("scroll_delay", scroll_cfg["delay_seconds"])

        async def scroll_to_load():
            scroll_position = 0
            last_height = await page.evaluate("document.body.scrollHeight")

            for _ in range(max_scrolls):
                scroll_position += await page.evaluate("window.innerHeight")
                await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                await asyncio.sleep(scroll_delay)

                new_height = await page.evaluate("document.body.scrollHeight")
                if scroll_position >= new_height:
                    break
                last_height = new_height

            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.5)

        async def extract_page_products():
            page_products = []

            # Scroll to load all lazy content
            await scroll_to_load()
            
            # Try to find table rows
            rows = await page.query_selector_all('table tbody tr')
            
            if not rows:
                rows = await page.query_selector_all('tr[class*="product"], tr[class*="item"]')
            
            for row in rows:
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
                        
                        # Cell 0: checkbox (skip)
                        # Cell 1: product name (contains full name + SKU)
                        if i == 1:
                            if lines:
                                # First line is the name
                                product["name"] = lines[0]
                                # Find SKU (last part if it's digits)
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
                        
                        # Cell 3: original/discount prices (2 prices)
                        elif i == 3:
                            for line in lines:
                                if '¥' in line:
                                    product["original_price"] = line
                                    break
                        
                        # Cell 4: your price (current price)
                        elif i == 4:
                            for line in lines:
                                if '¥' in line:
                                    product["your_price"] = line
                                    break
                        
                        # Cell 5: min price
                        elif i == 5:
                            for line in lines:
                                if '¥' in line or line == '未指定':
                                    product["min_price"] = line
                                    break
                        
                        # Cell 6: price status (有利/不利/中等)
                        elif i == 6:
                            for line in lines:
                                if any(s in line for s in ['有利', '不利', '中等']):
                                    product["price_status"] = line
                                    break
                    
                    if product.get("name") or product.get("sku"):
                        page_products.append(product)
                        
                except Exception:
                    continue
            return page_products

        # Navigate to target page
        if page_num > 1 or all_pages:
            current_page = 1
            target_page = page_num if not all_pages else None
            
            while True:
                if target_page and current_page >= target_page:
                    break
                    
                try:
                    # Scroll to top before pagination
                    await page.evaluate("window.scrollTo(0, 0)")
                    await asyncio.sleep(0.5)
                    
                    # Look for next page button
                    all_buttons = await page.query_selector_all('button')
                    next_page = current_page + 1
                    next_btn = None
                    
                    for btn in all_buttons:
                        text = (await btn.inner_text()).strip()
                        if text.isdigit() and int(text) == next_page:
                            next_btn = btn
                            break
                    
                    if not next_btn:
                        print(f"No more pages after page {current_page}")
                        break
                    
                    print(f"Clicking page {next_page}...")
                    await next_btn.click()
                    
                    # Wait for loading
                    await asyncio.sleep(2)
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await asyncio.sleep(1)
                    
                    await scroll_to_load()
                    current_page += 1
                    print(f"Navigated to page {current_page}")
                    
                except Exception as e:
                    print(f"Error navigating to page {current_page + 1}: {e}")
                    break
        
        # Extract first page
        products = await extract_page_products()
        print(f"Extracted {len(products)} products from page {page_num}")

        if all_pages:
            page_count = 0
            
            while page_count < 20:  # Max 20 pages
                try:
                    # Scroll to top before pagination
                    await page.evaluate("window.scrollTo(0, 0)")
                    await asyncio.sleep(0.5)
                    
                    # Look for page number buttons (1, 2, 3, etc.)
                    all_buttons = await page.query_selector_all('button')
                    
                    next_page = page_num + page_count + 1
                    next_btn = None
                    
                    for btn in all_buttons:
                        text = (await btn.inner_text()).strip()
                        if text.isdigit() and int(text) == next_page:
                            next_btn = btn
                            break
                    
                    if not next_btn:
                        print("No more pages found")
                        break
                    
                    print(f"Clicking page {next_page}...")
                    await next_btn.click()
                    
                    # Wait for loading indicator to disappear and content to load
                    await asyncio.sleep(2)
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await asyncio.sleep(1)
                    
                    await scroll_to_load()
                    
                    page_products = await extract_page_products()
                    
                    # Retry logic: if not enough products, scroll again
                    max_retries = 3
                    retry_count = 0
                    while len(page_products) < page_size and retry_count < max_retries:
                        retry_count += 1
                        print(f"  Only got {len(page_products)} products, retrying ({retry_count}/{max_retries})...")
                        
                        # Scroll back to top and try scrolling again
                        await page.evaluate("window.scrollTo(0, 0)")
                        await asyncio.sleep(0.5)
                        await scroll_to_load()
                        
                        page_products = await extract_page_products()
                    
                    if not page_products:
                        print("No products on this page, stopping...")
                        break
                    
                    products.extend(page_products)
                    page_count += 1
                    print(f"Extracted {len(page_products)} products from page {next_page}, total: {len(products)}")
                    
                except Exception as e:
                    print(f"Error during pagination: {e}")
                    import traceback
                    traceback.print_exc()
                    break

        return {
            "success": True,
            "products": products[:page_size] if not all_pages else products,
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
