"""Tests for MCP server handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


@pytest.mark.asyncio
class TestHandleLoginWithEmailCode:
    """Test login handler with email code."""

    async def test_handle_login_with_email_code_success(self):
        """Test successful login flow."""
        from ozon_mcp.server import handle_login_with_email_code

        env_vars = {
            "ozon_username": "test@qq.com",
            "ozon_login_url": "https://test.ozon.ru/login",
            "qq_imap_auth_code": "test_auth_code",
        }

        mock_page = AsyncMock()
        mock_page.url = "https://seller.ozon.ru/app/"

        mock_browser_manager = MagicMock()
        mock_browser_manager.start = AsyncMock(return_value=mock_page)
        mock_browser_manager.page = mock_page
        mock_browser_manager.navigate = AsyncMock()
        mock_browser_manager.fill = AsyncMock()
        mock_browser_manager.click = AsyncMock()
        mock_browser_manager.stop = AsyncMock()

        mock_mail = MagicMock()
        mock_mail.connect.return_value = True
        mock_mail.wait_for_code.return_value = "123456"
        mock_mail.disconnect = MagicMock()

        with patch.dict("os.environ", env_vars, clear=False), \
             patch("ozon_mcp.browser.BrowserManager", return_value=mock_browser_manager), \
             patch("ozon_mcp.mail.QQMailReader", return_value=mock_mail), \
             patch("ozon_mcp.server.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            result = await handle_login_with_email_code({})

            assert result["success"] is True
            assert "Login successful" in result["message"]
            assert result["code_received"] == "123456"

    async def test_handle_login_with_email_code_captcha_timeout(self):
        """Test timeout scenario when waiting for email code."""
        from ozon_mcp.server import handle_login_with_email_code

        env_vars = {
            "ozon_username": "test@qq.com",
            "ozon_login_url": "https://test.ozon.ru/login",
            "qq_imap_auth_code": "test_auth_code",
        }

        mock_page = AsyncMock()
        mock_page.url = "https://test.ozon.ru/login"

        mock_browser_manager = MagicMock()
        mock_browser_manager.start = AsyncMock(return_value=mock_page)
        mock_browser_manager.page = mock_page
        mock_browser_manager.navigate = AsyncMock()
        mock_browser_manager.fill = AsyncMock()
        mock_browser_manager.click = AsyncMock()
        mock_browser_manager.stop = AsyncMock()

        mock_mail = MagicMock()
        mock_mail.connect.return_value = True
        mock_mail.wait_for_code.return_value = None  # Timeout
        mock_mail.disconnect = MagicMock()

        with patch.dict("os.environ", env_vars, clear=False), \
             patch("ozon_mcp.browser.BrowserManager", return_value=mock_browser_manager), \
             patch("ozon_mcp.mail.QQMailReader", return_value=mock_mail), \
             patch("ozon_mcp.server.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            result = await handle_login_with_email_code({})

            assert result["success"] is False
            assert "timeout" in result["error"].lower()
            assert result["code_received"] is None

    async def test_handle_login_with_email_code_missing_env_vars(self):
        """Test handling when environment variables are missing."""
        from ozon_mcp.server import handle_login_with_email_code

        # Ensure env vars are not set
        with patch.dict("os.environ", {}, clear=True):
            result = await handle_login_with_email_code({})

        # The result should indicate missing env vars
        assert result["success"] is False
        assert "Missing" in result["error"]


@pytest.mark.asyncio
class TestHandleGetMarketingActions:
    """Test marketing actions data extraction handler."""

    async def test_handle_get_marketing_actions_success(self):
        """Test successful data extraction."""
        from ozon_mcp.server import handle_get_marketing_actions

        mock_page = AsyncMock()
        mock_page.url = "https://seller.ozon.ru/app/prices/control?tab=marketing_actions"

        # Mock product row - use AsyncMock for async methods
        mock_row = AsyncMock()
        mock_name = AsyncMock()
        mock_name.inner_text = AsyncMock(return_value="Test Product")
        mock_sku = AsyncMock()
        mock_sku.inner_text = AsyncMock(return_value="SKU001")
        mock_price = AsyncMock()
        mock_price.inner_text = AsyncMock(return_value="1000")
        mock_min_price = AsyncMock()
        mock_min_price.inner_text = AsyncMock(return_value="800")

        mock_row.query_selector = AsyncMock(side_effect=[
            mock_name, mock_sku, mock_price, mock_min_price
        ])

        mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
        mock_page.query_selector = AsyncMock(return_value=None)  # No empty state

        mock_browser_manager = MagicMock()
        mock_browser_manager.start = AsyncMock(return_value=mock_page)
        mock_browser_manager.page = mock_page
        mock_browser_manager.navigate = AsyncMock()
        mock_browser_manager.stop = AsyncMock()

        with patch("ozon_mcp.browser.BrowserManager", return_value=mock_browser_manager), \
             patch("ozon_mcp.server.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            result = await handle_get_marketing_actions({
                "page": 1,
                "page_size": 20,
            })

            assert result["success"] is True
            assert "products" in result
            assert len(result["products"]) == 1
            assert result["products"][0]["name"] == "Test Product"
            assert result["products"][0]["sku"] == "SKU001"

    async def test_handle_get_marketing_actions_redirected_to_login(self):
        """Test handling when redirected to login page."""
        from ozon_mcp.server import handle_get_marketing_actions

        mock_page = AsyncMock()
        mock_page.url = "https://sso.ozon.ru/auth/ozonid"

        mock_browser_manager = MagicMock()
        mock_browser_manager.start = AsyncMock(return_value=mock_page)
        mock_browser_manager.page = mock_page
        mock_browser_manager.navigate = AsyncMock()
        mock_browser_manager.stop = AsyncMock()

        with patch("ozon_mcp.browser.BrowserManager", return_value=mock_browser_manager), \
             patch("ozon_mcp.server.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            result = await handle_get_marketing_actions({})

            assert result["success"] is False
            assert "login" in result["error"].lower() or "logged in" in result["error"].lower()

    async def test_handle_get_marketing_actions_empty_page(self):
        """Test handling empty page with no products."""
        from ozon_mcp.server import handle_get_marketing_actions

        mock_page = AsyncMock()
        mock_page.url = "https://seller.ozon.ru/app/prices/control?tab=marketing_actions"

        mock_page.query_selector_all = AsyncMock(return_value=[])  # No products
        mock_page.query_selector = AsyncMock(return_value=None)  # No empty state

        mock_browser_manager = MagicMock()
        mock_browser_manager.start = AsyncMock(return_value=mock_page)
        mock_browser_manager.page = mock_page
        mock_browser_manager.navigate = AsyncMock()
        mock_browser_manager.stop = AsyncMock()

        with patch("ozon_mcp.browser.BrowserManager", return_value=mock_browser_manager), \
             patch("ozon_mcp.server.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

            result = await handle_get_marketing_actions({
                "page": 1,
                "page_size": 10,
            })

            assert result["success"] is True
            assert len(result["products"]) == 0


@pytest.mark.asyncio
class TestCallTool:
    """Test the tool dispatcher."""

    async def test_call_tool_login_with_email_code(self):
        """Test dispatch to login handler."""
        from ozon_mcp.server import call_tool

        with patch("ozon_mcp.server.handle_login_with_email_code", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = {"success": True}
            result = await call_tool("login-with-email-code", {})

            mock_handler.assert_called_once_with({})
            assert result["success"] is True

    async def test_call_tool_get_marketing_actions(self):
        """Test dispatch to marketing actions handler."""
        from ozon_mcp.server import call_tool

        with patch("ozon_mcp.server.handle_get_marketing_actions", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = {"products": []}
            result = await call_tool("get-marketing-actions", {"page": 1})

            mock_handler.assert_called_once_with({"page": 1})
            assert result["products"] == []

    async def test_call_tool_unknown_tool(self):
        """Test handling unknown tool."""
        from ozon_mcp.server import call_tool

        result = await call_tool("unknown-tool", {})

        assert "error" in result
        assert "Unknown tool" in result["error"]


class TestListTools:
    """Test list_tools function."""

    def test_list_tools_returns_tools(self):
        """Test that list_tools returns available tools."""
        from ozon_mcp.server import list_tools

        tools = list_tools()

        assert isinstance(tools, list)
        assert len(tools) >= 2

        # Check for login tool
        login_tool = next((t for t in tools if t.name == "login-with-email-code"), None)
        assert login_tool is not None
        assert "登录" in login_tool.description or "OZON" in login_tool.description

        # Check for marketing actions tool
        marketing_tool = next((t for t in tools if t.name == "get-marketing-actions"), None)
        assert marketing_tool is not None
        assert "营销" in marketing_tool.description or "产品名称" in marketing_tool.description

    def test_list_tools_login_schema(self):
        """Test login tool has correct schema."""
        from ozon_mcp.server import list_tools

        tools = list_tools()
        login_tool = next((t for t in tools if t.name == "login-with-email-code"), None)

        assert login_tool is not None
        assert login_tool.inputSchema["type"] == "object"

    def test_list_tools_marketing_schema(self):
        """Test marketing actions tool has correct schema."""
        from ozon_mcp.server import list_tools

        tools = list_tools()
        marketing_tool = next((t for t in tools if t.name == "get-marketing-actions"), None)

        assert marketing_tool is not None
        props = marketing_tool.inputSchema["properties"]
        assert "page" in props
        assert "page_size" in props
        assert "all_pages" in props
