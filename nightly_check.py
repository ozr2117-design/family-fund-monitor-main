import requests
import time
import json
import os
import sys
from datetime import datetime, timedelta

# Force UTF-8 output for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# Configuration
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
    '\u8d22\u901a\u5468\u671f\u4f18\u9009\u6df7\u5408C (025547)': '025547',
    '\u8d22\u901a\u79d1\u6280\u521b\u65b0\u6df7\u5408C (008984)': '008984',
    '\u8def\u535a\u8fc8\u4e2d\u56fd\u52a8\u529b\u80a1\u7968C (020237)': '020237',
    '\u6469\u6839\u5747\u8861\u7cbe\u9009\u6df7\u5408A (021273)': '021273',
    '\u534e\u5b89\u54c1\u8d28\u7504\u9009\u6df7\u5408A (013680)': '013680'
}

NIGHTLY_STATUS_FILE = "nightly_status.json"
DEADLINE_HOUR = 22

# ==========================================
# Utility functions
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
    print("Nightly Check Started (Single-run mode)...")

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
            icon = "\U0001f534" if pct > 0 else "\U0001f7e2" if pct < 0 else "\u26aa"
            msg_lines.append(f"{icon} {name.split('(')[0]}: {pct:+.2f}% (\u00a5{profit:+.0f})")
        else:
            msg_lines.append(f"\u23f3 {name.split('(')[0]}: \u5f85\u66f4\u65b0...")

    yield_rate = (total_profit / total_principal * 100) if total_principal > 0 else 0
    status_icon = "\u2705 \u5168\u91cf\u66f4\u65b0" if report_type == "all_done" else "\u26a0\ufe0f \u90e8\u5206\u66f4\u65b0"
    final_title = f"{status_icon}: {total_profit:+.0f} ({yield_rate:+.2f}%)"
    final_body = f"\U0001f4c5 {today_str} \u51c0\u503c ({updated_count}/{total_funds})\n\n" + "\n".join(msg_lines)
    if not is_all_updated:
        final_body += f"\n\n\u26a0\ufe0f \u672a\u66f4\u65b0: {', '.join(missing_funds)}"

    send_notification(final_title, final_body)
    save_json(NIGHTLY_STATUS_FILE, {"date": today_str, "sent": True})
    print("Notification sent. Task complete.")


if __name__ == "__main__":
    run_check()
