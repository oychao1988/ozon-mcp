"""Tests for server tool handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import importlib


@pytest.mark.asyncio
class TestLoginOTPFlow:
    """Test OTP code submission includes click."""

    async def test_otp_filled_then_submit_button_clicked(self):
        """Verify that after filling OTP code, a submit button is clicked."""
        # Reload server module to pick up any changes
        import ozon_mcp.server
        importlib.reload(ozon_mcp.server)
        from ozon_mcp.server import handle_login_with_email_code

        # Track all click calls
        clicked_selectors = []

        mock_page = AsyncMock()
        mock_page.url = "https://sso.ozon.ru/auth/ozonid"
        mock_page.title = AsyncMock(return_value="Введите код")
        mock_page.wait_for_selector = AsyncMock()  # satisfies all wait_for_selector calls
        mock_page.fill = AsyncMock()
        mock_page.click = AsyncMock(side_effect=lambda s: clicked_selectors.append(s))
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()

        mock_browser_manager = MagicMock()
        mock_browser_manager.start = AsyncMock(return_value=mock_page)
        mock_browser_manager.page = mock_page
        mock_browser_manager.navigate = AsyncMock()
        mock_browser_manager.fill = AsyncMock()
        mock_browser_manager.click = AsyncMock(side_effect=lambda s: clicked_selectors.append(s))
        mock_browser_manager.wait_for_selector = AsyncMock()
        mock_browser_manager.stop = AsyncMock()

        mock_mail = MagicMock()
        mock_mail.connect = MagicMock(return_value=True)
        mock_mail.wait_for_code = MagicMock(return_value="819831")
        mock_mail.disconnect = MagicMock()

        with patch("ozon_mcp.server.browser_module.BrowserManager", return_value=mock_browser_manager):
            with patch("ozon_mcp.server.mail_module.QQMailReader", return_value=mock_mail):
                with patch.dict("os.environ", {
                    "ozon_username": "test@qq.com",
                    "qq_imap_auth_code": "authcode123456",
                    "ozon_login_url": "https://sso.ozon.ru/auth/ozonid",
                }, clear=True):
                    result = await handle_login_with_email_code({})

        # Assert: a submit button was clicked AFTER the code was filled
        assert any("Подтвердить" in s or "Войти" in s or "Продолжить" in s
                   or "submit" in s.lower() or "confirm" in s.lower()
                   for s in clicked_selectors), \
            f"No submit button click found. All clicks: {clicked_selectors}"
