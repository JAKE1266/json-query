import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

DATA = {
    "shop": "演示书屋",
    "books": [
        {"title": "夜航西飞", "price": 45, "tags": ["旅行", "传记"]},
        {"title": "沙丘", "price": 68, "tags": ["科幻"]},
        {"title": "逐光之旅", "price": 52, "tags": ["科幻", "绘本"]},
    ],
}


def make(tmp: Path, name: str, content) -> str:
    p = tmp / name
    p.write_text(content if isinstance(content, str) else __import__("json").dumps(content, ensure_ascii=False),
                 encoding="utf-8")
    return str(p)


def run_cli(*args, stdin_text=None, expect=0):
    r = subprocess.run([PY, "-m", "json_query", *args], input=stdin_text,
                       capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if r.returncode != expect:
        raise AssertionError(f"exit={r.returncode} (expect {expect})\n"
                             f"stdout={r.stdout}\nstderr={r.stderr}")
    return r


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = make(Path(self.tmp.name), "data.json", DATA)

    def tearDown(self):
        self.tmp.cleanup()

    def test_scalar(self):
        r = run_cli(self.data, "shop")
        self.assertEqual(r.stdout, "shop = 演示书屋\n")

    def test_wild_multi_hits(self):
        r = run_cli(self.data, "books[*].title")
        self.assertEqual(r.stdout,
                         "books[0].title = 夜航西飞\n"
                         "books[1].title = 沙丘\n"
                         "books[2].title = 逐光之旅\n")

    def test_index_object(self):
        r = run_cli(self.data, "books[1]")
        self.assertIn('"title": "沙丘"', r.stdout)

    def test_nested_wild(self):
        r = run_cli(self.data, "books[*].tags[*]")
        self.assertIn("books[0].tags[0] = 旅行", r.stdout)
        self.assertIn("books[2].tags[1] = 绘本", r.stdout)

    def test_type_flag(self):
        r = run_cli(self.data, "books[0].price", "--type")
        self.assertIn("[int]", r.stdout)

    def test_count(self):
        r = run_cli(self.data, "books[*].title", "--count")
        self.assertEqual(r.stdout.strip(), "3")

    def test_cjk_keys(self):
        r = run_cli(self.data, "shop")  # 顶层英文键
        nested = make(Path(self.tmp.name), "cjk.json", '{"配置": {"超时": 30}}')
        r2 = run_cli(nested, "配置.超时")
        self.assertEqual(r2.stdout, "配置.超时 = 30\n")

    def test_no_result_exit1(self):
        r = run_cli(self.data, "books[9]", expect=1)
        self.assertIn("路径无结果", r.stderr)

    def test_stdin(self):
        r = run_cli("-", "shop", stdin_text='{"shop": "来自 stdin"}')
        self.assertEqual(r.stdout, "shop = 来自 stdin\n")

    def test_bad_path_syntax(self):
        r = run_cli(self.data, "a..b", expect=1)
        self.assertIn("无法解析路径片段", r.stderr)

    def test_missing_file(self):
        r = run_cli("nope.json", "shop", expect=1)
        self.assertIn("文件不存在", r.stderr)


if __name__ == "__main__":
    unittest.main()
