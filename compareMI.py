#!/usr/bin/env python

import time, sys, os
import csv
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from   optparse    import OptionParser



def buildDataDict():

   nc = "noCorr_MI.csv"
   ae = "afniBlip_MI.csv"
   ab = "afniB0_MI.csv"
   fe = "fslBlip_MI.csv"
   fb = "fslB0_MI.csv"

   allDataDict = {}

   with open(nc) as f:
      ncData = csv.reader(f, delimiter=",")
      for row in ncData:
	 allDataDict[row[0]] = [float(row[1])]

   with open(ae) as g:
      aeData = csv.reader(g, delimiter=",")
      for row in aeData:
	 if row[0] in allDataDict.keys():
            allDataDict[row[0]].append(float(row[1]))
      for key in allDataDict.keys():
	 if ( len(allDataDict[key]) < 2 ):
            allDataDict[key].append(float('nan'))

   with open(ab) as h:
      abData = csv.reader(h, delimiter=",")
      for row in abData:
	 if row[0] in allDataDict.keys():
            allDataDict[row[0]].append(float(row[1]))
      for key in allDataDict.keys():
	 if ( len(allDataDict[key]) < 3 ):
            allDataDict[key].append(float('nan'))

   with open(fe) as i:
      feData = csv.reader(i, delimiter=",")
      for row in feData:
	 if row[0] in allDataDict.keys():
            allDataDict[row[0]].append(float(row[1]))
      for key in allDataDict.keys():
	 if ( len(allDataDict[key]) < 4 ):
            allDataDict[key].append(float('nan'))

   with open(fb) as j:
      fbData = csv.reader(j, delimiter=",")
      for row in fbData:
	 if row[0] in allDataDict.keys():
            allDataDict[row[0]].append(float(row[1]))
      for key in allDataDict.keys():
	 if ( len(allDataDict[key]) < 5 ):
            allDataDict[key].append(float('nan'))

   for key in allDataDict.keys():
      print str(key) + " " + str(allDataDict[key])

   # busyPlot(allDataDict)
   # separatedPlots(allDataDict)
   percentPlots(allDataDict)



def busyPlot(allDataDict):

   aeAllList = []
   abAllList = []
   feAllList = []
   fbAllList = []
   nAllList  = []

   for key in allDataDict.keys():
      if not ( np.isnan(allDataDict[key][1]) or np.isnan(allDataDict[key][2]) or np.isnan(allDataDict[key][3]) or np.isnan(allDataDict[key][4]) ):
	 aeAllList.append(allDataDict[key][1])
	 abAllList.append(allDataDict[key][2])
	 feAllList.append(allDataDict[key][3])
	 fbAllList.append(allDataDict[key][4])
	 nAllList.append(allDataDict[key][0])

   ncAllSubs = np.array(list(range(0,len(nAllList))))
   nAlly     = np.array(nAllList)
   aeAlly    = np.array(aeAllList)
   abAlly    = np.array(abAllList)
   feAlly    = np.array(feAllList)
   fbAlly    = np.array(fbAllList)

   ### Plot all four corrections on one plot ###

   sns.set_style("darkgrid")
   plt.plot(ncAllSubs, nAlly, label='No Correction',   color='0.5', linestyle='-', lw=1, marker='.')
   plt.plot(ncAllSubs, aeAlly, label='3dQwarp (AFNI)', color='r', linestyle='-', lw=1, marker='.')
   plt.plot(ncAllSubs, feAlly, label='Topup (FSL)',  color='b', linestyle='-', lw=1, marker='.')
   plt.plot(ncAllSubs, abAlly, label='B0 Tools (AFNI)',   color='g', linestyle='-', lw=1, marker='.')
   plt.plot(ncAllSubs, fbAlly, label='Fugue (FSL)',    color='m', linestyle='-', lw=1, marker='.')
   plt.title("Mutual Information after EPI Distortion Corrections")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.15, 0.35)
   plt.legend(loc='lower left')
   plt.savefig("cMI1-allTogether.png")



def separatedPlots(allDataDict):

   ncList  = []
   aeList  = []
   naeList = []
   abList  = []
   nabList = []
   feList  = []
   nfeList = []
   fbList  = []
   nfbList = []

   for key in allDataDict.keys():
      ncList.append(allDataDict[key][0])
      if not np.isnan(allDataDict[key][1]):
	 aeList.append(allDataDict[key][1])
	 naeList.append(allDataDict[key][0])
      if not np.isnan(allDataDict[key][2]):
	 abList.append(allDataDict[key][2])
	 nabList.append(allDataDict[key][0])
      if not np.isnan(allDataDict[key][3]):
	 feList.append(allDataDict[key][3])
	 nfeList.append(allDataDict[key][0])
      if not np.isnan(allDataDict[key][4]):
	 fbList.append(allDataDict[key][4])
	 nfbList.append(allDataDict[key][0])

   ncSubs = np.array(list(range(0,len(ncList))))
   ncy    = np.array(ncList)
   aeSubs = np.array(list(range(0,len(naeList))))
   aey    = np.array(aeList)
   naey   = np.array(naeList)
   abSubs = np.array(list(range(0,len(nabList))))
   aby    = np.array(abList)
   naby   = np.array(nabList)
   feSubs = np.array(list(range(0,len(nfeList))))
   fey    = np.array(feList)
   nfey   = np.array(nfeList)
   fbSubs = np.array(list(range(0,len(nfbList))))
   fby    = np.array(fbList)
   nfby   = np.array(nfbList)

   ### Plot Blip and B0 on separate subplots  ###

   plt.subplot(211)
   sns.set_style("darkgrid")
   plt.plot(aeSubs, naey, label='No Correction',   color='0.5', linestyle='-', lw=1, marker='.')
   plt.plot(aeSubs, aey, label='3dQwarp (AFNI)', color='r', linestyle='-', lw=1, marker='.')
   plt.plot(feSubs, fey, label='Topup (FSL)',  color='b', linestyle='-', lw=1, marker='.')
   plt.title("Mutual Information after Blip Corrections")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.1, 0.35)
   plt.legend(loc='lower left')

   plt.subplot(212)
   sns.set_style("darkgrid")
   plt.plot(abSubs, naby, label='No Correction',   color='0.5', linestyle='-', lw=1, marker='.')
   plt.plot(abSubs, aby, label='B0 Tools (AFNI)',   color='g', linestyle='-', lw=1, marker='.')
   plt.plot(fbSubs, fby, label='Fugue (FSL)',    color='m', linestyle='-', lw=1, marker='.')
   plt.title("Mutual Information after B0 Corrections")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.1, 0.35)
   plt.legend(loc='lower left')

   plt.tight_layout()
   plt.savefig("cMI2-blipAndB0.png")

   ### Plot all four corrections on different subplots ###

   plt.subplot(411)
   sns.set_style("darkgrid")
   plt.plot(aeSubs, naey, label='No Correction',   color='k', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.plot(aeSubs, aey, label='3dQwarp (AFNI)', color='r', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.title("Mutual Information after 3dQwarp (AFNI) Correction")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.1, 0.35)

   plt.subplot(412)
   sns.set_style("darkgrid")
   plt.plot(feSubs, naey, label='No Correction',   color='k', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.plot(feSubs, fey, label='Topup (FSL)',  color='r', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.title("Mutual Information after Topup (FSL) Correction")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.1, 0.35)

   plt.subplot(413)
   sns.set_style("darkgrid")
   plt.plot(abSubs, naby, label='No Correction',   color='k', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.plot(abSubs, aby, label='B0 Tools (AFNI)',   color='r', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.title("Mutual Information after B0 Tools (AFNI) Correction")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.1, 0.35)

   plt.subplot(414)
   sns.set_style("darkgrid")
   plt.plot(fbSubs, naby, label='No Correction',   color='k', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.plot(fbSubs, fby, label='Fugue (FSL)',    color='r', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.title("Mutual Information after Fugue (FSL) Correction")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.1, 0.35)

   plt.tight_layout()
   plt.savefig("cMI3-allSeparated.png")



def percentPlots(allDataDict):

   ncList  = []
   aeList  = []
   naeList = []
   abList  = []
   nabList = []
   feList  = []
   nfeList = []
   fbList  = []
   nfbList = []

   for key in allDataDict.keys():
      ncList.append(allDataDict[key][0])
      if not np.isnan(allDataDict[key][1]):
         aePC = ((allDataDict[key][1] - allDataDict[key][0])/allDataDict[key][0])*100
	 aeList.append(aePC)
	 naeList.append(allDataDict[key][0])
      if not np.isnan(allDataDict[key][2]):
	 abPC = ((allDataDict[key][2] - allDataDict[key][0])/allDataDict[key][0])*100
	 abList.append(abPC)
	 nabList.append(allDataDict[key][0])
      if not np.isnan(allDataDict[key][3]):
         fePC = ((allDataDict[key][3] - allDataDict[key][0])/allDataDict[key][0])*100
	 feList.append(fePC)
	 nfeList.append(allDataDict[key][0])
      if not np.isnan(allDataDict[key][4]):
         fbPC = ((allDataDict[key][4] - allDataDict[key][0])/allDataDict[key][0])*100
	 fbList.append(fbPC)
	 nfbList.append(allDataDict[key][0])

   ncSubs = np.array(list(range(0,len(ncList))))
   ncy    = np.array(ncList)
   aeSubs = np.array(list(range(0,len(naeList))))
   aey    = np.array(aeList)
   naey   = np.array(naeList)
   abSubs = np.array(list(range(0,len(nabList))))
   aby    = np.array(abList)
   naby   = np.array(nabList)
   feSubs = np.array(list(range(0,len(nfeList))))
   fey    = np.array(feList)
   nfey   = np.array(nfeList)
   fbSubs = np.array(list(range(0,len(nfbList))))
   fby    = np.array(fbList)
   nfby   = np.array(nfbList)

   ### Plot all four corrections on different subplots ###

   # plt.subplot(411)
   plt.bar(naey, aey)
   plt.title("Mutual Information after 3dQwarp (AFNI) Correction")
   plt.xlabel('Subjects')
   plt.ylabel('MI')

   """
   plt.subplot(412)
   sns.set_style("darkgrid")
   plt.plot(feSubs, naey, label='No Correction',   color='k', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.plot(feSubs, fey, label='Topup (FSL)',  color='r', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.title("Mutual Information after Topup (FSL) Correction")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.1, 0.35)

   plt.subplot(413)
   sns.set_style("darkgrid")
   plt.plot(abSubs, naby, label='No Correction',   color='k', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.plot(abSubs, aby, label='B0 Tools (AFNI)',   color='r', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.title("Mutual Information after B0 Tools (AFNI) Correction")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.1, 0.35)

   plt.subplot(414)
   sns.set_style("darkgrid")
   plt.plot(fbSubs, naby, label='No Correction',   color='k', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.plot(fbSubs, fby, label='Fugue (FSL)',    color='r', linestyle='-', lw=0.5, marker='.', markersize=2)
   plt.title("Mutual Information after Fugue (FSL) Correction")
   plt.xlabel('Subjects')
   plt.ylabel('MI')
   plt.ylim(0.1, 0.35)

   plt.tight_layout()
   """

   plt.savefig("cMI4-percentChange.png")



def main():
   
   usage = "%prog [options]"
   description = ("Routine to create plots for comparing mutual information outputs from distortionFix.py:")

   usage =       ("  %prog [options]" )
   epilog =      ("For questions, suggestions, information, please contact Vinai Roopchansingh, Jerry French.")

   parser = OptionParser(usage=usage, description=description, epilog=epilog)

   buildDataDict()



if __name__ == '__main__':
   sys.exit(main())


