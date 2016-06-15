
### Locate Scans of Interest ###
set scanFolders = `find . -maxdepth 4 -mindepth 1 -type d -name "mr*"`
      
foreach folder ( $scanFolders )
   set referenceFile = `ls -1 $folder/*.dcm | head -1`
   set seriesDescription = `dicom_hdr $referenceFile | grep -i "series description"`

   echo
   echo Series description for series in folder $folder is $seriesDescription
   echo
end

