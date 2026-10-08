import re
import os
import ast


def analyze_code(filepath):
    """分析代码文件：行数统计、敏感信息检测、函数列表。"""
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        return f"错误：文件 {filepath} 不存在"

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            code = f.read()
    except UnicodeDecodeError:
        with open(abs_path, "r", encoding="latin-1") as f:
            code = f.read()
    except Exception as e:
        return f"错误：读取文件失败 — {e}"

    lines = code.split("\n")
    total_lines = len(lines)
    blank_lines = len([l for l in lines if not l.strip()])
    comment_lines = len([l for l in lines if l.strip().startswith(("#", "//", "/*", "*"))])
    code_lines = total_lines - blank_lines - comment_lines

    # 敏感信息检测
    sensitive_patterns = [
        (r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']', "硬编码密码"),
        (r'(?:secret|api_key|apikey|access_key)\s*=\s*["\'][^"\']{5,}["\']', "硬编码密钥"),
        (r'(?:token)\s*=\s*["\'][^"\']{5,}["\']', "硬编码 Token"),
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "IP 地址"),
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "邮箱地址"),
    ]

    findings = []
    for pattern, desc in sensitive_patterns:
        matches = re.findall(pattern, code, re.IGNORECASE)
        if matches:
            findings.append(f"  - {desc}: 发现 {len(matches)} 处")

    # 函数列表
    functions = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args_count = len(node.args.args)
                length = node.end_lineno - node.lineno + 1 if hasattr(node, "end_lineno") else 0
                functions.append(f"  - {node.name}(): 参数 {args_count} 个, 约 {length} 行")
    except SyntaxError:
        functions.append("  (语法错误，无法解析函数)")

    # 组装报告
    report = []
    report.append("=== 代码分析报告 ===")
    report.append(f"文件: {filepath}")
    report.append(f"总行数: {total_lines}")
    report.append(f"代码行: {code_lines} | 空行: {blank_lines} | 注释: {comment_lines}")
    report.append("")

    report.append("--- 敏感信息检测 ---")
    if findings:
        report.append("\n".join(findings))
    else:
        report.append("  未发现敏感信息")

    report.append("")
    report.append("--- 函数列表 ---")
    if functions:
        report.append("\n".join(functions))
    else:
        report.append("  未检测到函数定义")

    return "\n".join(report)
