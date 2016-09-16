#!/usr/bin/env python

'''
Usage:

will come at some point


'''

from __future__ import print_function
import argparse
import sys
import os
# import time
# import shelve
import logging

# #---
# class DirSentry:
#
#     def __init__(self, dir):
#         if not os.path.exists(dir):
#             raise RuntimeError('stocazzo '+dir)
#
#         self._olddir = os.path.realpath(os.getcwd())
#
#         os.chdir(dir)
#         logging.info('-- cd',dir)
#
#
#     def __del__(self):
#         os.chdir(self._olddir)
#         logging.info('-- cd',self._olddir)
#
# #---
# class Plugin(object):
#
#     def __init__(self, **kwargs):
#         for k,v in kwargs.iteritems():
#             setattr(self,k,v)
#
#
#     def execute():
#         print('Nothing to do')
#
#
#     def _run(self, cmd):
#         self._log.info('Command:',cmd)
#         os.system( cmd )
#
#
# #------------------------------------------------------------------------------
# # SVN plugin base class
# #------------------------------------------------------------------------------
#
# class SvnPlugin(Plugin):
#     '''
#     Base SVN plugin.
#     Implements several helper function used in the derived classes.
#     '''
#     _log = logging.getLogger(__name__)
#
#     def __init__(self,**kwargs):
#         super(SvnPlugin,self).__init__(**kwargs)
#
#
#     def _checkOutCactus(self,svnpath):
#         from os.path import exists,join
#         if ( exists(self.cactusRoot) and exists(join(self.cactusRoot,'.svn'))):
#             self._log.debug(self.cactusRoot,'already exists. Will use it')
#             return
#         cmd = 'svn co --depth=empty %s' % svnpath
#         if self.prefix:
#             cmd+=' '+self.cactusRoot
#
#         self._run(cmd)
#
#
#     def _rebuildEmpty(self, tag):
#         tokens = [ d for d in tag.split('/') if d ]
#
#         partials =  [ '/'.join(tokens[:i+1]) for i,_ in enumerate(tokens) ]
#
#         for s in partials:
#             cmd = 'svn up --depth=empty %s' % s
#             self._run(cmd)
#
#     def _switch(self, folder, fromtag):
#         cmd = 'svn switch %s %s' % ( os.path.join(fromtag, folder), folder )
#         self._run(cmd)
#
#
#     def _cactusCheckout(self, folder, fromtag):
#         # go to the tag directory
#         sentry = DirSentry(self.cactusRoot)
#
#         # sanitize the foldername
#         if folder[-1]=='/': folder = folder[:-1]
#
#         # and check it out in its final path
#         cmd = 'svn co %s %s' % ( os.path.join(fromtag, 'cactusupgrades', folder), folder )
#         self._run(cmd)
#
#     def _checkout(self, svnroot, folder, dest):
#         # go to the tag directory
#         sentry = DirSentry(self.cactusRoot)
#
#         # sanitize the foldername
#         if folder[-1]=='/': folder = folder[:-1]
#
#         # and check it out in its final path
#         cmd = 'svn co %s %s' % ( os.path.join(svnroot, folder), dest )
#         self._run(cmd)
#
#
#     def _fetch(self, folder):
#         # go to the tag directory
#         sentry = DirSentry(self.cactusRoot)
#
#         # sanitize the foldername
#         if folder[-1]=='/': folder = folder[:-1]
#
#         self._rebuildEmpty(folder)
#
#         # finally fetch the full folder
#         cmd = 'svn up --set-depth=infinity %s' % folder
#         self._run(cmd)
#
#
#     def _fetchAndSwitch(self, folder, fromtag):
#         # go to the tag directory
#         sentry = DirSentry(self.cactusRoot)
#
#         # sanitize the foldername
#         if folder[-1]=='/': folder = folder[:-1]
#
#         self._rebuildEmpty(folder)
#
#         cmd = 'svn switch %s %s' % ( os.path.join(fromtag, 'cactusupgrades', folder), folder )
#         self._run(cmd)
#
#
#         # finally fetch the full folder
#         cmd = 'svn up --set-depth=infinity %s' % folder
#         self._run(cmd)
#
#
#     def _checkPath(self, svnurl ):
#         # attempt an svn ls
#         retval = os.system('svn ls --depth=empty '+svnurl+ '> /dev/null 2>&1')
#
#         # and throw if it fails
#         if retval:
#             raise RuntimeError(svnurl+' does not exists')
#
#
#     def _mkLocalDir(self,folder):
#
#         try:
#             os.makedirs(os.path.join(self.cactusRoot,folder))
#         except OSError:
#             pass
#
#
#     def _findFirstExisting(self, svnroot, paths):
#         sentry = DirSentry(self.cactusRoot)
#
#         notFound = []
#         for p in paths:
#             try:
#                 svnpath = os.path.join(svnroot, p)
#                 self._checkPath(svnpath)
#             except RuntimeError as e:
#                 notFound.append(svnpath)
#                 continue
#
#             return p
#
#         raise RuntimeError('Failed to find tag path. Search paths:'+''.join(['\n   '+s for s in notFound]))
#
# #------------------------------------------------------------------------------
# # CactusFetcher plugin
# #------------------------------------------------------------------------------
#
# class CactusFetcher(SvnPlugin):
#     '''
#     CactusFetcher Plugin
#     Fetches a project from the same trunk/branch/tag the project was created from.
#     '''
#     _log = logging.getLogger(__name__)
#
#     @staticmethod
#     def addArguments(subparsers,cmd):
#         subp = subparsers.add_parser(cmd)
#         subp.add_argument('project', help='project to checkout')
#         subp.add_argument('--prefix',        help='checkout prefix', default='cactusupgrades')
#
#     def __init__(self, **kwargs):
#         super(CactusFetcher,self).__init__(**kwargs)
#
#         # make sure the prefix is well behaved
#         if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]
#
#         self.cactusRoot = os.path.realpath(self.prefix)
#
#     def execute(self):
#         import os
#
#         if not os.path.exists(self.prefix):
#             raise ValueError('Directory %s does not exist' % self.prefix)
#         folders = [self.project]
#
#         print('Retrieving:')
#         print('\n'.join(folders))
#
#         for f in folders:
#             self._fetch( f )
#
# #------------------------------------------------------------------------------
# # CactusCheckout plugin
# #------------------------------------------------------------------------------
#
# class CactusCheckout(SvnPlugin):
#     '''
#     '''
#     _log = logging.getLogger(__name__)
#
#     @staticmethod
#     def addArguments(subparsers,cmd):
#         subp = subparsers.add_parser(cmd)
#         subp.add_argument('project', help='project to checkout')
#         subp.add_argument('-t', '--fromtag', help='fetch the project from a different tag')
#         subp.add_argument('--prefix',        help='checkout prefix', default='cactusupgrades')
#
#     def __init__(self, **kwargs):
#         super(CactusCheckout,self).__init__(**kwargs)
#
#         # make sure the prefix is well behaved
#         if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]
#
#         self.cactusRoot = os.path.realpath(self.prefix)
#
#     def execute(self):
#         import os
#
#         if not os.path.exists(self.prefix):
#             raise ValueError('Directory %s does not exist' % self.prefix)
#         folders = [self.project]
#
#         print('Retrieving:')
#         print('\n'.join(folders))
#
#         # Take the foder from a different tag
#         tagPath = os.path.join('^/',self.fromtag)
#
#         for f in folders:
#             self._cactusCheckout( f, tagPath )
#
# #------------------------------------------------------------------------------
# # CactusProjectAdder plugin
# #------------------------------------------------------------------------------
#
# class CactusProjectAdder(SvnPlugin):
#     '''
#     CactusProjectAdder : checks out a project form a different area of cactus
#     '''
#     _log = logging.getLogger(__name__)
#
#     @staticmethod
#     def addArguments(subparsers,cmd):
#         subp = subparsers.add_parser(cmd)
#         subp.add_argument('project', help='Project to checkout')
#         subp.add_argument('fromtag', help='Tag to check the project from')
#         subp.add_argument('--svnroot', help='Alternate repository to take the tag from', default=None)
#         subp.add_argument('--prefix', help='Checkout prefix', default='cactusupgrades')
#
#
#     def __init__(self, **kwargs):
#         super(CactusProjectAdder,self).__init__(**kwargs)
#
#         # make sure the prefix is well behaved
#         if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]
#
#         self.cactusRoot = os.path.realpath(self.prefix)
#
#     def execute(self):
#         import os
#
#         if not os.path.exists(self.prefix):
#             raise ValueError('Directory %s does not exist' % self.prefix)
#
#
#         print('Discovering the svn project path in tag '+self.fromtag)
#         # Discover the correct folder to check out
#         sentry = DirSentry(self.cactusRoot)
#         repo = self.svnroot if self.svnroot else '^/'
#         print('Using svn repository:', repo)
#         tagPath = os.path.join(repo,self.fromtag)
#
#         subPaths = [
#                     os.path.join('cactusupgrades/projects', self.project),
#                     os.path.join(self.project)
#                 ]
#         svnpath = self._findFirstExisting( tagPath, subPaths )
#
#         print('Retrieving:')
#         print('\n'+ svnpath)
#
#         # First ensure <cactusRoot>/projects exists
#         self._mkLocalDir('projects')
#
#         self._checkout(tagPath,svnpath,os.path.join('projects',self.project))
#
#
#
# #------------------------------------------------------------------------------
# # CactusCreator plugin
# #------------------------------------------------------------------------------
#
# class CactusCreator(SvnPlugin):
#     _log = logging.getLogger(__name__)
#
#     @staticmethod
#     def addArguments(subparsers,cmd):
#         subp = subparsers.add_parser(cmd)
#         subp.add_argument('tag',             help='tag to checkout - it must contain a "cactusupgrades" folder.', default='trunk')
#         subp.add_argument('-b','--board',             help='board area to check out.', default=None)
#         subp.add_argument('-u', '--user',    help='svn username', default=os.getlogin())
#         subp.add_argument('--prefix',        help='Checkout prefix', default='cactusupgrades')
#
#     def __init__(self, **kwargs):
#         super(CactusCreator,self).__init__(**kwargs)
#
#         # make sure the prefix is well behaved
#         if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]
#
#         self.cactusRoot = os.path.realpath(self.prefix)
#
#     def execute(self):
#         import os
#
#         svnpath = 'svn+ssh://%s@svn.cern.ch/reps/cactus/%s/cactusupgrades' % (self.user,self.tag)
#
#         print('Checking out tag',self.tag)
#         self._checkPath(svnpath)
#         self._checkOutCactus(svnpath)
#
#         folders = ['scripts', 'components']
#         folders += ['boards'] if not self.board else [os.path.join('boards',self.board)]
#
#         print('Retrieving:')
#         print('\n'.join(folders))
#
#         for f in folders:
#             self._fetch( f )
#
# #------------------------------------------------------------------------------
# # WorkareaBuilder plugin
# #------------------------------------------------------------------------------
#
# class WorkareaBuilder(Plugin):
#     _log = logging.getLogger(__name__)
#
#     def __init__(self, **kwargs):
#         super(WorkareaBuilder,self).__init__(**kwargs)
#
#         if self.prefix[-1] == '/': self.prefix = self.prefix[:-1]
#
#
#     @staticmethod
#     def addArguments(subparsers,cmd):
#         # parser_add = parser.add_subparsers(dest = 'cmd')
#         subp = subparsers.add_parser(cmd)
#         subp.add_argument('project',        help='project to build')
#         subp.add_argument('top', nargs = '?', default='top', help = 'top level name')
#         subp.add_argument('-w','--workarea')
#         subp.add_argument('--prefix',       help='checkout prefix', default='cactusupgrades')
#
#     def make(self,workarea,env):
#         pass
#
#
#     def execute(self):
#         from os.path import realpath,basename,dirname,join
#
#         here = realpath(dirname(__file__))
#
#         self._log.info('script path',here)
#         self._log.info('Project:',self.project)
#
#         projectpath=self.project
#         if not os.path.exists(self.prefix):
#             raise RuntimeError('Project %s not found at %s' % (self.project, self.prefix) )
#
#         workarea = self.workarea if self.workarea else basename(self.project)
#
#         env = {
#             'REPLACE_BUILD_PROJECT':projectpath,
#             'REPLACE_TOPLVL':self.top,
#             'CACTUS_ROOT':realpath(self.prefix),
#             'SCRIPT_PATH':dirname(realpath(__file__))
#         }
#
#         # fetch & execute the method corresponding to the product
#         # self._prodmap[self.product](self,workarea,env)
#         self.make(workarea,env)


# #------------------------------------------------------------------------------
# #    __  ___        __    __    _       ___                ___       _ __   __
# #   /  |/  /__  ___/ /__ / /__ (_)_ _  / _ | _______ ___ _/ _ )__ __(_) /__/ /__ ____
# #  / /|_/ / _ \/ _  / -_) (_-</ /  ' \/ __ |/ __/ -_) _ `/ _  / // / / / _  / -_) __/
# # /_/  /_/\___/\_,_/\__/_/___/_/_/_/_/_/ |_/_/  \__/\_,_/____/\_,_/_/_/\_,_/\__/_/
# #                                                                                   #
# #------------------------------------------------------------------------------
#
# #------------------------------------------------------------------------------
# # Environment template
# #------------------------------------------------------------------------------
#
# envSimTemplate='''
# #!/bin/bash
#
# # Comment this line after customizing the environment
# # warning && return 1
#
# # Check for Xilinx environment
# if [ -z "$XILINX_VIVADO" ]; then
# echo "No Xilinx, no party"
# return
# fi
#
# # Path to modelsim executables
# # export PATH=$PATH:/software/CAD/Mentor/2013_2014/Questa/HDS_2012.2b/questasim/bin
#
# # This makes it go fast
# MTI_VCO_MODE=64
#
# # Where to find the various libraries and headers
# MODELSIM_ROOT=${MODELSIM_ROOT:-"/opt/mentor/modeltech/"}
#
# # Add it to the path to make finding modelsim easier
# PATH="${MODELSIM_ROOT}/bin:${PATH}"
#
# # Location of pre-compiled Xilinx libraries
# XILINX_SIMLIBS=.xil_sim_libs/$(basename ${XILINX_VIVADO})
#
# vars="MODELSIM_ROOT"
#
# notfound=0
# for v in $vars; do
#     echo ${v} ${!v}
#     if [ ! -d "${!v}" ]; then
#         echo "WARNING: $v does not exits"
#         (( notfound++ ))
#     fi
# done
#
# if [ $notfound -ne 0 ]; then
#    echo "Some directoried were not found. Check the settings in this file";
#    echo "No environment variable was set";
#    return;
# fi
#
# export PATH MTI_VCO_MODE MODELSIM_ROOT XILINX_SIMLIBS
# '''
#
#
# #------------------------------------------------------------------------------
# # Makefile template
# #------------------------------------------------------------------------------
#
# mkSimTemplate='''
# BUILD_PROJECT:={REPLACE_BUILD_PROJECT}
# TOPLVL:={REPLACE_TOPLVL}
# CACTUS_ROOT:={CACTUS_ROOT}
# SCRIPT_PATH:={SCRIPT_PATH}
#
# DEPFILE:=$(TOPLVL).dep
#
# # Derived paths
# UPGRADES_ROOT:=$(CACTUS_ROOT)
# DEPTREE:=$(SCRIPT_PATH)/dep_tree.py
# IPSIM_FOLDER:=$(TOPLVL)/$(TOPLVL).srcs/sources_1/ip
#
# .PHONY: help project fli _checkenv ipsim addrtab decode
#
# help:
# \t@echo "Please choose one of the following target: project bitfile addrtab package clean cleanproject"
#
# project: _checkenv fli ipsim
#
# \t$(DEPTREE) -p s $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) -o mkProject.tcl
# \t$(MODELSIM_ROOT)/bin/vsim -c -do "do mkProject.tcl; quit"
#
# ipsim: $(IPSIM_FOLDER)/built
#
# $(IPSIM_FOLDER)/built:
# \techo Building IPCores simulation
# \t$(DEPTREE) -p ip $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) -o mkSimIPs.tcl
# \tvivado -mode batch -source mkSimIPs.tcl
# \ttouch $@
#
# fli: _checkenv mac_fli.so
#
# mac_fli.so:
# \trm -rf modelsim_fli
# \tcp -a $(UPGRADES_ROOT)/components/ipbus_eth/firmware/sim/modelsim_fli ./
# \tcd modelsim_fli && ./mac_fli_compile.sh
# \tcp modelsim_fli/mac_fli.so .
#
# _checkenv:
# ifndef MODELSIM_ROOT
# \t$(error MODELSIM_ROOT is not defined)
# endif
#
# clean:
# \t@dir -1 | grep -v -e  '^\(Makefile\|env.sh\|env_example.sh\)' | xargs rm -rf
# \t@rm -rf $(XILINX_SIMLIBS)
#
# addrtab:
# \t@echo "Collecting address tables..."
# \t@mkdir -p addrtab
# \t@$(DEPTREE) -p a $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) | xargs -tI: cp : addrtab
# \t@echo "Done."
#
# decode: addrtab
# \trm -rf decoders
# \tcp -a addrtab decoders
# \t$(DEPTREE) -p b $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) -o decoders/update.sh
# \tchmod a+x decoders/update.sh
# \texport PATH=/opt/cactus/bin/uhal/tools:$$PATH; cd decoders && ./update.sh
# '''
#
# class ModelsimAreaBuilder(WorkareaBuilder):
#     _log = logging.getLogger(__name__)
#
#     def __init__(self, **kwargs):
#         super(ModelsimAreaBuilder,self).__init__(**kwargs)
#
#     def make(self,workarea,env):
#         from os.path import join
#
#         self._log.info('Creating a new ModelSim area')
#         try:
#             os.makedirs(workarea)
#         except:
#             self._log.info('Directory %s exists' % workarea)
#
#         # Modelsim: create environment file
#         envsim=join(workarea,'env.sh')
#         with open(envsim,'w') as f:
#             f.write(
#                 envSimTemplate
#                 )
#             self._log.info('File %s created' % envsim)
#
#         # Modelsim: create makefile
#         mksim = join(workarea,'Makefile')
#         with open(mksim,'w') as f:
#             f.write(
#                 mkSimTemplate.format(**env)
#                 )
#             self._log.info('File %s created' % mksim)
#
#



# #------------------------------------------------------------------------------
# #  _   ___              __     ___                ___       _ __   __
# # | | / (_)  _____ ____/ /__  / _ | _______ ___ _/ _ )__ __(_) /__/ /__ ____
# # | |/ / / |/ / _ `/ _  / _ \/ __ |/ __/ -_) _ `/ _  / // / / / _  / -_) __/
# # |___/_/|___/\_,_/\_,_/\___/_/ |_/_/  \__/\_,_/____/\_,_/_/_/\_,_/\__/_/
# #
# #------------------------------------------------------------------------------
# mkVivadoTemplate='''
# BUILD_PROJECT:={REPLACE_BUILD_PROJECT}
# TOPLVL:={REPLACE_TOPLVL}
# PROJNAME:=top
# CACTUS_ROOT:={CACTUS_ROOT}
#
# # Derived paths
# UPGRADES_ROOT:=$(CACTUS_ROOT)
# DEPTREE:=$(CACTUS_ROOT)/scripts/firmware/dep_tree.py
#
# # Timestamp
# TIMESTAMP=$(shell date +%y%m%d_%H%M)
#
# # Define target filenames
# ifdef name
# PKGNAME=$(name)
# else
# PKGNAME:=$(TOPLVL)
# endif
#
# DEPFILE:=$(TOPLVL).dep
# PROJECTFILE:=$(PROJNAME)/$(PROJNAME).xpr
# BITFILE:=$(PROJNAME)/$(PROJNAME).runs/impl_1/$(PROJNAME).bit
# PACKAGEFILE:=$(PKGNAME)_$(TIMESTAMP).tgz
#
#
# # Tcl commands
# define TCL_BUILD_BITFILE
# open_project $(PROJECTFILE)
# launch_runs synth_1
# wait_on_run synth_1
# launch_runs impl_1
# wait_on_run impl_1
# launch_runs impl_1 -to_step write_bitstream
# wait_on_run impl_1
# exit
# endef
# export TCL_BUILD_BITFILE
#
# define TCL_RESET_PROJECT
# open_project $(PROJECTFILE)
# reset_run synth_1
# exit
# endef
# export TCL_RESET_PROJECT
#
# .PHONY: clean reset addrtab decode
#
# $(PROJECTFILE):
# \t@$(DEPTREE) -p v $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) -o mkProject.tcl
# \t@vivado -mode batch -source mkProject.tcl
#
# $(BITFILE):
# \t@echo "$$TCL_BUILD_BITFILE" > mkBitfile.tcl
# \tvivado -mode batch -source mkBitfile.tcl
#
# $(PACKAGEFILE): addrtab bitfile
# \tmkdir -p pkg/src
# \tcp $(BITFILE) pkg/src/
# \tcp -a addrtab/ pkg/src/
# \ttar cvfz pkg/$(PACKAGEFILE) -C pkg/src addrtab $(PROJNAME).bit
#
# project: $(PROJECTFILE)
#
# bitfile: $(BITFILE)
#
# package: $(PACKAGEFILE)
#
# clean:
# \t@dir -1 | grep -v Makefile | xargs rm -rf
#
# reset:
# \trm -f $(BITFILE)
# \t@echo "$$TCL_RESET_PROJECT" > resetProject.tcl
# \tvivado -mode batch -source resetProject.tcl
#
#
# addrtab:
# \t@echo "Collecting address tables..."
# \t@mkdir -p addrtab
# \t@$(DEPTREE) -p a $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) | xargs -tI: cp : addrtab
# \t@echo "Done."
#
# decode: addrtab
# \trm -rf decoders
# \tcp -a addrtab decoders
# \t$(DEPTREE) -p b $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) -o decoders/update.sh
# \tchmod a+x decoders/update.sh
# \texport PATH=/opt/cactus/bin/uhal/tools:$$PATH; cd decoders && ./update.sh
# '''
#
# #------------------------------------------------------------------------------
# # VivadoAreaBuilder implementation
# #------------------------------------------------------------------------------
# class VivadoAreaBuilder(WorkareaBuilder):
#     _log = logging.getLogger(__name__)
#
#     def __init__(self, **kwargs):
#         super(VivadoAreaBuilder,self).__init__(**kwargs)
#
#     def make(self,workarea,env):
#         from os.path import join
#
#         self._log.info('Creating a new Vivado area')
#         try:
#             os.makedirs(workarea)
#         except:
#             self._log.info('Directory %s exists' % workarea)
#
#         # Vivado: create makefile
#         mkviv=join(workarea,'Makefile')
#
#         with open(mkviv,'w') as f:
#             f.write(
#                 mkVivadoTemplate.format(**env)
#                 )
#             self._log.info('File %s created' % mkviv)

#---
class CliFactory(object):
    def __init__(self, plugins):
        self.parser = argparse.ArgumentParser(
            description='Assists in setting up a firmware build and simulation area',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )

        subparsers = self.parser.add_subparsers(dest = 'cmd')
        for cmd,cls in plugins.iteritems():
            cls.addArguments(subparsers,cmd)

        self._plugins = plugins

    def get(self):
        val = self.parser.parse_args()

        plugin_cls = self._plugins[val.cmd]

        plugin = plugin_cls(**vars(val))

        return plugin

if __name__ == '__main__':

    from projmgr import CactusCreator, CactusProjectAdder, CactusFetcher, CactusCheckout, WorkareaBuilder
    from projmgr.vivado import VivadoAreaBuilder
    from projmgr.modelsim import ModelsimAreaBuilder

    plugins = {
        'create'   : CactusCreator,
        'addproj'  : CactusProjectAdder,
        'fetch'    : CactusFetcher,
        'checkout' : CactusCheckout,
        'buildarea': WorkareaBuilder,
        'sim'      : ModelsimAreaBuilder,
        'vivado'   : VivadoAreaBuilder,
    }

    cli_factory = CliFactory( plugins )
    plugin = cli_factory.get()

    try:
        plugin.execute()
    except Exception as e:

        print('\n- ERROR ---\n',e)
