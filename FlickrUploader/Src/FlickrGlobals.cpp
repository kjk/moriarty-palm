#include "FlickrPrivate.h"
#include "Flickr.h"
#include "FlickrDbg.h"

Err FlickrGlobals::Init(UInt16 refNum)
{
    MemSet(this, sizeof(*this), 0);
    thisLibRefNum = refNum;
    openCount = 0;
   
    return errNone; 
}

void FlickrGlobals::Dispose()
{
    
}

FlickrSocketContext::FlickrSocketContext(UInt16 libRef)
{
    MemSet(this, sizeof(*this), 0);
    magic = magicValue;
    imageData = NULL;
    requestData = NULL;
    progress = NULL;
    flickrAddress = 0;
    libRefNum = libRef;
    netLibRefNum = sysInvalidRefNum;
    netLibOpen = false;
    netLibLoaded = false;
    netSocket = -1;
    sent = 0;
//    chunkSize = 576;
    chunkSize = 8192;
    responseData = NULL;
    toggle = false;
    lastAnimationTicks = 0;
    imageSize = 0;
    requestSize = 0;
}

#define netLibName "Net.lib"

Err FlickrSocketContext::Init()
{   
    return InitSession();
}

Err FlickrSocketContext::NetLibInit()
{
    DMSG("NetLibInit(): enter"); DENDL;
    Err err = SysLibFind(netLibName, &netLibRefNum);
    if (errNone != err)
    {
        if (sysErrLibNotFound == err)
        {
            err = SysLibLoad(netLibType, netCreator, &netLibRefNum);
            if (errNone != err)
                return err;
            netLibLoaded = true;
        }
        else
            return err;
    }
    assert(sysInvalidRefNum != netLibRefNum);
    UInt16 ifErr;
    err = NetLibOpen(netLibRefNum, &ifErr);
    if (netErrAlreadyOpen == err)
        err = errNone;
        
    if (errNone != err)
    {
        DMSG("NetLibInit(): NetLibOpen() returned error: "); DNUM(err); DENDL;
        NetLibDispose();
        return err;
    }
    if (errNone != ifErr)
    {
        DMSG("NetLibInit(): NetLibOpen() returned interface error: "); DNUM(ifErr); DENDL;
        netLibOpen = true;
        NetLibDispose();
        return netErrNotOpen;
    }
    netLibOpen = true;
    DMSG("NetLibInit(): exit; netLibRefNum: "); DNUM(netLibRefNum); DENDL;
    return errNone;
}

void FlickrSocketContext::NetLibDispose()
{
    Err err;
    if (netLibOpen)
    {
        DMSG("NetLibDispose(): calling NetLibClose()"); DENDL;
        err = NetLibClose(netLibRefNum, false);
        if (errNone != err)
        {
            DMSG("NetLibDispose(): NetLibClose() returned error (ignored): "); DNUM(err); DENDL;
        }
        netLibOpen = false;
    }
    if (netLibLoaded)
    {
        DMSG("NetLibDispose(): calling SysLibRemove()"); DENDL;
        err = SysLibRemove(netLibRefNum);
        if (errNone != err)
        {
            DMSG("NetLibDispose(): SysLibRemove(netLibRefNum) returned error (ignored): "); DNUM(err); DENDL;
        }
        netLibLoaded = false;
    }
    netLibRefNum = sysInvalidRefNum;
    DMSG("NetLibDispose(): exit"); DENDL;
}

Err FlickrSocketContext::Reset()
{
    DisposeSession();
    return InitSession();
}

FlickrSocketContext::~FlickrSocketContext()
{
    DisposeSession();
    if (NULL != progress)
    {
        PrgStopDialog(progress, false);
        progress = NULL;
    }   
}

Err FlickrSocketContext::InitSession()
{
    stage = stageReadingImageData;
    fileName[0] = chrNull;
    sent = 0;
    imageSize = 0;
    requestSize = 0;
    responseSize = 0;
    return errNone;
}

void FlickrSocketContext::DisposeSession()
{
    if (NULL != imageData)
    {
        MemPtrFree(imageData);
        imageData = NULL;
        imageSize = 0;
    }
    DisposeRequest();
    NetLibDispose();
}

void FlickrSocketContext::DisposeRequest()
{
    Err err = errNone;
    if (-1 != netSocket)
    {
        DMSG("DisposeRequest(): calling NetLibSocketClose()"); DENDL;
        Int16 res = NetLibSocketClose(netLibRefNum, netSocket, FLICKR_NET_CLOSE_TIMEOUT, &err);
        if (-1 == res)
        {
            DMSG("NetLibDispose(): NetLibSocketClose() returned error (ignored): "); DNUM(err); DENDL;
        }
        netSocket = -1;
    }
    
    if (NULL != requestData)
    {
        MemPtrFree(requestData);
        requestData = NULL;
        requestSize = 0;
    }
    if (NULL != responseData)
    {
        MemPtrFree(responseData);
        responseData = NULL;
        responseSize = 0;
    }
    sent = 0;
}

FlickrDbOpen::FlickrDbOpen():
    dbRef(DmOpenDatabaseByTypeCreator(FlickrTypeID, FlickrCreatorID, dmModeReadOnly))
{    
    if (0 == dbRef)
    {
        DMSG("FlickrAlert() unable to open resource database; error: "); DNUM(DmGetLastErr()); DENDL;
    }
}
