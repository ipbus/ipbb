import pytest

from ipbb.depparser._cmdparser import DepCmdParser
from ipbb.depparser._cmdtypes import IncludeCommand, SetupCommand

# -----------------------------------------------------------------------------
def test_cmdparser_include():

    cp = DepCmdParser()

    args = cp.parse_line("include -c a:b --cd ../aaa afile.vhd".split())
    assert type(args) == IncludeCommand
    assert args.flags() == []
    assert args.extra() == None
    assert args.package == 'a'
    assert args.component == 'b'
    assert args.filepath == ['afile.vhd']


# -----------------------------------------------------------------------------
def test_cmdparser_setup():

    cp = DepCmdParser()

    args = cp.parse_line("setup -c a:b -f --cd ../aaa afile.vhd".split())
    assert type(args) == SetupCommand
    assert args.flags() == ['finalise']
    assert args.extra() == None
    assert args.package == 'a'
    assert args.component == 'b'
    assert args.filepath == ['afile.vhd']
