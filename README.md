<div align="center">

# 🚀 TrendPulse

**智能热点脉动监控与分析平台**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](docker/)

[简体中文](#简体中文) | [繁體中文](#繁體中文) | [English](#english)

</div>

---

## 简体中文

### 🎉 项目介绍

**TrendPulse** 是一个基于AI的多平台热点聚合、分析与监控平台。它能够自动抓取微博、知乎、百度、B站、头条、抖音等主流平台的热点数据，通过AI进行情感分析和智能摘要，并以美观的可视化界面展示趋势变化。

**灵感来源**: 本项目参考了 [TrendRadar](https://github.com/sansan0/TrendRadar) 的产品逻辑，在此基础上进行了深度优化和功能扩展，新增了AI智能分析、情感倾向分析、历史趋势追踪等差异化功能。

### ✨ 核心特性

- 🔥 **多平台聚合** - 支持微博、知乎、百度、B站、头条、抖音等主流平台
- 💭 **情感分析** - 自动分析热点情感倾向（正面/负面/中性）
- 🤖 **AI智能摘要** - 基于大语言模型自动生成热点摘要
- 📊 **趋势可视化** - 丰富的图表展示，包括热度趋势、平台分布、情感分布
- 🔌 **RESTful API** - 完整的API接口，支持第三方集成
- 🔔 **智能推送** - 支持企业微信、飞书、钉钉、Telegram等多渠道推送
- 🐳 **Docker支持** - 一键Docker部署，开箱即用
- ⚡ **自动化爬虫** - GitHub Actions定时自动爬取热点数据

### 🚀 快速开始

#### 环境要求

- Python 3.10+
- 2GB+ RAM
- 可选: OpenAI/Claude API密钥（用于AI摘要）

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/gitstq/TrendPulse.git
cd TrendPulse

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python main.py --init-db

# 5. 启动服务
python main.py --web
```

访问 http://localhost:8000 查看Web界面

#### Docker部署

```bash
# 使用Docker Compose
cd docker
docker-compose up -d

# 或使用Docker直接运行
docker build -t trendpulse -f docker/Dockerfile .
docker run -d -p 8000:8000 trendpulse
```

### 📖 详细使用指南

#### 配置说明

编辑 `config/config.yaml` 文件：

```yaml
# 关键词配置
keywords:
  focus:
    - "人工智能"
    - "AI"
    - "大模型"

# AI分析配置
ai:
  provider: "openai"  # 或 anthropic
  api_key: "${AI_API_KEY}"
  model: "gpt-3.5-turbo"

# 通知配置
notifications:
  wecom:
    enabled: true
    webhook_url: "${WECOM_WEBHOOK_URL}"
```

#### API接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/trends` | GET | 获取热点列表 |
| `/api/trends/hot` | GET | 获取最热热点 |
| `/api/stats` | GET | 获取统计数据 |
| `/api/dashboard` | GET | 获取仪表盘数据 |
| `/api/crawl` | POST | 手动触发爬虫 |

完整API文档启动后访问: http://localhost:8000/docs

### 💡 设计思路

#### 技术选型原因

- **FastAPI**: 高性能异步Web框架，自动生成API文档
- **SQLAlchemy**: 强大的ORM，支持多种数据库
- **SnowNLP**: 轻量级中文情感分析库
- **TailwindCSS**: 现代化CSS框架，快速构建美观界面
- **Chart.js**: 简单易用的图表库

#### 后续迭代计划

- [ ] 支持更多平台（小红书、快手等）
- [ ] 热点预警功能
- [ ] 用户自定义仪表盘
- [ ] 热点关联分析
- [ ] 移动端App

### 📦 打包与部署

#### 本地开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
pytest tests/

# 代码格式化
black src/
```

#### 生产部署

```bash
# 使用Gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api:app
```

### 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某个特性'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 📄 开源协议

本项目基于 [MIT](LICENSE) 协议开源。

---

## 繁體中文

### 🎉 專案介紹

**TrendPulse** 是一個基於AI的多平台熱點聚合、分析與監控平台。它能夠自動抓取微博、知乎、百度、B站、頭條、抖音等主流平台的熱點數據，通過AI進行情感分析和智能摘要，並以美觀的可視化界面展示趨勢變化。

### ✨ 核心特性

- 🔥 **多平台聚合** - 支援微博、知乎、百度、B站、頭條、抖音等主流平台
- 💭 **情感分析** - 自動分析熱點情感傾向（正面/負面/中性）
- 🤖 **AI智能摘要** - 基於大語言模型自動生成熱點摘要
- 📊 **趨勢可視化** - 豐富的圖表展示，包括熱度趨勢、平台分布、情感分布
- 🔌 **RESTful API** - 完整的API接口，支援第三方集成
- 🔔 **智能推送** - 支援企業微信、飛書、釘釘、Telegram等多渠道推送
- 🐳 **Docker支援** - 一鍵Docker部署，開箱即用

### 🚀 快速開始

```bash
# 克隆倉庫
git clone https://github.com/gitstq/TrendPulse.git
cd TrendPulse

# 安裝依賴
pip install -r requirements.txt

# 初始化數據庫
python main.py --init-db

# 啟動服務
python main.py --web
```

訪問 http://localhost:8000 查看Web界面

### 📄 開源協議

本專案基於 [MIT](LICENSE) 協議開源。

---

## English

### 🎉 Introduction

**TrendPulse** is an AI-powered multi-platform trending topics aggregation, analysis and monitoring platform. It automatically crawls trending data from major platforms including Weibo, Zhihu, Baidu, Bilibili, Toutiao, and Douyin, performs sentiment analysis and AI-powered summarization, and displays trend changes through beautiful visualizations.

### ✨ Key Features

- 🔥 **Multi-Platform Aggregation** - Supports Weibo, Zhihu, Baidu, Bilibili, Toutiao, Douyin
- 💭 **Sentiment Analysis** - Automatic sentiment classification (Positive/Negative/Neutral)
- 🤖 **AI-Powered Summarization** - Generate topic summaries using LLM
- 📊 **Trend Visualization** - Rich charts including trend lines, platform distribution, sentiment analysis
- 🔌 **RESTful API** - Complete API for third-party integration
- 🔔 **Smart Notifications** - Support WeCom, Feishu, DingTalk, Telegram
- 🐳 **Docker Support** - One-click Docker deployment
- ⚡ **Automated Crawling** - GitHub Actions scheduled crawling

### 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/gitstq/TrendPulse.git
cd TrendPulse

# Install dependencies
pip install -r requirements.txt

# Initialize database
python main.py --init-db

# Start server
python main.py --web
```

Visit http://localhost:8000 to access the web interface

### 📄 License

This project is licensed under the [MIT](LICENSE) License.

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by TrendPulse Team

</div>
