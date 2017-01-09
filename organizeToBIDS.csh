
# Notice, PDN zipped data folders naming convention is
# [LastName]_[FirstName]_[MiddleName]-[MRN]-[ScanDate(YYYYMMDD)]-[ScanID]-DICOM[.Extension]
# Example... QUILL_PETER_JASON-31415926-20170125-61023-DICOM.tgz

# Labels for PDN data
set anatMatchString0 = "RAGE"
set anatMatchString1 = "_1_2mm" # T2 scans with 0.75x0.75x2.00mm voxels
set anatMatchString2 = "PD"
set funcMatchString0 = "EPI"
set funcMatchString1 = "8min"
set fmapMatchString0 = "B0"
set fmapMatchString1 = ""
# set  dtiMatchString0 = "DTI"
set otherMatchString0 = "tr64_6fa14" # mcdespotspgr scan
set otherMatchString1 = "asset" # asset calibration scan

# Store top level directory location
set topDir = `pwd`

# Create text file for tracking file name conversion information
echo `date` >>! $topDir/fileTrackerBIDS.txt
echo  SUBJECT_ID SCAN_DATE SESSION_ID BIDS_SUB/SES_DIRECTORY >>! $topDir/fileTrackerBIDS.txt

# Rename all files with .gz extension to .tgz extension
set renameZips = `find . -mindepth 1 -maxdepth 1 -type f -name "*.gz"`
foreach renameZip ( $renameZips )
   set fileName = `echo $renameZip | cut -d "." -f2 | cut -d "/" -f2`
   mv $fileName".gz" $fileName".tgz"
end

# Locate all zip files
set subjectZips = `find . -mindepth 1 -maxdepth 1 -type f -name "*.tgz"`

# Build list of zip files by appending subFolderList with subject IDs
set subFolderList = ""
foreach subjectZip ( $subjectZips )
   set subjectFolder = `echo $subjectZip | cut -d "-" -f2`
   set subFolderList = ( $subFolderList $subjectFolder )
end

# Find and exclude duplicate subject IDs from subFolderList
set sortedSubList = `echo $subFolderList | tr " " "\n" | sort -du | tr "\n" " "`

# Create folder for each subject and add the respective session files
set subCount = 1
foreach sortedSub ( $sortedSubList )
   set subNumber = `printf "%02d" $subCount`
   mkdir sub-$subNumber
   mv *"-"$sortedSub"-"*".tgz" sub-$subNumber
   set subCount = `expr $subCount + 1`
end

# Find all newly created BIDS-compliant subject-level folders
set subBIDSFolders = `find . -maxdepth 1 -mindepth 1 -type d`

# Find and unpack all zipped session files
foreach subjDir ( $subBIDSFolders )
   # echo Entering subject $subjDir folder
   cd $subjDir

   # Get list of session files to be unpacked,
   # and in order of first to last session
   set sessionArchiveList = `ls *.tgz | fmt -1 | sort -d`
   set sessionFolderList = ""
   set sessionCount = 1

   # Make session-level BIDS folders for each session file and build a
   # list of sessions to organize to BIDS-compliant scan type folders
   foreach sessionArchive ( $sessionArchiveList )
      set sessionNumber = `printf "%02d" $sessionCount`
      mkdir ses-$sessionNumber
      mv $sessionArchive ses-$sessionNumber
      set sessionFolderList = ( $sessionFolderList ses-$sessionNumber )
      set sessionCount = `expr $sessionCount + 1`
      
      # Gather subject and session information from archive file name
      # then enter into fileTrackerBIDS.txt
      set subjectField = `echo $sessionArchive | cut -d "-" -f2`
      set dateField = `echo $sessionArchive | cut -d "-" -f3`
      set sessionField = `echo $sessionArchive | cut -d "-" -f4`
      echo $subjectField $dateField $sessionField $subjDir/ses-$sessionNumber >>! $topDir/fileTrackerBIDS.txt
   end

   # Unpack session files
   foreach sesDir ( $sessionFolderList )
      cd $sesDir
      tar xfz *.tgz
      cd ..
   end

   # Get list of newly unpacked session folders
   set sesFolders = `find . -maxdepth 1 -mindepth 1 -type d`

   # The following will create the BIDS-formatted scan type directories.
   # It will also convert dicom files to AFNI files (non-BIDS) and move
   # those files to their respective BIDS directory
   foreach session ( $sesFolders )
      pushd .
      cd $session
      set sesBIDSTopDir = `pwd`
      
      # Set subject ID and session ID to use for naming BIDS-compliant scan files
      set subjectID = `echo $sesBIDSTopDir | rev | cut -d "/" -f2 | rev`
      set sessionID = `echo $sesBIDSTopDir | rev | cut -d "/" -f1 | rev`

      # Locate Scans of Interest
      set scanFolders = `find . -maxdepth 4 -mindepth 1 -type d -name "mr*"`
      
      # Set counters for each type of scan being organized to BIDS
      set countAnatMatch0 = 1
      set countAnatMatch1 = 1
      set countAnatMatch2 = 1
      set countFuncMatch0 = 1
      set countFuncMatch1 = 1
      set countFmapMatch0 = 1
      set countFmapMatch1 = 1
      # set countDTIMatch0 = 1
      set countOtherMatch0 = 1
      set countOtherMatch1 = 1

      foreach folder ( $scanFolders )
         set referenceFile = `ls -1 $folder/*.dcm | head -1`
         set seriesDescription = `dicom_hdr $referenceFile | grep -i "series description"`

         ### Locate MP-RAGE data ###
         echo $seriesDescription | grep -iq $anatMatchString0
         if ($?) then
            : # echo Folder $folder does not contain MP-RAGE data.
         else
            set printAnat0=`printf "%02d" $countAnatMatch0`
            if (! -d $sesBIDSTopDir/anat) then
               # echo CREATING DIRECTORY $sesBIDSTopDir/anat
               mkdir -p $sesBIDSTopDir/anat
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $sesBIDSTopDir/anat
            endif
            set datasetPrefix = $subjectID\_$sessionID\_run-$printAnat0\_T1w
            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $sesBIDSTopDir/anat
            set countAnatMatch0 = `expr $countAnatMatch0 + 1`
            continue
         endif

         ### Locate T2 data ###
         echo $seriesDescription | grep -iq $anatMatchString1
         if ($?) then
            : # echo Folder $folder does not contain T2 data.
         else
            set printAnat1=`printf "%02d" $countAnatMatch1`
            if (! -d $sesBIDSTopDir/anat) then
               # echo CREATING DIRECTORY $sesBIDSTopDir/anat
               mkdir -p $sesBIDSTopDir/anat
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $sesBIDSTopDir/anat
            endif
            set datasetPrefix = $subjectID\_$sessionID\_run-$printAnat1\_T2w
            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $sesBIDSTopDir/anat
            set countAnatMatch1 = `expr $countAnatMatch1 + 1`
            continue
         endif
	 
	 ### Locate Proton Density data ###
         echo $seriesDescription | grep -iq $anatMatchString2
         if ($?) then
            : # echo Folder $folder does not contain PD data.
         else
            set printAnat2=`printf "%02d" $countAnatMatch2`
            if (! -d $sesBIDSTopDir/anat) then
               # echo CREATING DIRECTORY $sesBIDSTopDir/anat
               mkdir -p $sesBIDSTopDir/anat
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $sesBIDSTopDir/anat
            endif
            set datasetPrefix = $subjectID\_$sessionID\_run-$printAnat2\_PD
            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $sesBIDSTopDir/anat
            set countAnatMatch2 = `expr $countAnatMatch2 + 1`
            continue
         endif

         ### Locate DTI data ###
         # echo $seriesDescription | grep -iq $dtiMatchString0
         # if ($?) then
         #    : # echo Folder $folder does not contain MP-RAGE data.
         # else
         #    set printDTI0=`printf "%02d" $countDTIMatch0`
         #    if (! -d $sesBIDSTopDir/dwi) then
         #       # echo CREATING DIRECTORY $sesBIDSTopDir/anat
         #       mkdir -p $sesBIDSTopDir/dwi
         #    # else
         #       # echo DIRECTORY ALREADY EXISTS FOR $sesBIDSTopDir/anat
         #    endif
         #    set datasetPrefix = $subjectID\_$sessionID\_run-$printDTI0\_dwi
         #    Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
         #          -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
         #    mv $datasetPrefix* $sesBIDSTopDir/dwi
         #    set countDTIMatch0 = `expr $countDTIMatch0 + 1`
         #    continue
         # endif

         ### Locate EPI data ###
         echo $seriesDescription | grep -iq $funcMatchString0
         if ($?) then
            : # echo Folder $folder does not contain EPI data.
         else
            echo $seriesDescription | grep -iq $funcMatchString1
            if ($?) then
               if (! -d $sesBIDSTopDir/func) then
                  # echo CREATING DIRECTORY $sesBIDSTopDir/func
                  mkdir -p $sesBIDSTopDir/func
               # else
                  # echo DIRECTORY ALREADY EXISTS FOR $sesBIDSTopDir/func
               endif
               set printFunc0=`printf "%02d" $countFuncMatch0`
               set datasetPrefix = $subjectID\_$sessionID\_dir-y_run-$printFunc0\_epi
               Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                     -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
               mv $datasetPrefix* $sesBIDSTopDir/func
               set countFuncMatch0 = `expr $countFuncMatch0 + 1`
            else
               if (! -d $sesBIDSTopDir/fmap) then
                  # echo CREATING DIRECTORY $sesBIDSTopDir/fmap
                  mkdir -p $sesBIDSTopDir/fmap
               # else
                  # echo DIRECTORY ALREADY EXISTS FOR $sesBIDSTopDir/fmap
               endif
               set printFunc1=`printf "%02d" $countFuncMatch1`
               set datasetPrefix = $subjectID\_$sessionID\_dir-y-_run-$printFunc1\_epi
               Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                     -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
               mv $datasetPrefix* $sesBIDSTopDir/fmap
               set countFuncMatch1 = `expr $countFuncMatch1 + 1`
            endif
            continue
         endif

         ### Locate B0 data ###
         echo $seriesDescription | grep -iq $fmapMatchString0
         if ($?) then
            : # echo Folder $folder does not contain B0 data.
         else
            if (! -d $sesBIDSTopDir/fmap) then
               # echo CREATING DIRECTORY $sesBIDSTopDir/fmap
               mkdir -p $sesBIDSTopDir/fmap
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $sesBIDSTopDir/fmap
            endif
            set seriesNumber = `dicom_hdr $referenceFile | grep -i "Series Number" | cut -d"/" -f5`

            if ($seriesNumber =~ *0) then
               set printFmap0=`printf "%02d" $countFmapMatch0`
               set datasetPrefix = $subjectID\_$sessionID\_run-$printFmap0\_magnitude
               set countFmapMatch0 = `expr $countFmapMatch0 + 1`
            else
               set printFmap1=`printf "%02d" $countFmapMatch1`
               set datasetPrefix = $subjectID\_$sessionID\_run-$printFmap1\_frequency
               set countFmapMatch1 = `expr $countFmapMatch1 + 1`
            endif

            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $sesBIDSTopDir/fmap

         endif
	 
	 ### Locate mcDESPOT data ###
         echo $seriesDescription | grep -iq $otherMatchString0
         if ($?) then
            : # echo Folder $folder does not contain mcDESPOT data.
         else
            set printOther0=`printf "%02d" $countOtherMatch0`
            if (! -d $sesBIDSTopDir/other) then
               # echo CREATING DIRECTORY $sesBIDSTopDir/other
               mkdir -p $sesBIDSTopDir/other
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $sesBIDSTopDir/other
            endif
            set datasetPrefix = $subjectID\_$sessionID\_run-$printOther0\_mcdespot-tr64-6fa14
            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $sesBIDSTopDir/other
            set countOtherMatch0 = `expr $countOtherMatch0 + 1`
            continue
         endif
	 
	 ### Locate ASSET Calibration data ###
         echo $seriesDescription | grep -iq $otherMatchString1
         if ($?) then
            : # echo Folder $folder does not contain ASSET data.
         else
            set printOther1=`printf "%02d" $countOtherMatch1`
            if (! -d $sesBIDSTopDir/other) then
               # echo CREATING DIRECTORY $sesBIDSTopDir/other
               mkdir -p $sesBIDSTopDir/other
            # else
               # echo DIRECTORY ALREADY EXISTS FOR $sesBIDSTopDir/other
            endif
            set datasetPrefix = $subjectID\_$sessionID\_run-$printOther1\_asset
            Dimon -infile_pattern $folder/'*.dcm' -gert_create_dataset \
                  -gert_quit_on_err -gert_to3d_prefix $datasetPrefix
            mv $datasetPrefix* $sesBIDSTopDir/other
            set countOtherMatch1 = `expr $countOtherMatch1 + 1`
            continue
         endif

      # echo END OF LOOP within $folder
      end

      # Return to subject-level directory location stored in "pushd" above
      popd

   # echo END OF LOOP within $session
   end

   # Return to 
   cd ..

# echo END OF LOOP within $subjDir
end

# Remove original .tgz files and all unpacked non-BIDS directories and files
mkdir rmThisDirWhenDone
set zipList = `find . -mindepth 1 -maxdepth 3 -type f -name "*.tgz"`

foreach zipItem ( $zipList )
   # Since data are extracted session-wise, session-level waste folders
   # are created to store extraneous files prior to their removal
   set subFolder = `echo $zipItem | cut -d "/" -f2`
   set sesFolder = `echo $zipItem | cut -d "/" -f3`
   mkdir rmThisDirWhenDone/rm-$sesFolder

   set zipFile = `echo $zipItem | cut -d "/" -f4`
   set unzippedFolder = `echo $zipFile | cut -d "-" -f1,2`

   set rmList = ""
   set dicomList = `find ./$subFolder/$sesFolder/ -mindepth 1 -maxdepth 2 -type f -name "GERT*"`
   set dimonList = `find ./$subFolder/$sesFolder/ -mindepth 1 -maxdepth 2 -type f -name "dimon*"`
   set rmList = ( $dicomList $dimonList )

   echo Moving the following list to rmThisDirWhenDone/rm-$sesFolder
   echo $zipItem
   echo ./$subFolder/$sesFolder/$unzippedFolder
   echo $rmList

   mv -f $zipItem ./$subFolder/$sesFolder/$unzippedFolder $rmList rmThisDirWhenDone/rm-$sesFolder
   
end

# Remove files that are not BIDS-compliant
rm -rf rmThisDirWhenDone

# Anonymize AFNI file history by denoting with 3drefit
set allScans = `find -maxdepth 2 -mindepth 5 -type f -name "*+orig.HEAD"`

foreach scan ( $allScans )

   set scanOrig = `echo $scan | cut -d "." -f1,2`
   3drefit -denote $scanOrig
   
end

