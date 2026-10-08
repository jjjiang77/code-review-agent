import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.file_reader import read_file
from tools.code_analyzer import analyze_code
from tools.code_executor import execute_code
from agent import CodeReviewAgent
from memory import Memory


def test_read_file():
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    tmp.write("print('hello')")
    tmp.close()

    result = read_file(tmp.name)
    assert "print('hello')" in result

    result = read_file("/nonexistent/file.py")
    assert "不存在" in result

    os.unlink(tmp.name)
    print("test_read_file: PASS")


def test_analyze_code():
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    tmp.write(
        'password = "admin123"\n\n'
        'def foo(a, b):\n'
        '    return a + b\n'
    )
    tmp.close()

    result = analyze_code(tmp.name)
    assert "硬编码密码" in result
    assert "foo" in result

    os.unlink(tmp.name)
    print("test_analyze_code: PASS")


def test_execute_code():
    result = execute_code("print(sum(range(10)))")
    assert "45" in result

    result = execute_code("import os; os.system('rm -rf /')")
    assert "安全限制" in result

    print("test_execute_code: PASS")


def test_memory():
    mem = Memory(max_rounds=2)
    mem.add("system", "你是一个助手")
    for i in range(10):
        mem.add("user", f"问题{i}")
        mem.add("assistant", f"回答{i}")

    messages = mem.get_messages()
    assert len(messages) <= 5

    print("test_memory: PASS")


def test_parse_tool_call():
    agent = CodeReviewAgent.__new__(CodeReviewAgent)

    result = agent._parse_tool_call("我来读取文件\n[CALL:read_file|filepath=main.py]")
    assert result is not None
    assert result[0] == "read_file"
    assert result[1]["filepath"] == "main.py"

    result = agent._parse_tool_call("这是最终回答，没有工具调用")
    assert result is None

    print("test_parse_tool_call: PASS")


def test_tool_failure_not_fatal():
    agent = CodeReviewAgent.__new__(CodeReviewAgent)

    result = agent._execute_tool("read_file", {"filepath": "/nonexistent"})
    assert "不存在" in result

    result = agent._execute_tool("execute_code", {})
    assert "参数错误" in result or "未提供" in result

    print("test_tool_failure_not_fatal: PASS")


def test_agent_run_with_tool_call():
    """模拟 Agent 循环：LLM 先调工具，再给最终回答。"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "审查完成，没有问题。"

    # 第一次返回工具调用，第二次返回最终回答
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(
            content="[CALL:read_file|filepath=sample.py]"
        ))]),
        mock_response,
    ]

    agent = CodeReviewAgent(mock_client)
    result = agent.run("请审查 sample.py")

    assert "审查完成" in result
    # 确认 LLM 被调了两次（一次工具调用 + 一次最终回答）
    assert mock_client.chat.completions.create.call_count == 2

    print("test_agent_run_with_tool_call: PASS")


def test_agent_run_no_tool():
    """模拟 Agent 循环：LLM 直接回答，不调工具。"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "这段代码没有明显问题。"

    mock_client.chat.completions.create.return_value = mock_response

    agent = CodeReviewAgent(mock_client)
    result = agent.run("帮我看看 print(1) 有没有问题")

    assert "没有明显问题" in result
    assert mock_client.chat.completions.create.call_count == 1

    print("test_agent_run_no_tool: PASS")


def test_agent_max_iterations():
    """模拟 Agent 达到最大轮数。"""
    mock_client = MagicMock()
    # 每次都返回工具调用，永远不会给出最终回答
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "[CALL:read_file|filepath=sample.py]"
    mock_client.chat.completions.create.return_value = mock_response

    agent = CodeReviewAgent(mock_client)
    result = agent.run("请审查 sample.py")

    assert "最大推理轮数" in result
    # 确认调了 5 次（MAX_ITERATIONS）
    assert mock_client.chat.completions.create.call_count == 5

    print("test_agent_max_iterations: PASS")


if __name__ == "__main__":
    test_read_file()
    test_analyze_code()
    test_execute_code()
    test_memory()
    test_parse_tool_call()
    test_tool_failure_not_fatal()
    test_agent_run_with_tool_call()
    test_agent_run_no_tool()
    test_agent_max_iterations()
    print("\n全部测试通过！")
