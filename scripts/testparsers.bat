@echo off
call setdir.bat
if not defined DIR goto EOF

pushd %DIR%\server\tests
python UnitTestParsers.py
popd

:EOF
