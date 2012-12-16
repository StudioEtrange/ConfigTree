""" The module provides compatibility layer between Python 2.x and 3.x """

from sys import version_info

try:
    # Python 2.7, Python 3.x
    from collections import OrderedDict     # NOQA
except ImportError:
    # Python 2.6
    from ordereddict import OrderedDict     # NOQA

if version_info[0] == 2 and version_info[1] < 7:
    import simplejson as json               # NOQA
else:
    import json                             # NOQA

if version_info[0] == 3:
    string = str
else:
    string = basestring                     # NOQA
