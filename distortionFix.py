#!/usr/bin/env python

import time, sys, os
from   subprocess import Popen, PIPE, STDOUT
from   optparse  import  OptionParser
from   bidsFSUtils import bidsToolsFS



def afniBlipUpDown (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey = "T1w"
   restRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"
   magRunKey = "magnitude"
   freqRunKey = "frequency"
   dataNeedingGiantMove = ["",""] # Enter subject IDs that need giant_move
   
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
               if t1wRunKey in runLoc:
                  anatOrig = runLoc + "+orig"
               elif restRunKey in runLoc: # For this analysis we use the resting/task
		                          # for the forward calibration scan. Not
		                          # always going to be the case.
                  blipForHead = runLoc + '+orig.HEAD[1]'
                  # Make copy of volume 0 of EPI time series to original location so it can
                  # be found by afni_proc.py.  Testing distortion correction and alignment
                  # with a single volume for now.
                  restDset = scanTypeLoc + 'data2Fix'
                  restDsetCopyCmd = "3dTcat -prefix " + restDset + " " + runLoc + "+orig[0]"
                  os.system (restDsetCopyCmd)
               elif blipRevRunKey in runLoc:
                  blipRevHead = runLoc + '+orig.HEAD[1]'
               # elif magRunKey in runLoc:
               #    magOrig = runLoc + "+orig"
               #    magNiiGz = runLoc + ".nii.gz"
               # elif freqRunKey in runLoc:
               #    freqOrig = runLoc + "+orig"
               else:
                  pass

         if eachSubject in dataNeedingGiantMove:
            giantMoveOption = "-giant_move"
         else:
            giantMoveOption = ""

         afniSubProc = ["afni_proc.py", "-subj_id", eachSubject,
                  "-copy_anat", anatOrig,
                  "-dsets", restDset + "+orig",
                  "-blocks", "align",
                  "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveOption,
                  "-blip_reverse_dset", blipRevHead,
                  "-blip_forward_dset", blipForHead
                  ]

         # Run afni_proc.py to generate the analysis tcsh script for each session
         # of collected data.
         afniPreProc = Popen(afniSubProc, stdout=PIPE, stderr=PIPE)

         """
         # The following will be used for analyzing the same data using FSL.
         # This may be added as a command line option.
         
         fslPreProcA = Popen(["3dSkullStrip", "-input", magOrig,
                    "-prefix", magNiiGz])
         fslPreProcB = Popen(["3dcalc", "-a", P9999_B0+orig, "-b", magNiiGz,
                    "-expr", "`1000.0 * a * step(b)`", "-datum", "float",
                    "-prefix", fmap_Bo_rps.nii.gz])
         fslPreProcC = Popen(["3dresample", "-inset", fmap_Bo_rps.nii.gz,
                    "-prefix", fmap_Bo_rps_rs.nii.gz, "-master",
                    EPIset.nii.gz])
 
         fslProcA = Popen(["fugue", "-i", EPIset, "-u", EPIdewarp,
                    "--loadfmap="fmap_Bo_rps_rs,
                    "--despike",
                    "--smooth2=___",    # specify smoothing sigma.
                    "--dwell=___",      # EPI dwell time/echo spacing. i.e. 650e-6 for 650 microseconds.
                    "--unwarpdir=___"]) # EPI phase encoding direction - x,x-,y,y-,z,z-.
         fslProcB = Popen(["topup", "--imain="all_my_b0_images.nii,
                    "--datain="acquisition_parameters.txt,
                    "--config="b02b0.cnf,
                    "--out="my_output])
         """


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

