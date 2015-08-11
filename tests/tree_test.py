import warnings

from nose import tools

from configtree.tree import Tree, flatten, rarefy


warnings.filterwarnings('ignore', module='configtree.tree')

td = None


def empty_tree():
    global td
    td = Tree()


def full_tree():
    global td
    td = Tree({
        '1': 1,
        'a.2': 2,
        'a.b.3': 3,
        'a.b.4': 4,
        'a.b.5': 5,
        'a.b.6': 6
    })


@tools.with_setup(empty_tree)
def read_write_test():
    td['1'] = 1
    td['a.2'] = 2
    td['a.b.3'] = 3
    td['a']['b.4'] = 4
    td['a']['b']['5'] = 5
    td['a.b']['6'] = 6

    tools.eq_(td['1'], 1)
    tools.eq_(td['a.2'], 2)
    tools.eq_(td['a.b.3'], 3)
    tools.eq_(td['a.b.4'], 4)
    tools.eq_(td['a.b.5'], 5)
    tools.eq_(td['a.b.6'], 6)

    tools.eq_(td['a']['2'], 2)
    tools.eq_(td['a']['b.3'], 3)
    tools.eq_(td['a']['b.4'], 4)
    tools.eq_(td['a']['b.5'], 5)
    tools.eq_(td['a']['b.6'], 6)

    tools.eq_(td['a']['b']['3'], 3)
    tools.eq_(td['a']['b']['4'], 4)
    tools.eq_(td['a']['b']['5'], 5)
    tools.eq_(td['a']['b']['6'], 6)

    tools.eq_(td['a.b']['3'], 3)
    tools.eq_(td['a.b']['4'], 4)
    tools.eq_(td['a.b']['5'], 5)
    tools.eq_(td['a.b']['6'], 6)


@tools.with_setup(full_tree)
def contains_test():
    tools.ok_('1' in td)
    tools.ok_('a' in td)
    tools.ok_('a.2' in td)
    tools.ok_('a.b' in td)
    tools.ok_('a.b.3' in td)
    tools.ok_('a.b.4' in td)
    tools.ok_('a.b.5' in td)
    tools.ok_('a.b.6' in td)

    tools.ok_('2' in td['a'])
    tools.ok_('b' in td['a'])
    tools.ok_('b.3' in td['a'])
    tools.ok_('b.4' in td['a'])
    tools.ok_('b.5' in td['a'])
    tools.ok_('b.6' in td['a'])

    tools.ok_('3' in td['a.b'])
    tools.ok_('4' in td['a.b'])
    tools.ok_('5' in td['a.b'])
    tools.ok_('6' in td['a.b'])


@tools.with_setup(full_tree)
def len_test():
    tools.ok_(len(td), 6)
    tools.ok_(len(td['a']), 5)
    tools.ok_(len(td['a.b']), 4)


@tools.raises(KeyError)
@tools.with_setup(full_tree)
def tree_key_error_test():
    td = Tree()
    td['x']


@tools.raises(KeyError)
@tools.with_setup(full_tree)
def branch_key_error_test():
    td = Tree({'a.y': 1})
    td['a']['x']


@tools.with_setup(full_tree)
def tree_eq_dict_test():
    tools.eq_(td, {'1': 1, 'a.2': 2, 'a.b.3': 3, 'a.b.4': 4,
                                     'a.b.5': 5, 'a.b.6': 6})
    tools.eq_(td['a'], {'2': 2, 'b.3': 3, 'b.4': 4, 'b.5': 5, 'b.6': 6})
    tools.eq_(td['a.b'], {'3': 3, '4': 4, '5': 5, '6': 6})


@tools.with_setup(full_tree)
def iter_and_keys_test():
    tools.eq_(sorted(list(iter(td))), ['1', 'a.2', 'a.b.3', 'a.b.4',
                                                   'a.b.5', 'a.b.6'])
    tools.eq_(sorted(list(iter(td['a']))), ['2', 'b.3', 'b.4', 'b.5', 'b.6'])
    tools.eq_(sorted(list(iter(td['a.b']))), ['3', '4', '5', '6'])


@tools.with_setup(full_tree)
def rare_iterators_test():
    tools.eq_(list(td.rare_keys()), ['a', '1'])
    tools.eq_(list(td.rare_values()), [td['a'], 1])
    tools.eq_(list(td.rare_items()), [('a', td['a']), ('1', 1)])

    tools.eq_(list(td['a'].rare_keys()), ['b', '2'])
    tools.eq_(list(td['a'].rare_values()), [td['a.b'], 2])
    tools.eq_(list(td['a'].rare_items()), [('b', td['a.b']), ('2', 2)])


@tools.with_setup(empty_tree)
def repr_test():
    td['x.y'] = 1
    tools.eq_(repr(td), "Tree({'x.y': 1})")
    tools.eq_(repr(td['x']), "BranchProxy('x'): {'y': 1}")


@tools.with_setup(full_tree)
def copy_test():
    new_td = td.copy()
    tools.eq_(new_td, td)
    tools.ok_(new_td is not td)
    tools.ok_(isinstance(new_td, Tree))

    new_td = td['a'].copy()
    tools.eq_(new_td, td['a'])
    tools.ok_(new_td is not td['a'])
    tools.ok_(isinstance(new_td, Tree))


@tools.with_setup(empty_tree)
def override_branch_test():
    td['x.y.1'] = 1

    td['x'] = 1
    tools.ok_('x.y.1' not in td)
    tools.ok_('x.y' not in td)
    tools.eq_(td['x'], 1)

    td['x.y.1'] = 1
    tools.ok_('x.y.1' in td)
    tools.ok_('x.y' in td)
    tools.eq_(td['x'], {'y.1': 1})


@tools.with_setup(empty_tree)
def get_value_test():
    tools.eq_(td.get('x.y', 1), 1)
    tools.ok_('x.y' not in td)
    tools.eq_(td.setdefault('x.y', 2), 2)
    tools.ok_('x.y' in td)


@tools.with_setup(empty_tree)
def get_branch_test():
    bx = td.branch('x')
    tools.ok_('x' not in td)  # Empty branch not in tree
    bx['1'] = 1
    tools.ok_('x' in td)
    tools.ok_('x.1' in td)

    bxy = bx.branch('y')
    tools.ok_('x.y' not in td)
    tools.ok_('y' not in bx)

    bxy['2'] = 2
    tools.ok_('x.y.2' in td)
    tools.ok_('x.y' in td)
    tools.ok_('y.2' in bx)
    tools.ok_('y' in bx)


@tools.with_setup(full_tree)
def branch_as_tree_test():
    new_td = td['a.b'].as_tree()
    new_td['3'] = 33
    tools.ok_(isinstance(new_td, Tree))
    tools.eq_(new_td, {'3': 33, '4': 4, '5': 5, '6': 6})
    tools.eq_(td['a.b'], {'3': 3, '4': 4, '5': 5, '6': 6})


@tools.with_setup(full_tree)
def delete_value_test():
    del td['a.b.4']
    del td['a.b.5']
    del td['a.b.6']
    tools.ok_('a.b.3' in td)
    tools.ok_('a.b' in td)
    tools.ok_('a' in td)

    del td['a.b.3']
    tools.ok_('a.b' not in td)    # Empty branch is removed from tree


@tools.with_setup(full_tree)
def delete_branch_test():
    del td['a']
    tools.ok_('a.b.3' not in td)  # Branch is removed with its values
    tools.ok_('a.b.4' not in td)
    tools.ok_('a.b.5' not in td)
    tools.ok_('a.b.6' not in td)
    tools.ok_('a.b' not in td)
    tools.ok_('a.2' not in td)
    tools.ok_('a' not in td)


@tools.raises(KeyError)
@tools.with_setup(empty_tree)
def delete_key_error_test():
    del td['x']


def flatten_test():
    fd = dict(flatten({'a': {'b': {'c': {1: 1, 2: 2}}}}))
    tools.eq_(fd, {'a.b.c.1': 1, 'a.b.c.2': 2})


def rarefy_test():
    rd = rarefy(Tree({'a.b.c': 1, 'x.y.z': 1}))
    tools.eq_(rd, {'a': {'b': {'c': 1}}, 'x': {'y': {'z': 1}}})
