
import time
import os
import shutil
from os.path import abspath, join, split, splitext, exists


# ------------------------------------------------------------------------------
def find_ip_sim_src(projpath: str, projname: str, ipname: str, mode: str = 'file'):
    """Utility function to 
    
    Args:
        projpath (str): Path of the ipbb project
        projname (str): Name of the Vivado project
        ipname (str): Name of the ip path to search
    
    Returns:
        TYPE: Description
    """
    ip_proj_dir = [projpath, projname]

    # base ipcores simulation directories list generator
    dir_list_gen = ( ip_proj_dir + [f'{projname}.{gen_dir}', 'sources_1', 'ip', ipname] for gen_dir in ('gen', 'srcs') )
    # file path generator
    file_list_gen = ( d+[sim_dir, f"{ipname}.{ext}"] for d in dir_list_gen for sim_dir in ('', 'sim') for ext in ('vhd', 'v') )

    if mode == "dir":
        path_list = dir_list_gen
    elif mode == "file":
        path_list = file_list_gen
    else:
        raise ValueError(f'Invalid mode argument value: {mode}')

    for pl in path_list:
        p = abspath(join(*pl))
        if exists(p):
            return p

    return None

class IPCoresSimGenerator(object):

    reqsettings = {'device_name', 'device_package', 'device_speed'}

    # --------------------------------------------------------------
    def __init__(self, aProjInfo, aSimlibPath, aSimulator, aExportDir, aIPProjName):
        self.projInfo = aProjInfo
        self.simlibPath = aSimlibPath
        self.simulator = aSimulator
        self.exportdir = aExportDir
        self.ipProjName = aIPProjName

    # --------------------------------------------------------------
    def write(self, aTarget, aSettings, aComponentPaths, aCommandList, aLibs):

        if not self.reqsettings.issubset(aSettings):
            raise RuntimeError(f"Missing required variables: {', '.join(self.reqsettings.difference(aSettings))}")
        lXilinxPart = f'{aSettings["device_name"]}{aSettings["device_package"]}{aSettings["device_speed"]}'

        write = aTarget

        write('# Autogenerated project build script')
        write(time.strftime('# %c'))
        write()

        lWorkingDir = abspath(join(self.projInfo.path, self.ipProjName))

        write(f'create_project {self.ipProjName} {lWorkingDir} -part {lXilinxPart} -force')

        # Add ip repositories to the project variable
        write(f'set_property ip_repo_paths {{{" ".join([c.filepath for c in aCommandList["iprepo"]])}}} [current_project]')

        write('set_property "default_lib" "xil_defaultlib" [current_project]')
        write('set_property "simulator_language" "Mixed" [current_project]')
        write('set_property "target_language" "VHDL" [current_project]')

        write(f'set_property target_simulator {self.simulator} [current_project]')

        write(
            f'set_property compxlib.{self.simulator}_compiled_library_dir {self.simlibPath} [current_project]'
        )

        write()
        lXCIs = []
        for src in reversed(aCommandList['src']):
            lPath, lBasename = split(src.filepath)
            lName, lExt = splitext(lBasename)

            if lExt in ('.xci', '.xcix', '.edn'):
                write(f'import_files -norecurse -fileset sources_1 {src.filepath}')
                if lExt in ('.xci', '.xcix'):
                    lXCIs.append( (lName, lBasename) )

        if lXCIs:
            lIPs, lIPFiles = zip(*lXCIs)
            write(f'upgrade_ip [get_ips {" ".join(lIPs)}]')

            for lFile in lIPFiles:
                write(f'generate_target simulation [get_files {lFile}]')

        # Is this needed?
        write('set_property top top [get_filesets sim_1]')
        write(f'export_simulation -force -simulator {self.simulator} -directory {self.exportdir} -lib_map_path {self.simlibPath}')

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
