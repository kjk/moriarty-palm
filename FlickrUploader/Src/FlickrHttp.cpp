#include "FlickrHttp.h"
#include "FlickrDbg.h"
#include "FlickrPrivate.h"

static void HttpPrepareBoundary(char* buffer, const FlickrSocketContext& context)
{
    // TODO: verify that boundary is not found within imageData
    Int16 val = SysRandom(TimGetTicks());
    for (int i = 0; i < 4; ++i)
    {
        StrPrintF(buffer, "%hx", val);
        buffer += 4;
        val = SysRandom(0);
    }
}

#define FLICKR_ADDRESS "www.flickr.com"

#define HTTP_BOUNDARY_START "---------------------------"
#define HTTP_BOUNDARY_RANDOM_PART_LENGTH 16
#define HTTP_BOUNDARY_END "--"

#define HTTP_LINE_BREAK "\r\n"

#define HTTP_PART_START "\r\n" \
"Content-Disposition: form-data; name=\""
#define HTTP_PART_FILENAME "; filename=\""
#define HTTP_PART_BREAK "\r\n\r\n"
#define HTTP_PART_QUOTE_END "\""

#define HTTP_CONTENT_TYPE "\r\n" \
"Content-Type: "
#define HTTP_CONTENT_XFER_ENCODING_BINARY "\r\n" \
"Content-Transfer-Encoding: binary"

static void PrvAppendData(char*& p, const char* data, long dataLength = -1)
{
    if (-1 == dataLength)
        dataLength = StrLen(data);
    MemMove(p, data, dataLength);
    p += dataLength;
}

static UInt32 HttpPartLength(const char* name, const char* fileName, const char* contentType, const char* data, long dataLength)
{
    UInt32 length = StrLen(HTTP_BOUNDARY_START);
    length += StrLen(HTTP_BOUNDARY_END);
    length += HTTP_BOUNDARY_RANDOM_PART_LENGTH;
    length += StrLen(HTTP_PART_START);
    length += StrLen(name);
    length += StrLen(HTTP_PART_QUOTE_END);
    if (NULL != fileName)
    {
        length += StrLen(HTTP_PART_FILENAME);
        length += StrLen(fileName);
        length += StrLen(HTTP_PART_QUOTE_END);
    }
    if (NULL != contentType)
    {
        length += StrLen(HTTP_CONTENT_TYPE);
        length += StrLen(contentType);
    }
    length += StrLen(HTTP_CONTENT_XFER_ENCODING_BINARY);
    length += StrLen(HTTP_PART_BREAK);
    if (-1 == dataLength)
        dataLength = StrLen(data);
        
    length += dataLength;
    length += StrLen(HTTP_LINE_BREAK);
    return length;
}

static void HttpPreparePart(char*& p, const char* boundary, const char* name, const char* fileName, const char* contentType, const char* data, long dataLength)
{
    const char* start = p;
    PrvAppendData(p, HTTP_BOUNDARY_START);
    PrvAppendData(p, HTTP_BOUNDARY_END);
    PrvAppendData(p, boundary);
    PrvAppendData(p, HTTP_PART_START);
    PrvAppendData(p, name);
    PrvAppendData(p, HTTP_PART_QUOTE_END);
    if (NULL != fileName)
    {
        PrvAppendData(p, HTTP_PART_FILENAME);
        PrvAppendData(p, fileName);
        PrvAppendData(p, HTTP_PART_QUOTE_END);
    }
    if (NULL != contentType)
    {
        PrvAppendData(p, HTTP_CONTENT_TYPE);
        PrvAppendData(p, contentType);
    }
    PrvAppendData(p, HTTP_CONTENT_XFER_ENCODING_BINARY);
    PrvAppendData(p, HTTP_PART_BREAK);
    if (-1 == dataLength)
        dataLength = StrLen(data);
     
    PrvAppendData(p, data, dataLength);
    PrvAppendData(p, HTTP_LINE_BREAK);
    assert(p - start == HttpPartLength(name, fileName, contentType, data, dataLength));
}

static UInt32 HttpCalculateContentLength(const FlickrSocketContext& context)
{
    UInt32 length = 0;
    length += HttpPartLength("email", NULL, NULL, context.prefs.email, -1);
    length += HttpPartLength("password", NULL, NULL, context.prefs.password, -1);
    if (0 != StrLen(context.prefs.description))
        length += HttpPartLength("description", NULL, NULL, context.prefs.description, -1);
    if (0 != StrLen(context.prefs.tags))
        length += HttpPartLength("tags", NULL, NULL, context.prefs.tags, -1);
    length += HttpPartLength("photo", context.fileName, context.contentType, NULL, context.imageSize);
    
    if (context.prefs.useCustomPrivacySettings)
    {
        length += HttpPartLength("is_public", NULL, NULL, NULL, 1);
        length += HttpPartLength("is_friend", NULL, NULL, NULL, 1);
        length += HttpPartLength("is_family", NULL, NULL, NULL, 1);
    }
    
    length += StrLen(HTTP_BOUNDARY_START);
    length += StrLen(HTTP_BOUNDARY_END);
    length += HTTP_BOUNDARY_RANDOM_PART_LENGTH;
    length += StrLen(HTTP_BOUNDARY_END);
    return length;
}

static Err HttpPrepareContent(char*& p, const char* boundary, const FlickrSocketContext& context)
{
    HttpPreparePart(p, boundary, "email", NULL, NULL, context.prefs.email, -1);
    HttpPreparePart(p, boundary, "password", NULL, NULL, context.prefs.password, -1);
    if (0 != StrLen(context.prefs.description))
        HttpPreparePart(p, boundary, "description", NULL, NULL, context.prefs.description, -1);
    if (0 != StrLen(context.prefs.tags))
        HttpPreparePart(p, boundary, "tags", NULL, NULL, context.prefs.tags, -1);
    HttpPreparePart(p, boundary, "photo", context.fileName, context.contentType, (const char*)context.imageData, context.imageSize);
    
    if (context.prefs.useCustomPrivacySettings)
    {
        HttpPreparePart(p, boundary, "is_public", NULL, NULL, context.prefs.isPublic ? "1" : "0", 1);
        HttpPreparePart(p, boundary, "is_friend", NULL, NULL, context.prefs.isFriend ? "1" : "0", 1);
        HttpPreparePart(p, boundary, "is_family", NULL, NULL, context.prefs.isFamily ? "1" : "0", 1);
    }
    
    PrvAppendData(p, HTTP_BOUNDARY_START);
    PrvAppendData(p, HTTP_BOUNDARY_END);
    PrvAppendData(p, boundary);
    PrvAppendData(p, HTTP_BOUNDARY_END);
    return errNone;            
}

#define HTTP_HEADERS_PART1 \
"POST /tools/uploader_go.gne HTTP/1.1\r\n" \
"Connection: close\r\n" \
"Host: " FLICKR_ADDRESS "\r\n" \
"Content-Type: multipart/form-data; boundary=" HTTP_BOUNDARY_START

#define HTTP_HEADERS_PART2 "\r\n" \
"Content-Length: "

static UInt32 HttpCalculateRequestLength(const FlickrSocketContext& context, UInt32& contentLength)
{
    UInt32 cl = contentLength = HttpCalculateContentLength(context);
    char buffer[12] = {chrNull};
    StrPrintF(buffer, "%ld", cl);

    UInt32 length = 0;
    length += StrLen(HTTP_HEADERS_PART1);
    length += HTTP_BOUNDARY_RANDOM_PART_LENGTH;
    length += StrLen(HTTP_HEADERS_PART2);
    length += StrLen(buffer);
    length += 2 * StrLen(HTTP_LINE_BREAK);
    length += cl;
    return length;
}

static void HttpPrepareHeaders(char*& p, const char* boundary, UInt32 contentLength)
{
    PrvAppendData(p, HTTP_HEADERS_PART1);
    PrvAppendData(p, boundary);
    PrvAppendData(p, HTTP_HEADERS_PART2);
    
    char buffer[12] = {chrNull};
    StrPrintF(buffer, "%ld", contentLength);
    PrvAppendData(p, buffer);
    PrvAppendData(p, HTTP_LINE_BREAK);
    PrvAppendData(p, HTTP_LINE_BREAK);
}

Err HttpPrepareRequest(FlickrSocketContext& context)
{
    DMSG("HttpPrepareRequest() enter"); DENDL;
    
    char boundary[HTTP_BOUNDARY_RANDOM_PART_LENGTH + 1];
    HttpPrepareBoundary(boundary, context);
    DMSG("HttpPrepareRequest(): boundary: "); DMSG(boundary); DENDL;
    
    UInt32 contentLength;
    UInt32 length = HttpCalculateRequestLength(context, contentLength);
    context.requestData = PrvRealloc(context.requestData, length);
    if (NULL == context.requestData)
    {
        DMSG("HttpPrepareRequest(): PrvRealloc() failed; size: "); DNUM(length); DENDL;
        return exgMemError;
    }
    MemPtrSetOwner(context.requestData, 0);
    context.requestSize = length;
    
    char* start = (char*)context.requestData;
    char* p = start;
    HttpPrepareHeaders(p, boundary, contentLength);
    
    const char* content = p;
    Err err = HttpPrepareContent(p, boundary, context);
    assert(p - content == contentLength);
    assert(p - start == length);

    HostFILEType* f = HostFOpen("c:\\flickr_request.txt", "w");
    if (NULL != f)
    {
        HostFWrite(start, length, 1, f);
        HostFFlush(f);
        HostFClose(f);
    }
    return err;
}


Err FlickrAddressResolve(FlickrSocketContext& context)
{
    DMSG("FlickrAddressResolve(): enter"); DENDL;
    
    context.stage = stageResolvingHostAddress;
    PrvUpdateProgress(context, errNone);
    Err err = PrvProcessEvents(context, 0);
    if (errNone != err)
    {
        DMSG("FlickrAddressResolve(): PrvProcessEvents() returned error: "); DNUM(err); DENDL;
        return err;
    }

    NetHostInfoBufType* buffer = new NetHostInfoBufType;
    if (NULL == buffer)
    {
        DMSG("FlickrAddressResolve(): unable to allocate NetHostInfoBufType"); DENDL;
        return exgMemError;
    }   
    MemSet(buffer, sizeof(*buffer), 0);        
    
    NetHostInfoType* hostInfo = NetLibGetHostByName(context.netLibRefNum, FLICKR_ADDRESS, buffer, FLICKR_RESOLVE_TIMEOUT, &err);
    if (NULL != hostInfo && errNone == err)
    {
        assert(netSocketAddrINET == hostInfo->addrType);
        assert(sizeof(NetIPAddr) == hostInfo->addrLen);
        context.flickrAddress = buffer->address[0];
#ifndef NDEBUG        
        char addrText[16];
        DMSG("FlickrAddressResolve(): NetLibGetHostByName() finished; address: "); DMSG(NetLibAddrINToA(context.netLibRefNum, context.flickrAddress, addrText)); DENDL;
#endif        
    }
    delete buffer;
    DMSG("FlickrAddressResolve(): exit; error: "); DNUM(err); DENDL;
    return err;
}

static Err FlickrPrepareSocket(FlickrSocketContext& context)
{
    DMSG("FlickrPrepareSocket() enter"); DENDL;
    assert(NULL != context.requestData);
    assert(-1 == context.netSocket);
    context.stage = stageOpeningConnection;
    PrvUpdateProgress(context, errNone);
    Err err = PrvProcessEvents(context, 0);
    if (errNone != err)
    {
        DMSG("FlickrPrepareSocket(): PrvProcessEvents() (0) returned error: "); DNUM(err); DENDL;
        return err;
    }    

    context.netSocket = NetLibSocketOpen(context.netLibRefNum, netSocketAddrINET, netSocketTypeStream, netSocketProtoIPTCP, FLICKR_SOCKET_OPEN_TIMEOUT, &err);
    if (-1 == context.netSocket)
    {
        DMSG("FlickrPrepareSocket(): NetLibSocketOpen() returned error: "); DNUM(err); DENDL;
        return err;
    }    
    
    err = PrvProcessEvents(context, 0);
    if (errNone != err)
    {
        DMSG("FlickrPrepareSocket(): PrvProcessEvents() (1) returned error: "); DNUM(err); DENDL;
        return err;
    }    
    Int16 res;
/*
    bool val = true;        
    res = NetLibSocketOptionSet(context.netLibRefNum, context.netSocket, netSocketOptLevelSocket, netSocketOptSockNonBlocking, &val, sizeof(val), -1, &err);
    if (-1 == res)
    {
        if (netErrUnimplemented != err)
        {
            DMSG("FlickrPrepareSocket(): NetLibSocketOptionSet(nonBlocking) returned error: "); DNUM(err); DENDL;
            return err;
        }
        else
        {
            DMSG("FlickrPrepareSocket(): NetLibSocketOptionSet(nonBlocking) returned netErrUnimplemented"); DENDL;
        }
    }

    NetSocketLingerType linger;
    linger.onOff = true;
    linger.time = 0;
    
    res = NetLibSocketOptionSet(context.netLibRefNum, context.netSocket, netSocketOptLevelSocket, netSocketOptSockLinger, &linger, sizeof(linger), -1, &err);
    if (-1 == res)
    {
        if (netErrUnimplemented != err)
        {
            DMSG("FlickrPrepareSocket(): NetLibSocketOptionSet(linger) returned error: "); DNUM(err); DENDL;
            return err;
        }
        else
        {
            DMSG("FlickrPrepareSocket(): NetLibSocketOptionSetlinger() returned netErrUnimplemented"); DENDL;
        }
    }
  */
    
  
    err = PrvProcessEvents(context, 0);
    if (errNone != err)
    {
        DMSG("FlickrPrepareSocket(): PrvProcessEvents() (2) returned error: "); DNUM(err); DENDL;
        return err;
    }    

    NetSocketAddrINType addr = {netSocketAddrINET, NetHToNS(80), NetHToNL(context.flickrAddress)};

    res = NetLibSocketConnect(context.netLibRefNum, context.netSocket, (NetSocketAddrType*)&addr, sizeof(addr), FLICKR_SOCKET_CONNECT_TIMEOUT, &err);
    if (netErrWouldBlock == err)
    {
        DMSG("FlickrPrepareSocket(): NetLibSocketConnect() returned netErrWouldBlock"); DENDL;
        err = errNone;
    }        
    if (-1 == res && errNone != err)
    {
        DMSG("FlickrPrepareSocket(): NetLibSocketConnect() returned error: "); DNUM(err); DENDL;
        return err;
    }
    
    err = PrvProcessEvents(context, 0);
    if (errNone != err)
    {
        DMSG("FlickrPrepareSocket(): PrvProcessEvents() (3) returned error: "); DNUM(err); DENDL;
        return err;
    }    
    
    DMSG("FlickrPrepareSocket(): exit"); DENDL;
    return errNone;
}

static Err FlickrSendRequest(FlickrSocketContext& context);
static Err FlickrReceiveResponse(FlickrSocketContext& context);
static Err FlickrCheckSocketError(FlickrSocketContext& context);

static Err FlickrHandleConnectionEvents(FlickrSocketContext& context)
{
    DMSG("FlickrHandleConnectionEvents() enter"); DENDL;
    Err err;
    NetFDSetType readFds, writeFds, exceptFds;
    
    context.stage = stageUploadingImage;
    PrvUpdateProgress(context, errNone);
    err = PrvProcessEvents(context, 0);
    if (errNone != err)
    {
        DMSG("FlickrHandleConnectionEvents(): PrvProcessEvents() (0) returned error: "); DNUM(err); DENDL;
        return err;
    }    
    
    while (true)
    {
        netFDZero(&readFds); netFDZero(&writeFds); netFDZero(&exceptFds); 
        netFDSet(sysFileDescStdIn, &readFds);
        
        if (stageUploadingImage == context.stage)
            netFDSet(context.netSocket, &writeFds);
        else if (stageReadingResponse == context.stage)
            netFDSet(context.netSocket, &readFds);
        else
        {
            err = PrvProcessEvents(context, 0);
            if (errNone != err)
            {
                DMSG("FlickrHandleConnectionEvents(): PrvProcessEvents() (1) returned error: "); DNUM(err); DENDL;
                return err;
            }    
            break;
        }            

        UInt16 width = sysFileDescStdIn;
        if (context.netSocket > width)
            width = context.netSocket;

        ++width;

        Int16 numSockets = NetLibSelect(context.netLibRefNum, width, &readFds, &writeFds, &exceptFds, FLICKR_SELECT_TIMEOUT, &err);
        if (-1 == numSockets)
        {
            if (netErrTimeout == err)
            {
                DMSG("FlickrHandleConnectionEvents(): NetLibSelect() returned netErrTimeout"); DENDL;
                err = PrvProcessEvents(context, 0);
                if (errNone == err)
                    continue;
            }                
            if (errNone != err)
            {
                DMSG("FlickrHandleConnectionEvents(): NetLibSelect() returned error: "); DNUM(err); DENDL;
                return err;
            }                
        }
    
        if (netFDIsSet(sysFileDescStdIn, &readFds))
        {
            DMSG("FlickrHandleConnectionEvents(): input event"); DENDL;
            err = PrvProcessEvents(context, 0);
            if (errNone != err)
            {
                DMSG("FlickrHandleConnectionEvents(): PrvProcessEvents() (2) returned error: "); DNUM(err); DENDL;
                return err;
            }
            continue;
        }
        
        if (netFDIsSet(context.netSocket, &readFds))
        {
            DMSG("FlickrHandleConnectionEvents(): socket is readable"); DENDL;
            err = FlickrCheckSocketError(context);
            if (errNone != err)
            {
                DMSG("FlickrHandleConnectionEvents(): FlickrCheckSocketError() returned error: "); DNUM(err); DENDL;
                return err;
            }                
            err = FlickrReceiveResponse(context);
            if (errNone != err)
            {
                DMSG("FlickrHandleConnectionEvents(): FlickrReceiveResponse() returned error: "); DNUM(err); DENDL;
                return err;
            }
        }

        if (netFDIsSet(context.netSocket, &writeFds))
        {
            DMSG("FlickrHandleConnectionEvents(): socket is writable"); DENDL;
            err = FlickrCheckSocketError(context);
            if (errNone != err)
            {
                DMSG("FlickrHandleConnectionEvents(): FlickrCheckSocketError() returned error: "); DNUM(err); DENDL;
                return err;
            }                
            err = FlickrSendRequest(context);
            if (errNone != err)
            {
                DMSG("FlickrHandleConnectionEvents(): FlickrSendRequest() returned error: "); DNUM(err); DENDL;
                return err;
            }           
        }

        err = PrvProcessEvents(context, 0);
        if (errNone != err)
        {
            DMSG("FlickrHandleConnectionEvents(): PrvProcessEvents(3) returned error: "); DNUM(err); DENDL;
            return err;
        }
    }    
    DMSG("FlickrHandleConnectionEvents(): exit"); DENDL;
    return errNone;
}

Err FlickrPerformConnection(FlickrSocketContext& context)
{
    Err err = FlickrPrepareSocket(context);
    if (errNone != err)
        return err;

    return FlickrHandleConnectionEvents(context);
}

Err FlickrSendRequest(FlickrSocketContext& context)
{
    assert(stageUploadingImage == context.stage);
    assert(NULL != context.requestData);
    UInt32 total = context.requestSize;
    char* data = (char*)context.requestData;
    data += context.sent;
    
    UInt16 size = context.chunkSize;
    UInt32 rest = total - context.sent;
    if (size > rest)
        size = rest;
        
    Err err;
    Int16 res = NetLibSend(context.netLibRefNum, context.netSocket, data, size, 0, NULL, 0, FLICKR_SEND_TIMEOUT, &err);

    if (-1 == res)
    {
        DMSG("FlickrSendRequest(): NetLibSend() returned error: "); DNUM(err); DENDL;
        return err;
    }
    
    if (0 == res)
    {
        DMSG("FlickrSendRequest(): socket shut down by remote host; error: "); DNUM(err); DENDL;
        return netErrSocketInputShutdown;
    }
    
    context.sent += res;
    
    PrvUpdateProgress(context, errNone);
    err = PrvProcessEvents(context, 0);
    if (errNone != err)
    {
        DMSG("FlickrSendRequest(): PrvProcessEvents() (0) returned error: "); DNUM(err); DENDL;
        return err;
    }    
    
    if (total == context.sent)
    {
        DMSG("FlickrSendRequest(): whole data sent, switching to reading response"); DENDL;
        context.stage = stageReadingResponse;

        context.requestData = PrvRealloc(context.requestData, 0); 
        context.requestSize = 0;

        res = NetLibSocketShutdown(context.netLibRefNum, context.netSocket, netSocketDirOutput, -1, &err);
        if (-1 == res)
        {
            DMSG("FlickrSendRequest(): NetLibSocketShutdown() returned error (ignored): "); DNUM(err); DENDL;
        }
      
        PrvUpdateProgress(context, errNone);
        err = PrvProcessEvents(context, 0);
        if (errNone != err)
        {
            DMSG("FlickrSendRequest(): PrvProcessEvents() (1) returned error: "); DNUM(err); DENDL;
            return err;
        }    
    }
    return errNone;
}

static void LogResponseToMemo(const FlickrSocketContext& context);

static Err FlickrParseResponse(FlickrSocketContext& context)
{
    const char* data = (const char*)context.responseData;
    if (NULL == data)
    {
        DMSG("FlickrParseResponse(): responseData is NULL"); DENDL;
        return flickrErrHttpUnsupportedResponse;
    }

#ifndef NDEBUG
    LogResponseToMemo(context);
#endif    

    const char* p = StrStr(data, "HTTP/1.1 200 OK");
    if (NULL == p)
    {
        DMSG("FlickrParseResponse(): HTTP/1.1 200 OK not found"); DENDL;
        return flickrErrHttpUnsupportedResponse;
    }        
    
    p = StrStr(data, "<status>fail</status>");
    if (NULL != p)
    {
        p = StrStr(p, "<error>");
        if (NULL == p)
            return flickrErrUploadUnknown;
        
        p += StrLen("<error>");
        const char* end = StrStr(p, "</error>");
        if (NULL == end)
            return flickrErrUploadUnknown;
    
        if (end - p > 7)
            return flickrErrUploadUnknown;
        
        char buffer[8];
        StrNCopy(buffer, p, end - p);
        buffer[end - p] = chrNull;
        Int32 num = StrAToI(buffer);
        if (num < 0)
            return flickrErrUploadUnknown;
        
        return flickrErrUploadBase + num;
    }

    p = StrStr(data, "<status>ok</status>");
    if (NULL == p)
    {
        DMSG("FlickrParseResponse(): <status>ok</status> not found"); DENDL;
        return flickrErrUploadUnknown;
    }
    ++context.prefs.uploadedPicturesCount;
    FlickrSavePrefs(context.prefs);
    return errNone;
}

Err FlickrReceiveResponse(FlickrSocketContext& context)
{
//    DMSG("FlickrReceiveResponse(): enter"); DENDL;
    
    if (stageReadingResponse != context.stage)
    {
        DMSG("FlickrReceiveResponse(): invalid stage: "); DNUM(context.stage); DENDL;
        context.stage = stageReadingResponse;
    }
    
    Err err = errNone;
    void* buffer = MemPtrNew(context.chunkSize);
    if (NULL == buffer)
    {
        err = exgMemError;
        goto Finish;
    }                
        
    char* p = NULL;
    Int16 res = NetLibReceive(context.netLibRefNum, context.netSocket, buffer, context.chunkSize, 0, NULL, 0, FLICKR_SEND_TIMEOUT, &err);

    if (-1 == res)
    {
        DMSG("FlickrReceiveResponse(): NetLibReceive() returned error: "); DNUM(err); DENDL;
        goto Finish;
    }
    
    if (0 == res)
    {
        DMSG("FlickrReceiveResponse(): socket shut down by remote host; error: "); DNUM(err); DENDL;
        context.stage = stageFinished;
        
        res = NetLibSocketShutdown(context.netLibRefNum, context.netSocket, netSocketDirInput, -1, &err);
        if (-1 == res)
        {
            DMSG("FlickrReceiveResponse(): NetLibSocketShutdown() returned error (ignored): "); DNUM(err); DENDL;
            err = errNone;
        }
        
        err = FlickrParseResponse(context);
        goto Finish;
    }

    context.responseData = PrvRealloc(context.responseData, context.responseSize + res + 1);
    if (NULL == context.responseData)
    {
        DMSG("FlickrReceiveResponse(): PrevRealloc() failed; size: "); DNUM(context.responseSize + res + 1); DENDL;
        err = exgMemError;
        goto Finish;
    }
    MemPtrSetOwner(context.responseData, 0);
    p = (char*)context.responseData;
    p += context.responseSize;
    MemMove(p, buffer, res);
    p[res] = chrNull;
    context.responseSize += res;

#ifndef NDEBUG
    HostFILEType* f = HostFOpen("c:\\flickr_response.txt", "w");
    if (NULL != f)
    {
        HostFWrite(p, res, 1, f);
        HostFFlush(f);
        HostFClose(f);
    }
#endif    

Finish:    

    PrvUpdateProgress(context, err);
    err = PrvProcessEvents(context, 0);
    if (errNone != err)
    {
        DMSG("FlickrReceiveResponse(): PrvProcessEvents() returned error: "); DNUM(err); DENDL;
    }    

    if (NULL != buffer)
        MemPtrFree(buffer);

    DMSG("FlickrReceiveResponse(): exit; error: "); DNUM(err); DENDL;
    return err;
}

static Err FlickrCheckSocketError(FlickrSocketContext& context)
{
    int val = 0;
    UInt16 valLen = sizeof(val);
    Err err;
    Int16 res = NetLibSocketOptionGet(context.netLibRefNum, context.netSocket, netSocketOptLevelSocket, netSocketOptSockErrorStatus, &val, &valLen, -1, &err);
    if (-1 == res)
    {
        DMSG("FlickrCheckSocketError(): NetLibSocketOptionGet() returned error: "); DNUM(err); DMSG("; val: "); DNUM(val); DENDL;
        return errNone;
    }
    if (errNone != val)
    {
        DMSG("FlickrCheckSocketError(): exit; error: "); DNUM(val); DENDL;
    }        
    return val;
}

#ifndef NDEBUG
void LogResponseToMemo(const FlickrSocketContext& context)
{
    DmOpenRef db = DmOpenDatabaseByTypeCreator('DATA', sysFileCMemo, dmModeReadWrite);
    if (0 == db)
        return;

    UInt16 index = dmMaxRecordIndex;
    UInt16 len = context.responseSize + 1;
    void* data = NULL;
    MemHandle handle = DmNewRecord(db, &index, len);
    if (NULL == handle)
        goto Finish;
        
    data = MemHandleLock(handle);
    if (NULL == data)
        goto Finish;

    DmWrite(data, 0, context.responseData, len);
    
Finish:
    if (NULL != data)
        MemHandleUnlock(handle);
    
    if (NULL != handle)
        DmReleaseRecord(db, index, true);

    DmCloseDatabase(db);    
}
#endif
