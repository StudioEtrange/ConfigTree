from os import linesep

from nose import tools

from configtree import conv
from configtree.tree import Tree


t = Tree({
    'a.x': 1,
    'a.y': 'Testing "json"',
    'a.z': "Testing 'bash'",
    'none': None,
})


def json_test():
    result = conv.to_json(t)
    result = [line.rstrip() for line in result.split(linesep)]
    tools.eq_(result, [
        '{',
        '    "a.x": 1,',
        '    "a.y": "Testing \\"json\\"",',
        '    "a.z": "Testing \'bash\'",',
        '    "none": null',
        '}',
    ])


def bash_test():
    result = conv.to_bash(t)
    result = [line.rstrip() for line in result.split(linesep)]
    tools.eq_(result, [
        "A_X='1'",
        "A_Y='Testing \"json\"'",
        "A_Z='Testing \\'bash\\''",
        "NONE=''",
    ])


def map_test():
    tools.eq_(conv.map['json'], conv.to_json)
    tools.eq_(conv.map['bash'], conv.to_bash)
