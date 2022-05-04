# NOTE TO SELF: Merge with tools/common.py

import ipaddress
import sys
import re

from click import get_current_context, ClickException, Abort, BadParameter
from os.path import join, split, sep
from typing import NoReturn

from ..console import cprint, console

# ------------------------------------------------------------------------------
def getClickRootName() -> str:
    """
    Returns the name of the root context
    """
    return get_current_context().find_root().info_name

# ------------------------------------------------------------------------------
def raiseError(aMessage: str):
    """
    Print the error message to screen in bright red and a ClickException error
    """

    cprint("\nERROR: " + aMessage + "\n", style='red')
    raise ClickException("Command aborted.")

# ------------------------------------------------------------------------------
def validateComponent(ctx, param: str, value: str) -> tuple:
    """
    Validate package/component syntax
    """
    lTopSeps = value.count(':')
    lPathSeps = value.count(sep)
    # Validate the format
    if not ((lTopSeps == 1) or (lTopSeps == 0 and lPathSeps == 0)):
        raise BadParameter('Malformed component name : %s. Expected <package>:<component>' % value)

    return tuple(value.split(':'))


# ------------------------------------------------------------------------------
def validateMultiplePackageOrComponents(ctx, param: str, value: str ) -> tuple:
    """
    Validate a sequence of package/component strings
    """
    pocs = []
    for v in value:
        lSeparators = v.count(':')
        # Validate the format
        if lSeparators > 1:
            raise BadParameter('Malformed component name : %s. Expected <package>:<component>' % value)

        pocs.append(tuple(v.split(':')))

    return tuple(pocs)

# ------------------------------------------------------------------------------
def validateOptionalComponent(ctx, param: str, value: str) -> tuple:
    """
    Validate package/components allowing for None values
    """
    if value is None:
        return None
    
    return validateComponent(ctx, param, value)

# ------------------------------------------------------------------------------
def validateIpAddress(value) -> str :
    """
    Validate ip address strings
    """
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
def validateMacAddress(value) -> str:
    """
    Validate mac address strings
    """

    if value is None:
        return

    m = re.match(r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})', value)
    if m is None:
        raise BadParameter('Malformed mac address : %s' % value)

    lHexMac = ''.join([ '%02x' % int(c, 16) for c in value.split(':')])
    return 'X"{}"'.format(lHexMac)




