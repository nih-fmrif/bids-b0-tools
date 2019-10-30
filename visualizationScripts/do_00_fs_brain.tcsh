#!/bin/tcsh

# Run FS's recon-all on a single subject, and the convert to AFNI with
# @SUMA_Make_Spec_FS.
#
# This script swarmed with run_00*.tcsh.
#
# FS outdir will be   : ${odir_top}/${sid}/
# SUMA outdir will be : ${odir_top}/${sid}/SUMA/
#
# ======================================================================

set Nargs    = 3

set sid      = $1      
set ianat    = $2
set odir_top = $3

if ( $#argv != ${Nargs} ) then
    echo "** Need ${Nargs} args; you gave ${#argv}"
    exit 1
endif

# -------------------------------------------------

source /etc/profile.d/modules.csh

module load afni freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.csh

# Make output dir
\mkdir -p ${odir_top}

# Run FS
recon-all                                     \
    -all                                      \
    -sd       ${odir_top}                     \
    -subjid   ${sid}                          \
    -i        ${ianat}

# Convert to AFNI/SUMA
@SUMA_Make_Spec_FS                            \
    -NIFTI                                    \
    -fspath ${odir_top}/${sid}                \
    -sid    ${sid}
