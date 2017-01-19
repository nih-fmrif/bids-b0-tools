
#!/bin/tcsh

# Find all BIDS-formatted files and count totals
# Write info to text file

set subDirs = `find . -mindepth 1 -maxdepth 1 -type d -name "sub-*"`

# BIDS suffix labels for scans within respective BIDS folders
set anatScans = "T1w T2w PD"
set funcScans = "_dir-y_"
set fmapScans = "_dir-y-_ frequency magnitude"
set otherScans = "asset mcdespot"
set allBIDS = ( $anatScans $funcScans $fmapScans $otherScans )

if ( -f scanCounts.txt ) then
   rm -f scanCounts.txt
   echo Directory $allBIDS  >>! scanCounts.txt
else
   echo Directory $allBIDS  >>! scanCounts.txt
endif

foreach subDir ( $subDirs )

   set nList = ""

   foreach eachBIDS ( $allBIDS )
   
      set nScans = 0
      
      echo `ls -R $subDir | grep -iq $eachBIDS`

      if ( $? ) then
         : # echo $subDir does not contain $eachBIDS scans
      else
         # echo $subDir contains $eachBIDS scans
         set nScans = `ls -R -1 $subDir | grep -c ".*"$eachBIDS".*.nii"`
         # set nScans = `ls -R -1 $subDir | grep -c ".*"$eachBIDS".*+orig.HEAD"`
	 
      endif
      
      set nList = ( $nList $nScans )

   end
   
   echo `echo $subDir | cut -d "/" -f2` $nList
   echo `echo $subDir | cut -d "/" -f2` $nList >>! scanCounts.txt
   
end

echo "\n" >>! scanCounts.txt
echo "SESSIONS" >>! scanCounts.txt
echo "\n" >>! scanCounts.txt
echo Directory $allBIDS  >>! scanCounts.txt

foreach subDir ( $subDirs )

   set sesDirs = `find ./$subDir -mindepth 1 -maxdepth 1 -type d -name "ses-*"`

   foreach sesDir ( $sesDirs )
   
      set mList = ""

      foreach eachBIDS ( $allBIDS )

         set mScans = 0

         echo `ls -R $sesDir | grep -iq $eachBIDS`

         if ( $? ) then
            : # echo $sesDir does not contain $eachBIDS scans
         else
            # echo $sesDir contains $eachBIDS scans
            set mScans = `ls -R -1 $sesDir | grep -c ".*"$eachBIDS".*.nii"`
            # set mScans = `ls -R -1 $sesDir | grep -c ".*"$eachBIDS".*+orig.HEAD"`

         endif

         set mList = ( $mList $mScans )

      end
      
      echo `echo $sesDir | cut -d "/" -f3,4` $mList
      echo `echo $sesDir | cut -d "/" -f3,4` $mList >>! scanCounts.txt
      
   end
   
end
