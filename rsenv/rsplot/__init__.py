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
# Edit: All heavy imports (numpy, matplotlib, etc) have been moved to __init__ methods.
#     - Now, importing rsenv only takes a fraction of a sec :)

# From the Python 2 FAQ: (I.e. --> module import can be put in classes' __init_ method.
"""
If only instances of a specific class use a module, then it is reasonable to import 
the module in the class's __init__ method and then assign the module to an instance 
variable so that the module is always available (via that instance variable) during 
the life of the object. Note that to delay an import until the class is instantiated, 
the import must be inside a method. Putting the import inside the class but outside 
of any method still causes the import to occur when the module is initialized.
"""

import rscomponentanalyser          # Imports YAML, numpy, scipy, matplotlib, etc.
import rsfluoromaxdataplotter       # This also imports a lot of the same heavy modules.
import rsdataplotter1               # Also imports numpy, scipy, pyplot, etc.

