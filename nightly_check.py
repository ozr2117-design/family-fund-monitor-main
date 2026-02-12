import requests
import time
import json
import os
import sys
from datetime import datetime, timedelta

# Force UTF-8 output for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# ⚙️ 配置区 (安全升级版)
# ==========================================
def load_secrets():
    # 1. 尝试从环境变量读取 (GitHub Secrets)
    bark = os.getenv("BARK_KEY")
    pp = os.getenv("PUSHPLUS_TOKEN")
    
    # 2. 尝试从本地文件读取
    if not bark or not pp:
        try:
            if os.path.exists('secrets.json'):
                with open('secrets.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not bark: bark = data.get("BARK_URL") or data.get("BARK_KEY")
                    if not pp: pp = data.get("PUSHPLUS_TOKEN")
        except: pass

    return bark, pp

BARK_KEY, PUSHPLUS_TOKEN = load_secrets()
# 下面的 BARK_URLS 仅作为旧版兼容，如果不为空且 BARK_KEY 为空，可以尝试使用（这里简化逻辑，直接覆盖）

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
                    return float(latest_data["DWJZ"]), latest_data["FSRQ"]
    except Exception as e:
        print(f"Error fetching {fund_code}: {e}")
    return None, None

def send_notification(title, content):
    """统一发送通知 (Bark + PushPlus)"""
    print(f"[MSG] 准备发送通知: {title}")
    
    # 1. Push Bark
    if BARK_KEY:
        try:
            # 兼容完整URL或纯Key
            base_url = BARK_KEY if BARK_KEY.startswith("http") else f"https://api.day.app/{BARK_KEY}/"
            clean_url = base_url.rstrip('/')
            requests.get(f"{clean_url}/{title}/{content}?group=fund")
        except: pass

    # 2. Push PushPlus
    if PUSHPLUS_TOKEN and len(PUSHPLUS_TOKEN) > 5:
        try:
            pp_url = "http://www.pushplus.plus/send"
            pp_data = {
                "token": PUSHPLUS_TOKEN,
                "title": title,
                "content": content.replace("\n", "<br>"), # HTML换行
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
    
    funds_config = load_json('funds.json')
    nav_cache = load_json('nav_history.json')
    
    # 时区修正：GitHub Action 跑在 UTC，需+8小时转为北京时间
    # 无论是本地还是云端，统一用这个“北京时间”对象来判断
    bj_now = datetime.utcnow() + timedelta(hours=8)
    today_str = bj_now.strftime("%Y-%m-%d")
    print(f"📅 目标日期: {today_str} (当前时间: {bj_now.strftime('%H:%M')})")

    # ==========================
    # 🕒 等待逻辑：直到晚上 20:00
    # ==========================
    while True:
        # 刷新时间
        bj_now = datetime.utcnow() + timedelta(hours=8)
        
        # 如果是下午或晚上，且不到20点，就等待
        # 范围：12:00 <= T < 20:00
        if bj_now.hour >= 12 and bj_now.hour < 20:
            minutes_to_wait = (20 - bj_now.hour) * 60 - bj_now.minute
            print(f"[{bj_now.strftime('%H:%M')}] 也就是晚上8点才更新，我先歇会儿... 还有 {minutes_to_wait} 分钟")
            
            # 如果剩余时间很多，就睡久点；如果不到了，睡短点
            sleep_sec = 60 * 10 
            if minutes_to_wait < 10: sleep_sec = 60
            time.sleep(sleep_sec) 
        else:
            break
            
    print("⏰ 时间到！开始干活！")
    
    # 设置一个截止时间 (例如 北京时间 22:00)
    # 既然 GitHub Actions 最多跑 6 小时 (从 20:00 开始)，到 02:00 就会被杀掉
    # 我们设一个 22:00 的“软截止”，如果到点了还没全齐，也发消息
    deadline_hour = 22
    deadline_minute = 0 
    
    while True:
        updated_count = 0
        
        # 刷新时间
        bj_now = datetime.utcnow() + timedelta(hours=8)
        current_time_str = bj_now.strftime("%H:%M:%S")
        
        # 过滤出有代码映射的基金（防止 funds.json 里有新基金但代码未配，导致死循环）
        target_funds = [k for k in funds_config.keys() if k in FUND_CODES_MAP]
        total_funds = len(target_funds)
        updates_info = [] # 存储更新详情
        
        print(f"[{current_time_str}] 正在轮询接口 (监控 {total_funds} 只基金)...", end="\r")

        # 重新读取缓存，防止多进程写冲突（虽然本地一般单进程）
        nav_cache = load_json('nav_history.json') 
        
        need_save = False
        missing_funds = []

        for name in target_funds:
            info = funds_config[name]
            code = FUND_CODES_MAP.get(name)
            
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
            else:
                missing_funds.append(name.split('(')[0])

        if need_save:
            save_json('nav_history.json', nav_cache)

        # 检查是否全部更新完毕 OR 超过截止时间
        is_all_updated = (updated_count >= total_funds)
        is_past_deadline = (bj_now.hour > deadline_hour) or (bj_now.hour == deadline_hour and bj_now.minute >= deadline_minute)
        
        if is_all_updated or is_past_deadline:
            if is_all_updated:
                print("\n🎉 所有基金净值已更新！准备发送报告...")
                report_type = "全量更新"
            else:
                print(f"\n⚠️ 超过截止时间 ({deadline_hour}:{deadline_minute})，发送部分报告...")
                report_type = "部分更新"
            
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
                found_today = False
                
                if key_name in nav_cache and today_str in nav_cache[key_name]:
                     # 重新计算一下涨幅，为了准确
                    current_nav = nav_cache[key_name][today_str]
                    found_today = True
                    # 找昨天
                    hist = nav_cache[key_name]
                    dates = sorted(hist.keys())
                    if len(dates) >= 2:
                        prev = hist[dates[-2]]
                        if prev > 0: pct = (current_nav - prev) / prev * 100
                
                # 计算收益 (如果还没更新，pct就是0，收益也是0，显示为“待更新”)
                profit = principal * pct / 100
                if found_today:
                    total_profit += profit
                    icon = "🔴" if pct > 0 else "🟢" if pct < 0 else "⚪"
                    msg_lines.append(f"{icon} {name.split('(')[0]}: {pct:+.2f}% (¥{profit:+.0f})")
                else:
                    msg_lines.append(f"⏳ {name.split('(')[0]}: 待更新...")

            yield_rate = (total_profit / total_principal * 100) if total_principal > 0 else 0
            
            # 标题区分
            final_title = f"{report_type}: {total_profit:+.0f} ({yield_rate:+.2f}%)"
            final_body = f"📅 {today_str} 净值 ({updated_count}/{total_funds})\n\n" + "\n".join(msg_lines)
            
            if not is_all_updated:
                final_body += f"\n\n⚠️ 未更新: {', '.join(missing_funds)}"
            
            send_notification(final_title, final_body)
            print("✅ 通知已发送，任务结束。")
            break
        
        # 还没更完，休息一下再查
        time.sleep(180) 

if __name__ == "__main__":
    run_check()
