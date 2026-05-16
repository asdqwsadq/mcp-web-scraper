# MCP Web Scraper + AI Summarizer

> 🕸️ 网页抓取与AI智能摘要工具 — 一个 MCP (Model Context Protocol) 工具，抓取任何网页内容并用 AI 生成智能摘要

[![Smithery](https://img.shields.io/badge/Smithery-已上架-success)](https://smithery.ai/server/1364382646/web-scraper-ai-summarizer)
[![MCP.so](https://img.shields.io/badge/MCP.so-已上架-blue)](https://mcp.so/server/web-scraper-ai-summarizer)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 📋 功能

| 工具 | 描述 |
|------|------|
| 🔧 **fetch_url** | 抓取指定 URL 的网页内容，自动提取可读文本（移除导航、脚本、广告等干扰元素） |
| 🤖 **summarize_url** | 抓取网页内容并用 AI 生成智能摘要（支持多语言：中文、English、日本語等） |
| 🔍 **search_web** | 通过搜索引擎搜索网络信息（基于 Tavily Search API，专为 AI Agent 优化） |

## 🚀 快速开始

### 方式一：通过 Smithery 使用（推荐）

直接在支持 MCP 的客户端（如 Cursor、Claude Desktop）中搜索 `web-scraper-ai-summarizer` 安装即可。

### 方式二：自托管部署

```bash
# 1. 克隆仓库
git clone https://github.com/asdqwsadq/mcp-web-scraper.git
cd mcp-web-scraper

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key
# - NVIDIA_API_KEY: AI摘要（免费，注册 https://build.nvidia.com）
# - TAVILY_API_KEY: 网络搜索（免费，注册 https://tavily.com）

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python3 -m uvicorn server:app --host 0.0.0.0 --port 8080
```

### 方式三：Docker 部署

```bash
docker build -t mcp-web-scraper .
docker run -d --name mcp-web-scraper -p 8080:8080 --env-file .env mcp-web-scraper
```

## 🔧 MCP 协议调用示例

### 1. 抓取网页

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "fetch_url",
    "arguments": {
      "url": "https://example.com/article",
      "max_size": 30000
    }
  }
}
```

### 2. AI 摘要

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "summarize_url",
    "arguments": {
      "url": "https://example.com/article",
      "language": "中文"
    }
  }
}
```

### 3. 网络搜索

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_web",
    "arguments": {
      "query": "最新人工智能技术趋势",
      "count": 5
    }
  }
}
```

## 🔑 API 密钥配置

| 服务 | 用途 | 免费额度 | 申请地址 |
|------|------|----------|----------|
| 🧠 **NVIDIA NIM** | AI 摘要生成 | 1000 credits（无需信用卡） | https://build.nvidia.com |
| 🔍 **Tavily Search** | 网络搜索 | 1000 次/月 | https://tavily.com |
| 🔐 **XPack**（可选） | 用户认证 & 计费 | 自部署 | 见 XPack 文档 |

## 📦 技术架构

```
┌─────────────┐     HTTP/MCP      ┌──────────────────┐
│   MCP 客户端  │ ◄─────────────►  │  MCP HTTP Server  │
│ (Cursor/Cline)│                  │  (FastAPI + MCP)  │
└─────────────┘                    └────────┬─────────┘
                                            │
                    ┌───────────────────────┼───────────────────┐
                    │                       │                   │
                    ▼                       ▼                   ▼
            ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
            │  NVIDIA NIM  │     │ Tavily Search│     │  XPack Auth  │
            │  (AI摘要)     │     │  (网络搜索)   │     │  (计费)       │
            └──────────────┘     └──────────────┘     └──────────────┘
```

## 🛠️ 开发

```bash
# 启动开发服务器（热重载）
uvicorn server:app --host 0.0.0.0 --port 8080 --reload

# MCP 协议测试
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## 📄 协议

MIT License
