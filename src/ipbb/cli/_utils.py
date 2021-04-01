
from ..context import Context
from os import walk
from os.path import join, relpath, dirname, basename, exists, normpath

from click import command, option, Option, UsageError

# ------------------------------------------------------------------------------
def completeDepFile(cmp_argname):
    def completeDepFileImpl(ctx, args, incomplete):

        # print ('ctx.params', ctx.params)
        # print ('args', args)
        # import ipdb
        # ipdb.set_trace()
        # print (ctx.command.params)
        if ctx.params.get(cmp_argname, None) is None:
            return []
        ictx = Context()
        # nothing to complete if not in an ipbb area
        if ictx.work.path is None:
            return []

        lPkg, lCmp = ctx.params[cmp_argname]
        basepath = ictx.pathMaker.getPath(lPkg, lCmp, 'include')
        if not exists(basepath):
            return []

        from ..depparser import dep_file_types

        # print()
        # print(basepath)

        lDepFiles = []
        for root, dirs, files in walk(basepath):
            lDepFiles += [normpath(f) for f in files if any([f.endswith(ext) for ext in dep_file_types])]

        return [ f for f in lDepFiles if f.startswith(incomplete)]

    return completeDepFileImpl


# ------------------------------------------------------------------------------
def completeProject(ctx, args, incomplete):
    ictx = Context()

    # nothing to complete if not in an ipbb area
    if ictx.work.path is None:
        return []

    return [proj for proj in ictx.projects if incomplete in proj]


# ------------------------------------------------------------------------------
def completeSrcPackage(ctx, args, incomplete):
    ictx = Context()

    # nothing to complete if not in an ipbb area
    if ictx.work.path is None:
        return []

    return [pkg for pkg in ictx.sources if incomplete in pkg]


# ------------------------------------------------------------------------------
def completeComponent(ctx, args, incomplete):
    ictx = Context()

    # nothing to complete if not in an ipbb area
    if ictx.work.path is None:
        return []

    lPkgSeps = incomplete.count(':')
    if lPkgSeps > 1:
        return []
    elif lPkgSeps == 0:
        return [ (p + ':') for p in ictx.sources if p.startswith(incomplete) ]
        # pkgs = [p for p in ictx.sources if p.startswith(incomplete) ]
        # comps = []
        # for p in pkgs:
        #     comps += _findComponentsInPackage(ictx, p)

        # return comps

    else:
        lPkg, incomp_cmp = incomplete.split(':')

        # bail out if package is misspelled
        if lPkg not in ictx.sources:
            return []

        # Scan the package for matches with the partial component path
        return _findComponentsInPackage(ictx, lPkg, incomp_cmp)

    return []


# ------------------------------------------------------------------------------
def _findComponentsInPackage(ictx, pkg, incomp_cmp='', exclude=['.git', '.svn'], match_subdir='firmware'):
    """
    Helper function to find components in a package, starting from an incomplete component path

    """
    lMatchingComps = []
    lPkgPath = join(ictx.srcdir, pkg)

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

            if match_subdir in dirs:
                lMatchingComps += [pkg + ':' + relpath(root, lPkgPath)]
                dirs.remove(match_subdir)
            dirs[:] = [d for d in dirs if d not in exclude]
            if not dirs:
                continue
    return lMatchingComps


from click import command, option, Option, UsageError


# ------------------------------------------------------------------------------
class MutuallyExclusiveOption(Option):

    # Inspired by (and largely re-used from ) this Stack Overflow post:
    # https://stackoverflow.com/questions/37310718/mutually-exclusive-option-groups-in-python-click

    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        help = kwargs.get('help', '')
        if self.mutually_exclusive:
            ex_str = ', '.join(self.mutually_exclusive)
            kwargs['help'] = help + (
                ' NOTE: This argument is mutually exclusive with'
                ' argument(s): [' + ex_str + '].'
            )
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                "Illegal usage: '{}' is mutually exclusive with"
                " '{}'.".format(
                    self.name,
                    ", ".join(self.mutually_exclusive)
                )
            )

        return super().handle_parse_result(
            ctx,
            opts,
            args
        )
