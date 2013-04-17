"""
See also:
 - https://docs.google.com/document/d/10bSiPwq4DrLGoB8zaCJBG3nrtK5-nC21Yhx-cCEyCO4/edit
 - Dropbox/Dev/Projects/OligoManager2/oligomanager
 - Dropbox/Dev/Projects/OligoManager2/oligomanager/tools
 - Dropbox/Dev/Projects/OligoManager2/python_scripts  (obsolete)
 - Dropbox/NATlab shared/DesignBlueprints/caDNAno/A-few-hints-for-using-python.txt
 - Dropbox/Dev/Python/Python-copy-paste-examples.txt

"""



import rsnanodrop                   # This is fairly light-weight.

# BEFORE I CAN INCLUDE THESE AUTOMATICALLY, THEY SHOULD BE RE-CODED SO THEY DO NOT LOAD 
# A LOT OF HEAVY MODULE UPON INITIAL IMPORT, BUT ONLY WHEN THEY ARE ACTUALLY USED.
# AS OF WRITING, THESE MODULES TAKE ABOUT 20 SECS TO IMPORT WHICH IS TOO MUCH.

#import rscomponentanalyser          # Imports YAML, numpy, scipy, matplotlib, etc.
#import rsfluoromaxdataplotter       # This also imports a lot of the same heavy modules.
#import rsdataplotter1               # Also imports numpy, scipy, pyplot, etc.
