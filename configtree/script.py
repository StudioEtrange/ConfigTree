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
    formats = '|'.join(sorted(conv.map.keys()))

    parser = argparse.ArgumentParser(
        description='Load and convert configuration tree'
    )
    parser.add_argument(
        'path', nargs='?', default=os.getcwd(),
        help='path to configuration tree (default: current directory)'
    )
    parser.add_argument(
        # Do not use ``choices`` to be able to use converters
        # defined within ``loaderconf.py``
        '-f', '--format', default='json', required=False,
        help='output format [%s] (default: json)' % formats
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

    # Fail fast, if invalid format is given
    try:
        converter = conv.map[args.format]
    except KeyError:
        raise ValueError('Unsupportable output format "%s"' % args.format)

    tree = load(
        args.path,
        walk=conf.get('walk'),
        update=conf.get('update'),
        postprocess=conf.get('postprocess'),
        tree=conf.get('tree')
    )
    if args.branch is not None:
        tree = tree[args.branch]
    stdout.write(converter(tree))
    stdout.write(os.linesep)
