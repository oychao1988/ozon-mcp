"""Tests for SessionManager."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSessionManager:
    """Test SessionManager class."""

    @pytest.mark.asyncio
    async def test_create_session_returns_browser_manager(self):
        """create_session should return a BrowserManager instance."""
        with patch("ozon_mcp.session.BrowserManager") as MockBrowser:
            mock_browser = MagicMock()
            mock_browser.start = AsyncMock()
            MockBrowser.return_value = mock_browser

            from ozon_mcp.session import SessionManager
            manager = SessionManager()

            result = await manager.create_session("test_session")

            assert result == mock_browser
            assert manager.has_session("test_session")
            mock_browser.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_session_raises(self):
        """Creating a session with existing name should raise ValueError."""
        with patch("ozon_mcp.session.BrowserManager") as MockBrowser:
            mock_browser = MagicMock()
            mock_browser.start = AsyncMock()
            MockBrowser.return_value = mock_browser

            from ozon_mcp.session import SessionManager
            manager = SessionManager()

            await manager.create_session("dup_session")

            with pytest.raises(ValueError) as exc_info:
                await manager.create_session("dup_session")

            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_session_returns_none_for_missing(self):
        """get_session should return None for non-existent session."""
        from ozon_mcp.session import SessionManager
        manager = SessionManager()
        assert manager.get_session("missing") is None

    @pytest.mark.asyncio
    async def test_close_session_stops_and_removes(self):
        """close_session should stop browser and remove from dict."""
        with patch("ozon_mcp.session.BrowserManager") as MockBrowser:
            mock_browser = MagicMock()
            mock_browser.start = AsyncMock()
            mock_browser.stop = AsyncMock()
            MockBrowser.return_value = mock_browser

            from ozon_mcp.session import SessionManager
            manager = SessionManager()

            await manager.create_session("to_close")
            assert manager.has_session("to_close")

            result = await manager.close_session("to_close")

            assert result is True
            assert not manager.has_session("to_close")
            mock_browser.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_all_stops_everything(self):
        """close_all should stop all sessions."""
        with patch("ozon_mcp.session.BrowserManager") as MockBrowser:
            mock_browser1 = MagicMock()
            mock_browser1.start = AsyncMock()
            mock_browser1.stop = AsyncMock()
            mock_browser2 = MagicMock()
            mock_browser2.start = AsyncMock()
            mock_browser2.stop = AsyncMock()
            MockBrowser.side_effect = [mock_browser1, mock_browser2]

            from ozon_mcp.session import SessionManager
            manager = SessionManager()

            await manager.create_session("session_1")
            await manager.create_session("session_2")

            await manager.close_all()

            assert len(manager.list_sessions()) == 0
            mock_browser1.stop.assert_called_once()
            mock_browser2.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_sessions_returns_all_names(self):
        """list_sessions should return all active session names."""
        with patch("ozon_mcp.session.BrowserManager") as MockBrowser:
            mock_browser = MagicMock()
            mock_browser.start = AsyncMock()
            MockBrowser.return_value = mock_browser

            from ozon_mcp.session import SessionManager
            manager = SessionManager()

            await manager.create_session("a")
            await manager.create_session("b")
            await manager.create_session("c")

            sessions = manager.list_sessions()
            assert set(sessions) == {"a", "b", "c"}
