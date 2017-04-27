#!/usr/bin/env python

import time, sys, os
import csv
import matplotlib.pyplot as mp
from   subprocess  import Popen, PIPE, STDOUT
from   optparse    import OptionParser
from   bidsFSUtils import bidsToolsFS



defaultExt = ".nii"

allSub = ["sub-%02d" % i for i in range(1,99)]
allSes = ["ses-%02d" % j for j in range(1,5)]
allData = []

for sub in allSub:
   for ses in allSes:
      subSes = str(sub) + "_" + str(ses)
      allData.append(subSes)
   
dataNeedingGiantMove = ["",""]
giantMoveDict = dict()
for subj in allData:
   if subj in dataNeedingGiantMove:
      giantMoveDict.update({subj: "-giant_move"})
   else:
      giantMoveDict.update({subj: ""})

# executeProcs = ""           # Generate proc scripts but DO NOT execute
executeProcs = "-execute"   # Generate proc scripts and execute



def afniBlipUpDown (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey     = "T1w"
   epiRunKey     = "dir-y_run"
   blipForRunKey = "dir-y_run"
   blipRevRunKey = "dir-y-_run"

   for eachSubject in bidsSubjectDict.keys():

      subjLoc = bidsTopLevelDir + eachSubject + "/"

      for eachSession in bidsSubjectDict[eachSubject].keys():

         eachSubSes = eachSubject + "_" + eachSession

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
                  epiDsets = 'blipRest-' + eachSubSes + defaultExt
                  blipFor = runLoc + '[0..24]'

               if blipForRunKey in runLoc:
                  # blipForHead = runLoc + '[0..14]'
                  blipForHead = runLoc + '[0]' # For data with low contrast in time series

               if blipRevRunKey in runLoc:
                  # blipRevHead = runLoc
                  blipRevHead = runLoc + '[0]' # For data with low contrast in time series

	 if not ( (runLoc == "") or (anatOrig == "") or (epiDsets == "") or (blipForHead == "") or (blipRevHead == "") ):

	    print "Starting afniBlipUpDown for " + str(eachSubSes)
            epiDsetCopyCmd = "3dTcat -prefix " + epiDsets + " " + blipFor
            os.system (epiDsetCopyCmd)

            executeAndWait(["afni_proc.py", "-subj_id", eachSubSes,
                            "-copy_anat", anatOrig,
                            "-dsets", epiDsets,
			    "-blocks", "blip",
                            # "-blocks", "align",
                            # "-align_opts_aea", "-cost", "lpc+ZZ", giantMoveDict[eachSubSes],
                            # "-Allineate_opts", "-warp", "shift_rotate",
                            "-blip_reverse_dset", blipRevHead,
                            "-blip_forward_dset", blipForHead,
                            executeProcs])

            # send original T1, original rs-EPI, and fixed rs-EPI to registration step
	    os.system("3dTcat -prefix epiFixed-" + str(eachSubSes) + str(defaultExt) + " " + str(eachSubSes) + ".results/pb01." + str(eachSubSes) + ".r01.blip+orig")
            dsetsInput = "epiFixed-" + eachSubSes + defaultExt
	    antsReg(anatOrig=anatOrig, blipRest=blipFor, dsetsInput=dsetsInput, eachSubSes=eachSubSes)

            # Make results folder and move files created to that folder.
            moveDestInput = eachSubSes + ".results/"
            # os.system ("mkdir " + moveDestInput)
            moveFilesInput = "*" + eachSubSes + "*"
            os.system ("mv --no-clobber " + moveFilesInput + " " + moveDestInput)

            print str(eachSubSes) + " complete."
            with open("afniBlipUpDownFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")

         elif ( (runLoc == "") or (anatOrig == "") or (epiDsets == "") or (blipForHead == "") or (blipRevHead == "") ):

	    print str(eachSubSes) + " does not have necessary scans for afniBlipUpDown!"
            with open("afniBlipUpDownFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
	    antsRegOut = float('NaN')
            with open("antsRegMetrics.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
            continue

   plotMI(figPrefix="afniBlip")



def afniB0 (bidsTopLevelDir, bidsSubjectDict, epiPhaseEncodeEchoSpacing=0.00031, epiPhaseFOV=192.0):
   # epi phase encode echo spacing unit is in seconds, FOV is in mm

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
            anatDsetCopyCmd = "3dTcat -prefix anat-" + eachSubSes + defaultExt + " " + anatOrig
	    os.system (anatDsetCopyCmd)

            # Find the mode of the frequency distribution in the brain and
            # subtract this value from the field map. This is from potential vendor
            # offsets in F0.
            freqMode1 = Popen(["3dROIstats", "-nomeanout", "-quiet", "-mask", maskOrig, "-mode", freqOrig], stdout=PIPE)
            freqOut = freqMode1.communicate()[0]
            print "Starting afniB0 for " + str(eachSubSes)
            executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
                           "-expr", "(a-" + freqOut.strip() + ")*" + str(epiPhaseEncodeEchoSpacing) + "*" + str(epiPhaseFOV) + "*b", # Other analyses may use different scaling.
                           "-datum", "float", "-prefix", "fmapInHz-" + eachSubSes + defaultExt])

            executeAndWait(["3dmerge", "-1blur_sigma", "9", "-doall", "-datum", "float",
	                    "-prefix", "fmapInHz-smoothed-" + eachSubSes + defaultExt,
                            "fmapInHz-" + eachSubSes + defaultExt])

            # Self warp field map to match epi distortions
            executeAndWait(["3dNwarpApply", "-warp", "AP:1.0:fmapInHz-smoothed-" + eachSubSes + defaultExt,
	                    "-prefix", "fmapInHz-smoothed-warped2epi-" + eachSubSes + defaultExt,
			    "-source", "fmapInHz-smoothed-" + eachSubSes + defaultExt])

            # Now apply warped field map to fix EPI
            executeAndWait(["3dNwarpApply", "-warp", "AP:-1.0:fmapInHz-smoothed-warped2epi-" + eachSubSes + defaultExt,
	                    "-prefix", "epiFixed-" + eachSubSes + defaultExt,
			    "-source", blipRest])

            # send original T1, original rs-EPI, and fixed rs-EPI to registration step
            dsetsInput = "epiFixed-" + eachSubSes + defaultExt
            antsReg(anatOrig=anatOrig, blipRest=blipRest, dsetsInput=dsetsInput, eachSubSes=eachSubSes)

            # Make results folder and move files created to that folder.
            moveDestInput = eachSubSes + ".results/"
            os.system ("mkdir " + moveDestInput)
            moveFilesInput = "*?" + eachSubSes + "*"
            os.system ("mv -t " + moveDestInput + " " + moveFilesInput)

            print str(eachSubSes) + " complete."
            with open("afniB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")

         elif not ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (freqOrig == "") ) and (maskOrig == ""):
            print str(eachSubSes) + " has required scans but DOES NOT have mask for afniB0!"
            with open("afniB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " missingMaskOnly\n")
            continue

         elif ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (maskOrig == "") or (freqOrig == "") ):
            print str(eachSubSes) + " does not have required scans and/or mask for afniB0!"
            with open("afniB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            antsRegOut = float('NaN')
            with open("antsRegMetrics.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
            continue

   plotMI(figPrefix="afniB0")



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
            anatDsetCopyCmd = "3dTcat -prefix anat-" + eachSubSes + defaultExt + " " + anatOrig
	    os.system (anatDsetCopyCmd)

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

            # send original T1, original rs-EPI, and fixed rs-EPI to registration step
	    if ( defaultExt == ".nii" ):
	       os.system("gzip -d epiFixed-" + eachSubSes + ".nii.gz")
            dsetsInput = "epiFixed-" + eachSubSes + defaultExt
            antsReg(anatOrig=anatOrig, blipRest=blipRest, dsetsInput=dsetsInput, eachSubSes=eachSubSes)

            # Make results folder and move files created to that folder.
            moveDestInput = eachSubSes + ".results/"
            os.system ("mkdir " + moveDestInput)
            moveFilesInput = "*?" + eachSubSes + "*"
            os.system ("mv -t " + moveDestInput + " " + moveFilesInput)

            print str(eachSubSes) + " complete."
            with open("fslBlipUpDownFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")

         elif ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (blipFor == "") or (blipRev == "") ):

            print str(eachSubSes) + " does not have all the required scans for fslBlipUpDown!"
            with open("fslBlipUpDownFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            antsRegOut = float('NaN')
            with open("antsRegMetrics.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
            continue

   plotMI(figPrefix="fslBlip")



def maskB0 (bidsTopLevelDir, bidsSubjectDict):
   
   print "This module creates masks to be used with the afniB0 and fslB0 functions."
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

            print "Starting maskB0 for " + str(eachSubSes)
            
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
            with open("maskB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")
            
         elif ( (runLoc == "") or (magOrig == "") ):
	    print str(eachSubSes) + " does not have the required magnitude scan for maskB0!"
            with open("maskB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            continue



def fslB0 (bidsTopLevelDir, bidsSubjectDict, epiPhaseEncodeEchoSpacing=0.00031):
   
   print "This module is run after masks are created by the maskB0 function."
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
            anatDsetCopyCmd = "3dTcat -prefix anat-" + eachSubSes + defaultExt + " " + anatOrig
	    os.system (anatDsetCopyCmd)

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
            
            distDirections = ["x","x-","y","y-"]
            for eachDirection in distDirections:
               print "Starting fugue in " + str(eachDirection) + " direction for " + str(eachSubSes)
               executeAndWait(["fugue", "-i", "rest-" + eachSubSes, "--dwell=" + str(epiPhaseEncodeEchoSpacing),
                              "--loadfmap=fmapInRPSMasked-" + eachSubSes + defaultExt,
                              "-u", "epiFixed-" + eachSubSes + "_unwarpDir-" + eachDirection, 
                              "--unwarpdir=" + eachDirection,
                              "--savefmap=" + "fmapSmooth3_9-" + eachSubSes,
                              "--smooth3=9"])

            print "Fugue completed for " + str(eachSubSes)

            # Complete list of subjects with all scans for fslB0
            unwarpKeys = ["",""]

            # Input unwarp directions based on best fixed epi by visual inspection
            unwarpVals = ["x-", "y-", "y-", "y-", "x",
	                  "x",  "y-", "x-", "x",  "y-", 
			  "y-", "y-", "y-", "x-", "y-",
			  "y-", "x-", "x",  "y-", "x-",
			  "y-", "y-", "y-", "y-", "x-"]

            unwarpDict = dict(zip(unwarpKeys, unwarpVals))

            if eachSubSes in unwarpDict.keys():
               finalUnwarpDir = unwarpDict[eachSubSes]
	       unwarpLog = "1"
	    else:
	       finalUnwarpDir = "x"
	       unwarpLog = "2"

            print "Starting antsReg for " + str(eachSubSes)
            # send original T1, original rs-EPI, and fixed rs-EPI to registration step
	    if ( defaultExt == ".nii" ):
	       os.system("gzip -d epiFixed-" + eachSubSes + "_unwarpDir-" + finalUnwarpDir + ".nii.gz")
            dsetsInput = "epiFixed-" + eachSubSes + "_unwarpDir-" + finalUnwarpDir + defaultExt
            antsReg(anatOrig=anatOrig, blipRest=blipRest, dsetsInput=dsetsInput, eachSubSes=eachSubSes)

            # Make results folder and move files created to that folder.
            moveDestInput = eachSubSes + ".results/"
            os.system ("mkdir " + moveDestInput)
            moveFilesInput = "*?" + eachSubSes + "*"
            os.system ("mv -t " + moveDestInput + " " + moveFilesInput)

            print str(eachSubSes) + " complete."
            with open("fslB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " " + str(unwarpLog) + " finalUnwarpDir:" + str(finalUnwarpDir) + "\n")

         elif not ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (freqOrig == "") ) and (maskOrig == ""):
            print str(eachSubSes) + " has required scans but DOES NOT have mask for fslB0!"
            with open("fslB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " missingMaskOnly\n")
            continue

         elif ( (runLoc == "") or (anatOrig == "") or (blipRest == "") or (maskOrig == "") or (freqOrig == "") ):
            print str(eachSubSes) + " does not have required scans and/or mask for fslB0!"
            with open("fslB0FixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            antsRegOut = float('NaN')
            with open("antsRegMetrics.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
            continue

   plotMI(figPrefix="fslB0")



def noCorr (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey         = "T1w"
   epiRunKey         = "dir-y_run"

   for eachSubject in bidsSubjectDict.keys():

      subjLoc = bidsTopLevelDir + eachSubject + "/"

      for eachSession in bidsSubjectDict[eachSubject].keys():

         if "NULL" in eachSession:
            sessLoc = subjLoc
         else:
            sessLoc = subjLoc + eachSession + "/"

         runLoc      = ""
         anatOrig    = ""
         blipRest    = ""

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():
            
            scanTypeLoc = sessLoc + eachScanType + "/"

            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:

               runLoc = scanTypeLoc + eachRun

               if t1wRunKey in runLoc:
                  anatOrig = runLoc

               if epiRunKey in runLoc:
                  blipRest = runLoc + '[0..24]'

         eachSubSes = eachSubject + "_" + eachSession

	 if not ( (runLoc == "") or (anatOrig == "") or (blipRest == "") ):

	    print "Starting noCorr for " + str(eachSubSes)
	    restDsetCopyCmd = "3dTcat -prefix rest-" + eachSubSes + defaultExt + " " + blipRest
            os.system (restDsetCopyCmd)
            anatDsetCopyCmd = "3dTcat -prefix anat-" + eachSubSes + defaultExt + " " + anatOrig
	    os.system (anatDsetCopyCmd)

            # send original T1, original rs-EPI, and fixed rs-EPI to registration step
            dsetsInput = "rest-" + eachSubSes + defaultExt
            antsReg(anatOrig=anatOrig, blipRest=blipRest, dsetsInput=dsetsInput, eachSubSes=eachSubSes)

            # Make results folder and move files created to that folder.
            moveDestInput = eachSubSes + ".results/"
            os.system ("mkdir " + moveDestInput)
            moveFilesInput = "*?" + eachSubSes + "*"
            os.system ("mv -t " + moveDestInput + " " + moveFilesInput)

            print str(eachSubSes) + " complete."
            with open("noCorrFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")

         elif ( (runLoc == "") or (anatOrig == "") or (blipRest == "") ):

	    print str(eachSubSes) + " does not have necessary scans for noCorr!"
            with open("noCorrFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            antsRegOut = float('NaN')
            with open("antsRegMetrics.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
            continue

   plotMI(figPrefix="noCorr")



def afniStandard (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey         = "T1w"
   epiRunKey         = "dir-y_run"

   for eachSubject in bidsSubjectDict.keys():

      subjLoc = bidsTopLevelDir + eachSubject + "/"

      for eachSession in bidsSubjectDict[eachSubject].keys():

         if "NULL" in eachSession:
            sessLoc = subjLoc
         else:
            sessLoc = subjLoc + eachSession + "/"

         runLoc      = ""
         anatOrig    = ""
         blipRest    = ""

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():
            
            scanTypeLoc = sessLoc + eachScanType + "/"

            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:

               runLoc = scanTypeLoc + eachRun

               if t1wRunKey in runLoc:
                  anatOrig = runLoc

               if epiRunKey in runLoc:
                  blipRest = runLoc + '[0..24]'

         eachSubSes = eachSubject + "_" + eachSession

	 if not ( (runLoc == "") or (anatOrig == "") or (blipRest == "") ):

	    print "Starting afniStandard for " + str(eachSubSes)
	    restDsetCopyCmd = "3dTcat -prefix rest-" + eachSubSes + defaultExt + " " + blipRest
            os.system (restDsetCopyCmd)
            anatDsetCopyCmd = "3dTcat -prefix anat-" + eachSubSes + defaultExt + " " + anatOrig
	    os.system (anatDsetCopyCmd)

	    print "Starting afni_proc.py for " + str(eachSubSes)
            executeAndWait(["afni_proc.py", "-subj_id", eachSubSes,
                            "-copy_anat", anatOrig,
                            "-dsets", epiDsets,
                            "-blocks", "align",
                            "-align_opts_aea",
			    "-cost", "lpc+ZZ",
			    giantMoveDict[eachSubSes],
			    "-volreg_align_e2a",
                            executeProcs])

            # Make results folder and move files created to that folder.
            # moveDestInput = eachSubSes + ".results/"
            # os.system ("mkdir " + moveDestInput)
            # moveFilesInput = "*?" + eachSubSes + "*"
            # os.system ("mv -t " + moveDestInput + " " + moveFilesInput)

            print str(eachSubSes) + " complete."
            with open("afniStandardFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")

         elif ( (runLoc == "") or (anatOrig == "") or (blipRest == "") ):

	    print str(eachSubSes) + " does not have necessary scans for afniStandard!"
            with open("afniStandardFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            antsRegOut = float('NaN')
            with open("antsRegMetrics.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
            continue

   plotMI(figPrefix="afniStandard")



def fslStandard (bidsTopLevelDir, bidsSubjectDict):

   t1wRunKey         = "T1w"
   epiRunKey         = "dir-y_run"

   for eachSubject in bidsSubjectDict.keys():

      subjLoc = bidsTopLevelDir + eachSubject + "/"

      for eachSession in bidsSubjectDict[eachSubject].keys():

         if "NULL" in eachSession:
            sessLoc = subjLoc
         else:
            sessLoc = subjLoc + eachSession + "/"

         runLoc      = ""
         anatOrig    = ""
         blipRest    = ""

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():
            
            scanTypeLoc = sessLoc + eachScanType + "/"

            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:

               runLoc = scanTypeLoc + eachRun

               if t1wRunKey in runLoc:
                  anatOrig = runLoc

               if epiRunKey in runLoc:
                  blipRest = runLoc + '[0..24]'

         eachSubSes = eachSubject + "_" + eachSession

	 if not ( (runLoc == "") or (anatOrig == "") or (blipRest == "") ):

	    print "Starting fslStandard for " + str(eachSubSes)
	    restDsetCopyCmd = "3dTcat -prefix rest-" + eachSubSes + defaultExt + " " + blipRest
            os.system (restDsetCopyCmd)
            anatDsetCopyCmd = "3dTcat -prefix anat-" + eachSubSes + defaultExt + " " + anatOrig
	    os.system (anatDsetCopyCmd)

            # Skull strip T1w to use in 'epi_reg' step
	    print "Starting fsl_anat for " + str(eachSubSes)
            executeAndWait(["fsl_anat", 
	                    "-i", anatOrig,
			    "-o", eachSubSes])
	    
	    # Register epi to anat
	    print "Starting epi_reg for " + str(eachSubSes)
	    executeAndWait(["epi_reg",
	                    "--epi=" + blipRest,
	                    "--t1=" + eachSubSes + ".anat/T1.nii.gz",
			    "--t1brain=" + eachSubSes + ".anat/T1_biascorr_brain.nii.gz",
			    "--out=epiFixed-" + eachSubSes])

            # Make results folder and move files created to that folder.
            moveDestInput = eachSubSes + ".results/"
            os.system ("mkdir " + moveDestInput)
            moveFilesInput = "*?" + eachSubSes + "*"
            os.system ("mv -t " + moveDestInput + " " + moveFilesInput)

            print str(eachSubSes) + " complete."
            with open("fslStandardFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 1\n")

         elif ( (runLoc == "") or (anatOrig == "") or (blipRest == "") ):

	    print str(eachSubSes) + " does not have necessary scans for fslStandard!"
            with open("fslStandardFixLog.txt", "a") as fixFile:
	       fixFile.write(str(eachSubSes) + " 0\n")
            antsRegOut = float('NaN')
            with open("antsRegMetrics.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
            continue

   plotMI(figPrefix="fslStandard")



def antsReg(anatOrig="", blipRest="", dsetsInput="", eachSubSes=""):

   antsReg1 = ("antsRegistration "
               "-d 3 "
	       "--float "
               "-o '[fixedReg2T1_" + str(eachSubSes) + "_,fixedReg2T1_" + str(eachSubSes) + ".nii.gz]' "
               "--use-histogram-matching 1 "
	       "-r '[" + str(anatOrig) + "," + str(dsetsInput) + ",0]' "
               "-t Rigid'[1]' "
	       "-m mi'[" + str(anatOrig) + "," + str(dsetsInput) + ",1,32]' "
               "-s 1x1x1mm "
               "-c '[50x50x50]' "
               "-f 2x2x2")

   # antsReg2 = ("antsApplyTransforms "
   #             "-d 3 "
   #             "-e 3 "
   #             "-i " + str(dsetsInput) + " "
   #             "-r " + str(anatOrig) + " "
   #             "-o fixedReg2T1_" + str(eachSubSes) + str(defaultExt) + " "
   #             "-t '[fixedReg2T1_" + str(eachSubSes) + "_0GenericAffine.mat,0]'")

   # Write ANTs commands to shell script and execute
   with open("antsReg_1_" + str(eachSubSes) + ".csh", "a") as antsRegFile1:
      antsRegFile1.write(antsReg1)
   print "Starting ANTs registration for " + str(eachSubSes)
   os.system(antsReg1)

   # with open("antsReg_2_" + str(eachSubSes) + ".csh", "a") as antsRegFile2:
   #    antsRegFile2.write(antsReg2)
   # print "Applying ANTs registration transformations for " + str(eachSubSes)
   # os.system(antsReg2)

   os.system("3dTstat -prefix meanTS_fixedReg2T1_" + str(eachSubSes) + str(defaultExt) + " " + "fixedReg2T1_" + str(eachSubSes) + ".nii.gz")

   # Collect and write registration metrics to file
   antsRegMetric = Popen(["ImageMath", "3", "out.nii.gz",
                          "Mattes", anatOrig, "meanTS_fixedReg2T1_" + str(eachSubSes) + ".nii.gz"], 
			  stdout=PIPE)
   antsRegOut = antsRegMetric.communicate()[0]
   if (antsRegOut == ""):
      antsRegOut = float('NaN')
   with open("antsRegMetrics.csv", "a") as antsRegCSV:
      writer = csv.writer(antsRegCSV)
      writer.writerow([eachSubSes, abs(float(antsRegOut))])

   # Need to check on what deformationField should be
   # executeAndWait(["CreateJacobianDeterminantImage", "3",
   #                 deformationField, "jac_" + eachSubSes + defaultExt])



def plotMI(figPrefix=""):

   antsRegDict = dict()

   finalCSV = str(figPrefix) + "_MI.csv"
   os.system("mv antsRegMetrics.csv " + str(finalCSV))

   with open(finalCSV) as f:
      antsRegData = csv.reader(f, delimiter=",")
      for row in antsRegData:
         antsRegDict[row[0]] = float(row[1])

   mp.bar(range(len(antsRegDict)), antsRegDict.values(), align="center")
   mp.xticks(range(len(antsRegDict)), antsRegDict.keys())
   mp.savefig(str(figPrefix) + "_MI.png")



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

   usage =       ("  %prog -d bidsDataTree [options]" )
   epilog =      ("For questions, suggestions, information, please contact Vinai Roopchansingh, Jerry French.")

   parser = OptionParser(usage=usage, description=description, epilog=epilog)

   parser.add_option ("-d", "--dataDir",  action="store",
                                          help="Directory with BIDS-formatted subject data folders")
   
   parser.add_option ("-a", "--afni",     action="store_true", dest="software", default=True,
                                          help="DEFAULT, runs distortion correction using AFNI")
   parser.add_option ("-f", "--fsl",      action="store_false", dest="software", default=True,
                                          help="Alternative to -a, runs distortion correction using FSL")
   
   parser.add_option ("-e", "--epiBlip",  action="store_true", dest="scan", default=True,
                                          help="DEFAULT, inputs are Reverse Blip Epi Scans")
   parser.add_option ("-b", "--B0Fmaps",  action="store_false", dest="scan", default=True,
                                          help="Alternative to -e, inputs are B0 Field Maps")

   parser.add_option ("-s", "--stand",    action="store_true", dest="stand", default=False,
                                          help="Option to run the standard procedure for disortion correction \
					        from either AFNI or FSL. Do not use with -e or -b options")

   parser.add_option ("-n", "--noCorr",   action="store_true", dest="corr", default=False,
                                          help="Option to register T1 to rsEPI without distortion correction")

   parser.add_option ("-m", "--mask",     action="store_true", dest="mask", default=False,
                                          help="Option to generate B0 mask needed for B0 corrections")

   parser.add_option ("--esp",            type="float", dest="esp", default=0.00031,
                                          help="Set EPI phase encode echo spacing in seconds \
					        +++ DEFAULT=0.00031")
   parser.add_option ("--fov",            type="float", dest="fov", default=192.0,
                                          help="Set EPI phase field of view in mm \
					        +++ DEFAULT=192.0")

   (options, args) = parser.parse_args()

   if ( str(options.dataDir)[-1] != "/" ):
      options.dataDir = str(options.dataDir) + "/"

   bidsDict = bidsToolsFS().buildBIDSDict(options.dataDir)

   if not (options.corr or options.mask or options.stand):

      if (options.software and options.scan):
         print "Starting distortion correction using AFNI's BLIP-UP/DOWN TOOLS"
         afniBlipUpDown (options.dataDir, bidsDict)

      if (options.software and not options.scan):
         print "Starting distortion correction using AFNI's B0 TOOLS"
         afniB0 (options.dataDir, bidsDict, options.esp, options.fov)

      if (not options.software and options.scan):
         print "Starting distortion correction using FSL's TOPUP"
         fslBlipUpDown (options.dataDir, bidsDict)

      if (not options.software and not options.scan):
         print "Starting distortion correction using FSL's FUGUE"
         fslB0 (options.dataDir, bidsDict, options.esp)

   if (options.stand and options.software):
      print "Starting distortion correction using AFNI's Standard Procedure"
      afniStandard (options.dataDir, bidsDict)

   if (options.stand and not options.software):
      print "Starting distortion correction using FSL's Standard Procedure"
      fslStandard (options.dataDir, bidsDict)

   if (options.mask):
      print "Starting B0 MASK CREATION for use in B0 corrections"
      maskB0 (options.dataDir, bidsDict)

   if (options.corr):
      print "Starting ANTs REGISTRATION without distortion corrections"
      noCorr (options.dataDir, bidsDict)

   
if __name__ == '__main__':
   sys.exit(main())

