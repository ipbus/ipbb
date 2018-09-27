This is the documentations for the Vivado simulation environment. It goes through setting up the environment for libraries modules and full-FPGA designs. It also include documentations for using the simulation and its options.

This is written by
Musaab Al-Bakry
mual3221@colorado.edu

Supervised
Robert Glein
robert.glein@colorado.edu

In case of a library module:
	#initial checks:

		- Make sure that your library module is in lib/hdl/design
		- Make sure that the library dependency file is in lib/cfg

	#prepare library module project:
	#Let us assume we start on the general ipbb project directory

		- Source the ipbb enviroment
			command: source ../ipbb/env.sh #change the path if necessary
		- Change directory and make simulation directory
			commands:
				cd src/fpga/lib/cfg
				mkdir sim #if it doesn't exist already
				cd sim
		- Create dependency file for the simulation
			commands:
				touch $PROJ_NAME.dep (example: touch stub_if.dep)
			add the original dependency file, the test bench, and the board information:
				example content of dependency file:
					include ../../lib/cfg/stub_if.dep #dependency
					src ../../lib/hdl/tb/stub_if/tb_mux64.vhd #test bench
					#if you need to incorporate an ip-core:
						example: src ../../framework/hdl/ip/xilinx/ila/ila_0/sim/ila_0.vhd
					#For the board information:
						example:
							setup ../../framework/cfg/vcu118/settings_vu.tcl
							include ../../framework/cfg/vcu118/vu9p.dep
		- Source the Vivado build enviroment
			command: source $VIVADO_PATH_SH
			example: source /opt/Xilinx/Vivado/2018.2/settings64.sh
		- Create new simulation project (recommended: $PROJ_NAME_sim) with the simulation dependency file
			command: ipbb proj create vivado $PROJ_NAME fpga:./ -t $PROJ_PATH
			example: ipbb proj create vivado stub_if_sim fpga:./ -t ../../lib/cfg/sim/stub_if.dep

In case of a full-FPGA design:
	#initial checks:

		- Make sure that your library module is in framework/hdl/design/$BOARD_NAME
		- Make sure that the library dependency file is in framework/cfg/$BOARD_NAME

	#prepare library module project:
	#Let us assume we start on the general ipbb project directory

		- Source the ipbb enviroment
			command: source ../ipbb/env.sh #change the path if necessary
		- Change directory and make simulation directory
			commands:
				cd src/fpga/framework/cfg/vcu118
				mkdir sim #if it doesn't exist already
				cd sim
		- Create dependency file for the simulation
			commands:
				touch $PROJ_NAME.dep (example: touch top_vcu118.dep)
			add the original dependency file and the test bench:
				example content of dependency file:
					include ../../framework/cfg/vcu118/top_vcu118.dep #dependency
					src ../../framework/hdl/tb/tb_top_vcu118.vhd #test bench
					#if you need to incorporate an ip-core:
						example: src ../../framework/hdl/ip/xilinx/ila/ila_0/sim/ila_0.vhd
		- Source the Vivado build enviroment
			command: source $VIVADO_PATH_SH
			example: source /opt/Xilinx/Vivado/2018.2/settings64.sh
		- Create new simulation project (recommended: $PROJ_NAME_sim) with the simulation dependency file
			command: ipbb proj create vivado $PROJ_NAME fpga:./ -t $PROJ_PATH
			example: ipbb proj create vivado vcu118_blink_led_sim fpga:./ -t ../../framework/cfg/vcu118/sim/vcu118_blink_led.dep

make the project:
Do this step for any new change in the simulation dependency file.

	#Make the project
		commands:
			cd proj/$PROJ_NAME
			ipbb vivado make-project
		example:
			cd proj/stub_if_sim
			ipbb vivado make-project

Simulate your project
	command: ipbb vivado sim

	To get help in all the options for running this command, use $ipbb vivado sim -h
	Content of the help:
		Usage: ipbb vivado sim [OPTIONS]

		Options:
		  -rf, --run-for <time> <unit>  Specify the duration of the simulation of
		                                <time> <unit> in addition to the default 1 us.
		  -g, --GUI-mode                Show simulation in Vivado interface.
		  -h, --help                    Show this message and exit.

All the changes for the ipbb folder are in the file: ipbb/ipbb/cli/vivado.py(265:312)
