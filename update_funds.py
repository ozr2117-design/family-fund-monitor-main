import json

with open('funds.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Rename and update values
if "财通优选C (金梓才/AI)" in data:
    data["财通周期优选混合C (025547)"] = data.pop("财通优选C (金梓才/AI)")
    data["财通周期优选混合C (025547)"]["holding_value"] = 69179.98

if "新财通 (科技创新混合C)" in data:
    data["财通科技创新混合C (008984)"] = data.pop("新财通 (科技创新混合C)")
    data["财通科技创新混合C (008984)"]["holding_value"] = 14186.41

if "施罗德中国动力C (020237)" in data:
    data["路博迈中国动力股票C (020237)"] = data.pop("施罗德中国动力C (020237)")
data["路博迈中国动力股票C (020237)"]["holding_value"] = 88136.56

if "摩根均衡C (梁鹏/周期)" in data:
    data["摩根均衡精选混合A (021273)"] = data.pop("摩根均衡C (梁鹏/周期)")
data["摩根均衡精选混合A (021273)"]["holding_value"] = 283334.60

if "公募50私人定制 (进取型)" in data:
    data["公募50私人定制 (进取型)"]["holding_value"] = 0.0

if "泰康新锐C (韩庆/成长)" in data:
    data["泰康新锐C (韩庆/成长)"]["holding_value"] = 0.0

# Add new fund
data["华安品质甄选混合A (013680)"] = {
    "factor": 1.0,
    "holding_value": 75931.91,
    "holdings": [
        { "code": "sh688359", "name": "三孚新科", "weight": 5.0 },
        { "code": "sh600869", "name": "远东股份", "weight": 4.5 },
        { "code": "sh688981", "name": "中芯国际", "weight": 4.0 },
        { "code": "sz300308", "name": "中际旭创", "weight": 4.0 },
        { "code": "sz300835", "name": "龙磁科技", "weight": 3.5 },
        { "code": "sh603950", "name": "长源东谷", "weight": 3.5 },
        { "code": "sz301511", "name": "德福科技", "weight": 3.0 },
        { "code": "sh688256", "name": "寒武纪", "weight": 3.0 },
        { "code": "sz000519", "name": "中兵红箭", "weight": 3.0 },
        { "code": "sh605589", "name": "圣泉集团", "weight": 2.5 }
    ],
    "base_unit": 10000.0
}

with open('funds.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Updated funds.json")
