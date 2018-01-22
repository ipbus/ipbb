# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Added `--filter` option to `ipbb dep report`
- Simplified `ipbb vivado project`: IP syntesis runs are not launched automatically anymore.
- Added `--jobs` option to `ipbb vivado` `synth` and `impl` commands.
- Added vivavo variant autodetection to `ipb-prog vivado`.
- Improved `add git` branch/tag resolution.

## [0.2.9] - 2018-01-08
- Added check on branch/tag validity when adding git repositories.
- Improved ipbus-decoder code diff.
- Added suppoer for conda-based environment.
- Added the `cleanup` subcommand to `sim` and `vivado` command groups.
- Added the `srcstat` command to provide a compact status report of git and svn packages.

## [0.2.8] - 2017-10-05
### Changed
- Improved command-line help.
- Bugfix in `ipbb create vivado`
 
## [0.2.7] - 2017-09-01
### Added
- New script `ipb-prog`, for programming Xilinx board via jtag and `vivado_lab`.
- Virtualenv setup now based on `setuptools`.

### Changed
- Improved error messages.
- Consolidated `ipbb dep report` sections, now organised in text tables.

## [0.2.6] - 2017-07-17

### Changed
- Improved handling of Vivado library paths in Modelsim.
- Command line help improved. 

## [0.2.5] - 2017-04-23
