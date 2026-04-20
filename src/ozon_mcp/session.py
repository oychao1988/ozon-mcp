"""Multi-account session manager.

Allows running multiple OZON accounts simultaneously, each with its own
BrowserManager instance and Chrome profile.
"""
from typing import Dict, Optional
import asyncio
from .browser import BrowserManager


class SessionManager:
    """
    Manages multiple named browser sessions, one per OZON account.

    Usage:
        manager = SessionManager()
        await manager.create_session("account_a", profile_path="./profiles/a")
        await manager.create_session("account_b", profile_path="./profiles/b")

        session_a = manager.get_session("account_a")
        await session_a.navigate("https://seller.ozon.ru/...")

        await manager.close_session("account_a")
    """

    def __init__(self):
        self._sessions: Dict[str, BrowserManager] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def create_session(
        self,
        name: str,
        profile_path: Optional[str] = None,
        headless: bool = False,
        **browser_kwargs,
    ) -> BrowserManager:
        """
        Create a new named session with its own browser.

        Args:
            name: Unique session identifier (e.g., account email).
            profile_path: Chrome profile path. Auto-detected if None.
            headless: Whether to run headless.
            **browser_kwargs: Additional args passed to BrowserManager.

        Returns:
            The BrowserManager for this session.

        Raises:
            ValueError: If session name already exists.
        """
        if name in self._sessions:
            raise ValueError(f"Session '{name}' already exists. Use close_session() first.")

        if name not in self._locks:
            self._locks[name] = asyncio.Lock()

        browser = BrowserManager(
            profile_path=profile_path or f"./chrome-profile-{name}",
            headless=headless,
            use_profile=True,
            auto_detect_profile=profile_path is None,
            **browser_kwargs,
        )

        self._sessions[name] = browser
        await browser.start()
        return browser

    def get_session(self, name: str) -> Optional[BrowserManager]:
        """Get the BrowserManager for a named session, or None if not found."""
        return self._sessions.get(name)

    def has_session(self, name: str) -> bool:
        """Check if a session exists."""
        return name in self._sessions

    def list_sessions(self) -> list[str]:
        """List all active session names."""
        return list(self._sessions.keys())

    async def close_session(self, name: str) -> bool:
        """
        Close and remove a named session.

        Returns:
            True if session was closed, False if it didn't exist.
        """
        browser = self._sessions.pop(name, None)
        if browser:
            await browser.stop()
            self._locks.pop(name, None)
            return True
        return False

    async def close_all(self):
        """Close all sessions and clean up."""
        names = list(self._sessions.keys())
        for name in names:
            await self.close_session(name)
