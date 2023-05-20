
# https://stackoverflow.com/questions/39553008/how-to-read-a-python-tuple-using-pyyaml
# https://stackoverflow.com/questions/9169025/how-can-i-add-a-python-tuple-to-a-yaml-file-using-pyyaml/9169553#9169553
# https://itecnote.com/tecnote/python-how-to-add-a-python-tuple-to-a-yaml-file-using-pyyaml/
# https://github.com/speechbrain/HyperPyYAML/blob/main/hyperpyyaml/core.py
# https://stackoverflow.com/questions/73749807/implicit-resolvers-and-robust-representers-for-human-friendly-tuple-and-np-array
# https://github.com/yaml/pyyaml/blob/957ae4d495cf8fcb5475c6c2f1bce801096b68a5/lib/yaml/representer.py
from configtree import *
from configtree import source
from configtree.source import *
from configtree.source import OrderedDictYAMLLoader

import re
import yaml
import sys
import ast

if sys.version_info[0] > 2:  # pragma: no cover
     chars = (str, bytes)
     string = str
     basestr = str
else:  # pragma: no cover
     chars = (unicode, bytes)  # noqa
     string = unicode  # noqa
     basestr = basestring  # noqa

try:
     from collections.abc import *  # noqa
except ImportError:  # pragma: no cover
     from collections import *  # noqa

f='/home/nomorgan/workspace/mambo/test/env-tango/global.yaml'
source.map['.yaml'](open(f))
yaml.load(open(f),OrderedDictYAMLLoader)


# ---------------------
# debug
for event in yaml.parse("[42, {pi: 3.14, e: 2.72}]", yaml.Loader):
	print(event)



# ---------------------
tuple_pattern = re.compile(r"^\(.*\)$")
OrderedDictYAMLLoader.add_constructor('tag:yaml.org,2002:python/tuple', tuple_constructor)
OrderedDictYAMLLoader.add_implicit_resolver("!!python/tuple", tuple_pattern, first="(")

# -------------------------
tuple_pattern = re.compile(r"^\(.*\)$")
def tuple_constructor(loader, node):
    # Load the sequence of values from the YAML node
    values = loader.construct_sequence(node)
    #values = loader.construct_object(node)
    # Return a tuple constructed from the sequence
    return tuple(values)

OrderedDictYAMLLoader.add_constructor(tag="!tuple", constructor=tuple_constructor)
OrderedDictYAMLLoader.add_implicit_resolver("!tuple", tuple_pattern, first="(")

for event in yaml.parse("(2, [3,4, [1,1] ], [5, (10,11)], (7,8) )", OrderedDictYAMLLoader):
	print(event)
# -------------------------
import ast
tuple_pattern = re.compile(r"^\(.*\)$")
def tuple_constructor(loader, node):
    return ast.literal_eval(loader.construct_scalar(node))
    #return eval(loader.construct_scalar(node))

OrderedDictYAMLLoader.add_constructor(tag="!tuple", constructor=tuple_constructor)
OrderedDictYAMLLoader.add_implicit_resolver("!tuple", tuple_pattern, first="(")

# -------------------------
tuple_pattern = re.compile(r"^\(.*\)$")
def _make_tuple(loader, node):
    """Parse scalar node as a list, convert to tuple"""
    tuple_string = loader.construct_scalar(node) 
    list_string = "[" + tuple_string[1:-1] + "]"
    parsed_list = yaml.load(list_string, Loader=OrderedDictYAMLLoader)
    return tuple(parsed_list)
OrderedDictYAMLLoader.add_constructor(tag="!tuple", constructor=_make_tuple)
OrderedDictYAMLLoader.add_implicit_resolver("!tuple", tuple_pattern, first="(")


# -----------------------------
# BEST ALTERNATIVE
import ast

def get_marked_buffer(start_mark, end_mark):
    if start_mark.buffer is None:
        return None
    start = start_mark.pointer
    while start > 0 and start_mark.buffer[start-1] not in '\0\r\n\x85\u2028\u2029':
        start -= 1
    end = end_mark.pointer
    while end < len(end_mark.buffer) and end_mark.buffer[end] not in '\0\r\n\x85\u2028\u2029':
        end += 1
    return start_mark.buffer[start:end]

tuple_pattern  = re.compile("^(?:\((?:.|\n|\r)*,?(?:.|\n|\r)*\){1}(?: |\n|\r)*$)")
list_pattern  = re.compile("^(?:\[(?:.|\n|\r)*,?(?:.|\n|\r)*\]{1}(?: |\n|\r)*$)")

# original configtree have a bug with s="[(4,[7,8])]"

class OrderedDictYAMLLoader2(OrderedDictYAMLLoader):
    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)
        self.add_constructor(tag="!!!tuple", constructor=type(self).tuple_constructor)
        self.add_implicit_resolver("!!!tuple", tuple_pattern, first=list("("))
        self.add_constructor('tag:yaml.org,2002:seq', type(self).list_constructor)
        #self.add_constructor('!!!list',type(self).list_constructor)
        #self.add_implicit_resolver('!!!list', list_pattern, first=list("["))
    def tuple_constructor(self, node):
        tuple_string = self.construct_scalar(node)
        # Consider string '(1)' as a tuple with onlye one element. So add by default a coma to force list type (1,)
        try:
            return_value = ast.literal_eval(tuple_string[:-1] + ",)")
        except SyntaxError as ex:
            return_value = ast.literal_eval(tuple_string)
        return return_value
    def list_constructor(self, node):
        buffer = get_marked_buffer(node.start_mark, node.end_mark)
        if list_pattern.match(buffer):  
            data = []
            yield data
            data.extend(ast.literal_eval(buffer))
        else:
            self.construct_yaml_seq(node)



yaml.load("[3, 4, [1,1],(5, 3)]", OrderedDictYAMLLoader2)

yaml.load(open(f),OrderedDictYAMLLoader2)

yaml.load("(2, [3,4, [1,1] ], [5, (10,11)], (7,8) )", OrderedDictYAMLLoader2)
yaml.load("(2,)", OrderedDictYAMLLoader2)
yaml.load("(2)", OrderedDictYAMLLoader2)


yaml.load("[3, 4, [1,1],(5, 3)]", OrderedDictYAMLLoader2)

for event in yaml.parse("[3, 4, [1,1], (5, 3)]", OrderedDictYAMLLoader2):
    print(event)