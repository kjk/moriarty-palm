/*
 * FlickrDispatch.c
 *
 * dispatch table for InfoMan Flickr Uploader shared library
 *
 * This wizard-generated code is based on code adapted from the
 * SampleLib project distributed as part of the Palm OS SDK 4.0.
 *
 * Copyright (c) 1994-1999 Palm, Inc. or its subsidiaries.
 * All rights reserved.
 */
 
/* Our library public definitions (library API) */
#define BUILDING_FLICKR
#include "Flickr.h"
#include "FlickrDbg.h"


void *PrvHostTransferDispatchTable(void);

/* Local prototypes */
extern Err FlickrInstall(UInt16 refNum, SysLibTblEntryType *entryP);

static MemPtr FlickrDispatchTable(void);

Err FlickrInstall(UInt16 refNum, SysLibTblEntryType *entryP)
{
    #pragma unused(refNum)
    DMSG("FlickrInstall() enter\n");
    
    /* Install pointer to our dispatch table */
    entryP->dispatchTblP = (MemPtr *) PrvHostTransferDispatchTable();

    /* Initialize globals pointer to zero (we will set up our
    * library globals in the library "open" call). */
    entryP->globalsP = 0;
    
    DMSG("FlickrInstall() exit\n");
    return 0;
}

/* Palm OS uses short jumps */
/* 
#define prvJmpSize		4
#define libDispatchEntry(index)		(kOffset+((index)*prvJmpSize))
#define numberOfAPIs        (10)
#define entrySize           (2)
#define	kOffset             (entrySize * (5 + numberOfAPIs))

static MemPtr asm FlickrDispatchTable(void)
{
	LEA		@Table, A0			
	RTS							

@Table:
	DC.W		@Name
	DC.W		libDispatchEntry(0)			    
	DC.W		libDispatchEntry(1)		    	
	DC.W		libDispatchEntry(2)	    		
	DC.W		libDispatchEntry(3) 			
	DC.W		libDispatchEntry(5 - 1)		
	DC.W		libDispatchEntry(6 - 1)		
	DC.W		libDispatchEntry(7 - 1)		
	DC.W		libDispatchEntry(8 - 1)		
	DC.W		libDispatchEntry(9 - 1)		
	DC.W		libDispatchEntry(10 - 1)		
	DC.W		libDispatchEntry(11 - 1)		
	DC.W		libDispatchEntry(12 - 1)		
	DC.W		libDispatchEntry(13 - 1)		
	DC.W		libDispatchEntry(14 - 1)		

@GotoOpen:    
	JMP         FlickrOpen
@GotoClose:	
	JMP         FlickrClose
@GotoSleep:	
	JMP         FlickrSleep
@GotoWake:	
	JMP         FlickrWake

@GotoHandleEvent:    
    JMP         FlickrHandleEvent
@GotoConnect:    
    JMP         FlickrConnect
@GotoAccept:    
    JMP         FlickrAccept
@GotoDisconnect:    
    JMP         FlickrDisconnect
@GotoPut:    
    JMP         FlickrPut
@GotoGet:    
    JMP         FlickrGet
@GotoSend:    
    JMP         FlickrSend
@GotoReceive:
    JMP         FlickrReceive
@GotoOption:    
    JMP         FlickrControl
@GotoCheck:    
    JMP         FlickrRequest
	
@Name:
	DC.B		"IM FlickrUploader"
}
 */

#define	kNumDispatchEntries	14					// UPDATE THIS WHEN CALLS ARE ADDED TO @TABLE
#define	kOffset					((kNumDispatchEntries + 1) * 2)

#if EMULATION_LEVEL == EMULATION_NONE
#if defined(__MC68K__)
asm void *PrvHostTransferDispatchTable(void)
{
	LEA		@Table, A0								// table ptr
	RTS													// exit with it

@Table:
	DC.W		@Name
	DC.W		(kOffset)								// Open
	DC.W		(kOffset+(1*4))						// Close
	DC.W		(kOffset+(2*4))						// Sleep
	DC.W		(kOffset+(3*4))						// Wake
	
	// Start of the exchange libary
	DC.W		(kOffset+(4*4))						// HostTransferLibHandleEvent
	DC.W		(kOffset+(5*4))						// HostTransferLibConnect
	DC.W		(kOffset+(6*4))						// HostTransferLibAccept
	DC.W		(kOffset+(7*4))						// HostTransferLibDisconnect
	DC.W		(kOffset+(8*4))						// HostTransferLibPut
	DC.W		(kOffset+(9*4))						// HostTransferLibGet
	DC.W		(kOffset+(10*4))						// HostTransferLibSend
	DC.W		(kOffset+(11*4))						// HostTransferLibReceive
	DC.W		(kOffset+(12*4))						// HostTransferLibControl
	DC.W		(kOffset+(13*4))						// HostTransferLibRequest


@GotoOpen:
	JMP 		FlickrOpen
@GotoClose:
	JMP 		FlickrClose
@GotoSleep:
	JMP 		FlickrSleep
@GotoWake:
	JMP 		FlickrWake


@GotoHandleEvent:
	JMP 		FlickrHandleEvent
@GotoConnect:
	JMP 		FlickrConnect
@GotoAccept:
	JMP 		FlickrAccept
@GotoDisconnect:
	JMP 		FlickrDisconnect
@GotoPut:
	JMP 		FlickrPut
@GotoGet:
	JMP 		FlickrGet
@GotoSend:
	JMP 		FlickrSend
@GotoReceive:
	JMP 		FlickrReceive
@GotoOption:
	JMP 		FlickrControl
@GotoCheck:
	JMP 		FlickrRequest

@Name:
	DC.B		FlickrName

}
#else
#error "Processor type not defined"
#endif

#else	// EMULATION_LEVEL == EMULATION_NONE

static const void *dispatchTable[] =
{
	// Number of entries that follow (not counting the name entry after)
	(void*)kNumDispatchEntries,
	
	// Common to all libraries
	FlickrOpen,
	FlickrClose,
	FlickrSleep,
	FlickrWake,
	
	// Exchange lib common...
	FlickrHandleEvent,
	FlickrConnect,
	FlickrAccept,
	FlickrDisconnect,
	FlickrPut,
	FlickrGet,
	FlickrSend,
	FlickrReceive,
	FlickrControl,
	FlickrRequest,
	
	// The library name
	FlickrName
};

void *PrvHostTransferDispatchTable(void)
{
    return (void *)&dispatchTable;
}
#endif	// EMULATION_LEVEL == EMULATION_NONE
