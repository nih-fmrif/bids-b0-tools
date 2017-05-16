#!/usr/bin/env python

import sys, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# create dataframes from command line argument list of csv files
# each file should have 'sub' as first column header and the
# 'corrMethod' (from distortionFix.py) as the second column header

print "file list is " + str(sys.argv[1:])

# create dataframe
df = pd.concat([pd.read_csv(f, index_col='sub') for f in sys.argv[1:]], axis=1, join='outer')

# remove all rows with NaN in nc, ae, and fe
# df = df[np.isfinite(df['nc']+df['ae']+df['fe'])].sort()
df = df[np.isfinite(df['nc']+df['fby'])].sort()

# create new columns for percent changes from noCorr
for corr in [corrMeth for corrMeth in df.columns if corrMeth != 'nc']:
   df[corr] = (df[corr]-df['nc'])*100/df['nc']

corrMeans = {}
corrMeds = {}
corrStd = {}

for corr in df.columns:
   corrMeans.update ({corr : df[corr].mean()})
   corrMeds.update  ({corr : df[corr].median()})
   corrStd.update   ({corr : df[corr].std()})

df2 = pd.Series(corrMeans.values(), index=corrMeans.keys(), name='mean')
df3 = pd.Series(corrMeds.values(),  index=corrMeds.keys(),  name='median')
df4 = pd.Series(corrStd.values(),   index=corrStd.keys(),   name='std')
df = df.append(df2)
df = df.append(df3)
df = df.append(df4)

print df
print df.info()
# print df.describe()

# plot the MI values for each distortion correction technique by subject
df[df.columns].plot(kind='bar', grid=False)
plt.title("Mutual Information for each Correction Technique by Subject")
plt.xlabel('Subjects')
plt.ylabel('Mutual Information')
# plt.legend(['MI_nc', 'MI_ae', 'MI_ab', 'MI_fe', 'MI_fb'],
#            labels=['noCorr', 'afniBlip', 'afniB0', 'fslBlip', 'fslB0'],
#            bbox_to_anchor=(1.05, 1), loc=2, fontsize='small', borderaxespad=0.)
plt.ylim(-5, 5)
plt.savefig("test1.png", bbox_inches='tight')
os.system("display test1.png")


