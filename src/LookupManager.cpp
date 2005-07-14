#include <Text.hpp>
#include <DeviceInfo.hpp>

#include "MoriartyPreferences.hpp"
#include "MoriartyConnection.hpp"
#include "LookupManager.hpp"

#include "Forms/ConnectionProgressForm.hpp"

#include "History.hpp"
#include "DefinitionElement.hpp"
#include "HyperlinkHandler.hpp"

#include <SysUtils.hpp>

#include <HistorySupport.hpp>

#ifdef __MWERKS__
#pragma pcrelconstdata on
#endif

// TODO: the same is in FieldPayloadProtocolConnection.cpp
#define lineSeparator _T("\n")
#define lineSeparatorChar _T('\n')

// Given a fieldName and fieldValue, make it a protocol field and add to the
// existing request.
// Format of protocol field:
// - if we have value: fieldName ": " fieldValue lineSeparator
// - if we don't have value: fieldName ":" lineSeparator
// Return NULL if failed to add it to existing request (memory allocation failed)
// TODO: this should always use char * instead of char_t * since we're constructing
// a char * value in the end
DynStr *DynStrAddField(DynStr *dstr, const char_t *fieldName, const char_t *fieldValue)
{
    assert(NULL != fieldName);
    // TODO: could be optimized
    if (NULL == DynStrAppendCharP(dstr, fieldName))
        return NULL;

    if (NULL == fieldValue)
    {
        if (NULL == DynStrAppendCharP(dstr, _T(":")))
            return NULL;
    }
    else
    {
        if (NULL == DynStrAppendCharP(dstr, _T(": ")))
            return NULL;

        if (NULL == DynStrAppendCharP(dstr, fieldValue))
            return NULL;
    }

    if (NULL == DynStrAppendCharP(dstr, lineSeparator))
        return NULL;

    return dstr;
}

DynStr* DynStrAddField(DynStr* dstr, const char_t* fieldName, long numValue)
{
    char_t buffer[12] = {chrNull};
    tprintf(buffer, _T("%ld"), numValue);
    return DynStrAddField(dstr, fieldName, buffer);
}

DynStr *BuildRequestCommonFields(ulong_t transactionId)
{
    // TODO: instrument the code to dump the final size of request to a file
    // so that we can analyze it and select the size of the buffer that is both
    // small yet big enough to avoid re-allocation in majority of cases. 512
    // is just a guess
    DynStr *request = DynStrNew(512);
    if (NULL == request)
        goto Error;

    if (NULL == DynStrAddField(request, protocolVersionField, protocolVersion))
        goto Error;

    if (NULL == DynStrAddField(request, clientInfoField, clientInfo))
        goto Error;

    char_t buffer[9];
    tprintf(buffer, _T("%08lx"), transactionId);
    if (NULL == DynStrAddField(request, transactionIdField, buffer))
        goto Error;

    MoriartyApplication& app = MoriartyApplication::instance();

    if (!app.preferences().regCode.empty())
    {
        if (NULL == DynStrAddField(request, regCodeField, app.preferences().regCode.c_str()))
            goto Error;
        if (REG_CODE_DAYS_NOT_SET == app.regCodeDaysToExpire)
        {
            if (NULL == DynStrAddField(request, getRegCodeDaysToExpireField, (const char_t*)NULL))
                goto Error;
        }
    }
    else if (app.preferences().cookie.empty())
    {
        String token = deviceInfoToken();
        if (NULL == DynStrAddField(request, getCookieField, token.c_str()))
            goto Error;
    }
    else
    {
        if (NULL == DynStrAddField(request, cookieField, app.preferences().cookie.c_str()))
            goto Error;
    }

    if (!app.fLatestClientVersionRetrieved)
    {
        if (NULL == DynStrAddField(request, getLatestClientVersionField, _T("Palm")))
            goto Error;
    }
    return request;
Error:
    if (NULL != request)
        DynStrDelete(request);
    return NULL;    
}

// given transactionId, protocol field name and value, build full request to
// send to the server.
// Returns NULL if failed (out of memory)
// Caller needs to free the memory
char *BuildRequestOneField(ulong_t transactionId, const char_t *fieldName, const char_t *fieldValue)
{
    char   *result = NULL;
    DynStr *request = BuildRequestCommonFields(transactionId);
    if (NULL == request)
        goto Error;

    if (NULL == DynStrAddField(request, fieldName, fieldValue))
        goto Error;

    if (NULL == DynStrAppendChar(request, _T('\n')))
        goto Error;

// On WinCE char_t is utf16 unicode so we have to convert the string we've built
// to 8-bit ascii. On Palm it's already 8-bit ascii so we can just set the string
// as the request
#ifdef _PALM_OS
    result = DynStrReleaseStr(request);
#else
    result = Utf16ToStr(DynStrGetCStr(request), DynStrLen(request));
    if (NULL == result)
        goto Error;
#endif
    DynStrDelete(request);
    return result;
Error:
    if (NULL != request)
        DynStrDelete(request);
    return NULL;
}


MoriartyConnection* LookupManager::createConnection()
{
    MoriartyApplication& app = MoriartyApplication::instance();
    MoriartyConnection* conn = new_nt MoriartyConnection(*this);
    if (NULL == conn)
        return NULL;

    conn->serverAddress = app.preferences().serverAddress;
    conn->setTransferTimeout(app.ticksPerSecond()*20L);
    return conn;
}

status_t LookupManager::enqueueConnection(MoriartyConnection* conn)
{
    assert(NULL != conn);
    status_t error = conn->enqueue();
    if (errNone != error)
        delete conn;
    MoriartyApplication::popupForm(connectionProgressForm);
    return error;
}

status_t LookupManager::fetchWeather(const ArsLexis::String& location, const ArsLexis::String& locationToServer)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;
        
    conn->setWeatherLocation(location, locationToServer);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchWeather()
{
    MoriartyApplication& app = MoriartyApplication::instance();
    Preferences& prefs = app.preferences();
    return fetchWeather(prefs.weatherPreferences.weatherLocation, prefs.weatherPreferences.weatherLocationToServer);
}

status_t LookupManager::fetchMovies(const char_t* location)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;
    conn->setMoviesLocation(location);
    return enqueueConnection(conn);
}

LookupManager::LookupManager():
    lastPediaArticleTitle(NULL),
    crossModuleLookup(false),
    lastPediaLangCodes(NULL),
    lastPediaLangCodesCount(0),
    lastPediaArticle(NULL),
    lastPediaLinkingArticles(NULL),
    lastPediaLinkedArticles(NULL),
    lastPediaSearchResults(NULL),
    lastPediaLanguages(NULL),
    lastHistoryCacheName(NULL),
    lastModuleName(NULL),
    eBookDownloadInfo(NULL),
    eBookFileName(NULL),
    eBookModel(NULL),
    flickrPictureCountSent(false),
    ebookVersion(EBookPreferences::versionNotChecked)
{
    memzero(fLast411SearchActual_, sizeof(fLast411SearchActual_));
}


LookupManager::~LookupManager()
{
    delete lastPediaArticle;
    delete lastPediaLinkingArticles;
    delete lastPediaLinkedArticles;
    delete lastPediaSearchResults;
    delete lastPediaLanguages;
    
    setLastPediaArticleTitle(NULL);
    
    FreeCharP(&eBookDownloadInfo);
    FreeCharP(&eBookFileName);
    delete eBookModel;
    
    FreeStringList(lastPediaLangCodes, lastPediaLangCodesCount);
}

bool LookupManager::handleLookupFinishedInForm(const LookupFinishedEventData& data)
{
    bool handled=false;
    switch (data.result)
    {
        case lookupResultError:
            handleConnectionError(data.error);
            handled=true;
            break;
        
        case lookupResultServerError:
            handleServerError(data.serverError);
            handled=true;
            break;
            
        case lookupResultLocationUnknown:
            MoriartyApplication::alert(locationUnknownAlert);
            handled=true;
            break;

        case lookupResultNoResults:
            MoriartyApplication::alert(noResultsAlert);
            handled=true;
            break;

        case lookupResult411TooManyResults:
            MoriartyApplication::alert(tooManyResultsAlert);
            handled=true;
            break;

        case lookupResult411NoCity:
            MoriartyApplication::alert(noCityAlert);
            handled=true;
            break;
            
        case lookupResultConnectionCancelledByUser:
            handled=true;
            break;
    }
    return handled;
}

namespace {

#undef DEF_SERVER_ERR
#define DEF_SERVER_ERR(error,code,alert) \
        (ushort_t)error, alert,

    static const ushort_t serverErrorAlerts[]=
    {   
#include "ServerErrors.hpp"
    };
}

void LookupManager::handleServerError(ServerError serverError)
{
    assert(serverErrorNone!=serverError);

    int errorsCount = ARRAY_SIZE(serverErrorAlerts) / 2;
    ushort_t alertId = unknownServerErrorAlert;
    for (int i=0; i<errorsCount; i++)
    {
        if (serverErrorAlerts[i*2] == (ushort_t)serverError)
        {
            alertId = serverErrorAlerts[i*2+1];
            break;
        }
    }

    assert(unknownServerErrorAlert!=alertId);
    MoriartyApplication::alert(alertId);
}

void LookupManager::handleConnectionError(status_t error)
{
    ushort_t alertId=connectionErrorAlert;
    switch (error)
    {
        case SocketConnection::errResponseMalformed:
            alertId=malformedResponseAlert;
            break;
            
        case SocketConnection::errNetLibUnavailable:
            alertId=networkUnavailableAlert;
            break;
        
        case netErrTimeout:
            alertId=connectionTimedOutAlert;
            break;

        case netErrSocketClosedByRemote:
            // this most likely means we couldn't even connect to the server
            // i.e. server is not even running
            alertId=connectionServerNotRunning;
            break;

        case memErrNotEnoughSpace:
            alertId=notEnoughMemoryAlert;
            break;         
       
        case netErrUserCancel:
            return;
    }
    MoriartyApplication::alert(alertId);
}

status_t LookupManager::fetchReverseZip(const ArsLexis::String& zip)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->set411ReverseZip(zip);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchReverseArea(const ArsLexis::String& area)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->set411ReverseArea(area);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchInternationalCode(int countryIndex)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->set411InternationalCodeSearch(countryIndex);
    return enqueueConnection(conn);
}
    
status_t LookupManager::fetchAreaByCity(const ArsLexis::String& city, const ArsLexis::String& state)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->set411AreaByCity(city, state);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchZipByCity(const ArsLexis::String& city, const ArsLexis::String& state)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->set411ZipByCity(city, state);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchPersonData(const ArsLexis::String& firstName, const ArsLexis::String& lastName, const ArsLexis::String& cityOrZip, const ArsLexis::String& state)
{
    set411IncompleteSearch(firstName, lastName);

    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->set411PersonSearch(firstName, lastName, cityOrZip, state);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchReversePhone(const ArsLexis::String& phone)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->set411ReversePhone(phone);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchBusinessData(const ArsLexis::String& name, const ArsLexis::String& cityOrZip, const ArsLexis::String& state, bool surrounding, bool nameSearch)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->set411BusinessSearch(name, cityOrZip, state, surrounding, nameSearch);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchBusinessDataByUrl(const ArsLexis::String& url)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->set411BusinessSearchByUrl(url);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchZipByCity(const ArsLexis::String& cityState)
{
    String city, state;
    uint_t cut = cityState.find(_T(','));
    city.assign(cityState, 0, cut);
    state.assign(cityState, cut+1, String::npos);
    return fetchZipByCity(city,state);
}

status_t LookupManager::fetchAreaByCity(const ArsLexis::String& cityState)
{
    String city, state;
    uint_t cut = cityState.find(_T(','));
    city.assign(cityState,0,cut);
    state.assign(cityState, cut+1, String::npos);
    return fetchAreaByCity(city, state);
}

status_t LookupManager::fetchPersonData(const ArsLexis::String& cityState)
{
    String city, state;
    uint_t cut = cityState.find(_T(','));
    city.assign(cityState, 0, cut);
    state.assign(cityState, cut+1, String::npos);
    assert(!lastName_.empty());
    return fetchPersonData(firstName_,lastName_,city,state);
}

void LookupManager::setLast411Search(const ArsLexis::String& lastSearch, M411Indexes index)
{
    assert(0<=index && index<m411ModulesCount);
    last411Search_[index] = lastSearch;
    //make not actual all other from that structure
    if (personSearchTitle == index || 
        reversePhoneTitle == index)
    {
        fLast411SearchActual_[reversePhoneTitle] = false;
        fLast411SearchActual_[personSearchTitle] = false;
    }
    else 
    if (reverseAreaCodeTitle == index ||
        reverseZipCodeTitle == index ||
        zipByCityTitle == index ||
        areaCodeByCityTitle == index)
    {    
        fLast411SearchActual_[reverseAreaCodeTitle] = false;
        fLast411SearchActual_[reverseZipCodeTitle] = false;
        fLast411SearchActual_[zipByCityTitle] = false;
        fLast411SearchActual_[areaCodeByCityTitle] = false;
    }
    
    fLast411SearchActual_[index] = true;
}

const char_t* LookupManager::getLast411Search(M411Indexes index)
{
    assert(0<=index && index<m411ModulesCount);
    if (fLast411SearchActual_[index])
        return last411Search_[index].c_str();
    else
        return NULL;
}

const char_t* LookupManager::getLast411SearchAreaCityZip()
{
    if (fLast411SearchActual_[reverseAreaCodeTitle])
        return last411Search_[reverseAreaCodeTitle].c_str();
    else if (fLast411SearchActual_[reverseZipCodeTitle])
        return last411Search_[reverseZipCodeTitle].c_str();
    else if (fLast411SearchActual_[zipByCityTitle])
        return last411Search_[zipByCityTitle].c_str();
    else if (fLast411SearchActual_[areaCodeByCityTitle])
        return last411Search_[areaCodeByCityTitle].c_str();
    return NULL; 
}

status_t LookupManager::fetchField(const char_t *fieldName, const char_t *fieldValue)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    ulong_t transactionId = conn->transactionId;
    char *request = BuildRequestOneField(transactionId, fieldName, fieldValue);
    if (NULL == request)
        return memErrNotEnoughSpace;
    conn->setRequestOwn(request, strlen(request));
    if (0 == tstrcmp(fieldName, getGasPricesField))
    {
        // this is lame
        conn->gasPricesZip = fieldValue;
    }
    return enqueueConnection(conn);
}

status_t LookupManager::fetchJoke(const ArsLexis::String& url)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->setJoke(url);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchJokesList(const ArsLexis::String& jokesListQuery)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->setJokesList(jokesListQuery);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchCurrencies()
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->setCurrenciesRequest();
    return enqueueConnection(conn);
}

status_t LookupManager::fetchStocksList(const ArsLexis::String& symbols)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->setStocksList(symbols);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchStocksListValidateLast(const ArsLexis::String& symbols)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->setStocksListValidateLast(symbols);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchStock(const ArsLexis::String& url)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->setStock(url);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchStocksByName(const ArsLexis::String& url)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->setStockByName(url);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchHoroscope(const ArsLexis::String& str)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->setHoroscope(str);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchTvProviders(const ArsLexis::String& zipCode)
{
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    conn->setTvProvidersZipCode(zipCode);
    return enqueueConnection(conn);
}

status_t LookupManager::fetchUrl(const ArsLexis::char_t *url)
{
    // remove all flags except 's' from url
    // for now only 'c' flag is used
    int offset = 0;
    while (urlFlagServer != url[offset])
    {
        offset++;
        assert(_T('\0') != url[offset]);
    }   
    assert(urlSeparatorFlags == url[offset+1]);
    // read from cache
    if (offset > 0)
    {
        if (urlFlagHistory == url[offset-1] || urlFlagHistoryInCache == url[offset-1])
            offset--;
    }       
    if (ReadUrlFromCache(&url[offset]))
        return errNone;
        
    MoriartyConnection* conn = createConnection();
    if (NULL == conn)
        return memErrNotEnoughSpace;

    if (NULL == conn->setUrl(&url[offset]))
        return memErrNotEnoughSpace;
        
    return enqueueConnection(conn);
}


bool HandleCrossModuleLookup(const EventType& event, const char_t* cacheName, const char_t* moduleName)
{
    assert(LookupManager::lookupFinishedEvent == event.eType);
    const LookupFinishedEventData& data = reinterpret_cast<const LookupFinishedEventData&>(event.data);
    int moduleId = -1;
    switch (data.result)
    {
        case lookupResultPediaArticle:
        case lookupResultPediaSearch:
        case lookupResultPediaStats:
            moduleId = moduleIdPedia;
            break;
            
        case lookupResultLyrics:
            moduleId = moduleIdLyrics;
            break;
        
        case lookupResultAmazon:
            moduleId = moduleIdAmazon;
            break;
            
        case lookupResultListsOfBests:
            moduleId = moduleIdListsOfBests;
            break;

        case lookupResultNetflix:
        case lookupResultNetflixLoginUnknown:
        case lookupResultNetflixRequestPassword:
        case lookupResultNetflixLoginOk:
            moduleId = moduleIdNetflix;
            break;

        case lookupResultEBay:
        case lookupResultEBayNoCache:
        case lookupResultEBayLoginUnknown:
        case lookupResultEBayRequestPassword:
        case lookupResultEBayLoginOk:
            moduleId = moduleIdEBay;
            break;

        case lookupResultDictDef:
            moduleId = moduleIdDict;
            break;
        
        case lookupResultEBookSearchResults:
        case lookupResultEBookDownload:
        case lookupResultEBookBrowse:
        case lookupResultEBookHome:
            moduleId = moduleIdEBooks;
            break;

    }
    if (-1 == moduleId)
        return false;
    
    MoriartyApplication& app = MoriartyApplication::instance();
    app.lookupManager->crossModuleLookup = true;
    app.lookupManager->lastHistoryCacheName = cacheName;
    app.lookupManager->lastModuleName = moduleName;
    app.runModuleById(ModuleID(moduleId));
    
    sendEvent(LookupManager::lookupFinishedEvent, data);
    return true;
}

void FinishCrossModuleLookup(HistorySupport& history, const char_t* moduleName)
{
    CDynStr str;
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager& lm = *app.lookupManager;
    if (!lm.crossModuleLookup)
        return;
        
    lm.crossModuleLookup = false;
    if (NULL == lm.lastHistoryCacheName)
    {   
        Log(eLogWarning, "FinishCrossModuleLookup(): lm.lastHistoryCacheName is NULL, won't write return link.", true);
        return;
    }
    const char_t* lastCacheName = lm.lastHistoryCacheName;
    lm.lastHistoryCacheName = NULL;
    
    HistoryCache thisModuleCache;
    status_t err = thisModuleCache.open(history.cacheName());
    if (errNone != err)
    {
        LogStrUlong(eLogError, "FinishCrossModuleLookup(): unable to open thisModuleCache: ", err);
        return;
    }
    
    HistoryCache prevModuleCache;
    err = prevModuleCache.open(lastCacheName);
    if (errNone != err)
    {
        LogStrUlong(eLogError, "FinishCrossModuleLookup(): unable to open prevModuleCache: ", err);
        return;
    }
    ulong_t count = thisModuleCache.entriesCount();
    if (0 == count)
    {
        Log(eLogError, "FinishCrossModuleLookup(): thisModuleCache is empty, can't write return link's url.", true);
        return;
    }
    
    const char_t* url = thisModuleCache.entryUrl(history.currentHistoryIndex);
    const char_t* title = thisModuleCache.entryTitle(history.currentHistoryIndex);
    if (NULL != moduleName && NULL != str.AppendCharP3(moduleName, _T(": "), title))
        title = str.GetCStr();
        
    err = prevModuleCache.removeEntry(url);
    if (errNone != err)
        LogStrUlong(eLogWarning, "FinishCrossModuleLookup(): unable to remove old entry from prevModuleCache: ", err);
    
    err = prevModuleCache.appendLink(url, title);
    if (errNone != err)
    {
        LogStrUlong(eLogError, "FinishCrossModuleLookup(): unable to append link to prevModuleCache: ", err);
        return;
    }
    
    count = prevModuleCache.entriesCount();
    assert(0 != count); // We just wrote an entry to that cache.
    if (1 == count)
    {
        Log(eLogWarning, "FinishCrossModuleLookup(): prevModuleCache was empty, not possible to write return link to thisModuleCache.", true);
        return;
    }
    
    url = prevModuleCache.entryUrl(count - 2);
    title = prevModuleCache.entryTitle(count - 2);
    str.Truncate(0);
    
    if (NULL != lm.lastModuleName && NULL != str.AppendCharP3(lm.lastModuleName, _T(": "), title))
        title = str.GetCStr();
            
    err = thisModuleCache.removeEntry(url);
    if (errNone != err)
        LogStrUlong(eLogWarning, "FinishCrossModuleLookup(): unable to remove old entry from thisModuleCache: ", err);
    
    count = thisModuleCache.entriesCount();
    if (0 == count)
        err = thisModuleCache.appendLink(url, title);
    else
        err = thisModuleCache.insertLink(count - 1, url, title);
        
    if (errNone != err)
    {
        Log(eLogError, "FinishCrossModuleLookup(): unable to insert return link to into thisModuleCache: ", err);
        return;
    }
    history.currentHistoryIndex = thisModuleCache.entriesCount() - 1;
}

