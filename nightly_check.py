import requests
import time
import json
import os
import sys
from datetime import datetime

# Force UTF-8 output for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# ⚙️ 配置区
# ==========================================
# 从 daily_check.py 拿到的配置
BARK_URLS = [
    "https://api.day.app/8BTBArkBatQQdF39JpsBDg/",
]
PUSHPLUS_TOKEN = "36e8f929dd944cd08d38131e9995b3ad" # 用户没有设置Token，这里留空，如有需要请手动填入

FUND_CODES_MAP = {
    '摩根均衡C (梁鹏/周期)': '021274',
    '泰康新锐C (韩庆/成长)': '017366',
    '财通优选C (金梓才/AI)': '021528'
}

# ==========================================
# 🛠️ 核心功能函数
# ==========================================

def load_json(filename):
    """读取本地JSON文件"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_json(filename, data):
    """保存本地JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存失败: {e}")
        return False

def get_official_nav(fund_code):
    """获取官方净值接口"""
    timestamp = int(time.time() * 1000)
    url = f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={fund_code}&pageIndex=1&pageSize=1&_={timestamp}"
    headers = {
        "Referer": "http://fund.eastmoney.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            res = r.json()
            if "Data" in res and "LSJZList" in res["Data"]:
                data_list = res["Data"]["LSJZList"]
                if len(data_list) > 0:
                    latest_data = data_list[0]
                    # 返回: 净值(float), 日期(str YYYY-MM-DD)
                    return float(latest_data["JZZZL"]), latest_data["FSRQ"]
    except Exception as e:
        print(f"Error fetching {fund_code}: {e}")
    return None, None

def send_notification(title, content):
    """发送通知"""
    print(f"🔔 准备发送通知: {title}")
    
    # 1. Bark
    for url in BARK_URLS:
        try:
            clean_url = url.rstrip('/')
            # Bark不支持过长URL，做简单编码或截断如果是GET请求。
            # 这里直接拼接，注意content可能需要URL编码，requests会自动处理params但这里是在path里
            # 为了安全简单，直接用requests.get(url + /title/content) 可能有编码问题
            # 建议使用 params
            base_url = "https://api.day.app/8BTBArkBatQQdF39JpsBDg/" # 提取Key
            requests.get(f"{base_url}{title}/{content}?group=fund")
        except Exception as e:
            print(f"Bark Error: {e}")

    # 2. PushPlus
    if PUSHPLUS_TOKEN:
        try:
            pp_url = "http://www.pushplus.plus/send"
            pp_data = {
                "token": PUSHPLUS_TOKEN,
                "title": title,
                "content": content.replace('\n', '<br>'),
                "template": "html"
            }
            requests.post(pp_url, json=pp_data)
        except Exception as e:
            print(f"PushPlus Error: {e}")

# ==========================================
# 🚀 主循环逻辑
# ==========================================

def run_check():
    print("🌙 Nightly Check Started...")
    print("正在等待基金净值更新 (按 Ctrl+C 停止)...")
    
    funds_config = load_json('funds.json')
    nav_cache = load_json('nav_history.json')
    
    # 目标日期：默认为今天
    # 如果是凌晨0点-早上8点跑，可能想查的是“昨天”的净值？
    # 假设用户是在当天晚上跑，查“今天”的
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 目标日期: {today_str}")

    # ==========================
    # 🕒 等待逻辑：直到晚上 20:00
    # ==========================
    while True:
        now = datetime.now()
        # 如果是下午或晚上，且不到20点，就等待
        if now.hour >= 12 and now.hour < 20:
            minutes_to_wait = (20 - now.hour) * 60 - now.minute
            print(f"[{now.strftime('%H:%M')}] 也就是晚上8点才更新，我先歇会儿... 还有 {minutes_to_wait} 分钟")
            time.sleep(60 * 10) # 每10分钟看一眼时间
        else:
            break
            
    print("⏰ 时间到！开始干活！")

    while True:
        updated_count = 0
        total_funds = len(funds_config)
        updates_info = [] # 存储更新详情
        
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"[{current_time}] 正在轮询接口...", end="\r")

        # 重新读取缓存，防止多进程写冲突（虽然本地一般单进程）
        nav_cache = load_json('nav_history.json') # Reload to be safe
        
        need_save = False

        for name, info in funds_config.items():
            code = FUND_CODES_MAP.get(name)
            if not code: continue
            
            # 检查该基金今天是否已更新
            key_name = name
            if key_name not in nav_cache: nav_cache[key_name] = {}
            
            if today_str in nav_cache[key_name]:
                updated_count += 1
                # 已经有数据了，不用重复打印，除非是刚抓到的（这里简单处理）
                continue 
            
            # API 查询
            nav, date_str = get_official_nav(code)
            
            if date_str == today_str and nav is not None:
                # ！！！ 发现更新 ！！！
                nav_cache[key_name][date_str] = nav
                need_save = True
                updated_count += 1
                
                # 计算单日涨幅
                # 拿到昨天的净值对比一下
                sorted_dates = sorted(nav_cache[key_name].keys())
                last_nav = 0
                if len(sorted_dates) >= 2:
                    last_date = sorted_dates[-2] # -1 is today now
                    last_nav = nav_cache[key_name][last_date]
                
                pct_chg = 0
                if last_nav > 0:
                    pct_chg = (nav - last_nav) / last_nav * 100
                
                updates_info.append({
                    "name": name.split('(')[0],
                    "nav": nav,
                    "pct": pct_chg
                })
                print(f"\n✅ {name.split('(')[0]} 已更新: {nav} ({pct_chg:+.2f}%)")

        if need_save:
            save_json('nav_history.json', nav_cache)

        # 检查是否全部更新完毕
        if updated_count >= total_funds:
            print("\n🎉 所有基金净值已更新！准备发送报告...")
            
            # 生成报告
            total_profit = 0
            total_principal = 0
            msg_lines = []
            
            for name, info in funds_config.items():
                principal = info.get('holding_value', 0)
                total_principal += principal
                
                # 找今天的涨幅
                pct = 0
                key_name = name
                if key_name in nav_cache and today_str in nav_cache[key_name]:
                     # 重新计算一下涨幅，为了准确
                    current_nav = nav_cache[key_name][today_str]
                    # 找昨天
                    hist = nav_cache[key_name]
                    dates = sorted(hist.keys())
                    if len(dates) >= 2:
                        prev = hist[dates[-2]]
                        if prev > 0: pct = (current_nav - prev) / prev * 100
                    
                profit = principal * pct / 100
                total_profit += profit
                
                icon = "🔴" if pct > 0 else "🟢" if pct < 0 else "⚪"
                msg_lines.append(f"{icon} {name.split('(')[0]}: {pct:+.2f}% (¥{profit:+.0f})")

            yield_rate = (total_profit / total_principal * 100) if total_principal > 0 else 0
            
            final_title = f"今日实际: {total_profit:+.0f} ({yield_rate:+.2f}%)"
            final_body = f"📅 {today_str} 净值已出炉\n\n" + "\n".join(msg_lines)
            
            send_notification(final_title, final_body)
            print("✅ 通知已发送，任务结束。")
            break
        
        # 还没更完，休息一下再查
        # 晚上更新一般比较集中，可以设为 3分钟 一次
        time.sleep(180) 

if __name__ == "__main__":
    run_check()
