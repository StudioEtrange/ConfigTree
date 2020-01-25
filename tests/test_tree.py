import pytest

from configtree.tree import Tree, flatten, rarefy


@pytest.fixture
def td():
    return Tree({"1": 1, "a.2": 2, "a.b.3": 3, "a.b.4": 4, "a.b.5": 5, "a.b.6": 6})


def test_read_write():
    td = Tree()

    td["1"] = 1
    td["a.2"] = 2
    td["a.b.3"] = 3
    td["a"]["b.4"] = 4
    td["a"]["b"]["5"] = 5
    td["a.b"]["6"] = 6

    assert td["1"] == 1
    assert td["a.2"] == 2
    assert td["a.b.3"] == 3
    assert td["a.b.4"] == 4
    assert td["a.b.5"] == 5
    assert td["a.b.6"] == 6

    assert td["a"]["2"] == 2
    assert td["a"]["b.3"] == 3
    assert td["a"]["b.4"] == 4
    assert td["a"]["b.5"] == 5
    assert td["a"]["b.6"] == 6

    assert td["a"]["b"]["3"] == 3
    assert td["a"]["b"]["4"] == 4
    assert td["a"]["b"]["5"] == 5
    assert td["a"]["b"]["6"] == 6

    assert td["a.b"]["3"] == 3
    assert td["a.b"]["4"] == 4
    assert td["a.b"]["5"] == 5
    assert td["a.b"]["6"] == 6


def test_contains(td):
    assert "1" in td
    assert "a" in td
    assert "a.2" in td
    assert "a.b" in td
    assert "a.b.3" in td
    assert "a.b.4" in td
    assert "a.b.5" in td
    assert "a.b.6" in td

    assert "2" in td["a"]
    assert "b" in td["a"]
    assert "b.3" in td["a"]
    assert "b.4" in td["a"]
    assert "b.5" in td["a"]
    assert "b.6" in td["a"]

    assert "3" in td["a.b"]
    assert "4" in td["a.b"]
    assert "5" in td["a.b"]
    assert "6" in td["a.b"]


def test_len(td):
    assert len(td) == 6
    assert len(td["a"]) == 5
    assert len(td["a.b"]) == 4


def test_tree_key_error():
    td = Tree()
    with pytest.raises(KeyError):
        td["x"]


def test_branch_key_error():
    td = Tree({"a.y": 1})
    with pytest.raises(KeyError):
        td["a"]["x"]


def test_tree_eq_dict(td):
    assert td == {"1": 1, "a.2": 2, "a.b.3": 3, "a.b.4": 4, "a.b.5": 5, "a.b.6": 6}
    assert td["a"] == {"2": 2, "b.3": 3, "b.4": 4, "b.5": 5, "b.6": 6}
    assert td["a.b"] == {"3": 3, "4": 4, "5": 5, "6": 6}


def test_iter_and_keys(td):
    assert sorted(list(iter(td))) == ["1", "a.2", "a.b.3", "a.b.4", "a.b.5", "a.b.6"]
    assert sorted(list(iter(td["a"]))) == ["2", "b.3", "b.4", "b.5", "b.6"]
    assert sorted(list(iter(td["a.b"]))) == ["3", "4", "5", "6"]


def test_rare_iterators(td):
    def key(v):
        return str(v)

    assert sorted(list(td.rare_keys())) == ["1", "a"]
    assert sorted(list(td.rare_values()), key=key) == [1, td["a"]]
    assert sorted(list(td.rare_items()), key=key) == [("1", 1), ("a", td["a"])]

    assert sorted(list(td["a"].rare_keys())) == ["2", "b"]
    assert sorted(list(td["a"].rare_values()), key=key) == [2, td["a.b"]]
    assert sorted(list(td["a"].rare_items()), key=key) == [("2", 2), ("b", td["a.b"])]


def test_repr():
    td = Tree()

    td["x.y"] = 1
    assert repr(td) == "Tree({'x.y': 1})"
    assert repr(td["x"]) == "BranchProxy('x'): {'y': 1}"


def test_copy(td):
    new_td = td.copy()
    assert new_td == td
    assert new_td is not td
    assert isinstance(new_td, Tree)

    new_td = td["a"].copy()
    assert new_td == td["a"]
    assert new_td is not td["a"]
    assert isinstance(new_td, Tree)


def test_rare_copy(td):
    rd = td.rare_copy()
    assert rd == {"1": 1, "a": {"2": 2, "b": {"3": 3, "4": 4, "5": 5, "6": 6}}}

    rd = td["a"].rare_copy()
    assert rd == {"2": 2, "b": {"3": 3, "4": 4, "5": 5, "6": 6}}


def test_pop(td):
    assert td.pop("x", 1) == 1
    assert "x" not in td
    assert td.pop("a.2") == 2
    assert "a.2" not in td

    a = td.pop("a")
    assert "a" not in td
    assert isinstance(a, Tree)
    assert a == {"b.3": 3, "b.4": 4, "b.5": 5, "b.6": 6}


def test_branch_pop(td):
    b = td["a"].pop("b")
    assert "a.b" not in td
    assert isinstance(b, Tree)
    assert b == {"3": 3, "4": 4, "5": 5, "6": 6}


def test_pop_key_error():
    td = Tree()
    with pytest.raises(KeyError):
        td.pop("x")


def test_override_branch():
    td = Tree({"x.y.1": 1})

    td["x"] = 1
    assert "x.y.1" not in td
    assert "x.y" not in td
    assert td["x"] == 1

    td["x.y.1"] = 1
    assert "x.y.1" in td
    assert "x.y" in td
    assert td["x"] == {"y.1": 1}


def test_get_value():
    td = Tree()

    assert td.get("x.y", 1) == 1
    assert "x.y" not in td
    assert td.setdefault("x.y", 2) == 2
    assert "x.y" in td


def test_get_branch():
    td = Tree()

    bx = td.branch("x")
    assert "x" not in td  # Empty branch not in tree
    bx["1"] = 1
    assert "x" in td
    assert "x.1" in td

    bxy = bx.branch("y")
    assert "x.y" not in td
    assert "y" not in bx

    bxy["2"] = 2
    assert "x.y.2" in td
    assert "x.y" in td
    assert "y.2" in bx
    assert "y" in bx


def test_delete_value(td):
    del td["a.b.4"]
    del td["a.b.5"]
    del td["a.b.6"]
    assert "a.b.3" in td
    assert "a.b" in td
    assert "a" in td

    del td["a.b.3"]
    assert "a.b" not in td  # Empty branch is removed from tree


def test_delete_branch(td):
    del td["a"]
    assert "a.b.3" not in td  # Branch is removed with its values
    assert "a.b.4" not in td
    assert "a.b.5" not in td
    assert "a.b.6" not in td
    assert "a.b" not in td
    assert "a.2" not in td
    assert "a" not in td


def test_delete_key_error():
    td = Tree()
    with pytest.raises(KeyError):
        del td["x"]


def test_flatten():
    fd = dict(flatten({"a": {"b": {"c": {1: 1, 2: 2}}}}))
    assert fd == {"a.b.c.1": 1, "a.b.c.2": 2}


def test_rarefy():
    rd = rarefy(Tree({"a.b.c": 1, "x.y.z": 1}))
    assert rd == {"a": {"b": {"c": 1}}, "x": {"y": {"z": 1}}}

    rd = rarefy({"a.b.c": {"x.y.z": 1}})
    assert rd == {"a": {"b": {"c": {"x": {"y": {"z": 1}}}}}}
