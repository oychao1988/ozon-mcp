import os
import re
import imaplib
import email
import time
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_code(body: str) -> Optional[str]:
    """Extract 6-digit code from email body"""
    # Clean HTML tags
    clean_text = re.sub(r'<[^>]+>', ' ', body)
    # Common patterns for OZON OTP
    patterns = [
        r'код\s*[:\-]?\s*(\d{6})',
        r'code\s*[:\-]?\s*(\d{6})',
        r'验证码\s*[:\-]?\s*(\d{6})',
        r'(\d{6})' 
    ]
    for pattern in patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def fetch_latest_code():
    email_addr = os.getenv("ozon_username")
    auth_code = os.getenv("qq_imap_auth_code")
    
    if not email_addr or not auth_code:
        return "Error: Missing credentials in .env"

    try:
        # Connect to QQ Mail IMAP
        mail = imaplib.IMAP4_SSL("imap.qq.com")
        mail.login(email_addr, auth_code)
        mail.select("INBOX")

        # Search for OZON emails
        status, messages = mail.search(None, '(SUBJECT "OZON")')
        
        if status == 'OK' and messages[0]:
            # Get the latest message ID
            latest_id = messages[0].split()[-1]
            res, msg_data = mail.fetch(latest_id, "(RFC822)")
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Extract body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() in ["text/plain", "text/html"]:
                                body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    code = extract_code(body)
                    if code:
                        return code
        mail.close()
        mail.logout()
    except Exception as e:
        return f"Error connecting to mail: {str(e)}"
    
    return None

if __name__ == "__main__":
    code = fetch_latest_code()
    if code:
        print(code)
    else:
        print("NOT_FOUND")
