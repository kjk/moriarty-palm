@echo off

if %computername%==DVD goto SetDVD
if %computername%==DVD2 goto SetDVD2
if %computername%==TLAP goto SetTlap
if %computername%==KJKLAP1 goto SetKjklap1
if %computername%==MAGG goto SetSzymon
if %computername%==GIZMO goto SetAndrzej
if %computername%==RABBAN goto SetAndrzejDVD

echo "Don't know the setup for computer %computername%"
goto EOF

rem set COPY_LOB_CACHE to 1 if wants to copy LOB CACHE as well. Usually
rem we don't want to, because it's large and slows down copying
rem files to the server. However, it's a must if testing ListsOfBests
rem or when we deploy official server
rem can be overwritten by setting FORCE_COPY_LOB_CACHE=1 before calling here
rem (used by runlocal.bat)

:SetDVD
:SetDVD2
:SetTlap
:SetKjklap1
SET DSTDIR=c:\kjk\infoman\src
SET SRCDIR=c:\kjk\src\mine\moriarty_palm
SET COPY_LOB_CACHE=0
goto SetupDone

:SetSzymon
SET DSTDIR=l:\temp\infoman\src
SET SRCDIR=l:\moriarty_palm
SET COPY_LOB_CACHE=0
goto SetupDone

:SetAndrzejDVD
SET DSTDIR=c:\tmp\infoman\src
SET SRCDIR=c:\ArsLexis\moriarty_palm
SET COPY_LOB_CACHE=0
goto SetupDone

:SetAndrzej
SET DSTDIR=c:\tmp\infoman\src
SET SRCDIR=c:\ArsLexis\moriarty
SET COPY_LOB_CACHE=0
goto SetupDone

:SetupDone

IF NOT DEFINED FORCE_COPY_LOB_CACHE goto Skip
IF %FORCE_COPY_LOB_CACHE%==1 @SET COPY_LOB_CACHE=1

:Skip

SET PEDIADIR=%SRCDIR%\..\ipedia

del /f /s /q %DSTDIR%
mkdir %DSTDIR%

mkdir %DSTDIR%\lupy
mkdir %DSTDIR%\lupy\index
mkdir %DSTDIR%\lupy\search

copy %SRCDIR%\external\*.py %DSTDIR%

copy %SRCDIR%\external\lupy\*.py %DSTDIR%\lupy\
copy %SRCDIR%\external\lupy\index\*.py %DSTDIR%\lupy\index\
copy %SRCDIR%\external\lupy\search\*.py %DSTDIR%\lupy\search\
copy %SRCDIR%\scripts\infoman_gen_reg_codes.py %DSTDIR%
copy %SRCDIR%\scripts\import_reg_codes.py %DSTDIR%
copy %SRCDIR%\server\*.py %DSTDIR%
copy %SRCDIR%\server\*.txt %DSTDIR%
if %COPY_LOB_CACHE%==1 @copy %SRCDIR%\server\*.pic %DSTDIR%
copy %SRCDIR%\server\parsers\*.py %DSTDIR%
copy %PEDIADIR%\server\entities.py %DSTDIR%
copy %PEDIADIR%\server\iPediaServer.py %DSTDIR%
copy %PEDIADIR%\server\iPediaFields.py %DSTDIR%

pushd %DSTDIR%
rem remove stuff that is not needed to run the server
rem ultimately those shouldn't be in the \server dir at all
del InfoManWatchdog.py makeListsOfBestsCache.py makeListsOfBestsCacheItems.py TestServer.py
popd
