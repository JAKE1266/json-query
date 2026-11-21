"""命令行入口：

    python -m json_query data.json users[*].name
    python -m json_query data.json items[0] --type
    python -m json_query data.json "配置.超时" --count
    cat data.json | python -m json_query - users[1]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import QueryError, load_json, query


def _render(value) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _read_source(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    p = Path(path)
    if not p.exists():
        raise OSError(f"文件不存在: {p}")
    return p.read_text(encoding="utf-8-sig")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="json-query", description="JSON 点分路径查询（支持 [*] 通配 / 下标 / 切片）")
    ap.add_argument("--version", action="version", version=f"json-query {__version__}")
    ap.add_argument("file", help="JSON 文件；'-' 表示 stdin")
    ap.add_argument("path", help="查询路径，如 users[*].name、items[1:3]")
    ap.add_argument("--type", action="store_true", help="同时显示值类型")
    ap.add_argument("--count", action="store_true", help="只显示命中数")

    args = ap.parse_args(argv)
    try:
        data = load_json(_read_source(args.file))
        hits = query(data, args.path)
    except QueryError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"错误：{e.filename or e}", file=sys.stderr)
        return 1

    if args.count:
        print(len(hits))
        return 0 if hits else 1
    if not hits:
        print(f"路径无结果: {args.path!r}", file=sys.stderr)
        return 1
    for hit in hits:
        line = f"{hit.path} = {_render(hit.value)}"
        if args.type:
            kind = ("array" if isinstance(hit.value, list)
                    else "table" if isinstance(hit.value, dict)
                    else type(hit.value).__name__)
            line += f"  [{kind}]"
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
