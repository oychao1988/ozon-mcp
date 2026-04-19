"""Browser manager for OZON MCP Server using Playwright."""

import asyncio
import os
import glob
import subprocess
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Page


def get_chrome_profile_path() -> Optional[str]:
    """Get Chrome profile path from .env or auto-detect.

    Returns:
        Chrome profile path or None if not found
    """
    # Try to load from .env
    from dotenv import load_dotenv
    load_dotenv()

    # Check .env for configured path
    env_profile_path = os.getenv("chrome_profile_path")
    if env_profile_path and os.path.exists(env_profile_path):
        print(f"Using Chrome profile from .env: {env_profile_path}")
        return env_profile_path

    # Try local chrome-profile directory
    local_profile = "./chrome-profile"
    if os.path.exists(local_profile):
        print(f"Using local Chrome profile: {local_profile}")
        return local_profile

    # Auto-detect Chrome profile on macOS
    if os.path.exists("/Applications/Google Chrome.app"):
        # Common macOS Chrome profile locations
        possible_paths = [
            os.path.expanduser("~/Library/Application Support/Google/Chrome"),
            "/Users/Shared/Google/Chrome",
        ]

        for base_path in possible_paths:
            if os.path.exists(base_path):
                # Look for Default profile
                default_profile = os.path.join(base_path, "Default")
                if os.path.exists(default_profile):
                    # Copy to local directory to avoid profile lock issues
                    import shutil
                    local_copy = "./chrome-profile"

                    if not os.path.exists(local_copy):
                        print(f"Copying Chrome profile from {default_profile} to {local_copy}...")
                        shutil.copytree(default_profile, local_copy)
                        print(f"Chrome profile copied successfully")
                    else:
                        print(f"Using existing Chrome profile: {local_copy}")
                    return os.path.abspath(local_copy)

    print("No Chrome profile found, will use clean browser context")
    return None


async def apply_stealth(page: Page):
    """Apply stealth evasions to a Playwright page to avoid bot detection."""
    stealth_script = """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
        configurable: true
    });
    """
    await page.evaluate(stealth_script)


async def stealth_page(page: Page):
    """Apply stealth evasions via init script (runs before page loads)."""
    stealth_script = """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
        configurable: true
    });
    Object.defineProperty(navigator, 'languages', {
        get: () => ['zh-CN', 'zh', 'en-US', 'en'],
        configurable: true
    });
    window.chrome = { runtime: {} };
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    Object.defineProperty(Notification, 'permission', {
        get: () => 'default',
        configurable: true
    });
    delete navigator.__proto__.webdriver;
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => 8,
        configurable: true
    });
    Object.defineProperty(navigator, 'deviceMemory', {
        get: () => 8,
        configurable: true
    });
    """
    await page.add_init_script(stealth_script)


class BrowserManager:
    """Manage Playwright browser with persistent context for OZON automation."""

    def __init__(
        self,
        profile_path: str = None,
        headless: bool = False,
        use_profile: bool = True,
        auto_detect_profile: bool = True
    ):
        """Initialize browser manager.

        Args:
            profile_path: Path to Chrome profile directory. If None, will auto-detect.
            headless: Whether to run browser in headless mode
            use_profile: Whether to use Chrome profile (set False to avoid CAPTCHA)
            auto_detect_profile: Whether to auto-detect Chrome profile if not provided
        """
        self.headless = headless
        self.use_profile = use_profile
        self.browser = None
        self.context = None
        self._page = None

        # Resolve profile path
        if profile_path:
            self.profile_path = profile_path
        elif auto_detect_profile:
            self.profile_path = get_chrome_profile_path()
        else:
            self.profile_path = None

    async def start(self) -> Page:
        """Launch browser with persistent context.

        Returns:
            Playwright Page instance
        """
        playwright = await async_playwright().start()
        self.browser = playwright

        # Determine if we should use profile
        use_user_data_dir = self.use_profile and self.profile_path and os.path.exists(self.profile_path)

        launch_options = {
            "headless": self.headless,
            "viewport": {"width": 1920, "height": 1080},
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--window-size=1920,1080",
            ],
        }

        if use_user_data_dir:
            print(f"Launching browser with Chrome profile: {self.profile_path}")
            launch_options["user_data_dir"] = self.profile_path
            launch_options["args"].extend([
                "--disable-features=IsolateOrigins,site-per-process",
            ])
        else:
            print("Launching browser without profile (clean context)")

        # Launch browser
        self.context = await playwright.chromium.launch_persistent_context(**launch_options)

        # Reuse existing page if available, otherwise create new one
        if self.context.pages:
            self._page = self.context.pages[0]
        else:
            self._page = await self.context.new_page()

        # Apply stealth evasions only if not using profile
        if not use_user_data_dir:
            await stealth_page(self._page)

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

    async def evaluate(self, expression: str) -> any:
        """Execute JavaScript on the page.

        Args:
            expression: JavaScript expression to evaluate

        Returns:
            Result of the expression
        """
        self._check_page()
        return await self._page.evaluate(expression)

    async def wait_for_title(self, title: str, timeout: int = 30000) -> bool:
        """Wait for page title to contain a specific string.

        Args:
            title: Title substring to wait for
            timeout: Timeout in milliseconds

        Returns:
            True if title matched, False if timeout
        """
        self._check_page()
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout / 1000:
            if title.lower() in (await self._page.title()).lower():
                return True
            await asyncio.sleep(0.5)
        return False

    async def is_captcha_page(self) -> bool:
        """Check if current page is a CAPTCHA/challenge page.

        Returns:
            True if CAPTCHA detected, False otherwise
        """
        self._check_page()
        title = await self._page.title()
        captcha_titles = ['доступ ограничен', 'access denied', 'captcha', 'antibot', 'challenge']
        return any(ct in title.lower() for ct in captcha_titles)

    async def get_current_url(self) -> str:
        """Get current page URL.

        Returns:
            Current page URL
        """
        self._check_page()
        return self._page.url

    async def get_title(self) -> str:
        """Get current page title.

        Returns:
            Current page title
        """
        self._check_page()
        return await self._page.title()
