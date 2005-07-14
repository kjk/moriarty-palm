/*
 * FlickrImpl.c
 *
 * implementation for shared library
 *
 * This wizard-generated code is based on code adapted from the
 * SampleLib project distributed as part of the Palm OS SDK 4.0.
 *
 * Copyright (c) 1994-1999 Palm, Inc. or its subsidiaries.
 * All rights reserved.
 */

#include "Flickr.h"
#include "FlickrPrivate.h"
#include "FlickrDbg.h"
#include "FlickrRsc.h"
#include "FlickrHttp.h"
#include <MemGlue.h>

/*********************************************************************
 *
 * LIBRARY GLOBALS:
 *
 * IMPORTANT:
 * ==========
 * Libraries are *not* allowed to have global or static variables.
 * Instead, they allocate a memory chunk to hold their persistent data,
 * and save a handle to it in the library's system library table entry.
 * Example functions below demostrate how the library "globals" chunk
 * is set up, saved, and accessed.
 *
 * We use a movable memory chunk for our library globals to minimize
 * dynamic heap fragmentation.  Our library globals are locked only
 * when needed and unlocked as soon as possible.  This behavior is
 * critical for healthy system performance.
 *
 *********************************************************************/


/*********************************************************************
 * Library API Routines
 *********************************************************************/

/*
 * FUNCTION: FlickrOpen
 *
 * DESCRIPTION:
 *
 * Opens the library, creates and initializes the globals.
 * This function must be called before any other library functions.
 *
 * If FlickrOpen fails, do not call any other library API functions.
 * If FlickrOpen succeeds, call FlickrClose when you are done using
 * the library to enable it to release critical system resources.
 *
 * LIBRARY DEVELOPER NOTES:
 *
 * The library's "open" and "close" functions should *not* take an excessive
 * amount of time to complete.  If the processing time for either of these
 * is lengthy, consider creating additional library API function(s) to handle
 * the time-consuming chores.
 *
 *
 * PARAMETERS:
 *
 * refNum
 *		Library reference number returned by SysLibLoad() or SysLibFind().
 *
 * clientContextP
 *		pointer to variable for returning client context.  The client context is
 *		used to maintain client-specific data for multiple client support.  The
 *		value returned here will be used as a parameter for other library
 *		functions which require a client context.
 *
 * CALLED BY: anyone who wants to use this library
 *
 * RETURNS:
 *		errNone
 *		memErrNotEnoughSpace
 *
 */

Err FlickrOpen(UInt16 refNum)
{
    FlickrGlobals *gP;
    Err err = errNone;
    Int16 originalOpenCount = 0;

    DMSG("FlickrOpen() enter\n");

    /* Get library globals */
    gP = PrvLockGlobals(refNum);

    /* Check if already open */
    if (!gP)
    {
    	/* Allocate and initialize our library globals. */
    	gP = PrvMakeGlobals(refNum);
    	if ( !gP )
    		err = memErrNotEnoughSpace;
    }

    /* If we have globals, create a client context, increment open
     * count, and unlock our globals */
    if ( gP )
    {
    	originalOpenCount = gP->openCount;
    	if ( !err )
    		gP->openCount++;

    	PrvUnlockGlobals(gP);

    	/* If there was an error creating a client context and there  */
    	/* are no other clients, free our globals */
    	if ( err && (originalOpenCount == 0) )
    		PrvFreeGlobals(refNum);
    }

    DMSG("FlickrOpen() exit\n");
    return err;
}

/*
 * FUNCTION: FlickrClose
 *
 * DESCRIPTION:
 *
 * Closes the library, frees client context and globals.
 *
 * ***IMPORTANT***
 * May be called only if FlickrOpen succeeded.
 *
 * If other applications still have the library open, decrements
 * the reference count and returns FlickrErrStillOpen.
 *
 * LIBRARY DEVELOPER NOTES:
 *
 * The library's "open" and "close" functions should *not* take an excessive
 * amount of time to complete.  If the processing time for either of these
 * is lengthy, consider creating additional library API function(s) to handle
 * the time-consuming chores.
 *
 * PARAMETERS:
 *
 * refNum
 *		Library reference number returned by SysLibLoad() or SysLibFind().
 *
 * clientContext
 *		client context
 *
 * CALLED BY: Whoever wants to close the library
 *
 * RETURNS:
 *		errNone
 *		FlickrErrStillOpen -- library is still open by others (no error)
 */

Err FlickrClose(UInt16 refNum)
{
    FlickrGlobals * gP;
    Int16 openCount;
    Err err = errNone;

    DMSG("FlickrClose() enter\n");
    gP = PrvLockGlobals(refNum);

    /* If not open, return */
    if (!gP)
    {
    	/* MUST return zero here to get around a bug in system v1.x that
    	 * would cause SysLibRemove to fail. */
    	return errNone;
    }

    /* Decrement our library open count */
    gP->openCount--;

    /* Error check for open count underflow */
    ErrFatalDisplayIf(gP->openCount < 0, "InfoMan Flickr Uploader open count underflow");

    /* Save the new open count and the context count */
    openCount = gP->openCount;

    PrvUnlockGlobals(gP);

    /* If open count reached zero, free our library globals */
    if ( openCount <= 0 )
    {
    	/* Free our library globals */
    	PrvFreeGlobals(refNum);
    }
    else
    {
    	/* return this error code to inform the caller
    	 * that others are still using this library */
    	err = flickrErrStillOpen;
    }

    DMSG("FlickrClose() exit\n");
    return err;
}

/*
 * FUNCTION: FlickrSleep
 *
 * DESCRIPTION:
 *
 * Handles system sleep notification.
 *
 * ***IMPORTANT***
 * This notification function is called from a system interrupt.
 * It is only allowed to use system services which are interrupt-
 * safe.  Presently, this is limited to EvtEnqueueKey, SysDisableInts,
 * SysRestoreStatus.  Because it is called from an interrupt,
 * it must *not* take a long time to complete to preserve system
 * integrity.  The intention is to allow system-level libraries
 * to disable hardware components to conserve power while the system
 * is asleep.
 *
 * PARAMETERS:
 *
 * refNum
 *		Library reference number returned by SysLibLoad() or SysLibFind().
 *
 * CALLED BY: System
 *
 * RETURNS:	errNone
 */

Err FlickrSleep(UInt16 refNum)
{
    #pragma unused(refNum)
    return errNone;
}

/*
 * FUNCTION: FlickrWake
 *
 * DESCRIPTION:
 *
 * Handles system wake notification.
 *
 * ***IMPORTANT***
 * This notification function is called from a system interrupt.
 * It is only allowed to use system services which are interrupt-
 * safe.  Presently, this is limited to EvtEnqueueKey, SysDisableInts,
 * SysRestoreStatus.  Because it is called from an interrupt,
 * it must *not* take a long time to complete to preserve system
 * integrity.  The intention is to allow system-level libraries
 * to enable hardware components which were disabled when the system
 * went to sleep.
 *
 * PARAMETERS:
 *
 * refNum
 *		Library reference number returned by SysLibLoad() or SysLibFind().
 *
 * CALLED BY: System
 *
 * RETURNS:	errNone
 */

Err FlickrWake(UInt16 refNum)
{
    #pragma unused(refNum)
    return errNone;
}

// ExgLibHandleEvent
Boolean FlickrHandleEvent(UInt16 libRefnum, void *eventP)
{
    DMSG("FlickrHandleEvent() enter/exit\n");
    return false;
}


Err PrvProcessEvents(FlickrSocketContext& context, UInt16 timeout)
{
    Err err = errNone;
    EventType event;

    if (timeout || EvtEventAvail())
    {
        EvtGetEvent(&event, timeout);
        if (!FlickrHandleEvent(context.libRefNum, &event) && NULL != context.progress)
            PrgHandleEvent(context.progress, &event);  // update progress before waiting...
    }
    else if (NULL != context.progress)
        PrgHandleEvent(context.progress, NULL);  // update progress without event (for animation)

    if (NULL != context.progress)
    {
        err = context.progress->error;
        // check for a user cancel and handle it...
        if (PrgUserCancel(context.progress))
            err = exgErrUserCancel;
    }
    return err;
}

// ExgLibConnect
Err FlickrConnect(UInt16 libRefNum, ExgSocketType *exgSocketP)
{
    DMSG("FlickrConnect() enter/exit\n");
    return exgErrNotSupported;
}

// ExgLibAccept
Err FlickrAccept(UInt16 libRefnum, ExgSocketType *exgSocketP)
{
    DMSG("FlickrAccept() enter/exit\n");
    return exgErrNotSupported;
}

static Err FlickrUploadImage(FlickrSocketContext& context, ExgSocketType* socket);
static Err FlickrShowUploadCompleted(FlickrSocketContext& context);

// ExgLibDisconnect
Err FlickrDisconnect(UInt16 libRefnum, ExgSocketType *exgSocket, Err err)
{
    DMSG("FlickrDisconnect() enter; err: "); DNUM(err); DENDL;
    FlickrDbOpen dbOpen;
    FlickrSocketContext* context = (FlickrSocketContext*)exgSocket->socketRef;
    if (NULL == context)
    {
        DMSG("FlickrDisconnect() context is NULL"); DENDL;
        if (errNone == err)
            err = exgErrUnknown;

        goto Finish;
    }

    if (errNone != err)
        goto Finish;

    err = FlickrUploadImage(*context, exgSocket);
    if (errNone == err && !context->prefs.dontShowUploadCompletedForm)
        err = FlickrShowUploadCompleted(*context);

Finish:

    if (NULL != context && NULL != context->progress)
    {
        DMSG("PrgUpdateDialog() called"); DENDL;
        PrvUpdateProgress(*context, err);
        err = PrvProcessEvents(*context, 0);
    }

    delete context;
    exgSocket->socketRef = NULL;
    DMSG("FlickrDisconnect() exit; error: ");DNUM(err);DENDL
    return err;
}


static Err FlickrVerifyUserCredentials(bool& res, FlickrPrefs& prefs)
{
    Err err = errNone;
    UInt16 size = sizeof(FlickrPrefs);
    Int16 ver = PrefGetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, &prefs, &size, true);
    if (noPreferenceFound == ver)
    {
        res = false;
        return errNone;
    }
    res = ((0 != StrLen(prefs.email)) && (0 != StrLen(prefs.password)));
    return err;
}


static MemHandle StrCopyToHandle(const char* text, Int16 len = -1)
{
    if (-1 == len)
        len = StrLen(text);

    MemHandle handle = MemHandleNew(len + 1);
    if (NULL == handle)
    {
        DMSG("StrCopyToHandle(): MemHandleNew() failed; size: "); DNUM(len + 1); DENDL;
        return NULL;
    }
    char* p = (char*)MemHandleLock(handle);
    if (NULL == p)
    {
        MemHandleFree(handle);
        return NULL;
    }

    MemMove(p, text, sizeof(char) * len);
    p[len] = chrNull;

    MemPtrUnlock(p);
    return handle;
}

static Boolean UserCredentialsFormHandleEvent(EventType* event)
{
    switch (event->eType)
    {
        case ctlSelectEvent:
            DMSG("UserCredentialsFormHandleEvent(): ctlSelectEvent"); DENDL;
            if (okButton == event->data.ctlSelect.controlID)
            {
                FormType* form = FrmGetFormPtr(userCredentialsForm);
                UInt16 emailIndex = FrmGetObjectIndex(form, emailField);
                UInt16 passwordIndex = FrmGetObjectIndex(form, passwordField);
                const char* email = FldGetTextPtr((FieldType*)FrmGetObjectPtr(form, emailIndex));
                const char* password = FldGetTextPtr((FieldType*)FrmGetObjectPtr(form, passwordIndex));

                if (NULL == email || 0 == StrLen(email))
                {
                    FrmSetFocus(form, emailIndex);
                    return true;
                }
                if (NULL == password || 0 == StrLen(password))
                {
                    FrmSetFocus(form, passwordIndex);
                    return true;
                }
            }
            return false;

        default:
            return false;
    }
}

static Err UserCredentialsFormInit(FormType* form, const FlickrPrefs& prefs)
{
    FieldType* field;
    MemHandle handle;
    MemHandle newText;
    UInt16 len;

    FrmSetEventHandler(form, UserCredentialsFormHandleEvent);

    field = (FieldType*)FrmGetObjectPtr(form, FrmGetObjectIndex(form, emailField));
    assert(field != NULL);
//    FldSetMaxVisibleLines(field, 2);

    if (0 != (len = StrLen(prefs.email)))
    {
        newText = StrCopyToHandle(prefs.email, len);
        if (NULL == newText)
            return exgMemError;

        handle = FldGetTextHandle(field);
        if (NULL != handle)
            MemHandleFree(handle);

        FldSetTextHandle(field, newText);
        FldSetSelection(field, 0, len);
        FldRecalculateField(field, false);
    }
    if (0 != (len = StrLen(prefs.password)))
    {
        field = (FieldType*)FrmGetObjectPtr(form, FrmGetObjectIndex(form, passwordField));
        assert(field != NULL);
        newText = StrCopyToHandle(prefs.password, len);
        if (NULL == newText)
            return exgMemError;

        handle = FldGetTextHandle(field);
        if (NULL != handle)
            MemHandleFree(handle);

        FldSetTextHandle(field, newText);
        FldSetSelection(field, 0, len);
        FldRecalculateField(field, false);
    }
    return errNone;
}

static void UserCredentialsFormValidate(FormType* form, FlickrPrefs& prefs)
{
    const char* email = FldGetTextPtr((FieldType*)FrmGetObjectPtr(form, FrmGetObjectIndex(form, emailField)));
    const char* password = FldGetTextPtr((FieldType*)FrmGetObjectPtr(form, FrmGetObjectIndex(form, passwordField)));
    StrCopy(prefs.email, email);
    StrCopy(prefs.password, password);
}

void FlickrSavePrefs(const FlickrPrefs& prefs)
{
    PrefSetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, flickrPrefsVersion, &prefs, sizeof(FlickrPrefs), true);
}

static Err FlickrGetUserCredentials(FlickrPrefs& prefs)
{
    Err err = errNone;
    FormType* form = NULL;
    bool formStateSaved = false;

    FormActiveStateType activeState;
    FrmSaveActiveState(&activeState);
    formStateSaved = true;

    MenuEraseStatus(NULL);
    form = FrmInitForm(userCredentialsForm);
    if (NULL == form)
    {
        DMSG("FlickrGetUserCredentials(): unable to initialize form");DENDL;
        err = exgMemError;
        goto Finish;
    }

    err = UserCredentialsFormInit(form, prefs);
    if (errNone != err)
        goto Finish;

    FrmSetActiveForm(form);
    FrmDrawForm(form);

    UInt16 button = FrmDoDialog(form);
    switch (button)
    {
        case cancelButton:
            err = exgErrUserCancel;
            goto Finish;

        case okButton:
            UserCredentialsFormValidate(form, prefs);
            break;

        default:
            assert(false);
    }

    FlickrSavePrefs(prefs);

Finish:
    if (NULL != form)
        FrmDeleteForm(form);

    if (formStateSaved)
        FrmRestoreActiveState(&activeState);

    return err;
}

static void FlickrAlert(UInt16 alertId)
{
    FormActiveStateType activeState;
    FrmSaveActiveState(&activeState);

    MenuEraseStatus(NULL);
    FrmAlert(alertId);

    FrmRestoreActiveState(&activeState);
}

#define EXT_JPEG ".jpeg"
#define EXT_JPG   ".jpg"
#define EXT_PNG  ".png"
#define EXT_GIF   ".gif"

#define TYPE_JPEG "image/jpeg"
#define TYPE_PNG  "image/png"
#define TYPE_GIF   "image/gif"

static Err FlickrDetectExtensionAndType(const ExgSocketType* socket, const char*& ext, const char*& type, const char*& name)
{
    const char* url = socket->name;
    if (NULL == url)
        return exgErrBadData;

    name = StrChr(url, ':');
    if (NULL == name)
        return exgErrBadData;

    ++name;

    ext = NULL;
    type = NULL;
    bool extFromType = false;
    const char* pos = StrChr(url, '.');
    if (NULL != pos)
    {
        while (NULL != pos)
        {
            ext = pos;
            pos = StrChr(pos + 1, '.');
        }
        if (0 == StrCaselessCompare(ext, EXT_JPG) || 0 == StrCaselessCompare(ext, EXT_JPEG))
            type = TYPE_JPEG;
        else if (0 == StrCaselessCompare(ext, EXT_PNG))
            type = TYPE_PNG;
        else if (0 == StrCaselessCompare(ext, EXT_GIF))
            type = TYPE_GIF;
        else
        {
            DMSG("FlickrDetectExtensionAndType() unknown file extension: "); DMSG(ext); DENDL;
            return exgErrBadData;
        }
    }
    else
        extFromType = true;

    if (NULL == socket->type)
    {
        if (extFromType)
        {
            DMSG("FlickrDetectExtensionAndType() no extension nor mimeType"); DENDL;
            return exgErrBadData;
        }
        assert(type != NULL);
        return errNone;
    }

    if (NULL != type && 0 != StrCaselessCompare(type, socket->type))
    {
        DMSG("FlickrDetectExtensionAndType() extension and mimeType mismatch; ext: "); DMSG(ext);
        DMSG("; type: "); DMSG(type); DENDL;
    }

    type = socket->type;
    if (extFromType)
    {
        if (0 == StrCaselessCompare(type, TYPE_JPEG))
            ext = EXT_JPG;
        else if (0 == StrCaselessCompare(type, TYPE_PNG))
            ext = EXT_PNG;
        else if (0 == StrCaselessCompare(type, TYPE_GIF))
            ext = EXT_GIF;
        else
        {
            DMSG("FlickrDetectExtensionAndType() unknown mimeType: "); DMSG(type); DENDL;
            return exgErrBadData;
        }
    }
    return errNone;
}

static void FlickrSocketInspect(const ExgSocketType* exgSocket)
{
    DMSG("FlickrSocketInspect() length: "); DNUM(exgSocket->length); DENDL;
    DMSG("FlickrSocketInspect() count: "); DNUM(exgSocket->count); DENDL;

    if (NULL != exgSocket->name)
    {
        DMSG("FlickrSocketInspect() name: "); DMSG(exgSocket->name); DENDL;
    }

    if (NULL != exgSocket->type)
    {
        DMSG("FlickrSocketInspect() type: "); DMSG(exgSocket->type); DENDL;
    }

    if (NULL != exgSocket->description)
    {
        DMSG("FlickrSocketInspect() description: "); DMSG(exgSocket->description); DENDL;
    }
}

static Err FlickrAppendImageData(FlickrSocketContext& context, const void* data, UInt32 length);

static Err FlickrUploadImage(ExgSocketType* socket, FlickrSocketContext& context);

static Boolean FlickrProgressCallback(PrgCallbackDataPtr cbP);

static Err PrvStartProgress(FlickrSocketContext* context)
{
    Err err = errNone;
    if (NULL == context->progress)
    {
        DMSG("PrvStartProgress(): calling PrgStartDialog()"); DENDL;
        context->progress = PrgStartDialog("Flickr uploader", FlickrProgressCallback, context);
        if (NULL == context->progress)
        {
            err = exgMemError;
            FlickrAlert(notEnoughMemoryAlert);
            goto Finish;
        }
    }
Finish:
    return err;
}

static void PrvPrepareDescriptionText(FlickrPrefs& prefs);
static void PrvPrepareTags(FlickrPrefs& prefs);

// ExgLibPut
Err FlickrPut(UInt16 libRefnum, ExgSocketType* exgSocket)
{
    DMSG("FlickrPut() enter"); DENDL;
    FlickrDbOpen dbOpen;

    assert(exgSocket->libraryRef == libRefnum);

    FlickrSocketContext* context = NULL;

    const char* extension = NULL;
    const char* mimeType = NULL;
    const char* name = NULL;
    Err err = FlickrDetectExtensionAndType(exgSocket, extension, mimeType, name);
    if (errNone != err)
    {
        FlickrAlert(unsupportedFormatAlert);
        goto Finish;
    }

    DMSG("FlickrPut() using extension: "); DMSG(extension); DMSG(" and type: "); DMSG(mimeType); DENDL;

    if (NULL != exgSocket->socketRef)
    {
        DMSG("FlickrPut(): socketRef is not NULL!");DENDL;
        context = (FlickrSocketContext*)exgSocket->socketRef;
        if (FlickrSocketContext::magicValue != context->magic)
        {
            DMSG("FlickrPut(): socketRef probably is not context, magic value mismatch"); DENDL;
            exgSocket->socketRef = NULL;
        }
        else
        {
            err = FlickrUploadImage(*context, exgSocket);
            if (errNone != err)
                goto Finish;

            err = context->Reset();
            if (errNone != err)
                goto Finish;
        }
    }

    if (NULL == exgSocket->socketRef)
    {
        context = new FlickrSocketContext(libRefnum);
        if (NULL == context)
        {
            DMSG("FlickrPut(): not enough memory to create FlickrSocketContext");DENDL;
            FlickrAlert(notEnoughMemoryAlert);
            err = exgMemError;
            goto Finish;
        }
        err = context->Init();
        if (errNone != err)
        {
            // TODO: inspect error and display appropriate alert
            goto Finish;
        }
        exgSocket->socketRef = (UInt32)context;
        MemPtrSetOwner(context, 0);
    }

    bool hasCredentials;
    err = FlickrVerifyUserCredentials(hasCredentials, context->prefs);
    if (errNone != err)
        goto Finish;

    if (!hasCredentials)
    {
        DMSG("FlickrVerifyUserCredentials() returned false"); DENDL;
        err = FlickrGetUserCredentials(context->prefs);
        if (errNone != err)
            goto Finish;
    }

    DMSG("FlickrPut() user credentials obtained succesfully; email: "); DMSG(context->prefs.email);
    DMSG("; password: "); DMSG(context->prefs.password); DENDL;

#ifndef NDEBUG
    FlickrSocketInspect(exgSocket);
#endif

    PrvPrepareDescriptionText(context->prefs);
    PrvPrepareTags(context->prefs);

    StrNCopy(context->fileName, name, FlickrSocketContext::maxFileNameLength);
    context->fileName[FlickrSocketContext::maxFileNameLength] = chrNull;
    StrNCopy(context->contentType, mimeType, FlickrSocketContext::maxContentTypeLength);
    context->contentType[FlickrSocketContext::maxContentTypeLength] = chrNull;

    err = PrvStartProgress(context);

Finish:

    if (NULL != context && NULL != context->progress)
    {
        DMSG("PrgUpdateDialog() called"); DENDL;
        PrvUpdateProgress(*context, err);
        err = PrvProcessEvents(*context, 0);
    }

    if (errNone != err)
    {
        delete context;
        exgSocket->socketRef = NULL;
    }
    DMSG("FlickrPut() exit; error: ");DNUM(err);DENDL
    return err;
}

// ExgLibGet
Err FlickrGet(UInt16 libRefNum, ExgSocketType *exgSocketP)
{
    // Not to be implemented.
    DMSG("FlickrGet() enter/exit\n");
    return exgErrNotSupported;
}

// ExgLibSend
UInt32 FlickrSend(UInt16 libRefNum, ExgSocketType *exgSocket, const void *bufP, UInt32 bufLen, Err *errP)
{
    DMSG("FlickrSend() enter");DENDL;
    *errP = errNone;
    FlickrDbOpen dbOpen;

    FlickrSocketContext* context = (FlickrSocketContext*)exgSocket->socketRef;
    if (NULL == context)
    {
        DMSG("FlickrSend() context is NULL"); DENDL;
        *errP = exgErrUnknown;
        goto Finish;
    }

    DMSG("FlickrSend() bufLen: "); DNUM(bufLen); DENDL;

    *errP = FlickrAppendImageData(*context, bufP, bufLen);

    if (stageReadingImageData != context->stage)
        context->stage = stageReadingImageData;

Finish:

    if (NULL != context && NULL != context->progress)
    {
        DMSG("PrgUpdateDialog() called"); DENDL;
        PrvUpdateProgress(*context, *errP);
        *errP = PrvProcessEvents(*context, 0);
    }

    if (errNone != *errP)
    {
        delete context;
        exgSocket->socketRef = NULL;
    }
    DMSG("FlickrSend() exit; error: ");DNUM(*errP);DENDL
    return bufLen;
}

// ExgLibReceive
UInt32 FlickrReceive(UInt16 libRefNum, ExgSocketType *exgSocketP, void *bufP, UInt32 bufSize, Err *errP)
{
    // Not to be implemented.
    DMSG("FlickrReceive() enter/exit\n");
    *errP = exgErrNotSupported;
    return 0;
}

// ExgLibControl
Err FlickrControl(UInt16 libRefNum, UInt16 op, void *valueP, UInt16 *valueLenP)
{
    DMSG("FlickrControl() enter, op: ");DNUM(op);DMSG("; *valueLenP: ");DNUM(*valueLenP);DENDL
    FlickrDbOpen dbOpen;
    FlickrGlobalsPtr globals(libRefNum);
    switch (op)
    {
        case exgLibCtlGetTitle:
        {
            DMSG("FlickrControl(): exgLibCtlGetTitle\n");
            if (NULL == valueLenP)
                return exgErrBadParam;
            UInt16 len = StrLen(FlickrTitle);
            if (0 == *valueLenP || NULL == valueP)
            {
                *valueLenP = len;
                return errNone;
            }
            if (*valueLenP - 1 < len)
            {
                StrNCopy((char*)valueP, FlickrTitle, *valueLenP - 1);
                ((char*)valueP)[*valueLenP - 1] = chrNull;
            }
            else
            {
                StrCopy((char*)valueP, FlickrTitle);
                *valueLenP = len + 1;
            }
            return errNone;
        }
        case exgLibCtlGetVersion:
        {
            DMSG("FlickrControl(): exgLibCtlGetVersion\n");
            if (NULL == valueP || NULL == valueLenP || *valueLenP < 2)
                return exgErrBadParam;
            UInt16* ver = (UInt16*)valueP;
            *ver = exgLibAPIVersion;
            *valueLenP = 2;
            return errNone;
        }
        case exgLibCtlGetPreview:
            DMSG("FlickrControl(): exgLibCtlGetPreview\n");
            return exgErrNotSupported;

        case flickrCtlLibraryVersion:
        {
            DMSG("FlickrControl(): flickrCtlLibraryVersion\n");
            if (NULL == valueP || NULL == valueLenP || *valueLenP < 2)
                return exgErrBadParam;
            UInt16* ver = (UInt16*)valueP;
            *ver = FlickrVersion;
            *valueLenP = 2;
            return errNone;
        }         
        
        case flickrCtlInitializePrefs:
        {
            DMSG("FlickrControl(): flickrCtlInitializePrefs\n");
            FlickrPrefs* prefs = new FlickrPrefs;
            if (NULL == prefs)
                return memErrNotEnoughSpace;
            
            MemSet(prefs, sizeof(*prefs), 0);
            UInt16 size = sizeof(*prefs);
            Int16 ver = PrefGetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, prefs, &size, true);
            if (noPreferenceFound != ver)
                goto Finish;
                
            PrvPrepareDescriptionText(*prefs);
            PrvPrepareTags(*prefs);
            FlickrSavePrefs(*prefs);
Finish:
            delete prefs;            
            return errNone;
        }   
    }
    return exgErrNotSupported;
}

// ExgLibRequest
Err FlickrRequest(UInt16 libRefNum, ExgSocketType *socketP)
{
    DMSG("FlickrRequest() enter/exit\n");
    return exgErrNotSupported;
}

/*********************************************************************
 * Private Functions
 *********************************************************************/

/*
 * FUNCTION: PrvMakeGlobals
 *
 * DESCRIPTION: Create our library globals.
 *
 * PARAMETERS:
 *
 * refNum
 *		Library reference number returned by SysLibLoad() or SysLibFind().
 *
 * CALLED BY: internal
 *
 * RETURNS:
 *
 *		pointer to our *locked* library globals
 *		NULL if our globals	could not be created.
 */
FlickrGlobals* PrvMakeGlobals(UInt16 refNum)
{
    SysLibTblEntryType* libEntry = SysLibTblEntry(refNum);
    ErrFatalDisplayIf(libEntry == NULL, "invalid InfoMan Flickr Uploader refNum");

    /* Error check to make sure the globals don't already exist */
    ErrFatalDisplayIf(libEntry->globalsP != NULL, "InfoMan Flickr Uploader globals already exist");

    /* Allocate and initialize our library globals. */
    MemHandle handle = MemHandleNew(sizeof(FlickrGlobals));
    if (NULL == handle)
        return NULL;

    FlickrGlobals* globals = (FlickrGlobals*)MemHandleLock(handle);
    if (NULL == globals)
    {
        MemHandleFree(handle);
        return NULL;
    }

    Err err = globals->Init(refNum);
    if (errNone != err)
    {
        MemPtrUnlock(globals);
        MemHandleFree(handle);
        return NULL;
    }

    /* Set the owner of our globals memory chunk to "system" (zero), so it won't get
     * freed automatically by Memory Manager when the first application to call
     * FlickrOpen exits.  This is important if the library is going to stay open
     * between apps. */
    MemPtrSetOwner(globals, 0);
    libEntry->globalsP = (MemPtr)handle;
    return globals;
}

/*
 * FUNCTION: PrvFreeGlobals
 *
 * DESCRIPTION: Free our library globals.
 *
 * PARAMETERS:
 *
 * refNum
 *		Library reference number returned by SysLibLoad() or SysLibFind().
 *
 * CALLED BY: internal
 *
 * RETURNS: nothing
 */

void PrvFreeGlobals(UInt16 refNum)
{
    SysLibTblEntryType* libEntry = SysLibTblEntry(refNum);
    ErrFatalDisplayIf(libEntry == NULL, "invalid InfoMan Flickr Uploader refNum");
    MemHandle handle = (MemHandle)libEntry->globalsP;
    if (NULL != handle)
    {
        FlickrGlobals* globals = (FlickrGlobals*)MemHandleLock(handle);
        if (NULL != globals)
        {
            globals->Dispose();
            MemPtrUnlock(globals);
        }
        libEntry->globalsP = NULL;
        MemHandleFree(handle);
    }
}

/*
 * FUNCTION: PrvLockGlobals
 *
 * DESCRIPTION:	Lock our library globals
 *
 * PARAMETERS:
 *
 * refNum
 *		Library reference number returned by SysLibLoad() or SysLibFind().
 *
 * CALLED BY: internal
 *
 * RETURNS:
 *		pointer to our library globals
 *		NULL if our globals	have not been created yet.
 */

FlickrGlobals* PrvLockGlobals(UInt16 refNum)
{
    SysLibTblEntryType* libEntry = SysLibTblEntry(refNum);
    ErrFatalDisplayIf(libEntry == NULL, "invalid InfoMan Flickr Uploader refNum");

    MemHandle handle = (MemHandle)libEntry->globalsP;
    if (NULL == handle)
        return NULL;

    return (FlickrGlobals*)MemHandleLock(handle);
}

/*
 * FUNCTION: PrvIsLibOpen
 *
 * DESCRIPTION:	Check if the library has been opened.
 *
 * PARAMETERS:
 *
 * refNum
 *		Library reference number returned by SysLibLoad() or SysLibFind().
 *
 * CALLED BY: internal
 *
 * RETURNS: non-zero if the library has been opened
 */

Boolean PrvIsLibOpen(UInt16 refNum)
{
    Boolean isOpen = false;
    FlickrGlobals* globals = PrvLockGlobals(refNum);
    if (NULL != globals)
    {
        isOpen = true;
        PrvUnlockGlobals(globals);
    }
    return isOpen;
}

Err FlickrAppendImageData(FlickrSocketContext& context, const void* data, UInt32 length)
{
    context.imageData = PrvRealloc(context.imageData, context.imageSize + length);
    if (NULL == context.imageData)
    {
        DMSG("FlickrAppendImageData(): PrvRealloc() failed"); DENDL;
        return exgMemError;
    }
    MemPtrSetOwner(context.imageData, 0);
    char* p = (char*)context.imageData;
    p += context.imageSize;
    MemMove(p, data, length);
    context.imageSize += length;
    return errNone;
}


static void FlickrClearUserCredentials()
{
    FlickrPrefs* prefs = new FlickrPrefs();
    if (NULL == prefs)
        return;

    MemSet(prefs, sizeof(*prefs), 0);

    UInt16 size = sizeof(*prefs);
    Int16 ver = PrefGetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, prefs, &size, true);
    if (noPreferenceFound == ver)
    {
        delete prefs;
        return;
    }

    MemSet(prefs->password, prefs->maxPasswordLength + 1, 0);
    FlickrSavePrefs(*prefs);
    delete prefs;
}

Err FlickrUploadImage(FlickrSocketContext& context, ExgSocketType* socket)
{
    DMSG("FlickrUploadImage() enter"); DENDL;
    assert(NULL == context.requestData);

#ifndef NDEBUG
    HostFILEType* f = HostFOpen("c:\\flickr_image.jpg", "w");
    if (NULL != f)
    {
        HostFWrite(context.imageData, context.imageSize, 1, f);
        HostFFlush(f);
        HostFClose(f);
    }
#endif

Again:
    Err err = HttpPrepareRequest(context);
    if (errNone != err)
        return err;

    assert(NULL != context.requestData);

    if (!context.netLibOpen)
    {
        err = context.NetLibInit();
        if (errNone != err)
            return err;
    }

    if (0 == context.flickrAddress)
    {
        err = FlickrAddressResolve(context);
        if (errNone != err)
        {
            context.NetLibDispose();
            return err;
        }
    }

    err = FlickrPerformConnection(context);

    context.DisposeRequest();

    if (flickrErrUploadInvalidLogin == err)
    {
        DMSG("FlickrUploadImage(): FlickrPerformConnection() returned flickrErrUploadInvalidLogin"); DENDL;
        if (NULL != context.progress)
        {
            PrgStopDialog(context.progress, false);
            context.progress = NULL;
            PrvProcessEvents(context, errNone);
        }

        err = FlickrGetUserCredentials(context.prefs);
        if (errNone != err)
        {
            FlickrClearUserCredentials();
            return err;
        }

        context.stage = stageOpeningConnection;
        err = PrvStartProgress(&context);
        if (errNone != err)
            return err;

        PrvProcessEvents(context, errNone);

        goto Again;
    }
    return err;
}

static void PrvFillBuffer(char* buffer, UInt16 length, const char* text1, const char* text2)
{
    UInt16 len1 = StrLen(text1);
    UInt16 len2 = StrLen(text2);

    buffer[length - 1] =chrNull;
    StrNCopy(buffer, text1, length - 1);
    StrNCat(buffer, text2, length - 1);
    if (len1 + len2 > length - 1)
        buffer[length - 2] = chrEllipsis;
}

static Boolean FlickrErrCallback(PrgCallbackData* data)
{
    DMSG("FlickrErrCallback(): enter; error: "); DNUM(data->error); DENDL;
    assert(errNone != data->error);
    const char* text = NULL;
    switch (data->error)
    {
        case memErrNotEnoughSpace:
        case exgMemError:
            text = "Not enough memory to complete operation.";
            break;

        case flickrErrHttpUnsupportedResponse:
            text = "Server returned malformed response.";
            break;

        case flickrErrUploadInvalidLogin:
            text = "Invalid flickr.com login. Please verify your email and password.";
            break;

        case flickrErrUploadFileTypeNotRecognized:
            text = "Server rejected this file type.";
            break;

        case flickrErrUploadExceededUploadLimit:
            text = "Exceeded flickr.com upload limit.";
            break;

        case flickrErrUploadFileSizeZero:
        case flickrErrUploadGeneralFailure:
        case flickrErrUploadNoPhoto:
        case flickrErrUploadUnknown:
            text = "Unable to complete operation: unknown flickr.com error.";
            break;

        case exgErrUserCancel:
            text = "Cancelled by user.";
            break;            

        default:
            if (data->error >= netErrorClass && data->error < netErrorClass + 0x100)
                text = "Unable to complete operation: network error.";
            else                
                text = "Unable to complete operation: unknown error.";
    }
    char buffer[32] = {chrNull};
    if (data->showDetails)
        StrPrintF(buffer, "\nError: %hu", data->error);
    PrvFillBuffer(data->textP, data->textLen, text, buffer);
    DMSG("FlickrErrCallback(): exit"); DENDL;
    return true;
}

static void PrvFormatBytes(char* buffer, UInt32 size)
{
    // TOD: more "intelligent" display (bytes, kB, MB)
    size += 512;
    size /= 1024;
    StrPrintF(buffer, "%lukB", size);
}

static void PrvFormatPercents(char* buffer, UInt16 percents)
{
    StrPrintF(buffer, "%hu%%", percents);
}

static UInt16 FlickrNextProgressBitmapID(UInt16 current)
{
    if (progressBitmap0 == current)
        return progressBitmap1;
    if (progressBitmap1 == current)
        return progressBitmap2;
    if (progressBitmap2 == current)
        return progressBitmap3;
    if (progressBitmap3 == current)
        return progressBitmap4;
    return progressBitmap0;
}


Boolean FlickrProgressCallback(PrgCallbackData* data)
{
    if (errNone != data->error)
        return FlickrErrCallback(data);

    FlickrSocketContext* context = (FlickrSocketContext*)data->userDataP;
    char buffer[32] = {chrNull};
    char* text = "";

    assert(context != NULL);
    switch (data->stage)
    {
        case stageReadingImageData:
            text = "Reading image data: ";
            PrvFormatBytes(buffer, context->imageSize);
            break;

        case stageResolvingHostAddress:
            text = "Resolving host address...";
            break;

        case stageOpeningConnection:
            text = "Connecting...";
            break;

        case stageUploadingImage:
            text = "Uploading image: ";
            PrvFormatPercents(buffer, ((context->sent  * 1000L) + 5L)/(context->requestSize * 10L));
            break;

        case stageReadingResponse:
            text = "Waiting for response...";
            break;

        case stageFinished:
            text = "Upload finished";
            break;

        default:
            assert(false);
    }
    UInt32 ticks = TimGetTicks();
    if (ticks - FLICKR_PROGRESS_ANIMATION_TIMEOUT >= context->lastAnimationTicks)
    {
        data->bitmapId = FlickrNextProgressBitmapID(data->bitmapId);
        context->lastAnimationTicks = ticks;
    }
    PrvFillBuffer(data->textP, data->textLen, text, buffer);
    data->textChanged = true;
    return true;
}

static UInt32 PrvBlockSize(UInt32 size)
{
    UInt32 upper = 0xffffffff;
    UInt32 lower = 0x80000000;
    while (size <= lower)
    {
        upper = lower;
        lower >>= 1;
    }
    return upper;
}

void* PrvRealloc(void* p, UInt32 newSize)
{
    if (0 == newSize)
    {
        if (NULL != p)
            MemPtrFree(p);
        return NULL;
    }
    newSize = PrvBlockSize(newSize);
    if (NULL == p)
        return MemGluePtrNew(newSize);

    UInt32 size = MemPtrSize(p);
    if (newSize <= size)
        return p;

    Err err = MemPtrResize(p, newSize);
    if (errNone == err)
        return p;

    void* np = MemGluePtrNew(newSize);
    if (NULL != np)
        MemMove(np, p, size);

    MemPtrFree(p);
    return np;
}

void PrvUpdateProgress(FlickrSocketContext& context, Err error)
{
    if (errNone == error)
        context.toggle = !context.toggle;
    PrgUpdateDialog(context.progress, error, context.stage, context.toggle ? "0" : "1", true);
}

#define INFOMAN_WWW_LINK "<a href=\"http://www.arslexis.com/palm/infoman/flickr.html\">http://arslexis.com/flickr</a>"

static void PrvFillDeviceName(char* buffer, UInt16 length)
{
    UInt32 vendor = 0, device = 0;
    FtrGet(sysFtrCreator, sysFtrNumOEMCompanyID, &vendor);
    FtrGet(sysFtrCreator, sysFtrNumOEMDeviceID, &device);
    const char* vendorText = "Unknown";
    const char* deviceText = NULL;

    // TODO: update vendor/devices list (can't use array because of globals)
    switch (vendor)
    {
        case 'hspr':
            vendorText = "";
            switch (device) {
                case 0xb: deviceText = "Treo 180"; break;
                case 0xd: deviceText = "Treo 270"; break;
                case 0xe: deviceText = "Treo 300"; break;
                case 'H101': deviceText = "Treo 600"; break;
                case 'H201': deviceText = "Treo 600 Simulator"; break;
                case 'H102': deviceText = "Treo 650"; break;
                case 'H202': deviceText = "Treo 650 Simulator"; break;
            }
            break;

        case 'sony':
            vendorText = "Sony";
            switch (device) {
                case 'mdna': deviceText = "PEG-T615C"; break;
                case 'prmr': deviceText = "PEG-UX50"; break;
                case 'atom': deviceText = "PEG-TH55"; break;
                case 'mdrd': deviceText = "PEG-NX80V"; break;
                case 'tldo': deviceText = "PEG-NX73V"; break;
                case 'vrna': deviceText = "PEG-TG50"; break;
                case 'crdb': deviceText = "PEG-NX60 or NX70V"; break;
                case 'mcnd': deviceText = "PEG-SJ33"; break;
                case 'glps': deviceText = "PEG-SJ22"; break;
                case 'goku': deviceText = "PEG-TJ35"; break;
                case 'luke': deviceText = "PEG-TJ37"; break;
                case 'ystn': deviceText = "PEG-N610C"; break;
            }
            break;

        case 'palm':
        case 'Palm':
            vendorText = "";
            switch (device) {
                case 'hbbs': deviceText = "Palm m130"; break;
                case 'ecty': deviceText = "Palm m505"; break;
                case 'lith': deviceText = "Palm m515"; break;
                case 'Zpth': deviceText = "Zire 71"; break;
                case 'MT64': deviceText = "Tungsten C"; break;
                case 'atc1': deviceText = "Tungsten W"; break;
                case 'Cct1': deviceText = "Tungsten E"; break;
                case 'Frg1': deviceText = "Tungsten T"; break;
                case 'Frg2': deviceText = "Tungsten T2"; break;
                case 'Arz1': deviceText = "Tungsten T3"; break;
                case 'Zir4': deviceText = "Tungsten E2"; break;
                case 'TnT5': deviceText = "Tungsten T5"; break;
                case 'Cubs': deviceText = "Zire"; break;
                case 'Zi21': deviceText = "Zire 21"; break;
                case 'Zi22': deviceText = "Zire 31"; break;
                case 'Zi72': deviceText = "Zire 72"; break;
                case 'TunX': deviceText = "LifeDrive"; break;
            }
            break;

        case 'psys':
            vendorText = "Palm OS Simulator";
            break;
    }
    StrNCat(buffer, vendorText, length);
    if (NULL != deviceText)
    {
        if (0 != StrLen(vendorText))
            StrNCat(buffer, " ", length);
        StrNCat(buffer, deviceText, length);
    }
}

void PrvPrepareDescriptionText(FlickrPrefs& prefs)
{
    if (prefs.registered)
        return;

    StrNCopy(prefs.description, "Sent from ", prefs.maxDescriptionLength);
    PrvFillDeviceName(prefs.description, prefs.maxDescriptionLength);
    StrNCat(prefs.description," using ArsLexis InfoMan (" INFOMAN_WWW_LINK ").", prefs.maxDescriptionLength);
    prefs.description[prefs.maxDescriptionLength] = chrNull;
    return;
}

void PrvPrepareTags(FlickrPrefs& prefs)
{
    if (prefs.registered)
        return;

    StrNCopy(prefs.tags, flickrDefaultTag, prefs.maxTagsLength);
    prefs.tags[prefs.maxTagsLength] = chrNull;
    return;
}

static Err FlickrDisableUploadCompletedForm();

Err FlickrShowUploadCompleted(FlickrSocketContext& context)
{
    if (NULL != context.progress)
    {
        PrgStopDialog(context.progress, false);
        context.progress = NULL;
    }
    Err err = errNone;
    FormType* form = NULL;
    bool formStateSaved = false;
    FormActiveStateType activeState;
    FrmSaveActiveState(&activeState);
    formStateSaved = true;

    MenuEraseStatus(NULL);
    form = FrmInitForm(uploadCompletedForm);
    if (NULL == form)
    {
        err = exgMemError;
        goto Finish;
    }

    FrmSetActiveForm(form);
    FrmDrawForm(form);

    FrmDoDialog(form);

    ControlType* control = (ControlType*)FrmGetObjectPtr(form, FrmGetObjectIndex(form, dontShowUploadCompletedFormCheckbox));
    if (NULL != control)
    {
        Int16 val = CtlGetValue(control);
        if (0 != val)
            err = FlickrDisableUploadCompletedForm();
    }


Finish:
    if (NULL != form)
        FrmDeleteForm(form);

    if (formStateSaved)
        FrmRestoreActiveState(&activeState);

    return err;
}

static Err FlickrDisableUploadCompletedForm()
{
    FlickrPrefs* prefs = new FlickrPrefs();
    if (NULL == prefs)
        return exgMemError;

    MemSet(prefs, sizeof(*prefs), 0);

    Err err = errNone;
    UInt16 size = sizeof(*prefs);
    Int16 ver = PrefGetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, prefs, &size, true);

    prefs->dontShowUploadCompletedForm = true;
    FlickrSavePrefs(*prefs);

Finish:
    delete prefs;
    return err;
}

