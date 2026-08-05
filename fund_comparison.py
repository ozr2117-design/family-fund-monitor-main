# 依赖安装命令（请使用清华源）：
# pip install akshare pandas matplotlib -i https://pypi.tuna.tsinghua.edu.cn/simple

import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import platform
import warnings

warnings.filterwarnings('ignore')

# ----------------- 1. 中文字体和画图基础设置 -----------------
system = platform.system()
if system == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
elif system == 'Darwin':
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
else:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False  

def main():
    # ----------------- 2. 标的与参数配置 -----------------
    active_code = "021528"
    etf1_code = "515880"
    etf2_code = "516630"
    
    # 扩大数据获取范围以确保前置基准足够
    fetch_start = "2025-03-01"
    fetch_end = "2026-03-18"
    
    print(">>> 正在拉取数据，请稍候...")
    
    # ----------------- 3. 分别拉取数据并转为 DataFrame -----------------
    # 主动基金
    print(f"提取主动基金 {active_code} 数据...")
    df_active = pd.DataFrame()
    try:
        df_active_raw = ak.fund_open_fund_info_em(symbol=active_code, indicator="累计净值走势")
        if not df_active_raw.empty:
            df_active_raw['date'] = pd.to_datetime(df_active_raw['净值日期']).dt.normalize()
            df_active = df_active_raw[['date', '累计净值']].rename(columns={'累计净值': '021528_财通成长优选混合C'})
            df_active['021528_财通成长优选混合C'] = df_active['021528_财通成长优选混合C'].astype(float)
            df_active.drop_duplicates(subset=['date'], inplace=True)
    except Exception as e:
        print(f"获取主动基金数据失败: {e}")

    # ETF1 (利用累计净值规避行情接口前复权不准确的Bug)
    print(f"提取 ETF {etf1_code} 数据...")
    df_etf1 = pd.DataFrame()
    try:
        # ETF 本质也是公募基金，直接调取累计净值能绝对屏蔽所有分红跳空影响，且规避了 akshare 的行情 qfq 接口偶发失效的 Bug
        df_etf1_raw = ak.fund_open_fund_info_em(symbol=etf1_code, indicator="累计净值走势")
        if not df_etf1_raw.empty:
            df_etf1_raw['date'] = pd.to_datetime(df_etf1_raw['净值日期']).dt.normalize()
            df_etf1 = df_etf1_raw[['date', '累计净值']].rename(columns={'累计净值': '515880_通信设备ETF'})
            df_etf1['515880_通信设备ETF'] = df_etf1['515880_通信设备ETF'].astype(float)
            df_etf1.drop_duplicates(subset=['date'], inplace=True)
    except Exception as e:
        print(f"获取 ETF1 数据失败: {e}")

    # ETF2 (利用累计净值规避行情接口前复权不准确的Bug)
    print(f"提取 ETF {etf2_code} 数据...")
    df_etf2 = pd.DataFrame()
    try:
        df_etf2_raw = ak.fund_open_fund_info_em(symbol=etf2_code, indicator="累计净值走势")
        if not df_etf2_raw.empty:
            df_etf2_raw['date'] = pd.to_datetime(df_etf2_raw['净值日期']).dt.normalize()
            df_etf2 = df_etf2_raw[['date', '累计净值']].rename(columns={'累计净值': '516630_云计算ETF'})
            df_etf2['516630_云计算ETF'] = df_etf2['516630_云计算ETF'].astype(float)
            df_etf2.drop_duplicates(subset=['date'], inplace=True)
    except Exception as e:
        print(f"获取 ETF2 数据失败: {e}")

    # ----------------- 4. 强制基础合并 (Outer Join) -----------------
    print(">>> 正在进行 outer join 强制合并数据对齐...")
    dfs = [df for df in [df_active, df_etf1, df_etf2] if not df.empty]
    
    if not dfs:
        print("所有数据均获取失败，请检查网络接口。")
        return

    # 按 date 进行 outer merge
    df_all = dfs[0]
    for i in range(1, len(dfs)):
        df_all = pd.merge(df_all, dfs[i], on='date', how='outer')
        
    # 截取所需的大区间
    df_all = df_all[(df_all['date'] >= pd.to_datetime(fetch_start)) & (df_all['date'] <= pd.to_datetime(fetch_end))]
    
    # 将彻底合并完毕的 df 按照 date 排序，并设置为 index
    df_all.sort_values('date', inplace=True)
    df_all.set_index('date', inplace=True)

    # 处理缺失值
    df_all.ffill(inplace=True)
    df_all.bfill(inplace=True)

    # ----------------- 5. 时间段切分与统一归一化 -----------------
    start_1y = pd.to_datetime("2025-03-18")
    start_6m = pd.to_datetime("2025-09-18")
    end_date = pd.to_datetime("2026-03-18")

    # 近一年：2025-03-18 至 2026-03-18
    df_1y = df_all.loc[start_1y:end_date].copy()
    if not df_1y.empty:
        # 统一归一化转换：当前行的每列 / 起点这一行的对应列 - 1
        df_1y_norm = (df_1y / df_1y.iloc[0] - 1) * 100
    else:
        df_1y_norm = pd.DataFrame()

    # 近半年：2025-09-18 至 2026-03-18
    df_6m = df_all.loc[start_6m:end_date].copy()
    if not df_6m.empty:
        df_6m_norm = (df_6m / df_6m.iloc[0] - 1) * 100
    else:
        df_6m_norm = pd.DataFrame()

    # ----------------- 6. 统一绘图 -----------------
    print(">>> 正在生成走势对比图...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    plot_config = {
        '021528_财通成长优选混合C': {'color': '#d62728', 'linewidth': 2.5, 'zorder': 3}, 
        '515880_通信设备ETF': {'color': '#1f77b4', 'linewidth': 1.5, 'zorder': 2},      
        '516630_云计算ETF': {'color': '#2ca02c', 'linewidth': 1.5, 'zorder': 2}       
    }

    # === 左图：近半年 ===
    if not df_6m_norm.empty:
        for col in df_6m_norm.columns:
            # df_6m_norm 每列数据长度必然与 index 一致，绝不会抛出 shape 错误
            ax1.plot(df_6m_norm.index, df_6m_norm[col], label=col, 
                     color=plot_config.get(col, {}).get('color', '#333333'), 
                     linewidth=plot_config.get(col, {}).get('linewidth', 1.5),
                     zorder=plot_config.get(col, {}).get('zorder', 1))
        
        ax1.set_title('近半年累计涨跌幅对比（%）\n(2025-09-18 至 2026-03-18)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('累计涨跌幅 (%)', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend(loc='best', fontsize=10)
        ax1.tick_params(axis='x', rotation=45)
        ax1.axhline(0, color='black', linewidth=1, linestyle='-', alpha=0.5)

    # === 右图：近一年 ===
    if not df_1y_norm.empty:
        for col in df_1y_norm.columns:
            ax2.plot(df_1y_norm.index, df_1y_norm[col], label=col, 
                     color=plot_config.get(col, {}).get('color', '#333333'), 
                     linewidth=plot_config.get(col, {}).get('linewidth', 1.5),
                     zorder=plot_config.get(col, {}).get('zorder', 1))
            
        ax2.set_title('近一年累计涨跌幅对比（%）\n(2025-03-18 至 2026-03-18)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('累计涨跌幅 (%)', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend(loc='best', fontsize=10)
        ax2.tick_params(axis='x', rotation=45)
        ax2.axhline(0, color='black', linewidth=1, linestyle='-', alpha=0.5)

    plt.tight_layout()
    plt.savefig('output_plot.png', dpi=150)
    print(">>> 绘图完成！图片已保存为 output_plot.png")
    plt.show()

if __name__ == "__main__":
    main()
