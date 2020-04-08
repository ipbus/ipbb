from __future__ import print_function, absolute_import

import pytest

from ipbb.tools.alien import AlienNode, AlienDict, AlienTemplate


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

def test_alien_template():

    template = AlienTemplate("a = ${lvl1.var}")


    node = AlienNode()
    node.lvl1.var = "'Hello World'"
    node.lock = True
    print('lvl1.var:', repr(node.lvl1.var))

    string = template.substitute(node) 
    assert string == "a = {}".format("'Hello World'")

