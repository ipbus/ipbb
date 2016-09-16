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
# SVN plugin base class
#------------------------------------------------------------------------------

class SvnPlugin(Plugin):
    '''
    Base SVN plugin.
    Implements several helper function used in the derived classes.
    '''
    _log = logging.getLogger(__name__)

    def __init__(self,**kwargs):
        super(SvnPlugin,self).__init__(**kwargs)


    def _checkOutCactus(self,svnpath):
        from os.path import exists,join
        if ( exists(self.cactusRoot) and exists(join(self.cactusRoot,'.svn'))):
            self._log.debug(self.cactusRoot,'already exists. Will use it')
            return
        cmd = 'svn co --depth=empty %s' % svnpath
        if self.prefix:
            cmd+=' '+self.cactusRoot

        self._run(cmd)


    def _rebuildEmpty(self, tag):
        tokens = [ d for d in tag.split('/') if d ]

        partials =  [ '/'.join(tokens[:i+1]) for i,_ in enumerate(tokens) ]

        for s in partials:
            cmd = 'svn up --depth=empty %s' % s
            self._run(cmd)

    def _switch(self, folder, fromtag):
        cmd = 'svn switch %s %s' % ( os.path.join(fromtag, folder), folder )
        self._run(cmd)


    def _cactusCheckout(self, folder, fromtag):
        # go to the tag directory
        sentry = DirSentry(self.cactusRoot)

        # sanitize the foldername
        if folder[-1]=='/': folder = folder[:-1]

        # and check it out in its final path
        cmd = 'svn co %s %s' % ( os.path.join(fromtag, 'cactusupgrades', folder), folder )
        self._run(cmd)

    def _checkout(self, svnroot, folder, dest):
        # go to the tag directory
        sentry = DirSentry(self.cactusRoot)

        # sanitize the foldername
        if folder[-1]=='/': folder = folder[:-1]

        # and check it out in its final path
        cmd = 'svn co %s %s' % ( os.path.join(svnroot, folder), dest )
        self._run(cmd)


    def _fetch(self, folder):
        # go to the tag directory
        sentry = DirSentry(self.cactusRoot)

        # sanitize the foldername
        if folder[-1]=='/': folder = folder[:-1]

        self._rebuildEmpty(folder)

        # finally fetch the full folder
        cmd = 'svn up --set-depth=infinity %s' % folder
        self._run(cmd)


    def _fetchAndSwitch(self, folder, fromtag):
        # go to the tag directory
        sentry = DirSentry(self.cactusRoot)

        # sanitize the foldername
        if folder[-1]=='/': folder = folder[:-1]

        self._rebuildEmpty(folder)

        cmd = 'svn switch %s %s' % ( os.path.join(fromtag, 'cactusupgrades', folder), folder )
        self._run(cmd)


        # finally fetch the full folder
        cmd = 'svn up --set-depth=infinity %s' % folder
        self._run(cmd)


    def _checkPath(self, svnurl ):
        # attempt an svn ls
        retval = os.system('svn ls --depth=empty '+svnurl+ '> /dev/null 2>&1')

        # and throw if it fails
        if retval:
            raise RuntimeError(svnurl+' does not exists')


    def _mkLocalDir(self,folder):

        try:
            os.makedirs(os.path.join(self.cactusRoot,folder))
        except OSError:
            pass


    def _findFirstExisting(self, svnroot, paths):
        sentry = DirSentry(self.cactusRoot)

        notFound = []
        for p in paths:
            try:
                svnpath = os.path.join(svnroot, p)
                self._checkPath(svnpath)
            except RuntimeError as e:
                notFound.append(svnpath)
                continue

            return p

        raise RuntimeError('Failed to find tag path. Search paths:'+''.join(['\n   '+s for s in notFound]))

#------------------------------------------------------------------------------
# CactusFetcher plugin
#------------------------------------------------------------------------------

class CactusFetcher(SvnPlugin):
    '''
    CactusFetcher Plugin
    Fetches a project from the same trunk/branch/tag the project was created from.
    '''
    _log = logging.getLogger(__name__)

    @staticmethod
    def addArguments(subparsers,cmd):
        subp = subparsers.add_parser(cmd)
        subp.add_argument('project', help='project to checkout')
        subp.add_argument('--prefix',        help='checkout prefix', default='cactusupgrades')

    def __init__(self, **kwargs):
        super(CactusFetcher,self).__init__(**kwargs)

        # make sure the prefix is well behaved
        if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]

        self.cactusRoot = os.path.realpath(self.prefix)

    def execute(self):
        import os

        if not os.path.exists(self.prefix):
            raise ValueError('Directory %s does not exist' % self.prefix)
        folders = [self.project]

        print('Retrieving:')
        print('\n'.join(folders))

        for f in folders:
            self._fetch( f )

#------------------------------------------------------------------------------
# CactusCheckout plugin
#------------------------------------------------------------------------------

class CactusCheckout(SvnPlugin):
    '''
    '''
    _log = logging.getLogger(__name__)

    @staticmethod
    def addArguments(subparsers,cmd):
        subp = subparsers.add_parser(cmd)
        subp.add_argument('project', help='project to checkout')
        subp.add_argument('-t', '--fromtag', help='fetch the project from a different tag')
        subp.add_argument('--prefix',        help='checkout prefix', default='cactusupgrades')

    def __init__(self, **kwargs):
        super(CactusCheckout,self).__init__(**kwargs)

        # make sure the prefix is well behaved
        if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]

        self.cactusRoot = os.path.realpath(self.prefix)

    def execute(self):
        import os

        if not os.path.exists(self.prefix):
            raise ValueError('Directory %s does not exist' % self.prefix)
        folders = [self.project]

        print('Retrieving:')
        print('\n'.join(folders))

        # Take the foder from a different tag
        tagPath = os.path.join('^/',self.fromtag)

        for f in folders:
            self._cactusCheckout( f, tagPath )

#------------------------------------------------------------------------------
# CactusProjectAdder plugin
#------------------------------------------------------------------------------

class CactusProjectAdder(SvnPlugin):
    '''
    CactusProjectAdder : checks out a project form a different area of cactus
    '''
    _log = logging.getLogger(__name__)

    @staticmethod
    def addArguments(subparsers,cmd):
        subp = subparsers.add_parser(cmd)
        subp.add_argument('project', help='Project to checkout')
        subp.add_argument('fromtag', help='Tag to check the project from')
        subp.add_argument('--svnroot', help='Alternate repository to take the tag from', default=None)
        subp.add_argument('--prefix', help='Checkout prefix', default='cactusupgrades')


    def __init__(self, **kwargs):
        super(CactusProjectAdder,self).__init__(**kwargs)

        # make sure the prefix is well behaved
        if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]

        self.cactusRoot = os.path.realpath(self.prefix)

    def execute(self):
        import os

        if not os.path.exists(self.prefix):
            raise ValueError('Directory %s does not exist' % self.prefix)


        print('Discovering the svn project path in tag '+self.fromtag)
        # Discover the correct folder to check out
        sentry = DirSentry(self.cactusRoot)
        repo = self.svnroot if self.svnroot else '^/'
        print('Using svn repository:', repo)
        tagPath = os.path.join(repo,self.fromtag)

        subPaths = [
                    os.path.join('cactusupgrades/projects', self.project),
                    os.path.join(self.project)
                ]
        svnpath = self._findFirstExisting( tagPath, subPaths )

        print('Retrieving:')
        print('\n'+ svnpath)

        # First ensure <cactusRoot>/projects exists
        self._mkLocalDir('projects')

        self._checkout(tagPath,svnpath,os.path.join('projects',self.project))



#------------------------------------------------------------------------------
# CactusCreator plugin
#------------------------------------------------------------------------------

class CactusCreator(SvnPlugin):
    _log = logging.getLogger(__name__)

    @staticmethod
    def addArguments(subparsers,cmd):
        subp = subparsers.add_parser(cmd)
        subp.add_argument('tag',             help='tag to checkout - it must contain a "cactusupgrades" folder.', default='trunk')
        subp.add_argument('-b','--board',             help='board area to check out.', default=None)
        subp.add_argument('-u', '--user',    help='svn username', default=os.getlogin())
        subp.add_argument('--prefix',        help='Checkout prefix', default='cactusupgrades')

    def __init__(self, **kwargs):
        super(CactusCreator,self).__init__(**kwargs)

        # make sure the prefix is well behaved
        if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]

        self.cactusRoot = os.path.realpath(self.prefix)

    def execute(self):
        import os

        svnpath = 'svn+ssh://%s@svn.cern.ch/reps/cactus/%s/cactusupgrades' % (self.user,self.tag)

        print('Checking out tag',self.tag)
        self._checkPath(svnpath)
        self._checkOutCactus(svnpath)

        folders = ['components']
        folders += ['boards'] if not self.board else [os.path.join('boards',self.board)]

        print('Retrieving:')
        print('\n'.join(folders))

        for f in folders:
            self._fetch( f )

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
            'SCRIPT_PATH':dirname(realpath(__file__))
        }

        # fetch & execute the method corresponding to the product
        # self._prodmap[self.product](self,workarea,env)
        self.make(workarea,env)
