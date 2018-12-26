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
        headnode (obj:`ProcessNode`): Top-level process node.
        progenitor (obj:`psutil.Process`): Top-level process object.
    """
    def __init__(self, progenitor):
        super(ProcessTree, self).__init__()
        self.progenitor = progenitor

        lProgNode = ProcessNode(progenitor)
        lTreeNodes = { progenitor.pid: lProgNode }
        lTreeNodes.update({ cp.pid: ProcessNode(cp) for cp in progenitor.children(True) })

        for lNode in lTreeNodes.itervalues():
            lPPid = lNode.process.parent().pid
            try:
                lPNode = lTreeNodes[lPPid]
                lPNode.children.append(lNode)
                lNode.parent = lPNode
            except KeyError:
                continue

        self.headnode = lProgNode

    def __iter__(self):
        return ProcessIter(self.headnode)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
class ProcessTreeAnalyzer(object):
    """Class to analyze a hierarchy of processes
    
    Attributes:
        process (obj:`psutil.Process`): Description
    """
    def __init__(self, process, fields=['memory_full_info', 'cpu_percent', 'num_threads', 'cpu_times']):
        super(ProcessTreeAnalyzer, self).__init__()
        self.process = process
        self.fields = fields

    def snapshot(self, aInterval=None):
        lProcs = [self.process] + self.process.children(True)

        if aInterval:
            for p in lProcs:
                with p.oneshot():
                    p.cpu_percent()

            time.sleep(aInterval)

        aData = []
        for p in lProcs:
            with p.oneshot():
                aData += [[getattr(p, x)() for x in self.fields]]

        lSums = []
        for row in zip(*aData):
            if isinstance(row[0], tuple):
                lCls = type(row[0])
                lSums.append(lCls._make(map(sum, zip(*row))))
            else:
                lSums.append(sum(row))

        return zip(self.fields, lSums)
# ------------------------------------------------------------------------------
