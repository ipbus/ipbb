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

    dep_info = ("dummy", 0)
    # Lines without a @ are not processed
    line_no_assignment = 'a = "b"'
    assert dep_parser._line_process_assignments(line_no_assignment, dep_info) == line_no_assignment


# -----------------------------------------------------------------------------
def test_assign(dep_parser):
    dep_info = ("dummy", 0)

    assert dep_parser._line_process_assignments('@ a = "a_value"', dep_info) == None
    assert dep_parser.settings['a'] == 'a_value'
    assert dep_parser._line_process_assignments('@ c = a', dep_info) == None
    assert dep_parser.settings['c'] == 'a_value'
    assert dep_parser._line_process_assignments('@ d.e.f = 3.4', dep_info) == None
    assert dep_parser.settings['d.e.f'] == 3.4
    assert dep_parser._line_process_assignments('@ hls.cflags = "-std=c++11"', dep_info) == None
    assert dep_parser.settings['hls.cflags'] == "-std=c++11"



# -----------------------------------------------------------------------------
def test_assign_invalid_expr(dep_parser):
    with pytest.raises(DepAssignmentError):
        dep_parser._line_process_assignments('@ hello world', dep_info)


# -----------------------------------------------------------------------------
def test_assign_no_parname(dep_parser):
    with pytest.raises(DepAssignmentError):
        dep_parser._line_process_assignments('@ = s', dep_info)


# -----------------------------------------------------------------------------
def test_assign_no_value(dep_parser):
    with pytest.raises(DepAssignmentError):
        dep_parser._line_process_assignments('@ x =', dep_info)


# -----------------------------------------------------------------------------
def test_assign_invalid_parname(dep_parser):
    with pytest.raises(DepAssignmentError):
        dep_parser._line_process_assignments('@ 2_not_good = 0', dep_info)


# -----------------------------------------------------------------------------
def test_assign_invalid_value(dep_parser):

    dep_parser._line_process_assignments('@ a = print(3)', dep_info)

