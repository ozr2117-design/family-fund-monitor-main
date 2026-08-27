import requests
import time
import json
import os
import sys
from datetime import datetime, timedelta

# Force UTF-8 output for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# ⚙️ 配置区
# ==========================================
def load_secrets():
    bark = os.getenv("BARK_KEY")
    pp = os.getenv("PUSHPLUS_TOKEN")
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

FUND_CODES_MAP = {
    '财通周期优选混合C (025547)': '025547',
    '财通科技创新混合C (008984)': '008984',
    '路博迈中国动力股票C (020237)': '020237',
    '摩根均衡精选混合A (021273)': '021273',
    '华安品质甄选混合A (013680)': '013680'
}

NIGHTLY_STATUS_FILE = "nightly_status.json"
DEADLINE_HOUR = 22

# ==========================================
# 🛠️ 工具函数
# ==========================================
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Save failed: {e}")
        return False

def get_official_nav_pct(fund_code):
    timestamp = int(time.time() * 1000)
    url = f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={fund_code}&pageIndex=1&pageSize=2&_={timestamp}"
    headers = {
        "Referer": "http://fund.eastmoney.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            res = r.json()
            if "Data" in res and "LSJZList" in res["Data"]:
                data = res["Data"]["LSJZList"]
                if len(data) >= 2:
                    t_nav = float(data[0]["DWJZ"])
                    y_nav = float(data[1]["DWJZ"])
                    if y_nav > 0:
                        pct = (t_nav - y_nav) / y_nav * 100
                        return pct, data[0]["FSRQ"], t_nav
                elif len(data) == 1:
                    return float(data[0]["JZZZL"]), data[0]["FSRQ"], float(data[0]["DWJZ"])
    except Exception as e:
        print(f"Error fetching {fund_code}: {e}")
    return None, None, None

def calculate_adaptive_factor(current_factor, raw_est, actual_pct):
    """
    自适应抗噪 EMA+ 因子校准算法（针对中国公募基金定制）：
    1. 震荡日过滤 (abs(raw_est) < 0.2% 时信噪比极低，跳过校准保持原值)
    2. 同向 EMA 学习率平滑，单日最大比值截断 [0.5, 2.0]
    3. 反向异动阻尼回归 1.0 (防止负数或极端调仓爆炸)
    4. 物理边界 Clamp [0.65, 1.35]
    """
    if raw_est is None or abs(raw_est) < 0.2:
        return current_factor, "震荡保持"
    
    ratio = actual_pct / raw_est
    
    if ratio > 0:
        # 同向：限制单日比值倍数，避免单日极端噪音带偏
        clamped_ratio = max(0.5, min(2.0, ratio))
        # EMA: 80% 历史记忆 + 20% 今日观测
        new_factor = (current_factor * 0.8) + (clamped_ratio * 0.2)
        audit_tag = f"EMA(R={ratio:.2f})"
    else:
        # 反向：可能由于大额分红或剧烈调仓导致，采用阻尼向 1.0 靠拢
        new_factor = (current_factor * 0.9) + (1.0 * 0.1)
        audit_tag = "阻尼回归"
        
    final_factor = max(0.65, min(1.35, round(new_factor, 4)))
    return final_factor, audit_tag

def send_notification(title, content):
    print(f"[MSG] Sending: {title}")
    if BARK_KEY:
        try:
            base_url = BARK_KEY if BARK_KEY.startswith("http") else f"https://api.day.app/{BARK_KEY}/"
            requests.get(f"{base_url.rstrip('/')}/{title}/{content}?group=fund")
        except: pass
    if PUSHPLUS_TOKEN and len(PUSHPLUS_TOKEN) > 5:
        try:
            requests.post("http://www.pushplus.plus/send", json={
                "token": PUSHPLUS_TOKEN,
                "title": title,
                "content": content.replace("\n", "<br>"),
                "template": "html"
            })
        except Exception as e:
            print(f"PushPlus Error: {e}")

# ==========================================
# Main (single-run, no waiting loop)
# Triggered by cron-job.org every 30 mins
# ==========================================
def run_check():
    print("🌙 Nightly Check Started (Single-run mode)...")

    funds_config = load_json('funds.json')
    nav_cache = load_json('nav_history.json')
    nightly_status = load_json(NIGHTLY_STATUS_FILE)

    bj_now = datetime.utcnow() + timedelta(hours=8)
    today_str = bj_now.strftime("%Y-%m-%d")
    print(f"Date: {today_str} | Beijing time: {bj_now.strftime('%H:%M')}")

    if nightly_status.get("date") == today_str and nightly_status.get("sent"):
        print(f"Report already sent today ({today_str}), exiting.")
        return

    target_funds = [k for k in funds_config.keys() if k in FUND_CODES_MAP]
    total_funds = len(target_funds)
    need_save = False

    for name in target_funds:
        info = funds_config[name]
        code = FUND_CODES_MAP.get(name)
        if name not in nav_cache:
            nav_cache[name] = {}
        if today_str in nav_cache[name]:
            print(f"[cached] {name.split('(')[0]}")
            continue
        nav_pct, date_str, t_nav = get_official_nav_pct(code)
        if date_str == today_str and nav_pct is not None:
            nav_cache[name][date_str] = nav_pct
            if 'shares' in info and t_nav is not None:
                funds_config[name]['holding_value'] = round(info['shares'] * t_nav, 2)
            need_save = True
            print(f"[updated] {name.split('(')[0]}: {nav_pct:+.2f}%")
        else:
            print(f"[pending] {name.split('(')[0]}: not published yet")

    if need_save:
        save_json('nav_history.json', nav_cache)
        save_json('funds.json', funds_config)

    updated_count = sum(1 for n in target_funds if today_str in nav_cache.get(n, {}))
    missing_funds = [n.split('(')[0] for n in target_funds if today_str not in nav_cache.get(n, {})]
    is_all_updated = (updated_count >= total_funds)
    is_past_deadline = (bj_now.hour > DEADLINE_HOUR) or (bj_now.hour == DEADLINE_HOUR and bj_now.minute >= 0)

    if is_all_updated:
        report_type = "all_done"
        print("All NAVs updated, sending full report...")
    elif is_past_deadline:
        report_type = "partial"
        print(f"Past {DEADLINE_HOUR}:00 deadline, sending partial report...")
    else:
        print(f"Incomplete ({updated_count}/{total_funds}), exiting. Next trigger in ~30 min.")
        return

    # ── 🤖 执行 EMA+ 因子自动审计 ────────────────────────
    history = load_json('history.json')
    factor_history = load_json('factor_history.json')
    if today_str not in factor_history:
        factor_history[today_str] = {}
        
    factor_audit_logs = []
    for name in target_funds:
        if today_str in nav_cache.get(name, {}):
            actual_pct = nav_cache[name][today_str]
            raw_est = history.get(today_str, {}).get(name)
            current_f = funds_config[name].get('factor', 1.0)
            
            new_f, audit_tag = calculate_adaptive_factor(current_f, raw_est, actual_pct)
            funds_config[name]['factor'] = new_f
            factor_history[today_str][name] = new_f
            
            short_n = name.split('(')[0]
            if new_f != current_f:
                factor_audit_logs.append(f"⚖️ {short_n}: {current_f:.3f}→{new_f:.3f} ({audit_tag})")
            else:
                factor_audit_logs.append(f"⚖️ {short_n}: {current_f:.3f} ({audit_tag})")

    save_json('factor_history.json', factor_history)
    save_json('funds.json', funds_config)
    print("✅ EMA+ 因子自适应审计完成并已存盘")

    # ── 生成报告 ─────────────────────────────────────────
    total_profit = 0
    total_principal = 0
    msg_lines = []

    for name, info in funds_config.items():
        principal = info.get('holding_value', 0)
        total_principal += principal
        pct = 0
        found_today = False
        if name in nav_cache and today_str in nav_cache[name]:
            pct = nav_cache[name][today_str]
            found_today = True
        profit = principal * pct / 100
        if found_today:
            total_profit += profit
            icon = "🔴" if pct > 0 else "🟢" if pct < 0 else "⚪"
            msg_lines.append(f"{icon} {name.split('(')[0]}: {pct:+.2f}% (¥{profit:+.0f})")
        else:
            msg_lines.append(f"⏳ {name.split('(')[0]}: 待更新...")

    yield_rate = (total_profit / total_principal * 100) if total_principal > 0 else 0
    status_icon = "✅ 全量更新" if report_type == "all_done" else "⚠️ 部分更新"
    final_title = f"{status_icon}: {total_profit:+.0f} ({yield_rate:+.2f}%)"
    
    final_body = f"📅 {today_str} 净值 ({updated_count}/{total_funds})\n\n" + "\n".join(msg_lines)
    if not is_all_updated:
        final_body += f"\n\n⚠️ 未更新: {', '.join(missing_funds)}"
        
    if factor_audit_logs:
        final_body += "\n\n🤖 估值因子已自动校准:\n" + "\n".join(factor_audit_logs)

    send_notification(final_title, final_body)
    save_json(NIGHTLY_STATUS_FILE, {"date": today_str, "sent": True})
    print("Notification sent. Task complete.")


if __name__ == "__main__":
    run_check()
