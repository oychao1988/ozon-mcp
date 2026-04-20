"""Tests for base handler and retry logic."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from ozon_mcp.handlers.base import (
    BaseHandler,
    HandlerError,
    RetryableError,
    FatalError,
    retry_on_retryable,
)


class TestRetryDecorator:
    """Test the retry decorator."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_third_attempt(self):
        """Function should succeed after 2 failures."""
        attempt_count = 0

        @retry_on_retryable(max_attempts=3, delay=0.01)
        async def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise RetryableError("Temporary failure")
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_raises_after_max_attempts(self):
        """Should raise last exception after max attempts reached."""
        call_count = 0

        @retry_on_retryable(max_attempts=2, delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise RetryableError("Permanent failure")

        with pytest.raises(RetryableError) as exc_info:
            await always_fails()

        assert str(exc_info.value) == "Permanent failure"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_non_retryable_error_not_retried(self):
        """FatalError should not be retried."""
        call_count = 0

        @retry_on_retryable(max_attempts=3, delay=0.01)
        async def fatal_error_function():
            nonlocal call_count
            call_count += 1
            raise FatalError("Fatal — do not retry")

        with pytest.raises(FatalError):
            await fatal_error_function()

        assert call_count == 1


class TestBaseHandler:
    """Test BaseHandler class."""

    def test_require_browser_raises_when_not_initialized(self):
        """require_browser should raise FatalError if browser is None."""
        handler = BaseHandler()
        with pytest.raises(FatalError) as exc_info:
            handler.require_browser()
        assert "Browser not initialized" in str(exc_info.value)

    def test_require_page_raises_when_no_page(self):
        """require_page should raise FatalError if page is None."""
        mock_browser = MagicMock()
        mock_browser.page = None
        handler = BaseHandler(browser_manager=mock_browser)

        with pytest.raises(FatalError) as exc_info:
            handler.require_page()
        assert "Page not available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cleanup_stops_browser_and_mail(self):
        """cleanup should stop browser and disconnect mail."""
        mock_browser = MagicMock()
        mock_browser.stop = AsyncMock()
        mock_mail = MagicMock()
        mock_mail.disconnect = MagicMock()

        handler = BaseHandler(browser_manager=mock_browser, mail_reader=mock_mail)
        await handler.cleanup()

        mock_browser.stop.assert_called_once()
        mock_mail.disconnect.assert_called_once()

    def test_handler_accepts_browser_and_mail(self):
        """Handler should store browser and mail references."""
        mock_browser = MagicMock()
        mock_mail = MagicMock()
        handler = BaseHandler(browser_manager=mock_browser, mail_reader=mock_mail)

        assert handler.browser == mock_browser
        assert handler.mail == mock_mail

    def test_set_selectors_config(self):
        """set_selectors_config should store the config."""
        handler = BaseHandler()
        mock_config = {"login": {}}
        handler.set_selectors_config(mock_config)

        assert handler._config == mock_config
