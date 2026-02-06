import json
import os
import requests
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def load_secrets():
    print("🔍 正在检查配置文件...")
    
    # 1. Check Environment Variables
    bark_env = os.getenv("BARK_KEY")
    pp_env = os.getenv("PUSHPLUS_TOKEN")
    
    if bark_env: print(f"✅ 环境变量 BARK_KEY 已设置 (长度: {len(bark_env)})")
    else: print("❌ 环境变量 BARK_KEY 未设置")
    
    if pp_env: print(f"✅ 环境变量 PUSHPLUS_TOKEN 已设置 (长度: {len(pp_env)})")
    else: print("❌ 环境变量 PUSHPLUS_TOKEN 未设置")

    # 2. Check Local File
    bark_file = None
    pp_file = None
    
    if os.path.exists('secrets.json'):
        print("✅ 发现本地 secrets.json 文件")
        try:
            with open('secrets.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                bark_file = data.get("BARK_URL") or data.get("BARK_KEY")
                pp_file = data.get("PUSHPLUS_TOKEN")
                
                if bark_file: print(f"  - BARK 配置已读取: {bark_file[:10]}...")
                else: print("  - ⚠️ secrets.json 中缺少 BARK_URL 或 BARK_KEY")
                
                if pp_file: print(f"  - PushPlus 配置已读取: {pp_file[:5]}...")
                else: print("  - ⚠️ secrets.json 中缺少 PUSHPLUS_TOKEN")
        except Exception as e:
            print(f"❌ 读取 secrets.json 失败: {e}")
    else:
        print("❌ 未发现本地 secrets.json 文件")
        print("  👉 请复制 secrets.json.example 为 secrets.json 并填写配置")

    # Priority: Env > File
    final_bark = bark_env or bark_file
    final_pp = pp_env or pp_file
    
    return final_bark, final_pp

def test_send(bark, pp):
    print("\n🚀 开始测试推送...")
    
    if not bark and not pp:
        print("🛑没有任何有效的推送配置，无法测试。")
        return

    title = "测试通知"
    content = "这是一条测试消息，如果你收到它，说明配置正确！"

    # Test Bark
    if bark:
        print(f"\n[Test] 正在尝试发送 Bark...")
        try:
            base_url = bark if bark.startswith("http") else f"https://api.day.app/{bark}/"
            clean_url = base_url.rstrip('/')
            url = f"{clean_url}/{title}/{content}?group=test"
            print(f"  - 请求 URL: {url}")
            resp = requests.get(url)
            print(f"  - 响应状态码: {resp.status_code}")
            print(f"  - 响应内容: {resp.text}")
        except Exception as e:
            print(f"❌ Bark 发送异常: {e}")
    else:
        print("\n[Skip] 跳过 Bark 测试 (未配置)")

    # Test PushPlus
    if pp:
        print(f"\n[Test] 正在尝试发送 PushPlus...")
        try:
            pp_url = "http://www.pushplus.plus/send"
            pp_data = {
                "token": pp,
                "title": title,
                "content": content,
                "template": "html"
            }
            resp = requests.post(pp_url, json=pp_data)
            print(f"  - 响应状态码: {resp.status_code}")
            print(f"  - 响应内容: {resp.text}")
        except Exception as e:
            print(f"❌ PushPlus 发送异常: {e}")
    else:
        print("\n[Skip] 跳过 PushPlus 测试 (未配置)")

if __name__ == "__main__":
    b, p = load_secrets()
    test_send(b, p)
    print("\n✅ 测试结束")
