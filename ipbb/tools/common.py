from __future__ import print_function
# -------------------------------------------------------------------------

import os
import sys
import pexpect
import subprocess
import time


# -----------------------------------------------------------------------------
class ProcessIter(object):
    """ProcessTree iterator class
    
    Attributes:
        current (obj: `ProcessNode`): Current process node
        stack (obj: `list`): Node stack iterator
    """
    def __init__(self, root):
        super(ProcessIter, self).__init__()
        self.stack = [iter([root])]
        self.current = None

    def __iter__(self):
        return self

    def next(self):
        lNextNode = None
        while lNextNode is None:
            try:
                lNextNode = self.stack[-1].next()
            except StopIteration:
                self.stack.pop()
                if len(self.stack) == 0:
                    raise StopIteration

        # The first non-0 becomes the current
        self.current = lNextNode

        d = len(self.stack) - 1

        # sort next out
        lChildren = lNextNode.children
        if lChildren:
            self.stack.append(iter(lChildren))

        return self.current.process
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
class ProcessNode(object):
    """ProcessTree node
    
    Attributes:
        children (list): List of children
        parent (obj:`ProcessNode`): Reference to parent node
        process (obj:`psutil.Process`): Actual Process object
    """
    def __init__(self, process):
        super(ProcessNode, self).__init__()
        self.parent = None
        self.process = process
        self.children = []

    def __repr__(self):
        return 'ProcessNode(%d)' % self.process.pid
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
class ProcessTree(object):
    """Class representing a process tree hierarcy
    
    Attributes:
        topnode (obj:`ProcessNode`): Top-level process node.
        topprocess (obj:`psutil.Process`): Top-level process object.
    """
    def __init__(self, topprocess):
        super(ProcessTree, self).__init__()
        self.topprocess = topprocess

        topnode = ProcessNode(topprocess)
        tnodes = { topprocess.pid: topnode }
        tnodes.update({ cp.pid: ProcessNode(cp) for cp in topprocess.children(True) })

        for v in tnodes.itervalues():
            pp = v.process.parent().pid
            try:
                pn = tnodes[pp]
                pn.children.append(v)
                v.parent = pn
            except KeyError:
                continue

        self.topnode = topnode

    def __iter__(self):
        return ProcessIter(self.topnode)
# -----------------------------------------------------------------------------


# ------------------------------------------------------------------------------
class SmartOpen(object):

    # -------------------------------------------
    def __init__(self, aTarget):
        if isinstance(aTarget, basestring):
            self.target = open(aTarget, 'w')
        elif aTarget is None:
            self.target = sys.stdout
        else:
            self.target = aTarget
    # -------------------------------------------

    # -------------------------------------------
    @property
    def path(self):
        if self.target is not sys.stdout:
            return self.target.name
        else:
            return None
    # -------------------------------------------

    # -------------------------------------------
    def __enter__(self):
        return self
    # -------------------------------------------

    # -------------------------------------------
    def __exit__(self, type, value, traceback):
        if self.target is not sys.stdout:
            self.target.close()
    # -------------------------------------------

    # -------------------------------------------
    def __call__(self, *strings):
        self.target.write(' '.join(strings))
        self.target.write("\n")
        self.target.flush()
    # -------------------------------------------

# ------------------------------------------------------------------------------


# -----------------------------------------------------------------------------
class ProcessAnalyzer(object):
    """Class to analyze a hierarchy of processes
    
    Attributes:
        process (obj:`psutil.Process`): Description
    """
    def __init__(self, process):
        super(ProcessAnalyzer, self).__init__()
        self.process = process
        # self.childrenbuffer = process.children(True)

    def snapshot(self, aInterval=None):
        lProcs = [self.process] + self.process.children(True)

        lFields = ['memory_full_info', 'cpu_percent', 'num_threads', 'cpu_times']

        if aInterval:
            for p in lProcs:
                with p.oneshot():
                    p.cpu_percent()

            time.sleep(aInterval)

        aData = []
        for p in lProcs:
            with p.oneshot():
                aData += [[getattr(p, x)() for x in lFields]]

        lSums = []
        for row in zip(*aData):
            if isinstance(row[0], tuple):
                lCls = type(row[0])
                lSums.append(type(row[0])._make(map(sum, zip(*row))))
            else:
                lSums.append(sum(row))

        return zip(lFields, lSums)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
class OutputFormatter(object):
    """
    Output formatter class

    Attributes:
        prefix (str): String to be prepent to each output line.
        quiet (bool): Suppress output.
    """

    def __init__(self, prefix=None, quiet=False):
        self._write = sys.stdout.write
        self._flush = sys.stdout.flush
        self.quiet = quiet
        self.prefix = prefix
        self.pending = False

    def __del__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def write(self, message):
        """
        Arguments:
            message (string): Input message

        Returns:
            string: Formatted message

        """
        if self.quiet:
            return

        msg = self.prefix if (self.pending and self.prefix) else ''

        # update pending status
        self.pending = message.endswith('\n')

        # furthemore, postfix the prefix to the newlines in message, execpt for the last one if pending is pn        
        msg += message.replace('\n', '\n' + self.prefix, message.count('\n') - self.pending) if self.prefix else message

        self._write(msg)

    def flush(self):
        """Flushes the internal buffer

        """
        if self.quiet:
            return
        self._flush()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Helper function equivalent to which in posix systems
def which(aExecutable):
    '''Searches for exectable il $PATH'''
    lSearchPaths = os.environ["PATH"].split(os.pathsep) if aExecutable[0] != os.sep else [os.path.dirname(aExecutable)]
    for lPath in lSearchPaths:
        if not os.access(os.path.join(lPath, aExecutable), os.X_OK):
            continue
        return os.path.normpath(os.path.join(lPath, aExecutable))
    return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def mkdir(path, mode=0777):
    try:
        os.makedirs(path,mode)
    except OSError:
        if os.path.exists(path) and os.path.isdir(path):
            pass
        return
# ------------------------------------------------------------------------------



