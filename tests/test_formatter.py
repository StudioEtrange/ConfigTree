from os import linesep

from configtree import formatter
from configtree.tree import Tree


t = Tree(
    {
        "a.x": 1,
        "a.y": 'Testing "json"',
        "a.z": "Testing 'shell'",
        "list": ['Testing "json"', "Testing 'shell'"],
        "none": None,
        "bool": True,
    }
)


def test_json():
    result = formatter.to_json(t, indent=4, sort=True)
    result = [line.rstrip() for line in result.split(linesep)]
    assert result == [
        "{",
        '    "a.x": 1,',
        '    "a.y": "Testing \\"json\\"",',
        '    "a.z": "Testing \'shell\'",',
        '    "bool": true,',
        '    "list": [',
        '        "Testing \\"json\\"",',
        "        \"Testing 'shell'\"",
        "    ],",
        '    "none": null',
        "}",
    ]

    result = formatter.to_json(t, indent=4, sort=True, rare=True)
    result = [line.rstrip() for line in result.split(linesep)]
    assert result == [
        "{",
        '    "a": {',
        '        "x": 1,',
        '        "y": "Testing \\"json\\"",',
        '        "z": "Testing \'shell\'"',
        "    },",
        '    "bool": true,',
        '    "list": [',
        '        "Testing \\"json\\"",',
        "        \"Testing 'shell'\"",
        "    ],",
        '    "none": null',
        "}",
    ]


def test_shell():
    result = formatter.to_shell(
        t, prefix="local ", seq_sep=":", sort=True, capitalize=True
    )
    result = [line.rstrip() for line in result.split(linesep)]
    assert result == [
        "local A_X=1",
        "local A_Y='Testing \"json\"'",
        "local A_Z='Testing \\'shell\\''",
        "local BOOL=true",
        "local LIST='Testing \"json\":Testing \\'shell\\''",
        "local NONE=''",
    ]

    result = formatter.to_shell(t["a.x"], prefix="local X=")
    assert result == "local X=1"


def test_map():
    assert formatter.map["json"] == formatter.to_json
    assert formatter.map["shell"] == formatter.to_shell
