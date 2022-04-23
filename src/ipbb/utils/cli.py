# NOTE TO SELF: Merge with tools/common.py

import ipaddress
import sys
import re

from click import get_current_context, ClickException, Abort, BadParameter
from os.path import join, split,
from typing import NoReturn

# from ..tools.alien import AlienBranch
# from ..console import cprint, console
# from ..depparser import DepFormatter

# ------------------------------------------------------------------------------
def validateComponent(ctx, param, value):
    lTopSeps = value.count(':')
    lPathSeps = value.count(os.path.sep)
    # Validate the format
    if not ((lTopSeps == 1) or (lTopSeps == 0 and lPathSeps == 0)):
        raise BadParameter('Malformed component name : %s. Expected <package>:<component>' % value)

    return tuple(value.split(':'))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def validateMultiplePackageOrComponents(ctx, param, value):
    pocs = []
    for v in value:
        lSeparators = v.count(':')
        # Validate the format
        if lSeparators > 1:
            raise BadParameter('Malformed component name : %s. Expected <package>:<component>' % value)

        pocs.append(tuple(v.split(':')))

    return tuple(pocs)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def validateOptionalComponent(ctx, param, value):
    if value is None:
        return None
    
    return validateComponent(ctx, param, value)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def validateIpAddress(value):
    if value is None:
        return

    try:
        lIp = ipaddress.ip_address(value)
    except ValueError as lExc:
        # raise_with_traceback(BadParameter(str(lExc)), sys.exc_info()[2])
        tb = sys.exc_info()[2]
        raise BadParameter(str(lExc)).with_traceback(tb)

    lHexIp = ''.join([ '%02x' % ord(c) for c in lIp.packed])

    return 'X"{}"'.format(lHexIp)


# ------------------------------------------------------------------------------
def validateMacAddress(value):

    if value is None:
        return

    m = re.match(r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})', value)
    if m is None:
        raise BadParameter('Malformed mac address : %s' % value)

    lHexMac = ''.join([ '%02x' % int(c, 16) for c in value.split(':')])
    return 'X"{}"'.format(lHexMac)


# ------------------------------------------------------------------------------
def getClickRootName():
    return get_current_context().find_root().info_name
