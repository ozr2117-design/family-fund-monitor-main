import requests
import json
import os
from datetime import datetime, timedelta
import time

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

def load_funds():
    try:
        with open('funds.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def get_realtime_price(stock_codes):
    if not stock_codes: return {}
    url = f"http://qt.gtimg.cn/q={','.join(stock_codes)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code != 200:
                print(f"⚠️ 行情接口返回 {r.status_code}，重试 ({attempt+1}/3)...")
                continue

            price_data = {}
            parts = r.text.split(';')
            for part in parts:
                if '="' in part:
                    try:
                        code = part.split('=')[0].split('_')[-1]
                        data = part.split('="')[1].split('~')
                        if len(data) > 4:
                            close = float(data[4])
                            if close > 0:
                                price_data[code] = ((float(data[3]) - close) / close) * 100
                    except: continue
            
            if price_data: return price_data
            else: print("⚠️ 获取到的行情数据为空")
            
        except Exception as e:
            print(f"⚠️ 网络请求异常: {e}，重试 ({attempt+1}/3)...")
            time.sleep(2)
            
    print("❌ 多次重试失败，无法获取行情数据")
    return {}

def get_benchmark_pct(fund_name, market_data):
    code = 'sz399006' if any(k in fund_name for k in ["成长", "AI", "优选"]) else 'sh000001'
    return market_data.get(code, 0)

# 🔥 新增：写日记功能
def append_to_log(log_entries):
    if not log_entries: return
    
    today = datetime.now().strftime("%Y-%m-%d")
    new_lines = []
    
    for entry in log_entries:
        # 格式: | 日期 | 基金 | 信号 | 详情 | 操作 |
        line = f"| {today} | {entry['name']} | {entry['type']} | {entry['detail']} | {entry['action']} |"
        new_lines.append(line)
        
    try:
        # 读取现有内容
        LOG_FILE = "signals.md"
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 在表头(第2行)下面插入新内容，这样最新的在最上面
        insert_idx = 2
        for i, line in enumerate(lines):
            if "|---" in line:
                insert_idx = i + 1
                break
                
        # 插入
        for line in reversed(new_lines):
            lines.insert(insert_idx, line + "\n")
            
        # 写入
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("✅ 日记写入成功")
    except Exception as e:
        print(f"❌ 写日记失败: {e}")

# ==========================================
# 🛠️ 核心功能函数
# ==========================================
def send_message(title, content):
    """统一发送通知 (Bark + PushPlus)"""
    print(f"[MSG] 准备发送通知: {title}")
    
    # 1. Push Bark
    if BARK_KEY:
        try:
            # 兼容完整URL或纯Key
            base_url = BARK_KEY if BARK_KEY.startswith("http") else f"https://api.day.app/{BARK_KEY}/"
            clean_url = base_url.rstrip('/')
            requests.get(f"{clean_url}/{title}/{content}?group=fund", timeout=10)
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
            requests.post(pp_url, json=pp_data, timeout=10)
        except Exception as e:
            print(f"❌ PushPlus 推送失败: {e}")

# ==========================================
# 🚀 主程序
# ==========================================
def main():
    print(">>> 开始执行巡检...")
    if not BARK_KEY and not PUSHPLUS_TOKEN:
        print("[!] 未找到推送配置 (Env或secrets.json)，仅本地运行")

    funds = load_funds()
    if not funds: return
    
    all_codes = ['sh000001', 'sz399006']
    for f in funds.values():
        for s in f['holdings']: all_codes.append(s['code'])
    
    market_data = get_realtime_price(list(set(all_codes)))
    if not market_data: return

    messages = []
    log_entries = [] # 专门用于写日记的数据结构
    
    # GitHub Action 跑在 UTC，需+8小时转为北京时间
    bj_time = datetime.utcnow() + timedelta(hours=8)
    now = bj_time
    
    report_lines = []
    total_est_profit = 0
    
    for name, info in funds.items():
        factor = info.get('factor', 1.0)
        base_unit = info.get('base_unit', 1000)
        val = 0; w = 0
        for s in info['holdings']:
            if s['code'] in market_data:
                val += market_data[s['code']] * s['weight']; w += s['weight']
        
        est = (val / w * factor) if w > 0 else 0
        bench_val = get_benchmark_pct(name, market_data)
        short_name = name.split('(')[0]

        # 收集报告数据 (无论是否触发信号)
        icon = "🔴" if est > 0 else "🟢" if est < 0 else "⚪"
        report_lines.append(f"{icon} {short_name}: {est:+.2f}%")

        # 信号判断
        signal_type = None
        detail = ""
        action = ""
        
        # 1. 买入
        if est < -2.5 and est < bench_val:
            multiplier = 2 if est < -4.0 else 1
            buy_amt = base_unit * multiplier
            msg = f"🟢【机会】{short_name} {est:.2f}%\n📉 跑输基准 {abs(est-bench_val):.1f}%\n👉 建议加仓 ¥{buy_amt:,}"
            messages.append(msg)
            
            # 记录日志数据
            log_entries.append({
                "name": short_name,
                "type": "🟢 买入机会",
                "detail": f"估值 {est:.2f}% (跑输 {abs(est-bench_val):.1f}%)",
                "action": f"买入 ¥{buy_amt:,}"
            })

        # 2. 卖出
        elif est > 3.0 and est > (bench_val + 1.5):
            msg = f"🔴【止盈】{short_name} +{est:.2f}%\n🔥 跑赢基准 {abs(est-bench_val):.1f}%\n👉 建议卖出 1/4"
            messages.append(msg)
            
            log_entries.append({
                "name": short_name,
                "type": "🔴 止盈提醒",
                "detail": f"估值 +{est:.2f}% (跑赢 {abs(est-bench_val):.1f}%)",
                "action": "卖出 1/4"
            })

    # ---------------------------
    # 📢 1. 发送交易信号 (优先级最高)
    # ---------------------------
    if messages:
        final_body = "\n\n".join(messages)
        send_message("基金信号提醒", final_body)
        print("✅ 交易信号已推送")
        
        # 写日记
        append_to_log(log_entries)
    else:
        print("今日无交易信号")

    today_date = now.strftime('%Y-%m-%d')
    report_status_file = "report_status.json"
    
    # 读取报告发送状态
    report_sent = False
    try:
        if os.path.exists(report_status_file):
            with open(report_status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                if status_data.get("date") == today_date and status_data.get("sent"):
                    report_sent = True
    except: pass

    # 🕒 收盘估值报告逻辑优化
    # 只要是 15:00 之后，且今天还没发过，就发送 (不再限制 16:30 截止，防止 GitHub Action 延迟)
    is_report_time = (now.hour >= 15)
    
    # ---------------------------
    # 📢 2. 发送收盘估值报告
    # ---------------------------
    if is_report_time and not report_sent:
        print("[REPORT] 正在生成收盘估值报告...")
        title = f"收盘估值播报 {datetime.now().strftime('%H:%M')}"
        body = f"📅 {today_date}\n\n" + "\n".join(report_lines)
        send_message(title, body)
        print("[OK] 估值报告已推送")
        
        # 记录已发送状态
        try:
            with open(report_status_file, 'w', encoding='utf-8') as f:
                json.dump({"date": today_date, "sent": True}, f)
        except Exception as e:
            print(f"❌ 记录报告状态失败: {e}")

    elif report_sent:
        print(f"今日 ({today_date}) 收盘报告已发送，跳过。")
    else:
        print(f"非收盘报告时间 (当前 {now.strftime('%H:%M')})，等待 15:00 后发送")

if __name__ == "__main__":
    main()
