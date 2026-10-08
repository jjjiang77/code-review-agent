import subprocess
import sys
import tempfile
import os


def execute_code(code: str, timeout: int = 5) -> str:
    """在沙箱中执行 Python 代码片段。

    将代码写入临时文件，用子进程执行，捕获输出。
    设置超时防止死循环。

    Args:
        code: 要执行的 Python 代码字符串。
        timeout: 超时秒数，默认 5 秒。

    Returns:
        执行结果字符串，包含 stdout 和 stderr。
    """
    if not code:
        return "错误：未提供代码"

    if any(kw in code for kw in ["import os", "import subprocess", "os.system", "os.popen",
                                  "os.remove", "os.rmdir", "shutil"]):
        return "安全限制：检测到危险操作（文件系统访问），已拒绝执行"

    tmp_dir = tempfile.mkdtemp()
    tmp_file = os.path.join(tmp_dir, "_exec.py")

    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(code)
    except Exception as e:
        return f"错误：写入临时文件失败 — {e}"

    try:
        result = subprocess.run(
            [sys.executable, tmp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tmp_dir,
        )

        output = []
        if result.stdout:
            output.append(f"stdout:\n{result.stdout}")
        if result.stderr:
            output.append(f"stderr:\n{result.stderr}")
        if result.returncode != 0:
            output.append(f"退出码: {result.returncode}")

        return "\n".join(output) if output else "(无输出)"

    except subprocess.TimeoutExpired:
        return f"错误：代码执行超时（{timeout}秒）"
    except Exception as e:
        return f"错误：执行失败 — {e}"
    finally:
        try:
            os.remove(tmp_file)
            os.rmdir(tmp_dir)
        except Exception:
            pass
