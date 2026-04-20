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

            call_kwargs = mock_imap_class.call_args.kwargs
            assert "timeout" in call_kwargs, \
                f"timeout not passed to IMAP4_SSL. Got: {call_kwargs}"
            assert call_kwargs["timeout"] == 30, \
                f"timeout should be 30, got {call_kwargs['timeout']}"


class TestMailPollingBackoff:
    """Test that wait_for_code uses exponential backoff."""

    def test_wait_for_code_increases_poll_interval(self):
        """Verify poll interval grows exponentially when no code found."""
        import ozon_mcp.mail
        importlib.reload(ozon_mcp.mail)

        with patch("ozon_mcp.mail.imaplib.IMAP4_SSL") as mock_imap_class:
            mock_imap = MagicMock()
            mock_imap.search.return_value = ("OK", [b""])
            mock_imap.select.return_value = ("OK", [b"0"])
            mock_imap_class.return_value = mock_imap

            sleep_calls = []

            def mock_sleep(s):
                sleep_calls.append(s)

            # Simulate time: 0, 5, 10, 15, 20, 25, 30, 35
            time_values = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0]

            with patch.object(ozon_mcp.mail.time, "sleep", mock_sleep):
                with patch.object(ozon_mcp.mail.time, "time",
                                 side_effect=time_values):
                    from ozon_mcp.mail import QQMailReader
                    reader = QQMailReader("test@qq.com", "auth_code")
                    reader.connect()
                    with patch.object(reader, "get_unread_ozon_emails", return_value=[]):
                        result = reader.wait_for_code(timeout=30, poll_interval=5)

        assert len(sleep_calls) >= 2, f"Expected multiple sleeps, got: {sleep_calls}"
        assert sleep_calls[1] > sleep_calls[0], \
            f"Expected exponential growth in sleep intervals: {sleep_calls}"
