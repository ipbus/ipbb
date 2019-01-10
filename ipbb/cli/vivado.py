from __future__ import print_function
# ------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
import sys
import sh
import time
import re
import hashlib

# Elements
from os.path import join, split, exists, splitext, abspath, basename
from click import echo, secho, style, confirm
from texttable import Texttable

from ..tools.common import which, SmartOpen
from .utils import DirSentry, ensureNoMissingFiles, echoVivadoConsoleError

from ..depparser.VivadoProjectMaker import VivadoProjectMaker
from ..tools.xilinx import VivadoOpen, VivadoConsoleError, VivadoSnoozer

# Debugging and testing
#import pdb; pdb.set_trace()

# ------------------------------------------------------------------------------
def ensureVivado(env):
    if env.currentproj.settings['toolset'] != 'vivado':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'vivado', found '%s'" % env.currentproj.settings['toolset'])

    if not which('vivado'):
        # if 'XILINX_VIVADO' not in os.environ:
        raise click.ClickException(
            "Vivado not found. Please source the Vivado environment before continuing.")
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@click.group('vivado', short_help='Set up, syntesize, implement Vivado projects.', chain=True)
@click.option('-p', '--proj', default=None, help="Selected project, if not current")
@click.option('-q', '--quiet', is_flag=True, default=False, help="Suppress most of Vivado messages")
@click.pass_context
def vivado(ctx, proj, quiet):
    '''Vivado command group'''

    env = ctx.obj

    env.vivadoEcho = not quiet

    # lProj = proj if proj is not None else env.currentproj.name
    if proj is not None:
        # Change directory before executing subcommand
        from .proj import cd
        ctx.invoke(cd, projname=proj)
        return
    else:
        if env.currentproj.name is None:
            raise click.ClickException('Project area not defined. Move to a project area and try again')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def vivado_get_command_aliases(self, ctx, cmd_name):
    """
    Temporary hack for backward compatibility
    """
    rv = click.Group.get_command(self, ctx, cmd_name)
    if rv is not None:
        return rv
    if cmd_name == 'project':
        return click.Group.get_command(self, ctx, 'make-project')

import types
vivado.get_command = types.MethodType(vivado_get_command_aliases, vivado)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@vivado.command('make-project', short_help='Assemble the project from sources.')
@click.option('-r/-n', '--reverse/--natural', 'aReverse', default=True)
@click.option('-o/-1', '--optimize/--single', 'aOptimise', default=True, help="Toggle sim script optimisation.")
@click.option('-s', '--to-script', 'aToScript', default=None, help="Write Vivado tcl script to file and exit (dry run).")
@click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Vivado tcl commands to screen and exit (dry run).")
@click.pass_obj
def makeproject(env, aReverse, aOptimise, aToScript, aToStdout):
    '''Make the Vivado project from sources described by dependency files.'''

    lSessionId = 'make-project'

    # Check if vivado is around
    ensureVivado(env)

    lDepFileParser = env.depParser

    # Ensure thay all dependencies have been resolved
    ensureNoMissingFiles(env.currentproj.name, lDepFileParser)

    lVivadoMaker = VivadoProjectMaker(aReverse, aOptimise)

    lDryRun = aToScript or aToStdout

    try:
        with (
            VivadoOpen(lSessionId, echo=env.vivadoEcho) if not lDryRun 
            else SmartOpen(
                # Dump to script
                aToScript if not aToStdout 
                # Dump to terminal
                else None
            )
        ) as lConsole:
            lVivadoMaker.write(
                lConsole,
                lDepFileParser.vars,
                lDepFileParser.components,
                lDepFileParser.commands,
                lDepFileParser.libs,
            )
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        secho("Error caught while generating Vivado TCL commands:\n" +
              "\n".join(lExc), fg='red'
              )
        raise click.Abort()
    # -------------------------------------------------------------------------
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command('check-syntax', short_help='Run the synthesis step on the current project.')
@click.pass_obj
def checksyntax(env):
    
    lSessionId = 'chk-syn'

    lStopOn = [
        'HDL 9-806', # Syntax errors
        'HDL 9-69',  # Type not declared
    ]

    # Check
    lVivProjPath = join(env.currentproj.path, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath)

    ensureVivado(env)

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId, echo=env.vivadoEcho) as lConsole:

            # Open the project
            lConsole('open_project {}'.format(lVivProjPath))

            # Change message severity to ERROR for the isses we're interested in
            lConsole(['set_msg_config -id "{}" -new_severity "ERROR"'.format(e) for e in lStopOn])

            # Execute the syntax check
            lConsole('check_syntax')

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()


    secho("\n{}: Synthax check completed successfully.\n".format(env.currentproj.name), fg='green')   
# ------------------------------------------------------------------------------

# -------------------------------------
def getSynthRunProps(aConsole):
    '''Retrieve the status of synthesis runs
    
    Helper function
    '''

    with VivadoSnoozer(aConsole):
        lSynthesisRuns = aConsole('get_runs -filter {IS_SYNTHESIS}')[0].split()
        lRunProps = {}

        lProps = ['STATUS', 'PROGRESS', 'STATS.ELAPSED']
        
        for lRun in lSynthesisRuns:
            lValues = aConsole([ 'get_property {0} [get_runs {1}]'.format(lProp, lRun) for lProp in lProps ])
            lRunProps[lRun] = dict(zip(lProps, lValues))
    return lRunProps
# -------------------------------------

@vivado.command('synth', short_help='Run the synthesis step on the current project.')
@click.option('-j', '--jobs', type=int, default=None)
# @click.option('-e', '--email', default=None)
@click.pass_obj
def synth(env, jobs):
    '''Run synthesis'''

    lSessionId = 'synth'

    # Check
    lVivProjPath = join(env.currentproj.path, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath)

    ensureVivado(env)

    args = []

    if jobs is not None:
        args +=  ['-jobs {}'.format(jobs)]

    # if email is not None:
        # args +=  ['-email_to {} -email_all'.format(email)]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId, echo=env.vivadoEcho) as lConsole:

            # Open the project
            lConsole('open_project {}'.format(lVivProjPath))


            lRunProps = getSynthRunProps(lConsole)
            lIPRunsToReset  = [ k for k,v in lRunProps.iteritems() if (not k.startswith('synth') and v['STATUS'].startswith('Running'))]

            for run in lIPRunsToReset:
                secho('IP run {} found in running state. Resetting.'.format(run), fg='yellow')
                lConsole('reset_run {}'.format(run))

            lConsole([
                'reset_run synth_1',
                ' '.join(['launch_runs synth_1']+args),
            ])

            while (True):

                lRunProps = getSynthRunProps(lConsole)
                lProps = lRunProps.itervalues().next().keys()

                lSummary = Texttable(max_width=0)
                lSummary.set_deco(Texttable.HEADER | Texttable.BORDER)
                lSummary.add_row(['Run']+lProps)
                for lRun in sorted(lRunProps):
                    lInfo = lRunProps[lRun]
                    lSummary.add_row([lRun]+[ lInfo[lProp] for lProp in lProps ])
                secho('\n'+lSummary.draw(), fg='cyan')

                if lRunProps['synth_1']['PROGRESS'] == '100%':
                    break

                lConsole([
                        'wait_on_run synth_1 -timeout 1',
                    ])


    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()


    secho("\n{}: Synthesis completed successfully.\n".format(env.currentproj.name), fg='green')
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def getIPCoresCompiled(aConsole, proj):
	lVivProjPath = proj.path
	print(lVivProjPath)
	lIPCoresPath = join(lVivProjPath, 'top', 'top.srcs', 'sources_1', 'ip')
	for folder in next(os.walk(lIPCoresPath))[1]:
		if not os.path.isdir(join(lIPCoresPath, folder, 'sim')):
			secho("Simulation directory does not exist for %s. Compiling the ip-core."%(folder), fg='yellow')
			aConsole('generate_target all [get_files %s/top/top.srcs/sources_1/ip/%s/%s.xci]' % (lVivProjPath, folder, folder))
			aConsole('export_ip_user_files -of_objects [get_files %s/top/top.srcs/sources_1/ip/%s/%s.xci] -no_script -sync -force -quiet' % (lVivProjPath,folder,folder))
			aConsole('export_simulation -of_objects [get_files %s/top/top.srcs/sources_1/ip/%s/%s.xci] -directory %s/top/top.ip_user_files/sim_scripts -ip_user_files_dir %s/top/top.ip_user_files -ipstatic_source_dir %s/top/top.ip_user_files/ipstatic -lib_map_path [list {modelsim=%s/top/top.cache/compile_simlib/modelsim} {questa=%s/top/top.cache/compile_simlib/questa} {ies=%s/top/top.cache/compile_simlib/ies} {xcelium=%s/top/top.cache/compile_simlib/xcelium} {vcs=%s/top/top.cache/compile_simlib/vcs} {riviera=%s/top/top.cache/compile_simlib/riviera}] -use_ip_compiled_libs -force -quiet' %(lVivProjPath, folder, folder, lVivProjPath, lVivProjPath, lVivProjPath, lVivProjPath, lVivProjPath, lVivProjPath, lVivProjPath, lVivProjPath, lVivProjPath))

# ------------------------------------------------------------------------------
@vivado.command('sim', short_help='Run the simulation step on the specified dependency.')
@click.option('-rf', '--run-for', metavar='<time> <unit>',type=(int, str), default=(0,'us'), help = "Specify the duration of the simulation of <time> <unit> in addition to the default 1 us.")
@click.option('-g', '--GUI-mode', is_flag=True, help = "Show simulation in Vivado interface.")
@click.option('-c', '--iocheck', is_flag=True, help = "Compare simulation output text to the golden output in golden_hash.txt")
@click.pass_obj
def sim(env, run_for, gui_mode, iocheck):

	lSessionId = 'sim'

	# Check
	lVivProjPath = join(env.currentproj.path, 'top', 'top.xpr')
	if not exists(lVivProjPath):
		raise click.ClickException("Vivado project %s does not exist" % lVivProjPath, fg='red')

	ensureVivado(env)

	#find the test bench name
	proj_file = open(lVivProjPath, 'r')
	proj_file_text = proj_file.read()
	tb_path = re.search('[^/]+/tb_.+\.',proj_file_text).group(0)

	tb_path = tb_path[0:len(tb_path) - 1].split('/')
	board = tb_path[0]
	tb_file = tb_path[1]

	proj_file.close()

	from ..tools.xilinx import VivadoOpen, VivadoConsoleError
	try: #prepare and run simulation
		with VivadoOpen(lSessionId, echo=env.vivadoEcho) as lConsole:
			lConsole('open_project {}'.format(lVivProjPath)) #open the project in Vivado
			lConsole('set_property top {} [get_filesets sim_1]'.format(tb_file)) #set the top file
			lConsole('set_property source_mgmt_mode All [current_project]')
			lConsole('update_compile_order -fileset sources_1') #update compile order
			
			getIPCoresCompiled(lConsole, env.currentproj)
			
            #commented for testing
			lConsole(["launch_simulation"]) #run the simulation in Vivado for 1000ns
			if run_for[0] != 0:
				lConsole('run {}{}'.format(run_for[0],run_for[1])) #extend simulation for time specified
			lConsole("start_gui" if gui_mode else "") #start GUI when specified

	except VivadoConsoleError as lExc:
		echoVivadoConsoleError(lExc)
		raise click.Abort()

	if iocheck: #perform check on the textio output and golden output
		md5 = hashlib.md5()
		with open("../../src/fpga/framework/hdl/tb/{}/golden_hash.txt".format(board), 'r') as g:
			f = open("../../src/fpga/framework/hdl/tb/{}/output_text.txt".format(board), 'r')
			md5.update(f.read()) #feed file to md5sum
			hash_key = md5.hexdigest()
			hash_key_check = False
			for line in g.readlines():
				if line[0] != '#': #ignore comments in golden_hash.txt
					vals = line.split(',')
					if vals[1] == hash_key: #catch matching hash
						hash_key_check = True
						print("Output matched golden output! Calculated hash is: {}".format(hash_key))
						break

			if hash_key_check != True:
				raise click.ClickException(click.style("Simulation output does not match any golden output. Calculated hash is: {}".format(hash_key),fg='red'))

		# except Exception as error:
		# 	print("Error: golden_hash.txt not found")
		# 	raise click.Abort()

	secho("\n{}: Simulation completed successfully.\n".format(env.currentproj.name), fg='green')

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@vivado.command('impl', short_help='Run the implementation step on the current project.')
@click.option('-j', '--jobs', type=int, default=None)
@click.pass_obj
def impl(env, jobs):
    '''Launch implementation run'''

    lSessionId = 'impl'

    # Check
    lVivProjPath = join(env.currentproj.path, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath, fg='red')

    ensureVivado(env)

    lStopOn = [
        'Timing 38-282', # Force error when timing is not met
    ]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId, echo=env.vivadoEcho, stopOnCWarnings=True) as lConsole:

            # Change message severity to ERROR for the isses we're interested in
            lConsole(['set_msg_config -id "{}" -new_severity "ERROR"'.format(e) for e in lStopOn])

            # Open the project
            lConsole('open_project {}'.format(lVivProjPath))
            lConsole([
                'reset_run impl_1',
                'launch_runs impl_1' + (' -jobs {}'.format(jobs) if jobs is not None else ''),
                'wait_on_run impl_1',
            ])
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    secho("\n{}: Implementation completed successfully.\n".format(env.currentproj.name), fg='green')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command('order-constr', short_help='Change the order with which constraints are processed')
@click.option('-i/-r', '--initial/--reverse', 'order', default=True, help='Reset or invert the order of evaluation of constraint files.')
@click.pass_obj
def orderconstr(env, order):
    '''Reorder constraint set'''

    lSessionId = 'order-constr'
    # Check
    lVivProjPath = join(env.currentproj.path, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath, fg='red')

    ensureVivado(env)


    lDepFileParser = env.depParser
    lConstrSrc = [src.FilePath for src in lDepFileParser.commands['src'] if splitext(src.FilePath)[1] in ['.tcl', '.xdc']]
    lCmdTemplate = 'reorder_files -fileset constrs_1 -after [get_files {0}] [get_files {1}]'

    lConstrOrder = lConstrSrc if order else [ f for f in reversed(lConstrSrc)]
    # echo('\n'.join( ' * {}'.format(style(c, fg='blue')) for c in lConstrOrder ))

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId, echo=env.vivadoEcho) as lConsole:
            # Open vivado project
            lConsole('open_project {}'.format(lVivProjPath))
            # lConstraints = lConsole('get_files -of_objects [get_filesets constrs_1]')[0].split()
            # print()
            # print('\n'.join( ' * {}'.format(c) for c in lConstraints ))

            lCmds = [lCmdTemplate.format(lConstrOrder[i], lConstrOrder[i+1]) for i in xrange(len(lConstrOrder)-1)]
            lConsole(lCmds)

            lConstraints = lConsole('get_files -of_objects [get_filesets constrs_1]')[0].split()

        echo('\nNew constraint order:')
        echo('\n'.join( ' * {}'.format(style(c, fg='blue')) for c in lConstraints ))


# 'reorder_files -fileset constrs_1 -before [get_files {0}] [get_files {1}]'.format(,to)
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    secho("\n{}: Constraint order set to.\n".format(env.currentproj.name), fg='green')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@click.command('resource-usage', short_help='Print usage report for the top project.')
@click.pass_obj
def resourceusage(env):

    lSessionId = 'usage'

    # if env.currentproj.name is None:
    #     raise click.ClickException(
    #         'Project area not defined. Move into a project area and try again')

    # Check
    lVivProjPath = join(env.currentproj.path, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath)

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % lVivProjPath,
        'open_run impl_1',
    ]


    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId, echo=env.vivadoEcho) as lConsole:
            lConsole(lOpenCmds)
            # lConsole(lImplCmds)
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@vivado.command('bitfile', short_help="Generate a bitfile.")
@click.pass_obj
def bitfile(env):
    '''Create a bitfile'''

    lSessionId = 'bitfile'

    # if env.currentproj.name is None:
    #     raise click.ClickException(
    #         'Project area not defined. Move into a project area and try again')

    # Check
    lVivProjPath = join(env.currentproj.path, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath)

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % lVivProjPath,
    ]

    lBitFileCmds = [
        'launch_runs impl_1 -to_step write_bitstream',
        'wait_on_run impl_1',
    ]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId, echo=env.vivadoEcho) as lConsole:
            lConsole(lOpenCmds)
            lConsole(lBitFileCmds)
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    secho("\n{}: Bitfile successfully written.\n".format(env.currentproj.name), fg='green')

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command('status', short_help="Show the status of all runs in the current project.")
@click.pass_obj
def status(env):
    '''Show the status of all runs in the current project.'''

    lSessionId = 'status'

    # if env.currentproj.name is None:
    #     raise click.ClickException(
    #         'Project area not defined. Move into a project area and try again')

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % join(env.currentproj.path, 'top', 'top'),
    ]

    lInfos = {}
    lProps = ['STATUS', 'PROGRESS', 'IS_IMPLEMENTATION', 'IS_SYNTHESIS', 'STATS.ELAPSED']

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId, echo=env.vivadoEcho) as lConsole:
            echo('Opening project')
            lConsole(lOpenCmds)
            
            lIPs = lConsole('get_ips')[0].split()

            echo('Retrieving run information')
            # Gather data about existing runs
            lRuns = lConsole('get_runs')[0].split()
            for lRun in sorted(lRuns):
                secho(lRun, fg='blue')

                lCmds = [ 'get_property {0} [get_runs {1}]'.format(lProp, lRun) for lProp in lProps ]
                lValues = lConsole(lCmds)
                lInfos[lRun] = dict(zip(lProps, lValues))

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    echo()
    lSummary = Texttable(max_width=0)
    lSummary.set_deco(Texttable.HEADER | Texttable.BORDER)
    lSummary.header(['Run']+lProps)
    for lRun in sorted(lInfos):
        lInfo = lInfos[lRun]
        lSummary.add_row([lRun]+[ lInfo[lProp] for lProp in lProps ])
    echo(lSummary.draw())


# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
@vivado.command('reset', short_help="Reset synthesis and implementation runs.")
@click.pass_obj
def reset(env):
    '''Reset synth and impl runs'''

    lSessionId = 'reset'

    # if env.currentproj.name is None:
    #     raise click.ClickException(
    #         'Project area not defined. Move into a project area and try again')

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % join(env.currentproj.path, 'top', 'top'),
    ]

    lResetCmds = [
        'reset_run synth_1',
        'reset_run impl_1',
    ]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId, echo=env.vivadoEcho) as lConsole:
            lConsole(lOpenCmds)
            lConsole(lResetCmds)
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()
    
    secho("\n{}: synth_1 and impl_1 successfully reset.\n".format(env.currentproj.name), fg='green')

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command('package', short_help="Package the firmware image and metadata into a standalone archive")
@click.pass_context
@click.option('--tag', '-t', 'aTag', default=None, help="Optional tag to add to the archive name.")
def package(ctx, aTag):
    '''Package bitfile with address table and file list

    '''

    env = ctx.obj

    ensureVivado(env)

    lTopProjPath = 'top'

    if not exists(lTopProjPath):
        secho('Vivado project does not exist. Creating the project...', fg='yellow')
        ctx.invoke(makeproject)


    lBitPath = join(lTopProjPath, 'top.runs', 'impl_1', 'top.bit')
    if not exists(lBitPath):
        secho('Bitfile does not exist. Attempting a build ...', fg='yellow')
        ctx.invoke(bitfile)

    lPkgPath = 'package'
    lSrcPath = join(lPkgPath, 'src')

    # Cleanup first
    sh.rm('-rf', lPkgPath, _out=sys.stdout)

    # Create the folders
    try:
        os.makedirs(join(lSrcPath, 'addrtab'))
    except OSError:
        pass

    # -------------------------------------------------------------------------
    # Generate a json signature file
    import socket
    import time
    secho("Generating summary files", fg='blue')

    # -------------------------------------------------------------------------
    from .dep import hash
    lHash = ctx.invoke(hash, output=join(lSrcPath, 'hashes.txt'), verbose=True)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    lSummary = dict(env.currentproj.settings)
    lSummary.update({
        'time': socket.gethostname().replace('.', '_'),
        'build host': time.strftime("%a, %d %b %Y %H:%M:%S +0000"),
        'md5': lHash.hexdigest(),
    })

    with open(join(lSrcPath, 'summary.txt'), 'w') as lSummaryFile:
        import json
        json.dump(lSummary, lSummaryFile, indent=2)
    echo()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Copy bitfile and address table into the packaging area
    secho("Collecting bitfile", fg='blue')
    sh.cp('-av', lBitPath, lSrcPath, _out=sys.stdout)
    echo()

    secho("Collecting addresstable", fg='blue')
    for addrtab in env.depParser.commands['addrtab']:
        sh.cp('-av', addrtab.FilePath, join(lSrcPath, 'addrtab'), _out=sys.stdout)
    echo()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Tar everything up
    secho("Generating tarball", fg='blue')

    lTgzBaseName = '_'.join(
        [env.currentproj.settings['name']] +
        ([aTag] if aTag is not None else []) +
        [
            socket.gethostname().replace('.', '_'),
            time.strftime('%y%m%d_%H%M')
        ]
    )
    lTgzPath = join(lPkgPath, lTgzBaseName + '.tgz')

    # Zip everything
    sh.tar('cvfz', abspath(lTgzPath), '-C', lPkgPath,
           '--transform', 's|^src|' + lTgzBaseName + '|', 'src', _out=sys.stdout
           )
    echo()

    secho("Package " + style('%s' % lTgzPath, fg='green') + " successfully created.", fg='green')
    # -------------------------------------------------------------------------
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_context
def archive(ctx):

    lSessionId = 'archive'

    env = ctx.obj

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % join(env.currentproj.path, 'top', 'top'),
    ]
    lArchiveCmds = [
        'archive_project %s -force' % join(env.currentproj.path, '{}.xpr.zip'.format(env.currentproj.settings['name'])),
    ]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId, echo=env.vivadoEcho) as lConsole:
            lConsole(lOpenCmds)
            lConsole(lArchiveCmds)
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()
# ------------------------------------------------------------------------------
