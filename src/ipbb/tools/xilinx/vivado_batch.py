from __future__ import print_function, absolute_import
from builtins import range
import six
# ------------------------------------------------------------------------------

import re
import sh

# ------------------------------------------------------------------------------
class VivadoBatch(object):
    """
    Wrapper class to run Vivado jobs in batch mode
    """
    _reInfo = re.compile(u'^INFO:')
    _reWarn = re.compile(u'^WARNING:')
    _reCritWarn = re.compile(u'^CRITICAL WARNING:')
    _reError = re.compile(u'^ERROR:')

    # --------------------------------------------
    def __init__(self, scriptpath=None, echo=False, log=None, cwd=None, dryrun=False):
        super(VivadoBatch, self).__init__()

        if scriptpath:
            _, lExt = splitext(scriptpath)
            if lExt not in ['.tcl', '.do']:
                raise ValueError('Unsupported extension {}. Use \'.tcl\' or \'.do\''.format(lExt))

        self.scriptpath = scriptpath
        self.log = log
        self.terminal = sys.stdout if echo else None
        self.cwd = cwd
        self.dryrun = dryrun

    # --------------------------------------------
    def __enter__(self):
        self.script = (
            open(self.scriptpath, 'wt') if self.scriptpath
            else tempfile.NamedTemporaryFile(mode='w+t', suffix='.do')
        )
        return self

    # --------------------------------------------
    def __exit__(self, type, value, traceback):
        if not self.dryrun:
            self._run()
        self.script.close()

    # --------------------------------------------
    def __call__(self, *strings):
        for f in [self.script, self.terminal]:
            if not f:
                continue
            f.write(' '.join(strings) + '\n')
            f.flush()

    # --------------------------------------------
    def _run(self):

        # Define custom log file
        lRoot, _ = splitext(basename(self.script.name))
        lLog = 'vivado_{0}.log'.format(lRoot)
        lJou = 'vivado_{0}.jou'.format(lRoot)

        # Guard against missing vivado executable
        if not which('vivado'):
            raise VivadoNotFoundError(
                '\'vivado\' not found in PATH. Have you sourced Vivado\'s setup script?'
            )

        sh.vivado('-mode', 'batch', '-source', self.script.name, '-log', lLog, '-journal', lJou, _out=sys.stdout, _err=sys.stderr)
        self.errors = []
        self.info = []
        self.warnings = []

        with open(lLog) as lLogFile:
            for i, l in enumerate(lLogFile):
                if self._reError.match(l):
                    self.errors.append((i, l))
                elif self._reWarn.match(l):
                    self.warnings.append((i, l))
                elif self._reInfo.match(l):
                    self.info.append((i, l))
    # --------------------------------------------
# -------------------------------------------------------------------------