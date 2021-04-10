
import time
import os
import shutil
from os.path import abspath, join, split, splitext

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class HLSIpRepoXciGenerator(object):

    reqsettings = {'device_name', 'device_package', 'device_speed'}

    # --------------------------------------------------------------
    def __init__(self, aIPCatalogDir, aXciModName, aExportDir):
        self.ipCatalogDir = aIPCatalogDir
        self.xciModName = aXciModName
        self.exportdir = aExportDir

    # --------------------------------------------------------------
    def write(self, aTarget, aSettings, aComponentPaths, aCommandList, aLibs):

        if not self.reqsettings.issubset(aSettings):
            raise RuntimeError(f"Missing required variables: {', '.join(self.reqsettings.difference(aSettings))}")
        lXilinxPart = f'{aSettings["device_name"]}{aSettings["device_package"]}{aSettings["device_speed"]}'

        write = aTarget

        write('# Autogenerated project build script')
        # write(time.strftime('# %c'))
        # write()

        write(f'create_project -in_memory -part {lXilinxPart} -force')
        write(f'set_property ip_repo_paths {self.ipCatalogDir} [current_project]')
        write('update_ip_catalog -rebuild')
        write('set repo_path [get_property ip_repo_paths [current_project]]')
        ip_vlnv_list = write(f'foreach n [get_ipdefs -filter REPOSITORY==$repo_path] {{ puts "$n" }}')
        if len(ip_vlnv_list) > 1:
            raise RuntimeError(f"Found more than 1 core in HLS ip catalog! {', '.join(ip_vlnv_list)}")
        vlnv = ip_vlnv_list[0]
        write(f'create_ip -vlnv {vlnv} -module_name {self.xciModName} -dir {self.exportdir}')
        write('report_ip_status')

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------