from __future__ import print_function

import os
import sys
import argparse
import textwrap
import logging

from . import conv, formatter
from .loader import Loader, ProcessingError, UpdateAction, load, loaderconf


def ctdump(argv=None, stdout=None, stderr=None):
    """
    Shell script to load and format :class:`configtree.tree.Tree` objects.

    Run the command bellow in your console to get help.

    ..  code-block:: bash

        $ ctdump --help

    """
    logger = setup_logger(stderr)

    # At first we need to import ``loaderconf.py`` if it exists,
    # because there might be a custom formatter defined.
    # So we need to parse ``-p`` or ``--path`` argument.
    # Import itself will be done by :meth:`Loader.fromconf`.
    default_path = os.getcwd()
    path_parser = argparse.ArgumentParser(add_help=False)
    path_parser.add_argument('-p', '--path', default=default_path)
    args, _ = path_parser.parse_known_args(argv)

    loader_error = None
    try:
        load = Loader.fromconf(args.path)
    except Exception as e:
        # We should not crash here, because a user might ask to print help
        # or version number.
        logger.error('Failed to create loader.  Check your loaderconf.py')
        loader_error = e

    # Now we create main argument parser, that parses all passed arguments
    # and generates help message.
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
        dump configuration tree using specified format

          Configuration tree is loaded from current directory or
          from the directory specified by <path>.

          If loaderconf.py file exists under the <path> directory,
          it will be used to constuct the loader.  It is also a good place
          to define custom formatters and custom readers of source files.

          If branch <key> is specified, only the branch of tree will be dumped.

        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        '-b', '--branch', metavar='<key>',
        help='branch of tree to be dumped'
    )
    common_options.add_argument(
        '-p', '--path', default=default_path, metavar='<path>',
        help='path to configuration tree'
    )
    common_options.add_argument(
        '-v', '--verbose', action='store_true',
        help='print debug output'
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
                # Option name is prefixed by formatter name
                option = '--{}-{}'.format(name, option.replace('_', '-'))
                formatter_options[name].add_argument(option, **params)
            parser.usage += ' ' + format_usage(formatter_options[name])

    # Add options for getting help and version
    info_options = parser.add_argument_group(title='getting info')
    info_options.add_argument(
        '-h', '--help', action='help',
        help='show this help message and exit'
    )
    from . import __version__
    info_options.add_argument(
        '--version', action='version', version=__version__
    )
    parser.usage += '{} --help'.format(prog)
    parser.usage += '{} --version'.format(prog)

    # Parse arguments and load tree
    args = vars(parser.parse_args(argv))

    if loader_error:
        raise loader_error
    if args['verbose']:
        logger.setLevel(logging.INFO)

    logger.info('Loading tree')
    try:
        tree = load(args['path'])
    except ProcessingError as e:
        for error in e.args:
            logger.error('%s', error)
        return 1
    except Exception as e:
        if (e.args and isinstance(e.args[-1], UpdateAction)):
            logger.error('%s: %r', e.__class__.__name__, e.args)
            return 1
        raise                                   # pragma: no cover
    if args['branch'] is not None:
        try:
            tree = tree[args['branch']]
        except KeyError as e:
            logger.error('Branch <%s> does not exist', args['branch'])
            return 1

    # Extract formatter specific arguments from parsed ones
    formatter_args = {}
    if args['format'] in formatter_options:
        prefix_len = len(args['format']) + 1
        formatter_args = dict(
            # Strip formatter name prefix from argument name
            (option.dest[prefix_len:], args[option.dest])
            for option in formatter_options[args['format']]._group_actions
        )

    # Format tree and print result
    logger.info('Formatting result')
    result = formatter.map[args['format']](tree, **formatter_args)
    print(result, file=stdout)


def setup_logger(stderr=None):      # pragma: no cover
    """
    Helper function that sets up a logger for :func:`ctdump` and :func:`main`

    """
    from . import logger
    if stderr is False:
        return logger

    handler = logging.StreamHandler(stderr)
    handler.setFormatter(
        logging.Formatter('%(name)s [%(levelname)s]: %(message)s')
    )
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    return logger


###############################################################################
# Deprecated features
##


def main(argv=None, stdout=None, stderr=None):
    """
    ..  warning:: Deprecated in favor of :func:`ctdump`

    Shell script to load and format :class:`configtree.tree.Tree` objects.

    Run the command bellow in your console to get help.

    ..  code-block:: bash

        $ configtree --help

    """
    logger = setup_logger(stderr)
    logger.warning(
        '``configtree`` command is deprecated in favor of ``ctdump``'
    )

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
