class Package(object):
    """
    Attributes:
        name (str): Name of the package
        components (list): list of components
    """
    def __init__(self, name):
        super(Package, self).__init__()
        self.name = name
        self.components = {}

    def add(self, cmp):
        """Add component to this package

        Args:
            cmp (:obj:`Component`): component obj 
        """
        print cmp.path, self.components
        if cmp.path in self.components:
            raise RuntimeError("Component {} already part of {}".format(cmp.path, self.name))

        self.components[cmp.path] = cmp
        
class Component(object):
    """Attributes

    """
    def __init__(self, path):
        super(Component, self).__init__()
        self.path = path
        

def test():
    
    p = Package('pippo')
    p.add(Component('a/b/c'))

if __name__ == '__main__':
    test()