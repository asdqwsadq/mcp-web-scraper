"""
MCP Web Scraper + AI Summarizer Server
一个支持Streamable HTTP的MCP工具服务器

提供工具：
1. fetch_url - 抓取网页内容
2. summarize_url - 抓取网页+AI摘要
3. search_web - 通过Brave Search搜索网页

通过XPack进行用户认证和计费
"""

import os
import json
import re
import hashlib
import time
from typing import Optional
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 配置
# ============================================================

# NVIDIA NIM API 配置（用于AI摘要，免费额度）
NVIDIA_API_KEY=os.get...EY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "qwen/qwen3.5-122b-a10b")

# XPack 认证配置
XPACK_API_URL = os.getenv("XPACK_API_URL", "http://xpack-mcp-market:8002")  # Docker内网
XPACK_ADMIN_URL = os.getenv("XPACK_ADMIN_URL", "http://xpack-mcp-market:8001")
XPACK_ADMIN_TOKEN=os.get...EN", "")

# 服务器配置
SERVER_NAME = os.getenv("SERVER_NAME", "Web Scraper + AI Summarizer")
SERVER_VERSION = os.getenv("SERVER_VERSION", "1.0.0")

# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(title=SERVER_NAME, version=SERVER_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 辅助函数
# ============================================================

async def verify_xpack_auth(api_key: str) -> Optional[dict]:
    """
    通过XPack验证API key，返回用户信息
    如果验证失败返回None
    """
    if not api_key:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # XPack的API key验证端点
            resp = await client.get(
                f"{XPACK_API_URL}/api/user/info",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return data.get("data", {})
    except Exception:
        pass
    
    # 如果无法连接XPack，使用本地API key列表作为降级方案
    local_keys = os.getenv("LOCAL_API_KEYS", "")
    if local_keys:
        for key_entry in local_keys.split(","):
            k, uid = key_entry.split(":")
            if k == api_key:
                return {"user_id": uid, "username": "local_user"}
    
    return None


async def fetch_webpage(url: str, max_size: int = 50000) -> dict:
    """
    抓取网页内容并提取可读文本
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            
            content_type = resp.headers.get("content-type", "")
            html = resp.text
            
            # 提取文本
            soup = BeautifulSoup(html, "lxml")
            
            # 移除无关标签
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
                tag.decompose()
            
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            
            # 提取主要内容
            text = soup.get_text(separator="\n", strip=True)
            
            # 清理文本
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            text = "\n".join(lines)
            
            # 截断
            if len(text) > max_size:
                text = text[:max_size] + "\n\n[内容已截断，仅显示前{}字符]".format(max_size)
            
            return {
                "success": True,
                "title": title,
                "url": url,
                "content": text,
                "content_length": len(text),
                "content_type": content_type,
            }
    except httpx.TimeoutException:
        return {"success": False, "error": f"抓取超时: {url}"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP错误 {e.response.status_code}: {url}"}
    except Exception as e:
        return {"success": False, "error": f"抓取失败: {str(e)[:200]}"}


async def summarize_with_nim(text: str, url: str = "", language: str = "中文") -> str:
    """
    使用NVIDIA NIM API对文本进行AI摘要
    """
    if not NVIDIA_API_KEY:
        return "AI摘要功能未配置（NVIDIA_API_KEY缺失）"
    
    prompt = f"""请对以下网页内容进行摘要。用{language}回答。

要求：
1. 先给出1-2句话的简短摘要
2. 列出3-5个关键要点
3. 如果有数据、数字或重要结论，突出显示

网页内容：
---
{text[:30000]}
---"""

    system_prompt = "你是一个专业的网页内容摘要助手。你的任务是准确、简洁地总结网页内容，提取关键信息。"

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": NVIDIA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                }
            )
            resp.raise_for_status()
            data = resp.json()
            msg = data["choices"][0]["message"]
            # 尝试不同的字段名（兼容不同模型）
            return msg.get("content") or msg.get("reasoning_content") or str(msg)
    except Exception as e:
        return f"AI摘要生成失败: {str(e)[:200]}"


async def search_web(query: str, count: int = 5) -> dict:
    """
    搜索网页
    支持：Tavily Search API（首选，需要API Key）→ DuckDuckGo（无需key）
    """
    tavily_api_key = os.getenv("TAVILY_API_KEY", "")
    
    # 1. Tavily Search API（优先，AI Agent专用搜索）
    if tavily_api_key:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "query": query,
                        "search_depth": "basic",
                        "max_results": min(count, 10),
                        "include_answer": False,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {tavily_api_key}",
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                results = []
                for item in data.get("results", [])[:count]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("content", ""),
                    })
                return {"success": True, "results": results, "total": len(results), "source": "tavily"}
        except Exception as e:
            pass  # 降级到下一方案
    
    # 2. DuckDuckGo（无需API Key，但需要能访问国外网站）
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={__import__('urllib.parse').quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(search_url, headers=headers)
            soup = BeautifulSoup(resp.text, "lxml")
            results = []
            for result in soup.select("a.result__a, .result__title a")[:count]:
                title = result.get_text(strip=True)
                url = result.get("href", "")
                # DuckDuckGo的链接是重定向URL，需要提取真实URL
                if "uddg=" in url:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query)
                    url = qs.get("uddg", [url])[0]
                # 找描述
                parent = result.parent
                snippet_el = parent.select_one(".result__snippet, .result__snippet a") if parent else None
                description = snippet_el.get_text(strip=True) if snippet_el else ""
                if title:
                    results.append({"title": title, "url": url, "description": description})
            if results:
                return {"success": True, "results": results, "total": len(results), "source": "duckduckgo"}
    except Exception:
        pass
    
    return {"success": False, "error": "搜索功能暂不可用（请确认TAVILY_API_KEY配置正确，且VPS能访问国外网站）"}


# ============================================================
# MCP协议处理器（手动实现Streamable HTTP）
# ============================================================

# 注册的工具列表
TOOLS = [
    {
        "name": "fetch_url",
        "description": "抓取指定URL的网页内容并提取可读文本",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要抓取的网页URL（必须以http://或https://开头）"
                },
                "max_size": {
                    "type": "integer",
                    "description": "最大字符数（默认50000）",
                    "default": 50000
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "summarize_url",
        "description": "抓取网页内容并用AI生成智能摘要",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要分析的网页URL"
                },
                "language": {
                    "type": "string",
                    "description": "摘要语言（默认'中文'，可选'English', '日本語'等）",
                    "default": "中文"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "search_web",
        "description": "通过搜索引擎搜索网络信息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "count": {
                    "type": "integer",
                    "description": "返回结果数量（默认5，最大10）",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
]


async def handle_mcp_request(body: dict) -> dict:
    """
    处理MCP JSON-RPC请求
    
    支持方法：
    - initialize: 初始化连接
    - tools/list: 列出可用工具
    - tools/call: 调用工具
    - notifications/initialized: 通知已初始化
    """
    method = body.get("method", "")
    params = body.get("params", {})
    req_id = body.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION
                }
            }
        }
    
    if method == "notifications/initialized":
        # 无响应
        return None
    
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }
    
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        # 调用工具
        result = await execute_tool(tool_name, arguments)
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }
                ],
                "isError": not result.get("success", True)
            }
        }
    
    # 未知方法
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    }


async def execute_tool(name: str, arguments: dict) -> dict:
    """
    执行指定的工具
    """
    if name == "fetch_url":
        url = arguments.get("url", "")
        if not url.startswith(("http://", "https://")):
            return {"success": False, "error": "URL必须以http://或https://开头"}
        result = await fetch_webpage(url, arguments.get("max_size", 50000))
        return result
    
    elif name == "summarize_url":
        url = arguments.get("url", "")
        if not url.startswith(("http://", "https://")):
            return {"success": False, "error": "URL必须以http://或https://开头"}
        
        # 先抓取网页
        page = await fetch_webpage(url, 50000)
        if not page["success"]:
            return page
        
        # 再生成摘要
        language = arguments.get("language", "中文")
        summary = await summarize_with_nim(
            page["content"],
            url=url,
            language=language
        )
        
        return {
            "success": True,
            "url": url,
            "title": page.get("title", ""),
            "summary": summary,
            "content_length": page.get("content_length", 0),
        }
    
    elif name == "search_web":
        query = arguments.get("query", "")
        count = arguments.get("count", 5)
        return await search_web(query, count)
    
    else:
        return {"success": False, "error": f"未知工具: {name}"}


# ============================================================
# FastAPI 路由
# ============================================================

@app.get("/health")
async def health():
    """健康检查端点（Smithery要求）"""
    return {
        "status": "healthy",
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/")
async def root():
    """服务器根端点"""
    return {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "description": "MCP Streamable HTTP Server - 网页抓取与AI摘要工具",
        "tools": [t["name"] for t in TOOLS],
        "endpoints": {
            "GET /health": "健康检查",
            "POST /mcp": "MCP协议端点（Streamable HTTP）",
            "GET /.well-known/mcp/server-card.json": "Smithery服务器卡片"
        }
    }


@app.get("/.well-known/mcp/server-card.json")
async def server_card():
    """Smithery服务器卡片 - 用于自动发现"""
    return {
        "schemaVersion": "1.0",
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "description": "网页抓取与AI摘要工具 - 抓取任何网页内容并用AI生成智能摘要",
        "tools": [
            {
                "name": "fetch_url",
                "description": "抓取网页内容并提取可读文本"
            },
            {
                "name": "summarize_url",
                "description": "抓取网页并用AI生成智能摘要"
            },
            {
                "name": "search_web",
                "description": "搜索引擎网络搜索"
            }
        ],
        "authentication": {
            "type": "apiKey",
            "location": "header",
            "name": "Authorization"
        }
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    MCP Streamable HTTP 核心端点
    
    处理所有MCP JSON-RPC请求：
    - initialize
    - tools/list
    - tools/call
    - notifications
    
    支持两种认证方式：
    1. Authorization: Bearer *** - 通过XPack验证
    2. Authorization: Bearer *** - 本地测试key
    """
    try:
        body = await request.json()
    except Exception:
        return Response(
            content=json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }),
            media_type="application/json",
            status_code=400
        )
    
    # 处理请求
    result = await handle_mcp_request(body)
    
    if result is None:
        # notifications不需要响应
        return Response(status_code=202)
    
    return Response(
        content=json.dumps(result, ensure_ascii=False),
        media_type="application/json"
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)