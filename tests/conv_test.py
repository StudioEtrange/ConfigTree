from os import linesep

from nose import tools

from configtree import conv
from configtree.tree import Tree


t = Tree({
    'a.x': 1,
    'a.y': 'Testing "json"',
    'a.z': "Testing 'shell'",
    'none': None,
})


def json_test():
    result = conv.to_json(t)
    result = [line.rstrip() for line in result.split(linesep)]
    tools.eq_(result, [
        '{',
        '    "a.x": 1,',
        '    "a.y": "Testing \\"json\\"",',
        '    "a.z": "Testing \'shell\'",',
        '    "none": null',
        '}',
    ])


def rare_json_test():
    result = conv.to_rare_json(t)
    result = [line.rstrip() for line in result.split(linesep)]
    tools.eq_(result, [
        '{',
        '    "a": {',
        '        "x": 1,',
        '        "y": "Testing \\"json\\"",',
        '        "z": "Testing \'shell\'"',
        '    },',
        '    "none": null',
        '}',
    ])


def shell_test():
    result = conv.to_shell(t)
    result = [line.rstrip() for line in result.split(linesep)]
    tools.eq_(result, [
        "A_X='1'",
        "A_Y='Testing \"json\"'",
        "A_Z='Testing \\'shell\\''",
        "NONE=''",
    ])


def map_test():
    tools.eq_(conv.map['json'], conv.to_json)
    tools.eq_(conv.map['rare_json'], conv.to_rare_json)
    tools.eq_(conv.map['shell'], conv.to_shell)
