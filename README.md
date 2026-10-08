# 代码审查 Agent

基于 LLM 的代码审查助手。上传文件或粘贴代码，Agent 自主调用工具进行静态分析和深度审查，输出结构化的审查报告。

支持 **命令行** 和 **Web 界面** 两种交互方式。

---

## 功能特性

- 📂 **文件读取** — 拖拽上传或粘贴代码，支持多种编程语言
- 🔍 **静态分析** — 自动检测硬编码敏感信息（密码、密钥、Token、IP、邮箱）、统计行数、提取函数列表
- ⚡ **代码执行** — 沙箱环境运行代码片段，带超时保护和危险操作拦截
- 🤖 **Agent 自主推理** — LLM 自主决定调用哪些工具，多步分析后给出结论
- 💬 **对话记忆** — 保存历史上下文，支持多轮追问
- 🎨 **Web 界面** — 新野兽派风格左右分栏，左侧输入右侧报告，SSE 实时推送
- 📤 **多格式导出** — 支持复制 / Markdown / PDF / Word 四种报告导出方式
- 🧪 **单元测试** — 覆盖工具、Agent 循环、记忆管理等 9 个测试用例

---

## 技术选型

| 层级 | 技术 | 选型理由 |
|------|------|---------|
| 后端语言 | Python 3.9+ | 生态丰富，LLM SDK 完善 |
| Web 框架 | Flask | 轻量，SSE 流式推送支持好 |
| LLM | 通义千问（Qwen-Plus） | 国内访问稳定，兼容 OpenAI API 格式 |
| LLM SDK | openai-python | 通义千问兼容模式直接用 |
| 前端框架 | Vue 3（CDN 版） | 无需构建工具，单文件即用 |
| 流式推送 | SSE（Server-Sent Events） | 比 WebSocket 简单，单向推送够用 |
| Markdown 渲染 | marked.js | 轻量，浏览器端解析 |
| 代码分析 | 正则 + Python AST | 无需额外依赖，覆盖基础检测 |
| 代码执行 | subprocess 子进程 | 隔离执行环境，超时可控 |

---

## 环境要求

- Python 3.9 及以上
- 通义千问 API Key（[申请地址](https://bailian.console.aliyun.com/)）
- 现代浏览器（Chrome / Safari / Firefox）

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key：

```
DASHSCOPE_API_KEY=sk-你的key
```

### 3. 运行

**命令行模式：**

```bash
python main.py
```

**Web 界面模式：**

```bash
python app.py
# 浏览器打开 http://127.0.0.1:5000
```

---

## 使用方法

### Web 界面（推荐）

1. 启动后浏览器打开 `http://127.0.0.1:5000`
2. **左侧输入区**：拖拽代码文件到上传区，或直接在文本框粘贴代码
3. 点击 **「开始审查」** 按钮
4. **右侧报告区**：实时显示审查进度和结果
   - 第一步：静态分析（秒级返回）
   - 第二步：LLM 深度审查（几秒到几十秒）
   - 第三步：生成结构化报告
5. 审查完成后可点击右上角 **复制 / MD / PDF / Word** 导出报告

### 命令行

```bash
python main.py
```

常用指令：

| 输入 | 效果 |
|------|------|
| `请审查 sample.py` | Agent 读取文件 → 分析 → 输出审查报告 |
| `执行 print(sum(range(100)))` | Agent 沙箱执行代码，返回结果 |
| （粘贴代码）+ "看看有什么问题" | 直接审查粘贴的代码片段 |
| `clear` | 清空对话记忆 |
| `quit` | 退出程序 |

---

## 项目结构

```
code-review-agent/
├── main.py              # 命令行入口
├── app.py               # Flask Web 后端 + SSE 流式接口
├── agent.py             # Agent 核心循环（推理→工具调用→再推理）
├── memory.py            # 对话记忆管理（带截断保护）
├── prompts.py           # 系统提示词（角色定义 + 工具说明）
├── tools/
│   ├── __init__.py      # 工具导出
│   ├── file_reader.py   # 工具1：文件读取
│   ├── code_analyzer.py # 工具2：静态代码分析
│   └── code_executor.py # 工具3：沙箱代码执行
├── web/
│   └── index.html       # Vue 3 前端界面（新野兽派风格）
├── tests/
│   └── test_agent.py    # 单元测试（9 项）
├── sample.py            # 示例代码（含常见问题，用于演示）
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板
├── .gitignore           # Git 忽略配置
├── README.md            # 项目说明（本文件）
└── Design.md            # 设计文档
```

---

## Web 页面配置

### 启动参数

```bash
python app.py --port 8080        # 指定端口（默认 5000）
python app.py --host 0.0.0.0     # 指定监听地址（默认 127.0.0.1）
```

### API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 返回 Web 页面 |
| `/api/analyze` | POST | 审查代码，SSE 流式返回事件 |
| `/api/upload` | POST | 上传文件，返回文件内容 |
| `/api/status` | GET | 检查 API Key 配置状态 |

### SSE 事件类型

`/api/analyze` 以 SSE 格式推送事件，事件类型：

| 事件类型 | data 字段 | 说明 |
|---------|----------|------|
| `step` | `{step, label}` | 步骤变更通知 |
| `static_analysis` | `{report}` | 静态分析完成 |
| `answer` | `{content}` | LLM 最终回答 |
| `tool_call` | `{name, args}` | Agent 调用工具 |
| `tool_result` | `{result}` | 工具执行结果 |
| `error` | `{message}` | 出错 |
| `done` | `{}` | 全部完成 |

---

## 依赖说明（requirements.txt）

```
openai>=1.12.0       # LLM SDK，通义千问兼容模式
python-dotenv>=1.0.0 # 加载 .env 环境变量
flask>=2.3.0         # Web 框架
```

---

## 测试

```bash
python tests/test_agent.py
```

测试覆盖：
- 工具功能测试（文件读取、静态分析、代码执行）
- Agent 工具调用解析测试
- 记忆管理测试
- Agent 循环 mock 测试（3 种场景）

---

## 许可证

本项目为课程作业。
