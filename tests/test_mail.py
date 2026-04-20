"""Tests for mail module."""
import pytest
from unittest.mock import patch, MagicMock
import importlib


class TestIMAPTimeout:
    """Test that IMAP connections have a socket timeout."""

    def test_connect_sets_socket_timeout(self):
        """Verify IMAP connection sets a 30-second socket timeout."""
        import ozon_mcp.mail
        importlib.reload(ozon_mcp.mail)

        with patch("ozon_mcp.mail.imaplib.IMAP4_SSL") as mock_imap_class:
            mock_imap = MagicMock()
            mock_imap_class.return_value = mock_imap

            from ozon_mcp.mail import QQMailReader
            reader = QQMailReader("test@qq.com", "auth_code")
            reader.connect()

            # Check that IMAP4_SSL was called with timeout argument
            call_kwargs = mock_imap_class.call_args.kwargs
            assert "timeout" in call_kwargs, \
                f"timeout not passed to IMAP4_SSL. Got: {call_kwargs}"
            assert call_kwargs["timeout"] == 30, \
                f"timeout should be 30, got {call_kwargs['timeout']}"
