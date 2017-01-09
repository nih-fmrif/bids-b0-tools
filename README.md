
# BIDS-tools

Scripts, tools, and documents on creating, parsing, and working with
BIDS-structured data sets.



Use of organizeToBIDS.csh script
================================

Put .tgz files to be organized in folders, with each folder containing
data for 1 subject, and the name of the folder being that subject's ID.

With that structure, this script will build a BIDS tree with a
sub-subjectID folder, containing the different types of data, with the
matching scans inside each folder.


Limits of organizeToBIDS.csh:
-----------------------------

* It also does not generate the auxiliary JSON metadata files.

* Finally, this script outputs AFNI format (.HEAD/.BRIK) data sets.  To
change this behavior, .nii or .nii.gz can be added to the Dimon commands
file prefix flag values, to generate NIFTI-formatted data sets.

