"""OZON MCP Server - 浏览器自动化工具"""

__version__ = "0.1.1"

from .session import SessionManager
from .handlers.base import BaseHandler, HandlerError, RetryableError, FatalError
from ._selectors import SelectorConfig

__all__ = [
    "__version__",
    "SessionManager",
    "BaseHandler",
    "HandlerError",
    "RetryableError",
    "FatalError",
    "SelectorConfig",
]
