# flake8: noqa

""" The module provides compatibility layer between Python 2.x and 3.x """

from sys import version_info


if version_info[0] == 2:                                    # pragma: nocover
    string = basestring
    unicode = unicode
else:                                                       # pragma: nocover
    string = str
    unicode = str
