if %computername%==DVD goto SetDVD
if %computername%==DVD2 goto SetDVD2
if %computername%==TLAP goto SetTlap
if %computername%==KJKLAP1 goto SetKjklap1

echo "Don't know the setup for computer %computername%"
exit

:SetDVD2
:SetTlap
SET DIR=c:\kjk\src\moriarty_palm
goto Done

:SetDVD
:SetKjklap1
SET DIR=c:\kjk\src\mine\moriarty_palm
goto Done

:Done
set PYTHONPATH=%DIR%\external;%DIR%\server;%DIR%\server\parsers;%DIR%\server\tests;%DIR%\..\ipedia\Server;%DIR%\scripts\parserTestFiles