#!/bin/tcsh

# set up swarm for do_00*tcsh

set snum      = 00
set scr       = scripts_${snum}
set cmd       = `\ls do_${snum}*.tcsh`

set here      = $PWD
set topdir    = ${here}/ae
set odir_top  = ${here}/ae_proc_fs

set odir_scr  = ${here}/${scr}            # all the individual scripts
set odir_log  = ${here}/log_${scr}        # dir of log scripts
set oswarmer  = ${here}/swarm_${scr}.txt  # master script to swarm all

# ========================================================================

if ( -d ${odir_scr} ) then
    \rm -rf ${odir_scr}
endif

if ( -d ${odir_log} ) then
    \rm -rf ${odir_log}
endif

\mkdir -p ${odir_scr}
\mkdir -p ${odir_log}

# clear out & start swarm script
printf "" > ${oswarmer} 

# --------------------------- do work ---------------------------

# get all subj dirs
cd ${topdir}
set all_sdir = `\ls -d */ | sed 's/\/$//'`
cd -

foreach ddd  ( ${all_sdir} )
    
    set sid      = ${ddd:gas/.results//}
    set ianat    = `\ls ${topdir}/${ddd}/anat*nii`
    
    echo "tcsh ${cmd} ${sid} ${ianat} ${odir_top}" >> ${oswarmer}


end

echo "\n++ Start swarming: ${oswarmer}\n"

swarm -f ${oswarmer}                          \
    -g 10 -t 2                                \
    --partition=norm                          \
    --time=20:59:59                           \
    --merge-output                            \
    --logdir=log_${scr}                       \
    --module=afni

echo "\n++ Check status with: \n\nsjobs -u $USER \n\n"
