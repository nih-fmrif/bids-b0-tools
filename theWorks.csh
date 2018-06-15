#!/bin/tcsh

set    projectTop = "/data/$USER"

setenv PATH /usr/local/slurm/bin:{$PATH}
setenv PYTHONPATH $projectTop/BIDS-tools

if( $#argv < 2 ) then
  echo " "
  echo "Master script for executing all of the distortion"
  echo "correction functions located in distortionFix.py"
  echo "using the HPC @ NIH Biowulf cluster."
  echo " "
  echo "Usage: theWorks.csh suffix [options]"
  echo " "
  echo "Where 'suffix' is appended to the directory name"
  echo "that is created by theWorks.csh (ie. distFix_suffix)"
  echo " "
  echo "Options: Takes the same command line options as noted"
  echo "         in the '--help' output from distortionFix.py"
  echo "         NOTE: Do not include the dash (-) with these"
  echo "         options. Use spaces between each option." 
  echo " "
  echo "Example usage: "
  echo "   tcsh theWorks.csh 20170518 ae ab fe fb n"
  echo " "
  echo "This example will run afniBlipUpDown, afniB0, "
  echo "fslBlipUpDown, fslB0, and noCorr using one node each."
  echo " "
  echo "Important:"
  echo "Both the 'BIDS-tools' directory (see above) and the"
  echo "'bidsFormatData' directory should be located in the"
  echo "same directory that theWorks.csh is executed from."
  echo " "
  exit 0
endif

# set BIDS-tools and bidsFormatData directory locations

set dfpy          = "$projectTop/BIDS-tools/distortionFix.py"
# for testing with a smaller number of subjects
# set datadir       = "$projectTop/exampleSubjects/"
# full data set
set datadir       = "$projectTop/bidsFormatData/"

# create working directory using 'suffix' from command line

set worksdir = distFix_$argv[1]

if ( -e $worksdir ) then
   echo "*** Directory $worksdir already exists..."
   echo "*** try something different for 'suffix'."
else
   mkdir $worksdir
endif

# fix many distortions, in (perhaps) many ways

cd $worksdir

foreach corr ( $argv[2-] )

   mkdir $corr
   cd $corr/

   # create a batch tcsh script for each correction

   echo "module load python/2.7.9"         >! sbatch_$corr.csh
   echo "module load virtualenv"          >>! sbatch_$corr.csh
   echo "module load ANTs"                >>! sbatch_$corr.csh
   echo "module load fsl"                 >>! sbatch_$corr.csh
   echo "module load afni/current-openmp" >>! sbatch_$corr.csh

   echo "source $projectTop/venvWithPyFS/bin/activate.csh" >>! sbatch_$corr.csh
   # echo "sbatch --time=10-00:00:00 \" >>! sbatch_$corr.csh
   echo "sbatch --time=36:00:00 \" >>! sbatch_$corr.csh
   echo "       --mem=8g \" >>! sbatch_$corr.csh
   echo "       --partition nimh,norm \" >>! sbatch_$corr.csh
   echo "       --cpus-per-task=16 \" >>! sbatch_$corr.csh
   echo "       $dfpy -d $datadir -$corr" >>! sbatch_$corr.csh

   # begin correction by executing the batch tcsh script

   tcsh sbatch_$corr.csh

   cd ../

end

