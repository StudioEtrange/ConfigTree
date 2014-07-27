# flake8: noqa

""" The module provides compatibility layer between Python 2.x and 3.x """

from sys import version_info

try:
    # Python 2.7, Python 3.x
    from collections import OrderedDict
except ImportError:
    # Python 2.6
    from ordereddict import OrderedDict

if version_info[0] == 2 and version_info[1] < 7:
    import simplejson as json
else:
    import json

if version_info[0] == 2:
    string = basestring
    unicode = unicode
else:
    string = str
    unicode = str
