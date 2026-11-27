"""JSON 点分路径查询核心。

路径语法：
- ``a.b.c``           逐层取对象的键
- ``items[0]``        数组下标（负数表示倒数）
- ``items[*].name``   通配：展开数组全部元素或对象的全部键
- ``a.*.id``          通配可出现在任意层
- ``items[1:3]``      数组切片（含开头不含结尾）

查询结果是一组 ``(完整路径, 值)``；``get`` 要求恰好一个结果。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

_TOKEN_RE = re.compile(
    r"\.([\w\-][\w\- ]*)"        # .键名（\w 含 CJK 与数字；不含 *）
    r"|(\.\*)"                   # .*  通配
    r"|\[\*\]"                   # [*] 通配
    r"|\[(-?\d+)?\s*:\s*(-?\d+)?\]"   # [起:止]（两端均可省略）
    r"|\[(-?\d+)\]"              # [下标]
)


class QueryError(ValueError):
    """路径语法错误。"""


@dataclass(frozen=True)
class Hit:
    path: str
    value: Any


def tokenize(path: str) -> list[tuple[str, Any]]:
    """路径 → token 列表：("key", 名) / ("index", i) / ("slice", (a, b)) / ("wild",)。

    首个键允许省略前导点；键名允许 CJK、数字、连字符与空格。
    路径首尾空白不会自动去除，空格按键名内容处理。
    """
    if not path or not path.strip():
        raise QueryError("路径为空")
    text = path
    if text.startswith("."):
        text = text[1:]
    if not text.startswith("[") and not text.startswith(".*"):
        text = "." + text  # 让首个裸键走 .键名 分支
    tokens: list[tuple[str, Any]] = []
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            raise QueryError(f"无法解析路径片段: {text[pos:pos + 12]!r}（完整路径 {path!r}）")
        key, dot_star, s1, s2, idx = m.groups()
        if key is not None:
            tokens.append(("key", key))
        elif dot_star is not None or m.group(0) == "[*]":
            tokens.append(("wild", None))
        elif s1 is not None or s2 is not None or ":" in m.group(0):
            tokens.append(("slice", (int(s1) if s1 else None,
                                     int(s2) if s2 else None)))
        else:
            tokens.append(("index", int(idx)))
        pos = m.end()
    if not tokens:
        raise QueryError(f"路径为空: {path!r}")
    return tokens


def _step(node: Any, token, path: str) -> list[tuple[str, Any]]:
    kind, arg = token
    if kind == "key":
        if isinstance(node, dict) and arg in node:
            return [(f"{path}.{arg}", node[arg])]
        return []
    if kind == "index":
        if isinstance(node, list) and -len(node) <= arg < len(node):
            return [(f"{path}[{arg}]", node[arg])]
        return []
    if kind == "slice":
        if isinstance(node, list):
            start, stop = arg
            return [(f"{path}[{i}]", node[i]) for i in range(*slice(start, stop).indices(len(node)))]
        return []
    # wild
    if isinstance(node, list):
        return [(f"{path}[{i}]", v) for i, v in enumerate(node)]
    if isinstance(node, dict):
        return [(f"{path}.{k}", v) for k, v in node.items()]
    return []


def query(data: Any, path: str) -> list[Hit]:
    """按路径查询，返回全部命中（路径唯一可复现）。"""
    tokens = tokenize(path)
    nodes = [("", data)]
    for token in tokens:
        nodes = [hit for p, v in nodes for hit in _step(v, token, p)]
        if not nodes:
            return []
    return [Hit(p[1:] if p.startswith(".") else p, v) for p, v in nodes]


def get(data: Any, path: str) -> Any:
    """取唯一值；结果数不是 1 时抛 QueryError。"""
    hits = query(data, path)
    if not hits:
        raise QueryError(f"路径无结果: {path!r}")
    if len(hits) > 1:
        raise QueryError(f"路径命中 {len(hits)} 处（含通配），请用 query(): {path!r}")
    return hits[0].value


def load_json(text: str) -> Any:
    """解析 JSON 文本；错误转 QueryError。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise QueryError(f"JSON 解析失败（第 {e.lineno} 行第 {e.colno} 列）：{e.msg}") from None
