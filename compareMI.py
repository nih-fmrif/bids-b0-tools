#!/usr/bin/env python

import time, sys, os
import csv
import pandas as pd
import matplotlib.pyplot as plt

# create dataframes from MI csv files
nc = pd.read_csv('noCorr_MI.csv', names=['subs', 'MI_nc'])
ae = pd.read_csv('afniBlip_MI.csv', names=['subs', 'MI_ae'])
ab = pd.read_csv('afniB0_MI.csv', names=['subs', 'MI_ab'])
fe = pd.read_csv('fslBlip_MI.csv', names=['subs', 'MI_fe'])
fb = pd.read_csv('fslB0_MI.csv', names=['subs', 'MI_fb'])

# merge all MI columns into a single dataframe
df_1 = nc.merge(ae, on='subs')
df_2 = df_1.merge(ab, on='subs')
df_3 = df_2.merge(fe, on='subs')
df_m = df_3.merge(fb, on='subs')

# sort new dataframe alphabetically
df_ms = df_m.sort('subs')
df_ms['pcMI_ae'] = (df_ms['MI_ae']-df_ms['MI_nc'])*100/(df_ms['MI_nc']) 
df_ms['pcMI_ab'] = (df_ms['MI_ab']-df_ms['MI_nc'])*100/(df_ms['MI_nc'])
df_ms['pcMI_fe'] = (df_ms['MI_fe']-df_ms['MI_nc'])*100/(df_ms['MI_nc'])
df_ms['pcMI_fb'] = (df_ms['MI_fb']-df_ms['MI_nc'])*100/(df_ms['MI_nc'])
# print df_ms

df_median = pd.DataFrame({'subs': ['median'],
                          'pcMI_ae': [df_ms['pcMI_ae'].median(axis='index')],
                          'pcMI_ab': [df_ms['pcMI_ab'].median(axis='index')],
                          'pcMI_fe': [df_ms['pcMI_fe'].median(axis='index')],
                          'pcMI_fb': [df_ms['pcMI_fb'].median(axis='index')]})

df_mean   = pd.DataFrame({'subs': ['mean'],
                          'pcMI_ae': [df_ms['pcMI_ae'].mean(axis='index')],
                          'pcMI_ab': [df_ms['pcMI_ab'].mean(axis='index')],
                          'pcMI_fe': [df_ms['pcMI_fe'].mean(axis='index')],
                          'pcMI_fb': [df_ms['pcMI_fb'].mean(axis='index')]})

df_stdev  = pd.DataFrame({'subs': ['stdev'],
                          'pcMI_ae': [df_ms['pcMI_ae'].std(axis='index')],
                          'pcMI_ab': [df_ms['pcMI_ab'].std(axis='index')],
                          'pcMI_fe': [df_ms['pcMI_fe'].std(axis='index')],
                          'pcMI_fb': [df_ms['pcMI_fb'].std(axis='index')]})

df_final = df_ms.append([df_median, df_mean, df_stdev])
print df_final


# plot the MI values for each distortion correction technique by subject
df_final[['MI_nc', 'MI_ae', 'MI_ab', 'MI_fe', 'MI_fb']].plot(kind='bar', grid=False)
plt.title("Mutual Information for each Correction Technique by Subject")
plt.xlabel('Subjects')
plt.ylabel('Mutual Information')
plt.legend(['MI_nc', 'MI_ae', 'MI_ab', 'MI_fe', 'MI_fb'],
           labels=['noCorr', 'afniBlip', 'afniB0', 'fslBlip', 'fslB0'],
	   bbox_to_anchor=(1.05, 1), loc=2, fontsize='small', borderaxespad=0.)
# plt.ylim(0.14, 0.35)
plt.savefig("test1.png", bbox_inches='tight')
# os.system("display test1.png")


# plot the percent change in MI values for each distortion correction
# technique by subject
df_final[['pcMI_ae', 'pcMI_ab', 'pcMI_fe', 'pcMI_fb']].plot(kind='bar', grid=False)
plt.title("Mutual Information for each Correction Technique by Subject")
plt.xlabel('Subjects')
plt.ylabel('Percent Change in Mutual Information')
plt.legend(['pcMI_ae', 'pcMI_ab', 'pcMI_fe', 'pcMI_fb'],
           labels=['afniBlip', 'afniB0', 'fslBlip', 'fslB0'],
	   bbox_to_anchor=(1.05, 1), loc=2, fontsize='small', borderaxespad=0.)
plt.ylim(-15, 25)
plt.savefig("test2.png", bbox_inches='tight')
os.system("display test2.png")
