#!/usr/bin/env python

import sys
from   optparse  import  OptionParser
from   bidsFSUtils import bidsToolsFS



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

   options, args = parser.parse_args()

   bidsDict = bidsToolsFS().buildBIDSDict(options.dataDir)

   for eachSubject in bidsDict.keys():
      print "Subject's " + eachSubject + " dictionary is " + str(bidsDict[eachSubject])



if __name__ == '__main__':
   sys.exit(main())
