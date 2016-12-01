#!/usr/bin/env python

import time, sys, os
from   subprocess import Popen, PIPE, STDOUT
from   optparse  import  OptionParser
from   bidsFSUtils import bidsToolsFS



defaultExt = ".nii.gz" # NIFTI should be default
# defaultExt = "+orig"

allData = ["",""]

dataNeedingGiantMove = ["",""] # Enter subject IDs that need giant_move
giantMoveDict = dict()
for subj in allData:
   if subj in dataNeedingGiantMove:
      giantMoveDict.update({subj: "-giant_move"})
   else:
      giantMoveDict.update({subj: ""})
      
distDirection = ["x-", "y-", "y-", "y-", "x-", "x-", "y-", "x-", "x-", "x-", "y-", "y-",
                 "y-", "x-", "y-", "y-", "x-", "x-", "y-", "y-", "y-", "y-", "y-", "x-"] # Enter each subject's distortion direction
distDict = dict()
for subject, dist in zip(allData, distDirection):
   distDict[subject] = dist



def afniBlipUpDown (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey     = "T1w"
   epiRunKey     = "dir-y_run"
   blipForRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"

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

         afniSubProc = ["afni_proc.py", "-subj_id", eachSubject + "-" + eachSession,
                        "-copy_anat", anatOrig,
                        "-dsets", epiDsets + "+orig",
                        "-blocks", "align",
                        "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubject],
                        "-blip_reverse_dset", blipRevHead,
                        "-blip_forward_dset", blipForHead
                        ]

         # Run afni_proc.py to generate the analysis tcsh script for each session
         # of collected data.
         afniPreProc = Popen(afniSubProc, stdout=PIPE, stderr=PIPE)



def afniB0 (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey     = "T1w"
   epiRunKey     = "dir-y_run"
   blipForRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"
   magRunKey     = "magnitude"
   freqRunKey    = "frequency"
   maskRunKey    = "mask"

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
                  blipRest = runLoc + '+orig[0]' # Test, previously used '+orig[0..29]'
                  restDsetCopyCmd = "3dTcat -prefix rest-" + eachSubject + ".nii.gz" + " " + blipRest
                  os.system (restDsetCopyCmd)
                  # blipFor = runLoc + '+orig[1]'
               elif blipRevRunKey in runLoc:
                  blipRev = runLoc + '+orig[1]'
	       elif magRunKey in runLoc:
	          magOrig = runLoc + '+orig'
	       elif freqRunKey in runLoc:
	          freqOrig = runLoc + '+orig'
               elif maskRunKey in runLoc:
	          maskOrig = runLoc + '+orig'
               else:
                  pass

         executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
	                "-expr", "(a-16383)*2.0*PI*step(b)", # Other analyses may use different scaling.
	                "-datum", "float", "-prefix", "fmapInRPS-" + eachSubject + defaultExt])

         executeAndWait(["3dPolyfit", "-nord", "9", "-prefix", eachSubject + "_fittedMask.nii.gz",
	                 "-verb", "fmapInRPS-" + eachSubject + defaultExt])		 

         executeAndWait(["3dcalc", "-a", eachSubject + "_fittedMask.nii.gz", "-b", maskOrig,
	                "-expr", "a*step(b)", 
	                "-datum", "float", "-prefix", "fmapFittedInRPSMasked-" + eachSubject + defaultExt])

         # Unifize anatomical scan
         # executeAndWait(["3dUnifize", "-prefix", "magUF-" + eachSubject + defaultExt, "-input", magOrig])
	 
         # Automask command to generate mask from mag:
         # executeAndWait(["3dAutomask", "-prefix", "magUFMaskE3-" + eachSubject + defaultExt,
         #                "-erode", "3", "-peels", "2", "magUF-" + eachSubject + defaultExt])

         # Now compute B0 map in radians per sec and mask in single step:
         # executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
	 #                "-expr", "(a-16383)*2.0*PI*step(b)", # Other analyses may use different scaling.
	 #                "-datum", "float", "-prefix", "fmapInRPSMasked-" + eachSubject + defaultExt])

         # When fugue completes, gather inputs and execute afni_proc.py command.
         # This is to align the anatomical scan to the FSL output EPIs.
         # dsetsInput = "epiFixed-" + eachSubject + ".nii.gz"
         # executeAndWait(["afni_proc.py", "-subj_id", eachSubject,
         #                "-copy_anat", anatOrig,
         #                "-dsets", dsetsInput,
         #                "-blocks", "align",
         #                "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubject],
         #                "-Allineate_opts", "-warp", "shift_rotate", # to avoid changing shape of brain to match fixed or original
         #                                                            # echo planar images.  Potentially apply to _ALL_ correction
         #                                                            # schemes (blip-up/down included)
         #                "-execute"])

         # Move files created by fugue to subject's results folder.
         # moveDestInput = eachSubject + ".results/"
         # moveFilesInput = "*?" + eachSubject + "*"
         # os.system ("mv -t " + moveDestInput + " " + moveFilesInput)
	 print str(eachSubject) + " completed."



def fslBlipUpDown (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey     = "T1w"
   epiRunKey     = "dir-y_run"
   blipForRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"

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
         executeAndWait(["topup", imainInputA, datainInputA, outInputA,
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
         outInputB = "--out=epiFixed-" + eachSubject
         methodInput = "--method=jac"
         print "Step 2: Running applytopup on " + str(eachSubject)
         fslProcB = Popen(["applytopup", imainInputB, inindexInput,
                           datainInputB, topupInput, interpInput, outInputB,
                           methodInput], stdout=PIPE, stderr=PIPE)
         fslProcB.wait()

         # When applytopup completes, gather inputs and execute afni_proc.py command.
         # This is to align the anatomical scan to the FSL output EPIs.
         dsetsInput = "restCorrected-" + eachSubject + ".nii.gz"
         print "Step 3: Running afni_proc.py on " + str(eachSubject)
         afniSubProc = ["afni_proc.py", "-subj_id", eachSubject,
                        "-copy_anat", anatOrig,
                        "-dsets", dsetsInput,
                        "-blocks", "align",
                        "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubject],
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



def fslB0 (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey     = "T1w"
   epiRunKey     = "dir-y_run"
   blipForRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"
   magRunKey     = "magnitude"
   freqRunKey    = "frequency"
   maskRunKey    = "mask"

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
                  blipRest = runLoc + '+orig[0]' # Test, previously used '+orig[0..29]'
                  restDsetCopyCmd = "3dTcat -prefix rest-" + eachSubject + ".nii.gz" + " " + blipRest
                  os.system (restDsetCopyCmd)
                  # blipFor = runLoc + '+orig[1]'
               elif blipRevRunKey in runLoc:
                  blipRev = runLoc + '+orig[1]'
	       elif magRunKey in runLoc:
	          magOrig = runLoc + '+orig'
	       elif freqRunKey in runLoc:
	          freqOrig = runLoc + '+orig'
               elif maskRunKey in runLoc:
	          maskOrig = runLoc + '+orig'
               else:
                  pass

         # This module was broken into two steps. First, create masks. Second, use masks to do corrections.
	 # The masks from step one were edited by hand using AFNI's draw ROI tool.

         # Begin step one. Run the next two commands, but prevent the rest from executing.
	 
         # Step 1a. Unifize magnitude data
         # executeAndWait(["3dUnifize", "-prefix", "magUF-" + eachSubject + defaultExt, "-input", magOrig])
	 
         # Step 1b. Automask command to generate mask from mag:
         # executeAndWait(["3dAutomask", "-prefix", "magUFMaskE3-" + eachSubject + defaultExt,
         #                "-erode", "3", "-peels", "2", "magUF-" + eachSubject + defaultExt])

         # End step one and comment out the above two commands. Allow the following commands to run
	 # after masks have been hand-edited.
	 
         # Step 2a. Now compute B0 map in radians per sec and mask in single step:
         executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
	                "-expr", "(a-16383)*2.0*PI*step(b)", # Other analyses may use different scaling.
	                "-datum", "float", "-prefix", "fmapInRPSMasked-" + eachSubject + defaultExt])
	 
         # Step 2b. Now fix distortions with fugue
         executeAndWait(["fugue", "-i", "rest-" + eachSubject, "--dwell=310e-6",
	                "--loadfmap=fmapInRPSMasked-" + eachSubject + defaultExt,
	                "-u", "epiFixed-" + eachSubject, "--unwarpdir=" + distDict[eachSubject],
	                "--savefmap=" + "fmapSmoothedPoly5-" + eachSubject,
                        "--poly=5"])
	 print "Fugue completed for " + str(eachSubject)

         # Step 2c. When fugue completes, gather inputs and execute afni_proc.py command.
         # This is to align the anatomical scan to the FSL output EPIs.
         dsetsInput = "epiFixed-" + eachSubject + ".nii.gz"
         executeAndWait(["afni_proc.py", "-subj_id", eachSubject,
                        "-copy_anat", anatOrig,
                        "-dsets", dsetsInput,
                        "-blocks", "align",
                        "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubject],
                        "-Allineate_opts", "-warp", "shift_rotate", # to avoid changing shape of brain to match fixed or original
                                                                    # echo planar images.  Potentially apply to _ALL_ correction
								    # schemes (blip-up/down included)
                        "-execute"])

         # Move files created by fugue to subject's results folder.
         moveDestInput = eachSubject + ".results/"
         moveFilesInput = "*?" + eachSubject + "*"
         os.system ("mv -t " + moveDestInput + " " + moveFilesInput)
	 print str(eachSubject) + " completed."



def executeAndWait(commandArray):

   fslPopen = Popen(commandArray, stdout=PIPE, stderr=PIPE)

   fslPopen.wait()



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
      print "Starting distortion correction using AFNI's B0 TOOLS"
      afniB0 (options.dataDir, bidsDict)

   if (not options.software and options.scan):
      print "Starting distortion correction using FSL's TOPUP"
      fslBlipUpDown (options.dataDir, bidsDict)

   if (not options.software and not options.scan):
      print "Starting distortion correction using FSL's FUGUE"
      fslB0 (options.dataDir, bidsDict)


   
if __name__ == '__main__':
   sys.exit(main())

