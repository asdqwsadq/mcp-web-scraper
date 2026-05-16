# MCP Web Scraper + AI Summarizer

> 🕸️ 网页抓取与AI智能摘要工具 — 一个支持 **Streamable HTTP** 的 MCP 工具服务器

[![Smithery](https://img.shields.io/badge/Smithery-已上架-green)](https://smithery.ai/server/@asdqwsadq/mcp-web-scraper)
[![MCP.so](https://img.shields.io/badge/MCP.so-已上架-blue)](https://mcp.so/server/mcp-web-scraper)

## 📋 功能

| 工具 | 描述 |
|------|------|
| 🔧 **fetch_url** | 抓取指定URL的网页内容，自动提取可读文本（移除导航、脚本、广告等干扰） |
| 🔧 **summarize_url** | 抓取网页内容并用 AI 生成智能摘要（支持多语言） |
| 🔧 **search_web** | 通过搜索引擎搜索网络信息（基于 Tavily Search API） |

## 🚀 快速开始

### 方法一：通过 Smithery 使用（推荐）

在 Cursor/Claude Desktop 等 MCP 客户端中配置：

```json
{
  "mcpServers": {
    "web-scraper": {
      "url": "https://smithery.ai/server/@asdqwsadq/mcp-web-scraper"
    }
  }
}
```

### 方法二：自托管部署

```bash
# 1. 克隆仓库
git clone https://github.com/asdqwsadq/mcp-web-scraper.git
cd mcp-web-scraper

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python3 -m uvicorn server:app --host 0.0.0.0 --port 8080
```

### 方法三：Docker 部署

```bash
docker build -t mcp-web-scraper .
docker run -d --name mcp-web-scraper -p 8080:8080 --env-file .env mcp-web-scraper
```

## 🔧 工具使用示例

### 抓取网页

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

### AI 摘要

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

### 搜索

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_web",
    "arguments": {
      "query": "最新人工智能技术",
      "count": 5
    }
  }
}
```

## 🔑 API 密钥

| 服务 | 用途 | 免费额度 | 申请地址 |
|------|------|----------|----------|
| NVIDIA NIM | AI 摘要生成 | 1000 credits/月 | https://build.nvidia.com |
| Tavily Search | 网络搜索 | 1000 次/月 | https://tavily.com |

## 📄 协议

MIT
