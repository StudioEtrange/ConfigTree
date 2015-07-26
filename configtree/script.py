"""
The module provides a shell script which loads configuration tree
and convert it into various formats.

"""

from __future__ import print_function

import os
import sys
import argparse

from . import conv, formatter
from .loader import Loader, load, loaderconf


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

    loader = loaderconf(args.path)
    # Fail fast, if invalid format is given
    try:
        converter = conv.map[args.format]
    except KeyError:
        raise ValueError('Unsupportable output format "%s"' % args.format)

    tree = load(args.path, **loader)
    if args.branch is not None:
        tree = tree[args.branch]
    stdout.write(converter(tree))
    stdout.write(os.linesep)


def ctdump(argv=None, stdout=None):
    # At first we need to import ``loaderconf.py`` if it exists,
    # because there might be a custom formatter defined.
    # So we need to parse ``-p`` or ``--path`` argument.
    # Import itself will be done by :meth:`Loader.fromconf`.
    default_path = os.getcwd()
    path_parser = argparse.ArgumentParser(add_help=False)
    path_parser.add_argument('-p', '--path', default=default_path)
    args, _ = path_parser.parse_known_args(argv)
    load = Loader.fromconf(args.path)

    # Now we create main argument parser, that parses all passed arguments
    # and generates help message.
    parser = argparse.ArgumentParser(
        description='Load and convert configuration tree',
        add_help=False
    )
    # Standard auto-generated usage is a bit messy, so we build our own.
    parser.usage = ''
    prog = '\n  %(prog)s'

    def format_usage(option_group):
        f = parser._get_formatter()
        return f._format_actions_usage(option_group._group_actions, [])

    # Add common arguments and options
    formats = sorted(formatter.map.keys())
    required_options = parser.add_argument_group(title='required arguments')
    required_options.add_argument(
        'format', metavar='<format>', choices=formats,
        help='output format: %(choices)s',
    )

    common_options = parser.add_argument_group(title='common options')
    common_options.add_argument(
        '-k', '--key', required=False, metavar='<key>',
        help='branch of tree to be converted'
    )
    common_options.add_argument(
        '-p', '--path', required=False, default=default_path, metavar='<path>',
        help='path to load (default: current directory)'
    )

    parser.usage += '{} {} {} <formatter options>'.format(
        prog,
        format_usage(required_options),
        format_usage(common_options),
    )

    # Add formatter specific options that might be defined within
    # ``__options__`` attribute of formatter function.
    formatter_options = {}
    for name in formats:
        parser.usage += '{} {} <common options>'.format(prog, name)
        if hasattr(formatter.map[name], '__options__'):
            formatter_options[name] = parser.add_argument_group(
                '%s formatter options' % name
            )
            for option, params in formatter.map[name].__options__:
                option = '--{}-{}'.format(name, option.replace('_', '-'))
                formatter_options[name].add_argument(option, **params)
            parser.usage += ' ' + format_usage(formatter_options[name])

    # Add options for getting help and version
    info_options = parser.add_argument_group(title='getting info')
    info_options.add_argument(
        '-h', '--help', action='help',
        help='show this help message and exit'
    )
    info_options.add_argument(
        '--version', action='version', version='%(prog)s 0.4'
    )
    parser.usage += '{} --help'.format(prog)
    parser.usage += '{} --version'.format(prog)

    # Parse arguments and load tree
    args = vars(parser.parse_args(argv))
    tree = load(args['path'])
    if args['key'] is not None:
        tree = tree[args['key']]

    # Exract formatter specific arguments from parsed ones.
    formatter_args = {}
    if args['format'] in formatter_options:
        formatter_args = dict(
            (option.dest[len(args['format']) + 1:], args[option.dest])
            for option in formatter_options[args['format']]._group_actions
        )

    # Format tree and print result
    print(formatter.map[args['format']](tree, **formatter_args), file=stdout)
