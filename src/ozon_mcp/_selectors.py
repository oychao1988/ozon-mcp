"""Selector configuration loader with hot-reload support."""
import os
import yaml
from typing import Any, Dict, Optional


class SelectorConfig:
    """Loads and caches selectors from YAML. Supports hot-reload in dev mode."""

    def __init__(self, yaml_path: Optional[str] = None):
        if yaml_path is None:
            yaml_path = os.path.join(os.path.dirname(__file__), "selectors.yaml")
        self._yaml_path = yaml_path
        self._cache: Dict[str, Any] = {}
        self._mtime: float = 0
        self._reload()

    def _reload(self):
        """Reload selectors from YAML file."""
        if not os.path.exists(self._yaml_path):
            raise FileNotFoundError(f"selectors.yaml not found: {self._yaml_path}")
        with open(self._yaml_path, "r", encoding="utf-8") as f:
            self._cache = yaml.safe_load(f)
        self._mtime = os.path.getmtime(self._yaml_path)

    def get(self, *keys: str, reload: bool = False) -> Any:
        """
        Get a selector value by nested keys.

        Example:
            config.get("login", "email_button")
            config.get("settings", "scroll", "max_iterations")

        Args:
            reload: If True, always reload from disk before reading.
        """
        if reload or self._should_reload():
            self._reload()

        value = self._cache
        for key in keys:
            value = value[key]
        return value

    def _should_reload(self) -> bool:
        """Check if file was modified since last load."""
        if not os.path.exists(self._yaml_path):
            return False
        return os.path.getmtime(self._yaml_path) > self._mtime

    def get_login_selectors(self) -> Dict[str, Any]:
        """Get all login-related selectors."""
        return self.get("login")

    def get_marketing_selectors(self) -> Dict[str, Any]:
        """Get all marketing-related selectors."""
        return self.get("marketing")

    def get_scroll_config(self) -> Dict[str, Any]:
        """Get scroll configuration."""
        return self.get("settings", "scroll")

    def get_pagination_config(self) -> Dict[str, Any]:
        """Get pagination configuration."""
        return self.get("settings", "pagination")

    def get_timeout_config(self) -> Dict[str, Any]:
        """Get timeout configuration."""
        return self.get("settings", "timeout")
