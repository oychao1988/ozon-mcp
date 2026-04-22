import json
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_price(price_str: str) -> float:
    """Parse price string like '438,00 ¥' to float"""
    if not price_str or "未指定" in price_str:
        return float('inf') 
    
    # Remove currency and all types of spaces
    clean = price_str.replace('¥', '').replace('\xa0', '').replace(' ', '').replace('\u00a0', '')
    # Replace comma with dot
    clean = clean.replace(',', '.')
    
    try:
        return float(clean)
    except ValueError:
        return float('inf')

def check_prices_and_notify():
    json_path = "ozon_api_data.json"
    
    # Priority: Env var > Default hardcoded
    target_emails_str = os.getenv("alert_target_email") or "330882236@qq.com"
    # Support multiple emails separated by comma
    target_emails = [e.strip() for e in target_emails_str.split(',') if e.strip()]
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle the project's specific export format
    products = data.get("products", [])
    if not products and isinstance(data, list):
        products = data

    alerts = []
    for p in products:
        # Use lowercase keys as per ozon-mcp export format
        y_price_str = p.get("your_price") or p.get("Your Price", "")
        m_price_str = p.get("min_price") or p.get("Min Price", "")
        
        your_price = parse_price(y_price_str)
        min_price = parse_price(m_price_str)
        
        if your_price < min_price and min_price != float('inf'):
            alerts.append(p)

    if not alerts:
        print("所有商品价格均在正常范围内（未发现低于最低价的情况）。")
        return

    # Compose email
    subject = f"OZON 价格预警：发现 {len(alerts)} 个商品低于最低价"
    body = f"您好，系统在对全店 {len(products)} 个商品的监控中发现以下 {len(alerts)} 个商品价格异常：\n\n"
    
    for p in alerts:
        body += f"商品名称: {p.get('name') or p.get('Name')}\n"
        body += f"SKU: {p.get('sku') or p.get('SKU')}\n"
        body += f"当前价格: {p.get('your_price') or p.get('Your Price')}\n"
        body += f"最低价格: {p.get('min_price') or p.get('Min Price')}\n"
        body += "-" * 30 + "\n"

    body += "\n请及时处理。"

    # SMTP configuration
    smtp_server = "smtp.qq.com"
    smtp_port = 465
    sender_email = os.getenv("ozon_username")
    auth_code = os.getenv("qq_imap_auth_code")

    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender_email
        msg['To'] = ", ".join(target_emails)

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, auth_code)
            server.sendmail(sender_email, target_emails, msg.as_string())
        
        print(f"成功发送预警邮件至 {', '.join(target_emails)}，包含 {len(alerts)} 个异常商品。")
    except Exception as e:
        print(f"发送邮件失败: {e}")

if __name__ == "__main__":
    check_prices_and_notify()
