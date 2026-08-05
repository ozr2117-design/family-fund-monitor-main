import requests
from bs4 import BeautifulSoup
import re

def get_fund_holdings(fund_code):
    url = f"http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={fund_code}&topline=10&year=&month="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": f"http://fundf10.eastmoney.com/jjcc_{fund_code}.html"
    }
    r = requests.get(url, headers=headers)
    r.encoding = 'utf-8'
    
    # Extract HTML part from JS response
    match = re.search(r'content:"(.*?)",', r.text)
    if not match:
        print("Could not match content")
        return []
        
    html = match.group(1)
    soup = BeautifulSoup(html, 'html.parser')
    
    table = soup.find('table')
    if not table:
        print("No table found")
        return []
        
    holdings = []
    rows = table.find_all('tr')
    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) >= 9:
            stock_code = cols[1].text.strip()
            stock_name = cols[2].text.strip()
            weight = cols[6].text.strip().replace('%', '')
            try:
                weight_float = float(weight)
                
                # Format stock code
                prefix = 'hk'
                if stock_code.startswith('6'):
                    prefix = 'sh'
                elif stock_code.startswith('00') or stock_code.startswith('30') or stock_code.startswith('002'):
                    prefix = 'sz'
                elif stock_code.startswith('0') or stock_code.startswith('1'):
                    prefix = 'hk' # Basic heuristic
                
                # specific for some codes
                if stock_code.startswith('00'):
                    prefix = 'sz'
                
                formatted_code = f"{prefix}{stock_code}"
                
                holdings.append({
                    "code": formatted_code,
                    "name": stock_name,
                    "weight": weight_float
                })
            except Exception as e:
                pass
    return holdings

if __name__ == "__main__":
    import json
    data = get_fund_holdings("020237")
    with open("test_out.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
