import re

# Update app.py
with open('app.py', 'r', encoding='utf-8') as f:
    app_content = f.read()

# Replace AUDIT_MEMO items
app_content = app_content.replace('"施罗德中国动力": {', '"路博迈中国动力股票C": {')
app_content = app_content.replace('"财通优选": {', '"财通周期优选混合C": {')
app_content = app_content.replace('"泰康新锐": {', '"华安品质甄选混合A": {')
app_content = app_content.replace('"摩根均衡": {', '"摩根均衡精选混合A": {')

fund_codes_map = """FUND_CODES_MAP = {
    '财通周期优选混合C (025547)': '025547',
    '财通科技创新混合C (008984)': '008984',
    '路博迈中国动力股票C (020237)': '020237',
    '摩根均衡精选混合A (021273)': '021273',
    '华安品质甄选混合A (013680)': '013680'
}"""
app_content = re.sub(r'FUND_CODES_MAP = \{[\s\S]*?\}', fund_codes_map, app_content)

fund_aliases = """FUND_ALIASES = {
                    "财通周期优选混合C (025547)": "财通周期",
                    "财通科技创新混合C (008984)": "财通科技",
                    "路博迈中国动力股票C (020237)": "路博迈",
                    "摩根均衡精选混合A (021273)": "摩根均衡",
                    "华安品质甄选混合A (013680)": "华安品质"
                }"""
app_content = re.sub(r'FUND_ALIASES = \{[\s\S]*?\}', fund_aliases, app_content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_content)

# Update nightly_check.py
with open('nightly_check.py', 'r', encoding='utf-8') as f:
    nightly_content = f.read()

nightly_fund_codes = """FUND_CODES_MAP = {
    '财通周期优选混合C (025547)': '025547',
    '财通科技创新混合C (008984)': '008984',
    '路博迈中国动力股票C (020237)': '020237',
    '摩根均衡精选混合A (021273)': '021273',
    '华安品质甄选混合A (013680)': '013680'
}"""
nightly_content = re.sub(r'FUND_CODES_MAP = \{[\s\S]*?\}', nightly_fund_codes, nightly_content)

with open('nightly_check.py', 'w', encoding='utf-8') as f:
    f.write(nightly_content)

print("Updated app.py and nightly_check.py")
