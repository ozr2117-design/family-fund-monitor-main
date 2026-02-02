import streamlit as st
import requests
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from github import Github

# ==========================================
# 0. 🎯 核心配置：人工审计日志 (Audit Memo)
# ==========================================
# 这里就是你要的“审计胶囊”配置
AUDIT_MEMO = {
    "摩根均衡": {
        "tag": "⚠️ 偏离较高", 
        "text": "上周偏离 -0.7%，需注意误差", 
        "color": "#FFF3CD", # 浅橙色背景
        "text_color": "#856404" # 深褐色文字
    },
    "泰康新锐": {
        "tag": "✅ 准确率高", 
        "text": "基本跟净值一致，可信度高", 
        "color": "#D4EDDA", # 浅绿色背景
        "text_color": "#155724" # 深绿色文字
    },
    "财通优选": {
        "tag": "👌 偏差可控", 
        "text": "偏离值可接受，参考性强", 
        "color": "#D1ECF1", # 浅蓝色背景
        "text_color": "#0C5460" # 深蓝色文字
    }
}

# === 🎨 1. 页面配置与 CSS 魔法 (Apple Glassmorphism V5.1) ===
st.set_page_config(
    page_title="Family Wealth",
    page_icon="💎",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 注入 CSS：极光背景 + 信号卡片 + 禅模式样式 + 审计胶囊样式
st.markdown("""
    <style>
    /* 1. 全局极光背景 */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(255, 230, 240, 0.4) 0%, rgba(255, 255, 255, 0) 40%),
                    radial-gradient(circle at 90% 80%, rgba(230, 240, 255, 0.4) 0%, rgba(255, 255, 255, 0) 40%),
                    #fdfdfd;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
    }
    
    /* 2. 隐藏无关元素 */
    [data-testid="stSidebar"] {display: none;}
    [data-testid="stSidebarCollapsedControl"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 3. Settings 按钮 */
    div[data-testid="stPopover"] > button {
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        background-color: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        color: #666;
        font-size: 13px;
        padding: 4px 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        transition: all 0.2s;
    }
    div[data-testid="stPopover"] > button:hover {
        background-color: #fff;
        color: #007aff;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,122,255,0.15);
        border-color: #007aff;
    }

    /* 4. Popover 内部美化 */
    div[data-testid="stPopoverBody"] {
        background-color: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.5);
        padding: 15px !important;
    }
    div[role="radiogroup"] label > div:first-child { display: none !important; }
    div[role="radiogroup"] label {
        background-color: rgba(255, 255, 255, 0.6);
        padding: 12px 15px !important;
        border-radius: 12px !important;
        margin-bottom: 8px !important;
        border: 1px solid rgba(0,0,0,0.05);
        transition: all 0.2s ease;
        display: flex; width: 100%; color: #444;
    }
    div[role="radiogroup"] label:hover { background-color: #f5f5f7; transform: translateX(2px); }
    div[role="radiogroup"] [data-testid="stMarkdownContainer"] p { font-size: 14px; font-weight: 500; margin: 0; }

    /* 5. 收益率大卡片 */
    /* 5. 收益率大卡片 */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        padding: 15px 10px; /* Reduced horizontal padding */
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05);
        min-height: 115px !important; 
        max-height: 115px !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Optimize font size for metric values - Multiple selectors for maximum coverage */
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetric"] div[data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        font-size: 16px !important;
        overflow: visible !important;
        text-overflow: clip !important;
        max-width: none !important;
    }
    
    
    /* Also reduce metric label font for better space utilization */
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] > *,
    div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {
        font-size: 12px !important;
    }
    
    /* Desktop-specific fixes for metric display */
    @media (min-width: 768px) {
        /* Force Streamlit columns to respect width on desktop */
        div[data-testid="column"] {
            min-width: 0 !important;
            flex: 1 1 0 !important;
        }
        
        /* Ensure metric values don't get truncated on desktop */
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricValue"] > div {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            word-break: normal !important;
        }
    }
    
    /* 6. 基金卡片 & 列表 */
    div[data-testid="stExpander"] {
        border: none;
        box-shadow: 0 8px 24px rgba(0,0,0,0.03);
        border-radius: 16px;
        background-color: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(10px);
        margin-bottom: 15px;
        overflow: hidden;
    }
    .ios-list-container { display: flex; flex-direction: column; width: 100%; }
    .ios-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(0,0,0,0.06); width: 100%; }
    .ios-row:last-child { border-bottom: none; }
    .ios-index { font-size: 12px; color: #aaa; width: 24px; font-weight: 600; margin-right: 8px; }
    .ios-name { font-size: 14px; color: #333; font-weight: 500; flex: 1; margin-right: 10px; }
    .ios-pill { padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; min-width: 65px; text-align: right; color: white; font-family: -apple-system; }
    .detail-box { background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.4); }
    
    /* 🔥 信号提示卡片样式 */
    .signal-buy {
        background-color: #f6ffed;
        border: 1px solid #b7eb8f;
        color: #389e0d;
        padding: 10px 14px;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 6px rgba(56, 158, 13, 0.05);
    }
    .signal-sell {
        background-color: #fff2f0;
        border: 1px solid #ffccc7;
        color: #cf1322;
        padding: 10px 14px;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 6px rgba(207, 19, 34, 0.05);
    }

    /* 💊 审计胶囊样式 (新增) */
    .audit-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        margin-bottom: 12px;
        font-family: -apple-system;
    }
    </style>
""", unsafe_allow_html=True)

# === 📊 核心数据定义 ===
MARKET_INDICES = {
    'sh000001': '上证指数',
    'sz399006': '创业板指',
    'hkHSTECH': '恒生科技'
}

FUND_CODES_MAP = {
    '摩根均衡C (梁鹏/周期)': '021274',
    '泰康新锐C (韩庆/成长)': '017366',
    '财通优选C (金梓才/AI)': '021528'
}

# === 🛠️ 辅助逻辑：智能匹配基准 ===
def get_benchmark_code(fund_name):
    if "周期" in fund_name or "均衡" in fund_name:
        return 'sh000001', '上证'
    elif "成长" in fund_name or "AI" in fund_name or "优选" in fund_name:
        return 'sz399006', '创指'
    else:
        return 'sh000001', '上证'

# === 🛠️ GitHub 数据库操作 ===

def get_repo():
    try:
        token = st.secrets["github_token"]
        username = st.secrets["github_username"]
        repo_name = st.secrets["repo_name"]
        g = Github(token)
        return g.get_user(username).get_repo(repo_name)
    except Exception as e:
        st.error(f"GitHub 连接失败: {e}")
        return None

def load_json(filename):
    repo = get_repo()
    if not repo: return {}, None
    try:
        content = repo.get_contents(filename)
        return json.loads(content.decoded_content.decode('utf-8')), content.sha
    except:
        return {}, None

def save_json(filename, data, sha, message):
    repo = get_repo()
    if repo:
        new_content = json.dumps(data, indent=4, ensure_ascii=False)
        if sha:
            repo.update_file(filename, message, new_content, sha)
        else:
            repo.create_file(filename, message, new_content)

def save_factor_history(date_str, new_factors_dict):
    history, sha = load_json('factor_history.json')
    if not isinstance(history, dict): history = {}
    existing_record = history.get(date_str, {})
    existing_record.update(new_factors_dict)
    history[date_str] = existing_record
    save_json('factor_history.json', history, sha, f"Factor Log {date_str}")

# === 🕷️ 数据获取 ===

def get_realtime_price(stock_codes):
    if not stock_codes: return {}
    codes_str = ",".join(stock_codes)
    url = f"http://qt.gtimg.cn/q={codes_str}"
    try:
        r = requests.get(url, timeout=3)
        text = r.text
        price_data = {}
        parts = text.split(';')
        for part in parts:
            if '="' in part:
                try:
                    key_raw = part.split('=')[0].strip()
                    code = key_raw.split('_')[-1] 
                    data = part.split('="')[1].strip('"').split('~')
                    if len(data) > 30:
                        name = data[1].replace(" ", "")
                        current = float(data[3])
                        close = float(data[4])
                        pct = 0.0
                        if close > 0: pct = ((current - close) / close) * 100
                        price_data[code] = {'name': name, 'change': pct}
                except: continue
        return price_data
    except: return None

def get_official_nav(fund_code):
    url = f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={fund_code}&pageIndex=1&pageSize=1"
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
                    return float(latest_data["JZZZL"]), latest_data["FSRQ"]
    except: pass
    return None, None

# === 📈 历史数据与趋势分析 (Auto-Fetch) ===

def fetch_fund_history(fund_code, limit=20):
    """从天天基金接口抓取历史净值"""
    timestamp = int(time.time() * 1000)
    url = f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={fund_code}&pageIndex=1&pageSize={limit}&_={timestamp}"
    headers = {
        "Referer": "http://fund.eastmoney.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            res = r.json()
            if "Data" in res and "LSJZList" in res["Data"]:
                return res["Data"]["LSJZList"]
    except: pass
    return []

def update_history_cache(funds_config):
    """检查并更新历史净值缓存"""
    cache, sha = load_json('nav_history.json')
    if not isinstance(cache, dict): cache = {}
    
    need_save = False
    today = datetime.now().strftime("%Y-%m-%d")
    
    for name, info in funds_config.items():
        code = FUND_CODES_MAP.get(name)
        if not code: continue
        
        # 使用全名作为 Key，避免分割带来的混淆
        key_name = name
        if key_name not in cache: cache[key_name] = {}
        
        fund_history = cache[key_name]
        
        # 简单策略：如果最新数据的日期早于今天，就尝试更新
        sorted_dates = sorted(fund_history.keys())
        last_date = sorted_dates[-1] if sorted_dates else "2000-01-01"
        
        if last_date < today:
            data = fetch_fund_history(code)
            if data:
                count_new = 0
                for item in data:
                    d = item["FSRQ"]
                    try:
                        val = float(item["JZZZL"]) if item["JZZZL"] else 0.0
                        if d not in fund_history:
                            fund_history[d] = val
                            count_new += 1
                            need_save = True
                    except: pass
                if count_new > 0:
                    try:
                        st.toast(f"已更新: {name.split('(')[0]} ({count_new}条)")
                    except: pass
                
    if need_save:
        save_json('nav_history.json', cache, sha, f"Auto Update {today}")
    
    return cache

def get_dashboard_stats(fund_name, cache):
    """计算昨日收益和连涨连跌趋势"""
    key_name = fund_name
    stats = {"yesterday": 0, "streak": 0, "streak_type": "none", "last_date": "-"}
    
    if key_name not in cache: return stats
    
    history = cache[key_name]
    if not history: return stats
    
    # 按日期倒序
    dates = sorted(history.keys(), reverse=True)
    if not dates: return stats
    
    # 1. 昨日（最新）数据
    last_date = dates[0]
    stats["yesterday"] = history[last_date]
    stats["last_date"] = last_date[5:] # 只显示 MM-DD
    
    # 2. 连涨连跌计算
    if len(dates) < 2: return stats
    
    first_val = history[dates[0]]
    if first_val > 0:
        streak_type = "up"
    elif first_val < 0:
        streak_type = "down"
    else:
        streak_type = "flat"
        
    count = 1
    for d in dates[1:]:
        val = history[d]
        # 容错：0% 视为中断，或者延续？通常视为中断
        if (streak_type == "up" and val > 0) or \
           (streak_type == "down" and val < 0):
            count += 1
        else:
            break
            
    stats["streak"] = count
    stats["streak_type"] = streak_type
    
    return stats

# === 🚀 主程序 ===
def main():
    funds_config, config_sha = load_json('funds.json')
    if not funds_config: st.stop()

    # 🔥 自动更新历史数据
    nav_cache = update_history_cache(funds_config)

    # ==========================================
    # 🌟 顶部导航栏
    # ==========================================
    
    bj_time = datetime.utcnow() + timedelta(hours=8)
    now_hour = bj_time.hour
    greeting = "Good Morning ☀️" if 5 <= now_hour < 12 else "Good Afternoon ☕" if 12 <= now_hour < 18 else "Good Evening 🌙"

    top_col1, top_col2 = st.columns([3, 1])
    
    with top_col1:
        st.caption(f"{greeting} | {bj_time.strftime('%m-%d %H:%M')}")
        st.markdown(f"<h2 style='margin-top:-10px; color:#333; letter-spacing:0.5px; font-weight:300'>Family Wealth</h2>", unsafe_allow_html=True)

    # 🔥 禅模式状态初始化 (默认关闭)
    zen_mode = False

    with top_col2:
        with st.popover("⚙️ Settings", use_container_width=True):
            st.caption("Mode")
            # 🔥 禅模式开关
            zen_mode = st.toggle("🧘 禅模式 (隐藏金额)", value=False)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            st.caption("Views")
            mode = st.radio("Navigation", ["📡  实时看板", "💰  持仓管理"], label_visibility="collapsed", key="nav_radio")
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.caption("Actions")
            action_mode = st.radio("Tools", ["💾  收盘存证", "⚖️  晚间审计"], label_visibility="collapsed", index=None, key="action_radio")

            current_selection = action_mode if action_mode else mode

            # 💰 持仓管理
            if current_selection == "💰  持仓管理":
                st.divider()
                st.info("Manage Holdings & Strategy")
                with st.form("holding_form_pop"):
                    new_holdings = {}
                    new_bases = {}
                    
                    for name, info in funds_config.items():
                        short_name = name.split('(')[0]
                        st.markdown(f"**{short_name}**")
                        col_h1, col_h2 = st.columns(2)
                        
                        current_val = info.get('holding_value', 0)
                        val_h = col_h1.number_input(f"持仓 (¥)", value=float(current_val), step=100.0, key=f"h_{name}")
                        
                        current_base = info.get('base_unit', 1000)
                        val_b = col_h2.number_input(f"单次加仓 (¥)", value=float(current_base), step=100.0, key=f"b_{name}")
                        
                        new_holdings[name] = val_h
                        new_bases[name] = val_b
                        st.divider()
                    
                    if st.form_submit_button("Save Changes"):
                        for name in funds_config.keys():
                            funds_config[name]['holding_value'] = new_holdings[name]
                            funds_config[name]['base_unit'] = new_bases[name]
                        save_json('funds.json', funds_config, config_sha, "Update Config")
                        st.toast("Updated Successfully!")
                        time.sleep(1); st.rerun()

            elif current_selection == "💾  收盘存证":
                st.divider()
                if st.button("📸 Run Snapshot", type="primary", use_container_width=True):
                    with st.spinner("Processing..."):
                        snapshot_data = {}
                        all_codes = []
                        for f in funds_config.values():
                            for s in f['holdings']: all_codes.append(s['code'])
                        prices = get_realtime_price(list(set(all_codes)))
                        if prices:
                            today_str = bj_time.strftime("%Y-%m-%d")
                            for name, info in funds_config.items():
                                val = 0; w = 0
                                for s in info['holdings']:
                                    if s['code'] in prices:
                                        val += prices[s['code']]['change'] * s['weight']; w += s['weight']
                                snapshot_data[name] = val / w if w > 0 else 0
                            history, hist_sha = load_json('history.json')
                            history[today_str] = snapshot_data
                            save_json('history.json', history, hist_sha, f"Snapshot {today_str}")
                            st.success(f"Snapshot Saved: {today_str}")

            elif current_selection == "⚖️  晚间审计":
                st.divider()
                if st.button("🚀 Start Audit", type="primary", use_container_width=True):
                    history, _ = load_json('history.json')
                    factor_hist, _ = load_json('factor_history.json')
                    if history:
                        last_date = sorted(history.keys())[-1]
                        audited = factor_hist.get(last_date, {}) if factor_hist else {}
                        updates = []; need_save = False; current_success = {}
                        progress = st.progress(0)
                        for idx, (name, info) in enumerate(funds_config.items()):
                            if name in audited: progress.progress((idx+1)/len(funds_config)); continue
                            raw = history[last_date].get(name)
                            code = FUND_CODES_MAP.get(name)
                            if raw is not None and code:
                                off_pct, off_date = get_official_nav(code)
                                if off_date and off_date >= last_date and raw != 0:
                                    new_f = (info['factor'] * 0.8) + ((off_pct / raw) * 0.2)
                                    funds_config[name]['factor'] = round(new_f, 4)
                                    current_success[name] = round(new_f, 4)
                                    need_save = True
                            progress.progress((idx+1)/len(funds_config))
                        if need_save:
                            save_json('funds.json', funds_config, config_sha, "Audit")
                            save_factor_history(last_date, current_success)
                            st.success("Factors Optimized!"); time.sleep(1); st.rerun()
                        else: st.info("No updates needed today")

            st.divider()
            with st.expander("📊 Stability Check"):
                fh, _ = load_json('factor_history.json')
                if fh: st.line_chart(pd.DataFrame.from_dict(fh, orient='index').sort_index())

    # ==========================================
    # 👇 主展示区 (全域火控版 + 禅模式)
    # ==========================================
    if "持仓管理" not in str(mode) and "持仓管理" not in str(action_mode):
        placeholder = st.empty()
        
        all_codes = list(MARKET_INDICES.keys())
        for f in funds_config.values():
            for s in f['holdings']: all_codes.append(s['code'])
        all_codes = list(set(all_codes))
        
        while True:
            with placeholder.container():
                market_data = get_realtime_price(all_codes)
                if not market_data:
                    st.warning("Connecting..."); time.sleep(2); continue
                
                total_profit = 0
                total_principal = 0
                cards_data = []
                signal_msg = None
                
                for name, info in funds_config.items():
                    factor = info.get('factor', 1.0)
                    principal = info.get('holding_value', 0)
                    base_unit = info.get('base_unit', 1000) 
                    
                    val = 0; w = 0; stocks = []
                    for s in info['holdings']:
                        d = market_data.get(s['code'])
                        if d:
                            val += d['change'] * s['weight']; w += s['weight']
                            if len(stocks) < 3: 
                                stocks.append({"name": d['name'], "pct": d['change']})
                    
                    est = (val / w * factor) if w > 0 else 0
                    profit = principal * est / 100
                    total_profit += profit
                    total_principal += principal
                    
                    # 📈 历史统计 & 实际收益计算
                    h_stats = get_dashboard_stats(name, nav_cache)
                    yes_profit = principal * h_stats['yesterday'] / 100
                    
                    # 信号逻辑
                    bench_code, bench_name = get_benchmark_code(name)
                    bench_val = 0
                    if bench_code in market_data: bench_val = market_data[bench_code]['change']
                    
                    signal_type = None 
                    signal_desc = ""
                    action_advice = ""
                    
                    # 1. 🎯 买入
                    if est < -2.5 and est < bench_val:
                        signal_type = "BUY"
                        multiplier = 2 if est < -4.0 else 1
                        buy_amt = base_unit * multiplier
                        signal_desc = f"超跌错杀：跑输{bench_name} {abs(est-bench_val):.1f}%"
                        action_advice = f"建议加仓: +¥{buy_amt:,}"
                        if not signal_msg: signal_msg = "🎯 出现加仓机会"

                    # 2. 🔥 止盈
                    elif est > 3.0 and est > (bench_val + 1.5):
                        signal_type = "SELL"
                        signal_desc = f"短期过热：跑赢{bench_name} {abs(est-bench_val):.1f}%"
                        action_advice = "建议卖出: 1/4 持仓"
                        if not signal_msg: signal_msg = "🔥 出现止盈机会"

                    cards_data.append({
                        "name": name.split('(')[0],
                        "full_name": name, # 保留全名用于匹配胶囊
                        "est": est,
                        "profit": profit,
                        "principal": principal,
                        "stocks": stocks,
                        "signal_type": signal_type,
                        "signal_desc": signal_desc,
                        "action_advice": action_advice,
                        "h_stats": h_stats,
                        "yes_profit": yes_profit
                    })
                
                # Toast
                if signal_msg: st.toast(signal_msg)

                # 1. 💰 核心收益看板 (改版：预估 vs 实际)
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 计算今日实际收益 (基于 nav_cache)
                today_str = bj_time.strftime("%Y-%m-%d")
                total_actual_profit = 0
                actual_data_ready = True # 假设数据已准备好，除非发现缺失
                
                for name, info in funds_config.items():
                    # 检查缓存里是否有今天的日期
                    key_name = name
                    if key_name not in nav_cache or today_str not in nav_cache[key_name]:
                        actual_data_ready = False
                        break
                    else:
                        pct = nav_cache[key_name][today_str]
                        total_actual_profit += info.get('holding_value', 0) * pct / 100

                # 布局：2x2网格 - 给每个指标更多水平空间
                # 第一行：预估收益 | 实际收益
                row1_col1, row1_col2 = st.columns(2)
                
                # A. 今日预估收益 - 自定义HTML
                if zen_mode:
                    display_value_1 = "****"
                else:
                    # 使用K格式缩短数字显示
                    if abs(total_profit) >= 1000:
                        display_value_1 = f"{total_profit/1000:+.1f}K"
                    else:
                        display_value_1 = f"{total_profit:+.0f}"
                
                row1_col1.markdown(f"""
                <div style='background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(16px); 
                            border: 1px solid rgba(255, 255, 255, 0.6); padding: 15px 10px; 
                            border-radius: 20px; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05); 
                            min-height: 115px; display: flex; flex-direction: column; justify-content: center;'>
                    <div style='font-size: 12px; color: rgb(49, 51, 63); margin-bottom: 4px;'>今日预估收益</div>
                    <div style='font-size: 16px; font-weight: 600; color: rgb(49, 51, 63);'>{display_value_1}</div>
                </div>
                """, unsafe_allow_html=True)

                # B. 今日实际收益 - 自定义HTML
                if zen_mode:
                    display_value_2 = "****"
                    delta_display = ""
                else:
                    if actual_data_ready:
                        # 使用K格式缩短数字显示
                        if abs(total_actual_profit) >= 1000:
                            display_value_2 = f"{total_actual_profit/1000:+.1f}K"
                        else:
                            display_value_2 = f"{total_actual_profit:+.0f}"
                        delta_val = total_actual_profit - total_profit
                        delta_color = "#00ab41" if delta_val >= 0 else "#ff2b2b"
                        delta_display = f"<div style='font-size: 11px; color: {delta_color}; margin-top: 4px;'>{delta_val:+.0f} 差额</div>"
                    else:
                        display_value_2 = "💎"
                        delta_display = ""
                
                row1_col2.markdown(f"""
                <div style='background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(16px); 
                            border: 1px solid rgba(255, 255, 255, 0.6); padding: 15px 10px; 
                            border-radius: 20px; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05); 
                            min-height: 115px; display: flex; flex-direction: column; justify-content: center;'>
                    <div style='font-size: 12px; color: rgb(49, 51, 63); margin-bottom: 4px;'>今日实际收益</div>
                    <div style='font-size: 16px; font-weight: 600; color: rgb(49, 51, 63);'>{display_value_2}</div>
                    {delta_display}
                </div>
                """, unsafe_allow_html=True)

                # 第二行：预估收益率 | 实际收益率
                row2_col1, row2_col2 = st.columns(2)
                
                # C. 预估收益率 - 自定义HTML
                est_yield_rate = (total_profit/total_principal*100) if total_principal > 0 else 0
                row2_col1.markdown(f"""
                <div style='background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(16px); 
                            border: 1px solid rgba(255, 255, 255, 0.6); padding: 15px 10px; 
                            border-radius: 20px; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05); 
                            min-height: 115px; display: flex; flex-direction: column; justify-content: center;'>
                    <div style='font-size: 12px; color: rgb(49, 51, 63); margin-bottom: 4px;'>预估收益率</div>
                    <div style='font-size: 16px; font-weight: 600; color: rgb(49, 51, 63);'>{est_yield_rate:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

                # D. 实际收益率 - 自定义HTML
                if actual_data_ready:
                    act_yield_rate = (total_actual_profit/total_principal*100) if total_principal > 0 else 0
                    display_value_4 = f"{act_yield_rate:+.2f}%"
                else:
                    display_value_4 = "💎"
                
                row2_col2.markdown(f"""
                <div style='background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(16px); 
                            border: 1px solid rgba(255, 255, 255, 0.6); padding: 15px 10px; 
                            border-radius: 20px; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05); 
                            min-height: 115px; display: flex; flex-direction: column; justify-content: center;'>
                    <div style='font-size: 12px; color: rgb(49, 51, 63); margin-bottom: 4px;'>实际收益率</div>
                    <div style='font-size: 16px; font-weight: 600; color: rgb(49, 51, 63);'>{display_value_4}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. 💎 持仓列表
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
                st.markdown("<span style='color:#999; font-size:12px; letter-spacing:1px; margin-left:2px; font-weight:500'>PORTFOLIO</span>", unsafe_allow_html=True)
                
                for card in cards_data:
                    icon = "👑" if card['est'] > 0 else "📿"
                    
                    title_suffix = f" {card['est']:+.2f}%"
                    if card['signal_type'] == "BUY": title_suffix += " 🎯 机会"
                    elif card['signal_type'] == "SELL": title_suffix += " 🔥 止盈"
                    
                    title = f"{icon} {card['name']}{title_suffix}"
                    
                    with st.expander(title):
                        # ----------------------------------------------------
                        # 🔥 插入审计胶囊 (AUDIT PILL) - 抗干扰版
                        # ----------------------------------------------------
                        pill_html = ""
                        for k, v in AUDIT_MEMO.items():
                            if k in card['full_name']: # 匹配全名
                                # 使用列表拼接，彻底防止 f-string 缩进引发的 Markdown 渲染错误
                                html_parts = [
                                    f"<div class='audit-pill' style='background-color:{v['color']}; color:{v['text_color']};'>",
                                    f"<strong>{v['tag']}</strong> | {v['text']}",
                                    "</div>"
                                ]
                                pill_html = "".join(html_parts)
                                break
                        
                        if pill_html:
                            st.markdown(pill_html, unsafe_allow_html=True)
                        
                        # ----------------------------------------------------
                        # 📊 历史数据看板 (NEW)
                        # ----------------------------------------------------
                        h_stats = card['h_stats']
                        yes_profit = card['yes_profit']
                        
                        if h_stats['last_date'] != "-":
                            col_h1, col_h2 = st.columns(2)
                            
                            # 昨日盈亏
                            y_color = "#d93025" if h_stats['yesterday'] > 0 else "#1e8e3e"
                            y_sign = "+" if h_stats['yesterday'] > 0 else ""
                            col_h1.markdown(f"""
                            <div style='background:rgba(255,255,255,0.4); border-radius:8px; padding:8px 12px;'>
                                <div style='font-size:11px; color:#666'>昨日 ({h_stats['last_date']})</div>
                                <div style='font-size:14px; font-weight:600; color:{y_color}'>{y_sign}¥{yes_profit:,.1f}</div>
                                <div style='font-size:10px; color:#999'>{y_sign}{h_stats['yesterday']}%</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 连涨连跌
                            s_icon = "🔥" if h_stats['streak_type'] == "up" else "🥶" if h_stats['streak_type'] == "down" else "😐"
                            s_text = f"{h_stats['streak']}连涨" if h_stats['streak_type'] == "up" else f"{h_stats['streak']}连跌" if h_stats['streak_type'] == "down" else "平盘"
                            s_bg = "#fff2f0" if h_stats['streak_type'] == "up" else "#f6ffed" if h_stats['streak_type'] == "down" else "#f5f5f5"
                            s_color = "#cf1322" if h_stats['streak_type'] == "up" else "#389e0d" if h_stats['streak_type'] == "down" else "#666"
                            
                            col_h2.markdown(f"""
                            <div style='background:{s_bg}; border-radius:8px; padding:8px 12px; height:100%; display:flex; align-items:center;'>
                                <div style='font-size:13px; font-weight:600; color:{s_color}'>
                                    {s_icon} {s_text}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                        # ----------------------------------------------------

                        # 信号区域 (不受禅模式影响，必须清晰)
                        if card['signal_type'] == "BUY":
                            st.markdown(f"<div class='signal-buy'><div><div>🎯 {card['signal_desc']}</div><div style='font-size:15px; margin-top:4px'>👉 {card['action_advice']}</div></div></div>", unsafe_allow_html=True)
                        elif card['signal_type'] == "SELL":
                            st.markdown(f"<div class='signal-sell'><div><div>🔥 {card['signal_desc']}</div><div style='font-size:15px; margin-top:4px'>👉 {card['action_advice']}</div></div></div>", unsafe_allow_html=True)

                        # 详情数据 (禅模式屏蔽逻辑)
                        kc1, kc2 = st.columns([1.1, 2])
                        color_code = "#ff3b30" if card['profit']>0 else "#34c759"
                        
                        if zen_mode:
                            profit_display = "<span style='color:#aaa'>****</span>"
                            principal_display = "****"
                        else:
                            profit_display = f"￥{card['profit']:+.1f}"
                            principal_display = f"￥{card['principal']:,}"
                        
                        kc1.markdown(f"""
                        <div class='detail-box'>
                            <div style='font-size:12px; color:#888; margin-bottom:2px'>今日盈亏</div>
                            <div style='font-size:20px; font-weight:600; color:{color_code}; font-family:-apple-system'>{profit_display}</div>
                            <div style='height:15px'></div>
                            <div style='font-size:12px; color:#888; margin-bottom:2px'>本金</div>
                            <div style='font-size:16px; color:#333; font-weight:500'>{principal_display}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        list_html = "<div class='ios-list-container'>"
                        for i, s in enumerate(card['stocks']):
                            bg_color = "#ff3b30" if s['pct'] > 0 else ("#34c759" if s['pct'] < 0 else "#8e8e93")
                            txt_color = "white"
                            list_html += f"<div class='ios-row'><div class='ios-index'>{i+1}</div><div class='ios-name'>{s['name']}</div><div class='ios-pill' style='background-color:{bg_color}; color:{txt_color}'>{s['pct']:+.2f}%</div></div>"
                        list_html += "</div>"
                        
                        kc2.markdown(list_html, unsafe_allow_html=True)

                # 3. 🌍 底部大盘
                st.divider()
                st.markdown("<span style='color:#999; font-size:12px; letter-spacing:1px; margin-left:2px; font-weight:500'>MARKET INDICES</span>", unsafe_allow_html=True)
                mc1, mc2, mc3 = st.columns(3)
                m_cols = [mc1, mc2, mc3]
                for i, code in enumerate(MARKET_INDICES):
                    d = market_data.get(code)
                    if d: m_cols[i].metric(MARKET_INDICES[code], f"{d['change']:.2f}%")

            time.sleep(30)

if __name__ == "__main__":
    main()
