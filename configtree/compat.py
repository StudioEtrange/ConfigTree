from sys import version_info


if version_info[0] == 3:
    string = str
else:
    string = basestring     # NOQA
