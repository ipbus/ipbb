from __future__ import print_function, absolute_import
from future.utils import raise_with_traceback
# ------------------------------------------------------------------------------

from ..cmds import Environment
from os import walk
from os.path import join, relpath, dirname, basename, exists


# ------------------------------------------------------------------------------
def completePackage(ctx, args, incomplete):
    env = Environment()

    # nothing to complete if not in an ipbb area
    if env.work.path is None:
        return []

    return [pkg for pkg in env.sources if incomplete in pkg]


# ------------------------------------------------------------------------------
def completeComponent(ctx, args, incomplete):
    env = Environment()

    # nothing to complete if not in an ipbb area
    if env.work.path is None:
        return []

    lPkgSeps = incomplete.count(':')
    if lPkgSeps > 1:
        return []
    elif lPkgSeps == 0:
        return [ (p + ':') for p in env.sources if p.startswith(incomplete) ]
        # pkgs = [p for p in env.sources if p.startswith(incomplete) ]
        # comps = []
        # for p in pkgs:
        #     comps += _findComponentsInPackage(env, p)

        # return comps

    else:
        lPkg, incomp_cmp = incomplete.split(':')

        # bail out if package is misspelled
        if lPkg not in env.sources:
            return []

        # Scan the package for matches with the partial component path
        return _findComponentsInPackage(env, lPkg, incomp_cmp)

    return []


# ------------------------------------------------------------------------------
def _findComponentsInPackage(env, pkg, incomp_cmp='', exclude=['.git', '.svn']):
    """
    Helper function to find components in a package, starting from an incomplete component path

    """
    lMatchingComps = []
    lPkgPath = join(env.srcdir, pkg)

    # Resolve the list of paths to 
    lSearchPaths = []
    if incomp_cmp:
        lPartialComPath = join(lPkgPath, dirname(incomp_cmp))
        if not exists(lPartialComPath):
            return []
        lDirHint = basename(incomp_cmp)
        if lDirHint:
            root, dirs, files = next(walk(lPartialComPath))
            lSearchPaths = [join(lPartialComPath, d) for d in dirs if d.startswith(lDirHint)]
        else:
            lSearchPaths = [lPartialComPath]
    else:
        lSearchPaths += [lPkgPath]

    for p in lSearchPaths:
        for root, dirs, files in walk(p, topdown=True):

            if 'firmware' in dirs:
                lMatchingComps += [pkg + ':' + relpath(root, lPkgPath)]
                dirs.remove('firmware')
            dirs[:] = [d for d in dirs if d not in exclude]
            if not dirs:
                continue
            # print(dirs)
    return lMatchingComps