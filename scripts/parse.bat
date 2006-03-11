@echo off
call setdir.bat
if not defined DIR goto EOF

python ..\server\parsers\parseFromErrorFile.py %1

:EOF
