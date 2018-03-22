@echo off
REM %~dp0 is the directory of the 0th parameter (the name of this script)

REM Use %* to pass in all cmd args (except %0)
C:\Users\scholer\Anaconda3\envs\pyqt5\python.exe %~dp0\cadnano_apply_seq.py %*

REM
REM python %~dp0\espec_grep.py %*
