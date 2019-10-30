The scripts here are used to:

+ (do_00*.tcsh, run*.tcsh) Run FS's recon-all to generate
  parcellation/segmentations of the T1w anatomical volume.  For this
  step, execute the run_00*.tcsh script, which will generate the swarm
  file (job submission file for computer cluster) and submit it.

+ (do_01*.tcsh) Copy the [0]th vol of the EPIs into each subject's
  SUMA/ directory, and unifize each (for visualization purposes,
  only).  Run the do_01*.tcsh script for this step.

+ (do_02*.tcsh) Make images of the tissue class boundaries overlaid on
  the EPIs and anatomical volumes.  This makes most of Fig. 2.  Run
  the do_02*.tcsh script for this step.

