#include "FlickrDbg.h"

void DbgNum(long l)
{
    char buff[12];
    StrPrintF(buff, "%ld", l);
    DbgMessage(buff);
}

void DbgHex(unsigned long l)
{
    char buff[12];
    StrPrintF(buff, "0x%0lx", l);
    DbgMessage(buff);
}

