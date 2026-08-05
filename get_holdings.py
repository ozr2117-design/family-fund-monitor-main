import akshare as ak
import json

funds = ["021273", "025547", "020237", "013680", "008984"]
result = {}

for fund in funds:
    try:
        df = ak.fund_portfolio_hold_em(symbol=fund, date="2024")
        if not df.empty:
            latest_date = df['季度'].max()
            df_latest = df[df['季度'] == latest_date].head(10)
            holdings = []
            for _, row in df_latest.iterrows():
                code = row['股票代码']
                # format code
                if code.startswith('6'):
                    code = 'sh' + code
                elif code.startswith('3') or code.startswith('0'):
                    code = 'sz' + code
                elif code.startswith('8') or code.startswith('4'):
                    code = 'bj' + code
                
                holdings.append({
                    "code": code,
                    "name": row['股票名称'],
                    "weight": float(row['占净值比例'])
                })
            result[fund] = holdings
    except Exception as e:
        print(f"Error for {fund}: {e}")

with open('new_holdings.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("Done")
