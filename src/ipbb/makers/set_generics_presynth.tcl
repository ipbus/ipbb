# Presynth script for setting generics containing build metadata

# Build time (seconds since epoch)
set UNIX_TIME [format %04X [clock seconds]]
puts UNIX_TIME=$UNIX_TIME
set GENERIC_VALUES "UNIX_TIME=32'h$UNIX_TIME"

# For each source area, 3 generics:
#  * <NAME>_GIT_SHA: 28 bits
#  * <NAME>_GIT_CLEAN: 1 bit
#  * <NAME>_GIT_REF: string (branch/tag name)
# 3 generics covering all source areas (values for each repo concantenated):
#  * GIT_REPOS_NAME: std_logic_vector, 160 bits per repo (UTF-8)
#  * GIT_REPOS_REF: std_logic_vector, 160 bits per repo (UTF-8)
#  * GIT_REPOS_SHA: std_logic_vector, 28 bits per repo
#  * GIT_REPOS_CLEAN: std_logic_vector, 1 bit per repo
#
# Commands used to extract git info:
#  1) git rev-parse --abbrev-ref HEAD   => branch name for branches; 'HEAD' for tagged or specific commits
#  2) git describe --exact-match        => tag name if current commit matches a tag (non-zero exit code otherwise)
#  3) git rev-parse --short HEAD        => 7-char SHA
#  4) git diff --quiet HEAD             => Non-zero exit code if local changes not included in commit

set SOURCES_ROOTDIR {{{source_root_dir}}}
puts "SOURCES_ROOTDIR=$SOURCES_ROOTDIR"
set SOURCES_SUBDIRS {{{source_areas}}}
puts "SOURCES_SUBDIRS=$SOURCES_SUBDIRS"

set ORIG_PWD [pwd]
set GIT_REPOS_NAME [format "%u'h" [expr 160 * [llength $SOURCES_SUBDIRS]]]
set GIT_REPOS_REF [format "%u'h" [expr 160 * [llength $SOURCES_SUBDIRS]]]
set GIT_REPOS_SHA [format "%u'h" [expr 28 * [llength $SOURCES_SUBDIRS]]]
set GIT_REPOS_CLEAN [format "%u'b" [llength $SOURCES_SUBDIRS]]

foreach SOURCE_AREA_NAME $SOURCES_SUBDIRS {
  puts "SOURCE AREA: $SOURCE_AREA_NAME"
  set VAR_PREFIX [string map {- _} [string toupper $SOURCE_AREA_NAME]]
  puts "  VAR_PREFIX=$VAR_PREFIX"

  binary scan [encoding convertto utf-8 "$SOURCE_AREA_NAME"] H* SOURCE_AREA_NAME_UTF
  puts "  UTF-8-encoded name: $SOURCE_AREA_NAME_UTF"
  append GIT_REPOS_NAME [format %-040s [string range $SOURCE_AREA_NAME_UTF 0 39]]

  cd $SOURCES_ROOTDIR/$SOURCE_AREA_NAME
  puts "  pwd=[pwd]"

  set GIT_REF [exec git rev-parse --abbrev-ref HEAD]
  if {$GIT_REF == {HEAD}} {
    if { [catch {exec git describe --exact-match} GIT_REF] } {
      puts "  Checked-out commit does not appear to match branch or tag"
      set GIT_REF ""
    }
  }
  puts "  GIT_REF=$GIT_REF"
  binary scan [encoding convertto utf-8 "$GIT_REF"] H* GIT_REF_UTF
  puts "  UTF-8-encoded ref: $GIT_REF_UTF"
  append GIT_REPOS_REF [format %-040s [string range $GIT_REF_UTF 0 39]]

  set GIT_SHA [exec git rev-parse --short HEAD]
  puts "  GIT_SHA=$GIT_SHA"
  set [set VAR_PREFIX]_GIT_SHA "28'h$GIT_SHA"
  append GIT_REPOS_SHA $GIT_SHA

  set GIT_CLEAN [string match 0 [catch { exec git diff --quiet HEAD }]]
  puts "  GIT_CLEAN=$GIT_CLEAN"
  append GIT_REPOS_CLEAN $GIT_CLEAN
  set [set VAR_PREFIX]_GIT_CLEAN $GIT_CLEAN

  append GENERIC_VALUES " [set VAR_PREFIX]_GIT_SHA=28'h$GIT_SHA [set VAR_PREFIX]_GIT_CLEAN=1'b$GIT_CLEAN [set VAR_PREFIX]_GIT_REF={\"$GIT_REF\"}"
}

append GENERIC_VALUES " GIT_REPOS_NAME=$GIT_REPOS_NAME GIT_REPOS_REF=$GIT_REPOS_REF GIT_REPOS_SHA=$GIT_REPOS_SHA GIT_REPOS_CLEAN=$GIT_REPOS_CLEAN"
puts ORIG_PWD=$ORIG_PWD
cd $ORIG_PWD


# GitLab CI variables
#  - GITLAB_CI_PROJECT_ID:  Project ID number (value of $CI_PROJECT_ID)
#  - GITLAB_CI_PIPELINE_ID: CI pipeline ID number (value of $CI_PIPELINE_ID)
#  - GITLAB_CI_JOB_ID:      CI job ID number (value of $CI_JOB_ID)

set GITLAB_CI_PROJECT_ID 0
set GITLAB_CI_PIPELINE_ID 0
set GITLAB_CI_JOB_ID 0

if { [info exists ::env(GITLAB_CI) ] } {
  set GITLAB_CI_PROJECT_ID $::env(CI_PROJECT_ID)
  set GITLAB_CI_PIPELINE_ID $::env(CI_PIPELINE_ID)
  set GITLAB_CI_JOB_ID $::env(CI_JOB_ID)

  puts "GITLAB_CI_PROJECT_ID : $GITLAB_CI_PROJECT_ID"
  puts "GITLAB_CI_PIPELINE_ID: $GITLAB_CI_PIPELINE_ID"
  puts "GITLAB_CI_JOB_ID     : $GITLAB_CI_JOB_ID"
}

append GENERIC_VALUES " GITLAB_CI_PROJECT_ID=$GITLAB_CI_PROJECT_ID"
append GENERIC_VALUES " GITLAB_CI_PIPELINE_ID=$GITLAB_CI_PIPELINE_ID"
append GENERIC_VALUES " GITLAB_CI_JOB_ID=$GITLAB_CI_JOB_ID"


puts "Generics: $GENERIC_VALUES"
puts "Current fileset: [current_fileset]"
set_property generic "$GENERIC_VALUES" [current_fileset]
