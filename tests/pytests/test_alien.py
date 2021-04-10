import pytest

from ipbb.tools.alien import AlienDict, AlienTemplate, AlienBranch, AlienTree


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
    """ Test Alientree's locking mechanism

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

    assert set(n for n in branch) == {'l1_a.v2_a', 'l1_a.l2_a.v3_a', 'l1_a.l2_a', 'l1_a', 'v1_a',}

    assert set(n for n in branch._iterleaves()) == set(leaves)



# -----------------------------------------------------------------------------
def test_alienbranch_template():

    template = AlienTemplate("a = ${lvl1.var}")

    branch = AlienBranch()
    branch.lvl1.var = "'Hello World'"
    branch._lock(True)
    # print('lvl1.var:', repr(branch.lvl1.var))

    string = template.substitute(branch)
    assert string == "a = {}".format(branch.lvl1.var)


# -----------------------------------------------------------------------------
def test_alienbranch_eval():

    branch = AlienBranch()
    branch.a = 10
    branch._lock(True)

    leaf_a = eval('a', None, branch)

    assert leaf_a == 10

    # with pytest.raises(KeyError) as excinfo:
        # eval('b', None, branch)


# -----------------------------------------------------------------------------
def test_alientree():

    tree = AlienTree()
    leaves = [
        ('v1_a', 'a'),
        ('l1_a.v2_a', 'x'),
        ('l1_a.l2_a.v3_a', 3),
    ]

    for k, v in leaves:
        tree[k] = v

    assert set(n for n in tree) == {'l1_a.v2_a', 'l1_a.l2_a.v3_a', 'l1_a.l2_a', 'l1_a', 'v1_a', }

    assert {'l1_a.v2_a'}.issubset(tree)

    # print()
    # print('\n'.join( n+': '+str(v) for n,v in tree.branches()))
