@echo off
REM %~dp0 is the directory of the 0th parameter (the name of this script)

REM Use %* to pass in all cmd args (except %0)
REM echo %*
REM echo python %~dp0\conda_grep_envs.py %*
python %~dp0\conda_grep_envs.py %*

