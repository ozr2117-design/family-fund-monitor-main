# Family Wealth 💰 基金监测看板

这是一个基于 **Streamlit** 的个人基金资产监测与管理系统。它能够通过底层持仓股票的实时数据，估算基金当天的实时净值与盈亏，并结合历史净值数据提供买卖信号参考。

## ✨ 主要功能

*   **📊 实时估值**: 基于基金持仓的前十大重仓股实时涨跌幅，动态估算当日基金净值。
*   **📈 趋势分析**: 自动抓取并更新基金历史净值，展示“连涨/连跌”趋势及昨日盈亏。
*   **🎯 交易信号**:
    *   **买入信号**: 当跌幅超过基准指数一定比例（超跌错杀）时提示。
    *   **止盈信号**: 当涨幅超过基准指数一定比例（短期过热）时提示。
*   **🧘 禅模式 (Zen Mode)**: 一键隐藏敏感金额，只关注涨跌幅百分比，适合在公共场合查看。
*   **☁️ 云端同步**: 使用 **GitHub** 作为轻量级后端数据库，自动保存配置、持仓信息及历史数据，支持多端同步。
*   **📱 移动端友好**: 针对从 iOS/Android 浏览器访问进行了样式优化，提供原生 App 般的体验。
*   **🛠 工具箱**:
    *   **实时看板**: 核心监控页面。
    *   **持仓管理**: 在线调整持仓金额与定投基数。
    *   **收盘存证**: 每日收盘后手动快照保存当日资产状态。
    *   **晚间审计**: 自动校准预估净值与官方公布净值的偏差，优化估算因子。

## 🛠️ 安装与配置

### 1. 环境准备

确保你的电脑上安装了 Python 3.8 或以上版本。

### 2. 克隆项目

```bash
git clone <repository-url>
cd <project-folder>
```

### 3. 安装依赖

使用 `requirements.txt` 安装所需 Python 库：

```bash
pip install -r requirements.txt
```

主要依赖库：
*   `streamlit`: Web 应用框架
*   `requests`: 网络请求
*   `pandas`: 数据处理
*   `PyGithub`: GitHub API 交互

### 4. 🔑 配置 GitHub Token (关键步骤)

本项目使用 GitHub issue 或文件系统存储数据，因此需要配置 GitHub 访问权限。

1.  在项目根目录下创建一个名为 `.streamlit` 的文件夹（如果不存在）。
2.  在 `.streamlit` 文件夹中创建一个名为 `secrets.toml` 的文件。
3.  在 `secrets.toml` 中填入以下内容：

```toml
github_token = "your_github_personal_access_token"
github_username = "your_github_username"
repo_name = "your_repo_name"  # 例如 "username/my-fund-monitor"
```

> **如何获取 GitHub Token?**
> 1. 登录 GitHub，进入 **Settings** -> **Developer settings** -> **Personal access tokens** -> **Tokens (classic)**。
> 2. 点击 **Generate new token**。
> 3. 勾选 `repo` 权限（用于读写仓库文件）。
> 4. 复制生成的 Token 填入 `secrets.toml`。

## 🚀 运行程序

在终端中执行以下命令启动应用：

```bash
streamlit run app.py
```

启动后，浏览器会自动打开 `http://localhost:8501`。如果是在服务器上运行，可以通过该 URL 访问（需配置网络）。

## 📂 文件结构

*   `app.py`: 主程序入口，包含 UI 逻辑和核心业务代码。
*   `funds.json`: 基金配置文件（存储持仓、代码、系数等，会自动同步到 GitHub）。
*   `history.json`: 每日收盘快照历史数据。
*   `nav_history.json`: 基金历史净值缓存数据。
*   `factor_history.json`: 估值因子审计历史。
*   `requirements.txt`: 项目依赖列表。

## 📝 使用指南

1.  **添加/修改基金**: 可以在 `funds.json` 中配置初始基金，或者在界面上的“Settings -> 持仓管理”中调整持仓和定投基数。
2.  **查看信号**: 首页卡片会自动根据实时行情显示 "🎯 机会" 或 "🔥 止盈" 标签。
3.  **晚间维护**: 建议在晚上 10 点后，点击 "Settings -> 晚间审计 -> Start Audit"，系统会根据官方公布的净值自动修正估算因子，提高明日估算的准确度。

---
*Created for personal wealth management.*
