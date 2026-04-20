"""QQ 邮箱 IMAP 操作模块"""

import imaplib
import email
import re
import time
import random
from typing import Optional, List, Tuple


class QQMailReader:
    """QQ 邮箱读取器，用于获取验证码"""

    def __init__(
        self,
        email_addr: str,
        auth_code: str,
        imap_server: str = "imap.qq.com",
        imap_port: int = 993
    ):
        self.email = email_addr
        self.auth_code = auth_code
        self.imap_server = imap_server
        self.imap_port = imap_port
        self._imap = None

    def connect(self) -> bool:
        """连接到 IMAP 服务器"""
        try:
            self._imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=30)
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

    def _extract_code_from_text(self, text: str) -> Optional[str]:
        """从纯文本提取 6 位验证码

        Args:
            text: 邮件纯文本内容

        Returns:
            验证码字符串或 None
        """
        # 清理 HTML 标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # OZON 验证码匹配模式
        patterns = [
            # 俄语: код 819831
            r'код\s*[:\-]?\s*(\d{6})',
            # 俄语: для подтверждения ... используйте код
            r'используйте\s*код\s*[:\-]?\s*(\d{6})',
            # 通用 6 位数字（在验证码相关词后面）
            r'(?:ваш|ваш\s*код|your\s*code)\s*[:\-]?\s*(\d{6})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_code_from_html(self, html: str) -> Optional[str]:
        """从 HTML 中提取验证码

        Args:
            html: 邮件 HTML 内容

        Returns:
            验证码字符串或 None
        """
        # 清理 HTML 并提取文本
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        return self._extract_code_from_text(text)

    def get_unread_ozon_emails(self, limit: int = 5) -> List[dict]:
        """获取未读的 OZON 邮件

        Args:
            limit: 返回的最大邮件数量

        Returns:
            邮件列表，每项包含 id, subject, date, body
        """
        if not self._imap and not self.connect():
            return []

        try:
            self._imap.select('INBOX')
            _, messages = self._imap.search(None, 'UNSEEN')

            if not messages[0]:
                # 如果没有未读邮件，获取最近的邮件
                _, messages = self._imap.search(None, 'ALL')

            message_ids = messages[0].split()
            if not message_ids:
                return []

            ozon_emails = []

            # 从最新的邮件开始检查
            for msg_id in reversed(message_ids[-50:]):
                try:
                    _, msg_data = self._imap.fetch(msg_id, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])

                    # 解码主题
                    subject_parts = email.header.decode_header(msg['Subject'])
                    subject = ""
                    for part, encoding in subject_parts:
                        if isinstance(part, bytes):
                            subject += part.decode(encoding or 'utf-8', errors='ignore')
                        else:
                            subject += part

                    # 检查是否是 OZON 邮件
                    if 'OZON' not in subject.upper() and 'Ozon' not in subject and 'ozon' not in subject:
                        continue

                    # 获取邮件正文
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body += payload.decode('utf-8', errors='ignore')
                            elif part.get_content_type() == 'text/html' and not body:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body += payload.decode('utf-8', errors='ignore')
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')

                    ozon_emails.append({
                        'id': msg_id.decode(),
                        'subject': subject,
                        'date': msg['Date'],
                        'body': body,
                    })

                    if len(ozon_emails) >= limit:
                        break

                except Exception as e:
                    print(f"处理邮件 {msg_id} 时出错: {e}")
                    continue

            return ozon_emails

        except Exception as e:
            print(f"获取邮件列表时出错: {e}")
            return []

    def get_latest_ozon_code(self) -> Optional[str]:
        """获取最新的 OZON 验证码

        Returns:
            验证码字符串或 None
        """
        emails = self.get_unread_ozon_emails(limit=10)

        for email_data in emails:
            body = email_data.get('body', '')

            # 尝试从 HTML 提取
            code = self._extract_code_from_html(body)
            if code:
                return code

        return None

    def wait_for_code(
        self,
        subject_keyword: str = "OZON",
        timeout: int = 120,
        poll_interval: int = 5
    ) -> Optional[str]:
        """等待并获取验证码邮件

        Args:
            subject_keyword: 邮件主题关键词
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）

        Returns:
            验证码字符串或 None
        """
        if not self._imap and not self.connect():
            return None

        start_time = time.time()
        attempt = 0

        while time.time() - start_time < timeout:
            try:
                # 获取最新的 OZON 邮件
                emails = self.get_unread_ozon_emails(limit=3)

                for email_data in emails:
                    body = email_data.get('body', '')

                    # 提取验证码
                    code = self._extract_code_from_html(body)
                    if code:
                        # 标记邮件为已读
                        try:
                            self._imap.store(email_data['id'].encode(), '+FLAGS', '\\Seen')
                        except:
                            pass
                        return code

            except Exception as e:
                print(f"检查邮件时出错: {e}")

            # Exponential backoff: increase interval each attempt, cap at 60s
            attempt += 1
            backoff = min(poll_interval * (2 ** attempt) + random.uniform(0, 1), 60)
            time.sleep(backoff)

        return None

    def search_emails(
        self,
        keyword: str,
        folder: str = 'INBOX',
        limit: int = 20
    ) -> List[dict]:
        """搜索邮件

        Args:
            keyword: 搜索关键词
            folder: 邮件文件夹
            limit: 返回的最大数量

        Returns:
            匹配的邮件列表
        """
        if not self._imap and not self.connect():
            return []

        try:
            self._imap.select(folder)
            _, messages = self._imap.search(None, f'ALL')

            message_ids = messages[0].split()
            results = []

            for msg_id in reversed(message_ids[-limit:]):
                try:
                    _, msg_data = self._imap.fetch(msg_id, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])

                    # 解码主题
                    subject_parts = email.header.decode_header(msg['Subject'])
                    subject = ""
                    for part, encoding in subject_parts:
                        if isinstance(part, bytes):
                            subject += part.decode(encoding or 'utf-8', errors='ignore')
                        else:
                            subject += part

                    if keyword.lower() in subject.lower():
                        results.append({
                            'id': msg_id.decode(),
                            'subject': subject,
                            'date': msg['Date'],
                        })

                except Exception:
                    continue

            return results

        except Exception as e:
            print(f"搜索邮件时出错: {e}")
            return []
