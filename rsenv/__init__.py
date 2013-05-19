"""
See also:
 - https://docs.google.com/document/d/10bSiPwq4DrLGoB8zaCJBG3nrtK5-nC21Yhx-cCEyCO4/edit
 - Dropbox/Dev/Projects/OligoManager2/oligomanager
 - Dropbox/Dev/Projects/OligoManager2/oligomanager/tools
 - Dropbox/Dev/Projects/OligoManager2/python_scripts  (obsolete)
 - Dropbox/NATlab shared/DesignBlueprints/caDNAno/A-few-hints-for-using-python.txt
 - Dropbox/Dev/Python/Python-copy-paste-examples.txt

Other tips for a better interpreter:
 - See env/__init__.py
 - http://rc98.net/pystartup

Also consider:
 - Using the ipython interpreter as your default interactive interpreter.
"""



import rsplot
from rsconfluence import *
#import rsconfluence
import rsseq
import rsprotein 
from rsvarious import *
#from rshelp import *'
import rshelp
import rsnanodrop_utils
from rsexceptions import *
# Not importing rsfavmodules. Import manually if needed using
# from rsfavmodules import *


""" from http://conjurecode.com/enable-auto-complete-in-python-interpreter/
If If the PYTHONSTARTUP variable is set to a readable file, then the contents of that file will be 
run before anything else when the interactive interpreter is run."""
import rlcompleter, readline
readline.parse_and_bind('tab:complete')

