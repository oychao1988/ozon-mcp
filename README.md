# OZON MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[中文](#中文文档) | [English](#english-docs)

---

## 中文文档

OZON MCP Server 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 的工具，通过 Playwright 实现 OZON 电商后台自动化操作，支持 QQ 邮箱验证码自动读取。

### 功能

- **自动登录** (`login-with-email-code`) - 使用 QQ 邮箱验证码自动登录 OZON 卖家后台
- **价格监控** (`get-marketing-actions`) - 获取营销活动商品价格数据，识别低于最低价格的商品

### 安装

#### 方式一：使用 uv tool 安装（推荐，用于 Claude Code/Cursor）

```bash
# 安装 uv (如果没有)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 全局安装 ozon-mcp 包
uv tool install ozon_mcp

# 安装浏览器
uv run --tool ozon_mcp playwright install chromium
```

#### 方式二：克隆源码开发

```bash
# 克隆项目
git clone https://github.com/oychao1988/ozon-mcp.git
cd ozon-mcp

# 安装 uv (如果没有)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 使用 uv 安装依赖
uv sync
uv run playwright install chromium
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并填写：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# OZON 账号配置（只需要用户名）
ozon_username="your_qq@qq.com"

# QQ 邮箱授权码（16位）- 获取方式见下方
qq_imap_auth_code="your_16_digit_auth_code"

# Chrome Profile 配置（可选）
chrome_profile_source="copy_to_local"
```

#### 获取 QQ 邮箱授权码

1. 登录 [mail.qq.com](https://mail.qq.com)
2. 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
3. 开启 IMAP/SMTP 服务，获取 16 位授权码

### 在 Claude Code 中配置

#### 方式一：使用 uvx 运行（推荐）

```bash
# 添加 MCP Server
claude mcp add ozon --transport stdio -- uvx ozon_mcp
```

或手动编辑 `~/.claude.json`：

```json
{
  "mcpServers": {
    "ozon": {
      "command": "uvx",
      "args": ["ozon_mcp"]
    }
  }
}
```

#### 方式二：使用已安装的 ozon-mcp 命令

```bash
claude mcp add ozon --transport stdio -- ozon-mcp
```

### 在 Cursor 中配置

#### 方式一：使用 uvx（推荐）

```json
{
  "mcpServers": {
    "ozon": {
      "command": "uvx",
      "args": ["ozon_mcp"]
    }
  }
}
```

#### 方式二：使用已安装的 ozon-mcp 命令

```json
{
  "mcpServers": {
    "ozon": {
      "command": "ozon-mcp"
    }
  }
}
```

#### 配置方式

1. 在项目根目录创建 `.mcp.json`
2. 或打开 Cursor 设置 (Cmd+,) → 搜索 "MCP" → "Edit MCP Settings (JSON)"

### 使用方法

#### 工具列表

##### 1. login-with-email-code

自动登录 OZON 卖家后台（使用 QQ 邮箱接收验证码）。

```json
{
  "command": "login-with-email-code"
}
```

##### 2. get-marketing-actions

获取营销活动商品价格数据。

```json
{
  "command": "get-marketing-actions",
  "arguments": {
    "page": 1,
    "page_size": 20,
    "all_pages": false
  }
}
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | number | 1 | 页码（从 1 开始） |
| page_size | number | 20 | 每页产品数量 |
| all_pages | boolean | false | 是否获取所有页面数据 |

### 项目结构

```
ozon-mcp/
├── src/ozon_mcp/          # 核心代码
│   ├── server.py          # MCP Server 入口
│   ├── browser.py         # Playwright 浏览器管理
│   ├── mail.py            # QQ 邮箱 IMAP 操作
│   └── ozon_selectors.py  # OZON 页面选择器
├── tests/                 # 测试代码
├── .env.example           # 环境变量示例
├── pyproject.toml         # 项目配置
└── mcp.json              # MCP 配置示例
```

### 开发

```bash
# 安装开发依赖
uv sync --dev

# 运行测试
uv run pytest tests/ -v

# 手动启动服务器测试
uv run python -m ozon_mcp.server
```

### 注意事项

1. **隐私保护** - 请勿提交 `.env` 文件或 `chrome-profile/` 目录到 Git
2. **验证码** - 确保 QQ 邮箱能正常接收 OZON 的验证码邮件
3. **Chrome Profile** - 首次登录后会保存登录状态，避免重复验证

---

## English Docs

OZON MCP Server is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) based tool for automating OZON seller platform operations using Playwright, with QQ Mail OTP support.

### Features

- **Auto Login** - Login to OZON using QQ Mail verification codes
- **Price Monitoring** - Check marketing action prices and identify underpriced items

### Installation

```bash
git clone https://github.com/oychao1988/ozon-mcp.git
cd ozon-mcp
uv sync
uv run playwright install chromium
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
ozon_username="your_qq@qq.com"
qq_imap_auth_code="your_16_digit_auth_code"
```

Get QQ Mail auth code from: mail.qq.com → Settings → Account → IMAP/SMTP service

### Claude Code Configuration

```bash
claude mcp add ozon --transport stdio -- uvx ozon_mcp.server
```

Or edit `~/.claude.json`:

```json
{
  "mcpServers": {
    "ozon": {
      "command": "uvx",
      "args": ["--directory", "/path/to/ozon-mcp", "ozon_mcp.server"]
    }
  }
}
```

### Cursor Configuration

Edit Cursor MCP settings (Cmd+, → search "MCP" → "Edit MCP Settings"):

```json
{
  "mcpServers": {
    "ozon": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ozon-mcp", "python", "-m", "ozon_mcp.server"],
      "env": {
        "ozon_username": "your_qq@qq.com",
        "qq_imap_auth_code": "your_auth_code"
      }
    }
  }
}
```

### License

MIT License - see [LICENSE](LICENSE) file
