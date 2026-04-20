"""Base handler with retry and error recovery logic."""
import asyncio
import functools
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class HandlerError(Exception):
    """Base exception for handler errors."""

    def __init__(self, message: str, recoverable: bool = True):
        super().__init__(message)
        self.message = message
        self.recoverable = recoverable


class RetryableError(HandlerError):
    """Error that should trigger a retry."""

    def __init__(self, message: str):
        super().__init__(message, recoverable=True)


class FatalError(HandlerError):
    """Error that should not be retried."""

    def __init__(self, message: str):
        super().__init__(message, recoverable=False)


def retry_on_retryable(
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: tuple = (RetryableError,),
):
    """
    Decorator that retries on RetryableError with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each attempt.
        exceptions: Tuple of exception types that trigger retry.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception

        return wrapper

    return decorator


class BaseHandler:
    """
    Base class for MCP tool handlers.

    Provides common retry logic, error recovery, and browser session management.
    Subclasses implement the specific tool logic.
    """

    def __init__(self, browser_manager=None, mail_reader=None):
        self.browser = browser_manager
        self.mail = mail_reader
        self._config = None

    def set_selectors_config(self, config):
        """Inject selector config (allows dependency injection for testing)."""
        self._config = config

    async def cleanup(self):
        """Clean up resources. Override in subclass for specific cleanup."""
        if self.browser:
            await self.browser.stop()
        if self.mail:
            self.mail.disconnect()

    def require_browser(self):
        """Raise FatalError if browser is not initialized."""
        if not self.browser:
            raise FatalError("Browser not initialized. Call start() first.")

    def require_page(self):
        """Raise FatalError if page is not available."""
        self.require_browser()
        if not self.browser.page:
            raise FatalError("Page not available")
