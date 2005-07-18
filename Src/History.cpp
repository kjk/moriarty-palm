#include "History.hpp"
#include "ModulesData.hpp"
#include "HyperlinkHandler.hpp"
#include <Text.hpp>
#include <DynStr.hpp>
#include <HistoryCache.hpp>
#include "PediaCacheDataRead.hpp"

#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"
#include <UniversalDataHandler.hpp>
#include <SysUtils.hpp>
#include <ByteFormatParser.hpp>

static status_t UDF_CacheDataRead(Reader& reader, LookupResult result, UniversalDataFormat& udf)
{
//    MoriartyApplication& app = MoriartyApplication::instance();
//    LookupManager* lm = app.lookupManager;

    status_t err= readUniversalDataFromReader(reader, udf);
    if (errNone != err)
        return err;

    LookupFinishedEventData data(result);
    sendEvent(LookupManager::lookupFinishedEvent, data);
    return errNone;
}

static status_t AmazonCacheDataRead(const char_t* title, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    return UDF_CacheDataRead(reader, lookupResultAmazon, lm->amazonData);
}

static status_t EBayCacheDataRead(const char_t* title, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    return UDF_CacheDataRead(reader, lookupResultEBay, lm->eBayData);
}

static status_t NetflixCacheDataRead(const char_t* title, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    return UDF_CacheDataRead(reader, lookupResultNetflix, lm->netflixData);
}

static status_t ListsOfBestsCacheDataRead(const char_t* title, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    return UDF_CacheDataRead(reader, lookupResultListsOfBests, lm->listsOfBestsData);
}

static status_t LyricsCacheDataRead(const char_t* title, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    return UDF_CacheDataRead(reader, lookupResultLyrics, lm->lyricsData);
}

static status_t DictCacheDataRead(const char_t* title, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    return UDF_CacheDataRead(reader, lookupResultDictDef, lm->dictData);
}

static status_t EBookSearchDataRead(const char_t* title, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    DefinitionModel* model;
    status_t err = ReadByteFormatFromReader(reader, model);
    if (errNone != err)
        return err;
        
    model->setTitle(title);
    PassOwnership(model, lm->eBookModel);    
    
    LookupFinishedEventData data(lookupResultEBookSearchResults);
    sendEvent(LookupManager::lookupFinishedEvent, data);
    return errNone;
}

static status_t EBookBrowseDataRead(const char_t*, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    DefinitionModel* model;
    status_t err = ReadByteFormatFromReader(reader, model);
    if (errNone != err)
        return err;
        
    PassOwnership(model, lm->eBookModel);    
    
    LookupFinishedEventData data(lookupResultEBookBrowse);
    sendEvent(LookupManager::lookupFinishedEvent, data);
    return errNone;
}

static status_t EBookWelcomeDataRead(const char_t*, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    DefinitionModel* model;
    status_t err = ReadByteFormatFromReader(reader, model);
    if (errNone != err)
        return err;
        
    PassOwnership(model, lm->eBookModel);    
    
    LookupFinishedEventData data(lookupResultEBookHome);
    sendEvent(LookupManager::lookupFinishedEvent, data);
    return errNone;
}


typedef status_t (* CacheDataReadHandler)(const char_t* title, Reader&);

struct UrlSchemaToCacheNameEntry
{
    const char_t*        urlSchema;
    const char_t*        cacheName;
    CacheDataReadHandler readHandler;
};

static UrlSchemaToCacheNameEntry schemaToCacheNameDispatch[] = 
{
    {urlSchemaDictTerm,           dictHistoryCacheName,         DictCacheDataRead},
    {urlSchemaDictRandom,         dictHistoryCacheName,         DictCacheDataRead},
    {_T("hs+dictstats"),          dictHistoryCacheName,         DictCacheDataRead},
    {_T("Hs+dictstats"),          dictHistoryCacheName,         DictCacheDataRead},

    
    {urlSchemaEncyclopediaTerm,   pediaHistoryCacheName,        PediaCacheDataRead},
    {urlSchemaEncyclopediaSearch, pediaHistoryCacheName,        PediaSearchDataRead},
    
    {urlSchemaEBookBrowse,          ebookHistoryCacheName,          EBookBrowseDataRead},
    {urlSchemaEBookHome,          ebookWelcomeCacheName,          EBookWelcomeDataRead},
    {urlSchemaEBookSearch,          ebookHistoryCacheName,          EBookSearchDataRead},
    
    {_T("s+amazonbrowse"),        amazonHistoryCacheName,       AmazonCacheDataRead},
    {_T("s+amazonsearch"),        amazonHistoryCacheName,       AmazonCacheDataRead},
    {_T("s+amazonitem"),          amazonHistoryCacheName,       AmazonCacheDataRead},
    {_T("s+amazonlist"),          amazonHistoryCacheName,       AmazonCacheDataRead},
    {_T("s+amazonwishlist"),      amazonHistoryCacheName,       AmazonCacheDataRead},
    
    {_T("s+netflixbrowse"),       netflixHistoryCacheName,      NetflixCacheDataRead},
    {_T("s+netflixsearch"),       netflixHistoryCacheName,      NetflixCacheDataRead},
    {_T("s+netflixitem"),         netflixHistoryCacheName,      NetflixCacheDataRead},
    
    {_T("s+listsofbestsitem"),    listsOfBestsHistoryCacheName, ListsOfBestsCacheDataRead},
    {_T("s+listsofbestssearch"),  listsOfBestsHistoryCacheName, ListsOfBestsCacheDataRead},
    {_T("s+listsofbestsbrowse"),  listsOfBestsHistoryCacheName, ListsOfBestsCacheDataRead},

    {_T("s+ebay"),                eBayHistoryCacheName,         EBayCacheDataRead},
    {_T("hs+ebay"),               eBayHistoryCacheName,         EBayCacheDataRead},
    {_T("Hs+ebay"),               eBayHistoryCacheName,         EBayCacheDataRead},

    {_T("s+lyricssearch"),        lyricsHistoryCacheName,       LyricsCacheDataRead},
    {_T("s+lyricsitem"),          lyricsHistoryCacheName,       LyricsCacheDataRead}
};

static const UrlSchemaToCacheNameEntry* CacheNameForUrl(const char_t* url)
{
    assert(NULL != url);
    long i = StrFind(url, -1, urlSeparatorSchema);
    if (-1 == i)
        return NULL;
    CDynStr str;
/*    
    long f = StrFind(url, -1, urlSeparatorFlags);
 */    
    if (NULL == str.AppendCharPBuf(&url[0], i))
        return NULL;
    const UrlSchemaToCacheNameEntry* cache = NULL;
    for (i = 0; i < ARRAY_SIZE(schemaToCacheNameDispatch); ++i)
    {
        if (0 == tstrcmp(str.GetCStr(), schemaToCacheNameDispatch[i].urlSchema))
        {
            cache = &schemaToCacheNameDispatch[i];
            break;
        }
    }
    return cache;
}

bool ReadUrlFromCache(HistoryCache& cache, const char_t* url)
{
    const UrlSchemaToCacheNameEntry* cacheData = CacheNameForUrl(url);
    if (NULL == cacheData || NULL == cacheData->readHandler)
        return false;
    
    ulong_t index = cache.entryIndex(url);
    if (HistoryCache::entryNotFound == index)
        return false;
    
    if (0 != tstrcmp(cacheData->cacheName, cache.dataStore->name()))
    {
        assert(cache.entryIsOnlyLink(index));
        return false;
    }     

    DataStoreReader* reader = cache.readerForEntry(index);
    if (NULL == reader)
        return false;

    status_t err = cacheData->readHandler(cache.entryTitle(index), *reader);
    delete reader;
    return (errNone == err);
}

bool ReadUrlFromCache(const char_t* url)
{
    const UrlSchemaToCacheNameEntry* cacheData = CacheNameForUrl(url);
    if (NULL == cacheData || NULL == cacheData->readHandler)
        return false;
        
    assert(StrStartsWith(url, -1, cacheData->urlSchema, -1));

    HistoryCache cache;
    status_t err = cache.open(cacheData->cacheName);
    if (errNone != err)
        return false;

    assert(StrStartsWith(url, -1, cacheData->urlSchema, -1));

    ulong_t index = cache.entryIndex(url);
    if (HistoryCache::entryNotFound == index)
        return false;

    if (errNone != (err = cache.moveEntryToEnd(index)))
        return false;

    DataStoreReader* reader = cache.readerForEntry(index);
    if (NULL == reader)
        return false;

    err = cacheData->readHandler(cache.entryTitle(index), *reader);
    delete reader;
    return (errNone == err);
}

status_t ReadByteFormatFromReader(Reader& reader, DefinitionModel*& model)
{
    ByteFormatParser* parser = new_nt ByteFormatParser();
    if (NULL == parser)
        return memErrNotEnoughSpace;
    
    status_t err = FeedHandlerFromReader(*parser, reader);
    if (errNone != err)
    {
        delete parser;
        return err;
    }

    model = parser->releaseModel();
    delete parser;
    if (NULL == model)
        return memErrNotEnoughSpace;

    return errNone;
}

