@echo off
call setdir.bat
if not defined DIR goto EOF

pushd %DIR%\server\parsers
python netflix.py %1 %2 %3 %4
popd

:EOF
