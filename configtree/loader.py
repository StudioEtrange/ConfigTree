import os
import re
import fnmatch
import pkg_resources

from .tree import Tree, flatten


parsers = {}
for entry in pkg_resources.iter_entry_points('configtree.parsers'):
    try:
        parsers[entry.name] = entry.load()
    except ImportError as e:
        pass


def load(path, postprocess=None, filter=None):
    result = Tree()
    filter = filter or (lambda x: True)
    if os.path.isfile(path):
        result.update(_load_file(path))
    else:
        for curpath, dirnames, filenames in os.walk(path):
            for dirname in dirnames[:]:
                dirpath = os.path.join(curpath, dirname)
                relpath = os.path.relpath(dirpath, path)
                if not filter(relpath):
                    dirnames.remove(dirname)
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                filepath = os.path.join(curpath, filename)
                relpath = os.path.relpath(filepath, path)
                if filter(relpath):
                    result.update(_load_file(filepath))
    if postprocess:
        postprocess(result)
    return result


def ignore(*args):
    return _filter(*args, accept=False)


def accept(*args):
    return _filter(*args, accept=True)


def _filter(*args, **kw):
    accept = kw['accept']
    patterns = []
    for pattern in args:
        pattern = fnmatch.translate(pattern)
        pattern = re.compile(pattern, re.IGNORECASE)
        patterns.append(pattern)

    def filter_path(path):
        for pattern in patterns:
            if pattern.match(path):
                return accept
        return not accept

    return filter_path


def _load_file(path):
    ext = os.path.splitext(path)[1]
    with open(path) as f:
        parse = parsers[ext]
        return flatten(parse(f))
