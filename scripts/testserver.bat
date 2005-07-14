@echo off
call setdir.bat
if not defined DIR goto EOF

pushd %DIR%\server\tests
python UnitTestsServer.py %1 %2 %3 %4 %5 %6 %7 %8 %9
popd

:EOF