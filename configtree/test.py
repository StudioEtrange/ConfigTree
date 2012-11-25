from nose import tools

from configtree import Tree, flatten


td = Tree()


def write_test():
    td['1'] = 1
    td['a.2'] = 2
    td['a.b.3'] = 3
    td['a']['b.4'] = 4
    td['a']['b']['5'] = 5
    td['a.b']['6'] = 6


def read_test():
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


def len_test():
    tools.ok_(len(td), 6)
    tools.ok_(len(td['a']), 5)
    tools.ok_(len(td['a.b']), 4)


@tools.raises(KeyError)
def tree_key_error_test():
    td['x']


@tools.raises(KeyError)
def branch_key_error_test():
    td['a']['x']


def tree_eq_dict_test():
    tools.eq_(td, {'1': 1, 'a.2': 2, 'a.b.3': 3, 'a.b.4': 4,
                                     'a.b.5': 5, 'a.b.6': 6})
    tools.eq_(td['a'], {'2': 2, 'b.3': 3, 'b.4': 4, 'b.5': 5, 'b.6': 6})
    tools.eq_(td['a.b'], {'3': 3, '4': 4, '5': 5, '6': 6})


def iter_and_keys_test():
    tools.eq_(sorted(list(iter(td))), ['1', 'a.2', 'a.b.3', 'a.b.4',
                                                   'a.b.5', 'a.b.6'])
    tools.eq_(sorted(list(iter(td['a']))), ['2', 'b.3', 'b.4', 'b.5', 'b.6'])
    tools.eq_(sorted(list(iter(td['a.b']))), ['3', '4', '5', '6'])


def override_branch_test():
    td['i.j.1'] = 1

    td['i'] = 1
    tools.ok_('i.j.1' not in td)
    tools.ok_('i.j' not in td)
    tools.eq_(td['i'], 1)

    td['i.j.1'] = 1
    tools.ok_('i.j.1' in td)
    tools.ok_('i.j' in td)
    tools.eq_(td['i'], {'j.1': 1})


def get_value_test():
    tools.eq_(td.get('i.j.2', 2), 2)
    tools.ok_('i.j.2' not in td)
    tools.eq_(td.setdefault('i.j.2', 2), 2)
    tools.ok_('i.j.2' in td)


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


def branch_as_tree_test():
    new_td = td['a.b'].as_tree()
    new_td['3'] = 33
    tools.ok_(isinstance(new_td, Tree))
    tools.eq_(new_td, {'3': 33, '4': 4, '5': 5, '6': 6})
    tools.eq_(td['a.b'], {'3': 3, '4': 4, '5': 5, '6': 6})


def delete_test():
    del td['a.b.4']
    del td['a.b.5']
    del td['a.b.6']
    tools.ok_('a.b.3' in td)
    tools.ok_('a.b' in td)
    tools.ok_('a' in td)

    del td['a.b.3']
    tools.ok_('a.b' not in td)    # Empty branch is removed from tree

    del td['i']
    tools.ok_('i.j.1' not in td)  # Branch is removed with its values
    tools.ok_('i.j.2' not in td)
    tools.ok_('i.j' not in td)
    tools.ok_('i' not in td)


def flatten_test():
    fd = dict(flatten({'a': {'b': {'c': {1: 1, 2: 2}}}}))
    tools.eq_(fd, {'a.b.c.1': 1, 'a.b.c.2': 2})
