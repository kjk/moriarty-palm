@rem scripts that copies InfoMan server files to the server
@rem kills currently running server and starts a new one
@rem could be vastly improved by copying only files that have
@rem changed (a good approximation of this would be checked out
@rem files which can be quickly determined with svn status)
@rem another way to speed it up would be to copy to a local directory,
@rem zip it, copy the zip file to the server and unzip it there

@rem set your Unix user, password and where do you keep the sources
@rem (note that ipedia sources must be at the same level as moriarty_palm)
@rem e.g.:

@rem set settings based on computer name
@if %computername%==DVD goto SetDVD
@if %computername%==DVD2 goto SetDVD
@if %computername%==TLAP goto SetDVD
@if %computername%==KJKLAP1 goto SetKjklap1
@if %computername%==MAGG goto SetSzymon

@echo "Don't know the setup for computer %computername%"
@goto EOF

@SET FORCE_COPY_LOB_CACHE=1

:SetDVD
@SET USER=infoman-kjk
@rem this relates to what createlocal.bat uses for DSTDIR
@SET DIR=c:\kjk\infoman
@SET DSTDIR=/infoman/kjk/
@SET FORCE_COPY_LOB_CACHE=0
@goto SetupDone

:SetKjklap1
@SET USER=infoman-kjk
@rem this relates to what createlocal.bat uses for DSTDIR
@SET DIR=c:\kjk\infoman
@SET DSTDIR=/tmp/infoman-kjk/
@SET FORCE_COPY_LOB_CACHE=0
@goto SetupDone

:SetSzymon
@SET USER=infoman-szymon
@rem this relates to what createlocal.bat uses for DSTDIR
@SET DIR=l:\temp\infoman
@SET FORCE_COPY_LOB_CACHE=1
@goto SetupDone

:SetupDone

@rem provide password as the first argument
@SET PWD=%1

@IF NOT DEFINED USER echo "need to define USER" & goto :EOF
@IF NOT DEFINED PWD echo 'need to define PWD' & goto :EOF

@SET SEC_P=%2
@IF DEFINED SEC_P goto SetupOfficial
@goto NotOfficial

:SetupOfficial
@IF %SEC_P%==official goto ReallySetupOfficial
@echo if second param given, it should be "official" and not %SEC_P%
@goto EOF

:ReallySetupOfficial
@rem TODO: check that the computer is DVD or KJKLAP1
@rem echo setting up for official server
@SET USER=infoman
@SET FORCE_COPY_LOB_CACHE=1
@SET DSTDIR=/tmp/infoman/
:NotOfficial

bzip2 wn-dict.txt
bzip2 wn-word-index.pickle
bzip2 wn-words.pickle
pscp -r -pw %PWD% wn-dict.txt.bz2 wn-word-index.pickle.bz2 wn-words.pickle.bz2 %USER%@infoman.arslexis.com:/%DSTDIR%
plink -pw %PWD% %USER%@infoman.arslexis.com cd %DSTDIR%; bzip2 -d *bz2
bzip2 -d *bz2

:EOF
