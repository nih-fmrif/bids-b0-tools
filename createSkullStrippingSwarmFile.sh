
#!/bin/sh

subjectDataDir='/data/BIDSFormatData.organized.on.2019.08.20'
    brainPrior='/data/infant-2yr-pmaps.nii.gz'
 brainTemplate='/data/infant-2yr-withSkull.nii.gz'

cd $subjectDataDir

curDateAndTime=`date +%Y%m%d_%H%M%S`
   swarmScript="$subjectDataDir/skullStrippingSwarmScript.$curDateAndTime"

touch $swarmScript

    # ssModule="ANTs/2.3.1"
    # ssModule="fsl"
      ssModule="afni"

      anatDirs=`find $subjectDataDir -name anat -type d`

for dir in $anatDirs 
do
   cd $dir
   anats=`ls *T1*nii*`
   for eachAnat in $anats
   do
      rootName=`echo $eachAnat | cut -f -1 -d .`
      skullStrippedName=`echo $rootName`\_skull_stripped_afni
      # echo "cd $dir ; module load $ssModule ; antsBrainExtraction.sh -d 3   -a $eachAnat   -e $brainTemplate   -m $brainPrior -o $skullStrippedName" >> $swarmScript
      # echo "cd $dir ; module load $ssModule ; bet2 $rootName $skullStrippedName" >> $swarmScript
      echo "cd $dir ; module load $ssModule ; 3dSkullStrip -use_skull -surface_coil -input $eachAnat -prefix $skullStrippedName\.nii" >> $swarmScript
   done
done

echo ""
echo "   Now run FreeSurfer swarm with command:"
echo ""
echo "      swarm --usecsh -g 4 -f $swarmScript"
echo ""

