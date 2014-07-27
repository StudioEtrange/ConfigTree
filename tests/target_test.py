from os import linesep

from nose import tools

from configtree import target
from configtree.tree import Tree


t = Tree({
    'a.x': 1,
    'a.y': 'Testing "json"',
    'a.z': "Testing 'bash'",
})


def json_test():
    result = target.output_json(t)
    result = [line.rstrip() for line in result.split(linesep)]
    tools.eq_(result, [
        '{',
        '    "a.x": 1,',
        '    "a.y": "Testing \\"json\\"",',
        '    "a.z": "Testing \'bash\'"',
        '}',
    ])


def bash_test():
    result = target.output_bash(t)
    result = [line.rstrip() for line in result.split(linesep)]
    tools.eq_(result, [
        "A_X='1'",
        "A_Y='Testing \"json\"'",
        "A_Z='Testing \\'bash\\''",
    ])

def map_test():
    tools.eq_(target.map['json'], target.output_json)
    tools.eq_(target.map['bash'], target.output_bash)
