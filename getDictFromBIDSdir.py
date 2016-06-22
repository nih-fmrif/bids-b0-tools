#!/usr/bin/env python

from   optparse  import  OptionParser
import time, sys, os
from   fs.opener import fsopendir, fsopen
# import subprocess
# import string


"""

This script is designed to traverse a BIDS formatted data tree, and label
the necessary data sets in each subject's folder needed for a particular
analysis.

"""



# class buildBIDSDict:

   #def __init__(self, options):

def buildBIDSDict(options):
  
      print "BIDS tree is " + options.dataDir
      bidsFS = fsopendir(options.dataDir)

      internalBIDSPath = bidsFS._decode_path(options.dataDir)

      # allFiles = bidsFS.walkfiles()
      subDirs = bidsFS.walkdirs(wildcard="*sub-*")
      subjectList = []

      allRuns = bidsFS.walkfiles(wildcard="*run*")
      # Store all unique dataset names
      runsList = []

      for eachRun in allRuns:
         # Delimiter here for AFNI formatted data sets. For 
         # proper BIDS tree, would need other scheme, e.g.:
         #
         # runRootName = eachRun.split(".")[0]
         runRootName = eachRun.split("+")[0]
         if runRootName not in runsList:
            runsList.append(runRootName)
      # print str(runsList)

      bidsMasterTreeDict = {}

      # Iterate over all datasets and build bidsMasterTreeDict
      for eachRun in runsList:

         runNameElements = eachRun.split("/")

         # If this is a properly formed BIDS tree, the format should be:
         # 
         #    sub-*/ses-*/scanType/*run*
         # 
         # or:
         # 
         #    sub-*/scanType/*run*

         thisRunName = runNameElements[-1]
         thisRunNameScanType = runNameElements[-2]

         if 'ses-' in runNameElements[-3]:
            thisRunNameSession = runNameElements[-3]
	    thisRunNameSub = runNameElements[-4]
         else:
	    thisRunNameSession = 'ses-0'
	    thisRunNameSub = runNameElements[-3]

         if thisRunNameSub not in bidsMasterTreeDict.keys():
	    sessionDict = {}
	    bidsMasterTreeDict[thisRunNameSub] = sessionDict
	    
	 if thisRunNameSession not in bidsMasterTreeDict[thisRunNameSub].keys():
	    scanTypeDict = {}
	    bidsMasterTreeDict[thisRunNameSub][thisRunNameSession] = scanTypeDict

	 if thisRunNameScanType not in bidsMasterTreeDict[thisRunNameSub][thisRunNameSession].keys():
            scanTypeRunList = []
            bidsMasterTreeDict[thisRunNameSub][thisRunNameSession][thisRunNameScanType] = scanTypeRunList

         if thisRunName not in bidsMasterTreeDict[thisRunNameSub][thisRunNameSession][thisRunNameScanType]:
	    bidsMasterTreeDict[thisRunNameSub][thisRunNameSession][thisRunNameScanType].append(thisRunName)

      return (bidsMasterTreeDict)

      """
      # rel_path = fs._decode_path(rel_path)
      
         # subprocess.call  (['3dcalc', 
                            # "-a", ("08_" + self.subjectID + "_anat"
                            # + "_unif" + ".nii" + self.compress),
                            # "-prefix", ("08_" + self.subjectID + "_anat"  \
                            # + "_unif_short" + ".nii" + self.compress),
                            # "-datum", "short", "-nscale", "-expr", "a"])

         # # create temporary obliquified anat (not aligned) for output grid
         # # create temporary obliquified anat (not aligned) for output grid
         # subprocess.call  (['3dWarp', 
                         # "-card2oblique", ("07_" + dataToCorrectName
                         # + "_unif.nii" + self.compress),
                         # "-prefix", ("08_" + self.subjectID + "_anat"  \
                         # + "_ob_temp" + ".nii" + self.compress),
                         # ("08_" + self.subjectID + "_anat"  \
                         # + "_unif_short" + ".nii" + self.compress)])

         # # align unifized, short integer data to EPI, with output on oblique anat grid
         # alignCmds = ['align_epi_anat.py',
                      # "-anat", ("08_" + self.subjectID + "_anat"
                      # + "_unif_short" + ".nii" + self.compress),
                      # "-epi", "07_" + dataToCorrectName + "_unif.nii" \
                      # + self.compress,
                      # "-epi_base", "0", "-epi_strip", "3dAutomask",
                      # "-suffix", "_aligned", "-cost", "lpa", "-master_anat",
                      # ("08_" + self.subjectID + "_anat"  \
                            # + "_ob_temp" + ".nii" + self.compress)]
         # # these skullstrip options worked well for a particular subject,
         # # but not so great for another.
         # # This is not critical for most alignments. Affine alignment
         # # register over the whole dataset, so bits of extra skull or missing brain
         # # generally won't change the alignment
         # #          "-skullstrip_opts", 
         # #          "-push_to_edge", "-shrink_fac", "0.1", "-shrink_fac_bot_lim", "0.01" ]

         # # Exercise user option for giant_move if required.
         # if self.giant_move == True:
            # alignCmds.append("-giant_move")

         # subprocess.call  (alignCmds)

      # # If we're all happy, then exit that way!
      # #   but who's ever "all happy" anyway?
      """
      sys.exit (1)



def main():

   """Will return an instance of the option list"""

   usage = "%prog [options]"
   description = ("Routine to build a command from a BIDS tree:")

   usage =       ("  %prog -d bidsDataTree" )
   epilog =      ("For questions, suggestions, information, please contact Vinai Roopchansingh, Jerry French")

   parser = OptionParser(usage=usage, description=description, epilog=epilog)

   parser.add_option ("-d", "--dataDir",  action="store",
                                          help="Directory with BIDS-formatted subject data folders")

   parser.add_option ("-g", "--giant_move", action="store_true",
                                          help="Set giant_move option for align_epi_anat if final align of anatomy to corrected EPI fails if datasets are far apart in space.")

   options, args = parser.parse_args()

   # print str(buildBIDSDict(options))

   # job2Run.unWarpData()

   bidsDict = buildBIDSDict(options)
   
   for eachSubject in bidsDict.keys():
      print "Subject's " + eachSubject + " dictionary is " + str(bidsDict[eachSubject])



if __name__ == '__main__':
   sys.exit(main())

