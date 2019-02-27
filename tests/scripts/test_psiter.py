#!/usr/bin/env python
import psutil
import sys
import pprint
import time
import collections
import itertools

from ipbb.tools.pstree import ProcessTree, ProcessIter, ProcessNode, ProcessTreeAnalyzer
from texttable import Texttable


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
def test_summary(pid):
    from collections import defaultdict

    p = psutil.Process(pid)
    tree = ProcessTree(p)

    for i in tree:
        print 'Process', i

    pa = ProcessTreeAnalyzer(p)
    print 'stats'
    s = pa.snapshot(0.1)

    lSummary = Texttable(max_width=0)
    lSummary.set_deco(Texttable.HEADER | Texttable.BORDER)
    lSummary.header(['pid'] + pa.fields)

    for pid, data in s:
        print pid, data
        lSummary.add_row([pid] + data)

    # for n, v in pa.summary(1):
        # print n, 
    print lSummary.draw()


# -----------------------------------------------------------------------------
def test_xxx(pid):
    p = psutil.Process(pid)

    fields = ['name', 'cmdline', 'memory_full_info', 'cpu_percent', 'num_threads', 'cpu_times.user']

    # Normalise the fields
    for fn in fields:
        if '.' in fn:
            print fn.split('.')


    # lData = []
    # with p.oneshot():

    #     lProps = []
    #     for f in fields:

    #         x = getattr(p, f)()
    #         if f is 'cmdline':
    #             lProps += [' '.join(x)]
    #         elif isinstance(x, tuple):
    #             lProps += [e for e in x]
    #         else:
    #             lProps += [x]

    #     lData += [(p.pid, lProps)]
    #     lData += [ (p.pid, [getattr(p, x)() for x in fields])]

    # print lData

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    test_xxx(pid)
