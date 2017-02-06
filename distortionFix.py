#!/usr/bin/env python

import time, sys, os
from   subprocess import Popen, PIPE, STDOUT
from   optparse  import  OptionParser
from   bidsFSUtils import bidsToolsFS


defaultExt = ".nii"      # For NIFTI datasets
# defaultExt = "+orig"   # For AFNI datasets

allData = ["sub-%02d" % i for i in range(1,53)]

dataNeedingGiantMove = ["sub-09_ses-03","sub-12_ses-02","sub-14_ses-02",
                        "sub-25_ses-01","sub-28_ses-01","sub-28_ses-02",
			"sub-37_ses-02"]
giantMoveDict = dict()
for subj in allData:
   if subj in dataNeedingGiantMove:
      giantMoveDict.update({subj: "-giant_move"})
   else:
      giantMoveDict.update({subj: ""})

# executeProcs = ""           # Generate proc scripts but do not execute
executeProcs = "-execute"   # Generate proc scripts and execute


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

         runLoc = ""
         anatOrig = ""
         epiDsets = ""
         blipForHead = ""
         blipRevHead = ""

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():
            
            scanTypeLoc = sessLoc + eachScanType + "/"

            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:

               runLoc = scanTypeLoc + eachRun

               if t1wRunKey in runLoc:
                  anatOrig = runLoc

               if blipForRunKey in runLoc:
                  epiDsets = scanTypeLoc + 'data2Fix' + defaultExt
                  blipFor = runLoc + '[0..9]'

               if blipForRunKey in runLoc:
                  # blipForHead = runLoc + '+orig.HEAD[0..14]'
                  blipForHead = runLoc + '[1]' # For data with low contrast in time series

               if blipRevRunKey in runLoc:
                  # blipRevHead = runLoc + '+orig.HEAD'
                  blipRevHead = runLoc + '[1]' # For data with low contrast in time series

         eachSubSes = eachSubject + "_" + eachSession

	 if not ( (runLoc == "") or (anatOrig == "") or (epiDsets == "") or (blipForHead == "") or (blipRevHead == "") ):
            print "Starting fslBlipUpDown for " + str(eachSubSes)
            epiDsetCopyCmd = "3dTcat -prefix " + epiDsets + " " + blipFor
            os.system (epiDsetCopyCmd)

            executeAndWait(["afni_proc.py", "-subj_id", eachSubSes,
                           "-copy_anat", anatOrig,
                           "-dsets", epiDsets,
                           "-blocks", "align",
                           "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubject],
                           "-Allineate_opts", "-warp", "shift_rotate",
                           "-blip_reverse_dset", blipRevHead,
                           "-blip_forward_dset", blipForHead,
                           executeProcs])

         elif ( (runLoc == "") or (anatOrig == "") or (epiDsets == "") or (blipForHead == "") or (blipRevHead == "") ):
            print str(eachSubSes) + " does not have necessary scans for afniBlipUpDown!"
            break


def afniB0 (bidsTopLevelDir, bidsSubjectDict):

   # in progress

   """
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

         runLoc = ""
         anatOrig = ""
         blipRest = ""
         blipFor = ""
         blipRev = ""
         magOrig = ""
         freqOrig = ""
         maskOrig = ""

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

         if ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (blipFor == "") or (blipRev == "") or (magOrig == "") or (freqOrig == "") or (maskOrig == "") ):
            print str(eachSubject) + "/" + str(eachSession) + " does not have complete data for AFNI B0 correction"
         else:
            print str(eachSubject) + "/" + str(eachSession) + " is good to go!"

         executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
                        "-expr", "(a-16383)*2.0*PI*step(b)", # Other analyses may use different scaling.
                        "-datum", "float", "-prefix", "fmapInRPS-" + eachSubject + defaultExt])

         executeAndWait(["3dPolyfit", "-nord", "9", "-prefix", eachSubject + "_fittedMask.nii.gz",
                         "-verb", "fmapInRPS-" + eachSubject + defaultExt])                 

         executeAndWait(["3dcalc", "-a", eachSubject + "_fittedMask.nii.gz", "-b", maskOrig,
                        "-expr", "a*step(b)", 
                        "-datum", "float", "-prefix", "fmapFittedInRPSMasked-" + eachSubject + defaultExt])

         # Unifize anatomical scan
         executeAndWait(["3dUnifize", "-prefix", "magUF-" + eachSubject + defaultExt, "-input", magOrig])
         
         # Automask command to generate mask from mag:
         executeAndWait(["3dAutomask", "-prefix", "magUFMaskE3-" + eachSubject + defaultExt,
                        "-erode", "3", "-peels", "2", "magUF-" + eachSubject + defaultExt])

         # Now compute B0 map in radians per sec and mask in single step:
         executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
                        "-expr", "(a-16383)*2.0*PI*step(b)", # Other analyses may use different scaling.
                        "-datum", "float", "-prefix", "fmapInRPSMasked-" + eachSubject + defaultExt])

         # When fugue completes, gather inputs and execute afni_proc.py command.
         This is to align the anatomical scan to the FSL output EPIs.
         dsetsInput = "epiFixed-" + eachSubject + ".nii.gz"
         executeAndWait(["afni_proc.py", "-subj_id", eachSubject + "_" + eachSession,
                        "-copy_anat", anatOrig,
                        "-dsets", dsetsInput,
                        "-blocks", "align",
                        "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubject],
                        "-Allineate_opts", "-warp", "shift_rotate", # to avoid changing shape of brain to match fixed or original
                                                                    # echo planar images.  Potentially apply to _ALL_ correction
                                                                    # schemes (blip-up/down included)
                        executeProcs])

         # Move files created by fugue to subject's results folder.
         moveDestInput = eachSubject + "_" + eachSession + ".results/"
         moveFilesInput = "*?" + eachSubject + "*"
         os.system ("mv -t " + moveDestInput + " " + moveFilesInput)
         print str(eachSubject) + " completed"
   """


def fslBlipUpDown (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey     = "T1w"
   epiRunKey     = "dir-y_run"
   blipForRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"

   acqParams = "acqParams.txt" # name of the text file with four columns
   if not os.path.isfile(acqParams):
      print "fslBlipUpDown requires acquisition parameters text file! Currently defined as: " + str(acqParams)
      return

   for eachSubject in bidsSubjectDict.keys():

      subjLoc = bidsTopLevelDir + eachSubject + "/"

      for eachSession in bidsSubjectDict[eachSubject].keys():

         if "NULL" in eachSession:
            sessLoc = subjLoc
         else:
            sessLoc = subjLoc + eachSession + "/"

         runLoc   = ""
         anatOrig = ""
         blipRest = ""
         blipFor  = ""
         blipRev  = ""

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():

            scanTypeLoc = sessLoc + eachScanType + "/"

            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:
               runLoc = scanTypeLoc + eachRun
               if t1wRunKey in runLoc:
                  anatOrig = runLoc
               elif epiRunKey in runLoc: # For this analysis we use the resting/task
                                         # for the forward calibration scan. Not
                                         # always going to be the case.
                  blipRest = runLoc + '[0..29]'
                  blipFor = runLoc + '[1]'
               elif blipRevRunKey in runLoc:
                  blipRev = runLoc + '[1]'
               else:
                  pass

         eachSubSes = eachSubject + "_" + eachSession

         if not ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (blipFor == "") or (blipRev == "") ):

            print "Starting fslBlipUpDown for " + str(eachSubSes)
            restDsetCopyCmd = "3dTcat -prefix rest-" + eachSubSes + defaultExt + " " + blipRest
            os.system (restDsetCopyCmd)
            bothBlipsCmd = "3dTcat -prefix bothBlips-" + eachSubSes + defaultExt + " " + blipRev + " " + blipFor
            os.system (bothBlipsCmd)

            # Gather inputs and execute topup command
            imainInputA = "--imain=bothBlips-" + eachSubSes
            datainInputA = "--datain=" + acqParams
            configInput = "--config=b02b0.cnf"
            outInputA = "--out=warpField-" + eachSubSes
            print "Step 1: Running topup on " + str(eachSubSes)
            executeAndWait(["topup", imainInputA, datainInputA, outInputA, configInput])

            # When topup completes, gather inputs and execute applytopup command
            # This will generate distortion-corrected EPIs using the warp field
            # output from topup.
            imainInputB = "--imain=rest-" + eachSubSes
            inindexInput = "--inindex=2"
            datainInputB = "--datain=" + acqParams
            topupInput = "--topup=warpField-" + eachSubSes
            interpInput = "--interp=spline"
            outInputB = "--out=epiFixed-" + eachSubSes
            methodInput = "--method=jac"
            print "Step 2: Running applytopup on " + str(eachSubSes)
            executeAndWait(["applytopup", imainInputB, inindexInput,
                              datainInputB, topupInput, interpInput, outInputB,
                              methodInput])

           # When applytopup completes, gather inputs and execute afni_proc.py command.
            # This is to align the anatomical scan to the FSL output EPIs.
            dsetsInput = "epiFixed-" + eachSubSes + defaultExt
            print "Step 3: Running afni_proc.py on " + str(eachSubSes)
            executeAndWait(["afni_proc.py", "-subj_id", eachSubSes,
                           "-copy_anat", anatOrig,
                           "-dsets", dsetsInput,
                           "-blocks", "align",
                           "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubject],
                           "-Allineate_opts", "-warp", "shift_rotate",
                           executeProcs])

            # Move files created by topup and applytopup to subject's results folder
            # that was created after AFNI alignment
            moveDestInput = eachSubSes + ".results/"
            moveFilesInput = "*?" + eachSubSes + "*"
            os.system ("mv -t " + moveDestInput + " " + moveFilesInput)

         elif ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (blipFor == "") or (blipRev == "") ):
            print str(eachSubSes) + " does not have all the required scans for fslBlipUpDown!"
            break


def fslB0 (bidsTopLevelDir, bidsSubjectDict):
   
   fslB0Step = raw_input("Enter 1 to normalize magnitude data and generate masks or \
                        \nEnter 2 to fix distortions with fugue (mask required!) :")
   print "Executing step " + str(fslB0Step)

   t1wRunKey     = "T1w"
   epiRunKey     = "dir-y_run"
   blipForRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"
   magRunKey     = "magnitude"
   freqRunKey    = "frequency"
   maskRunKey    = "magUFMask"

   for eachSubject in bidsSubjectDict.keys():

      subjLoc = bidsTopLevelDir + eachSubject + "/"

      for eachSession in bidsSubjectDict[eachSubject].keys():

         if "NULL" in eachSession:
            sessLoc = subjLoc
         else:
            sessLoc = subjLoc + eachSession + "/"

         runLoc   = ""
         anatOrig = ""
         blipRest = ""
         blipRev  = ""
         magOrig  = ""
         freqOrig = ""
         maskOrig = ""

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():

            scanTypeLoc = sessLoc + eachScanType + "/"

            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:

               runLoc = scanTypeLoc + eachRun

               if t1wRunKey in runLoc:
                  anatOrig = runLoc
               elif epiRunKey in runLoc: # For this analysis we use the resting/task
                                         # for the forward calibration scan. Not
                                         # always going to be the case.
                  blipRest = runLoc + '[0]' # Test, previously used '+orig[0..29]'
               elif blipRevRunKey in runLoc:
                  blipRev = runLoc + '[0]'
               elif magRunKey in runLoc:
                  magOrig = runLoc
               elif freqRunKey in runLoc:
                  freqOrig = runLoc
               elif maskRunKey in runLoc:
                  maskOrig = runLoc
               else:
                  pass

         eachSubSes = eachSubject + "_" + eachSession

         # This module is executed in two steps. Step 1 creates masks and step 2 uses masks for corrections.
         # The masks from step 1 were edited by hand using AFNI's draw ROI tool.
         
         if ( (fslB0Step == "1") and not ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (magOrig == "") or (freqOrig == "") ) ):
            print "Starting fslBlipUpDown for " + str(eachSubSes)
            restDsetCopyCmd = "3dTcat -prefix rest-" + eachSubSes + defaultExt + " " + blipRest
            os.system (restDsetCopyCmd)
            
            # Step 1a. Unifize magnitude data
            print "Starting step 1a (3dUnifize) for " + str(eachSubSes)
            executeAndWait(["3dUnifize", "-prefix",
                            "magUF-" + eachSubSes + defaultExt,
                            "-input", magOrig])
         
            # Step 1b. Automask command to generate mask from mag:
            print "Starting step 1b (3dAutomask) for " + str(eachSubSes)
            executeAndWait(["3dAutomask", "-prefix",
                            eachSubSes + "_magUFMask" + defaultExt,
                            "-erode", "3", "-peels", "2",
                            "magUF-" + eachSubSes + defaultExt])


            print str(eachSubSes) + " step 1 complete."
            
         elif ( (fslB0Step == "1") and ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (magOrig == "") or (freqOrig == "") ) ):
            print str(eachSubSes) + " does not have all the required scans for fslB0!"
            break


         if ( (fslB0Step == "2") and not ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (maskOrig == "") or (freqOrig == "") ) ):
            # Step 2a. Now compute B0 map in radians per sec and mask:
            print "Starting step 2a (3dROIstats+3dcalc) for " + str(eachSubSes)
            # Find the mode of the frequency distribution in the brain and
            # subtract this value from the field map. This is from potential vendor
            # offsets in F0.
            freqMode1 = Popen(["3dROIstats", "-nomeanout", "-quiet", "-mask", maskOrig, "-mode", freqOrig], stdout=PIPE)
            freqOut = freqMode1.communicate()[0]
            executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
                           "-expr", "(a-" + freqOut.strip() + ")*2.0*PI*step(b)", # Other analyses may use different scaling.
                           "-datum", "float", "-prefix", "fmapInRPSMasked-" + eachSubSes + defaultExt])

            # Step 2b. Now fix distortions with fugue
            executeAndWait(["3dcalc", "-a", blipRest, "-b", blipRev,
                            "-expr", "isnegative(a+b-1000)", "-datum", "float",
                            "-prefix", "epiNegMask_" + eachSubSes + defaultExt])

            unwarpTestDict = {}
            
            distDirections = ["x","x-","y","y-"]
            for eachDirection in distDirections:
               print "Starting step 2b (fugue) for " + str(eachSubSes)
               executeAndWait(["fugue", "-i", "rest-" + eachSubSes, "--dwell=310e-6",
                              "--loadfmap=fmapInRPSMasked-" + eachSubSes + defaultExt,
                              "-u", "epiFixed-" + eachSubSes + "_unwarpDir-" + eachDirection, 
                              "--unwarpdir=" + eachDirection, # To test best direction, run four times with  
                                                              # distDict[eachSubject] replaced with x, x-, y, and x-
                              "--savefmap=" + "fmapSmooth3_2-" + eachSubSes,
                              "--smooth3=2"])

               executeAndWait(["3dcalc", "-a", "epiFixed-" + eachSubSes + "_unwarpDir-" + eachDirection + defaultExt,
                               "-expr", "ispositive(a-1000)", "-datum", "float",
                               "-prefix", "epiFixedMask_" + eachSubSes + "_" + eachDirection + defaultExt])

               epiMaskMean = Popen(["3dROIstats", "-nomeanout", "-quiet", "-mask", "epiNegMask_" + eachSubSes + defaultExt,
                                    "-nzsum", "epiFixedMask_" + eachSubSes + "_" + eachDirection + ".nii.gz"], stdout=PIPE)
               epiMaskMeanOut = epiMaskMean.communicate()[0]
               unwarpTestDict.update({eachDirection: epiMaskMeanOut.strip()})

            bestUnwarpTest = min(unwarpTestDict.values(), key=float)
            print str(unwarpTestDict)
            print "Value of least difference from sum of epiFor+epiRev is " + str(bestUnwarpTest)
            for unwarpTest, unwarpValue in unwarpTestDict.iteritems():
               if unwarpValue == bestUnwarpTest:
                  bestUnwarpDir = unwarpTest
            print "Best unwarp direction for " + str(eachSubSes) + " is therefore " + str(bestUnwarpDir)

            print "Fugue completed for " + str(eachSubSes)

            # Step 2c. When fugue completes, gather inputs and execute afni_proc.py command.
            print "Starting step 2c (afni_proc.py) for " + str(eachSubSes)
            # This is to align the anatomical scan to the FSL output EPIs.
            dsetsInput = "epiFixed-" + eachSubSes + "_unwarpDir-" + bestUnwarpDir + defaultExt
            executeAndWait(["afni_proc.py", "-subj_id", eachSubSes,
                           "-copy_anat", anatOrig,
                           "-dsets", dsetsInput,
                           "-blocks", "align",
                           "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubject],
                           "-Allineate_opts", "-warp", "shift_rotate", # to avoid changing shape of brain to match fixed or original
                                                                       # echo planar images.  Potentially apply to _ALL_ correction
                                                                       # schemes (blip-up/down included)
                           executeProcs])

            # Move files created by fugue to subject's results folder.
            moveDestInput = eachSubSes + ".results/"
            moveFilesInput = "*?" + eachSubSes + "*"
            os.system ("mv -t " + moveDestInput + " " + moveFilesInput)
            print str(eachSubSes) + " fslB0 step 2 complete."

         elif ( (fslB0Step == "2") and ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (maskOrig == "") or (freqOrig == "") ) ):
            print str(eachSubSes) + " does not have required scans (and/or mask) for fslB0 step 2!"
            break



def executeAndWait(commandArray):

   thisPopen = Popen(commandArray, stdout=PIPE, stderr=PIPE)

   thisPopen.wait()



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
      print "Coming attractions... AFNI's B0 TOOLS!"
      afniB0 (options.dataDir, bidsDict)

   if (not options.software and options.scan):
      print "Starting distortion correction using FSL's TOPUP"
      fslBlipUpDown (options.dataDir, bidsDict)

   if (not options.software and not options.scan):
      print "Starting distortion correction using FSL's FUGUE"
      fslB0 (options.dataDir, bidsDict)


   
if __name__ == '__main__':
   sys.exit(main())

