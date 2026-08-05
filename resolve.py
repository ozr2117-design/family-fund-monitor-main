import requests
names = ['博迁新材', '中化国际', '中国稀土', '中稀有色', '海亮股份', '厦门钨业', '圣泉集团', '呈和科技', '东岳集团', '国瓷材料', '三祥新材',
         '中际旭创', '新易盛', '太辰光', '瑞可达', '博创科技', '长芯博创', '优迅股份', '优迅医学', '仕佳光子', '源杰科技', '天孚通信', '长飞光纤光缆', '长飞光纤',
         '桐昆股份', '新凤鸣', '博源化工', '远兴能源', '万华化学', '天华新能', '国城矿业', '新和成', '羚锐制药', '宁德时代', '大中矿业']
res = {}
for name in names:
    r = requests.get(f'https://suggest3.sinajs.cn/suggest/type=&key={name}&name=')
    if r.status_code == 200 and '\"\"' not in r.text:
        try:
            parts = r.text.split('\"')[1].split(';')
            if parts and parts[0]:
                code = parts[0].split(',')[3]
                res[name] = code
        except: pass
print(res)
