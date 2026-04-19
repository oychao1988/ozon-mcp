"""MCP Server main entry for OZON browser automation."""

import asyncio
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent

import browser as browser_module
import mail as mail_module
import ozon_selectors as selectors


# Load environment variables at module level
load_dotenv()

# MCP Server instance
app = Server("ozon")


def list_tools() -> List[Tool]:
    """List available tools for the MCP server.

    Returns:
        List of Tool definitions
    """
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
                },
            },
        ),
    ]


async def handle_login_with_email_code(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle login with email code.

    Args:
        args: Tool arguments (currently unused)

    Returns:
        Dict with success status and message
    """
    # Get environment variables
    ozon_username = os.getenv("ozon_username")
    ozon_login_url = os.getenv("ozon_login_url")
    qq_imap_auth_code = os.getenv("qq_imap_auth_code")

    # Validate required env vars
    if not ozon_username or not ozon_login_url or not qq_imap_auth_code:
        return {
            "success": False,
            "error": "Missing required environment variables: ozon_username, ozon_login_url, qq_imap_auth_code",
        }

    browser_manager = None

    try:
        # Initialize browser manager
        browser_manager = browser_module.BrowserManager(
            profile_path="./chrome-profile",
            headless=False,  # Show browser for debugging
        )

        # Start browser
        page = await browser_manager.start()

        # Navigate to login page
        await browser_manager.navigate(ozon_login_url)
        await asyncio.sleep(2)

        # Fill email
        await browser_manager.fill(selectors.LoginPage.EMAIL_INPUT, ozon_username)
        await asyncio.sleep(0.5)

        # Click send code button
        await browser_manager.click(selectors.LoginPage.SEND_CODE_BUTTON)
        await asyncio.sleep(1)

        # Initialize mail reader
        mail_reader = mail_module.QQMailReader(
            email=ozon_username,
            auth_code=qq_imap_auth_code,
        )

        # Connect to mail server
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
                "code_received": None,
            }

        # Fill in the code
        await browser_manager.fill(selectors.LoginPage.CODE_INPUT, code)
        await asyncio.sleep(0.5)

        # Submit
        await browser_manager.click(selectors.LoginPage.SUBMIT_BUTTON)
        await asyncio.sleep(3)

        # Check URL after login attempt
        current_url = page.url

        # Check for login error
        if "login" in current_url.lower() or "auth" in current_url.lower():
            mail_reader.disconnect()
            return {
                "success": False,
                "error": "Login failed - redirected back to login page",
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
        return {
            "success": False,
            "error": f"Login error: {str(e)}",
        }
    finally:
        if browser_manager:
            await browser_manager.stop()


async def handle_get_marketing_actions(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle marketing actions data extraction.

    Args:
        args: Tool arguments with page, page_size, all_pages

    Returns:
        Dict with success status and products list
    """
    page_num = args.get("page", 1)
    page_size = args.get("page_size", 20)
    all_pages = args.get("all_pages", False)

    browser_manager = None

    try:
        # Initialize browser manager
        browser_manager = browser_module.BrowserManager(
            profile_path="./chrome-profile",
            headless=False,
        )

        # Start browser
        page = await browser_manager.start()

        # Navigate to marketing actions page
        marketing_url = "https://seller.ozon.ru/app/prices/control?tab=marketing_actions"
        await browser_manager.navigate(marketing_url)
        await asyncio.sleep(2)

        # Check if redirected to login page
        current_url = page.url
        if "login" in current_url.lower() or "auth" in current_url.lower():
            return {
                "success": False,
                "error": "Not logged in - redirected to login page. Please use login-with-email-code first.",
            }

        products = []

        async def extract_page_products():
            """Extract products from current page."""
            page_products = []

            # Check for empty state
            try:
                empty_state = await page.query_selector(selectors.MarketingActionsPage.EMPTY_STATE)
                if empty_state:
                    return []
            except Exception:
                pass

            # Get product rows
            rows = await page.query_selector_all(selectors.MarketingActionsPage.PRODUCT_ROW)

            for row in rows:
                try:
                    product = {}

                    # Get product name
                    name_elem = await row.query_selector(selectors.MarketingActionsPage.PRODUCT_NAME)
                    if name_elem:
                        product["name"] = await name_elem.inner_text()

                    # Get SKU
                    sku_elem = await row.query_selector(selectors.MarketingActionsPage.SKU)
                    if sku_elem:
                        product["sku"] = await sku_elem.inner_text()

                    # Get your price
                    price_elem = await row.query_selector(selectors.MarketingActionsPage.YOUR_PRICE)
                    if price_elem:
                        product["your_price"] = await price_elem.inner_text()

                    # Get min price
                    min_price_elem = await row.query_selector(selectors.MarketingActionsPage.MIN_PRICE)
                    if min_price_elem:
                        product["min_price"] = await min_price_elem.inner_text()

                    if product.get("name") or product.get("sku"):
                        page_products.append(product)

                except Exception as e:
                    # Skip rows that cause errors
                    continue

            return page_products

        # Extract first page
        products = await extract_page_products()

        # Handle pagination if all_pages is True
        if all_pages:
            while True:
                # Check if there's a next page button
                try:
                    next_button = await page.query_selector(
                        selectors.MarketingActionsPage.NEXT_PAGE_BUTTON
                    )
                    if not next_button:
                        break

                    # Click next page
                    await next_button.click()
                    await asyncio.sleep(2)

                    # Extract products from this page
                    page_products = await extract_page_products()
                    if not page_products:
                        break

                    products.extend(page_products)

                except Exception:
                    break

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


async def call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch tool call to appropriate handler.

    Args:
        name: Tool name
        args: Tool arguments

    Returns:
        Result dict from handler
    """
    if name == "login-with-email-code":
        return await handle_login_with_email_code(args)
    elif name == "get-marketing-actions":
        return await handle_get_marketing_actions(args)
    else:
        return {
            "error": f"Unknown tool: {name}",
        }


async def main():
    """Main entry point for the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(
                tools=list_tools(),
            ),
        )