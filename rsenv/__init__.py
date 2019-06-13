# """
# See also:
#  - https://docs.google.com/document/d/10bSiPwq4DrLGoB8zaCJBG3nrtK5-nC21Yhx-cCEyCO4/edit
#  - Dropbox/Dev/Projects/OligoManager2/oligomanager
#  - Dropbox/Dev/Projects/OligoManager2/oligomanager/tools
#  - Dropbox/Dev/Projects/OligoManager2/python_scripts  (obsolete)
#  - Dropbox/NATlab shared/DesignBlueprints/caDNAno/A-few-hints-for-using-python.txt
#  - Dropbox/Dev/Python/Python-copy-paste-examples.txt
#
# Other tips for a better interpreter:
#  - See env/__init__.py
#  - http://rc98.net/pystartup
#
# Also consider:
#  - Using the ipython interpreter as your default interactive interpreter.
# """

#__all__ = ['confluence.py', 'exceptions.py', 'fs_util.py', 'help.py', 'nanodrop_utils.py', 'phys', 'data_analysis', 'protein.py', 'qpcr', 'rsfavmodules.py', 'seq', 'utils', 'various.py', '__init__.py

#__all__ = ['confluence', 'exceptions', 'fs_util', 'help', 'nanodrop_utils', 'phys', 'data_analysis', 'protein', 'qpcr', 'rsfavmodules', 'seq', 'utils', 'various']

# from . import rsfavmodules as fav
# from . import seq

#import data_analysis
#import qpcr
##from rsconfluence import *
#import confluence
#import seq
#import protein
#from various import *
##from rshelp import *'
#import help
#import nanodrop_utils
#from exceptions import *
#from util import *
# Not importing rsfavmodules. Import manually if needed using
# from rsfavmodules import *


# from http://conjurecode.com/enable-auto-complete-in-python-interpreter/
# If If the PYTHONSTARTUP variable is set to a readable file, then the contents of that file will be
# run before anything else when the interactive interpreter is run.
#import rlcompleter, readline
#readline.parse_and_bind('tab:complete')


__version__ = '0.3.0'
