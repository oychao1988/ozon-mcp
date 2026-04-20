"""Tests for selector config loader."""
import pytest
import tempfile
import os
import time


def test_selector_config_loads_yaml():
    """Test that SelectorConfig loads values from YAML."""
    yaml_content = """
login:
  email_login_button: 'button:has-text("登录")'
  settings:
    timeout: 30
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        yaml_path = f.name

    try:
        from ozon_mcp._selectors import SelectorConfig
        config = SelectorConfig(yaml_path=yaml_path)

        assert config.get("login", "email_login_button") == 'button:has-text("登录")'
        assert config.get("login", "settings", "timeout") == 30
    finally:
        os.unlink(yaml_path)


def test_selector_config_get_login_selectors():
    """Test convenience method returns login selectors dict."""
    yaml_content = """
login:
  email_login_button: 'button:has-text("登录")'
  otp_inputs:
    - 'input[type="text"]'
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        yaml_path = f.name

    try:
        from ozon_mcp._selectors import SelectorConfig
        config = SelectorConfig(yaml_path=yaml_path)
        selectors = config.get_login_selectors()

        assert isinstance(selectors, dict)
        assert "email_login_button" in selectors
        assert selectors["otp_inputs"] == ["input[type=\"text\"]"]
    finally:
        os.unlink(yaml_path)


def test_selector_config_get_scroll_config():
    """Test convenience method returns scroll config."""
    yaml_content = """
settings:
  scroll:
    max_iterations: 20
    delay_seconds: 1.0
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        yaml_path = f.name

    try:
        from ozon_mcp._selectors import SelectorConfig
        config = SelectorConfig(yaml_path=yaml_path)
        scroll = config.get_scroll_config()

        assert scroll["max_iterations"] == 20
        assert scroll["delay_seconds"] == 1.0
    finally:
        os.unlink(yaml_path)
