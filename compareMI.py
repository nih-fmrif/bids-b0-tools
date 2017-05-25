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

# create new columns for percent changes from noCorr
for corr in [corrMeth for corrMeth in df.columns if corrMeth != 'nc']:
   df[corr] = (df[corr]-df['nc'])*100/df['nc']

# print df.info()
print df.describe()

# Cannot append directly on to original df as we append to it, as the appended rows will affect
# computed statistics.  Make an empty data frame (df1) matching original (with "index=..."),
# append to this new frame, based on statistics computed from original frame.

df1 = pd.DataFrame(columns=df.columns)
df1 = df1.append(pd.Series([df[corr].mean()   for corr in df.columns], index=df.columns, name='mean'))
df1 = df1.append(pd.Series([df[corr].median() for corr in df.columns], index=df.columns, name='median'))
df1 = df1.append(pd.Series([df[corr].std()    for corr in df.columns], index=df.columns, name='std'))


# Then append new data frame to original for plotting and display
df  = df.append (df1)

print df

# remove all rows with NaN in nc, ae, and fe
df = df[np.isfinite(df['nc']+df['ae']+df['fe'])].sort()
# df = df[np.isfinite(df['nc']+df['ab_AP_-1.0'])].sort()

# plot the MI values for each distortion correction technique by subject
df[df.columns].plot(kind='bar', grid=False)
plt.title("Mutual Information for each Correction Technique by Subject")
plt.xlabel('Subjects')
plt.ylabel('Mutual Information')
plt.legend(df.columns, labels=df.columns, bbox_to_anchor=(1.05, 1), loc=2, fontsize='small', borderaxespad=0.)
plt.ylim(-15, 25)
plt.savefig("test1.png", bbox_inches='tight')
os.system("display test1.png &")


