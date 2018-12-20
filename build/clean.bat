@echo off
rem Deletes all intermediate and terminal artifacts from the build folder
rmdir /S /Q dist
rmdir /S /Q sdsu
rmdir /S /Q sdsu.egg-info
del README.rst
