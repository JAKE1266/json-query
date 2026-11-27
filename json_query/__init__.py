"""json-query —— JSON 点分路径查询。"""
from .core import Hit, QueryError, get, load_json, query, tokenize

__version__ = "0.1.1"

__all__ = ["Hit", "QueryError", "get", "load_json", "query", "tokenize", "__version__"]
