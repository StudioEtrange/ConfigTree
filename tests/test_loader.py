import math
import os
import sys

import pytest

from configtree.loader import (
    Loader,
    Pipeline,
    Walker,
    File,
    Updater,
    UpdateAction,
    Promise,
    ResolverProxy,
    Required,
    PostProcessor,
    ProcessingError,
)
from configtree.tree import Tree


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(data_dir, "data", "loader")


@pytest.fixture(autouse=True)
def cleanup_env():
    yield

    for path in sys.path[:]:
        if path.startswith(data_dir):
            sys.path.remove(path)
    try:
        del sys.modules["loaderconf"]
    except KeyError:
        pass


def test_loader():
    update = Updater(namespace={"floor": math.floor})
    load = Loader(update=update)
    result = load(data_dir)
    assert result == {
        "a.x": 1,
        "a.y": 2,
        "b.x": 10,
        "b.y": 20,
        "subsystem.a.x": 101,
        "subsystem.a.y": 102,
        "subsystem.b.x": 110,
        "subsystem.b.y": 120,
        "c.x": 10,
        "c.y": 20,
        "c.z": 30,
    }

    walk = Walker(env="y")
    load = Loader(walk=walk, update=update)
    result = load(data_dir)
    assert result == {
        "a.x": 1,
        "a.y": 2,
        "b.x": 10,
        "b.y": 20,
        "subsystem.a.x": 101,
        "subsystem.a.y": 102,
        "subsystem.b.x": 110,
        "subsystem.b.y": 120,
        "a.b.x": 1,
        "a.b.y": 2,
        "a.b.z": 3,
        "a.b.c": "x = 1, y = 2",
        "a.b.l": [4, 5, 6],
        "z": 3,
        "path": os.path.join(data_dir, "somepath"),
        "here": os.path.join(data_dir, "env-y.yaml"),
        "c.x": 10,
        "c.y": 20,
        "c.z": 30,
    }
    
    walk = Walker(env="z")
    load = Loader(walk=walk, update=update)
    result = load(os.path.join(data_dir,"env-z"))
    assert result == {
        "a.b.l": [4, 5, 6, 7, '8'],
        "a.b.x": 1,
        "a.b.y": 3,
        "a.b.z": 7,
        "u": [1, 2, 3, 4, '', 'first second', 'third'],
        "w": 'foo bar',
        "t": ['', 'first second', 'third'],
        "j": 'foo',
        "y": 10,
        "k": [1, 2, 1, 2],
        "mu": ['third', 'four'],
        "moo": ['foo bar'],
    }


def test_loader_fromconf():
    load = Loader.fromconf(data_dir)
    assert load.walk == "walk"
    assert load.update == "update"
    assert load.postprocess == "postprocess"
    assert load.tree == "tree"


def test_loader_fromconf_no_loaderconf():
    load = Loader.fromconf(os.path.dirname(data_dir))
    assert isinstance(load.walk, Walker)
    assert isinstance(load.update, Updater)
    assert isinstance(load.postprocess, PostProcessor)
    assert isinstance(load.tree, Tree)


def test_loader_fromconf_import_error():
    with pytest.raises(ImportError):
        Loader.fromconf(os.path.join(data_dir, "bad_loaderconf"))


def test_pipeline():
    class Test(Pipeline):
        @Pipeline.worker(1)
        def first(self):
            pass

        @Pipeline.worker(2, enabled=False)
        def second(self):
            pass

        @Pipeline.worker(3)
        def third(self):
            pass

    t = Test()
    assert t.__pipeline__ == [t.first, t.third]


def test_walker():
    walk = Walker()
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    assert files == [
        os.path.join("default", "a.json"),
        os.path.join("default", "b.yaml"),
        os.path.join("default", "empty.yaml"),
        os.path.join("default", "subsystem", "a.yaml"),
        os.path.join("default", "subsystem", "b.yaml"),
        os.path.join("final-common", "c.yaml"),
        "final-common.yaml",
    ]

    walk = Walker(env="y")
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    assert files == [
        os.path.join("default", "a.json"),
        os.path.join("default", "b.yaml"),
        os.path.join("default", "empty.yaml"),
        os.path.join("default", "subsystem", "a.yaml"),
        os.path.join("default", "subsystem", "b.yaml"),
        "env-y.yaml",
        os.path.join("final-common", "c.yaml"),
        "final-common.yaml",
    ]

    walk = Walker(env="x")
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    assert files == [
        os.path.join("default", "a.json"),
        os.path.join("default", "b.yaml"),
        os.path.join("default", "empty.yaml"),
        os.path.join("default", "subsystem", "a.yaml"),
        os.path.join("default", "subsystem", "b.yaml"),
        os.path.join("env-x", "a.yaml"),
        os.path.join("final-common", "c.yaml"),
        "final-common.yaml",
    ]

    walk = Walker(env="x.xx")
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    assert files == [
        os.path.join("default", "a.json"),
        os.path.join("default", "b.yaml"),
        os.path.join("default", "empty.yaml"),
        os.path.join("default", "subsystem", "a.yaml"),
        os.path.join("default", "subsystem", "b.yaml"),
        os.path.join("env-x", "a.yaml"),
        os.path.join("env-x", "env-xx", "b.yaml"),
        os.path.join("final-common", "c.yaml"),
        "final-common.yaml",
    ]

    walk = Walker(env="xx")
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    assert files == [
        os.path.join("default", "a.json"),
        os.path.join("default", "b.yaml"),
        os.path.join("default", "empty.yaml"),
        os.path.join("default", "subsystem", "a.yaml"),
        os.path.join("default", "subsystem", "b.yaml"),
        "env-xx.yaml",
        os.path.join("final-common", "c.yaml"),
        "final-common.yaml",
    ]


def test_file():
    f = File(data_dir, "default", {})
    assert f.path == data_dir
    assert f.name == "default"
    assert f.fullpath == os.path.join(data_dir, "default")
    assert f.isdir == True
    assert f.isfile == False
    assert f.cleanname == "default"
    assert f.ext == ""

    f = File(data_dir, "env-y.yaml", {})
    assert f.path == data_dir
    assert f.name == "env-y.yaml"
    assert f.fullpath == os.path.join(data_dir, "env-y.yaml")
    assert f.isdir == False
    assert f.isfile == True
    assert f.cleanname == "env-y"
    assert f.ext == ".yaml"

    f1 = File(data_dir, "env-y.yaml", {})
    f2 = File(data_dir, "final-common.yaml", {})
    assert (f1 < f2) == True


def test_updater_set_default():
    tree = Tree({"foo": "bar"})
    update = Updater()
    update(tree, "foo?", "baz", "/test/source.yaml")
    assert tree == {"foo": "bar"}

    update(tree, "bar?", "baz", "/test/source.yaml")
    assert tree == {"foo": "bar", "bar": "baz"}


def test_loader_set_default_tree():
    tree = Tree({"foo": "bar"})
    load = Loader(tree=tree)
    assert id(load.tree) == id(tree)

    tree = Tree()
    load = Loader(tree=tree)
    assert id(load.tree) == id(tree)


def test_updater_call_method():
    tree = Tree({"foo": []})
    update = Updater()
    update(tree, "foo#append", 1, "/test/source.yaml")
    assert tree["foo"] == [1]

    update(tree, "foo#append", ">>> 2", "/test/source.yaml")
    assert isinstance(tree["foo"], Promise)
    assert tree["foo"](), [1, 2]

    update(tree, "foo#append", 3, "/test/source.yaml")
    assert isinstance(tree["foo"], Promise)
    assert tree["foo"](), [1, 2, 3]


def test_updater_add_method():
    update = Updater()
    
    tree = Tree({"foo": None})
    update(tree, "foo+", 1, "/test/source.yaml")
    assert tree["foo"] == 1

    tree = Tree({"foo": None})
    update(tree, "foo+", "1", "/test/source.yaml")
    assert tree["foo"] == "1"

    tree = Tree({"foo": None})
    update(tree, "foo+", (1), "/test/source.yaml")
    assert tree["foo"] == (1)

    tree = Tree({"foo": None})
    update(tree, "foo+", [1], "/test/source.yaml")
    assert tree["foo"] == [1]

    tree = Tree({"foo": ""})
    update(tree, "foo+", "1", "/test/source.yaml")
    assert tree["foo"] == "1"

    update(tree, "foo+", "[2]", "/test/source.yaml")
    assert tree["foo"] == "1 [2]"

    update(tree, "foo+", "3 4", "/test/source.yaml")
    assert tree["foo"] == "1 [2] 3 4"

    tree = Tree({})
    update(tree, "foo+", "1", "/test/source.yaml")
    assert tree["foo"] == "1"

    tree = Tree({"foo": ""})
    update(tree, "foo+", [1], "/test/source.yaml")
    assert tree["foo"] == [1]

    update(tree, "foo+", [2], "/test/source.yaml")
    assert tree["foo"] == [1, 2]

    update(tree, "foo+", 3, "/test/source.yaml")
    assert tree["foo"] == [1, 2, 3]

    update(tree, "foo+", "4", "/test/source.yaml")
    assert tree["foo"] == [1, 2, 3, '4']

    update(tree, "foo+", [5,6] , "/test/source.yaml")
    assert tree["foo"] == [1, 2, 3, '4', 5, 6]


    tree = Tree({"foo": ()})
    update(tree, "foo+", (1), "/test/source.yaml")
    assert tree["foo"] == (1,)

    update(tree, "foo+", (2), "/test/source.yaml")
    assert tree["foo"] == (1, 2)

    update(tree, "foo+", "3 4", "/test/source.yaml")
    assert tree["foo"] == (1, 2, "3 4")

    update(tree, "foo+", [5], "/test/source.yaml")
    assert tree["foo"] == (1, 2, "3 4", 5)

    update(tree, "foo+", ["6","7"], "/test/source.yaml")
    assert tree["foo"] == (1, 2, "3 4", 5, "6", "7")

    update(tree, "foo+", [["8","9"]], "/test/source.yaml")
    assert tree["foo"] == (1, 2, "3 4", 5, "6", "7", ["8","9"])

    update(tree, "foo+", 10, "/test/source.yaml")
    assert tree["foo"] == (1, 2, "3 4", 5, "6", "7", ["8","9"], 10)


    tree = Tree({"foo": []})
    update(tree, "foo+", ">>> [1]", "/test/source.yaml")
    assert tree["foo"] == [1]

    update(tree, "foo+", 2, "/test/source.yaml")
    assert tree["foo"] == [1, 2]

    update(tree, "foo+", (3, "4"), "/test/source.yaml")
    assert tree["foo"] == [1, 2, 3, "4"]


    tree = Tree({"foo": []})
    update(tree, "foo+", 1, "/test/source.yaml")
    assert tree["foo"] == [1]

    update(tree, "foo+", ">>> 2", "/test/source.yaml")
    assert tree["foo"] == [1, 2]

    update(tree, "foo+", ">>> [3, 4]", "/test/source.yaml")
    assert tree["foo"] == [1, 2, 3, 4]

    update(tree, "foo+", ">>> ('5', 6)", "/test/source.yaml")
    assert tree["foo"] == [1, 2, 3, 4, "5", 6]


    tree = Tree({"foo": []})
    update(tree, "foo+", "", "/test/source.yaml")
    assert tree["foo"] == ['']

    tree = Tree({"foo": ""})
    update(tree, "foo+", "first", "/test/source.yaml")
    assert tree["foo"] == "first"
    
    update(tree, "foo+", "second", "/test/source.yaml")
    assert tree["foo"] == "first second"

    update(tree, "foo+", [3], "/test/source.yaml")
    assert tree["foo"] == "first second [3]"
    
    update(tree, "foo+", "%>> 4 and 5", "/test/source.yaml")
    assert tree["foo"] == "first second [3] 4 and 5"


    tree = Tree({"foo": 1})
    update(tree, "foo+", 2, "/test/source.yaml")
    assert tree["foo"] == 3
    
    update(tree, "foo+", ">>> 6", "/test/source.yaml")
    assert tree["foo"] == 9

    update(tree, "foo+", "10", "/test/source.yaml")
    assert tree["foo"] == "9 10"


def test_updater_format_value():
    tree = Tree({"x.a": 1, "x.b": 2})
    update = Updater()
    update(tree, "x.c", "$>> {self[x.a]} {branch[b]}", "/test/source.yaml")
    assert isinstance(tree["x.c"], Promise)
    assert tree["x.c"]() == "1 2"
    tree["x.a"] = "foo"
    tree["x.b"] = "bar"
    assert tree["x.c"]() == "foo bar"


def test_updater_printf_value():
    tree = Tree({"x.a": 1, "x.b": 2})
    update = Updater()
    update(tree, "x.c", "%>> %(x.a)s %(x.b)r", "/test/source.yaml")
    assert isinstance(tree["x.c"], Promise)
    assert tree["x.c"]() == "1 2"
    tree["x.a"] = "foo"
    tree["x.b"] = "bar"
    assert tree["x.c"]() == "foo 'bar'"


def test_updater_eval_value():
    tree = Tree({"x.a": 5.0, "x.b": 2})
    update = Updater(namespace={"floor": math.floor})
    update(tree, "x.c", '>>> floor(self["x.a"] / branch["b"])', "/test/source.yaml")
    assert isinstance(tree["x.c"], Promise)
    assert tree["x.c"]() == 2.0
    tree["x.a"] = 10.0
    tree["x.b"] = 3
    assert tree["x.c"]() == 3.0


def test_updater_required_valeue():
    tree = Tree()
    update = Updater()
    update(tree, "foo", "!!!", "/test/source.yaml")
    update(tree, "bar", "!!! Update me", "/test/source.yaml")

    assert isinstance(tree["foo"], Required)
    assert repr(tree["foo"]) == "Undefined required key <foo>"
    assert isinstance(tree["bar"], Required)
    assert repr(tree["bar"]) == "Undefined required key <bar>: Update me"


def test_update_action_repr():
    action = UpdateAction(Tree(), "foo", "bar", "/test/source.yaml")
    assert repr(action) == "<tree['foo'] = 'bar' from '/test/source.yaml'>"


def test_update_action_promise():
    action = UpdateAction(Tree(), "foo", "bar", "/test/source.yaml")
    promise = action.promise(lambda: int(None))
    with pytest.raises(TypeError) as info:
        promise()
    assert info.value.args[-1] == action


def test_update_action_branch():
    tree = Tree({"x.a": 1, "x.b": 2})
    action = UpdateAction(tree, "x.c", 3, "/test/source.yaml")
    assert action.branch == action.tree["x"]

    action = UpdateAction(tree, "y", 3, "/test/source.yaml")
    assert action.branch == action.tree


def test_update_action_default_update():
    tree = Tree()
    UpdateAction(tree, "foo", "bar", "/test/source.yaml")()
    assert tree == {"foo": "bar"}


def test_update_action_update():
    tree = Tree()
    action = UpdateAction(tree, "foo", "bar", "/test/source.yaml")
    action.update = lambda a: a.tree.setdefault(a.key, a.value)

    action()
    assert tree == {"foo": "bar"}

    action.value = "baz"
    action()
    assert tree == {"foo": "bar"}


def test_promise():
    p = Promise(lambda: 42)
    assert p() == 42


def test_promise_resolve():
    assert Promise.resolve(Promise(lambda: 42)) == 42
    assert Promise.resolve("foo") == "foo"


def test_resolver_proxy():
    tree = Tree({"foo": Promise(lambda: 42), "bar": "baz"})
    tree = ResolverProxy(tree, "/test/source.yaml")
    assert tree["foo"] == 42
    assert tree["bar"] == "baz"
    assert tree["__file__"] == "/test/source.yaml"
    assert tree["__dir__"] == "/test"
    assert set(tree.keys()) == set(["foo", "bar"])

    with pytest.raises(KeyError):
        tree["baz"]


def test_postprocessor_resolve_promise():
    tree = Tree({"foo": Promise(lambda: 42), "bar": "baz"})
    postprocess = PostProcessor()
    postprocess(tree)
    assert tree == {"foo": 42, "bar": "baz"}


def test_postprocessor_check_required():
    tree = Tree({"foo": Required("foo", ""), "bar": Required("bar", "Update me")})
    postprocess = PostProcessor()

    with pytest.raises(ProcessingError) as info:
        postprocess(tree)

    assert info.value.args == (tree["bar"], tree["foo"])
