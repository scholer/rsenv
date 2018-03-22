@echo off
REM %~dp0 is the directory of the 0th parameter (the name of this script)
REM Use %* to pass in all cmd args (except %0)
python %~dp0\espec_grep.py %*
