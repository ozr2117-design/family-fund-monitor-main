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
        "tag": "✅ 准确率高", 
        "text": "上周偏离值在0.1-0.5之间，可信度高", 
        "color": "#D4EDDA", # 浅绿色背景
        "text_color": "#155724" # 深绿色文字
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
    },
    "施罗德中国动力": {
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
    '财通优选C (金梓才/AI)': '021528',
    '新财通 (科技创新混合C)': '008984',
    '施罗德中国动力C (020237)': '020237',
    '摩根均衡C (梁鹏/周期)': '021274',
    '泰康新锐C (韩庆/成长)': '017366'
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
                        
                        # Extract date from index 30 (Format: 20231027153000)
                        data_date = ""
                        if len(data) > 30:
                            raw_time = data[30]
                            if len(raw_time) >= 8:
                                data_date = f"{raw_time[:4]}-{raw_time[4:6]}-{raw_time[6:8]}"
                        
                        price_data[code] = {'name': name, 'change': pct, 'date': data_date}
                except: continue
        return price_data
    except: return None

def get_fund_estimated_nav(fund_codes):
    """获取公募基金的实时估算涨跌幅 (天天基金估值接口)。
    返回格式与 get_realtime_price 一致: {code: {'name':..., 'change':..., 'date':...}}
    """
    result = {}
    for code in fund_codes:
        url = f"https://fundgz.1234567.com.cn/js/{code}.js"
        try:
            r = requests.get(url, timeout=4, headers={"Referer": "http://fund.eastmoney.com/"})
            import re as _re
            m = _re.search(r'jsonpgz\((.+)\)', r.text)
            if m:
                data = json.loads(m.group(1))
                name = data.get('name', code)
                # gszzl: 估算涨跌幅 (%), gztime: 估算时间
                pct_str = data.get('gszzl', '0')
                gztime = data.get('gztime', '')
                pct = float(pct_str) if pct_str else 0.0
                date_str = gztime[:10] if len(gztime) >= 10 else ''
                result[code] = {'name': name, 'change': pct, 'date': date_str}
        except:
            continue
    return result

def is_fund_code(code):
    """判断一个 code 是公募基金代码（6位纯数字）而非股票代码（带前缀sh/sz/hk等）"""
    return code.isdigit() and len(code) == 6

@st.cache_data(ttl=3600)
def get_official_nav_pct(fund_code):
    """获取最新两个净值并计算涨跌幅"""
    # 获取2条数据，确保能算出涨跌幅
    url = f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={fund_code}&pageIndex=1&pageSize=2"
    headers = {
        "Referer": "http://fund.eastmoney.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            res = r.json()
            if "Data" in res and "LSJZList" in res["Data"]:
                data = res["Data"]["LSJZList"]
                if len(data) >= 2:
                    today_nav = float(data[0]["DWJZ"])
                    yesterday_nav = float(data[1]["DWJZ"])
                    date_str = data[0]["FSRQ"]
                    
                    if yesterday_nav > 0:
                        pct = (today_nav - yesterday_nav) / yesterday_nav * 100
                        return pct, date_str
                elif len(data) == 1:
                     # 只有一天数据，尝试直接取 JZZZL (虽然不太准，但作为备用)
                     return float(data[0]["JZZZL"]), data[0]["FSRQ"]
    except: pass
    return None, None

def get_audit_status(est_val, actual_val):
    """计算偏差并返回审计状态"""
    if actual_val is None: return None
    
    diff = abs(est_val - actual_val)
    
    if diff <= 0.3:
        return {
            "tag": "✅ 准确率高",
            "text": f"偏差仅 {diff:.2f}%，估值非常精准",
            "color": "#D4EDDA",
            "text_color": "#155724",
            "icon": "🎯"
        }
    elif diff <= 1.0:
        return {
            "tag": "👌 偏差可控",
            "text": f"偏差 {diff:.2f}% 在正常范围内",
            "color": "#D1ECF1",
            "text_color": "#0C5460",
             "icon": "👌"
        }
    else:
        return {
            "tag": "⚠️ 偏差较大",
            "text": f"偏差 {diff:.2f}%，请注意市场异动",
            "color": "#FFF3CD",
            "text_color": "#856404",
             "icon": "⚠️"
        }

def fetch_fund_holdings(fund_code):
    """抓取基金最新季报前十大重仓股"""
    url = f"http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=10&year=&month="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": f"http://fundf10.eastmoney.com/jjcc_{fund_code}.html"
    }
    import re
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.encoding = 'utf-8'
        match = re.search(r'content:"(.*?)",', r.text)
        if not match: return []
        html = match.group(1)
        
        holdings = []
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.IGNORECASE | re.DOTALL)
        for row in rows[1:]:
            cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.IGNORECASE | re.DOTALL)
            if len(cols) >= 9:
                stock_code = re.sub(r'<[^>]+>', '', cols[1]).strip()
                stock_name = re.sub(r'<[^>]+>', '', cols[2]).strip()
                weight_str = re.sub(r'<[^>]+>', '', cols[6]).strip().replace('%', '')
                try:
                    weight_float = float(weight_str)
                    if len(stock_code) == 5:
                        prefix = 'hk'
                    else:
                        if stock_code.startswith('6'): prefix = 'sh'
                        elif stock_code.startswith('0') or stock_code.startswith('3'): prefix = 'sz'
                        elif stock_code.startswith('8') or stock_code.startswith('4') or stock_code.startswith('9'): prefix = 'bj'
                        else: prefix = 'sh'
                    holdings.append({
                        "code": f"{prefix}{stock_code}",
                        "name": stock_name,
                        "weight": weight_float
                    })
                except Exception:
                    pass
        return holdings
    except Exception as e:
        return []

# === 📈 历史数据与趋势分析 (Auto-Fetch) ===

@st.cache_data(ttl=3600*4)
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
    stats["full_last_date"] = last_date # YYYY-MM-DD
    
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
        
        # 🟢 交易状态逻辑 (Added by User Request)
        is_trading = False
        if bj_time.weekday() < 5: # Mon-Fri
            current_time = bj_time.time()
            # 简单构造时间对象用于比较 (注意：这里用replace是为了确保只比较时间部分，或者直接构造datetime)
            # 更简单的是比较 hour/minute
            t_val = current_time.hour * 100 + current_time.minute
            if (930 <= t_val <= 1130) or (1300 <= t_val <= 1500):
                is_trading = True
        
        # 🌟 交易状态胶囊 (美化版 Glassmorphism)
        if is_trading:
            # 交易中：活跃蓝
            status_text = "交易中"
            # CSS compacted to avoid indentation issues
            pill_style = "background: rgba(227, 242, 253, 0.6); color: #1565c0; border: 1px solid rgba(255, 255, 255, 0.6); backdrop-filter: blur(5px);"
            icon = "⚡" 
        else:
            # 休市中：优雅灰/暖色 (茶)
            status_text = "休市中"
            pill_style = "background: rgba(245, 245, 247, 0.6); color: #666; border: 1px solid rgba(255, 255, 255, 0.6); backdrop-filter: blur(5px);"
            icon = "☕"

        # NOTE: Indentation removed to prevent Markdown Code Block rendering
        st.markdown(f"""
<div style="display: flex; align-items: center; margin-top: -2px;">
<h2 style='margin: 0; color:#333; letter-spacing:0.5px; font-weight:300; font-size: 28px;'>Family Wealth</h2>
<div style='margin-left: 12px; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; letter-spacing: 0.5px; display: flex; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.04); {pill_style}'>
<span style='margin-right: 4px; font-size: 10px;'>{icon}</span> {status_text}
</div>
</div>
""", unsafe_allow_html=True)

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
            action_mode = st.radio("Tools", ["💾  收盘存证", "⚖️  晚间审计", "🔄  季报更新"], label_visibility="collapsed", index=None, key="action_radio")

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

            elif current_selection == "🔄  季报更新":
                st.divider()
                st.info("自动从天天基金获取最新前十大重仓股 (按持仓市值排序)")
                if st.button("🔄 一键更新季报持仓", type="primary", use_container_width=True):
                    with st.spinner("正在获取最新季报持仓..."):
                        updates = 0
                        for name, info in funds_config.items():
                            code = FUND_CODES_MAP.get(name)
                            if code:
                                new_holdings = fetch_fund_holdings(code)
                                if new_holdings and len(new_holdings) > 0:
                                    funds_config[name]['holdings'] = new_holdings
                                    updates += 1
                        if updates > 0:
                            save_json('funds.json', funds_config, config_sha, "Auto Update Holdings")
                            st.success(f"成功更新 {updates} 只基金的持仓数据！")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.warning("未能获取到新数据，或请求过于频繁。")

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
                    
                    # 判断持仓类型：股票 or 公募基金
                    fund_sub_codes = [s['code'] for s in info['holdings'] if is_fund_code(s['code'])]
                    
                    if fund_sub_codes:
                        # 🏦 FOF模式：子持仓为公募基金，使用天天基金估值接口
                        sub_fund_data = get_fund_estimated_nav(fund_sub_codes)
                        for s in info['holdings']:
                            d = sub_fund_data.get(s['code'])
                            if d:
                                val += d['change'] * s['weight']; w += s['weight']
                                if len(stocks) < 10:
                                    stocks.append({"name": d['name'], "pct": d['change']})
                    else:
                        # 📈 普通模式：子持仓为股票，使用腾讯行情
                        for s in info['holdings']:
                            d = market_data.get(s['code'])
                            if d:
                                val += d['change'] * s['weight']; w += s['weight']
                                if len(stocks) < 10: 
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
                    if 9 <= now_hour < 15 and est < -2.5 and est < bench_val:
                        signal_type = "BUY"
                        multiplier = 2 if est < -4.0 else 1
                        buy_amt = base_unit * multiplier
                        signal_desc = f"超跌错杀：跑输{bench_name} {abs(est-bench_val):.1f}%"
                        action_advice = f"建议加仓: +¥{buy_amt:,}"
                        if not signal_msg: signal_msg = "🎯 出现加仓机会"

                    # 2. 🔥 止盈
                    elif 9 <= now_hour < 15 and est > 3.0 and est > (bench_val + 1.5):
                        signal_type = "SELL"
                        signal_desc = f"短期过热：跑赢{bench_name} {abs(est-bench_val):.1f}%"
                        action_advice = "建议卖出: 1/4 持仓"
                        if not signal_msg: signal_msg = "🔥 出现止盈机会"

                    cards_data.append({
                        "name": name.split('(')[0].strip(),
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
                # 布局：2x2网格 - 增加间距
                # 第一行：预估收益 | 实际收益
                row1_col1, row1_col2 = st.columns(2, gap="medium")
                
                # A. 今日预估收益 - 自定义HTML
                if zen_mode:
                    display_value_1 = "****"
                else:
                    # 使用完整数字格式
                    if abs(total_profit) >= 1000:
                        display_value_1 = f"{total_profit:+,.0f}"
                    else:
                        display_value_1 = f"{total_profit:+.0f}"
                
                # 优先使用行情数据中的日期
                est_date_str = bj_time.strftime('%Y年%m月%d日')
                if market_data:
                    # 尝试从第一个有效数据中获取日期
                    for code, d in market_data.items():
                        if d.get('date'):
                            try:
                                ymd = d['date'].split('-')
                                est_date_str = f"{ymd[0]}年{int(ymd[1])}月{int(ymd[2])}日"
                                break
                            except: pass

                row1_col1.markdown(f"""
                <div style='background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(16px); 
                            border: 1px solid rgba(255, 255, 255, 0.6); padding: 15px 10px; 
                            border-radius: 20px; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05); 
                            min-height: 115px; display: flex; flex-direction: column; justify-content: center;'>
                    <div style='font-size: 12px; color: rgb(49, 51, 63); margin-bottom: 4px;'>
                        今日预估收益 <span style='font-size:11px; color:#999; margin-left:4px; font-weight:400'>{est_date_str}</span>
                    </div>
                    <div style='font-size: 16px; font-weight: 600; color: rgb(49, 51, 63); overflow: visible !important; text-overflow: clip !important; white-space: nowrap !important;'>{display_value_1}</div>
                </div>
                """, unsafe_allow_html=True)

                # B. 今日实际收益 - 自定义HTML
                if zen_mode:
                    display_value_2 = "****"
                    delta_display = ""
                else:
                    if actual_data_ready:
                        # 使用完整数字格式
                        if abs(total_actual_profit) >= 1000:
                            display_value_2 = f"{total_actual_profit:+,.0f}"
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
                    <div style='font-size: 16px; font-weight: 600; color: rgb(49, 51, 63); overflow: visible !important; text-overflow: clip !important; white-space: nowrap !important;'>{display_value_2}</div>
                    {delta_display}
                </div>
                """, unsafe_allow_html=True)

                # 增加行间距
                st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

                # 第二行：预估收益率 | 实际收益率
                row2_col1, row2_col2 = st.columns(2, gap="medium")
                
                # C. 预估收益率 - 自定义HTML
                est_yield_rate = (total_profit/total_principal*100) if total_principal > 0 else 0
                row2_col1.markdown(f"""
                <div style='background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(16px); 
                            border: 1px solid rgba(255, 255, 255, 0.6); padding: 15px 10px; 
                            border-radius: 20px; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05); 
                            min-height: 115px; display: flex; flex-direction: column; justify-content: center;'>
                    <div style='font-size: 12px; color: rgb(49, 51, 63); margin-bottom: 4px;'>预估收益率</div>
                    <div style='font-size: 16px; font-weight: 600; color: rgb(49, 51, 63); overflow: visible !important; text-overflow: clip !important; white-space: nowrap !important;'>{est_yield_rate:+.2f}%</div>
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
                    <div style='font-size: 16px; font-weight: 600; color: rgb(49, 51, 63); overflow: visible !important; text-overflow: clip !important; white-space: nowrap !important;'>{display_value_4}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. 💎 持仓列表
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
                
                # 获取最新日期用于标题显示
                latest_date_str = ""
                if cards_data:
                    # 尝试从第一个数据的 h_stats 中获取日期
                    try:
                        raw_date = cards_data[0]['h_stats']['last_date']
                        if raw_date and raw_date != "-":
                            # 格式化: 2026-02-06 -> 2026年2月6日收益情况
                            ymd = raw_date.split('-')
                            if len(ymd) == 3:
                                latest_date_str = f" <span style='font-size:11px; font-weight:400; color:#999; margin-left:6px'>{ymd[0]}年{int(ymd[1])}月{int(ymd[2])}日收益情况</span>"
                    except: pass

                st.markdown(f"<span style='color:#999; font-size:12px; letter-spacing:1px; margin-left:2px; font-weight:500'>PORTFOLIO</span>{latest_date_str}", unsafe_allow_html=True)
                
                # 定义简称映射
                FUND_ALIASES = {
                    "财通优选C": "财通",
                    "新财通": "新财通",
                    "施罗德中国动力C": "施耐德",
                    "摩根均衡C": "摩根",
                    "泰康新锐C": "泰康"
                }

                for card in cards_data:
                    icon = "👑" if card['est'] > 0 else "📿"
                    
                    title_suffix = f" {card['est']:+.2f}%"
                    if card['signal_type'] == "BUY": title_suffix += " 🎯 机会"
                    elif card['signal_type'] == "SELL": title_suffix += " 🔥 止盈"
                    
                    # ----------------------------------------------------
                    # 📊 昨日盈亏数据 (已移回卡片内部显示)
                    # ----------------------------------------------------
                    
                    # 使用简称
                    display_name = FUND_ALIASES.get(card['name'], card['name'])
                    
                    title = f"{icon} {display_name}{title_suffix}"
                    
                    with st.expander(title):
                        # ----------------------------------------------------
                        # 🔥 插入审计胶囊 (AUDIT PILL) - 动态版
                        # ----------------------------------------------------
                        pill_html = ""
                        audit_data = None
                        
                        # 1. 尝试获取今日实际净值进行动态对比
                        key_name = card['full_name'] # name is short, full_name is key
                        if key_name in nav_cache and today_str in nav_cache[key_name]:
                            actual_pct = nav_cache[key_name][today_str]
                            audit_data = get_audit_status(card['est'], actual_pct)
                        
                        # 2. 如果没有今日数据，尝试使用静态配置 (作为兜底)
                        if not audit_data:
                            for k, v in AUDIT_MEMO.items():
                                if k in card['full_name']:
                                    audit_data = v
                                    break
                        
                        # 3. 渲染
                        if audit_data:
                            # 确保兼容新旧字段
                            bg_color = audit_data.get('color', '#f8f9fa')
                            text_color = audit_data.get('text_color', '#333')
                            tag = audit_data.get('tag', 'Note')
                            text = audit_data.get('text', '')
                            
                            html_parts = [
                                f"<div class='audit-pill' style='background-color:{bg_color}; color:{text_color};'>",
                                f"<strong>{tag}</strong> | {text}",
                                "</div>"
                            ]
                            pill_html = "".join(html_parts)
                        
                        if pill_html:
                            st.markdown(pill_html, unsafe_allow_html=True)
                        
                        # ----------------------------------------------------
                        # 📊 昨日盈亏数据 (回归卡片内部)
                        # ----------------------------------------------------
                        h_stats = card['h_stats']
                        if h_stats['last_date'] != "-":
                            yes_profit = card['yes_profit']
                            abs_profit = abs(yes_profit)
                            y_sign_pct = "+" if h_stats['yesterday'] > 0 else ""
                            y_sign_money = "+" if yes_profit > 0 else "-"
                            
                            # 颜色逻辑保持一致：涨红跌绿
                            color_style = "color:#ff3b30" if h_stats['yesterday'] > 0 else "color:#34c759"
                            
                            s_icon = "🔥" if h_stats['streak_type'] == "up" else "🥶" if h_stats['streak_type'] == "down" else "😐"
                            s_text = f"{h_stats['streak']}连涨" if h_stats['streak_type'] == "up" else f"{h_stats['streak']}连跌" if h_stats['streak_type'] == "down" else "平盘"
                            
                            # 格式化日期：2026-02-06 -> 2026年2月6日
                            date_display = ""
                            try:
                                full_date = h_stats.get('full_last_date', '')
                                if full_date:
                                    ymd = full_date.split('-')
                                    date_display = f"{ymd[0]}年{int(ymd[1])}月{int(ymd[2])}日"
                            except: pass

                            st.markdown(f"""
                            <div style='
                                background-color: rgba(248, 249, 250, 0.7); 
                                border: 1px solid rgba(0,0,0,0.05); 
                                border-radius: 10px; 
                                padding: 10px 14px; 
                                display: flex; 
                                align-items: center; 
                                justify-content: space-between; 
                                margin-bottom: 15px;
                                margin-top: 4px;
                                font-family: -apple-system;
                            '>
                                <div style='display:flex; align-items:center;'>
                                    <span style='color:#8e8e93; font-size:12px; font-weight:500; letter-spacing:0.3px'>{date_display}</span>
                                    <div style='width:1px; height:12px; background:#ddd; margin:0 8px;'></div>
                                    <span style='{color_style}; font-size:14px; font-weight:600; font-variant-numeric: tabular-nums;'>{y_sign_pct}{h_stats['yesterday']:.2f}%</span>
                                    <span style='{color_style}; font-size:14px; font-weight:600; margin-left:6px; font-variant-numeric: tabular-nums;'>{y_sign_money}¥{abs_profit:,.0f}</span>
                                </div>
                                <div style='
                                    background: rgba(0,0,0,0.04); 
                                    padding: 3px 8px; 
                                    border-radius: 6px; 
                                    font-size: 11px; 
                                    font-weight: 600; 
                                    color: #555;
                                    display: flex;
                                    align-items: center;
                                '>
                                    {s_icon} <span style='margin-left:3px'>{s_text}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
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
                            <div style='font-size:12px; color:#888; margin-bottom:2px'>今日预估盈亏</div>
                            <div style='font-size:20px; font-weight:600; color:{color_code}; font-family:-apple-system'>{profit_display}</div>
                            <div style='height:15px'></div>
                            <div style='font-size:12px; color:#888; margin-bottom:2px'>本金</div>
                            <div style='font-size:16px; color:#333; font-weight:500'>{principal_display}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 改为2列网格布局，展示前10大持仓
                        list_html = "<div class='ios-list-container' style='display: grid; grid-template-columns: 1fr 1fr; gap: 0 12px;'>"
                        for i, s in enumerate(card['stocks']):
                            bg_color = "#ff3b30" if s['pct'] > 0 else ("#34c759" if s['pct'] < 0 else "#8e8e93")
                            txt_color = "white"
                            # 简化行样式，适应网格
                            list_html += f"<div class='ios-row' style='border-bottom: 1px solid rgba(0,0,0,0.03); padding: 6px 0;'><div class='ios-index'>{i+1}</div><div class='ios-name' style='font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{s['name']}</div><div class='ios-pill' style='background-color:{bg_color}; color:{txt_color}; font-size:12px; padding:2px 6px; min-width:50px;'>{s['pct']:+.2f}%</div></div>"
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
