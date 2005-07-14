/*
 * FlickrPrivate.h
 *
 * header for implementation for shared library
 *
 * This wizard-generated code is based on code adapted from the
 * SampleLib project distributed as part of the Palm OS SDK 4.0.
 *
 * Copyright (c) 1994-1999 Palm, Inc. or its subsidiaries.
 * All rights reserved.
 */
 
#ifndef FLICKRPRIVATE_H_
#define FLICKRPRIVATE_H_

#include "FlickrCrtSupport.h"
#include "Flickr.h"

/*********************************************************************
 * Private Structures
 *********************************************************************/
 
enum FlickrTransferStage
{
    transferStageInvalid
};

/* Library globals */

struct FlickrGlobals
{
    /* our library reference number (for convenience and debugging) */
    UInt16 thisLibRefNum;

    /* library open count */
    Int16 openCount;
    
    /* TODO: add other library globals here */

    Err Init(UInt16 refNum);

    void Dispose();

};

FlickrGlobals* PrvMakeGlobals(UInt16 refNum);
void PrvFreeGlobals(UInt16 refNum);
FlickrGlobals* PrvLockGlobals(UInt16 refNum);
Boolean PrvIsLibOpen(UInt16 refNum);
#define PrvUnlockGlobals(gP)        MemPtrUnlock(gP)

void FlickrSavePrefs(const FlickrPrefs& prefs);

class FlickrGlobalsPtr
{
    FlickrGlobals* pointer_;
public:

    explicit FlickrGlobalsPtr(UInt16 refNum): pointer_(PrvLockGlobals(refNum)) {}
    
    FlickrGlobalsPtr(FlickrGlobals* pointer): pointer_(pointer) {}
    
    bool Valid() const {return NULL != pointer_;}
    
    void Unlock() {if (NULL != pointer_) PrvUnlockGlobals(pointer_); pointer_ = NULL;}
    
    ~FlickrGlobalsPtr() {Unlock();}
    
    operator FlickrGlobals*() {return pointer_;}
    operator const FlickrGlobals*() const {return pointer_;}

    FlickrGlobals& operator* () {return *pointer_;}
    const FlickrGlobals& operator* () const {return *pointer_;}
    
    FlickrGlobals* operator->() {return pointer_;}
    const FlickrGlobals* operator->() const {return pointer_;}
    
};

enum FlickrExchangeStage
{
    stageReadingImageData,
    stageResolvingHostAddress,
    stageOpeningConnection,
    stageUploadingImage,
    stageReadingResponse,
    stageFinished
};    

struct FlickrSocketContext
{
private:

    Err InitSession();

public:

    static const UInt32 magicValue = 0x3141592F;
    UInt32 magic;
    UInt16 libRefNum;
    FlickrPrefs prefs;
    
    void* imageData;
    UInt32 imageSize;
    
    UInt16 stage;    
    
    ProgressPtr progress;
    
    NetIPAddr flickrAddress;
    
    NetSocketRef netSocket;
    
    UInt16 netLibRefNum;
    
    bool netLibLoaded;
    bool netLibOpen;
    
    void* requestData;
    UInt32 requestSize;
    UInt32 sent;
    UInt16 chunkSize;
    
    void* responseData;
    UInt32 responseSize;
    
    enum {
        maxFileNameLength = 255,
        maxContentTypeLength = 63
    };
    
    char fileName[maxFileNameLength + 1];
    char contentType[maxContentTypeLength + 1];
    
    bool toggle;
    UInt32 lastAnimationTicks;
    
    FlickrSocketContext(UInt16 libRef);
    
    ~FlickrSocketContext();
    
    Err Init();
    
    Err NetLibInit();
    
    void NetLibDispose();

    void DisposeSession();

    void DisposeRequest();
    
    Err Reset();
    
};

Err PrvProcessEvents(FlickrSocketContext& context, UInt16 timeout);
void PrvUpdateProgress(FlickrSocketContext& context, Err error);

#define FLICKR_NET_CLOSE_TIMEOUT (SysTicksPerSecond() * 5)
#define FLICKR_RESOLVE_TIMEOUT (SysTicksPerSecond() * 30)
#define FLICKR_SOCKET_OPEN_TIMEOUT (SysTicksPerSecond() * 5)
#define FLICKR_SOCKET_CONNECT_TIMEOUT (SysTicksPerSecond() * 30)
#define FLICKR_SEND_TIMEOUT                     (SysTicksPerSecond() * 5)

#define FLICKR_PROGRESS_ANIMATION_TIMEOUT (SysTicksPerSecond() / 2)

#define FLICKR_SELECT_TIMEOUT                   FLICKR_PROGRESS_ANIMATION_TIMEOUT

struct FlickrDbOpen
{
    DmOpenRef dbRef;
    
    FlickrDbOpen();
    
    ~FlickrDbOpen() {if (0 != dbRef) DmCloseDatabase(dbRef);}

};

void* PrvRealloc(void* p, UInt32 newSize);

#endif /* FLICKRPRIVATE_H_ */
