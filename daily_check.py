import requests
import json
import os
from datetime import datetime, timedelta

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
    try:
        r = requests.get(url, timeout=3)
        price_data = {}
        parts = r.text.split(';')
        for part in parts:
            if '="' in part:
                try:
                    code = part.split('=')[0].split('_')[-1]
                    data = part.split('="')[1].split('~')
                    close = float(data[4])
                    if close > 0:
                        price_data[code] = ((float(data[3]) - close) / close) * 100
                except: continue
        return price_data
    except: return {}

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
    
    # 🕒 必须在 此时间段内 才发送“收盘估值报告”
    # 目标：15:15 | 范围放宽: 15:00 - 16:30 (应对 GitHub Actions 延迟)
    # GitHub Action 跑在 UTC，需+8小时转为北京时间
    bj_time = datetime.utcnow() + timedelta(hours=8)
    now = bj_time
    # 只要是 15点，或者 16点30分之前，都允许发送 (防止排队太久导致错过)
    # 只有 15:00 之后才发送收盘报告 (14:45 只发信号)
    is_market_close_window = (now.hour == 15) or (now.hour == 16 and now.minute <= 30)
    
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

    # ---------------------------
    # 📢 2. 发送收盘估值报告 (特定时间段)
    # ---------------------------
    if is_market_close_window:
        print("[REPORT] 正在生成收盘估值报告...")
        title = f"收盘估值播报 {datetime.now().strftime('%H:%M')}"
        body = f"📅 {datetime.now().strftime('%Y-%m-%d')}\n\n" + "\n".join(report_lines)
        send_message(title, body)
        print("[OK] 估值报告已推送")
    else:
        print(f"非收盘报告时间 (当前 {now.strftime('%H:%M')})")

if __name__ == "__main__":
    main()
