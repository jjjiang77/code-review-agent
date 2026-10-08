import os


def read_file(filepath: str) -> str:
    """读取本地代码文件内容。

    Args:
        filepath: 文件路径，支持相对路径和绝对路径。

    Returns:
        文件内容字符串。如果文件不存在或读取失败，返回错误信息。
    """
    if not filepath:
        return "错误：未提供文件路径"

    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        return f"错误：文件 {filepath} 不存在"

    if os.path.isdir(abs_path):
        return f"错误：{filepath} 是目录，不是文件"

    max_size = 1024 * 1024  # 1MB
    if os.path.getsize(abs_path) > max_size:
        return f"错误：文件 {filepath} 超过 1MB 限制"

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(abs_path, "r", encoding="latin-1") as f:
            return f.read()
    except Exception as e:
        return f"错误：读取文件失败 — {e}"
