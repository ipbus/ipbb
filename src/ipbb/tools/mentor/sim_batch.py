
import tempfile
import sh
import sys

from os.path import join, split, exists, splitext, basename
from ...utils import which
from .sim_common import autodetect, ModelSimNotFoundError, _vsim, _vcom

# -----------------------------------------------------------------------------
class ModelSimBatch(object):
    """docstring for VivadoBatch"""

    # --------------------------------------------
    def __init__(self, scriptpath=None, echo=False, log=None, cwd=None, dryrun=False):
        super().__init__()

        if scriptpath:
            _, lExt = splitext(scriptpath)
            if lExt not in ['.tcl', '.do']:
                raise ValueError(
                    'Unsupported extension {}. Use \'.tcl\' or \'.do\''.format(lExt)
                )

        self.scriptpath = scriptpath
        self.log = log
        self.terminal = sys.stdout if echo else None
        self.cwd = cwd
        self.dryrun = dryrun

    # --------------------------------------------
    def __enter__(self):
        self.script = (
            open(self.scriptpath, 'w')
            if self.scriptpath
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

        # Guard against missing vivado executable
        if not which('vsim'):
            raise ModelSimNotFoundError(
                "'%s' not found in PATH. Failed to detect ModelSim/QuestaSim" % _vsim
            )

        vsim = sh.Command(_vsim)
        # TODO:

        lRoot, _ = splitext(basename(self.script.name))

        lLog = self.log if self.log else 'transcript_{}.log'.format(lRoot)

        vsim(
            '-c',
            '-l',
            lLog,
            '-do',
            self.script.name,
            '-do',
            'quit',
            _out=sys.stdout,
            _err=sys.stderr,
            _cwd=self.cwd,
        )