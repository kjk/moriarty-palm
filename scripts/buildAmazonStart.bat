@echo off
call setdir.bat
if not defined DIR goto EOF

parserTestFiles\buildAmazonStartPage.py

copy amazon-start-page.txt ..\Rsc
copy amazon-start-page-small.txt ..\Rsc

:EOF
