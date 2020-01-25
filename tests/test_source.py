import os

from configtree import source
from configtree.tree import flatten


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(data_dir, "data", "source")


def test_json():
    with open(os.path.join(data_dir, "test.json")) as f:
        result = source.from_json(f)
        result = list(flatten(result))
        assert result == [("a", 1), ("b", 2), ("c.x", 1), ("c.y", 2), ("c.z", 3)]


def test_yaml():
    with open(os.path.join(data_dir, "test.yaml")) as f:
        result = source.from_yaml(f)
        result = list(flatten(result))
        assert result == [("a", 1), ("b", 2), ("c.x", 1), ("c.y", 2), ("c.z", 3)]


def test_map():
    assert source.map[".yml"] == source.from_yaml
    assert source.map[".yaml"] == source.from_yaml
    assert source.map[".json"] == source.from_json
