"""Browser manager for OZON MCP Server using Playwright."""

from playwright.async_api import async_playwright, Page


class BrowserManager:
    """Manage Playwright browser with persistent context for OZON automation."""

    def __init__(self, profile_path: str, headless: bool = False):
        """Initialize browser manager.

        Args:
            profile_path: Path to Chrome profile directory
            headless: Whether to run browser in headless mode
        """
        self.profile_path = profile_path
        self.headless = headless
        self.browser = None
        self.context = None
        self._page = None

    async def start(self) -> Page:
        """Launch browser with persistent context.

        Returns:
            Playwright Page instance
        """
        playwright = await async_playwright().start()
        self.browser = playwright

        # Launch browser with persistent context using Chrome profile
        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir=self.profile_path,
            headless=self.headless,
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
            ],
        )

        # Reuse existing page if available, otherwise create new one
        if self.context.pages:
            self._page = self.context.pages[0]
        else:
            self._page = await self.context.new_page()

        return self._page

    async def stop(self):
        """Close browser and cleanup resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.stop()
        self.browser = None
        self.context = None
        self._page = None

    @property
    def page(self) -> Page:
        """Get the current page.

        Returns:
            Playwright Page instance

        Raises:
            RuntimeError: If page is not initialized
        """
        if self._page is None:
            raise RuntimeError("Page not initialized. Call start() first.")
        return self._page

    def _check_page(self):
        """Check if page is initialized."""
        if self._page is None:
            raise RuntimeError("Page not initialized. Call start() first.")

    async def navigate(self, url: str, wait_until: str = "networkidle"):
        """Navigate to URL.

        Args:
            url: URL to navigate to
            wait_until: Wait condition (load, domcontentloaded, networkidle)
        """
        self._check_page()
        await self._page.goto(url, wait_until=wait_until)

    async def fill(self, selector: str, value: str):
        """Fill input field.

        Args:
            selector: CSS selector for the input element
            value: Value to fill
        """
        self._check_page()
        await self._page.fill(selector, value)

    async def click(self, selector: str):
        """Click element.

        Args:
            selector: CSS selector for the element to click
        """
        self._check_page()
        await self._page.click(selector)

    async def wait_for_selector(self, selector: str, timeout: int = 10000):
        """Wait for element to appear.

        Args:
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds
        """
        self._check_page()
        await self._page.wait_for_selector(selector, timeout=timeout)

    async def get_text(self, selector: str) -> str:
        """Get inner text of element.

        Args:
            selector: CSS selector for the element

        Returns:
            Inner text of the element
        """
        self._check_page()
        element = await self._page.wait_for_selector(selector)
        return await element.inner_text()

    async def get_input_value(self, selector: str) -> str:
        """Get value of input element.

        Args:
            selector: CSS selector for the input element

        Returns:
            Input value
        """
        self._check_page()
        element = await self._page.wait_for_selector(selector)
        return await element.input_value()

    async def scroll_to_bottom(self):
        """Scroll to bottom of page."""
        self._check_page()
        await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    async def wait_for_load_state(self, state: str = "networkidle"):
        """Wait for page load state.

        Args:
            state: Load state to wait for (load, domcontentloaded, networkidle)
        """
        self._check_page()
        await self._page.wait_for_load_state(state)
