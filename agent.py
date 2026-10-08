import re
import time

from openai import OpenAI

from prompts import SYSTEM_PROMPT
from memory import Memory
from tools import read_file, analyze_code, execute_code

TOOL_REGISTRY = {
    "read_file": read_file,
    "analyze_code": analyze_code,
    "execute_code": execute_code,
}

MAX_ITERATIONS = 5
MAX_RETRIES = 3


class CodeReviewAgent:
    """代码审查 Agent。"""

    def __init__(self, client, model="qwen-plus", event_callback=None):
        self.client = client
        self.model = model
        self.memory = Memory(max_rounds=20)
        self.memory.add("system", SYSTEM_PROMPT)
        self.event_callback = event_callback  # 事件回调，用于 Web 界面推送

    def _emit(self, event_type, data):
        """触发事件回调。"""
        if self.event_callback:
            self.event_callback(event_type, data)

    def run(self, user_input):
        """Agent 主循环：用户输入 -> LLM推理 -> 工具调用 -> 输出。"""
        self.memory.add("user", user_input)
        self._emit("user", {"content": user_input})

        for i in range(MAX_ITERATIONS):
            llm_response = self._call_llm()
            if llm_response is None:
                self._emit("error", {"message": "LLM 调用失败"})
                return "Agent 请求失败，请检查 API Key 和网络后重试。"

            tool_call = self._parse_tool_call(llm_response)

            if tool_call is None:
                self.memory.add("assistant", llm_response)
                self._emit("answer", {"content": llm_response})
                return llm_response

            tool_name, tool_args = tool_call
            print(f"  [工具调用] {tool_name}({tool_args})")
            self._emit("tool_call", {"name": tool_name, "args": tool_args})

            result = self._execute_tool(tool_name, tool_args)
            print(f"  [工具结果] {result[:200]}...")
            self._emit("tool_result", {"name": tool_name, "result": result})

            self.memory.add("assistant", llm_response)
            self.memory.add("tool", f"工具 {tool_name} 的执行结果:\n{result}")

        self._emit("max_iterations", {"message": "达到最大推理轮数"})
        return "Agent 达到最大推理轮数，请简化请求后重试。"

    def _call_llm(self):
        """调用 LLM，失败时重试最多 3 次。"""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.memory.get_messages(),
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"  [LLM 调用失败] {e}")
                    return None
                wait = 2 ** attempt
                print(f"  [重试] 第 {attempt + 1} 次失败, {wait}s 后重试...")
                time.sleep(wait)
        return None

    def _parse_tool_call(self, text):
        """从 LLM 回复中解析工具调用。

        格式: [CALL:工具名|参数名=参数值]
        """
        pattern = r'\[CALL:(\w+)\|([^\]]+)\]'
        match = re.search(pattern, text)

        if not match:
            return None

        tool_name = match.group(1)
        args_str = match.group(2)

        args = {}
        for pair in args_str.split("|"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                args[key.strip()] = value.strip()

        if tool_name not in TOOL_REGISTRY:
            return None

        return tool_name, args

    def _execute_tool(self, tool_name, args):
        """执行工具调用。工具失败返回错误信息，不中断循环。"""
        func = TOOL_REGISTRY[tool_name]
        try:
            return func(**args)
        except TypeError as e:
            return f"工具参数错误: {e}"
        except Exception as e:
            return f"工具执行出错: {e}"
