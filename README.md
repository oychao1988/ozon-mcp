# OZON MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/ozon-mcp.svg)](https://badge.fury.io/py/ozon-mcp)

[中文](#中文文档) | [English](#english-docs)

---

## 中文文档

OZON MCP Server 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 的工具，通过 Playwright 实现 OZON 电商后台自动化操作，支持 QQ 邮箱验证码自动读取。

### 功能

- **自动登录** (`login-with-email-code`) - 使用 QQ 邮箱验证码自动登录 OZON 卖家后台
- **价格监控** (`get-marketing-actions`) - 获取营销活动商品价格数据，识别低于最低价格的商品

### 安装

#### 方式一：从 PyPI 安装（推荐）

```bash
# 安装 uv (如果没有)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 全局安装 ozon-mcp
uv tool install ozon-mcp

# 安装浏览器
uv tool run ozon-mcp playwright install chromium
```

#### 方式二：克隆源码开发

```bash
# 克隆项目
git clone https://github.com/oychao1988/ozon-mcp.git
cd ozon-mcp

# 安装 uv (如果没有)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
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

#### 方式一：使用已安装的 ozon-mcp 命令（推荐）

```bash
claude mcp add ozon --transport stdio -- ozon-mcp
```

#### 方式二：使用 uvx 远程运行

```bash
claude mcp add ozon --transport stdio -- uvx ozon-mcp
```

### 在 Cursor 中配置

在 `.mcp.json` 或 Cursor MCP 设置中添加：

```json
{
  "mcpServers": {
    "ozon": {
      "command": "ozon-mcp"
    }
  }
}
```

或使用 uvx：

```json
{
  "mcpServers": {
    "ozon": {
      "command": "uvx",
      "args": ["ozon-mcp"]
    }
  }
}
```

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

### 发布到 PyPI

```bash
# 构建包
uv build

# 发布到 PyPI（需要账号）
uv publish

# 或发布到 TestPyPI 测试
uv publish --repository testpypi
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
# Install via uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install ozon-mcp

# Install browser
uv tool run ozon-mcp playwright install chromium
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
claude mcp add ozon --transport stdio -- ozon-mcp
```

### Cursor Configuration

Add to `.mcp.json` or Cursor MCP settings:

```json
{
  "mcpServers": {
    "ozon": {
      "command": "ozon-mcp"
    }
  }
}
```

### License

MIT License - see [LICENSE](LICENSE) file
