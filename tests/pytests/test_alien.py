from __future__ import print_function, absolute_import

import pytest

from ipbb.tools.alien import AlienDict, AlienTemplate, AlienBranch, AlienTree


# # -----------------------------------------------------------------------------
# def test_aliennode_settergetter():
#     """
#     { function_description }

#     :raises     AssertionError:  { exception_description }
#     """
#     node = AlienNode()
#     node.vivado.jobs = 3

#     assert hasattr(node, 'vivado')
#     assert hasattr(node.vivado, 'jobs')
#     assert node.vivado.jobs == 3
#     assert node['vivado.jobs'] == 3

#     node['design.top'] = 'top_entity'
#     assert node['design.top'] == 'top_entity'
#     assert node['design']['top'] == 'top_entity'
#     assert node.design.top == 'top_entity'


#     node.lock = True

#     assert node.lock == True
#     assert node.vivado.lock == True

#     with pytest.raises(KeyError):
#         node.modelsim.var = 4

# # -----------------------------------------------------------------------------
# def test_alien_template():

#     template = AlienTemplate("a = ${lvl1.var}")


#     node = AlienNode()
#     node.lvl1.var = "'Hello World'"
#     node.lock = True
#     print('lvl1.var:', repr(node.lvl1.var))

#     string = template.substitute(node) 
#     assert string == "a = {}".format("'Hello World'")


# -----------------------------------------------------------------------------
def test_alienbranch_settergetter():
    """
    { function_description }

    :raises     AssertionError:  { exception_description }
    """
    branch = AlienBranch()
    branch.vivado.jobs = 3

    assert hasattr(branch, 'vivado')
    assert hasattr(branch.vivado, 'jobs')

    assert branch.vivado.jobs == 3
    assert branch['vivado.jobs'] == 3

    branch['design.top'] = 'top_entity'
    assert branch['design.top'] == 'top_entity'
    assert branch['design']['top'] == 'top_entity'
    assert branch.design.top == 'top_entity'


# -----------------------------------------------------------------------------
def test_alienbranch_locking():
    """
    { function_description }

    :raises     AssertionError:  { exception_description }
    """
    
    branch = AlienBranch()
    branch.vivado.jobs = 3

    branch._lock(True)

    assert branch._locked == True
    assert branch.vivado._locked == True

    with pytest.raises(KeyError):
        branch.modelsim.var = 4


# -----------------------------------------------------------------------------
def test_alienbranch_iter():

    branch = AlienBranch()
    leaves = [
        ('v1_a','a'),
        ('l1_a.v2_a','x'),
        ('l1_a.l2_a.v3_a',3),
        ]

    for k, v in leaves:
        branch[k] = v

    assert set(n for n in branch) == set(['l1_a.v2_a', 'l1_a.l2_a.v3_a', 'l1_a.l2_a', 'l1_a', 'v1_a',])

    # print('\n'.join( n+': '+str(v) for n,v in branch._iterleaves()))

    assert set(n for n in branch._iterleaves()) == set(leaves)

    print()
    print('\n'.join( n+': '+str(v) for n,v in branch._iterbranches()))


# -----------------------------------------------------------------------------
def test_alienbranch_template():

    template = AlienTemplate("a = ${lvl1.var}")


    branch = AlienBranch()
    branch.lvl1.var = "'Hello World'"
    branch.lock = True
    print('lvl1.var:', repr(branch.lvl1.var))

    string = template.substitute(branch) 
    assert string == "a = {}".format("'Hello World'")


# -----------------------------------------------------------------------------
def test_alienbranch_exec():

    branch = AlienBranch()
    exec('a = 10', None, branch)

    print()
    assert 'a' in branch
    assert branch.a == 10


# -----------------------------------------------------------------------------
def test_alientree():

    tree = AlienTree()
    leaves = [
        ('v1_a','a'),
        ('l1_a.v2_a','x'),
        ('l1_a.l2_a.v3_a',3),
        ]

    for k, v in leaves:
        tree[k] = v

    assert set(n for n in tree) == set(['l1_a.v2_a', 'l1_a.l2_a.v3_a', 'l1_a.l2_a', 'l1_a', 'v1_a',])

    print()
    print('\n'.join( n+': '+str(v) for n,v in tree.branches()))
