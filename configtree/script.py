"""
The module provides a shell script which loads configuration tree
and convert it into various formats.

"""

import os
import sys
import argparse

from . import conv
from .loader import load


def main(argv=None, stdout=None):
    argv = argv or sys.argv[1:]
    stdout = stdout or sys.stdout

    parser = argparse.ArgumentParser(
        description='Load and convert configuration tree'
    )
    parser.add_argument(
        'path', nargs='?', default=os.getcwd(),
        help='path to configuration tree (default: current directory)'
    )
    parser.add_argument(
        '-f', '--format', default='json', required=False,
        choices=list(sorted(conv.map.keys())),
        help='output format (default: json)'
    )
    parser.add_argument(
        '-b', '--branch', required=False,
        help='branch of tree, which should be converted'
    )
    args = parser.parse_args(argv)

    sys.path.insert(0, args.path)
    try:
        import loaderconf
        conf = loaderconf.__dict__
    except ImportError:
        conf = {}

    tree = load(
        args.path,
        walk=conf.get('walk'),
        update=conf.get('update'),
        postprocess=conf.get('postprocess'),
        tree=conf.get('tree')
    )
    if args.branch is not None:
        tree = tree[args.branch]
    stdout.write(conv.map[args.format](tree).encode('utf-8'))
    stdout.write('\n'.encode('utf-8'))
