import json
import os
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

import json_query
from json_query import QueryError, get, query, tokenize

ROOT = Path(__file__).resolve().parents[1]


def run_cli(console, args, payload, cwd):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    env["PYTHONUTF8"] = "0"
    result = subprocess.run(
        [str(console), *args], input=payload.encode("utf-8"),
        capture_output=True, cwd=cwd, env=env,
    )
    stdout = result.stdout.decode("utf-8").replace("\r\n", "\n")
    stderr = result.stderr.decode("utf-8").replace("\r\n", "\n")
    if result.returncode != 0:
        raise RuntimeError(
            f"exit={result.returncode}\nstdout={stdout}\nstderr={stderr}"
        )
    return stdout, stderr


def main():
    module_path = Path(json_query.__file__).resolve()
    if module_path == (ROOT / "json_query" / "__init__.py").resolve():
        raise RuntimeError(f"json_query 仍从源码目录导入：{module_path}")

    package = distribution("json-query-kit")
    if package.version != "0.1.1" or json_query.__version__ != package.version:
        raise RuntimeError(
            f"版本不符：metadata={package.version}, module={json_query.__version__}"
        )

    scripts_dir = Path(sys.executable).parent
    console = scripts_dir / ("json-query.exe" if os.name == "nt" else "json-query")
    if not console.exists():
        raise RuntimeError(f"控制台脚本不存在：{console}")

    if tokenize("name ") != [("key", "name ")]:
        raise RuntimeError("键名尾空格未保留")
    try:
        tokenize(" name")
    except QueryError:
        pass
    else:
        raise RuntimeError("路径首空格被静默清理")
    data = {"name ": 1, "name": 2, "items": [{"name ": 3}]}
    if [(hit.path, hit.value) for hit in query(data, "name ")] != [("name ", 1)]:
        raise RuntimeError("尾空格键查询失败")
    if get(data, "name ") != 1:
        raise RuntimeError("尾空格键 get 失败")
    if [(hit.path, hit.value) for hit in query(data, "items[*].name ")] != [("items[0].name ", 3)]:
        raise RuntimeError("通配后的尾空格键查询失败")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        source = work / "data.json"
        source.write_text(
            json.dumps({"shop": "演示书屋", "name ": "尾空格"}, ensure_ascii=False),
            encoding="utf-8",
        )

        stdout, stderr = run_cli(console, ["--version"], "", work)
        if stdout.strip() != "json-query 0.1.1" or stderr:
            raise RuntimeError(f"版本检查失败：stdout={stdout!r}, stderr={stderr!r}")

        stdout, stderr = run_cli(console, [str(source), "shop"], "", work)
        if stdout != "shop = 演示书屋\n" or stderr:
            raise RuntimeError(f"文件输入异常：stdout={stdout!r}, stderr={stderr!r}")

        stdout, stderr = run_cli(
            console, ["-", "name "], '{"name ": "尾空格"}', work,
        )
        if stdout != "name  = 尾空格\n" or stderr:
            raise RuntimeError(f"UTF-8 管道或尾空格键异常：stdout={stdout!r}, stderr={stderr!r}")

        stdout, stderr = run_cli(
            console, [str(source), "shop", "--count"], "", work,
        )
        if stdout != "1\n" or stderr:
            raise RuntimeError(f"计数模式异常：stdout={stdout!r}, stderr={stderr!r}")

    print("Installed wheel smoke test passed")


if __name__ == "__main__":
    main()
