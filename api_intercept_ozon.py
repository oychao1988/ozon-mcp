import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def intercept_ozon_prices():
    # Configuration
    user_data_dir = "./chrome-profile"
    target_url = "https://seller.ozon.ru/app/prices/control?tab=marketing_actions"
    output_file = "ozon_api_data.json"
    
    # Use a dict for de-duplication by SKU
    all_products_dict = {}
    total_expected = 0
    pages_processed = 0

    print(f"🚀 启动高性能 API 拦截模式...")

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = await browser.new_page()

        async def handle_response(response):
            nonlocal total_expected, pages_processed
            # Intercept all product-related APIs that contain price information
            if "/api/v1/products/list-by-filter" in response.url and response.status == 200:
                try:
                    payload = await response.json()
                    items = payload.get("products", [])
                    if not items:
                        return

                    # Update total_expected whenever a larger value is encountered
                    current_total = payload.get("total_items") or 0
                    if current_total > total_expected:
                        total_expected = current_total
                        print(f"📢 发现更多商品，更新预期总数: {total_expected}")

                    for item in items:
                        # Extract from OZON API structure
                        part_item = item.get("part_item") or {}
                        part_price = item.get("part_price") or {}
                        part_marketing = item.get("part_marketing_price") or {}
                        
                        name = part_item.get("name") or "Unknown"
                        sku = str(part_item.get("offer_id") or item.get("item_id") or "")
                        if not sku: continue
                        
                        # Your Price
                        price_obj = part_price.get("price") or {}
                        your_price = price_obj.get("units") or "0"
                        
                        # Min Price
                        min_price_obj = part_price.get("min_price") or {}
                        min_price = min_price_obj.get("units") or "未指定"
                        
                        # Buyer Price
                        marketing_price_obj = part_marketing.get("price") or {}
                        buyer_price = marketing_price_obj.get("units") or your_price
                        
                        currency = price_obj.get("currencyCode") or "¥"

                        all_products_dict[sku] = {
                            "name": name,
                            "sku": sku,
                            "your_price": f"{your_price} {currency}",
                            "min_price": f"{min_price} {currency}",
                            "buyer_price": f"{buyer_price} {currency}"
                        }
                    
                    pages_processed += 1
                    current_unique_count = len(all_products_dict)
                    progress = (current_unique_count / total_expected * 100) if total_expected > 0 else 0
                    print(f"📦 已抓取去重商品: {current_unique_count} | 进度: {progress:.1f}%")
                    
                except Exception:
                    pass

        page.on("response", handle_response)

        print(f"🌐 正在导航至: {target_url}")
        await page.goto(target_url, wait_until="networkidle")
        await asyncio.sleep(5)

        # Loop through pages strictly
        max_pages = 30 # Safety limit
        for i in range(max_pages):
            # Find the pagination buttons
            next_btn = page.locator("button.table-500").last
            
            if await next_btn.is_visible():
                is_disabled = await next_btn.get_attribute("disabled")
                if is_disabled is not None:
                    print("🏁 已到达最后一页按钮。")
                    break
                
                print(f"⏭️ 正在翻页 ({i+1})...")
                await next_btn.click()
                await asyncio.sleep(4) # Wait for API response
                
                # Double check if we reached the expected count
                if total_expected > 0 and len(all_products_dict) >= total_expected:
                    # Continue a bit more to be safe, but usually we can stop
                    pass 
            else:
                print("🏁 未找到翻页按钮。")
                break

        final_list = list(all_products_dict.values())

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "total": len(final_list),
                "products": final_list
            }, f, ensure_ascii=False, indent=2)

        print(f"\n✨ 任务完成！总计提取: {len(final_list)} 个商品")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(intercept_ozon_prices())
