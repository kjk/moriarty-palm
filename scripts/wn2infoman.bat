@echo off
call setdir.bat
if not defined DIR goto EOF

..\server\wn2infoman.py %1 %2 %3 %4 %5 %6 %7

:EOF