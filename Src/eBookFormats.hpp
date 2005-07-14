#ifndef MORIARTY_EBOOK_FORMATS_HPP__
#define MORIARTY_EBOOK_FORMATS_HPP__

#include <Debug.hpp>
#include <BaseTypes.hpp>
#include <DynStr.hpp>
#include <FieldPayloadProtocolConnection.hpp>
#include <VfsMgr.h>

#define readerAppCreator_eReader 'PPrs'
#define readerAppName_eReader "eReader"

#define readerDatabaseType_eReader 'PNRd'
#define readerDatabaseCreator_eReader readerAppCreator_eReader

#define readerAppCreatorTiBR 'TiBR'
#define readerAppNameTiBR "TiBR"

#define readerAppCreator_CSpotRun 'CSBR'
#define readerAppName_CSpotRun "CSpotRun"

#define readerDatabaseType_zTXT 'zTXT'
#define readerDatabaseCreator_zTXT 'GPlm'

#define readerAppCreatorPlucker 'Plkr'
#define readerAppNamePlucker "Plucker"

#define readerDatabaseTypePlucker 'Data'
#define readerDatabaseCreatorPlucker readerAppCreatorPlucker

#define readerAppCreatorSilo 'Silo'
#define readerAppNameSilo "iSilo"

#define readerDatabaseCreatorSilo readerAppCreatorSilo
#define readerDatabaseCreatorSiloX 'SilX'
#define readerDatabaseTypeSilo 'SDoc'

#define readerDatabaseType_ToGo 'ToGo'
#define readerDatabaseCreator_ToGo 'ToGo'

#define readerDatabaseType_TEXt 'TEXt'
#define readerDatabaseCreator_REAd 'REAd'

#define readerAppCreator_QExpress 'Q001'
#define readerAppName_QExpress "QExpress"

#define readerAppCreator_Weasel readerDatabaseCreator_zTXT
#define readerAppName_Weasel "Weasel"

#define eBookFormatName_eReader "eReader"
#define eBookFormatName_Doc         "Doc"
#define eBookFormatName_zTXT        "zTXT"
#define eBookFormatName_iSilo         "iSilo"
#define eBookFormatName_iSiloX      "iSiloX"
#define eBookFormatName_Plucker    "Plucker"

enum EBookFormat
{
    ebookFormat_Unknown = 0,
    ebookFormat_Doc = 1,
//    ebookFormat_PDF = 2,
    ebookFormat_eReader = 4,
    ebookFormat_Plucker = 8,
    ebookFormat_zTXT = 16,
    ebookFormat_iSilo = 32,
    ebookFormat_iSiloX = 64
};

EBookFormat eBook_ParseFormatName(const char* name, ulong_t length);
const char* eBook_FormatName(EBookFormat format);

enum EBookReader
{
    ebookReader_None,
    ebookReader_eReader,
    ebookReader_TiBR,
    ebookReader_Plucker,
    ebookReader_iSilo,
    ebookReader_CSpotRun,
    ebookReader_QExpress,
    ebookReader_Weasel,
};

typedef UInt32 EBookFormats;


EBookFormats eBook_DetectAvailableFormats();

status_t eBook_FormatsToText(EBookFormats mask, DynStr* out);

EBookFormats eBook_ParseFormats(const char_t* formats, ulong_t length);

enum {vfsVolumeMainMemory = UInt16(vfsIteratorStop)};

EBookReader eBook_DetectReaderForFormat(EBookFormat format);

bool eBook_ReaderSupportsGoTo(EBookReader reader);

EBookFormat eBook_DetectBookFormat(UInt32 creator, UInt32 type);

status_t eBook_DetectDatabaseFormat(UInt16 vfsVolume, const char_t* dbName, EBookFormat& format);

// @return dmErrCantOpen if format is unknown or no reader is installed for this format
status_t eBook_LaunchReader(UInt16 vfsVolume, const char_t* dbName, EBookReader reader);

status_t eBook_Copy(UInt16 srcVolume, const char_t* name, UInt16 targetVolume);

status_t eBook_Delete(UInt16 volume, const char_t* name);

status_t eBook_Move(UInt16 srcVolume, const char_t* name, UInt16 targetVolume);

#define PALM_DIRECTORY "/PALM"

#define eBook_DOWNLOAD_PATH PALM_DIRECTORY "/Books" 

// On VFS volume book is downloaded into PALM/Books directory
class eBookDownloadHandler: public FieldPayloadProtocolConnection::PayloadHandler
{
    UInt16 vfsVolume_;
    FileRef file_;
    ulong_t totalLength_;
    ulong_t length_;
    char* image_;
    char_t* info_;
    char_t* fileName_;

   
public:

    eBookDownloadHandler();
    
    status_t initialize(UInt16 vfsVolume, const char_t* databaseInfo, ulong_t databaseSize);
    
    ~eBookDownloadHandler();
    
    status_t handleIncrement(const char_t* payload, ulong_t& length, bool finish);
    
    UInt16 vfsVolume() const {return vfsVolume_;}
    const char_t* info() const {return info_;}
    const char_t* fileName() const {return fileName_;}
    
//    UInt32 type() const {return type_;}
//    UInt32 creator() const {return creator_;}
    

};

bool eBook_ParseDatabaseInfo(const char_t* info, ulong_t& dbNameLen, const char_t*& author, ulong_t& authorLen, const char_t*& title, ulong_t& titleLen);

class LookupManager;

void eBook_ExpireCache(LookupManager& lm);

bool eBook_ConfirmOverwrite(UInt16 targetVfsVolume);

#endif