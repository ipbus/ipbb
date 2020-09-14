#!/usr/bin/env python3


class AlienNode2g(object):
    """
    Utility class to easily build trees of key-values, useful for configuration
    tress
    """
    def __init__(self):
        super().__init__()
        self.__dict__['_locked'] = False

    def __repr__(self):
        return str({ k:v for k, v in self.__dict__.items() if not k.startswith('_')})
        
    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if self._locked or name.startswith('__'):
                raise
            else:
                value = self.__dict__[name] = type(self)()
                return value

    def __setattr__(self, name, value):
        if name not in self.__dict__ and name.startswith('_'):
            raise AttributeError("Attributes starting with '_' are reserved ")
        super().__setattr__(name, value)

    def __getitem__(self, name):
        # print('get',name)
        tokens = name.split('.',1)
        child = getattr(self,tokens[0])
        if len(tokens) == 1:
            return child
        else:
            return child[tokens[1]]

    def __setitem__(self, name, value):

        tokens = name.rsplit('.',1)
        if len(tokens) == 1:
            setattr(self, name, value)
        else:
            setattr(self[tokens[0]],tokens[1], value)

    def __iter__(self):
        for n,o in self.__dict__.items():
            if n.startswith('_'):
                continue
            elif isinstance(o, type(self)):
                for cn in o:
                    yield n+'.'+cn
                yield n
            else:
                yield n

    def _iternodes(self):
        for n,o in self.__dict__.items():
            if n.startswith('_'):
                continue
            elif isinstance(o, type(self)):
                for cn, co in o._iternodes():
                    yield n+'.'+cn, co
            else:
                yield n,o
#-----------------------------------------------------------------------

def iternodes(node):
    """
    Helper function to iterate over a node tree
    
    :param      node:  The node
    :type       node:  { type_description }
    
    :returns:   { description_of_the_return_value }
    :rtype:     { return_type_description }
    """
    return node._iternodes()

node = AlienNode2g()
print(node)
print(vars(node))
print(dir(node))
print(vars(node))
print(node.a)
print(node)

node.b.c = 5
print(node)
print(node['b.c'])
print(node['b.d'])
print(node['b']['c'])
print(node)
node['l1.l2.l3.l4'] =7
node.l1.l2.l3.l4=8
print (node)
for k in node:
    print ('-', k)


print('locked:', node._locked)
node._locked = True
try:
    node.noway.val = 7
except Exception as e:
    print (type(e), e)

for n in node:
    print (n)

print('b' in node)

for n in node._iternodes():
    print (n)

for n in iternodes(node):
    print (n)