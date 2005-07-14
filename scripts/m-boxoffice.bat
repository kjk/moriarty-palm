@echo off
call setdir.bat
if not defined DIR goto EOF

python ..\server\parsers\boxoffice.py %1 %2 %3 %4 %5 %6

:EOF
