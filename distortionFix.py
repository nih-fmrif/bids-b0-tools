#!/usr/bin/env python

import time, sys, os, subprocess
from   optparse  import  OptionParser
from   bidsFSUtils import bidsToolsFS



def afniBlipUpDown (bidsTopLevelDir, bidsSubjectDict):

   for eachSubject in bidsSubjectDict.keys():

      subjLoc = bidsTopLevelDir + eachSubject + "/"

      for eachSession in bidsSubjectDict[eachSubject].keys():
         if "NULL" in eachSession:
            sessLoc = subjLoc
         else:
            sessLoc = subjLoc + eachSession + "/"

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():
            scanTypeLoc = sessLoc + eachScanType + "/"

            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:
               runLoc = scanTypeLoc + eachRun
               if "T1w" in runLoc:
                  anatOrig = runLoc + "+orig"

               if "dir-y_run" in runLoc:
                  restHead = runLoc + "+orig.HEAD"

               if "dir-y-_run" in runLoc:
                  blipHead = runLoc + "+orig.HEAD"

         # Run afni_proc.py to generate the analysis tcsh script for each session
         # of collected data.
         subprocess.Popen(['afni_proc.py', '-subj_id', eachSubject,
                  '-copy_anat', anatOrig,
                  '-dsets', restHead,
                  '-blocks', 'tshift', 'align', 'volreg',
                  '-blip_reverse_dset', blipHead,
                  '-volreg_align_e2a'])



def main():

   """Will print the string equivalent of a dictionary
      representing a BIDS-formatted directory tree
      structure.
   """

   usage = "%prog [options]"
   description = ("Routine to build command to apply distortion correct to data pointed to\n by a dictionary from a BIDS tree:")

   usage =       ("  %prog -d bidsDataTree" )
   epilog =      ("For questions, suggestions, information, please contact Vinai Roopchansingh, Jerry French.")

   parser = OptionParser(usage=usage, description=description, epilog=epilog)

   parser.add_option ("-d", "--dataDir",  action="store",
                                          help="Directory with BIDS-formatted subject data folders")
   
   parser.add_option ("-a", "--afni",     action="store_true", dest="software", default=True,
                                          help="DEFAULT, runs distortion correction using AFNI")
   parser.add_option ("-f", "--fsl",      action="store_false", dest="software",
                                          help="Alternative to -a, runs distortion correction using FSL")
   
   parser.add_option ("-b", "--B0Fmaps",  action="store_true", dest="scan", default=True,
                                          help="DEFAULT, inputs Field Maps")
   parser.add_option ("-e", "--epiFmaps", action="store_true", dest="scan",
                                          help="Alternative to -b, inputs BlipUpDown Epi Scans")

   options, args = parser.parse_args()

   bidsDict = bidsToolsFS().buildBIDSDict(options.dataDir)

   afniBlipUpDown (options.dataDir, bidsDict)
   

   
if __name__ == '__main__':
   sys.exit(main())

