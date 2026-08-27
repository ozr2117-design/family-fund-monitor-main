import sys
import time
from playwright.sync_api import sync_playwright

def wake_up(app_url):
    print(f"🚀 正在使用无头浏览器访问: {app_url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        try:
            page.goto(app_url, wait_until="networkidle", timeout=60000)
            
            # 查找并点击 Streamlit 的休眠唤醒按钮
            wake_btn = page.locator('button:has-text("Yes, get this app back up"), button:has-text("get this app back up"), button:has-text("Wake up")')
            
            if wake_btn.count() > 0 and wake_btn.first.is_visible():
                print("⚡ 检测到 App 处于休眠状态，正在点击唤醒按钮...")
                wake_btn.first.click()
                print("⏳ 已点击唤醒，等待 15 秒让服务拉起...")
                time.sleep(15)
            else:
                print("✅ App 当前处于活跃状态，已完成 WebSocket 握手！")
                time.sleep(5)
                
            print(f"🎉 最终页面标题: {page.title()}")
        except Exception as e:
            print(f"⚠️ 访问过程中出现提示: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://family-fund-monitor-1.streamlit.app/"
    wake_up(target_url)
