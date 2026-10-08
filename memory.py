class Memory:
    """管理 Agent 的上下文记忆。

    保存对话历史，让 LLM 能引用之前的交互内容。
    支持设置最大轮数，超出后自动截断旧消息。
    """

    def __init__(self, max_rounds: int = 20):
        self.messages: list[dict] = []
        self.max_rounds = max_rounds

    def add(self, role: str, content: str):
        """添加一条消息。"""
        self.messages.append({"role": role, "content": content})
        self._truncate()

    def get_messages(self) -> list[dict]:
        """获取当前所有消息，供 LLM 调用时使用。"""
        return list(self.messages)

    def clear(self):
        """清空记忆。"""
        self.messages.clear()

    def _truncate(self):
        """超出最大轮数时截断旧消息，保留 system 消息。"""
        non_system = [m for m in self.messages if m["role"] != "system"]
        if len(non_system) > self.max_rounds * 2:
            system_msgs = [m for m in self.messages if m["role"] == "system"]
            self.messages = system_msgs + non_system[-self.max_rounds * 2:]
