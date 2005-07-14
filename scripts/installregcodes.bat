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

@ rem if second param is "official" then we update the official server

@rem set settings based on computer name
@if %computername%==DVD goto SetDVD
@if %computername%==DVD2 goto SetDVD2
@if %computername%==TLAP goto Tlap
@if %computername%==KJKLAP1 goto SetKjklap1

@echo "Don't know the setup for computer %computername%"
@goto EOF

:SetDVD
:SetDVD2
:SetTlap
@SET USER=infoman-kjk
@rem this relates to what createlocal.bat uses for DSTDIR
@SET SRC=C:\kjk\src\mine\moriarty_palm
@goto SetupDone

:SetKjklap1
@SET USER=infoman-kjk
@rem this relates to what createlocal.bat uses for DSTDIR
@SET SRC=C:\kjk\src\mine\moriarty_palm
@goto SetupDone

:SetupDone

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

:NotOfficial

@rem provide password as the first argument
@SET PWD=%1

@IF NOT DEFINED USER echo "need to define USER" & goto :EOF
@IF NOT DEFINED PWD echo 'need to define PWD' & goto :EOF
@IF NOT DEFINED SRC echo "need to define SRC" & goto :EOF

plink -pw %PWD% %USER%@infoman.arslexis.com cd /home/%USER%; rm -rf tmp; mkdir tmp
pscp -pw %PWD% %SRC%\server\multiUserSupport.py %SRC%\scripts\import_reg_codes.py %SRC%\scripts\infoman_gen_reg_codes.py %SRC%\scripts\reg_codes.csv %USER%@infoman.arslexis.com:/home/%USER%/tmp
plink -pw %PWD% %USER%@infoman.arslexis.com cd /home/%USER%/tmp; python2.4 import_reg_codes.py

:EOF
