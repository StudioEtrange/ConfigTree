import os
import pkg_resources

from .tree import Tree, flatten


parsers = {}
for entry in pkg_resources.iter_entry_points('configtree.parsers'):
    try:
        parsers[entry.name] = entry.load()
    except ImportError as e:
        #raise
        pass


def load(path, postprocess=None):
    result = Tree()
    if os.path.isfile(path):
        result.update(load_file(path))
    else:
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                print filepath
                result.update(load_file(filepath))
    if postprocess:
        postprocess(result)
    return result


def load_file(path):
    ext = os.path.splitext(path)[1]
    with open(path) as f:
        parse = parsers[ext]
        return flatten(parse(f))
