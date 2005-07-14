@echo off
call setdir.bat
if not defined DIR goto EOF

python parseStats.py %1 %2 %3 %4 %5 %6 %7

:EOF