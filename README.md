<div align="center">

# 🔥 TrendPulse

**多平台热点聚合AI分析工具**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](docker/)

[简体中文](#简体中文) | [繁體中文](#繁體中文) | [English](#english)

</div>

---

## 简体中文

### 🎉 项目介绍

**TrendPulse** 是一个轻量级多平台热点聚合与AI智能分析工具，帮助用户实时监控各大平台热点，通过AI进行深度分析，并自动推送重要信息。

**灵感来源**：受 GitHub Trending 项目 [TrendRadar](https://github.com/sansan0/TrendRadar) 启发，我们进行了**独立自研开发**，增加了更多中文平台支持、优化了推送机制、增强了可视化界面，打造更适合中文用户的热点监控工具。

### ✨ 核心特性

- 🔥 **多平台热点聚合** - 支持知乎、微博、B站、GitHub、HackerNews等平台
- 🤖 **AI智能分析** - 趋势追踪、情感分析、相似检测、关键词提取
- 📢 **多渠道推送** - 企业微信、钉钉、Telegram、邮件、Webhook
- 🌐 **Web管理面板** - 可视化配置、数据分析、历史记录
- ⏰ **定时任务** - 支持Cron表达式，灵活配置监控频率
- 🐳 **一键部署** - Docker Compose一键启动

### 🚀 快速开始

#### 环境要求

- Python 3.9+
- SQLite（内置，无需额外安装）
- OpenAI API Key（用于AI分析，可选）

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/gitstq/TrendPulse.git
cd TrendPulse

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化配置
cp config.yaml.example config.yaml

# 4. 编辑配置文件
vim config.yaml
# 配置你的 AI API Key 和通知渠道

# 5. 启动应用
python start.py
```

#### Docker 部署

```bash
# 1. 克隆仓库
git clone https://github.com/gitstq/TrendPulse.git
cd TrendPulse

# 2. 复制并编辑配置
cp config.yaml.example config.yaml
vim config.yaml

# 3. 启动容器
cd docker
docker-compose up -d

# 4. 访问应用
# 打开浏览器访问 http://localhost:8080
```

### 📖 详细使用指南

#### 配置说明

编辑 `config.yaml` 文件：

```yaml
# AI分析配置
ai:
  provider: "openai"  # 可选: openai, claude
  api_key: "your-api-key-here"
  model: "gpt-3.5-turbo"

# 通知配置
notifiers:
  wechat:
    enabled: true
    webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key"
  
  dingtalk:
    enabled: true
    webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=your-token"
```

#### Web界面功能

- 📊 **仪表盘** - 实时统计数据、最近热点
- 🔥 **热点列表** - 查看所有热点、筛选排序
- ⚙️ **设置** - 配置管理、系统状态

### 💡 设计思路与迭代规划

#### 技术选型

- **FastAPI** - 高性能异步Web框架
- **SQLAlchemy** - ORM数据库操作
- **APScheduler** - 定时任务调度
- **Jinja2** - 模板引擎

#### 后续功能计划

- [ ] 更多平台支持（抖音、小红书等）
- [ ] 数据导出功能
- [ ] 热点趋势图表
- [ ] 自定义AI分析模板
- [ ] 多用户支持

### 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 📄 开源协议

本项目采用 [MIT](LICENSE) 协议开源。

---

## 繁體中文

### 🎉 專案介紹

**TrendPulse** 是一個輕量級多平台熱點聚合與AI智能分析工具，幫助用戶實時監控各大平台熱點，透過AI進行深度分析，並自動推送重要資訊。

### ✨ 核心特性

- 🔥 **多平台熱點聚合** - 支援知乎、微博、B站、GitHub、HackerNews等平台
- 🤖 **AI智能分析** - 趨勢追蹤、情感分析、相似檢測、關鍵詞提取
- 📢 **多渠道推送** - 企業微信、釘釘、Telegram、郵件、Webhook
- 🌐 **Web管理面板** - 視覺化配置、數據分析、歷史記錄
- ⏰ **定時任務** - 支援Cron表達式，靈活配置監控頻率
- 🐳 **一鍵部署** - Docker Compose一鍵啟動

### 🚀 快速開始

```bash
# 安裝依賴
pip install -r requirements.txt

# 初始化配置
cp config.yaml.example config.yaml

# 編輯配置並啟動
python start.py
```

### 📄 開源協議

[MIT](LICENSE) 協議

---

## English

### 🎉 Introduction

**TrendPulse** is a lightweight multi-platform trending topics aggregator with AI-powered analysis. It helps users monitor hot topics across various platforms in real-time, perform deep analysis using AI, and automatically push important information.

### ✨ Key Features

- 🔥 **Multi-platform Aggregation** - Supports Zhihu, Weibo, Bilibili, GitHub, HackerNews
- 🤖 **AI-Powered Analysis** - Trend tracking, sentiment analysis, keyword extraction
- 📢 **Multi-channel Notifications** - WeChat Work, DingTalk, Telegram, Email, Webhook
- 🌐 **Web Dashboard** - Visual configuration, data analysis, history records
- ⏰ **Scheduled Tasks** - Cron expression support for flexible monitoring
- 🐳 **One-click Deployment** - Docker Compose ready

### 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize configuration
cp config.yaml.example config.yaml

# Edit config and start
python start.py
```

### 📄 License

[MIT](LICENSE) License

---

<div align="center">

Made with ❤️ by [gitstq](https://github.com/gitstq)

</div>
