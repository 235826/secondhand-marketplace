"""按 Python token 统计有效物理行，排除空白、注释和独立文档字符串。"""

import ast
import io
import json
import tokenize
from pathlib import Path


def count(path):
    source = path.read_text()
    docstring_lines = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                value = node.body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    docstring_lines.update(range(value.lineno, value.end_lineno + 1))
    ignored = {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENDMARKER,
        tokenize.ENCODING,
    }
    lines = set()
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type not in ignored:
            lines.update(range(token.start[0], token.end[0] + 1))
    return len(lines - docstring_lines)


def main():
    root = Path(__file__).resolve().parents[1]
    business = {
        str(p.relative_to(root)): count(p) for p in sorted((root / "marketplace").glob("*.py"))
    }
    result = {
        "definition": "Python 有效物理行，排除空白、注释及模块/类/函数文档字符串；"
        "SQL 多行字符串属于实现，计入其有效行；模板、样式、测试、脚本另列。",
        "business_python": business,
        "business_python_total": sum(business.values()),
        "tests_python_total": sum(count(p) for p in (root / "tests").glob("*.py")),
        "scripts_python_total": sum(count(p) for p in (root / "scripts").glob("*.py")),
        "sql_physical_lines": len((root / "marketplace/schema.sql").read_text().splitlines()),
        "template_files": len(list((root / "marketplace/templates").glob("*.html"))),
        "gui_generated_lines": 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
