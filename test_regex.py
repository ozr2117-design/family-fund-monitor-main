import requests
import re

def get_fund_holdings_regex(fund_code):
    url = f"http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=10&year=&month="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": f"http://fundf10.eastmoney.com/jjcc_{fund_code}.html"
    }
    r = requests.get(url, headers=headers)
    r.encoding = 'utf-8'
    
    match = re.search(r'content:"(.*?)",', r.text)
    if not match:
        return []
        
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

if __name__ == "__main__":
    import json
    data = get_fund_holdings_regex("020237")
    print(json.dumps(data, ensure_ascii=False, indent=2))
