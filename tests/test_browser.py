"""Tests for browser module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
class TestBrowserManager:
    """Test BrowserManager class."""

    async def test_browser_manager_init(self):
        """Test BrowserManager initialization."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./chrome-profile", headless=True)

        assert manager.profile_path == "./chrome-profile"
        assert manager.headless is True
        assert manager.browser is None
        assert manager.context is None
        assert manager._page is None

    async def test_browser_manager_init_defaults(self):
        """Test BrowserManager initialization with defaults."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        assert manager.profile_path == "./profile"
        assert manager.headless is False

    async def test_browser_context_creation(self):
        """Test browser context creation with mocking."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./chrome-profile", headless=True)

        # Mock the playwright instance
        mock_playwright = MagicMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # Set up the mock chain
        mock_playwright.chromium.launch_persistent_context = AsyncMock(return_value=mock_context)
        mock_context.pages = [mock_page]
        mock_playwright.start = AsyncMock(return_value=mock_playwright)

        with patch("ozon_mcp.browser.async_playwright", return_value=mock_playwright):
            page = await manager.start()

            # Verify start was called on playwright
            mock_playwright.start.assert_called_once()

            # Verify launch_persistent_context was called with correct args
            mock_playwright.chromium.launch_persistent_context.assert_called_once()
            call_args = mock_playwright.chromium.launch_persistent_context.call_args

            # Check user_data_dir
            assert call_args.kwargs["user_data_dir"] == "./chrome-profile"

            # Check headless
            assert call_args.kwargs["headless"] is True

            # Check viewport
            assert call_args.kwargs["viewport"] == {"width": 1280, "height": 800}

            # Check args contain expected flags
            args = call_args.kwargs.get("args", [])
            assert "--disable-blink-features=AutomationControlled" in args
            assert "--disable-web-security" in args

            # Verify existing page was reused
            assert manager._page == mock_page
            assert page == mock_page

    async def test_start_creates_new_page_if_none_exists(self):
        """Test that start creates new page if context has no pages."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        mock_playwright = MagicMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_context.pages = []  # No existing pages
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_playwright.chromium.launch_persistent_context = AsyncMock(return_value=mock_context)
        mock_playwright.start = AsyncMock(return_value=mock_playwright)

        with patch("ozon_mcp.browser.async_playwright", return_value=mock_playwright):
            page = await manager.start()

            # Verify new_page was called
            mock_context.new_page.assert_called_once()
            assert page == mock_page

    async def test_stop_closes_browser(self):
        """Test that stop closes browser properly."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        mock_context = AsyncMock()
        mock_playwright_obj = AsyncMock()

        manager.context = mock_context
        manager.browser = mock_playwright_obj

        await manager.stop()

        mock_context.close.assert_called_once()
        mock_playwright_obj.stop.assert_called_once()
        assert manager.browser is None
        assert manager.context is None
        assert manager._page is None

    async def test_page_property_raises_if_no_page(self):
        """Test that page property raises RuntimeError if page not initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        with pytest.raises(RuntimeError, match="Page not initialized"):
            _ = manager.page

    async def test_page_property_returns_page(self):
        """Test that page property returns the page if initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")
        mock_page = MagicMock()
        manager._page = mock_page

        assert manager.page == mock_page

    async def test_navigate_raises_if_no_page(self):
        """Test that navigate raises RuntimeError if page not initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        with pytest.raises(RuntimeError, match="Page not initialized"):
            await manager.navigate("https://example.com")

    async def test_navigate_calls_goto(self):
        """Test that navigate calls goto with correct parameters."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")
        mock_page = AsyncMock()
        manager._page = mock_page

        await manager.navigate("https://example.com", wait_until="networkidle")

        mock_page.goto.assert_called_once_with("https://example.com", wait_until="networkidle")

    async def test_fill_raises_if_no_page(self):
        """Test that fill raises RuntimeError if page not initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        with pytest.raises(RuntimeError, match="Page not initialized"):
            await manager.fill("#input", "value")

    async def test_fill_calls_fill(self):
        """Test that fill calls fill on page."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")
        mock_page = AsyncMock()
        manager._page = mock_page

        await manager.fill("#input", "test value")

        mock_page.fill.assert_called_once_with("#input", "test value")

    async def test_click_raises_if_no_page(self):
        """Test that click raises RuntimeError if page not initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        with pytest.raises(RuntimeError, match="Page not initialized"):
            await manager.click("#button")

    async def test_click_calls_click(self):
        """Test that click calls click on page."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")
        mock_page = AsyncMock()
        manager._page = mock_page

        await manager.click("#button")

        mock_page.click.assert_called_once_with("#button")

    async def test_wait_for_selector_raises_if_no_page(self):
        """Test that wait_for_selector raises RuntimeError if page not initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        with pytest.raises(RuntimeError, match="Page not initialized"):
            await manager.wait_for_selector("#element")

    async def test_wait_for_selector_calls_wait_for_selector(self):
        """Test that wait_for_selector calls wait_for_selector on page."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")
        mock_page = AsyncMock()
        manager._page = mock_page

        await manager.wait_for_selector("#element", timeout=5000)

        mock_page.wait_for_selector.assert_called_once_with("#element", timeout=5000)

    async def test_get_text_raises_if_no_page(self):
        """Test that get_text raises RuntimeError if page not initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        with pytest.raises(RuntimeError, match="Page not initialized"):
            await manager.get_text("#element")

    async def test_get_text_returns_text(self):
        """Test that get_text returns inner_text from page."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.inner_text = AsyncMock(return_value="Hello World")
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)
        manager._page = mock_page

        result = await manager.get_text("#element")

        assert result == "Hello World"
        mock_page.wait_for_selector.assert_called_once_with("#element")

    async def test_get_input_value_raises_if_no_page(self):
        """Test that get_input_value raises RuntimeError if page not initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        with pytest.raises(RuntimeError, match="Page not initialized"):
            await manager.get_input_value("#input")

    async def test_get_input_value_returns_value(self):
        """Test that get_input_value returns input value from page."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.input_value = AsyncMock(return_value="input content")
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)
        manager._page = mock_page

        result = await manager.get_input_value("#input")

        assert result == "input content"
        mock_page.wait_for_selector.assert_called_once_with("#input")

    async def test_scroll_to_bottom_raises_if_no_page(self):
        """Test that scroll_to_bottom raises RuntimeError if page not initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        with pytest.raises(RuntimeError, match="Page not initialized"):
            await manager.scroll_to_bottom()

    async def test_scroll_to_bottom_evaluates_script(self):
        """Test that scroll_to_bottom evaluates scroll script."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")
        mock_page = AsyncMock()
        manager._page = mock_page

        await manager.scroll_to_bottom()

        mock_page.evaluate.assert_called_once_with("window.scrollTo(0, document.body.scrollHeight)")

    async def test_wait_for_load_state_raises_if_no_page(self):
        """Test that wait_for_load_state raises RuntimeError if page not initialized."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")

        with pytest.raises(RuntimeError, match="Page not initialized"):
            await manager.wait_for_load_state("networkidle")

    async def test_wait_for_load_state_calls_wait_for_load_state(self):
        """Test that wait_for_load_state calls wait_for_load_state on page."""
        from ozon_mcp.browser import BrowserManager

        manager = BrowserManager(profile_path="./profile")
        mock_page = AsyncMock()
        manager._page = mock_page

        await manager.wait_for_load_state("networkidle")

        mock_page.wait_for_load_state.assert_called_once_with("networkidle")
