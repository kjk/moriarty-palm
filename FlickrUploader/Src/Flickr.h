/*
 * Flickr.h
 *
 * public header for shared library
 *
 * This wizard-generated code is based on code adapted from the
 * SampleLib project distributed as part of the Palm OS SDK 4.0,
 *
 * Copyright (c) 1994-1999 Palm, Inc. or its subsidiaries.
 * All rights reserved.
 */

#ifndef FLICKR_H_
#define FLICKR_H_

/* Palm OS common definitions */
#include <ExgLib.h>
#include <SystemMgr.h>

/*********************************************************************
 * Type and creator of Sample Library database
 *********************************************************************/
#define         FlickrVersion      0x0100

#define		FlickrCreatorID	'FlcK'
#define		FlickrTypeID		sysFileTExgLib
#define         FlickrTitle                 "flickr (InfoMan)"

/*********************************************************************
 * Internal library name which can be passed to SysLibFind()
 *********************************************************************/
 
#define		FlickrName		"IM FlickrUploader-FlcK"

#define         flickrDefaultTag "\"from arslexis infoman\""

enum FlickrUploadError
{
    flickrUploadErrorInvalidLogin = 1,
    flickrUploadErrorNoPhoto,
    flickrUploadErrorGeneralUploadFailure,
    flickrUploadErrorFileSizeZero,
    flickrUploadErrorFileTypeNotRecognized,
    flickrUploadErrorExceededUploadLimit
};    

enum FlickrErr {
    flickrErrParam = (appErrorClass | 1),
    flickrErrNotOpen,
    flickrErrStillOpen,
    flickrErrHttpUnsupportedResponse,
    

    flickrErrUploadUnknown,
    flickrErrUploadBase = flickrErrUploadUnknown,
    flickrErrUploadInvalidLogin,
    flickrErrUploadNoPhoto,
    flickrErrUploadGeneralFailure,
    flickrErrUploadFileSizeZero,
    flickrErrUploadFileTypeNotRecognized,
    flickrErrUploadExceededUploadLimit
};    

enum FlickrControlOperation {
    flickrCtlLibraryVersion = exgLibCtlSpecificOp,
    flickrCtlInitializePrefs
};

/*********************************************************************
 * API Prototypes
 *********************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

#if EMULATION_LEVEL != EMULATION_NONE
// Private entrypoint used by simulator to install library
Err	PrvInstallHostTransferDispatcher(UInt16 refNum, SysLibTblEntryType *entryP);
#endif

/* Standard library open, close, sleep and wake functions */

extern Err FlickrOpen(UInt16 refNum);
				
extern Err FlickrClose(UInt16 refNum);

extern Err FlickrSleep(UInt16 refNum);

extern Err FlickrWake(UInt16 refNum);

/* Custom library API functions */

//	Handle events that this library needs. This will be called by
//	sysHandle event when certain low level events are triggered.					
extern Boolean FlickrHandleEvent(UInt16 libRefnum, void *eventP);
						
//  Establish a new connection 						
extern Err FlickrConnect(UInt16 libRefNum, ExgSocketType *exgSocketP);

// Accept a connection request from remote end
extern Err FlickrAccept(UInt16 libRefnum, ExgSocketType *exgSocketP);

// Disconnect
extern Err FlickrDisconnect(UInt16 libRefnum, ExgSocketType *exgSocketP, Err error);

// Initiate a Put command. This passes the name and other information about
// an object to be sent
extern Err FlickrPut(UInt16 libRefnum, ExgSocketType *exgSocketP);

// Initiate a Get command. This requests an object from the remote end.
extern Err FlickrGet(UInt16 libRefNum, ExgSocketType *exgSocketP);

// Send data to remote end - called after a Put command
extern UInt32 FlickrSend(UInt16 libRefNum, ExgSocketType *exgSocketP, const void *bufP, UInt32 bufLen, Err *errP);

// Receive data from remote end -- called after Accept
extern UInt32 FlickrReceive(UInt16 libRefNum, ExgSocketType *exgSocketP, void *bufP, UInt32 bufSize, Err *errP);

// Send various option commands to the Exg library
extern Err FlickrControl(UInt16 libRefNum, UInt16 op, void *valueP, UInt16 *valueLenP);

// Tell the Exg library to check for incoming data
extern Err FlickrRequest(UInt16 libRefNum, ExgSocketType *socketP);

#ifdef __cplusplus
}

struct FlickrPrefs
{

    enum {
        maxEmailLength = 255,
        maxPasswordLength = 31,
        maxDescriptionLength = 511,
        maxTagsLength = 255
    };
    
    char email[maxEmailLength + 1];
    char password[maxPasswordLength + 1];
    char description[maxDescriptionLength + 1];
    char tags[maxTagsLength + 1];
    
    bool registered;
    bool useCustomPrivacySettings;
    bool isPublic;
    bool isFriend;
    bool isFamily;
    bool dontShowUploadCompletedForm;
    
    UInt32 uploadedPicturesCount;
    
};

enum 
{
    flickrPrefsResourceID = 0,
    flickrPrefsVersion = 1
};

#endif

#endif /* FLICKR_H_ */
