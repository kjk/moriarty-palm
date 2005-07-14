#include "eBookFormats.hpp"
#include "MoriartyPreferences.hpp"
#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"
#include <HistoryCache.hpp>

static status_t VFSMakeDirs(UInt16 targetVolume, const char* path)
{
    long start = 1;
    long pos = start;
    CDynStr str;
    bool finish = false;
    while (!finish)
    {
        pos = StrFind(path + start, -1, '/');
        if (-1 == pos)
        {
            pos = tstrlen(path + start);
            finish = true;
        }
        
            
        if (NULL == str.AppendChar('/'))
            return memErrNotEnoughSpace;
        if (NULL == str.AppendCharPBuf(path + start, pos))
            return memErrNotEnoughSpace;
        
        Err err = VFSDirCreate(targetVolume, str.GetCStr());
        if (vfsErrFileAlreadyExists == err)
            err = errNone;
        
        if (errNone != err)
            return err;
        
        start += pos + 1;
   }
   return errNone;
}

eBookDownloadHandler::eBookDownloadHandler():
    info_(NULL),
    vfsVolume_(vfsVolumeMainMemory),
    file_(NULL),
    length_(0),
    totalLength_(0),
    image_(NULL),
    fileName_(NULL)
{
}

static bool VFSFileExists(UInt16 volume, const char* name)
{
    FileRef f;
    status_t err = VFSFileOpen(volume, name, vfsModeRead, &f);
    if (errNone == err)
    {
        VFSFileClose(f);
        return true;
    }
    return false;
}

status_t eBookDownloadHandler::initialize(UInt16 vfsVolume, const char_t* info, ulong_t databaseSize)
{
    vfsVolume_ = vfsVolume;
    totalLength_ = databaseSize;

    info_ = StringCopy2(info);
    if (NULL == info_)
        return memErrNotEnoughSpace;

    long pos = StrFind(info_, -1, ';');
        
    status_t err;
    if (vfsVolumeMainMemory != vfsVolume_)
    {
        err = VFSMakeDirs(vfsVolume, eBook_DOWNLOAD_PATH);
        if (errNone != err)
            return err;
            
        CDynStr str;
        if (NULL == str.AppendCharP(eBook_DOWNLOAD_PATH "/"))
            return memErrNotEnoughSpace;
        
        if (NULL == str.AppendCharPBuf(info_, pos))
            return memErrNotEnoughSpace;
            
        if (NULL == str.AppendCharP(".pdb"))
            return memErrNotEnoughSpace;
            
        fileName_ = str.ReleaseStr();
        
        if (VFSFileExists(vfsVolume_, fileName_))
        {
            if (eBook_ConfirmOverwrite(vfsVolume_))
                VFSFileDelete(vfsVolume_, fileName_);
            else
                return netErrUserCancel;
        }
        
        err = VFSFileOpen(vfsVolume_, fileName_, vfsModeCreate | vfsModeWrite, &file_);
        if (errNone != err)
            return err;
        
        err= VFSFileResize(file_, totalLength_);
        if (errNone != err)
        {
            VFSFileClose(file_);
            file_ = NULL;
            
            VFSFileDelete(vfsVolume, fileName_);
            return err;
        }
       
        VFSFileSeek(file_, vfsOriginBeginning, 0);
    }
    else
    {
        fileName_ = StringCopy2N(info_, pos);
        if (NULL == fileName_)
            return memErrNotEnoughSpace;
            
        LocalID locId = DmFindDatabase(0, fileName_);
        if (0 != locId)
        {
            if (eBook_ConfirmOverwrite(vfsVolume_))
                DmDeleteDatabase(0, locId);
            else
                return netErrUserCancel;                
        }            
           
        image_ = (char*)malloc(totalLength_);
        if (NULL == image_)
            return memErrNotEnoughSpace;
    }
    return errNone;
}

eBookDownloadHandler::~eBookDownloadHandler()
{
    if (NULL != file_)
        VFSFileClose(file_);

    if (NULL != image_)
        free(image_);
    
    FreeCharP(&info_);
    FreeCharP(&fileName_);
}

status_t eBookDownloadHandler::handleIncrement(const char_t* payload, ulong_t& length, bool finish)
{
    assert(length_ + length <= totalLength_);
    status_t err;
    
    UInt32 type, creator;
    
    if (vfsVolumeMainMemory != vfsVolume_)
    {
        UInt32 written;
        err = VFSFileWrite(file_, length, payload, &written);

  // VFSFileDBInfo() seems to be slightly broken - when called here it returns buggy results
        if (finish && errNone == err)
        {
            err = VFSFileSeek(file_, vfsOriginBeginning, 0);
            err = VFSFileDBInfo(file_, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, &type, &creator, NULL);
            err = errNone;
        }
             
        if (finish)
        {
            VFSFileClose(file_);
            file_ = NULL;
        }
 
        if (errNone != err)
        {
            VFSFileDelete(vfsVolume_, fileName_);
            return err;
        }

        length = written;
    }
    else
    {
        MemMove(image_ + length_, payload, length);
        if (finish)
        {
            err = DmCreateDatabaseFromImage(image_);
            free(image_);
            image_ = NULL;
            
            if (errNone != err)
                return err;

            LocalID locId = DmFindDatabase(0, fileName_);
            assert(0 != locId);
            
            err = DmDatabaseInfo(0, locId, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, &type, &creator);
            if (errNone != err)
            {
                DmDeleteDatabase(0, locId);
                return err;
            }
        }
    }
    length_ += length;
    
    if (finish)
    {
        EBookPreferences& prefs = MoriartyApplication::instance().preferences().ebookPrefs;
        if (-1 == StrArrFind(prefs.managedEBooks, prefs.managedEBooksSize, info_))
            StrArrAppendStrCopy(prefs.managedEBooks, prefs.managedEBooksSize, info_);
    }
    return errNone;
}
 
enum {
    readerDatabaseTypeAny = 0,
    readerDatabaseCreatorAny = 0
};
   
struct EBookFormatDescriptor {
    EBookFormat format; 
    UInt32 type;
    UInt32 creator;
};

static const EBookFormatDescriptor eBookFormatDescriptors[] = {
    {ebookFormat_eReader,   readerDatabaseType_eReader,     readerDatabaseCreator_eReader},
    {ebookFormat_iSilo,           readerDatabaseType_ToGo,           readerDatabaseCreator_ToGo},
    {ebookFormat_zTXT,          readerDatabaseType_zTXT,          readerDatabaseCreator_zTXT},
    {ebookFormat_Doc,           readerDatabaseType_TEXt,           readerDatabaseCreator_REAd},
    {ebookFormat_iSiloX,        readerDatabaseTypeSilo,               readerDatabaseCreatorSiloX},
    {ebookFormat_iSilo,        readerDatabaseTypeSilo,               readerDatabaseCreatorSilo},
    {ebookFormat_Plucker,    readerDatabaseTypePlucker,         readerDatabaseCreatorPlucker},
};

EBookFormat eBook_DetectBookFormat(UInt32 creator, UInt32 type)
{
    EBookFormat format = ebookFormat_Unknown;
    for (uint_t i = 0; i < ARRAY_SIZE(eBookFormatDescriptors); ++i)
    {
        const EBookFormatDescriptor& desc = eBookFormatDescriptors[i];
        if (readerDatabaseTypeAny != desc.type && desc.type != type)
            continue;
        if (readerDatabaseCreatorAny != desc.creator && desc.creator != creator)
            continue;
        return desc.format;
    }
    return format;   
}

status_t eBook_DetectDatabaseFormat(UInt16 vfsVolume, const char_t* dbName, EBookFormat& format)
{
    UInt32 type, creator;
    Err err;
    if (vfsVolumeMainMemory == vfsVolume)
    {
        LocalID lid = DmFindDatabase(0, dbName);
        if (0 == lid)
            return DmGetLastErr();
        
        err = DmDatabaseInfo(0, lid, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, &type, &creator);
        if (errNone != err)
            return err;
        
        format = eBook_DetectBookFormat(creator, type);
        return errNone;
    }
    else
    {
        FileRef ref;
        err = VFSFileOpen(vfsVolume, dbName, vfsModeRead, &ref);
        if (errNone != err)
            return err;
            
        err = VFSFileDBInfo(ref, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, &type, &creator, NULL);
        if (errNone == err)
            format = eBook_DetectBookFormat(creator, type);
            
        VFSFileClose(ref);
        
        return err;
    }
}

struct EBookReaderDescriptor {
    EBookReader reader;
    const char* name;
    UInt32 creator;
    EBookFormats formats;
    bool supportsGoTo;
};

// TODO: verify supportsGoTo correctness
// iSilo - works; TiBR - doesn't work; eReader - doesn't open the db, but app starts
static const EBookReaderDescriptor eBookReaderDescriptors[] = {
    {ebookReader_eReader, readerAppName_eReader, readerAppCreator_eReader, ebookFormat_eReader | ebookFormat_Doc, false},
    {ebookReader_iSilo,       readerAppNameSilo,          readerAppCreatorSilo,         ebookFormat_iSilo | ebookFormat_iSiloX | ebookFormat_Doc, true},
    {ebookReader_Weasel,    readerAppName_Weasel,   readerAppCreator_Weasel, ebookFormat_Doc | ebookFormat_zTXT, false},
    {ebookReader_Plucker,   readerAppNamePlucker,    readerAppCreatorPlucker,    ebookFormat_Plucker, true},
    {ebookReader_CSpotRun, readerAppName_CSpotRun, readerAppCreator_CSpotRun, ebookFormat_Doc, false},
    {ebookReader_TiBR,      readerAppNameTiBR,         readerAppCreatorTiBR,        ebookFormat_Doc, false},
    {ebookReader_QExpress, readerAppName_QExpress, readerAppCreator_QExpress, ebookFormat_Doc, false},
};

static bool AppDbExists(UInt32 creator, UInt16& cardNo, LocalID& id)
{
    DmSearchStateType searchState;
    Err err = DmGetNextDatabaseByTypeCreator(true, &searchState, 'appl', creator, true, &cardNo, &id);
    return (errNone == err);
}

EBookFormats eBook_DetectAvailableFormats()
{
    UInt16 cardNo; LocalID id;
    EBookFormats formats = 0;
    for (uint_t i = 0; i < ARRAY_SIZE(eBookReaderDescriptors); ++i)
    {
        const EBookReaderDescriptor& desc = eBookReaderDescriptors[i];
        if (AppDbExists(desc.creator, cardNo, id))
            formats |= desc.formats;
    }
    return formats;
}

static status_t FindReaderForFormat(EBookFormat format, UInt16& cardNo, LocalID& id, EBookReader& reader)
{
    for (uint_t i = 0; i < ARRAY_SIZE(eBookReaderDescriptors); ++i)
    {
        const EBookReaderDescriptor& desc = eBookReaderDescriptors[i];
        if (0 == (format & desc.formats))
            continue;
            
        if (AppDbExists(desc.creator, cardNo, id))
        {
            reader = desc.reader;
            return errNone;
        }
    }
    return dmErrCantOpen;
}

EBookReader eBook_DetectReaderForFormat(EBookFormat format)
{
    EBookReader reader; UInt16 cardNo; LocalID id;
    status_t err = FindReaderForFormat(format, cardNo, id, reader);
    if (errNone != err)
        return ebookReader_None;
    return reader;
}

bool eBook_ReaderSupportsGoTo(EBookReader reader)
{
    assert(ebookReader_None != reader);
    for (uint_t i = 0; i < ARRAY_SIZE(eBookReaderDescriptors); ++i)
    {
        const EBookReaderDescriptor& desc = eBookReaderDescriptors[i];
        if (reader == desc.reader)
            return desc.supportsGoTo;
    }
    assert(false);
    return false;
}

static status_t LaunchReaderGoTo(const char_t* dbName, UInt16 cardNo, LocalID id, bool goTo)
{
    LocalID docId = DmFindDatabase(0, dbName);
    if (0 == docId)
        return DmGetLastErr();
    
    if (goTo)
    {
        GoToParamsType* params = (GoToParamsType*)malloc(sizeof(GoToParamsType));
        if (NULL == params)
            return memErrNotEnoughSpace;
            
        memzero(params, sizeof(*params));
        params->dbID = docId;
        
        MemPtrSetOwner(params, 0);
        return SysUIAppSwitch(cardNo, id, sysAppLaunchCmdGoTo, params);
    }
    else
        return SysUIAppSwitch(cardNo, id, sysAppLaunchCmdNormalLaunch, NULL);
}

status_t eBook_LaunchReader(UInt16 vfsVolume, const char_t* dbName, EBookReader reader)
{
    UInt16 cardNo = 0; LocalID id = 0; bool supportsGoTo;
    assert(ebookReader_None != reader);
    for (uint_t i = 0; i < ARRAY_SIZE(eBookReaderDescriptors); ++i)
    {
        const EBookReaderDescriptor& desc = eBookReaderDescriptors[i];
        if (reader == desc.reader && AppDbExists(desc.creator, cardNo, id))
        {
            supportsGoTo = desc.supportsGoTo;
            break;
        }
    }
    if (0 == id)
        return dmErrCantOpen;
        
    EBookFormat format = ebookFormat_Unknown;
    status_t err = eBook_DetectDatabaseFormat(vfsVolume, dbName, format);
    if (errNone != err)
        return err;
        
    if (ebookFormat_Unknown == format)
        return dmErrCantOpen;
        
    if (vfsVolumeMainMemory == vfsVolume)
        return LaunchReaderGoTo(dbName, cardNo, id, supportsGoTo);
    else
        return SysUIAppSwitch(cardNo, id, sysAppLaunchCmdNormalLaunch, NULL);
}

struct EBookFormatName {
    EBookFormat format;
    const char* name;
};

// Names defined here should reflect FORMATS variable defined in ebooks.py
static const EBookFormatName formatNames[] = {
    {ebookFormat_Doc,               eBookFormatName_Doc},
    {ebookFormat_eReader,          eBookFormatName_eReader},
    {ebookFormat_iSilo,                 eBookFormatName_iSilo},
    {ebookFormat_iSiloX,                eBookFormatName_iSiloX},
    {ebookFormat_Plucker,               eBookFormatName_Plucker},
    {ebookFormat_zTXT,                  eBookFormatName_zTXT}
};

EBookFormat eBook_ParseFormatName(const char* name, ulong_t length)
{
    for (uint_t i = 0; i < ARRAY_SIZE(formatNames); ++i)
    {
        const EBookFormatName& desc = formatNames[i];
        if (StrEquals(desc.name, name, length))
            return desc.format;
    }
    assert(false);
    return ebookFormat_Unknown;
}

const char* eBook_FormatName(EBookFormat format)
{
    for (uint_t i = 0; i < ARRAY_SIZE(formatNames); ++i)
    {
        const EBookFormatName& desc = formatNames[i];
        if (desc.format == format)
            return desc.name;        
    }
    assert(false);
    return NULL;
}

EBookFormats eBook_ParseFormats(const char_t* formats, ulong_t length)
{
    EBookFormats res = 0;
    while (true)
    {
        long pos = StrFind(formats, length, _T(' '));
        if (-1 == pos)
            pos = length;
        
        EBookFormat f = eBook_ParseFormatName(formats, pos);
        res |= f;
        
        if (pos == length)
            return res;
        
        ++pos;
        formats += pos;
        length -= pos;
    }
}

status_t eBook_FormatsToText(EBookFormats mask, DynStr* out)
{
    assert(NULL != out);
    bool trunc = false;
    for (uint_t i = 0; i < ARRAY_SIZE(formatNames); ++i)
    {
        const EBookFormatName& desc = formatNames[i];
        if (0 == (desc.format & mask))
            continue;

        if (NULL == DynStrAppendCharP2(out, desc.name, _T(" ")))
            return memErrNotEnoughSpace;
     
        trunc = true;       
    }
    if (trunc)
        DynStrTruncate(out, DynStrLen(out) - 1);
    return errNone;
}

status_t eBook_Copy(UInt16 srcVolume, const char_t* name, UInt16 targetVolume)
{
    CDynStr str;
    LocalID id;
    Err err;
    if (vfsVolumeMainMemory == srcVolume)
    {   
        if (NULL == str.AppendCharP3(eBook_DOWNLOAD_PATH "/", name, ".pdb"))
            return memErrNotEnoughSpace;
            
        id = DmFindDatabase(0, name);
        if (0 == id)
        {
            err = DmGetLastErr();
            return err;
        }    

        err = VFSMakeDirs(targetVolume, eBook_DOWNLOAD_PATH);
        if (errNone != err)
            return err;    
        

        if (VFSFileExists(targetVolume, str.GetCStr()))
        {
            if (eBook_ConfirmOverwrite(targetVolume))
                VFSFileDelete(targetVolume, str.GetCStr());
            else
                return netErrUserCancel;
        }
        
        err = VFSExportDatabaseToFile(targetVolume, str.GetCStr(), 0,  id);
        return err;
    }
    else if (vfsVolumeMainMemory == targetVolume)
    {
        UInt16 cardNo = 0;
        
        long last = 0;
        while (true)
        {
            long pos = StrFind(name + last, -1, '/');
            if (-1 != pos)
                last += pos + 1;
            else
                break;
        }
        
        long len = StrLen(name) - last;
        if (len > 4)
            len -= 4;
        
        if (NULL == str.AppendCharPBuf(name + last, len))
            return memErrNotEnoughSpace;
        
        LocalID id = DmFindDatabase(0, str.GetCStr());
        if (0 != id)
        {
            if (eBook_ConfirmOverwrite(targetVolume))
                DmDeleteDatabase(0, id);
            else
                return netErrUserCancel;                
        }            
        
        err = VFSImportDatabaseFromFile(srcVolume, name, &cardNo, &id);
        return err;
    }
    else
    {
        err = VFSMakeDirs(targetVolume, eBook_DOWNLOAD_PATH);
        if (errNone != err)
            return err;    
        

        if (VFSFileExists(targetVolume, name))
        {
            if (eBook_ConfirmOverwrite(targetVolume))
                VFSFileDelete(targetVolume, name);
            else
                return netErrUserCancel;
        }
            
        FileRef from = NULL, to = NULL;
        void* buffer = NULL;
        
        err = VFSFileOpen(srcVolume, name, vfsModeRead, &from);
        if (errNone != err)
            return err;

        err = VFSFileOpen(targetVolume, name, vfsModeWrite | vfsModeCreate, &to);
        if (errNone != err)
            goto Finish;

        
        buffer = malloc(1024);
        if (NULL == buffer)
        {
            err = memErrNotEnoughSpace;
            goto Finish;
        }

        while (true)
        {
            UInt32 read = 0;            
            err = VFSFileRead(from, 1024, buffer, &read);
            if (errNone != err)
                goto Finish;
            
            UInt32 wrt = 0;
            err = VFSFileWrite(to, read, buffer, &wrt);
            if (errNone != err)
                goto Finish;
            
            if (1024 != read)
                break;
        }            
Finish:
        if (NULL != buffer)
            free(buffer);
        if (NULL != to)
            VFSFileClose(to);
        if (NULL != from)
            VFSFileClose(from);
        return err;
    }
}

status_t eBook_Delete(UInt16 volume, const char_t* name)
{
    if (vfsVolumeMainMemory == volume)
    {
        LocalID id = DmFindDatabase(0, name);
        if (0 == id)
            return DmGetLastErr();
        
        return DmDeleteDatabase(0, id);
    }
    else
        return VFSFileDelete(volume, name);
}

status_t eBook_Move(UInt16 srcVolume, const char_t* name, UInt16 targetVolume)
{
    status_t err = eBook_Copy(srcVolume, name, targetVolume);
    if (errNone != err)
        return err;
    return eBook_Delete(srcVolume, name);
}

bool eBook_ParseDatabaseInfo(const char_t* info, ulong_t& dbNameLen, const char_t*& author, ulong_t& authorLen, const char_t*& title, ulong_t& titleLen)
{
    ulong_t len = tstrlen(info);
    long pos = StrFind(info, len, _T(';'));
    if (-1 == pos)
        return false;
    
    dbNameLen = pos++;
    author = info + pos;
    len -= pos;
    pos = StrFind(author, len, _T(';'));
    if (-1 == pos)
        return false;
    
    authorLen = pos++;
    title = author + pos;
    len -= pos;
    strip(author, authorLen);
    titleLen = len;
    strip(title, titleLen);
    return true;    
}

void eBook_ExpireCache(LookupManager& lm)
{
    EBookPreferences& prefs = MoriartyApplication::instance().preferences().ebookPrefs;
    if (lm.ebookVersion > prefs.version)
    {
        HistoryCache cache;
        Err err = cache.open(ebookWelcomeCacheName);
        if (errNone != err)
            return;

        uint_t i = cache.entriesCount();
        while (i > 0)
            cache.removeEntry(--i);
        cache.close();            
    }
}

bool eBook_ConfirmOverwrite(UInt16 targetVfsVolume)
{
    const char* type = "database";
    if (vfsVolumeMainMemory != targetVfsVolume)
        type = "file";
        
    UInt16 res = FrmCustomAlert(confirmOverwriteAlert, type, "", "");
    return 0 == res;
}

