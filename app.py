import os
import json
import queue
import threading
import sys
import tempfile

from dotenv import load_dotenv
from flask import Flask, Response, request, send_from_directory, jsonify
from openai import OpenAI

from agent import CodeReviewAgent
from tools import analyze_code

load_dotenv()

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

# 全局 agent（单会话简化版，生产环境用 session）
_agent = None


def get_agent():
    """获取或创建 Agent。"""
    global _agent
    if _agent is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        _agent = CodeReviewAgent(client, model="qwen-plus")
    return _agent


@app.route("/")
def index():
    """首页 — 直接返回静态 HTML，不走模板引擎（避免 Vue 的 {{ }} 和 Jinja2 冲突）。"""
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """审查代码，SSE 流式返回事件。

    请求体：
    {
        "filename": "sample.py",   // 文件名（可选）
        "code": "def foo(): ..."   // 代码内容
    }
    """
    data = request.get_json()
    code = data.get("code", "")
    filename = data.get("filename", "代码片段")
    if not code:
        return {"error": "代码不能为空"}, 400

    event_queue = queue.Queue()

    def event_callback(event_type, event_data):
        event_queue.put({"type": event_type, "data": event_data})

    agent = get_agent()
    agent.event_callback = event_callback

    def run_agent():
        try:
            prompt = (
                f"请审查以下代码（文件名：{filename}），给出结构化的审查报告。\n\n"
                f"```\n{code}\n```"
            )
            agent.run(prompt)
        except Exception as e:
            event_queue.put({"type": "error", "data": {"message": str(e)}})
        finally:
            event_queue.put({"type": "done", "data": {}})

    # 第一步：先推静态分析结果（快速反馈）
    event_queue.put({"type": "step", "data": {"step": 1, "label": "静态分析中..."}})

    # 把代码写到临时文件里跑 analyze_code
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=os.path.splitext(filename)[1] or ".py",
        delete=False, encoding="utf-8"
    )
    tmp.write(code)
    tmp.close()
    static_result = analyze_code(tmp.name)
    os.unlink(tmp.name)

    event_queue.put({
        "type": "static_analysis",
        "data": {"report": static_result},
    })

    # 第二步：LLM 深度审查
    event_queue.put({"type": "step", "data": {"step": 2, "label": "LLM 深度审查中..."}})
    threading.Thread(target=run_agent, daemon=True).start()

    def generate():
        while True:
            event = event_queue.get()
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event["type"] == "done" or event["type"] == "error":
                break

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/upload", methods=["POST"])
def upload():
    """上传文件并返回文件内容。"""
    if "file" not in request.files:
        return {"error": "没有上传文件"}, 400

    f = request.files["file"]
    if not f.filename:
        return {"error": "文件名为空"}, 400

    try:
        content = f.read().decode("utf-8")
    except UnicodeDecodeError:
        return {"error": "文件编码不支持，请上传文本文件"}, 400

    return jsonify({
        "filename": f.filename,
        "code": content,
        "size": len(content),
    })


@app.route("/api/status")
def status():
    """检查 API Key 配置状态。"""
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    return {
        "has_key": bool(api_key) and api_key != "sk-your-api-key-here",
    }


if __name__ == "__main__":
    port = 5000
    host = "127.0.0.1"
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    if "--host" in sys.argv:
        host = sys.argv[sys.argv.index("--host") + 1]
    app.run(debug=True, host=host, port=port)
