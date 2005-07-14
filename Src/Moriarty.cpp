
#include "MoriartyApplication.hpp"

void std::__msl_error(const char* str)
{
    ErrFatalDisplay(str);
    ErrThrow(sysErrParamErr);
}

void ArsLexis::handleBadAlloc()
{
    ErrThrow(memErrNotEnoughSpace);    
}

UInt32 PilotMain(UInt16 cmd, MemPtr cmdPBP, UInt16 launchFlags)
{
    return Application::main<MoriartyApplication>(cmd, cmdPBP, launchFlags);
}

const char rsaPublicKey[] = "\xdb\xa6\x0a\x13\x10\x98\xb7\xfc\x9d\x78\x47\x9f\x40\xf0\x10\xdd\xe6\x52\xad\xe7\x21\xc6\x12\xdb\x22\x4a\xb2\x90\x58\x3c\x5f\x98\xae\xf1\xd2\x6b\x66\xca\x33\xf9\x16\xa6\xa2\xdb\xdc\x8a\x42\x34\x96\x80\x42\x81\x7e\xc9\xab\x0c\x76\x79\x4d\x46\x08\xa4\x7a\xd3";