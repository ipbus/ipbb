import pytest

from ipbb.depparser._fileparser import DepFileParser, DepAssignmentError
from ipbb.depparser._pathmaker import Pathmaker

# Some test cases
# a_var = 'b'
# c_3 = 3
# dom = 4.5
# a.b.c = x
# 0_crap = 365
# = s
# 0_das = 3
# x  =

# -----------------------------------------------------------------------------
@pytest.fixture
def dep_parser():
    pm = Pathmaker('.')
    return DepFileParser('sim', pm)


# -----------------------------------------------------------------------------
def test_no_assign(dep_parser):
    # Lines without a @ are not processed
    line_no_assignment = 'a = "b"'
    assert dep_parser._lineProcessAssignments(line_no_assignment) == line_no_assignment


# -----------------------------------------------------------------------------
def test_assign(dep_parser):
    assert dep_parser._lineProcessAssignments('@ a = "a_value"') == None
    assert dep_parser.settings['a'] == 'a_value'
    assert dep_parser._lineProcessAssignments('@ c = a') == None
    assert dep_parser.settings['c'] == 'a_value'
    assert dep_parser._lineProcessAssignments('@ d.e.f = 3.4') == None
    assert dep_parser.settings['d.e.f'] == 3.4
    assert dep_parser._lineProcessAssignments('@ hls.cflags = "-std=c++11"') == None
    assert dep_parser.settings['hls.cflags'] == "-std=c++11"



# -----------------------------------------------------------------------------
def test_assign_invalid_expr(dep_parser):
    with pytest.raises(DepAssignmentError):
        dep_parser._lineProcessAssignments('@ hello world')


# -----------------------------------------------------------------------------
def test_assign_no_parname(dep_parser):
    with pytest.raises(DepAssignmentError):
        dep_parser._lineProcessAssignments('@ = s')


# -----------------------------------------------------------------------------
def test_assign_no_value(dep_parser):
    with pytest.raises(DepAssignmentError):
        dep_parser._lineProcessAssignments('@ x =')


# -----------------------------------------------------------------------------
def test_assign_invalid_parname(dep_parser):
    with pytest.raises(DepAssignmentError):
        dep_parser._lineProcessAssignments('@ 2_not_good = 0')


# -----------------------------------------------------------------------------
def test_assign_invalid_value(dep_parser):

    dep_parser._lineProcessAssignments('@ a = print(3)')

