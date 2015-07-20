import math
import os
import sys
from nose import tools

from configtree.loader import (
    load, loaderconf, make_walk, make_update,
    Pipeline, worker,
    Walker, File,
    Updater, UpdateAction, Promise, ResolverProxy, resolve, Required,
    PostProcessor, ProcessingError
)
from configtree.tree import Tree


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(data_dir, 'data', 'loader')


def teardown_func():
    try:
        sys.path.remove(data_dir)
    except ValueError:
        pass
    try:
        del sys.modules['loaderconf']
    except KeyError:
        pass


def walk_test():
    walk = make_walk()
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    tools.eq_(files, [
        os.path.join('default', 'a.json'),
        os.path.join('default', 'b.yaml'),
        os.path.join('default', 'subsystem', 'a.yaml'),
        os.path.join('default', 'subsystem', 'b.yaml'),
        os.path.join('final-common', 'c.yaml'),
        'final-common.yaml',
    ])

    walk = make_walk(env='y')
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    tools.eq_(files, [
        os.path.join('default', 'a.json'),
        os.path.join('default', 'b.yaml'),
        os.path.join('default', 'subsystem', 'a.yaml'),
        os.path.join('default', 'subsystem', 'b.yaml'),
        'env-y.yaml',
        os.path.join('final-common', 'c.yaml'),
        'final-common.yaml',
    ])

    walk = make_walk(env='x')
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    tools.eq_(files, [
        os.path.join('default', 'a.json'),
        os.path.join('default', 'b.yaml'),
        os.path.join('default', 'subsystem', 'a.yaml'),
        os.path.join('default', 'subsystem', 'b.yaml'),
        os.path.join('env-x', 'a.yaml'),
        os.path.join('final-common', 'c.yaml'),
        'final-common.yaml',
    ])

    walk = make_walk(env='x.xx')
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    tools.eq_(files, [
        os.path.join('default', 'a.json'),
        os.path.join('default', 'b.yaml'),
        os.path.join('default', 'subsystem', 'a.yaml'),
        os.path.join('default', 'subsystem', 'b.yaml'),
        os.path.join('env-x', 'a.yaml'),
        os.path.join('env-x', 'env-xx', 'b.yaml'),
        os.path.join('final-common', 'c.yaml'),
        'final-common.yaml',
    ])


def update_test():
    tree = Tree({'a.b.x': 1})

    update = make_update()
    update(tree, 'a.b.y', 2)
    tools.eq_(tree['a.b.y'], 2)

    update(tree, 'a.b.z', '>>> self["a.b.x"] + branch["y"]')
    tools.eq_(tree['a.b.z'], 3)

    update(tree, 'a.b.l?', [])
    tools.eq_(tree['a.b.l'], [])

    update(tree, 'a.b.l?', [1, 2, 3])
    tools.eq_(tree['a.b.l'], [])

    update(tree, 'a.b.l#extend', [4, 5, 6])
    tools.eq_(tree['a.b.l'], [4, 5, 6])

    update(tree, 'a.b.c', '$>> x = {self[a.b.x]}, y = {branch[y]}')
    tools.eq_(tree['a.b.c'], 'x = 1, y = 2')

    update = make_update(namespace={'floor': math.floor})
    update(tree, 'z', '>>> int(floor(3.8))')
    tools.eq_(tree['z'], 3)


def load_test():
    update = make_update(namespace={'floor': math.floor})
    result = load(data_dir, update=update)
    tools.eq_(result, {
        'a.x': 1,
        'a.y': 2,
        'b.x': 10,
        'b.y': 20,
        'subsystem.a.x': 101,
        'subsystem.a.y': 102,
        'subsystem.b.x': 110,
        'subsystem.b.y': 120,
        'c.x': 10,
        'c.y': 20,
        'c.z': 30,
    })

    walk = make_walk(env='y')
    result = load(data_dir, walk=walk, update=update)
    tools.eq_(result, {
        'a.x': 1,
        'a.y': 2,
        'b.x': 10,
        'b.y': 20,
        'subsystem.a.x': 101,
        'subsystem.a.y': 102,
        'subsystem.b.x': 110,
        'subsystem.b.y': 120,
        'a.b.x': 1,
        'a.b.y': 2,
        'a.b.z': 3,
        'a.b.c': 'x = 1, y = 2',
        'a.b.l': [4, 5, 6],
        'z': 3,
        'path': os.path.join(data_dir, 'somepath'),
        'here': os.path.join(data_dir, 'env-y.yaml'),
        'c.x': 10,
        'c.y': 20,
        'c.z': 30,
    })


def postprocess_test():

    def postprocess(tree):
        for key, value in tree.items():
            tree[key] = value + 1000

    update = make_update(namespace={'floor': math.floor})
    result = load(data_dir, update=update, postprocess=postprocess)
    tools.eq_(result, {
        'a.x': 1001,
        'a.y': 1002,
        'b.x': 1010,
        'b.y': 1020,
        'subsystem.a.x': 1101,
        'subsystem.a.y': 1102,
        'subsystem.b.x': 1110,
        'subsystem.b.y': 1120,
        'c.x': 1010,
        'c.y': 1020,
        'c.z': 1030,
    })


@tools.with_setup(teardown=teardown_func)
def loader_conf_test():
    conf = loaderconf(os.path.dirname(data_dir))
    tools.eq_(conf, {})

    conf = loaderconf(data_dir)
    tools.eq_(conf, {
        'walk': 'walk',
        'update': 'update',
        'postprocess': 'postprocess',
        'tree': 'tree',
    })


def pipeline_test():

    class Test(Pipeline):

        @worker(1)
        def first(self):
            pass

        @worker(2, enabled=False)
        def second(self):
            pass

        @worker(3)
        def third(self):
            pass

    t = Test()
    tools.eq_(t.__pipeline__, [t.first, t.third])


def updater_set_default_test():
    tree = Tree({'foo': 'bar'})
    update = Updater()
    update(tree, 'foo?', 'baz', '/test/source.yaml')
    tools.eq_(tree, {'foo': 'bar'})

    update(tree, 'bar?', 'baz', '/test/source.yaml')
    tools.eq_(tree, {'foo': 'bar', 'bar': 'baz'})


def file_test():
    f = File(data_dir, 'default', {})
    tools.eq_(f.path, data_dir)
    tools.eq_(f.name, 'default')
    tools.eq_(f.fullpath, os.path.join(data_dir, 'default'))
    tools.eq_(f.isdir, True)
    tools.eq_(f.isfile, False)
    tools.eq_(f.cleanname, 'default')
    tools.eq_(f.ext, '')

    f = File(data_dir, 'env-y.yaml', {})
    tools.eq_(f.path, data_dir)
    tools.eq_(f.name, 'env-y.yaml')
    tools.eq_(f.fullpath, os.path.join(data_dir, 'env-y.yaml'))
    tools.eq_(f.isdir, False)
    tools.eq_(f.isfile, True)
    tools.eq_(f.cleanname, 'env-y')
    tools.eq_(f.ext, '.yaml')

    f1 = File(data_dir, 'env-y.yaml', {})
    f2 = File(data_dir, 'final-common.yaml', {})
    tools.eq_(f1 < f2, True)


def updater_call_method_test():
    tree = Tree({'foo': []})
    update = Updater()
    update(tree, 'foo#append', 1, '/test/source.yaml')
    tools.eq_(tree['foo'], [1])

    update(tree, 'foo#append', '>>> 2', '/test/source.yaml')
    tools.ok_(isinstance(tree['foo'], Promise))
    tools.ok_(tree['foo'](), [1, 2])

    update(tree, 'foo#append', 3, '/test/source.yaml')
    tools.ok_(isinstance(tree['foo'], Promise))
    tools.ok_(tree['foo'](), [1, 2, 3])


def updater_format_value_test():
    tree = Tree({'x.a': 1, 'x.b': 2})
    update = Updater()
    update(tree, 'x.c', '$>> {self[x.a]} {branch[b]}', '/test/source.yaml')
    tools.ok_(isinstance(tree['x.c'], Promise))
    tools.ok_(tree['x.c'](), '1 2')
    tree['x.a'] = 'foo'
    tree['x.b'] = 'bar'
    tools.ok_(tree['x.c'](), 'foo bar')


def updater_printf_value_test():
    tree = Tree({'x.a': 1, 'x.b': 2})
    update = Updater()
    update(tree, 'x.c', '%>> %(x.a)s %(x.b)r', '/test/source.yaml')
    tools.ok_(isinstance(tree['x.c'], Promise))
    tools.ok_(tree['x.c'](), '1 2')
    tree['x.a'] = 'foo'
    tree['x.b'] = 'bar'
    tools.ok_(tree['x.c'](), "foo 'bar'")


def updater_eval_value_test():
    tree = Tree({'x.a': 5.0, 'x.b': 2})
    update = Updater(namespace={'floor': math.floor})
    update(
        tree, 'x.c', '>>> floor(self["x.a"] / branch["b"])',
        '/test/source.yaml',
    )
    tools.ok_(isinstance(tree['x.c'], Promise))
    tools.ok_(tree['x.c'](), 2.0)
    tree['x.a'] = 10.0
    tree['x.b'] = 3
    tools.ok_(tree['x.c'](), 3.0)


def updater_required_valeue_test():
    tree = Tree()
    update = Updater()
    update(tree, 'foo', '!!!', '/test/source.yaml')
    update(tree, 'bar', '!!! Update me', '/test/source.yaml')

    tools.ok_(isinstance(tree['foo'], Required))
    tools.eq_(repr(tree['foo']), "Required(key='foo', comment='')")
    tools.ok_(isinstance(tree['bar'], Required))
    tools.eq_(repr(tree['bar']), "Required(key='bar', comment='Update me')")


def update_action_repr_test():
    action = UpdateAction(Tree(), 'foo', 'bar', '/test/source.yaml')
    tools.eq_(repr(action), "<'foo': 'bar'> from /test/source.yaml")


def update_action_promise_test():
    action = UpdateAction(Tree(), 'foo', 'bar', '/test/source.yaml')
    promise = action.promise(lambda: int(None))
    with tools.assert_raises(TypeError) as context:
        promise()
    tools.eq_(context.exception.args[0], action)


def update_action_branch_test():
    tree = Tree({'x.a': 1, 'x.b': 2})
    action = UpdateAction(tree, 'x.c', 3, '/test/source.yaml')
    tools.eq_(action.branch, action.tree['x'])

    action = UpdateAction(tree, 'y', 3, '/test/source.yaml')
    tools.eq_(action.branch, action.tree)


def update_action_default_update_test():
    tree = Tree()
    UpdateAction(tree, 'foo', 'bar', '/test/source.yaml')()
    tools.eq_(tree, {'foo': 'bar'})


def update_action_update_test():
    tree = Tree()
    action = UpdateAction(tree, 'foo', 'bar', '/test/source.yaml')
    action.update = lambda a: a.tree.setdefault(a.key, a.value)

    action()
    tools.eq_(tree, {'foo': 'bar'})

    action.value = 'baz'
    action()
    tools.eq_(tree, {'foo': 'bar'})


def promise_test():
    p = Promise(lambda: 42)
    tools.eq_(p(), 42)


def resolve_test():
    tools.eq_(resolve(Promise(lambda: 42)), 42)
    tools.eq_(resolve('foo'), 'foo')


def resolver_proxy_test():
    tree = Tree({
        'foo': Promise(lambda: 42),
        'bar': 'baz',
    })
    tree = ResolverProxy(tree)
    tools.eq_(tree['foo'], 42)
    tools.eq_(tree['bar'], 'baz')
    tools.eq_(set(tree.keys()), set(['foo', 'bar']))


def postprocessor_resolve_promise_test():
    tree = Tree({
        'foo': Promise(lambda: 42),
        'bar': 'baz',
    })
    postprocess = PostProcessor()
    postprocess(tree)
    tools.eq_(tree, {'foo': 42, 'bar': 'baz'})


def postprocessor_check_required_test():
    tree = Tree({
        'foo': Required('foo', ''),
        'bar': Required('bar', 'Update me'),
    })
    postprocess = PostProcessor()

    with tools.assert_raises(ProcessingError) as context:
        postprocess(tree)

    tools.eq_(context.exception.args[0], [tree['bar'], tree['foo']])
