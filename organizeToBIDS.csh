
# # Labels for PDN data
# set anatMatchString0 = "RAGE"
# set funcMatchString0 = "EPI"
# set funcMatchString1 = "8min"
# set fmapMatchString0 = "B0"
# set  dtiMatchString0 = "DTI"

# Labels for X-scanner data
set anatMatchString0 = "RAGE"
set anatMatchString1 = "T2"
set funcMatchString0 = "3mm_iso"
set funcMatchString1 = "cal"
set fmapMatchString0 = "B0"
set fmapMatchString1 = ""
set  dtiMatchString0 = "DTI"

### For final run ###
set patientFolders = `find . -maxdepth 1 -mindepth 1 -type d`

# echo List of patient folders is: $patientFolders

foreach patientDir ($patientFolders)
   # echo Entering patient folder $patientDir
   cd $patientDir

   # Get list of all files to be unpacked.
   set scanArchiveList = `ls *.tgz`

   if ("$scanArchiveList" == "") then
      echo No archive files found in $patientDir.  Moving to next folder.
   else
      # Make subject top-level BIDS folder
      set subjectID = sub-`echo $patientDir | cut -d "/" -f2`
      mkdir $subjectID
      cd $subjectID
      set subjectBIDSTopDir = `pwd`
      cd ..
   endif

   # echo Unpacking archive $scanArchiveList
   foreach patientSessionArchive ($scanArchiveList)
      # echo Unpacking session $patientSessionArchive
      echo "Archive found. Unpacking ..."
      tar xfz $patientSessionArchive
   end

   echo "Done unpacking archives. Now organizing into BIDS folders."

   set sessionFolders = `find . -maxdepth 2 -mindepth 2 -type d`

   foreach session ($sessionFolders)
      pushd .
      cd $session

      ### Locate Scans of Interest ###
      set scanFolders = `find . -maxdepth 4 -mindepth 1 -type d -name "mr*"`
      
      ### Counters for each type of data being organized to BIDS ###
      set countAnatDatasets = 1
      set countRestDatasets = 1
      set countB0MagDatasets = 1
      set countB0FreqDatasets = 1
      set countOppEpiDatasets = 1
      set countDTIDatasets = 1

      foreach folder ( $scanFolders )
         set referenceFile = `ls -1 $folder/*.dcm | head -1`
         set seriesDescription = `dicom_hdr $referenceFile | grep -i "series description"`

         ### Locate MP-RAGE data ###
         echo $seriesDescription | grep -iq $anatMatchString0
         if ($?) then
            : # echo Folder $folder does not contain MP-RAGE data.
         else
            set printAnat=`printf "%02d" $countAnatDatasets`
            if (! -d $subjectBIDSTopDir/anat) then
               # echo CREATING DIRECTORY $subjectBIDSTopDir/anat
               mkdir -p $subjectBIDSTopDir/anat
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $subjectBIDSTopDir/anat
            endif
            set datasetPrefix = $subjectID\_run-$printAnat\_T1w
            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $subjectBIDSTopDir/anat
            set countAnatDatasets = `expr $countAnatDatasets + 1`
            continue
         endif

         ### Locate T2 data ###
         echo $seriesDescription | grep -iq $anatMatchString1
         if ($?) then
            : # echo Folder $folder does not contain MP-RAGE data.
         else
            set printAnat=`printf "%02d" $countAnatDatasets`
            if (! -d $subjectBIDSTopDir/anat) then
               # echo CREATING DIRECTORY $subjectBIDSTopDir/anat
               mkdir -p $subjectBIDSTopDir/anat
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $subjectBIDSTopDir/anat
            endif
            set datasetPrefix = $subjectID\_run-$printAnat\_T2w
            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $subjectBIDSTopDir/anat
            set countAnatDatasets = `expr $countAnatDatasets + 1`
            continue
         endif

         ### Locate DTI data ###
         echo $seriesDescription | grep -iq $dtiMatchString0
         if ($?) then
            : # echo Folder $folder does not contain MP-RAGE data.
         else
            set printAnat=`printf "%02d" $countDTIDatasets`
            if (! -d $subjectBIDSTopDir/dwi) then
               # echo CREATING DIRECTORY $subjectBIDSTopDir/anat
               mkdir -p $subjectBIDSTopDir/dwi
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $subjectBIDSTopDir/anat
            endif
            set datasetPrefix = $subjectID\_run-$printAnat\_dwi
            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $subjectBIDSTopDir/dwi
            set countDTIDatasets = `expr $countDTIDatasets + 1`
            continue
         endif

         ### Locate EPI data ###
         echo $seriesDescription | grep -iq $funcMatchString0
         if ($?) then
            : # echo Folder $folder does not contain EPI data.
         else
            echo $seriesDescription | grep -iq $funcMatchString1
            if ($?) then
               if (! -d $subjectBIDSTopDir/func) then
                  # echo CREATING DIRECTORY $subjectBIDSTopDir/func
                  mkdir -p $subjectBIDSTopDir/func
               # else
                  # echo DIRECTORY ALREADY EXISTS FOR $subjectBIDSTopDir/func
               endif
               set printRest=`printf "%02d" $countRestDatasets`
               set datasetPrefix = $subjectID\_dir-y_run-$printRest\_epi
               Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                     -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
               mv $datasetPrefix* $subjectBIDSTopDir/func
               set countRestDatasets = `expr $countRestDatasets + 1`
            else
               if (! -d $subjectBIDSTopDir/fmap) then
                  # echo CREATING DIRECTORY $subjectBIDSTopDir/fmap
                  mkdir -p $subjectBIDSTopDir/fmap
               # else
                  # echo DIRECTORY ALREADY EXISTS FOR $subjectBIDSTopDir/fmap
               endif
               set printOppEpi=`printf "%02d" $countOppEpiDatasets`
               set datasetPrefix = $subjectID\_dir-y-_run-$printOppEpi\_epi
               Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                     -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
               mv $datasetPrefix* $subjectBIDSTopDir/fmap
               set countOppEpiDatasets = `expr $countOppEpiDatasets + 1`
            endif
            continue
         endif

         ### Locate B0 data ###
         echo $seriesDescription | grep -iq $fmapMatchString0
         if ($?) then
            : # echo Folder $folder does not contain B0 data.
         else
            if (! -d $subjectBIDSTopDir/fmap) then
               # echo CREATING DIRECTORY $subjectBIDSTopDir/fmap
               mkdir -p $subjectBIDSTopDir/fmap
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $subjectBIDSTopDir/fmap
            endif
            set seriesNumber = `dicom_hdr $referenceFile | grep -i "Series Number" | cut -d"/" -f5`

            if ($seriesNumber =~ *0) then
               set printB0=`printf "%02d" $countB0MagDatasets`
               set datasetPrefix = $subjectID\_run-$printB0\_magnitude
               set countB0MagDatasets = `expr $countB0MagDatasets + 1`
            else
               set printB0=`printf "%02d" $countB0FreqDatasets`
               set datasetPrefix = $subjectID\_run-$printB0\_frequency
               set countB0FreqDatasets = `expr $countB0FreqDatasets + 1`
            endif

            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $subjectBIDSTopDir/fmap

         endif

      # echo END OF LOOP within $folder
      end

      ### Return to directory location stored in "pushd" above ###
      popd
      # echo Script location 4, at `pwd`

   end
   # echo Leaving patient folder $patientDir
   cd ..

end

