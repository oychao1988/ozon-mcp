"""QQ 邮箱 IMAP 操作模块"""

import imaplib
import email
import re
import time
from typing import Optional


class QQMailReader:
    """QQ 邮箱读取器，用于获取验证码"""

    def __init__(
        self,
        email: str,
        auth_code: str,
        imap_server: str = "imap.qq.com",
        imap_port: int = 993
    ):
        self.email = email
        self.auth_code = auth_code
        self.imap_server = imap_server
        self.imap_port = imap_port
        self._imap = None

    def connect(self) -> bool:
        """连接到 IMAP 服务器"""
        try:
            self._imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self._imap.login(self.email, self.auth_code)
            return True
        except Exception as e:
            print(f"IMAP 连接失败: {e}")
            return False

    def disconnect(self):
        """断开 IMAP 连接"""
        if self._imap:
            try:
                self._imap.close()
                self._imap.logout()
            except:
                pass
            self._imap = None

    def _extract_code(self, content: str) -> Optional[str]:
        """从邮件内容提取 6 位验证码"""
        patterns = [
            r'验证码[：:]\s*(\d{6})',
            r'验证码是[：:]?\s*(\d{6})',
            r'code[：:]\s*(\d{6})',
            r'(?<!\d)(\d{6})(?!\d)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def wait_for_code(
        self,
        subject_keyword: str = "OZON",
        timeout: int = 120,
        poll_interval: int = 5
    ) -> Optional[str]:
        """等待并获取验证码邮件"""
        if not self._imap and not self.connect():
            return None

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                self._imap.select('INBOX')
                _, messages = self._imap.search(None, 'UNSEEN')
                message_ids = messages[0].split()

                for msg_id in reversed(message_ids):
                    _, msg_data = self._imap.fetch(msg_id, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])

                    subject = email.header.decode_header(msg['Subject'])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode('utf-8', errors='ignore')

                    if subject_keyword.lower() in subject.lower():
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == 'text/plain':
                                    body_bytes = part.get_payload(decode=True)
                                    if body_bytes:
                                        body += body_bytes.decode('utf-8', errors='ignore')
                        else:
                            body_bytes = msg.get_payload(decode=True)
                            if body_bytes:
                                body = body_bytes.decode('utf-8', errors='ignore')

                        code = self._extract_code(body)
                        if code:
                            self._imap.store(msg_id, '+FLAGS', '\\Seen')
                            return code

            except Exception as e:
                print(f"检查邮件时出错: {e}")

            time.sleep(poll_interval)

        return None
