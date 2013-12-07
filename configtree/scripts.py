import os
import sys
import argparse

from . import target
from . import loader


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
        choices=target.map.keys(),
        help='output format (default: json)'
    )
    parser.add_argument(
        '-b', '--branch', required=False,
        help='branch of tree, which should be processed'
    )
    args = parser.parse_args(argv)

    tree = loader.load(args.path)
    if args.branch is not None:
        tree = tree[args.branch]
    print(target.map[args.format](tree))

