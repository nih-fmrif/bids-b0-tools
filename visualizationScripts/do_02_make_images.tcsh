#!/bin/tcsh

# The script used to create Figure 2 in Roopchansingh et al.'s:
#     "EPI Distortion Correction is Easy and Useful, and You Should
#      Use It: A case study with toddler data"
#
# Note: column labels and arrows were added later (via Libreoffice Impress)
#
#
# auth: PA Taylor (SSCC, NIMH, NIH, USA)
# date: 2019-10-29
#
############################################################################

set here = $PWD

# Some environment variables.  NB: my ~/.afnirc settings might be
# different than yours, Dear Reader, so note that that might result in
# image differences.
setenv AFNI_DEFAULT_IMSAVE      png
setenv AFNI_ENVIRON_WARNINGS    NO

# Define a list of subj to proc: these are ones that have all data
# (T1w, FMRI, B_0 correction phase map, and reverse-blip EPI)
set all_subj = ( sub-22_ses-02 \
                 sub-22_ses-03 \
                 sub-24_ses-01 \
                 sub-26_ses-01 \
                 sub-27_ses-01 \
                 sub-32_ses-01 \
                 sub-39_ses-02 )
                 

# Some inputs and variable names used when processing each subj
set ianat          = brain.nii
set ianat_res      = brain_res.nii
set ianat_edge     = CONTRAST_UP_edge.nii
set ianat_edge_sh  = CONTRAST_UP_edge_SH.nii
set oprefA         = imgD_T1_edges


# ------------------------ proc each subj ---------------------

# The directories that get looped over are the output of running FS's
# "recon-all" and AFNI's "@SUMA_Make_Spec_FS" on the T1w anatomical.
# Additionally, AFNI's "3dUnifize -EPI" was run on the uncorrected and
# corrected EPI volumes, to help deal with visualizing tissue
# contrasts in the presence of inhomogeneity.  Thus, those epi*UNI.nii
# volumes are in the same SUMA/ directories as the
# "@SUMA_Make_Spec_FS" outputs from the start here.

foreach subj ( ${all_subj} )

    echo "\n\n++ Proc subj: ${subj}\n\n"

    # Define slices to view for each subject.  We only really care
    # about the z-component here, since we only used axial slices.  A
    # possibly smarter way to automate this could have been using 3dCM
    # to get the center of mass of each dset and then add/subtract
    # some distance from there...  But mainly, we wanted axial slices
    # from similar parts of the brain, and had to deal with the fact
    # that each toddler's brain was in a different native space
    # location (and often at a somewhat quirky angle).

    if ( ( ${subj} == sub-22_ses-02 ) || \
         ( ${subj} == sub-22_ses-03 ) || \
         ( ${subj} == sub-24_ses-01 ) ) then
         set coords = ( 0 0 15 )
    else if ( ( ${subj} == sub-32_ses-01 ) ) then
         set coords = ( 0 0 8 )
    else if ( ( ${subj} == sub-26_ses-01 ) ) then
         set coords = ( 0 0 -18 )
    else if( ( ${subj} == sub-27_ses-01 ) ) then
         set coords = ( 0 0 21 )
    else if( ( ${subj} == sub-39_ses-02 ) ) then
         set coords = ( 0 0 18 )
    endif

    set suma_dir  = ${subj}/SUMA
    cd ${suma_dir}

    # Upsample the uncorrected EPI dset, and at the same time get rid
    # of empty regions around the brain in the axial planes (with
    # negative zero-padding, i.e., removing slices).  The output of
    # the subsequent "if" condition will define the output grid for
    # all images, then (hences its name ${dset_up_zp_mast}).

    set rest_base = `\ls epiRest*UNI.nii`
    set gg        = `basename ${rest_base} .nii`
    set dset_up   = ${gg}_US0.nii
    set dset_up_zp_mast = ${gg}_US.nii

    # Since there is lots of empty space around each brain, get rid of
    # some of that whilst upsampling so brains occupy most of the
    # figure space.
    if ( ! -e ${dset_up_zp_mast} ) then

        # upsample
        3dresample                            \
            -prefix ${dset_up}                \
            -dxyz 0.5 0.5 0.5                 \
            -rmode NN                         \
            -input ${rest_base}

        # tighten the FOV in the axial plane
        3dZeropad                             \
            -prefix ${dset_up_zp_mast}        \
            -R -40                            \
            -L -40                            \
            -A -25                            \
            -P -25                            \
            ${dset_up}
    endif


    # Make the edges, if they haven't been already
    if ( ! -e ${ianat_edge_sh} ) then

        # Make a volume where each tissue class has a distinct value:
        # will be useful to define tissue contrast boundaries.
        3dcalc -echo_edu                         \
            -overwrite                           \
            -a aparc+aseg_REN_gm.nii.gz          \
            -b aparc+aseg_REN_csf.nii.gz         \
            -c aparc.a2009s+aseg_REN_vent.nii.gz \
            -d aparc.a2009s+aseg_REN_wmat.nii.gz \
            -expr '100*d +200*a + 300*(b+c)'     \
            -prefix CONTRAST.nii

        # Upsample AND match other FOV
        3dAllineate                              \
            -overwrite                           \
            -1Dmatrix_apply IDENTITY             \
            -final NN                            \
            -master ${dset_up_zp_mast}           \
            -source  CONTRAST.nii                \
            -prefix  CONTRAST_UP.nii             \
            -overwrite       

        # get edges of the volume
        3dedge3                                  \
            -overwrite                           \
            -prefix ${ianat_edge}                \
            -input CONTRAST_UP.nii

        # make the edges slightly more prominent: thicken lines
        # because the individual figure panels will be tiny;
        # otherwise, could ignore this step.
        3dcalc                                   \
            -overwrite                           \
            -a ${ianat_edge}                     \
            -b 'a[0,1,0,0]'                      \
            -expr 'step(a+b)'                    \
            -prefix ${ianat_edge_sh}
    endif

    # Upsample T1w dset AND match other FOV
    3dAllineate                                  \
        -overwrite                               \
        -1Dmatrix_apply IDENTITY                 \
        -final NN                                \
        -master  ${dset_up_zp_mast}              \
        -source  ${ianat}                        \
        -prefix  ${ianat_res}                    \
        -overwrite

    # Smile for the camera (ulay: T1w anat; olay: tissue edges)
    @chauffeur_afni                              \
        -ulay  ${ianat_res}                      \
        -olay  ${ianat_edge_sh}                  \
        -set_dicom_xyz ${coords}                 \
        -globalrange SLICE                       \
        -cbar     "red_monochrome"               \
        -func_range 1                            \
        -opacity  9                              \
        -prefix   ${oprefA}                      \
        -blowup 4                                \
        -montx 1 -monty 1                        \
        -set_xhairs OFF                          \
        -label_mode 0 -label_size 3              \
        -do_clean

    # Now loop through all the corrected EPIs: upsample and take
    # images
    set all_epi = `\ls epi*UNI.nii`
    foreach ff ( ${all_epi} )
        
        set gg      = `basename ${ff} .nii`
        set dset_up = ${gg}_US.nii
        set opref   = imgD_${gg}_edges

        # Upsample and match FOV of original EPI
        if ( ! -e ${dset_up} ) then
            3dAllineate                         \
                -overwrite                      \
                -1Dmatrix_apply IDENTITY        \
                -final NN                       \
                -master ${dset_up_zp_mast}      \
                -source  ${ff}                  \
                -prefix  ${dset_up}             \
                -overwrite       
        endif

        # Smile for the camera (ulay: unifized EPI; olay: tissue edges)
        @chauffeur_afni                         \
            -ulay            ${dset_up}         \
            -olay            ${ianat_edge_sh}   \
            -ulay_range      200 800            \
            -func_range      1                  \
            -set_dicom_xyz   ${coords}          \
            -cbar            "red_monochrome"   \
            -blowup          4                  \
            -opacity         9                  \
            -prefix          ${opref}           \
            -montx 1 -monty 1                   \
            -set_xhairs OFF                     \
            -label_mode 0 -label_size 3         \
            -do_clean
    end
    
    # ------------------ concatenate images for each subj -------------

    # For each subject, combine the individual images from above into
    # a single row, which will be then merged below for the group figure.
    imcat                                        \
        -overwrite                               \
        -gap     0                               \
        -ny 1                                    \
        -prefix ALLD_${subj}.jpg                 \
        imgD_T1*axi.*                            \
        imgD_epiRest0*axi*png                    \
        imgD_epi*_ab-*axi*png                    \
        imgD_epi*_fb-*axi*png                    \
        imgD_epi*_ae-*axi*png                    \
        imgD_epi*_fe-*axi*png

    # An alternative universe to the above: make a 2x3 montage of each
    # subject's individual images, for a different style of figure
    # (not used here, in the end)
    imcat                                        \
        -overwrite                               \
        -gap     0                               \
        -ny 2 -nx 3                              \
        -prefix ALLD2_${subj}.jpg                \
        imgD_T1*axi.*                            \
        imgD_epi*_fb-*axi*png                    \
        imgD_epi*_fe-*axi*png                    \
        imgD_epiRest0*axi*png                    \
        imgD_epi*_ab-*axi*png                    \
        imgD_epi*_ae-*axi*png                    \

    cd $here
end

# Make final group image: basically glue all the previously made rows
# of images together
imcat                                             \
    -overwrite                                    \
    -gap     5                                    \
    -gap_col 250 250 250                          \
    -nx 1                                         \
    -prefix FINAL_COMBO_grid.jpg                  \
    sub-*/SUMA/ALLD_*.jpg
        

echo ""
echo "++ Your final image awaits:  FINAL_COMBO_grid.jpg"
echo ""
