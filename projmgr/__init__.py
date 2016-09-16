from __future__ import print_function

import logging
import os


#---
class DirSentry:

    def __init__(self, dir):
        if not os.path.exists(dir):
            raise RuntimeError('stocazzo '+dir)

        self._olddir = os.path.realpath(os.getcwd())

        os.chdir(dir)
        logging.info('-- cd',dir)


    def __del__(self):
        os.chdir(self._olddir)
        logging.info('-- cd',self._olddir)

#---
class Plugin(object):

    def __init__(self, **kwargs):
        for k,v in kwargs.iteritems():
            setattr(self,k,v)


    def execute():
        print('Nothing to do')


    def _run(self, cmd):
        self._log.info('Command:',cmd)
        os.system( cmd )


#------------------------------------------------------------------------------
# WorkareaBuilder plugin
#------------------------------------------------------------------------------

class WorkareaBuilder(Plugin):
    _log = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(WorkareaBuilder,self).__init__(**kwargs)

        if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]


    @staticmethod
    def addArguments(subparsers,cmd):
        # parser_add = parser.add_subparsers(dest = 'cmd')
        subp = subparsers.add_parser(cmd)
        subp.add_argument('project',        help='project to build')
        subp.add_argument('top', nargs = '?', default='top', help = 'top level name')
        subp.add_argument('-w','--workarea')
        subp.add_argument('--prefix',       help='checkout prefix', default='cactusupgrades')

    def make(self,workarea,env):
        pass


    def execute(self):
        from os.path import realpath,basename,dirname,join

        here = realpath(dirname(__file__))

        self._log.info('script path',here)
        self._log.info('Project:',self.project)

        projectpath=self.project
        if not os.path.exists(self.prefix):
            raise RuntimeError('Project %s not found at %s' % (self.project, self.prefix) )

        workarea = self.workarea if self.workarea else basename(self.project)

        env = {
            'REPLACE_BUILD_PROJECT':projectpath,
            'REPLACE_TOPLVL':self.top,
            'CACTUS_ROOT':realpath(self.prefix),
            'SCRIPT_PATH':self.scriptpath
        }

        # fetch & execute the method corresponding to the product
        # self._prodmap[self.product](self,workarea,env)
        self.make(workarea,env)
