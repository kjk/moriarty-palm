@echo off
call setdir.bat
if not defined DIR goto EOF

pushd %DIR%\scripts\parserTestFiles
python buildParserTests.py %1 %2 %3 %4 %5 %6
popd

:EOF
