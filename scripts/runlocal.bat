@rem create a local copy 

@rem set settings based on computer name
@if %computername%==DVD goto SetDVD
@if %computername%==DVD2 goto SetDVD
@if %computername%==TLAP goto SetDVD
@if %computername%==KJKLAP1 goto SetKjklap1
@if %computername%==MAGG goto SetSzymon
@if %computername%==GIZMO goto SetAndrzej
@if %computername%==RABBAN goto SetAndrzejDVD

@echo "Don't know the setup for computer %computername%"
@goto EOF

:SetDVD
@SET DSTDIR=c:\kjk\infoman\src
@SET SRCDIR=c:\kjk\src\mine\moriarty_palm
@goto SetupDone

:SetKjklap1
@SET DSTDIR=c:\kjk\infoman\src
@SET SRCDIR=c:\kjk\src\mine\moriarty_palm
@goto SetupDone

:SetSzymon
@SET DSTDIR=l:\temp\infoman\src
@SET SRCDIR=l:\moriarty_palm
@goto SetupDone

:SetAndrzej
@SET DSTDIR=c:\tmp\infoman\src
@SET SRCDIR=c:\ArsLexis\moriarty
@goto SetupDone

:SetAndrzejDVD
@SET DSTDIR=c:\tmp\infoman\src
@SET SRCDIR=c:\ArsLexis\moriarty_palm
@goto SetupDone

:SetupDone

@set FORCE_COPY_LOB_CACHE=1
@call createlocal.bat

pushd %DSTDIR%
start cmd.exe /K python.exe InfoManServer.py -verbose -disableregcheck %1 %2 %3
popd

:EOF
