from nose import tools

from configtree import target
from configtree.tree import Tree


t = Tree({
    'a.x': 1,
})


def json_test():
    result = target.output_json(t)
    result = [line.rstrip() for line in result.split('\n')]
    tools.eq_(result, [
        '{',
        '    "a.x": 1',
        '}',
    ])


def bash_test():
    result = target.output_bash(t)
    tools.eq_(result, 'export A_X=1')


def map_test():
    tools.eq_(target.map['json'], target.output_json)
    tools.eq_(target.map['bash'], target.output_bash)
