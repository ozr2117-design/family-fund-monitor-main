import json

funds_data = {
    "财通周期优选混合C (025547)": {
        "factor": 1.0,
        "holding_value": 69179.98,
        "base_unit": 10000.0,
        "holdings": [
            {"code": "sh605376", "name": "博迁新材", "weight": 9.43},
            {"code": "sh600500", "name": "中化国际", "weight": 7.73},
            {"code": "sh600259", "name": "中稀有色", "weight": 7.03},
            {"code": "sz002203", "name": "海亮股份", "weight": 6.86},
            {"code": "sh600549", "name": "厦门钨业", "weight": 5.35},
            {"code": "sh605589", "name": "圣泉集团", "weight": 5.02},
            {"code": "sh688625", "name": "呈和科技", "weight": 4.49},
            {"code": "hk00189", "name": "东岳集团", "weight": 4.43},
            {"code": "sz300285", "name": "国瓷材料", "weight": 4.15},
            {"code": "sh603663", "name": "三祥新材", "weight": 4.07}
        ]
    },
    "财通科技创新混合C (008984)": {
        "factor": 1.0,
        "holding_value": 14186.41,
        "base_unit": 10000.0,
        "holdings": [
            {"code": "sz300308", "name": "中际旭创", "weight": 9.53},
            {"code": "sz300502", "name": "新易盛", "weight": 9.50},
            {"code": "sz300570", "name": "太辰光", "weight": 9.47},
            {"code": "sh688800", "name": "瑞可达", "weight": 8.24},
            {"code": "sz300548", "name": "长芯博创", "weight": 8.23},
            {"code": "sh688807", "name": "优迅股份", "weight": 8.12},
            {"code": "sh688313", "name": "仕佳光子", "weight": 8.09},
            {"code": "sh688498", "name": "源杰科技", "weight": 7.66},
            {"code": "sz300394", "name": "天孚通信", "weight": 7.25},
            {"code": "hk06869", "name": "长飞光纤光缆", "weight": 6.15}
        ]
    },
    "路博迈中国动力股票C (020237)": {
        "factor": 1.0,
        "holding_value": 88136.56,
        "base_unit": 10000.0,
        "holdings": [
            {"code": "sh688498", "name": "源杰科技", "weight": 4.67},
            {"code": "sh688195", "name": "腾景科技", "weight": 4.63},
            {"code": "sh600066", "name": "宇通客车", "weight": 4.52},
            {"code": "sh605117", "name": "德业股份", "weight": 4.36},
            {"code": "sz000338", "name": "潍柴动力", "weight": 4.14},
            {"code": "sz002463", "name": "沪电股份", "weight": 3.82},
            {"code": "sz002028", "name": "思源电气", "weight": 3.77},
            {"code": "sz300274", "name": "阳光电源", "weight": 3.77},
            {"code": "hk01378", "name": "中国宏桥", "weight": 3.73},
            {"code": "sz002812", "name": "恩捷股份", "weight": 3.37}
        ]
    },
    "摩根均衡精选混合A (021273)": {
        "factor": 1.0,
        "holding_value": 283334.60,
        "base_unit": 10000.0,
        "holdings": [
            {"code": "sh601233", "name": "桐昆股份", "weight": 9.08},
            {"code": "sh603225", "name": "新凤鸣", "weight": 8.40},
            {"code": "sz000683", "name": "博源化工", "weight": 5.28},
            {"code": "sh600309", "name": "万华化学", "weight": 4.43},
            {"code": "sz300390", "name": "天华新能", "weight": 3.60},
            {"code": "sz000688", "name": "国城矿业", "weight": 3.23},
            {"code": "sz002001", "name": "新和成", "weight": 3.17},
            {"code": "sh600285", "name": "羚锐制药", "weight": 3.17},
            {"code": "sz300750", "name": "宁德时代", "weight": 3.12},
            {"code": "sz001203", "name": "大中矿业", "weight": 3.06}
        ]
    },
    "华安品质甄选混合A (013680)": {
        "factor": 1.0,
        "holding_value": 75931.91,
        "base_unit": 10000.0,
        "holdings": [
            {"code": "sh688359", "name": "三孚新科", "weight": 5.0},
            {"code": "sh600869", "name": "远东股份", "weight": 4.5},
            {"code": "sh688981", "name": "中芯国际", "weight": 4.0},
            {"code": "sz300308", "name": "中际旭创", "weight": 4.0},
            {"code": "sz300835", "name": "龙磁科技", "weight": 3.5},
            {"code": "sh603950", "name": "长源东谷", "weight": 3.5},
            {"code": "sz301511", "name": "德福科技", "weight": 3.0},
            {"code": "sh688256", "name": "寒武纪", "weight": 3.0},
            {"code": "sz000519", "name": "中兵红箭", "weight": 3.0},
            {"code": "sh605589", "name": "圣泉集团", "weight": 2.5}
        ]
    }
}

with open("funds.json", "w", encoding="utf-8") as f:
    json.dump(funds_data, f, ensure_ascii=False, indent=4)
print("Updated funds.json with latest holdings.")
