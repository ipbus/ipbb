#!/usr/bin/env python
import psutil
import sys
import pprint
import time
import collections
import itertools

from ipbb.tools.pstree import ProcessTree, ProcessIter, ProcessNode, ProcessAnalyzer


if len(sys.argv) != 2:
    print 'Error'
    print sys.argv
    raise SystemExit(-1)
pid = int(sys.argv[1])


# -----------------------------------------------------------------------------
def test_iter(pid):
    p = psutil.Process(pid)

    z = ProcessTree(p)

    for i in z:
        pass
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    from collections import defaultdict

    p = psutil.Process(pid)
    tree = ProcessTree(p)

    for i in tree:
        print 'Process', i

    pa = ProcessTreeAnalyzer(p)
    for n, v in pa.snapshot(0.1):
        print n, v
# -----------------------------------------------------------------------------
