import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from agent import CodeReviewAgent


def main():
    load_dotenv()

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key or api_key == "sk-your-api-key-here":
        print("请先配置 API Key！")
        print("1. 复制 .env.example 为 .env")
        print("2. 填入你的通义千问 API Key")
        print("   申请地址: https://bailian.console.aliyun.com/")
        sys.exit(1)

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    agent = CodeReviewAgent(client, model="qwen-plus")

    print("=" * 50)
    print("  代码审查 Agent")
    print("  输入 'quit' 退出 | 'clear' 清空记忆")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("再见！")
            break
        if user_input.lower() == "clear":
            agent.memory.clear()
            from prompts import SYSTEM_PROMPT
            agent.memory.add("system", SYSTEM_PROMPT)
            print("  [记忆已清空]")
            continue

        print("\nAgent> ", end="")
        result = agent.run(user_input)
        print(result)


if __name__ == "__main__":
    main()
