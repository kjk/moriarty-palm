@echo off
call setdir.bat
if not defined DIR goto EOF

python makeListsOfBestsCache.py %1 %2 %3 %4 %5 %6

:EOF