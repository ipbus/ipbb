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

    # @property
    # def locked(self):
    #     return self._locked

    # def lock(self):
    #     """Lock the dictionary and its children"""
    #     self._locked = True
    #     for o in self.itervalues():
    #         if type(o) == type(self):
    #             o.lock()

    # def unlock(self):
    #     """Unlock the dictionary and its children"""
    #     self._locked = False
    #     for o in self.itervalues():
    #         if type(o) == type(self):
    #             o.unlock()

    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name)
        except KeyError:
            if self._locked:
                raise
            else:
                value = self[name] = type(self)()
                return value


class AlienNode(object):
    """
    Utility class to build auto-expanding tress of opbjects
    """
    def __init__(self):
        super(AlienNode, self).__init__()
        # Create _children first
        self._children = {}
        self._locked = False
        
    @property
    def lock(self):
        return self._locked

    @lock.setter
    def lock(self, value):
        self._locked = value
        for c in itervalues(self._children):
            c.lock = value

    # def lock(self):
    #     self._locked = True
    #     for c in itervalues(self._children):
    #         if type(c) == type(self):
    #             c.lock()

    # def unlock(self):
    #     self._locked = False
    #     for c in itervalues(self._children):
    #         if type(c) == type(self):
    #             c.unlock()
    

    def __getitem__(self, name):
        # print('get',name)
        tokens = name.split('.',1)
        child = getattr(self,tokens[0])
        if len(tokens) == 1:
            return child
        else:
            return child[tokens[1]]

    def __setitem__(self, name, value):
        # print('set', name, value)
        tokens = name.rsplit('.',1)
        child = getattr(self,tokens[0])
        if len(tokens) == 1:
            setattr(self, name, value)
        else:
            setattr(self[tokens[0]],tokens[1], value)

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            try:
                return self._children[name]
            except KeyError:
                if self._locked:
                    raise
                else:
                    value = self._children[name] = type(self)()
                    # setattr(self, name, value)
                    # value = self.name = type(self)()
                    return value

    def __setattr__(self, name, value):

        # Add a standard attribute, if it's not another me
        # Note, the order is important to allow the creation of _children
        if type(value) != type(self):
            super(AlienNode, self).__setattr__(name, value)
            if name in self._children:
                del self._children[name]
        else:
            self._children[name] = value
            if value in self.__dict__:
                del self.__dict__[name]

class AlienTemplate(Template):
    """
    This class describes an alien template.
    """
    idpattern =  r'[_a-z][\._a-z0-9]*'

 