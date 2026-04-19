"""QQ Mail Reader 模块测试"""

import pytest
from unittest.mock import MagicMock, patch, Mock
import email
from email.message import EmailMessage

from mail import QQMailReader


class TestQQMailReaderInit:
    """测试 QQMailReader 构造函数"""

    def test_qq_mail_reader_init(self):
        """测试构造函数设置正确的值"""
        reader = QQMailReader(
            email="test@qq.com",
            auth_code="test_auth_code",
            imap_server="imap.qq.com",
            imap_port=993
        )
        assert reader.email == "test@qq.com"
        assert reader.auth_code == "test_auth_code"
        assert reader.imap_server == "imap.qq.com"
        assert reader.imap_port == 993
        assert reader._imap is None


class TestExtractCode:
    """测试验证码提取功能"""

    def test_extract_code_from_email(self):
        """测试从邮件内容中提取各种格式的验证码"""
        reader = QQMailReader(email="test@qq.com", auth_code="code")

        # 测试模式 1: 验证码：123456
        assert reader._extract_code("您的验证码是：123456") == "123456"

        # 测试模式 2: 验证码: 654321
        assert reader._extract_code("验证码: 654321") == "654321"

        # 测试模式 3: 验证码是123456
        assert reader._extract_code("验证码是123456") == "123456"

        # 测试模式 4: 验证码是 111111
        assert reader._extract_code("验证码是 111111") == "111111"

        # 测试模式 5: code: 222222
        assert reader._extract_code("code: 222222") == "222222"

        # 测试模式 6: code:333333
        assert reader._extract_code("code:333333") == "333333"

        # 测试模式 7: 纯 6 位数字（上下文边界）
        assert reader._extract_code("您好，您的验证码 999888，请查收") == "999888"

        # 测试模式 8: 大写模式
        assert reader._extract_code("验证码: 555666") == "555666"

        # 测试模式 9: 无验证码内容
        assert reader._extract_code("这是一封普通邮件") is None

        # 测试模式 10: 5 位数字不应被匹配
        assert reader._extract_code("订单号 12345") is None

        # 测试模式 11: 7 位数字不应被匹配
        assert reader._extract_code("订单号 1234567") is None

        # 测试模式 12: 嵌入在长字符串中
        assert reader._extract_code("尊敬的用户，您的验证码：123456，感谢您的使用。") == "123456"


class TestConnect:
    """测试连接功能"""

    @patch("mail.imaplib.IMAP4_SSL")
    def test_connect_success(self, mock_imap_class):
        """测试成功连接到 IMAP 服务器"""
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap

        reader = QQMailReader(email="test@qq.com", auth_code="auth_code")
        result = reader.connect()

        assert result is True
        mock_imap.login.assert_called_once_with("test@qq.com", "auth_code")

    @patch("mail.imaplib.IMAP4_SSL")
    def test_connect_failure(self, mock_imap_class):
        """测试连接失败时的处理"""
        mock_imap_class.side_effect = Exception("Connection refused")

        reader = QQMailReader(email="test@qq.com", auth_code="auth_code")
        result = reader.connect()

        assert result is False
        assert reader._imap is None


class TestDisconnect:
    """测试断开连接功能"""

    @patch("mail.imaplib.IMAP4_SSL")
    def test_disconnect_with_active_connection(self, mock_imap_class):
        """测试断开已连接的 IMAP"""
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap

        reader = QQMailReader(email="test@qq.com", auth_code="auth_code")
        reader.connect()
        reader.disconnect()

        mock_imap.close.assert_called_once()
        mock_imap.logout.assert_called_once()
        assert reader._imap is None

    def test_disconnect_without_connection(self):
        """测试断开时没有活动连接"""
        reader = QQMailReader(email="test@qq.com", auth_code="auth_code")
        # 不应抛出异常
        reader.disconnect()
        assert reader._imap is None


def _make_mock_msg(subject: str, body: str, from_addr: str = "noreply@ozon.ru") -> bytes:
    """创建模拟邮件消息的原始字节"""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = 'test@qq.com'
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    return msg.as_bytes()


class TestWaitForCode:
    """测试等待获取验证码功能"""

    @patch("mail.imaplib.IMAP4_SSL")
    @patch("mail.time.sleep")
    @patch("mail.time.time")
    def test_wait_for_code_timeout(self, mock_time, mock_sleep, mock_imap_class):
        """测试超时场景"""
        mock_imap = MagicMock()
        mock_imap_class.return_value = mock_imap

        # 模拟 search 返回空结果
        mock_imap.search.return_value = ('OK', [b''])
        mock_imap.select.return_value = ('OK', [b'0'])

        # 模拟时间：快速到达超时
        mock_time.side_effect = [0, 130, 131, 132, 133, 134]

        reader = QQMailReader(email="test@qq.com", auth_code="auth_code")
        result = reader.wait_for_code(subject_keyword="OZON", timeout=120, poll_interval=5)

        assert result is None
