#!/usr/bin/env python

import time, sys, os, glob
import csv
import pandas as pd
import matplotlib.pyplot as plt
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

# List of subjects with poor initial alignment of epi and anat
dataNeedingGiantMove = ["sub-09_ses-03", "sub-12_ses-02", "sub-14_ses-02", "sub-18_ses-04", "sub-25_ses-01",
                        "sub-31_ses-01", "sub-32_ses-02", "sub-36_ses-01", "sub-37_ses-02"]

forwardReverseBlipsInDifferentPositions = ["sub-09_ses-03", "sub-14_ses-02", "sub-22_ses-01", "sub-34_ses-01",
                                           "sub-37_ses-02"]

# checkAllUnwarpDirs = True will align all unwarp directions in afniB0 and fslB0 functions using ANTs
# checkAllUnwarpDirs = False will only align unwarp directions defined in afniUnwarpVals and fslUnwarpVals
checkAllUnwarpDirs = False

# Complete list of subjects with all scans for B0 corrections
unwarpKeys = ["sub-07_ses-04", "sub-14_ses-02", "sub-22_ses-02", "sub-22_ses-03", "sub-24_ses-01",
              "sub-26_ses-01", "sub-27_ses-01", "sub-32_ses-01", "sub-33_ses-01", "sub-34_ses-01",
              "sub-39_ses-02"]
# Input unwarp directions based on best fixed epi by visual inspection
# after fslB0 corrections using all 4 directions
fslUnwarpVals = ["y-", "y-", "y-", "y-", "y-",
                 "y-", "y-", "y-", "y-", "y-",
                 "y-"]
fslUnwarpDict = dict(zip(unwarpKeys, fslUnwarpVals))

afniUnwarpVals = ["AP_1.0", "AP_1.0", "AP_1.0", "AP_1.0", "AP_1.0",
                  "AP_1.0", "AP_1.0", "AP_1.0", "AP_1.0", "AP_1.0",
                  "AP_1.0"]
afniUnwarpDict = dict(zip(unwarpKeys, afniUnwarpVals))

# Dict of subjects acquired in de-cub position, to specify to topup to get phase encode axis right
acqParams        = "acqParams.txt" # name of the text file with data used by topup for blip up/down corrections
subjectsDecubbed = {"sub-02_ses-01" : "-1 0 0 0.02976\n1 0 0 0.02976",
                    "sub-11_ses-02" : "-1 0 0 0.02976\n1 0 0 0.02976",
                    "sub-13_ses-03" : "-1 0 0 0.02976\n1 0 0 0.02976",
                    "sub-15_ses-02" : "-1 0 0 0.02976\n1 0 0 0.02976",
                    "sub-28_ses-01" : "-1 0 0 0.02976\n1 0 0 0.02976",
                    "sub-28_ses-02" : "-1 0 0 0.02976\n1 0 0 0.02976",
                    "sub-29_ses-01" : "-1 0 0 0.02976\n1 0 0 0.02976",
                    "sub-38_ses-01" : "-1 0 0 0.02976\n1 0 0 0.02976",
                    "default"       : "0 -1 0 0.02976\n0 1 0 0.02976"
                   }






def getScans (bidsTopLevelDir, bidsSubjectDict, corrMethod, epiPhaseEncodeEchoSpacing=0.00031, epiPhaseFOV=192.0):

   t1wRunKey         = "T1w."
   t1wSSRunKey       = "T1w_skull_stripped" # generated via: 3dSkullStrip -use_skull -surface_coil -input $t1wRunKey -prefix $t1wSSRunKey.nii
   epiRestRunKey     = "dir-y_run"
   epiBlipForRunKey  = "dir-y_run"
   epiBlipRevRunKey  = "dir-y-_run"
   magRunKey         = "magnitude"
   freqRunKey        = "frequency"
   maskRunKey        = "magUFMask.nii"

   for eachSubject in bidsSubjectDict.keys():
      subjLoc = bidsTopLevelDir + eachSubject + "/"
      for eachSession in bidsSubjectDict[eachSubject].keys():
         eachSubSes = eachSubject + "_" + eachSession

         if "NULL" in eachSession:
            sessLoc = subjLoc
         else:
            sessLoc = subjLoc + eachSession + "/"

         runLoc          = ""
         anatOrig        = ""
         anatSSOrig      = ""
         epiRestOrig     = ""
         epiBlipForOrig  = ""
         epiBlipRevOrig  = ""
         magOrig         = ""
         freqOrig        = ""
         maskOrig        = ""
         logNum          = False

         for eachScanType in bidsSubjectDict[eachSubject][eachSession].keys():
            scanTypeLoc = sessLoc + eachScanType + "/"
            for eachRun in bidsSubjectDict[eachSubject][eachSession][eachScanType]:
               runLoc = scanTypeLoc + eachRun

               if t1wRunKey in runLoc:
                  anatOrig = runLoc
               if t1wSSRunKey in runLoc:
                  anatSSOrig = runLoc
               if epiRestRunKey in runLoc:
                  epiRestOrig = runLoc + '[0..14]'
               if epiBlipForRunKey in runLoc:
                  # epiBlipForOrig = runLoc + '[0..14]'
                  epiBlipForOrig = runLoc + '[0]' # For data with low contrast in time series
               if epiBlipRevRunKey in runLoc:
                  # epiBlipRevOrig = runLoc + '[0..14]'
                  epiBlipRevOrig = runLoc + '[0]' # For data with low contrast in time series
               if magRunKey in runLoc:
                  magOrig = runLoc
               if freqRunKey in runLoc:
                  freqOrig = runLoc
               if maskRunKey in runLoc:
                  maskOrig = runLoc

         # Perform distortion correction method 'corrMethod' if session contains the necessary files

         if (corrMethod in ('ae', 'fe', 'ab', 'fb', 'as', 'fs', 'nc')):
            if ((corrMethod in ('ae', 'fe')) and (eachSubSes not in forwardReverseBlipsInDifferentPositions)):
               if not ((runLoc == "") or (anatOrig == "") or (anatSSOrig == "") or (epiRestOrig == "") or (epiBlipForOrig == "") or (epiBlipRevOrig == "")):
                  copyOrigs (eachSubSes=eachSubSes, anatOrig=anatOrig, anatSSOrig=anatSSOrig, epiRestOrig=epiRestOrig)
                  if (corrMethod == "ae"):
                     afniBlipUpDown(eachSubSes=eachSubSes, epiBlipForOrig=epiBlipForOrig, epiBlipRevOrig=epiBlipRevOrig)
                  else:
                     fslBlipUpDown(eachSubSes=eachSubSes, epiBlipForOrig=epiBlipForOrig, epiBlipRevOrig=epiBlipRevOrig)
                  logNum = True
               else:
                  logNum = False

            if ((corrMethod in ('ab', 'fb')) and (eachSubSes in unwarpKeys)):
               if (maskOrig == ""):
                  print str(eachSubSes) + " requires a mask!"
               if not ( (runLoc == "") or (anatOrig == "") or (anatSSOrig == "") or (epiRestOrig == "") or (magOrig == "") or (freqOrig == "") or (maskOrig == "") ):
                  copyOrigs (eachSubSes=eachSubSes, anatOrig=anatOrig, anatSSOrig=anatSSOrig, epiRestOrig=epiRestOrig)
                  if (corrMethod == "ab"):
                     afniB0(eachSubSes=eachSubSes, magOrig=magOrig, freqOrig=freqOrig, maskOrig=maskOrig, epiPhaseEncodeEchoSpacing=epiPhaseEncodeEchoSpacing, epiPhaseFOV=epiPhaseFOV)
                  else:
                     fslB0(eachSubSes=eachSubSes, magOrig=magOrig, freqOrig=freqOrig, maskOrig=maskOrig, epiPhaseEncodeEchoSpacing=epiPhaseEncodeEchoSpacing, epiPhaseFOV=epiPhaseFOV)
                  logNum = True
               else:
                  logNum = False

            if (corrMethod in ('as', 'fs', 'nc')):
               if not ((runLoc == "") or (anatOrig == "") or (anatSSOrig == "") or (epiRestOrig == "")):
                  copyOrigs (eachSubSes=eachSubSes, anatOrig=anatOrig, anatSSOrig=anatSSOrig, epiRestOrig=epiRestOrig)
                  if (corrMethod == "as"):
                     afniStandard(eachSubSes=eachSubSes)
                  elif (corrMethod == "fs"):
                     fslStandard(eachSubSes=eachSubSes)
                  else:
                     noCorr(eachSubSes=eachSubSes)
                  logNum = True
               else:
                  logNum = False

            if (logNum): # if performing a correction, then do registration, make results directory, and move results there
               antsReg(eachSubSes=eachSubSes, corrMethod=corrMethod)

               if not os.path.exists(eachSubSes + ".results/"):
                  os.system ("mkdir " + eachSubSes + ".results/")
               os.system ("mv --no-clobber *" + eachSubSes + "* " + eachSubSes + ".results/")
               if (corrMethod in ('fe')):
                  os.system ("mv --no-clobber " + acqParams + "  " + eachSubSes + ".results/")

         else: # corrMethod not in ('ae', 'fe', 'ab', 'fb', 'as', 'fs', 'nc'), i.e. (corrMethod == "m") - masking routine
            if not ( (runLoc == "") or (magOrig == "") ):
               maskB0 (eachSubSes=eachSubSes, magOrig=magOrig)
            else:
               logNum = False
               continue

         fixLog(eachSubSes=eachSubSes, corrMethod=corrMethod, logNum=logNum)

   # When testing for the best unwarp direction (ie. checkAllUnwarpDirs = True) with B0 functions.
   if (checkAllUnwarpDirs) and (corrMethod in ('ab', 'fb') and (eachSubSes in unwarpKeys)):
      df = pd.concat([pd.read_csv(f, index_col='sub') for f in glob.glob('*.csv')], axis=1, join='outer').sort()

      # For each successful session, plot the MI for all unwarp directions for each session.
      df[df.columns].plot(kind='bar', grid=False)
      plt.legend(df.columns, labels=df.columns, bbox_to_anchor=(1.05, 1), loc=2, fontsize='small', borderaxespad=0.)
      plt.ylim(df.values.min()-0.01, df.values.max()+0.01)
      plt.savefig(str(corrMethod) + "_unwarpPlot.png", bbox_inches='tight')

      # Next, record the best unwarp direction for each session to a text file.
      # This info can then be used to build the global 'afniUnwarpVals' or 'fslUnwarpVals' lists (see above).
      with open("bestUnwarpDirs.txt", "a") as bestUnwarpFile:
         bestUnwarpFile.write(str(df.T.idxmax(axis=0)))



def copyOrigs (eachSubSes="", anatOrig="", anatSSOrig="", epiRestOrig=""):

   os.system ("3dTcat      -prefix anat-"      + str(eachSubSes) + str(defaultExt) + " " + str(anatOrig))
   os.system ("3dTcat      -prefix epiRest-"   + str(eachSubSes) + str(defaultExt) + " " + str(epiRestOrig))
   # Also include mask generation from skull-stripped version of anatomical data set.
   os.system ("3dAutomask  -prefix brain-mask"                   + str(defaultExt) + " " + str(anatSSOrig))
   os.system ("3dresample  -prefix anat-mask-" + str(eachSubSes) + str(defaultExt) + " " + 
                          "-master " + "anat-" + str(eachSubSes) + str(defaultExt) + " " + " -input brain-mask.nii")
   os.system ("rm          -f      brain-mask"                   + str(defaultExt))



def fixLog (eachSubSes="", corrMethod="", logNum=""):

   if (logNum):
      print "Distortion correction completed for " + str(eachSubSes)
      with open(str(corrMethod) + "FixLog.txt", "a") as fixFile:
         fixFile.write(str(eachSubSes) + " 1\n")

   else:
      print str(eachSubSes) + " does not have necessary scans for the selected correction method (" + str(corrMethod) + ")!"
      with open(str(corrMethod) + "FixLog.txt", "a") as fixFile:
         fixFile.write(str(eachSubSes) + " 0\n")

      if not ( (checkAllUnwarpDirs) and (corrMethod in ('ab', 'fb')) ):
         with open(str(corrMethod) + "_MI.csv", "a") as antsRegCSV:
            writer = csv.writer(antsRegCSV)
            writer.writerow([eachSubSes, float('NaN')])



###### AFNI BLIP OPTION ######
###### EXPERIMENTAL: AFNI BLIP-UP/DOWN CORRECTION ######

def afniBlipUpDown (eachSubSes="", epiBlipForOrig="", epiBlipRevOrig=""):
   print "Starting afniBlipUpDown for " + str(eachSubSes)

   executeAndWait(["afni_proc.py", "-subj_id", eachSubSes,
                   "-dsets", "epiRest-" + eachSubSes + defaultExt,
                   "-blocks", "blip",
                   "-blip_reverse_dset", epiBlipRevOrig,
                   "-blip_forward_dset", epiBlipForOrig,
                   "-execute"])

   # send original T1, original rs-EPI, and fixed rs-EPI to registration step
   os.system("3dTcat -prefix epiFixed-" + str(eachSubSes) + str(defaultExt) + " " + str(eachSubSes) + ".results/pb01." + str(eachSubSes) + ".r01.blip+orig")



###### AFNI B0 OPTION ######
###### EXPERIMENTAL: AFNI B0 FIELD MAP CORRECTION ######

def afniB0 (eachSubSes="", magOrig="", freqOrig="", maskOrig="", epiPhaseEncodeEchoSpacing=0.00031, epiPhaseFOV=192.0,
            bandwidthHzAcquistionReadout=250000.0, bandwidthHzPerPixelReadout=2000.0, nPixelsReadout=96, nPixelsPhase=96):
   # epi phase encode echo spacing unit is in seconds, FOV is in mm
   print "Starting afniB0 for " + str(eachSubSes)

   # Find the mode of the frequency distribution in the brain and
   # subtract this value from the field map. This is from potential
   # vendor offsets in F0.
   freqMode1 = Popen(["3dROIstats", "-nomeanout", "-quiet", "-mask", maskOrig, "-mode", freqOrig], stdout=PIPE)
   freqOut = freqMode1.communicate()[0]

   sampleTime = 1.0 / bandwidthHzAcquistionReadout # or: 1.0 / (bandwidthHzPerPixelReadout * nPixelsReadout)
   frequencyShiftScaling = epiPhaseEncodeEchoSpacing / sampleTime
   bandwidthHzPerPixelReadout = bandwidthHzAcquistionReadout / nPixelsReadout
   perPixelFrequencyShiftPhase = bandwidthHzPerPixelReadout / frequencyShiftScaling # or: bandwidthHzAcquistionReadout / (nPixelsReadout * frequencyShiftScaling)

   executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
                  "-expr", "(a-" + freqOut.strip() + ")/" + str(perPixelFrequencyShiftPhase) + "*" + str(epiPhaseFOV) + "*b/" + str(nPixelsPhase), # Other analyses may use different scaling.
                  "-datum", "float",
                  "-prefix", "fmapInHz-" + eachSubSes + defaultExt])

   # Use the '-1blur_sigma 9' option to match the '--smooth3=9' option in FSL's fugue
   executeAndWait(["3dmerge", "-1blur_sigma", "9", "-doall", "-datum", "float",
                   "-prefix", "fmapInHz-smoothed-" + eachSubSes + defaultExt,
                   "fmapInHz-" + eachSubSes + defaultExt])

   distDirections = ["RL", "AP"]
   distDirectionsSigns = [-1.0, 1.0]

   for distDir in distDirections:
      for dirSign in distDirectionsSigns:
         if (checkAllUnwarpDirs or (str(distDir + "_" + str(dirSign)) == afniUnwarpDict[eachSubSes])):
            print "Starting afni 3dNwarpApply in " + str(distDir) + "_" + str(dirSign) + " direction for " + str(eachSubSes)
            # Self warp field map to match epi distortions
            executeAndWait(["3dNwarpApply", "-warp", distDir + ":" + str(dirSign * 1.0) + ":fmapInHz-smoothed-" + eachSubSes + defaultExt,
                            "-prefix", "fmapInHz-smoothed-warped2epi_" + distDir + "_" + str(dirSign * -1.0) + "_" + eachSubSes + defaultExt,
                            "-source", "fmapInHz-smoothed-" + eachSubSes + defaultExt])

            # Now apply warped field map to fix EPI
            executeAndWait(["3dNwarpApply", "-warp", distDir + ":" + str(dirSign * -1.0) + ":fmapInHz-smoothed-warped2epi_" + distDir + "_" + str(dirSign * -1.0) + "_" + eachSubSes + defaultExt,
                            "-prefix", "epiFixed-" + distDir + "_" + str(dirSign *  1.0) + "_" + eachSubSes + defaultExt,
                            "-source", "epiRest-" + eachSubSes + defaultExt])

   if eachSubSes in afniUnwarpDict.keys():
      finalUnwarpDir = afniUnwarpDict[eachSubSes]
   else:
      finalUnwarpDir = "AP_-1.0"

   # send original T1, original rs-EPI, and fixed rs-EPI to registration step
   os.system ("3dTcat -prefix epiFixed-" + eachSubSes + defaultExt + " epiFixed-" + finalUnwarpDir + "_" + eachSubSes + defaultExt)



###### FSL BLIP OPTION (TOPUP) ######
###### EXPERIMENTAL: FSL BLIP-UP/DOWN CORRECTION ######

def fslBlipUpDown (eachSubSes="", epiBlipForOrig="", epiBlipRevOrig=""):
   print "Starting fslBlipUpDown for " + str(eachSubSes)

   if not os.path.isfile(acqParams):
      print "*** distortionFix.py could not locate the acquisition parameters text file, which"
      print "*** is currently defined as: " + str(acqParams) + " in the fslBlipUpDown function."
      print "*** Generating a sample text file based on the PDN data to continue..."
      with open("acqParams.txt", "a") as paramFile:
         if (eachSubSes in subjectsDecubbed.keys()):
            print ("Using ***SPECIAL*** phase encoding direction set " + subjectsDecubbed[eachSubSes] + " for subject " + eachSubSes)
            paramFile.write(subjectsDecubbed[eachSubSes])
         else:
            print ("Using ** default ** phase encoding direction parameters for subject " + eachSubSes)
            paramFile.write(subjectsDecubbed["default"])
      print "*** Please refer to topup documentation to set the proper parameters for your data."

   os.system ("3dTcat -prefix bothBlips-" + str(eachSubSes) + str(defaultExt) + " " + str(epiBlipRevOrig) + " " + str(epiBlipForOrig))

   print "Step 1: Running topup on " + str(eachSubSes)
   executeAndWait(["topup", "--imain=bothBlips-" + eachSubSes, 
                   "--datain=" + acqParams, 
                   "--config=b02b0.cnf",
                   "--out=warpField-" + eachSubSes])

   print "Step 2: Running applytopup on " + str(eachSubSes)
   executeAndWait(["applytopup", "--imain=epiRest-" + eachSubSes, 
                   "--inindex=2",
                   "--datain=" + acqParams, 
                   "--topup=warpField-" + eachSubSes,
                   "--interp=spline",
                   "--out=epiFixed-" + eachSubSes,
                   "--method=jac"])

   # send original T1, original rs-EPI, and fixed rs-EPI to registration step
   if ( defaultExt == ".nii" ):
      os.system("gzip -d epiFixed-" + eachSubSes + ".nii.gz")



###### FSL B0 OPTION (FUGUE) ######
###### EXPERIMENTAL: FSL B0 FIELD MAP CORRECTION ######

def fslB0 (eachSubSes="", magOrig="", freqOrig="", maskOrig="", epiPhaseEncodeEchoSpacing=0.00031, epiPhaseFOV=192.0):
   # This module is run after masks are created by the maskB0 function.
   # The masks from step 1 were edited by hand using AFNI's draw ROI tool.
   print "Starting fslB0 for " + str(eachSubSes)

   # Now compute B0 map in radians per sec and mask
   # Find the mode of the frequency distribution in the brain and
   # subtract this value from the field map. This is from potential vendor
   # offsets in F0.
   freqMode1 = Popen(["3dROIstats", "-nomeanout", "-quiet", "-mask", maskOrig, "-mode", freqOrig], stdout=PIPE)
   freqOut = freqMode1.communicate()[0]
   executeAndWait(["3dcalc", "-a", freqOrig, "-b", maskOrig,
                   "-expr", "(a-" + freqOut.strip() + ")*2.0*PI*step(b)", # Other analyses may use different scaling.
                   "-datum", "float",
                   "-prefix", "fmapInRPSMasked-" + eachSubSes + defaultExt])

   distDirections = ["x", "x-", "y", "y-"]
   for eachDirection in distDirections:
      if (checkAllUnwarpDirs or (eachDirection == fslUnwarpDict[eachSubSes])):
         print "Starting fugue in " + str(eachDirection) + " direction for " + str(eachSubSes)
         executeAndWait(["fugue", "-i", "epiRest-" + eachSubSes,
                         "--dwell=" + str(epiPhaseEncodeEchoSpacing),
                         "--loadfmap=fmapInRPSMasked-" + eachSubSes + defaultExt,
                         "-u", "epiFixed-" + eachDirection + "_" + eachSubSes,
                         "--unwarpdir=" + eachDirection,
                         "--savefmap=" + "fmapSmooth3_9-" + eachSubSes,
                         "--smooth3=9"])

   if eachSubSes in fslUnwarpDict.keys():
      finalUnwarpDir = fslUnwarpDict[eachSubSes]
   else:
      finalUnwarpDir = "x"

   # send original T1, original rs-EPI, and fixed rs-EPI to registration step
   if ( defaultExt == ".nii" ):
      os.system("gzip -d epiFixed-*.nii.gz")
   os.system ("3dTcat -prefix epiFixed-" + eachSubSes + defaultExt + " epiFixed-" + finalUnwarpDir + "_" + eachSubSes + defaultExt)





###### NO CORRECTION ######
###### BASELINE: REGISTRATION WITHOUT CORRECTION ######

def noCorr (eachSubSes=""):
   print "Starting noCorr for " + str(eachSubSes)

   os.system ("3dTcat -prefix epiFixed-" + eachSubSes + defaultExt + " epiRest-" + eachSubSes + defaultExt)





###### ANTS REGISTRATION ######
###### RIGID TRANSFORMATION OF CORRECTED EPI TO ANAT ######
###### USED FOR ALL THE ABOVE CORRECTION TECHNIQUES ######

def antsReg(eachSubSes="", corrMethod=""):
   print "Starting antsReg for " + str(eachSubSes)

   testUnwarps = []

   if (checkAllUnwarpDirs):
      if (corrMethod == 'fb'):
         testUnwarps = ["x", "x-", "y", "y-"]
      elif (corrMethod == 'ab'):
         testUnwarps = ["AP_1.0", "AP_-1.0", "RL_1.0", "RL_-1.0"]
      else:
         testUnwarps = [""]
   else:
      testUnwarps = [""]

   for testUnwarp in testUnwarps:

      if (checkAllUnwarpDirs) and ( corrMethod in ('ab', 'fb') ):
         subjDirID = str(testUnwarp) + "_" + str(eachSubSes)
      else:
         subjDirID = str(eachSubSes)

      anatDset = "anat-" +      str(eachSubSes) + str(defaultExt)
      anatMask = "anat-mask-" + str(eachSubSes) + str(defaultExt)

      if corrMethod in ('ae', 'ab', 'fe', 'fb', 'nc'):

         # Instead of volume registering and interpolating, just interpolate EPI data set to anatomical data set grid.
         regriddedData = "epiFixed-Interpolated-" + subjDirID + ".nii"

         resampleEPI2Anat = ("3dresample -rmode Cu   "
                             " -master " + anatDset +
                             " -input epiFixed-" + subjDirID + ".nii   "
                             " -prefix " + regriddedData)

         with open("epiResample_" + subjDirID + ".csh", "a") as epiResampleFile:
            epiResampleFile.write(resampleEPI2Anat)
         os.system(resampleEPI2Anat)

         # metric4Registration = "--metric MI'[anat-" + eachSubSes + ".nii,epiFixed-" + subjDirID + ".nii,1,32,Regular,0.25]' "
         metric4Registration = "--metric CC'[" + anatDset + ",epiFixed-" + subjDirID + ".nii,1,3]' "
         basicRegistration   = ("antsRegistration   -d 3   --float   --transform Rigid'[0.1]' "  +  metric4Registration  +
                                "--convergence '[1000x500x250x100]'  --shrink-factors 8x4x2x1   --smoothing-sigmas 1.5x1.5x1.5x0vox   ")

         if eachSubSes in dataNeedingGiantMove:
            print "Adding histogram matching and initial moving transform for " + str(subjDirID)
            # antsRegistration adapted from https://github.com/stnava/ANTs/wiki/Anatomy-of-an-antsRegistration-call
            regOutput = "fixedReg2T1_" + subjDirID
            antsReg1 = (basicRegistration +
                        "--output '[" + regOutput + "_," + regOutput + ".nii]'   "
                        "--use-histogram-matching 0   "
                        "--initial-moving-transform '[" + anatDset + ",epiFixed-" + subjDirID + ".nii,0]' ")

            # Write ANTs commands to shell script and execute
            with open("antsReg_1_" + str(eachSubSes) + ".csh", "a") as antsRegFile1:
               antsRegFile1.write(antsReg1)
            os.system(antsReg1)

            dataSetToMatchAgainst = regOutput + ".nii"

         else:
            dataSetToMatchAgainst = regriddedData

            print "No histogram matching and initial moving transform needed for " + str(subjDirID)

      # begin calculating alignment metric, initially MI (mutual information), then Pearson Correlation
      # metric4Matching = "Mattes"
      metric4Matching = "PearsonCorrelation"
      print "Gathering and documenting matching statistics, here: " + metric4Matching + ", for " + str(eachSubSes)
      antsRegMetric = Popen(["ImageMath", "3", "out.nii.gz",
                             metric4Matching, anatDset, dataSetToMatchAgainst, anatMask], 
                             stdout=PIPE)
      antsRegOut = antsRegMetric.communicate()[0]
      if (antsRegOut == ""):
         antsRegOut = float('NaN')

      # write csv files with naming conventions specific to the 
      # correction option and 'checkAllUnwarpDirs' setting

      if (checkAllUnwarpDirs) and ( corrMethod in ('ab', 'fb') ):
         if os.path.exists(str(corrMethod) + "_" + str(testUnwarp) + "_MI.csv"):
            with open(str(corrMethod) + "_" + str(testUnwarp) + "_MI.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
         else:
            with open(str(corrMethod) + "_" + str(testUnwarp) + "_MI.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow(['sub', str(corrMethod) + "_" + str(testUnwarp)])
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
      else:
         if os.path.exists(str(corrMethod) + "_MI.csv"):
            with open(str(corrMethod) + "_MI.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow([eachSubSes, abs(float(antsRegOut))])
         else:
            with open(str(corrMethod) + "_MI.csv", "a") as antsRegCSV:
               writer = csv.writer(antsRegCSV)
               writer.writerow(['sub', str(corrMethod)])
               writer.writerow([eachSubSes, abs(float(antsRegOut))])





###### AFNI VOLREG ######
###### BASELINE: AFNI STANDARD DISTORTION CORRECTION PROCEDURE ######

def afniStandard (eachSubSes=""):
   print "Starting afniStandard for " + str(eachSubSes)

   if eachSubSes in dataNeedingGiantMove:
      executeAndWait(["align_epi_anat.py", 
                      "-anat", "anat-" + eachSubSes + defaultExt,
                      "-epi", "epiRest-" + eachSubSes + defaultExt,
                      "-epi2anat",
                      "-epi_base", "1",
                      "-volreg_method", "3dAllineate",
                      "-giant_move",
                      "-tshift", "off"])
   else:
      executeAndWait(["align_epi_anat.py", 
                      "-anat", "anat-" + eachSubSes + defaultExt,
                      "-epi", "epiRest-" + eachSubSes + defaultExt,
                      "-epi2anat",
                      "-epi_base", "1",
                      "-volreg_method", "3dAllineate",
                      "-tshift", "off"])

   os.system("3dTcat -prefix fixedReg2T1_" + str(eachSubSes) + str(defaultExt) + " epiRest-" + str(eachSubSes) + "_al+orig")





###### FSL EPI_REG ######
###### BASELINE: FSL STANDARD DISTORTION CORRECTION PROCEDURE ######

def fslStandard (eachSubSes=""):
   print "Starting fslStandard for " + str(eachSubSes)

   # Skull strip T1w to use in 'epi_reg' step
   print "Starting fsl_anat for " + str(eachSubSes)
   executeAndWait(["fsl_anat", 
                   "-i", "anat-" + eachSubSes + defaultExt,
                   "-o", eachSubSes])

   # Register epi to anat
   print "Starting epi_reg for " + str(eachSubSes)
   executeAndWait(["epi_reg",
                   "--epi=epiRest-" + str(eachSubSes) + str(defaultExt),
                   "--t1=" + eachSubSes + ".anat/T1.nii.gz",
                   "--t1brain=" + eachSubSes + ".anat/T1_biascorr_brain.nii.gz",
                   "--out=fixedReg2T1_" + eachSubSes])

   os.system("gzip -d fixedReg2T1_*.nii.gz")





###### CREATE MASK ######
###### REQUIREMENT FOR ALL B0 CORRECTIONS ABOVE ######

def maskB0 (eachSubSes="", magOrig=""):
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
                   "-erode", "1", "-peels", "2",
                   "magUF-" + eachSubSes + defaultExt])





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

   if (options.mask):
      corrMethod = "m"
      print "Starting B0 MASK CREATION for use in B0 corrections (-" + str(corrMethod) + ")"
   elif (options.corr):
      corrMethod = "nc"
      print "Starting ANTs REGISTRATION without distortion corrections (-" + str(corrMethod) + ")"
   else:
      if (options.software):
         if (options.scan) and (options.stand):
            corrMethod = "as"
            print "Starting distortion correction using AFNI's Standard Procedure (-" + str(corrMethod) + ")"
         elif (options.scan):
            corrMethod = "ae"
            print "Starting distortion correction using AFNI's BLIP-UP/DOWN TOOLS (-" + str(corrMethod) + ")"
         else:
            corrMethod = "ab"
            print "Starting distortion correction using AFNI's B0 TOOLS (-" + str(corrMethod) + ")"
      else:
         if (options.scan) and (options.stand):
            corrMethod = "fs"
            print "Starting distortion correction using FSL's Standard Procedure (-" + str(corrMethod) + ")"
         elif (options.scan):
            corrMethod = "fe"
            print "Starting distortion correction using FSL's TOPUP (-" + str(corrMethod) + ")"
         else:
            corrMethod = "fb"
            print "Starting distortion correction using FSL's FUGUE (-" + str(corrMethod) + ")"

   getScans (options.dataDir, bidsDict, corrMethod, options.esp, options.fov)




   
if __name__ == '__main__':
   sys.exit(main())


