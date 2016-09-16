from __future__ import print_function
from . import Plugin, DirSentry
import logging
import os


class TestGit(Plugin):
    '''
    CactusFetcher Plugin
    Fetches a project from the same trunk/branch/tag the project was created from.
    '''
    _log = logging.getLogger(__name__)

    @staticmethod
    def addArguments(subparsers,cmd):
        subp = subparsers.add_parser(cmd)
        subp.add_argument('repo',        help='repository', default='repo')
        subp.add_argument('--codebox',        help='Area where the code lives', default='cactusupgrades')

    def __init__(self,**kwargs):
        super(TestGit,self).__init__(**kwargs)

        # make sure the prefix is well behaved
        if self.codebox[-1] == '/': self.codebox = self.codebox[:-1]

    def execute(self):
        try:
            os.makedirs(self.codebox)
        except:
            pass
        # go to the tag directory
        sentry = DirSentry(self.codebox)

        self._run('git clone %s' % (self.repo,))
