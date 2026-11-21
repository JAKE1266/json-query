# json-query

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-29%20passing-success)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

零依赖的 JSON 点分路径查询 —— 一条命令从 JSON 里取值，支持数组下标、切片与 `[*]` 通配。

- **路径语法**：`a.b.c` / `items[0]` / `tags[-1]`（倒数）/ `items[1:3]`（切片，两端可省略）
- **通配**：`users[*].name` 展开数组；`配置.*` 展开对象全部键；可多层串联（`books[*].tags[*]`）
- **多结果友好**：每次命中都输出**完整可复现路径**，一眼看清值从哪来
- **类型标注**：`--type` 附带 `[str]` / `[int]` / `[array]` / `[table]`
- **CJK 键**：`配置.超时` 直接可用
- **退出码语义**：无命中 exit 1，方便接入脚本与管道

零第三方依赖，Python ≥ 3.8。

## 安装

```bash
pip install .
```

## 真实运行示例

对 `samples/data.json`（书店数据，3 本书）：

```console
$ python -m json_query samples/data.json "books[*].title"
books[0].title = 夜航西飞
books[1].title = 沙丘
books[2].title = 逐光之旅

$ python -m json_query samples/data.json "books[0].tags[*]" --type
books[0].tags[0] = 旅行  [str]
books[0].tags[1] = 传记  [str]

$ python -m json_query samples/data.json "books[9]"
路径无结果: 'books[9]'
（exit code 1）
```

管道与计数：

```console
$ cat data.json | python -m json_query - "shop"
shop = 演示书屋
$ python -m json_query samples/data.json "books[*].tags[*]" --count
5
```

## 作为库使用

```python
from json_query import get, query

data = {"users": [{"name": "张三"}, {"name": "李四"}], "配置": {"超时": 30}}

query(data, "users[*].name")
# [Hit('users[0].name', '张三'), Hit('users[1].name', '李四')]

get(data, "配置.超时")     # 30 —— 唯一命中才返回，多命中抛 QueryError
query(data, "不存在")      # []
```

## 路径语法速查

| 写法 | 含义 |
|------|------|
| `a.b.c` | 逐层取对象的键 |
| `items[0]` / `items[-1]` | 数组下标（支持倒数） |
| `items[1:3]` | 切片（含头不含尾，两端可省略） |
| `items[*]` | 展开数组全部元素 |
| `配置.*` | 展开对象全部键 |
| `users[*].roles[*]` | 通配可多层串联 |

键名允许中文、字母、数字、连字符与空格（`.`、`[`、`]`、`*` 为语法字符不可用于键名）。

## 设计取舍

- **结果必带路径**：通配查询的值脱离路径就没有意义，`Hit(path, value)` 让每次输出都能复制回脚本
- **单值 / 多值两套 API**：`get` 严格唯一（多命中即报错），`query` 返回全部命中——语义清晰不猜测
- **无结果不算错误**：`query` 返回空列表；CLI 层才把无命中转为 exit 1
- **零依赖**：`pip install json-query` 不拉任何包

## 运行测试

```bash
python -m unittest discover -s tests
# Ran 29 tests ... OK
```


## 📁 项目结构

```
json-query/
├── LICENSE
├── json_query/
├── pyproject.toml
├── samples/
├── tests/
└── README.md
```

## License

MIT
