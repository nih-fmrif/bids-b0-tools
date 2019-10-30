#!/bin/tcsh

# Copy+unifize EPI dsets into FS output directory, in order to make
# images and figures out of them.  (Actually, we just use the [0]th
# vol of each.
#
# auth: PA Taylor (SSCC, NIMH, NIH, USA)
# date: 2019-10-29
#
############################################################################

set here = $PWD

# subj to proc:  they have all dsets (though some might still not be used)
set all_subj = ( sub-22_ses-02 \
                 sub-22_ses-03 \
                 sub-24_ses-01 \
                 sub-26_ses-01 \
                 sub-27_ses-01 \
                 sub-32_ses-01 \
                 sub-39_ses-02 )


# -------------------------- proc each subject -------------------------

foreach subj ( ${all_subj} )

    echo "\n\n++ Proc subj: ${subj}\n\n"

    # Where the FS+@SUMA_Make_Spec_FS output is
    set suma_dir  = ae_proc_fs/${subj}/SUMA

    # ----- Copy [0]th vol of orig dset, and then unifize it

    set dset_orig = epiRest/ae/${subj}.results/epiRest-${subj}.nii
    set opref     = ${suma_dir}/epiRest0-${subj}

    3dcalc -echo_edu \
        -a ${dset_orig}"[0]" \
        -expr 'a' \
        -prefix ${opref}.nii

    3dUnifize -echo_edu                                        \
        -EPI                                                   \
        -prefix ${opref}_UNI.nii                               \
        ${opref}.nii

    # ----- Copy [0]th vol of fixed dsets, and then unifize it

    foreach mm ( ae ab fe fb )

        set dset_fixed = epiFixed/${mm}/${subj}.results/epiFixed-${subj}.nii
        set opref      = ${suma_dir}/epiFixed0_${mm}-${subj}

        # copy [0]th vol of fixed dset
        3dcalc -echo_edu                                           \
            -a ${dset_fixed}"[0]"                                  \
            -expr 'a'                                              \
            -prefix ${opref}.nii

        3dUnifize -echo_edu                                        \
            -EPI                                                   \
            -prefix ${opref}_UNI.nii                               \
            ${opref}.nii
    end

    cd ${here}
end

echo "\n\n++ Done copying and unifizing dsets.\n\n"
