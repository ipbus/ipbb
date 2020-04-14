#!/usr/bin/env python
from __future__ import print_function, absolute_import
from future.utils import iterkeys, itervalues, iteritems

from string import Template



# ------------------------------------------------------------------------------
class DictObj(object):
    """
    Convenience class to wrap a python dictionary in an opbject
    """

    def __init__(self, aDict={} ):
        super(DictObj, self).__setattr__('data', aDict)

    def __setattr__(self, key, value):
        self.data[key] = value

    def __getattr__(self, key):
        # we don't need a special call to super here because getattr is only
        # called when an attribute is NOT found in the instance's dictionary
        try:
            return self.data[key]
        except KeyError:
            raise AttributeError

    def __repr__(self):
        type_name = type(self).__name__

        arg_strings = [ '%s=%s' % (key, repr(value)) for key, value in sorted(self.data.iteritems())]

        return '%s(%s)' % (type_name, ', '.join(arg_strings))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
class AlienDict(dict):
    """
    Implementation of perl's autovivification feature.
    """
    def __init__(self,*args, **kwargs):
        """
        Constructor
        """
        super(self.__class__,self).__init__(self, *args, **kwargs)
        self._locked = False

    @property
    def lock(self):
        return self._locked

    @lock.setter
    def lock(self, value):
        self._locked = value
        for c in itervalues(self._children):
            c.lock = value

    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name)
        except KeyError:
            if self._locked:
                raise
            else:
                value = self[name] = type(self)()
                return value


# ------------------------------------------------------------------------------
# class AlienNode(object):
#     """
#     Utility class to build auto-expanding tress of opbjects
#     """
#     def __init__(self):
#         super(AlienNode, self).__init__()
#         # Create _children first
#         self._children = {}
#         self._locked = False
        
#     @property
#     def lock(self):
#         return self._locked

#     @lock.setter
#     def lock(self, value):
#         self._locked = value
#         for c in itervalues(self._children):
#             c.lock = value

#     def __getitem__(self, name):
#         # print('get',name)
#         tokens = name.split('.',1)
#         child = getattr(self,tokens[0])
#         if len(tokens) == 1:
#             return child
#         else:
#             return child[tokens[1]]

#     def __setitem__(self, name, value):
#         # print('set', name, value)
#         tokens = name.rsplit('.',1)
#         child = getattr(self,tokens[0])
#         if len(tokens) == 1:
#             setattr(self, name, value)
#         else:
#             setattr(self[tokens[0]],tokens[1], value)

#     def __getattr__(self, name):
#         try:
#             return self.__dict__[name]
#         except KeyError:
#             try:
#                 return self._children[name]
#             except KeyError:
#                 if self._locked:
#                     raise
#                 else:
#                     value = self._children[name] = type(self)()
#                     # setattr(self, name, value)
#                     # value = self.name = type(self)()
#                     return value

#     def __setattr__(self, name, value):

#         # Add a standard attribute, if it's not another me
#         # Note, the order is important to allow the creation of _children
#         if type(value) != type(self):
#             super(AlienNode, self).__setattr__(name, value)
#             if name in self._children:
#                 del self._children[name]
#         else:
#             self._children[name] = value
#             if value in self.__dict__:
#                 del self.__dict__[name]


# ------------------------------------------------------------------------------
class AlienBranch(object):
    """
    Utility class to easily build trees of key-values, useful for configuration
    tress
    """
    def __init__(self):
        super(AlienBranch, self).__init__()
        self.__dict__['_locked'] = False

    def __repr__(self):
        return str({ k:v for k, v in self.__dict__.iteritems() if not k.startswith('_')})
        
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
        super(AlienBranch, self).__setattr__(name, value)

    def __getitem__(self, name):
        # print('get',name)
        tokens = name.split('.',1)
        item = getattr(self,tokens[0])
        if len(tokens) == 1:
            return item
        else:
            return item[tokens[1]]


    def __setitem__(self, name, value):

        tokens = name.rsplit('.',1)
        if len(tokens) == 1:
            setattr(self, name, value)
        else:
            setattr(self[tokens[0]],tokens[1], value)

    def __iter__(self):
        for b,o in self.__dict__.iteritems():
            if b.startswith('_'):
                continue
            elif isinstance(o, type(self)):
                for cn in o:
                    yield b+'.'+cn
                yield b
            else:
                yield b

    def _iterleaves(self):
        for b, o in self.__dict__.iteritems():
            if b.startswith('_'):
                continue
            elif isinstance(o, type(self)):
                for cb, co in o._iterleaves():
                    yield b+'.'+cb, co
            else:
                yield b, o

    def _iterbranches(self):
        for b, o in self.__dict__.iteritems():
            if b.startswith('_'):
                continue
            elif isinstance(o, type(self)):
                for cb, co in o._iterbranches():
                    yield b+'.'+cb, co
                yield b, o

    # @lock.setter
    def _lock(self, value):
        self._locked = value
        for b, o in self._iterbranches():
            if isinstance(o, type(self)):
                o._lock(value)

    def _get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            if default:
                return default
            else:
                raise

# ------------------------------------------------------------------------------
class AlienTree(object):
    """
    docstring for AlienTree
    """
    def __init__(self):
        super(AlienTree, self).__init__()
        self._trunk = AlienBranch()

    @property
    def trunk(self):
        return self._trunk

    def __call__(self):
        return self._trunk

    def __iter__(self):
        return self._trunk.__iter__()

    def __getitem__(self, name):
        return self._trunk.__getitem__(name)

    def __setitem__(self, name, value):
        return self._trunk.__setitem__(name, value)

    def lock(self, value):
        self._trunk._lock(value)

    def get(self, name, default=None):
        return self._trunk._get(name, default)

    def leaves(self):
        return self._trunk._iterleaves()
    
    def branches(self):
        return self._trunk._iterbranches()

        

# ------------------------------------------------------------------------------
def iterleaves(branch):
    """
    Helper function to iterate over a branch tree
    
    :param      branch:  A branch tree
    :type       branch:  AlienBranch
    
    :returns:   A branch leaf
    :rtype:     anything
    """
    return branch._iterleaves()

# ------------------------------------------------------------------------------
def iterbranches(branch):
    """
    Helper function to iterate over a branch tree
    
    :param      branch:  A branch tree
    :type       branch:  AlienBranch
    
    :returns:   A branch leaf
    :rtype:     anything
    """
    return branch._iterbranches()
# ------------------------------------------------------------------------------
class AlienTemplate(Template):
    """
    This class describes an alien template.
    """
    idpattern =  r'[_a-z][\._a-z0-9]*'

 