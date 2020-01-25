import sys


if sys.version_info[0] > 2:  # pragma: no cover
    chars = (str, bytes)
    string = str
    basestr = str
else:  # pragma: no cover
    chars = (unicode, bytes)  # noqa
    string = unicode  # noqa
    basestr = basestring  # noqa
