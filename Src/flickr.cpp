#include "flickr.hpp"
#include "moriarty.h"
#include "MoriartyPreferences.hpp"
#include "MoriartyApplication.hpp"

#include "../FlickrUploader/Src/Flickr.h"

#include <DataStore.hpp>

#include "ModulesData.hpp"

#define FLICKR_MIME_TYPES "image/jpeg\timage/png\timage/gif"
#define FLICKR_MIME_TYPES_DESCRIPTIONS "JPEG Image\tPNG Image\tGIF Image"

#define FLICKR_EXTENSIONS "JPG\tPNG\tGIF"
#define FLICKR_EXTENSIONS_DESCRIPTIONS "JPEG Image\tPNG Image\tGIF Image"

#define FLICKR_SCHEME exgSendScheme
#define FLICKR_SCHEME_DESCRIPTION "Upload image to flickr.com using InfoMan"

#pragma segment Segment1

// This code is taken from PalmSource Knowledge Base. It removes non-existant exchange library registration info
static UInt16 CleanUpExgMgrPrefs()
{
    Err err = errNone;
    UInt32 romVersion = 0;
    DmOpenRef prefDB = NULL;
    UInt16 numRemoved = 0;
    Int32 i;
    
    // if we're on Palm OS Cobalt 6.0 or later, the crashing bug has been
    // fixed, and we can't call PrefOpenPreferenceDB.  So, we'll just return
    // immediately.
    FtrGet(sysFileCSystem, sysFtrNumROMVersion, &romVersion);
    if (romVersion >= sysMakeROMVersion(6, 0, 0, 0, 0))
    {
        return 0;
    }

    // open the unsaved preferences database
    prefDB = PrefOpenPreferenceDB(false);
    
    // loop through all the resources, looking for ExgMgr-related prefs
    // we loop backwards so we don't have to adjust our index when we
    // delete bogus entries.
    for (i = DmNumResources(prefDB) - 1L; i >= 0; --i)
    {
        DmResType resType = 0;
        DmResID resID = 0;
        
        err = DmResourceInfo(prefDB, i, &resType, &resID, NULL);
        if (err == errNone)
        {
            // only check if the pref is a supported ExgMgr value
            // (range expanded to include PalmOne edit items defined below)
            #define exgRegEditCreatorID     0xff7b
            #define exgRegEditExtensionID   0xff7d
            #define exgRegEditTypeID        0xff7e

            if (resID == exgRegCreatorID ||
            	resID == exgRegSchemeID ||
            	resID == exgRegExtensionID ||
            	resID == exgRegTypeID ||
            	resID == exgRegEditCreatorID ||
            	resID == exgRegEditExtensionID ||
            	resID == exgRegEditTypeID)
            {
                // look for an application or exg library with this creator ID
                UInt16 cardNo;
                LocalID dbID;
                DmSearchStateType stateInfo;
                
                err = DmGetNextDatabaseByTypeCreator(
                    true, &stateInfo, sysFileTExgLib, resType, false,
                    &cardNo, &dbID);
                if (err == dmErrCantFind)
                {
                    err = DmGetNextDatabaseByTypeCreator(
                        true, &stateInfo, sysFileTApplication, resType, false,
                        &cardNo, &dbID);

                    if (err == dmErrCantFind)
                    {
                        // no library or application found, so delete the pref
                        err = DmRemoveResource(prefDB, i);
                        ++numRemoved;
                    }
                }
            }
        }
    }

    // clean up
    DmCloseDatabase(prefDB);

    // return number of entries removed, in case we want to display that
    return numRemoved;
}

static Err FlickrLibRegistered(bool& out)
{   

    UInt32 count;
    UInt32* ids = NULL;
    Err err = ExgGetRegisteredApplications(&ids, &count, NULL, NULL, exgRegSchemeID, exgSendScheme);
    if (errNone != err)
        return err;
        
    out = false;
    if (0 == count)
        goto Finish;
    
    for (UInt32 i = 0; i < count; ++i)
    {
        if (FlickrCreatorID == ids[i])
        {
            out = true;
            goto Finish;
        }
    }
        
Finish:
    if (NULL != ids)
        MemPtrFree(ids);
    return err;
}

static Err FlickrLibInstalled(bool& res)
{
    DmSearchStateType state;
    UInt16 cardNo; 
    LocalID id;
    Err err = DmGetNextDatabaseByTypeCreator(true, &state,  sysFileTExgLib, FlickrCreatorID, true, &cardNo, &id);
    if (errNone != err)
    {
        if (dmErrCantFind == err)
        {
            res = false;
            return errNone;
        }
        return err;
    }
    res = true;
    return errNone;
}    

static Err FlickrTest()
{
    ExgSocketType socket;
    memzero(&socket, sizeof(socket));
    socket.name = exgSendPrefix "test.jpg";
    socket.type = "image/jpeg";
    socket.length = 100;
    socket.count = 1;
    
    Err err = ExgPut(&socket);
    if (errNone == err)
        ExgDisconnect(&socket, memErrNotEnoughSpace);
    return err;
}

static Err FlickrRegister()
{
    Err err;
    err = ExgRegisterDatatype(FlickrCreatorID, exgRegTypeID, FLICKR_MIME_TYPES, FLICKR_MIME_TYPES_DESCRIPTIONS, 0);
    if (errNone != err)
        return err;

    err = ExgRegisterDatatype(FlickrCreatorID, exgRegExtensionID, FLICKR_EXTENSIONS, FLICKR_EXTENSIONS_DESCRIPTIONS, 0);
    if (errNone != err)
        return err;
        
    err = ExgRegisterDatatype(FlickrCreatorID, exgRegSchemeID, "flickr\t" exgSendScheme, FlickrTitle, 0);
    return err;
}

static Err FlickrLibInstall()
{
    Err err = errNone;
    MemHandle h = DmGet1Resource(sysResTAppGData, flickrExchangeLibrary);
    if (NULL == h)
    {   
        err = DmGetLastErr();
        return err;
    }        
    void* p = MemHandleLock(h);
    if (NULL == p)        
    {   
        err = memErrNotEnoughSpace;
        goto Finish;
    }
    err = DmCreateDatabaseFromImage(p);
    if (errNone == err)
    {
        bool pres;
        Err ignore = FlickrLibInstalled(pres);
        assert(errNone == ignore);
        assert(true == pres);
        bool loaded = false;
        UInt16 refNum = 0;
        
        ignore = SysLibFind(FlickrName, &refNum);
        if (errNone != ignore)
        {
            ignore = SysLibLoad(sysFileTExgLib, FlickrCreatorID, &refNum);  
            if (errNone == ignore)
                loaded = true;

            if (errNone == ignore)
            {
                UInt16 zero = 0;
                ignore = ExgLibControl(refNum, flickrCtlInitializePrefs, NULL, &zero);
            }                
        }                
        
        FlickrSynchronizeRegistrationStatus();

        ignore = FlickrRegister();
        
//        ignore = FlickrTest();
        // Exchange Library must be left loaded in order for Exchange Manager to find it - don't call SysLibRemove()
    }
Finish:
    if (NULL != p)
        MemPtrUnlock(p);
    if (NULL != h)
        DmReleaseResource(h);
    return err;     
}

static void FlickrRemoveLib(UInt16 refNum)
{
    ExgRegisterDatatype(FlickrCreatorID, exgRegSchemeID, NULL, NULL, 0);
    ExgRegisterDatatype(FlickrCreatorID, exgRegExtensionID, NULL, NULL, 0);
    ExgRegisterDatatype(FlickrCreatorID, exgRegTypeID, NULL, NULL, 0);
    
    SysLibRemove(refNum);

    DmSearchStateType state;
    UInt16 cardNo; 
    LocalID id;
    Err err = DmGetNextDatabaseByTypeCreator(true, &state,  sysFileTExgLib, FlickrCreatorID, true, &cardNo, &id);
    if (errNone == err)
        DmDeleteDatabase(cardNo, id);
}

static Err FlickrDatabasesDifferent(bool& result);

static Err FlickrRemoveOldVersion(bool& lastVersion)
{
    UInt16 refNum;
    lastVersion = false;
    Err err = SysLibFind(FlickrName, &refNum);
    if (errNone != err)
    {
        err = SysLibLoad(sysFileTExgLib, FlickrCreatorID, &refNum);  
        if (errNone != err)
            return err;
    }                
    
    err = ExgLibOpen(refNum);
    UInt16 ver;
    UInt16 size = sizeof(ver);
    err = ExgLibControl(refNum, flickrCtlLibraryVersion, &ver, &size);
    
// Always reinstall library in debug version    
#ifdef NDEBUG    
    if (ver >= FlickrVersion)
        lastVersion = true;
#endif        

    err = ExgLibClose(refNum);
            
    if (lastVersion)
        return errNone;
        
    FlickrRemoveLib(refNum);    
    return errNone;
}

status_t FlickrInitialize()
{
    CleanUpExgMgrPrefs();

    bool status;
    Err err = FlickrLibInstalled(status);
    if (errNone != err)
        status = false;

    if (status)
        FlickrRemoveOldVersion(status);
        
    if (!status)
    {        
        err = FlickrLibInstall();
        if (errNone != err)
            return err;
    }
    
    err = FlickrLibRegistered(status);
    if (errNone != err)
        return err;
    
    if (status)
        return errNone;
      
    return FlickrRegister();  
}

void FlickrSynchronizeRegistrationStatus()
{
    bool regged = false;
    MoriartyApplication& app = MoriartyApplication::instance();
    if (app.hasPreferences())
    {
        regged = !app.preferences().regCode.empty();
        goto Sync;
    }
    return;
    
    // Unfortunately we can't use the code below because these classes aren't in 1st segment.
/*    
    Preferences* prefs = NULL;
    DataStoreReader* reader = NULL;
    Serializer* serializer = NULL;
    DataStore* ds = new_nt DataStore();
    if (NULL == ds)
        return;
        
    Err err = ds->open(appDataFile);
    if (errNone != err)
        goto Done;

    reader = new_nt DataStoreReader(*ds);
    if (NULL == reader)
    {
        err = memErrNotEnoughSpace;
        goto Done;
    }
    
    err = reader->open(globalPrefsStream);
    if (errNone != err)
        goto Done;
        
    serializer = new_nt Serializer(*reader);
    if (NULL == serializer)
    {
        err = memErrNotEnoughSpace;
        goto Done;
    }
    
    prefs = new_nt Preferences();
    if (NULL == prefs)
    {
        err = memErrNotEnoughSpace;
        goto Done;
    }
    
    err = prefs->serialize(*serializer);
    if (errNone == err)
        regged = !prefs->regCode.empty();

Done:
    if (NULL != prefs)
        delete prefs;
        
    delete serializer;
    delete reader;
    delete ds;
    if (errNone != err)
        return;
*/
        
Sync:
    FlickrPrefs* flickrPrefs = new_nt FlickrPrefs();
    if (NULL == flickrPrefs)
        return;

    memzero(flickrPrefs, sizeof(*flickrPrefs));
    UInt16 size = sizeof(*flickrPrefs);
    PrefGetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, flickrPrefs, &size, true);
    flickrPrefs->registered = regged;
    PrefSetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, flickrPrefsVersion, flickrPrefs, sizeof(*flickrPrefs), true);
    delete flickrPrefs;        
}

UInt32 FlickrGetResetPictureCount()
{
    FlickrPrefs* flickrPrefs = new_nt FlickrPrefs();
    if (NULL == flickrPrefs)
        return 0;

    memzero(flickrPrefs, sizeof(*flickrPrefs));
    UInt16 size = sizeof(*flickrPrefs);
    PrefGetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, flickrPrefs, &size, true);

    UInt32 count = flickrPrefs->uploadedPicturesCount;
    flickrPrefs->uploadedPicturesCount = 0;
    
    PrefSetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, flickrPrefsVersion, flickrPrefs, sizeof(*flickrPrefs), true);
    delete flickrPrefs;        
    return count;
}

/*
Err FlickrDatabasesDifferent(bool& result)
{
    Err err = errNone;
    MemHandle embH = NULL;
    void* embP = NULL;
    MemHandle dbH = NULL;
    void* dbP = NULL;
    DmOpenRef db = DmOpenDatabaseByTypeCreator(sysFileTExgLib, FlickrCreatorID, dmModeReadOnly);
    if (NULL == db)
    {
        result = true;
        return errNone;
    }        
    result = false;
    
    DmDatabaseInfo
    
    
    embH = DmGet1Resource(sysResTAppGData, flickrExchangeLibrary);
    if (NULL == embH)
    {   
        err = DmGetLastErr();
        goto Finish;
    }
    UInt32 embSize = MemHandleSize(embH);
    
    
    
    embP = MemHandleLock(embH);
    if (NULL == embP)
    {
        err = memErrChunkNotLocked;
        goto Finish;
    }

    


Finish:
    if (NULL != embP)
        MemHandleUnlock(embH);
    if (NULL != embH)        
        DmReleaseResource(embH);
        
        
    if (NULL != db)
        DmCloseDatabase(db);        
    return err;
}
*/