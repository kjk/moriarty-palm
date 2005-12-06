@echo off
call setdir.bat
if not defined DIR goto EOF

python ..\server\parsers\log-file.py %1 %2 %3

:EOF
