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

### 快速开始

#### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

#### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写：

```bash
# OZON 账号配置
ozon_username="your_qq@qq.com"
ozon_login_url="https://sso.ozon.ru/auth/ozonid?localization_language_code=zh-Hans"

# QQ 邮箱授权码（16位）- 获取方式见下方
qq_imap_auth_code="your_16_digit_auth_code"

# Chrome Profile 路径（可选，默认使用 ./chrome-profile/）
chrome_profile_path="./chrome-profile/"
```

#### 3. 获取 QQ 邮箱授权码

1. 登录 [mail.qq.com](https://mail.qq.com)
2. 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
3. 开启 IMAP/SMTP 服务，获取 16 位授权码

#### 4. 运行 MCP Server

```bash
cd src
python -m ozon_mcp.server
```

或在 Claude Code 中添加 `mcp.json` 配置。

### 使用方法

#### 命令行参数

```json
{
  "command": "login-with-email-code",
  "timeout": 120
}
```

```json
{
  "command": "get-marketing-actions",
  "page": 1,
  "page_size": 20,
  "all_pages": false
}
```

### 项目结构

```
ozon-mcp/
├── src/ozon_mcp/          # 核心代码
│   ├── server.py          # MCP Server 入口
│   ├── browser.py         # Playwright 浏览器管理
│   ├── mail.py            # QQ 邮箱 IMAP 操作
│   └── selectors.py       # OZON 页面选择器
├── tests/                 # 测试代码
├── requirements.txt       # 依赖
├── pyproject.toml         # 项目配置
└── mcp.json               # MCP 配置示例
```

### 开发

```bash
# 运行测试
pytest tests/ -v

# 安装开发依赖
pip install -e ".[dev]"
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

### Quick Start

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and configure your credentials.

Get QQ Mail auth code from: mail.qq.com → Settings → Account → IMAP/SMTP service

### License

MIT License - see [LICENSE](LICENSE) file