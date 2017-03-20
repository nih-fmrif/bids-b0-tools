#!/usr/bin/env python

import time, sys, os
from   subprocess import Popen, PIPE, STDOUT
from   optparse  import  OptionParser
from   bidsFSUtils import bidsToolsFS



defaultExt = ".nii"

allSub = ["sub-%02d" % i for i in range(1,99)]
allSes = ["ses-%02d" % j for j in range(1,5)]
allData = []

for sub in allSub:
   for ses in allSes:
      subSes = str(sub) + "_" + str(ses)
      allData.append(subSes)
   
dataNeedingGiantMove = [""]
giantMoveDict = dict()
for subj in allData:
   if subj in dataNeedingGiantMove:
      giantMoveDict.update({subj: "-giant_move"})
   else:
      giantMoveDict.update({subj: ""})

executeProcs = ""           # Generate proc scripts but DO NOT execute
# executeProcs = "-execute"   # Generate proc scripts and execute



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

         runLoc      = ""
         anatOrig    = ""
         epiDsets    = ""
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
                  blipFor = runLoc + '[0..24]'

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
                           "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubSes],
                           "-Allineate_opts", "-warp", "shift_rotate",
                           "-blip_reverse_dset", blipRevHead,
                           "-blip_forward_dset", blipForHead,
                           executeProcs])

            # send original T1, original rs-EPI, and fixed rs-EPI to registration step
            antsReg(anatOrig=anatOrig, blipRest=blipRest, dsetsInput=dsetsInput, eachSubSes=eachSubSes)

            print str(eachSubSes) + " complete."
            with open("afniBlipUpDownFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")

         elif ( (runLoc == "") or (anatOrig == "") or (epiDsets == "") or (blipForHead == "") or (blipRevHead == "") ):

	    print str(eachSubSes) + " does not have necessary scans for afniBlipUpDown!"
            with open("afniBlipUpDownFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            continue


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
      print "fslBlipUpDown requires acquisition parameters text file....."
      print "This is currently defined as: " + str(acqParams) + " in distortionFix.py"
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
                  blipRest = runLoc + '[0..24]'
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
            print "Running afni_proc.py on " + str(eachSubSes)
            executeAndWait(["afni_proc.py", "-subj_id", eachSubSes,
                           "-copy_anat", anatOrig,
                           "-dsets", dsetsInput,
                           "-blocks", "align",
                           "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubSes],
                           "-Allineate_opts", "-warp", "shift_rotate",
                           executeProcs])

            # send original T1, original rs-EPI, and fixed rs-EPI to registration step
            antsReg(anatOrig=anatOrig, blipRest=blipRest, dsetsInput=dsetsInput, eachSubSes=eachSubSes)

            # Move files created by topup and applytopup to subject's results folder
            # that was created after AFNI alignment
            moveDestInput = eachSubSes + ".results/"
            moveFilesInput = "*?" + eachSubSes + "*"
            os.system ("mv -t " + moveDestInput + " " + moveFilesInput)

            print str(eachSubSes) + " complete."
            with open("fslBlipUpDownFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")

         elif ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (blipFor == "") or (blipRev == "") ):

            print str(eachSubSes) + " does not have all the required scans for fslBlipUpDown!"
            with open("fslBlipUpDownFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            continue


def fslMaskB0 (bidsTopLevelDir, bidsSubjectDict):
   
   print "This module creates masks to be used with the fslB0 function."
   print "The masks can be edited by hand using AFNI's draw ROI tool."

   magRunKey     = "magnitude"

   for eachSubject in bidsSubjectDict.keys():

      subjLoc = bidsTopLevelDir + eachSubject + "/"

      for eachSession in bidsSubjectDict[eachSubject].keys():

         if "NULL" in eachSession:
            sessLoc = subjLoc
         else:
            sessLoc = subjLoc + eachSession + "/"

         runLoc   = ""
         magOrig  = ""

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():

            scanTypeLoc = sessLoc + eachScanType + "/"

            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:

               runLoc = scanTypeLoc + eachRun

               if magRunKey in runLoc:
                  magOrig = runLoc
               else:
                  pass

         eachSubSes = eachSubject + "_" + eachSession
         
         if not ( (runLoc == "") or (magOrig == "") ):

            print "Starting fslMaskB0 for " + str(eachSubSes)
            
            # Unifize magnitude data
            print "Starting step 1a (3dUnifize) for " + str(eachSubSes)
            executeAndWait(["3dUnifize", "-prefix",
                            "magUF-" + eachSubSes + defaultExt,
                            "-input", magOrig])
         
            # Automask command to generate mask from mag:
            print "Starting step 1b (3dAutomask) for " + str(eachSubSes)
            executeAndWait(["3dAutomask", "-prefix",
                            eachSubSes + "_magUFMask" + defaultExt,
                            "-erode", "3", "-peels", "2",
                            "magUF-" + eachSubSes + defaultExt])

            print str(eachSubSes) + " complete."
            with open("fslMaskB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")
            
         elif ( (runLoc == "") or (magOrig == "") ):
	    print str(eachSubSes) + " does not have the required magnitude scan for fslMaskB0!"
            with open("fslMaskB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            continue



def fslB0 (bidsTopLevelDir, bidsSubjectDict):
   
   print "This module is run after masks are created by the fslMaskB0 function."
   print "The masks from step 1 were edited by hand using AFNI's draw ROI tool."

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
                  blipRest = runLoc + '[0..24]' # Tested with, '[0]'
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

         if not ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (maskOrig == "") or (freqOrig == "") ):

	    restDsetCopyCmd = "3dTcat -prefix rest-" + eachSubSes + defaultExt + " " + blipRest
            os.system (restDsetCopyCmd)

            # Now compute B0 map in radians per sec and mask:
            print "Starting 3dROIstats and 3dcalc for " + str(eachSubSes)
            # Find the mode of the frequency distribution in the brain and
            # subtract this value from the field map. This is from potential vendor
            # offsets in F0.
            freqMode1 = Popen(["3dROIstats", "-nomeanout", "-quiet", "-mask", maskOrig, "-mode", freqOrig], stdout=PIPE)
            freqOut = freqMode1.communicate()[0]
            executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
                           "-expr", "(a-" + freqOut.strip() + ")*2.0*PI*step(b)", # Other analyses may use different scaling.
                           "-datum", "float", "-prefix", "fmapInRPSMasked-" + eachSubSes + defaultExt])

            executeAndWait(["3dcalc", "-a", blipRest, "-b", blipRev,
                            "-expr", "isnegative(a+b-1000)", "-datum", "float",
                            "-prefix", "epiNegMask_" + eachSubSes + defaultExt])

            unwarpTestDict = {}
            
            distDirections = ["x","x-","y","y-"]
            for eachDirection in distDirections:
               print "Starting fugue for " + str(eachSubSes)
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
               epiMaskMean.wait()
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

            # When fugue completes, gather inputs and execute afni_proc.py command.
            print "Starting afni_proc.py for " + str(eachSubSes)
            # This is to align the anatomical scan to the FSL output EPIs.
            dsetsInput = "epiFixed-" + eachSubSes + "_unwarpDir-" + bestUnwarpDir + defaultExt
            executeAndWait(["afni_proc.py", "-subj_id", eachSubSes,
                           "-copy_anat", anatOrig,
                           "-dsets", dsetsInput,
                           "-blocks", "align",
                           "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubSes],
                           "-Allineate_opts", "-warp", "shift_rotate", # to avoid changing shape of brain to match fixed or original
                                                                       # echo planar images.  Potentially apply to _ALL_ correction
                                                                       # schemes (blip-up/down included)
                           executeProcs])

            # send original T1, original rs-EPI, and fixed rs-EPI to registration step
            antsReg(anatOrig=anatOrig, blipRest=blipRest, dsetsInput=dsetsInput, eachSubSes=eachSubSes)

            # Move files created by fugue to subject's results folder.
            moveDestInput = eachSubSes + ".results/"
            moveFilesInput = "*?" + eachSubSes + "*"
            os.system ("mv -t " + moveDestInput + " " + moveFilesInput)

            print str(eachSubSes) + " complete."
            with open("fslB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1" + " bestUnwarpTest:" + str(bestUnwarpTest) + " bestUnwarpDir:" + str(bestUnwarpDir) + "\n")
	       fixFile.write(str(unwarpTestDict) + "\n")

         elif ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (maskOrig == "") or (freqOrig == "") ):
            print str(eachSubSes) + " does not have required scans and/or mask for fslB0!"
            with open("fslB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            continue



def antsReg(anatOrig, blipRest, dsetsInput, eachSubSes):

   print " "
   print "anatOrig:   " + str(anatOrig)
   print "blipRest:   " + str(blipRest)
   print "dsetsInput: " + str(dsetsInput)
   print "eachSubSes: " + str(eachSubSes)
   print " "

   """
   executeAndWait(["antsRegistration",
                   "-d", "3",
                   "-m", "mi'[" + anatOrig + "," + dsetsInput + ",1,32]'",
                   "-t", "Rigid'[1]'",
                   "-o", "'[fixedReg2T1_" + eachSubSes + "]'",
                   "-s", "1x1x1mm",
                   "-c", "'[50x50x50]'",
                   "-f", "2x2x2"])

   executeAndWait(["antsApplyTransforms",
                   "-d", "3",
                   "-e", "3",
                   "-i", dsetsInput,
                   "-r", anatOrig,
                   "-o", "fixedReg2T1" + eachSubSes + defaultExt,
                   "-t", "'[fixedReg2T1_" + eachSubSes + "0GenericAffine.mat,0]'"])
   """



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

   parser.add_option ("-m", "--mask",     action="store_true", dest="mask", default=False,
                                          help="DEFAULT, inputs are Reverse Blip Epi Scans")

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

   if (not options.software and not options.scan) and (options.mask):
      print "Starting B0 MASK CREATION for use in FSL's FUGUE"
      fslMaskB0 (options.dataDir, bidsDict)

   if (not options.software and not options.scan) and not (options.mask):
      print "Starting distortion correction using FSL's FUGUE"
      fslB0 (options.dataDir, bidsDict)


   
if __name__ == '__main__':
   sys.exit(main())

