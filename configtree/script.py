"""
The module provides a shell script which loads configuration tree
and convert it into various formats

"""

import os
import sys
import argparse

from . import conv
from .loader import Loader


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='Load and convert configuration tree'
    )
    parser.add_argument(
        'path', nargs='?', default=os.getcwdu(),
        help='path to configuration tree (default: current directory)'
    )
    parser.add_argument(
        '-f', '--format', default='json', required=False,
        choices=conv.map.keys(),
        help='output format (default: json)'
    )
    parser.add_argument(
        '-b', '--branch', required=False,
        help='branch of tree, which should be converted'
    )
    parser.add_argument(
        '-s', '--settings', nargs='*', default=[],
        help='loader settings'
    )
    args = parser.parse_args(argv)

    settings = {}
    for arg in args.settings:
        key, value = arg.split('=')
        settings[key] = value

    load = Loader.from_settings(settings, args.path)
    tree = load(args.path)
    if args.branch is not None:
        tree = tree[args.branch]
    print(conv.map[args.format](tree))
