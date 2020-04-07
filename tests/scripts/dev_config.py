#!/usr/bin/env python
from __future__ import print_function, absolute_import
from future.utils import iterkeys, itervalues, iteritems

from string import Template


class AlienDict(dict):
    """Implementation of perl's autovivification feature."""
    def __init__(self,*args, **kwargs):
        # init the dict
        super(self.__class__,self).__init__(self, *args, **kwargs)
        self._locked = False

    def lock(self):
        self._locked = True
        for o in self.itervalues():
            if type(o) == type(self):
                o.lock()

    def unlock(self):
        self._locked = False
        for o in self.itervalues():
            if type(o) == type(self):
                o.unlock()

    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name)
        except KeyError:
            if self._locked:
                raise
            else:
                value = self[name] = type(self)()
                return value


class AlienObj(object):
    """docstring for AlienObj"""
    def __init__(self):
        super(AlienObj, self).__init__()
        # Create _children first
        self._children = {}
        self._locked = False
        
    def lock(self):
        self._locked = True
        for c in itervalues(self._children):
            if type(c) == type(self):
                c.lock()

    def unlock(self):
        self._locked = False
        for c in itervalues(self._children):
            if type(c) == type(self):
                c.unlock()

    @property
    def locked(self):
        return self._locked
    

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
            super(AlienObj, self).__setattr__(name, value)
            if name in self._children:
                del self._children[name]
        else:
            self._children[name] = value
            if value in self.__dict__:
                del self.__dict__[name]

class AlienTemplate(Template):
    idpattern =  r'[_a-z][\._a-z0-9]*'
 
#-----------------------------------------------------------------------

a = AlienDict()

print(a)

a['x'] = 3
a['y']['z'] = 4

print (a)

cfg = AlienObj()
cfg.vivado.synth.jobs = 3
print(cfg.vivado.synth.jobs)
cfg.lock()
cfg.vivado.synth.ciccio = 5
print(cfg.vivado.synth.ciccio)
try:
    print(cfg.minnie)
except KeyError as exc:
    print(repr(exc))

# Testing templates
print(AlienTemplate("a = ${vivado.synth.jobs}").substitute(cfg))

cfg.unlock()

cfg['d.e'] = 'stoca'
print(cfg.d.e)
exec('x=5', None, cfg)
exec('b.c=10', None, cfg)




