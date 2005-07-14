@echo off
call setdir.bat
if not defined DIR goto EOF

pushd %DIR%\server
python ebooks.py -update
popd

:EOF
