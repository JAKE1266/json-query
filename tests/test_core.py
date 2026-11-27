import unittest

from json_query.core import QueryError, get, load_json, query, tokenize

DATA = {
    "name": "演示",
    "count": 3,
    "tags": ["alpha", "beta", "gamma"],
    "users": [
        {"name": "张三", "age": 20, "roles": ["admin"]},
        {"name": "李四", "age": 35, "roles": ["dev", "ops"]},
    ],
    "配置": {"超时": 30, "重试": 3},
    "empty": [],
}


class TestTokenize(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(tokenize("a.b.c"), [("key", "a"), ("key", "b"), ("key", "c")])

    def test_index_slice_wild(self):
        self.assertEqual(tokenize("items[0]"), [("key", "items"), ("index", 0)])
        self.assertEqual(tokenize("items[1:3]"),
                         [("key", "items"), ("slice", (1, 3))])
        self.assertEqual(tokenize("items[*].name"),
                         [("key", "items"), ("wild", None), ("key", "name")])

    def test_leading_dot_optional(self):
        self.assertEqual(tokenize(".a"), tokenize("a"))

    def test_cjk_keys(self):
        self.assertEqual(tokenize("配置.超时"), [("key", "配置"), ("key", "超时")])

    def test_spaces_are_part_of_keys(self):
        self.assertEqual(tokenize("name "), [("key", "name ")])
        self.assertEqual(tokenize("a b"), [("key", "a b")])
        self.assertEqual(tokenize("items[*].name "),
                         [("key", "items"), ("wild", None), ("key", "name ")])

    def test_outer_whitespace_is_not_silently_trimmed(self):
        for bad in [" name", "name\t", ". name"]:
            with self.assertRaises(QueryError, msg=bad):
                tokenize(bad)

    def test_invalid(self):
        for bad in ["", "  ", "a..b", "a[", "a[x]", "a[1:2:3]", "@#$"]:
            with self.assertRaises(QueryError, msg=bad):
                tokenize(bad)


class TestQuery(unittest.TestCase):
    def test_scalar_and_object(self):
        self.assertEqual(query(DATA, "name")[0].value, "演示")
        obj = query(DATA, "配置.超时")[0]
        self.assertEqual((obj.path, obj.value), ("配置.超时", 30))

    def test_index_and_negative(self):
        self.assertEqual(query(DATA, "tags[1]")[0].value, "beta")
        self.assertEqual(query(DATA, "tags[-1]")[0].value, "gamma")
        self.assertEqual(query(DATA, "tags[-4]"), [])

    def test_slice(self):
        self.assertEqual([h.value for h in query(DATA, "tags[0:2]")], ["alpha", "beta"])
        self.assertEqual([h.value for h in query(DATA, "tags[1:]")], ["beta", "gamma"])

    def test_wild_array(self):
        hits = query(DATA, "users[*].name")
        self.assertEqual([h.value for h in hits], ["张三", "李四"])
        self.assertEqual([h.path for h in hits], ["users[0].name", "users[1].name"])

    def test_wild_object(self):
        hits = query(DATA, "配置.*")
        self.assertEqual([h.value for h in hits], [30, 3])

    def test_wild_on_scalar_gives_nothing(self):
        self.assertEqual(query(DATA, "name[*]"), [])

    def test_no_result(self):
        self.assertEqual(query(DATA, "不存在"), [])
        self.assertEqual(query(DATA, "users[9]"), [])

    def test_trailing_space_key(self):
        data = {"name ": 1, "name": 2}
        hits = query(data, "name ")
        self.assertEqual([(hit.path, hit.value) for hit in hits], [("name ", 1)])
        self.assertEqual(get(data, "name "), 1)

    def test_trailing_space_key_after_wildcard(self):
        data = {"items": [{"name ": 3}, {"name": 4}]}
        hits = query(data, "items[*].name ")
        self.assertEqual([(hit.path, hit.value) for hit in hits], [("items[0].name ", 3)])

    def test_multi_wild_chains(self):
        hits = query(DATA, "users[*].roles[*]")
        self.assertEqual([h.value for h in hits], ["admin", "dev", "ops"])
        self.assertEqual(hits[1].path, "users[1].roles[0]")


class TestGet(unittest.TestCase):
    def test_unique(self):
        self.assertEqual(get(DATA, "count"), 3)
        self.assertEqual(get(DATA, "users[0].age"), 20)

    def test_ambiguous_raises(self):
        with self.assertRaises(QueryError):
            get(DATA, "users[*].name")

    def test_missing_raises(self):
        with self.assertRaises(QueryError):
            get(DATA, "不存在")


class TestLoadJson(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(load_json('{"a": 1}'), {"a": 1})

    def test_bad_json_position(self):
        with self.assertRaises(QueryError) as ctx:
            load_json('{"a": 1,\n"b": }')
        self.assertIn("第 2 行", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
