import requests

def test_bark(bark_key):
    if not bark_key:
        print("❌ Bark Key 为空，跳过测试")
        return

    print(f"Testing Bark with Key: {bark_key} ...")
    url = f"https://api.day.app/{bark_key}/Bark测试/这是一条测试消息?group=test"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            print("✅ Bark 推送请求成功！请检查手机是否收到。")
        else:
            print(f"❌ Bark 推送失败: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Bark 请求异常: {e}")

def test_pushplus(token):
    if not token:
        print("❌ PushPlus Token 为空，跳过测试")
        return

    print(f"Testing PushPlus with Token: {token} ...")
    url = "http://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": "PushPlus测试",
        "content": "这是一条来自Family Fund Monitor的测试消息",
        "template": "html"
    }
    try:
        r = requests.post(url, json=data)
        if r.status_code == 200:
            print("✅ PushPlus 推送请求成功！请检查微信/App是否收到。")
            print(f"响应: {r.text}")
        else:
            print(f"❌ PushPlus 推送失败: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ PushPlus 请求异常: {e}")

if __name__ == "__main__":
    print("=== 🔔 通知服务测试工具 ===")
    
    # 1. Test Bark
    print("\n[1] 测试 Bark")
    bark_key = input("请输入你的 Bark Key (直接回车跳过): ").strip()
    test_bark(bark_key)

    # 2. Test PushPlus
    print("\n[2] 测试 PushPlus")
    pp_token = input("请输入你的 PushPlus Token (直接回车跳过): ").strip()
    test_pushplus(pp_token)
    
    input("\n测试结束，按回车退出...")
