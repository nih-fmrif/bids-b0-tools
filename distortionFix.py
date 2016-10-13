#!/usr/bin/env python

import time, sys, os
from   subprocess import Popen, PIPE, STDOUT
from   optparse  import  OptionParser
from   bidsFSUtils import bidsToolsFS



def afniBlipUpDown (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey     = "T1w"
   epiRunKey     = "dir-y_run"
   blipForRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"
   magRunKey     = "magnitude"
   freqRunKey    = "frequency"
   dataNeedingGiantMove = ["",""] # Enter subject IDs that need giant_move

   for eachSubject in bidsSubjectDict.keys():

      subjLoc = bidsTopLevelDir + eachSubject + "/"

      for eachSession in bidsSubjectDict[eachSubject].keys():
         if "NULL" in eachSession:
            sessLoc = subjLoc
         else:
            sessLoc = subjLoc + eachSession + "/"

         epiDsets = ""

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():
            scanTypeLoc = sessLoc + eachScanType + "/"

            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:

               runLoc = scanTypeLoc + eachRun

               if t1wRunKey in runLoc:
                  anatOrig = runLoc + "+orig"

               # if epiRunKey in runLoc:
               if blipForRunKey in runLoc:
                  epiDsets = scanTypeLoc + 'data2Fix'
                  epiDsetCopyCmd = "3dTcat -prefix " + epiDsets + " " + runLoc + "+orig[0..9]"
                  os.system (epiDsetCopyCmd)

               if blipForRunKey in runLoc:
                  blipForHead = runLoc + '+orig.HEAD[0..14]'
                  # blipForHead = runLoc + '+orig.HEAD[1]' # For data with low contrast in time series

               if blipRevRunKey in runLoc:
                  blipRevHead = runLoc + '+orig.HEAD'
                  # blipRevHead = runLoc + '+orig.HEAD[1]' # For data with low contrast in time series

               # if magRunKey in runLoc:
               #    magOrig = runLoc + "+orig"

               # if freqRunKey in runLoc:
               #    freqOrig = runLoc + "+orig"

         if eachSubject in dataNeedingGiantMove:
            giantMoveOption = "-giant_move"
         else:
            giantMoveOption = ""

         afniSubProc = ["afni_proc.py", "-subj_id", eachSubject + "-" + eachSession,
                        "-copy_anat", anatOrig,
                        "-dsets", epiDsets + "+orig",
                        "-blocks", "align",
                        "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveOption,
                        "-blip_reverse_dset", blipRevHead,
                        "-blip_forward_dset", blipForHead
                        ]

         # Run afni_proc.py to generate the analysis tcsh script for each session
         # of collected data.
         afniPreProc = Popen(afniSubProc, stdout=PIPE, stderr=PIPE)



def fslBlipUpDown (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey     = "T1w"
   epiRunKey     = "dir-y_run"
   blipForRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"
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
               elif epiRunKey in runLoc: # For this analysis we use the resting/task
		                         # for the forward calibration scan. Not
		                         # always going to be the case.
                  blipRest = runLoc + '+orig[0..29]'
                  restDsetCopyCmd = "3dTcat -prefix rest-" + eachSubject + ".nii.gz" + " " + blipRest
                  os.system (restDsetCopyCmd)
                  blipFor = runLoc + '+orig[1]'
               elif blipRevRunKey in runLoc:
                  blipRev = runLoc + '+orig[1]'
               else:
                  pass

         acqParams = "acqParams.txt" # name of the text file with four columns
         warpRes = "10" # default is 10
         bothBlipsCmd = "3dTcat -prefix bothBlips-" + eachSubject + ".nii.gz" + " " + blipRev + " " + blipFor
         os.system (bothBlipsCmd)

         # Gather inputs and execute topup command
         imainInputA = "--imain=bothBlips-" + eachSubject
         datainInputA = "--datain=" + acqParams
         configInput = "--config=b02b0.cnf"
         outInputA = "--out=warpField-" + eachSubject
         warpresInput = "--warpres=" + warpRes
         print "Step 1: Running topup on " + str(eachSubject)
         fslProcA = Popen(["topup", imainInputA, datainInputA, outInputA,
                           configInput], stdout=PIPE, stderr=PIPE)
         fslProcA.wait()

         # When topup completes, gather inputs and execute applytopup command
         # This will generate distortion-corrected EPIs using the warp field
         # output from topup.
         imainInputB = "--imain=rest-" + eachSubject
         inindexInput = "--inindex=2"
         datainInputB = "--datain=" + acqParams
         topupInput = "--topup=warpField-" + eachSubject
         interpInput = "--interp=spline"
         outInputB = "--out=restCorrected-" + eachSubject
         methodInput = "--method=jac"
         print "Step 2: Running applytopup on " + str(eachSubject)
         fslProcB = Popen(["applytopup", imainInputB, inindexInput,
                           datainInputB, topupInput, interpInput, outInputB,
                           methodInput], stdout=PIPE, stderr=PIPE)
         fslProcB.wait()

         # When applytopup completes, gather inputs and execute afni_proc.py command.
         # This is to align the anatomical scan to the FSL output EPIs.
         if eachSubject in dataNeedingGiantMove:
            giantMoveOption = "-giant_move"
         else:
            giantMoveOption = ""

         dsetsInput = "restCorrected-" + eachSubject + ".nii.gz"
         print "Step 3: Running afni_proc.py on " + str(eachSubject)
         afniSubProc = ["afni_proc.py", "-subj_id", eachSubject,
                        "-copy_anat", anatOrig,
                        "-dsets", dsetsInput,
                        "-blocks", "align",
                        "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveOption,
                        "-execute"
                        ]

         # Run afni_proc.py to generate the analysis tcsh script for each session
         # of collected data.
         afniPreProc = Popen(afniSubProc, stdout=PIPE, stderr=PIPE)
         afniPreProc.wait()

         # Move files created by topup and applytopup to subject's results folder
         # that was created after AFNI alignment
         moveDestInput = eachSubject + ".results/"
         moveFilesInput = "*?" + eachSubject + "*"
         os.system ("mv -t " + moveDestInput + " " + moveFilesInput)


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
                    "--dwell=620e-6",      # EPI dwell time/echo spacing. i.e. 650e-6 for 650 microseconds.
                    "--unwarpdir=___"]) # EPI phase encoding direction - x,x-,y,y-,z,z-. (default = y)

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
   parser.add_option ("-f", "--fsl",      action="store_false", dest="software", default=True,
                                          help="Alternative to -a, runs distortion correction using FSL")
   
   parser.add_option ("-e", "--epiFmaps", action="store_true", dest="scan", default=True,
                                          help="DEFAULT, inputs are Reverse Blip Epi Scans")
   parser.add_option ("-b", "--B0Fmaps",  action="store_false", dest="scan", default=True,
                                          help="Alternative to -e, inputs are B0 Field Maps")

   (options, args) = parser.parse_args()

   if ( str(options.dataDir)[-1] != "/" ):
      options.dataDir = str(options.dataDir) + "/"

   bidsDict = bidsToolsFS().buildBIDSDict(options.dataDir)

   if (options.software and options.scan):
      print "Starting distortion correction using AFNI's BLIP-UP/DOWN TOOLS"
      afniBlipUpDown (options.dataDir, bidsDict)

   if (options.software and not options.scan):
      print "Coming soon attractions ... distortion correction featuring AFNI's B0 FIELD MAP TOOLS"

   if (not options.software and options.scan):
      print "Starting distortion correction using FSL's TOPUP"
      fslBlipUpDown (options.dataDir, bidsDict)

   if (not options.software and not options.scan):
      print "Coming soon attractions ... distortion correction starring FSL's FUGUE"

   
if __name__ == '__main__':
   sys.exit(main())

