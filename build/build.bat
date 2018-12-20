@echo off
echo Building package... (you have updated setup.py parameters, right?)

rem Copy all package contents (except build/) into this directory
mkdir sdsu
xcopy .. sdsu > NUL
xcopy ..\security sdsu\security\ /e > NUL
xcopy ..\static sdsu\static\ /e > NUL
copy ..\README.rst . > NUL

rem Run test suite
rem python setup.py test sdist --format=targz

rem Build, register, and publish package
python setup.py sdist bdist_wheel
rem twine upload --repository-url https://test.pypi.org/legacy/ dist/*
twine upload dist/*

rem Remove build artifacts
rem rmdir dist /S /Q
rem rmdir pyroclast /S /Q
rem rmdir pyroclast.egg-info /S /Q
rem del README.md
