@echo off
call setdir.bat
if not defined DIR goto EOF

pushd %DIR%\server\parsers
python dictionary.py %1 %2 %3 %4 %5 %6 %7
popd

:EOF
