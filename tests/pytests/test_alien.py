from __future__ import print_function, absolute_import

import pytest

from ipbb.tools.alien import AlienNode, AlienDict, AlienTemplate, AlienBranch


# -----------------------------------------------------------------------------
def test_aliennode_settergetter():
    """
    { function_description }

    :raises     AssertionError:  { exception_description }
    """
    node = AlienNode()
    node.vivado.jobs = 3

    assert hasattr(node, 'vivado')
    assert hasattr(node.vivado, 'jobs')
    assert node.vivado.jobs == 3
    assert node['vivado.jobs'] == 3

    node['design.top'] = 'top_entity'
    assert node['design.top'] == 'top_entity'
    assert node['design']['top'] == 'top_entity'
    assert node.design.top == 'top_entity'


    node.lock = True

    assert node.lock == True
    assert node.vivado.lock == True

    with pytest.raises(KeyError):
        node.modelsim.var = 4

# -----------------------------------------------------------------------------
def test_alien_template():

    template = AlienTemplate("a = ${lvl1.var}")


    node = AlienNode()
    node.lvl1.var = "'Hello World'"
    node.lock = True
    print('lvl1.var:', repr(node.lvl1.var))

    string = template.substitute(node) 
    assert string == "a = {}".format("'Hello World'")


# -----------------------------------------------------------------------------
def test_alienbranch_settergetter():
    """
    { function_description }

    :raises     AssertionError:  { exception_description }
    """
    node = AlienBranch()
    node.vivado.jobs = 3

    assert hasattr(node, 'vivado')
    assert hasattr(node.vivado, 'jobs')

    assert node.vivado.jobs == 3
    assert node['vivado.jobs'] == 3

    node['design.top'] = 'top_entity'
    assert node['design.top'] == 'top_entity'
    assert node['design']['top'] == 'top_entity'
    assert node.design.top == 'top_entity'


# -----------------------------------------------------------------------------
def test_alienbranch_locking():
    """
    { function_description }

    :raises     AssertionError:  { exception_description }
    """
    
    node = AlienBranch()
    node.vivado.jobs = 3

    node._lock(True)

    assert node._locked == True
    assert node.vivado._locked == True

    with pytest.raises(KeyError):
        node.modelsim.var = 4


# -----------------------------------------------------------------------------
def test_alienbranch_iter():

    node = AlienBranch()
    leaves = [
        ('v1_a','a'),
        ('l1_a.v2_a','x'),
        ('l1_a.l2_a.v3_a',3),
        ]

    for k, v in leaves:
        node[k] = v

    assert set(n for n in node) == set(['l1_a.v2_a', 'l1_a.l2_a.v3_a', 'l1_a.l2_a', 'l1_a', 'v1_a',])

    # print('\n'.join( n+': '+str(v) for n,v in node._iterleaves()))

    assert set(n for n in node._iterleaves()) == set(leaves)

    print()
    print('\n'.join( n+': '+str(v) for n,v in node._iternodes()))

# -----------------------------------------------------------------------------
def test_alien2g_template():

    template = AlienTemplate("a = ${lvl1.var}")


    node = AlienBranch()
    node.lvl1.var = "'Hello World'"
    node.lock = True
    print('lvl1.var:', repr(node.lvl1.var))

    string = template.substitute(node) 
    assert string == "a = {}".format("'Hello World'")