#include "MoriartyPreferences.hpp"
#include <cstring>
#include "CurrencyUtils.h"

#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"

#include "eBookFormats.hpp"

#include <rsa/rsa.h>

#define SERVER_TO_USE SERVER_ARSLEXIS

// NOTE: don't add in the middle of this enum or re-arrange the order.
// We need ids to be stable across different versions of the program
// (i.e. when user upgrades the program we want the new version to be
// able to use preferences from previous version)
enum {
    serialIdServerAddress,
    serialIdCookie,
    serialIdRegCode,
    serialIdKeybardLaunchEnabled,
    serialIdRenderingPreferences,
    
    
    // This id is declared "frozen" and can't be used. 
    // It was serialized out in shipping version of InfoMan in which this module wasn't available.
    // To prevent serialization errors I assign to such modules fresh id and disable their
    // serialization until they become available.
    _serialIdEpicuriousPreferencesFrozen, 
    
    serialIdMoviesLocation,
    serialIdWeatherPreferences,
    serialIdJokesPreferences,
    serialIdStocksPreferences,
    serialIdCurrencyPreferences,
    _serialIdAmazonPreferencesFrozen,
    _serialIdNetflixPreferencesFrozen,
    serialIdGasPricesPreferences,
    _serialIdListsOfBestsPreferencesFrozen,
    serialIdHoroscopesPreferences,
    serialIdModulesDisabledStatus, 
    // Added alias for previous id to accomodate change in object's semantics
    serialIdModulesState = serialIdModulesDisabledStatus,
    serialIdBoxOfficeCompactView,
    _serialIdLyricsPreferencesFrozen,
    serialIdLatestClientVersion,
    serialIdTvListingsPreferences,
    serialIdPediaPreferences,
    serialIdEpicuriousPreferences,
    serialIdAmazonPreferences,
    serialIdNetflixPreferences,
    serialIdListsOfBestsPreferences,
    serialIdLyricsPreferences,
    serialIdFlightsPreferences,
    serialIdEBookPreferences,
    serialIdEBayPreferences,
    serialIdFlickrPreferences,
    serialIdMainFromView,
    serialIdDictionaryPreferences
};

Preferences::Preferences(): 
    serverAddress(SERVER_TO_USE),
    fKeyboardLaunchEnabled(true),
#ifndef SHIPPING
    fServerSelected(false),
#endif
    fBoxOfficeCompactView(false),
    mainFormView(0)
{
}

Preferences::EpicuriousPreferences::EpicuriousPreferences()
{
    fDisplayRecipePart[recipeName] = true;
    fDisplayRecipePart[recipeNote] = true;
    fDisplayRecipePart[recipeIngredients] = true;
    fDisplayRecipePart[recipePreperation] = true;
    fDisplayRecipePart[recipeReviews] = false;
    fDisplayRecipePart[recipeGlobalNote] = true;
}

void Preferences::EpicuriousPreferences::serialize(Serializer& serializer)
{
    for (int i = 0; i < recipePartsCount; i++)
    {
        serializer(fDisplayRecipePart[i]);
    }
}

Preferences::JokesPreferences::JokesPreferences()
{
    // but btw server (and www.jokes.com) find all when no one is checked
    for (int i = 0; i < typeTableSize; i++)
    {
        fType[i] = true;
    }
    for (int i = 0; i < categoryTableSize; i++)
    {
        fCategory[i] = true;
    }
    for (int i = 0; i < explicitnessTableSize; i++)
    {
        fExplicitness[i] = true;
    }
    minimumRating = 0;
    sortOrder = 0;
}

void Preferences::JokesPreferences::serialize(Serializer& serializer)
{
    for (int i = 0; i < typeTableSize; i++)
    {
        serializer(fType[i]);
    }
    for (int i = 0; i < categoryTableSize; i++)
    {
        serializer(fCategory[i]);
    }
    for (int i = 0; i < explicitnessTableSize; i++)
    {
        serializer(fExplicitness[i]);
    }
    serializer(minimumRating)
              (sortOrder);
}

Preferences::StocksPreferences::Portfolios::~Portfolios()
{}

Preferences::StocksPreferences::Portfolios::Portfolios()
{
    name.clear();
    symbols.clear();
    quantities.clear();
    totalValue.clear();
}

void Preferences::StocksPreferences::Portfolios::serialize(Serializer& serializer)
{
    serializer
    (name)
    (totalValue);
    uint_t size = quantities.size();
    assert (symbols.size() == size);
    serializer(size);
    quantities.resize(size);
    symbols.resize(size);
    for (uint_t i = 0; i < size; i++)
    {
        serializer
        (symbols[i])
        (quantities[i]);
    }
}

Preferences::StocksPreferences::~StocksPreferences()
{
    std::for_each(portfolios.begin(), portfolios.end(), ObjectDeleter<Portfolios>());
}

Preferences::StocksPreferences::StocksPreferences()
{
    currentPortfolio = noPortfolio;
    lastDownloadedPortfolio = noPortfolio;
    lastDownloadedStock = noPortfolio; //same as no stock (-1)
    newQuantity = 0;
    
    //add default portfolio
    if (noPortfolio != addPortfolio(_T("Default")))
        currentPortfolio = defaultPortfolio;
}

void Preferences::StocksPreferences::serialize(Serializer& serializer)
{
    serializer
    (currentPortfolio)
    (lastDownloadedPortfolio);
          
    uint_t size = portfolios.size();
    serializer(size);
    if (Serializer::directionInput == serializer.direction())
    {
        std::for_each(portfolios.begin(), portfolios.end(), ObjectDeleter<Portfolios>());        
        portfolios.resize(size);
        for (uint_t i = 0; i < size; ++i)
            portfolios[i] = new Portfolios();
    }
    else 
        assert(portfolios.size() == size);

    for (uint_t i = 0; i < size; i++)
    {
        Portfolios* p = portfolios[i];
        serializer(*p);
    }
    int ver = portfolios[0]->schemaVersion();
}

int Preferences::StocksPreferences::addPortfolio(const ArsLexis::String name)
{
    if (portfolios.size() == totalNumberOfPortfolios)
        return noPortfolio;
    int index = portfoliosCount();
    portfolios.push_back(new Portfolios());
    portfolios[index]->name.assign(name);
    portfolios[index]->symbols.push_back(_T("^DJI"));
    portfolios[index]->symbols.push_back(_T("^IXIC"));
    portfolios[index]->symbols.push_back(_T("^GSPC"));
    portfolios[index]->quantities.push_back(0);
    portfolios[index]->quantities.push_back(0);
    portfolios[index]->quantities.push_back(0);
    return index;
}

void Preferences::StocksPreferences::deletePortfolio(int index)
{
    if (index >= portfoliosCount() || 0 > index)
        return;
    portfolios.erase(portfolios.begin()+index);
}

Preferences::WeatherPreferences::WeatherPreferences()
{
    weatherLocation.clear();
    weatherLocationToServer.clear();
    fDegreesModeCelsius = false;
}

void Preferences::WeatherPreferences::serialize(Serializer& serializer)
{
    serializer
    (weatherLocation)
    (weatherLocationToServer)
    (fDegreesModeCelsius);
}

Preferences::CurrencyPreferences::CurrencyPreferences():
    commonCurrenciesCount_(0)
{
    uint_t count = CommonCurrenciesCount();
    selectedCurrencies.reserve(count);
    for (uint_t i = 0; i < count; ++i)
    {
        int index = getCurrencyIndex(GetCommonCurrencySymbol(i));
        assert(-1 != index);
        selectedCurrencies.push_back(index);
    }
    commonCurrenciesCount_ = count;
}

Preferences::CurrencyPreferences::~CurrencyPreferences()
{
}


void Preferences::CurrencyPreferences::serialize(Serializer& serializer)
{
    uint_t count = selectedCurrencies.size();
    uint_t index;
    serializer(commonCurrenciesCount_);
    serializer(count);
    if (Serializer::directionInput == serializer.direction())
    {
        selectedCurrencies.clear();
        selectedCurrencies.reserve(count);
        for (uint_t i = 0; i< count; ++i)
        {
            serializer(index);
            selectedCurrencies.push_back(index);
        }
    }
    else 
    {
        SelectedCurrencies_t::const_iterator end = selectedCurrencies.end();
        for (SelectedCurrencies_t::const_iterator it = selectedCurrencies.begin(); it != end; ++it)
        {
            index = *it;
            serializer(index);
        }
    }
}

void Preferences::CurrencyPreferences::selectCurrency(uint_t index)
{
    int common = GetCommonCurrencyIndex(index);
    SelectedCurrencies_t::iterator pos;
    if (-1 != common)
    {
        for (pos = selectedCurrencies.begin(); pos != selectedCurrencies.begin() + commonCurrenciesCount_; ++pos)
        {
            int i = GetCommonCurrencyIndex(*pos);
            assert(-1 != i);
            if (common <= i)
                break;
        }
        ++commonCurrenciesCount_;
    }
    else {
        for (pos = selectedCurrencies.begin() + commonCurrenciesCount_; pos != selectedCurrencies.end(); ++pos)
        {
            if (index < *pos)
                break;
        }
    }
    selectedCurrencies.insert(pos, index);
}

void Preferences::CurrencyPreferences::deselectCurrency(uint_t index)
{
    bool common = IsCommonCurrency(index);
    SelectedCurrencies_t::iterator pos = std::find(selectedCurrencies.begin(), selectedCurrencies.end(), index);
    assert(selectedCurrencies.end() != pos);
    selectedCurrencies.erase(pos);
    if (common)
        --commonCurrenciesCount_;
}

bool Preferences::CurrencyPreferences::isCurrencySelected(uint_t index) const
{
    SelectedCurrencies_t::const_iterator pos = std::find(selectedCurrencies.begin(), selectedCurrencies.end(), index);
    if (selectedCurrencies.end() != pos)
        return true;
    return false;
}

status_t Preferences::serialize(Serializer& serializer)
{
    volatile status_t error = errNone;
    ModulesState modulesState(MoriartyApplication::instance());
    ErrTry {
        serializer
        (moviesLocation, serialIdMoviesLocation)
        (weatherPreferences, serialIdWeatherPreferences)
        (jokesPreferences, serialIdJokesPreferences)
        (stocksPreferences, serialIdStocksPreferences)
        (currencyPreferences, serialIdCurrencyPreferences)
        (gasPricesPreferences, serialIdGasPricesPreferences)
        (horoscopesPreferences, serialIdHoroscopesPreferences)
//        (serverAddress, serialIdServerAddress)
        (cookie, serialIdCookie)
        (regCode, serialIdRegCode)
        (modulesState, serialIdModulesState)
        (fKeyboardLaunchEnabled, serialIdKeybardLaunchEnabled)
        (fBoxOfficeCompactView, serialIdBoxOfficeCompactView)
        (latestClientVersion,serialIdLatestClientVersion)
        (mainFormView, serialIdMainFromView)
        (amazonPreferences, serialIdAmazonPreferences)
    
#ifndef SHIPPING        
        (epicuriousPreferences , serialIdEpicuriousPreferences)
        (netflixPreferences, serialIdNetflixPreferences)
        (listsOfBestsPreferences, serialIdListsOfBestsPreferences)
        (lyricsPreferences, serialIdLyricsPreferences)
        (pediaPrefs, serialIdPediaPreferences)
        (flightsPreferences, serialIdFlightsPreferences)
        (ebookPrefs, serialIdEBookPreferences)
        (eBayPreferences, serialIdEBayPreferences)
        (dictionaryPreferences, serialIdDictionaryPreferences)
        
#endif        
       
        ;
    }
    ErrCatch(ex) {
        error = ex;
    } ErrEndCatch
    return error;
}

void Preferences::StocksPreferences::swap(Preferences::StocksPreferences& other)
{
    std::swap(currentPortfolio, other.currentPortfolio);
    std::swap(lastDownloadedPortfolio, other.lastDownloadedPortfolio);
    std::swap(lastDownloadedStock, other.lastDownloadedStock);
    std::swap(portfolios, other.portfolios);
}

uint_t Preferences::AmazonPreferences::schemaVersion() const
{
    return 2;
}

bool Preferences::AmazonPreferences::serializeInFromVersion(Serializer& ser, uint_t version)
{
    if (1 != version)
        return false;
    bool searchResultsPage;
    ser(searchResultsPage);
    return true;
}

void Preferences::AmazonPreferences::serialize(Serializer& serializer)
{
    serializer
    (smallMain)
    (currentLevel);
}

Preferences::AmazonPreferences::AmazonPreferences() :
    smallMain(true),
    currentLevel(-1)
{}

void Preferences::HoroscopesPreferences::serialize(Serializer& serializer)
{
    assert( -1 != downloadedSign );
    serializer
    (downloadedSign)
    (downloadedQuery);
}

Preferences::HoroscopesPreferences::HoroscopesPreferences() :
    downloadedSign(0)
{
    downloadedQuery.clear();
}

void Preferences::LyricsPreferences::serialize(Serializer& serializer)
{
}

Preferences::LyricsPreferences::LyricsPreferences()
{
}

void Preferences::NetflixPreferences::serialize(Serializer& serializer)
{
    serializer
    (login)
    (password)
    (fCookieIsOnServer)
    (fLogged);
    
    CDynStr str;
    if (NULL != encryptedCredentials)
    {
        str.AttachStr(encryptedCredentials);
        encryptedCredentials = NULL;
    }
    
    serializer(str);
    
    encryptedCredentials = str.ReleaseStr();
}

void Preferences::NetflixPreferences::forgetCredentials()
{
    if (NULL != encryptedCredentials)
    {
        free(encryptedCredentials);
        encryptedCredentials = NULL;
    }
}


Preferences::NetflixPreferences::NetflixPreferences():
    encryptedCredentials(NULL)
{
    fCookieIsOnServer = false;
    fLogged = false;
    fNeedToUpdateQueue = true;
}

Preferences::NetflixPreferences::~NetflixPreferences()
{
    if (NULL != encryptedCredentials)
        free(encryptedCredentials);
}


static status_t EncryptDynStr(DynStr* inOut)
{
    assert(NULL != inOut);
    
    status_t err = errNone;

    uint8* key = (uint8*)rsaPublicKey;
    
    const int chunkLen = rsaKeyLengthBytes - 1;
    
    const long dataLen = DynStrLen(inOut);
    int chunkCount = dataLen / chunkLen;
    if (0 != (dataLen % chunkLen))
        ++chunkCount;
    
    const long outLen = rsaKeyLengthBytes * chunkCount;
    
    uint8* data = (uint8*)DynStrGetCStr(inOut);
    uint8* rsaTmpSpace = NULL;
    uint8* out = NULL;
    
    rsaTmpSpace = (uint8*)malloc(8 * rsaKeyLengthBits);
    if (NULL == rsaTmpSpace)
    {
        err = memErrNotEnoughSpace;
        goto Cleanup;
    }   
    
    out = (uint8*)malloc(outLen + 1);
    if (NULL == out)
    {
        err = memErrNotEnoughSpace;
        goto Cleanup;
    }
    
    out[outLen] = 0;
    
    for (int i = 0; i < chunkCount; ++i)
    {
        uint8* in = data + (i * chunkLen);
        long len = dataLen - (i * chunkLen);
        if (len > chunkLen)
            len = chunkLen;
        
        uint8* o = out + (i * rsaKeyLengthBytes);
        
        int res = rsa_encrypt(in, len, o, key, rsaKeyLengthBits, rsaTmpSpace);
        if (0 != res)
        {   
            err = sysErrParamErr;
            goto Cleanup;
        }
    }
    
    assert(0 == out[outLen]);
        
    DynStrAttachCharPBuf(inOut, (char_t*)out, outLen, outLen + 1);
    out = NULL;

Cleanup:
    if (NULL != rsaTmpSpace)
    {
        // rsaTmpSpace is tainted - such buffers should be zero'ed before freeing.
        memzero(rsaTmpSpace, 8 * rsaKeyLengthBits);
        free(rsaTmpSpace);
    }
    
    if (NULL != out)
        free(out);
        
    return err;
}

#define INFOMAN_RSA_ENCRYPT

/**
 * This uses lookupManager->fetchUrl()
 */
status_t Preferences::NetflixPreferences::sendLoginAndPasswordToServer()
{
    status_t err = errNone;
    DynStr *str = NULL, *str1 = NULL;
    if (NULL == encryptedCredentials)
    {        
        str = DynStrFromCharP3(login.c_str(), _T(";"), password.c_str());
        if (NULL == str)
        {
            err = memErrNotEnoughSpace;
            goto Exit;
        }   
    
        err = EncryptDynStr(str);
        if (errNone != err)
            goto Exit;
        
        str1 = DynStrNew(2 * DynStrLen(str) + 1);
        if (NULL == str1)
        {
            err = memErrNotEnoughSpace;
            goto Exit;
        }   
    
        long length = bufferToHexCode(DynStrGetData(str), DynStrLen(str), DynStrGetData(str1), 2 * DynStrLen(str) + 1);
        assert(length == DynStrLen(str) * 2);
        
        encryptedCredentials = DynStrReleaseStr(str1);
        
        DynStrDelete(str1);
        str1 = NULL;
        
        DynStrDelete(str);
        str = NULL;
    }
    
    str = DynStrFromCharP2(_T("s+netflixlogin:"), encryptedCredentials);    
    if (NULL == str)
    {
        err = memErrNotEnoughSpace;
        goto Exit;
    }   
        
    LookupManager* lookupManager = MoriartyApplication::instance().lookupManager;
    assert(NULL!=lookupManager);
    lookupManager->fetchUrl(DynStrGetCStr(str));

Exit:
    if (NULL != str)
        DynStrDelete(str);

    if (NULL != str1)
        DynStrDelete(str1);    
    
    return err;
}

void Preferences::GasPricesPreferences::serialize(Serializer& serializer)
{
    serializer
    (version)
    (afterPriceIndex)
    (zipCode);
}

Preferences::GasPricesPreferences::GasPricesPreferences() :
    version(downInfoVersion),
    afterPriceIndex(1)
{
    zipCode.clear();
}

Preferences::ListsOfBestsPreferences::ListsOfBestsPreferences()
{
    lastSearchKeyword_.clear();
}

void Preferences::ListsOfBestsPreferences::serialize(Serializer& serializer)  
{
    serializer
    (lastSearchKeyword_);
}  

void Preferences::swap(Preferences& other)
{
    std::swap(latestClientVersion, other.latestClientVersion);
    std::swap(cookie, other.cookie);
    std::swap(regCode, other.regCode);
    std::swap(epicuriousPreferences, other.epicuriousPreferences);
    std::swap(moviesLocation, other.moviesLocation);
    std::swap(weatherPreferences, other.weatherPreferences);
    std::swap(jokesPreferences, other.jokesPreferences);
    std::swap(stocksPreferences, other.stocksPreferences);
    std::swap(currencyPreferences, other.currencyPreferences);
    std::swap(amazonPreferences, other.amazonPreferences);
    std::swap(gasPricesPreferences, other.gasPricesPreferences);
    std::swap(horoscopesPreferences, other.horoscopesPreferences);
    std::swap(netflixPreferences, other.netflixPreferences);
    std::swap(listsOfBestsPreferences, other.listsOfBestsPreferences);
    std::swap(lyricsPreferences, other.lyricsPreferences);
    std::swap(tvListingsPreferences, other.tvListingsPreferences);
    std::swap(pediaPrefs, other.pediaPrefs);
    std::swap(flightsPreferences, other.flightsPreferences);
    ebookPrefs.swap(other.ebookPrefs);
    std::swap(eBayPreferences, other.eBayPreferences);
    std::swap(mainFormView, other.mainFormView);
    std::swap(dictionaryPreferences, other.dictionaryPreferences);
    
}

Preferences::ModulesState::~ModulesState() {}

void Preferences::ModulesState::serialize(Serializer& serializer)
{
    if (Serializer::directionInput == serializer.direction())
        serializeIn(serializer);
    else
        serializeOut(serializer);
}

uint_t Preferences::ModulesState::schemaVersion() const
{
    return 2;
}

bool Preferences::ModulesState::serializeInFromVersion(Serializer& serializer, uint_t version)
{
    if (1 != version)
        return false;
    String array;
    serializer(array);
    uint_t count = MoriartyApplication::modulesCount();
    for (uint_t i = 0; i < count; ++i) 
        MoriartyApplication::getModule(i).disabledByUser = false;
    for (uint_t i = 0; i < array.length(); ++i) 
    {
        ModuleID id = static_cast<ModuleID>(array[i]);
        MoriartyModule* module = MoriartyApplication::getModuleById(id);
        if (NULL != module)
            module->disabledByUser = true;
    }
    return true;
}

void Preferences::ModulesState::serializeIn(Serializer& serializer)
{
    serializeInFromVersion(serializer, 1);
    uint_t updatedModules;
    serializer(updatedModules);
    for (uint_t i = 0; i < updatedModules; ++i)
    {
        uint_t id;
        UInt32 lastUpdate;
        serializer(id);
        serializer(lastUpdate);
        MoriartyModule* module = MoriartyApplication::getModuleById(static_cast<ModuleID>(id));
        if (NULL != module)
            module->lastUpdateTime = lastUpdate;
    }
}

void Preferences::ModulesState::serializeOut(Serializer& serializer)
{
    String array;
    uint_t count = MoriartyApplication::modulesCount();
    for (uint_t i = 0; i < count; ++i) 
    {
        MoriartyModule& module = MoriartyApplication::getModule(i);
        if (module.disabledByUser)
            array.push_back(module.id);
    }
    serializer(array);
    
    uint_t updatedModules = 0;
    for (uint_t i =0; i < count; ++i)
        if (moduleNeverUpdated != MoriartyApplication::getModule(i).lastUpdateTime)
            ++updatedModules;
    serializer(updatedModules);
    for (uint_t i =0; i < count; ++i) 
    {
        if (0 == updatedModules)
            break;
        MoriartyModule& module = MoriartyApplication::getModule(i);
        if (moduleNeverUpdated == module.lastUpdateTime)
            continue;
        uint_t id = module.id;
        serializer(id);
        serializer(module.lastUpdateTime);
        --updatedModules;
    }
}

Preferences::TvListingsPreferences::TvListingsPreferences():
    providerId(providerIdInvalid)   
{}

Preferences::TvListingsPreferences::~TvListingsPreferences()
{}

void Preferences::TvListingsPreferences::serialize(Serializer& serializer)
{
    serializer
    (zipCode)
    (providerId);
}

DictionaryPreferences::DictionaryPreferences():
    wordsCount(wordsCountNotChecked),
    fUpdated(false),
    randomWordSufix(0)
{
    std::strcpy(dictionaryCode, _T("wn "));
    std::strcpy(dictionaryName, _T("WordNet"));
}

void DictionaryPreferences::serialize(Serializer& serialize)
{
    serialize(dictionaryName, maxDictionaryNameLen + 1);
    serialize(dictionaryCode, maxDictionaryCodeLen + 1);
    serialize(wordsCount);
    serialize(randomWordSufix);
}

PediaPreferences::PediaPreferences():
    articleCount(articleCountNotChecked)
{
    memzero(dbDate, sizeof(dbDate));
    std::strcpy(languageCode, _T("en"));
}

void PediaPreferences::serialize(Serializer& serialize)
{
    serialize(languageCode, maxLanguageCodeLen + 1);
    serialize(articleCount);
    serialize(dbDate, maxDbDateLen + 1);    
}

void Preferences::FlightsPreferences::serialize(Serializer& serializer)
{
    //empty - we don't need/want to store this data...
}

Preferences::FlightsPreferences::FlightsPreferences()
{
    valid = false;
}

static const char* defaultEBookFormats = "Doc eReader iSilo iSiloX zTXT";

EBookPreferences::EBookPreferences():
    targetVfsVolume(vfsVolumeMainMemory),
    managedEBooks(NULL),
    managedEBooksSize(0),
    requestedFormats(const_cast<char*>(defaultEBookFormats)),
    dontConfirmDownloadWithNoReader(false),
    version(versionNotChecked)
{
}

EBookPreferences::~EBookPreferences()
{
    StrArrFree(managedEBooks, managedEBooksSize);
    if (defaultEBookFormats != requestedFormats)
        FreeCharP(&requestedFormats);
}

void EBookPreferences::replaceRequestedFormats(char* newStr)
{
    assert(newStr != NULL);
    if (defaultEBookFormats == requestedFormats)
        requestedFormats = newStr;
    else
        ReplaceCharP(&requestedFormats, newStr);
}


void EBookPreferences::serialize(Serializer& serialize)
{
    serialize(targetVfsVolume);
    serialize(dontConfirmDownloadWithNoReader);
    serialize(version);
    ulong_t size = managedEBooksSize;
    serialize(size);
    ulong_t i;
    if (Serializer::directionOutput == serialize.direction())
    {
        for (i = 0; i < size; ++i)
        {
            char_t* str = managedEBooks[i];
            serialize(str, tstrlen(str));
        }
        
        assert(NULL != requestedFormats);
        serialize(requestedFormats, tstrlen(requestedFormats));
    }
    else
    {
        StrArrFree(managedEBooks, managedEBooksSize);
        managedEBooks = StrArrCreate(size);
        if (NULL == managedEBooks)
            return;
        
        CDynStr str;
        managedEBooksSize = size;
        
        for (i = 0; i < size; ++i)
        {
            serialize(str);
            managedEBooks[i] = str.ReleaseStr();
        }
        
        serialize(str);
        if (defaultEBookFormats == requestedFormats)
            requestedFormats = NULL;
        ReplaceCharP(&requestedFormats, str.ReleaseStr());
        if (NULL == requestedFormats)
            requestedFormats = StringCopy2("");
        if (NULL == requestedFormats)
            requestedFormats = const_cast<char*>(defaultEBookFormats);        
    }
}

void EBookPreferences::swap(EBookPreferences& other)
{
    std::swap(targetVfsVolume, other.targetVfsVolume);
    std::swap(dontConfirmDownloadWithNoReader, other.dontConfirmDownloadWithNoReader);
    std::swap(managedEBooks, other.managedEBooks);
    std::swap(managedEBooksSize, other.managedEBooksSize);    
    std::swap(requestedFormats, other.requestedFormats);
}


void Preferences::EBayPreferences::serialize(Serializer& serializer)
{
    serializer
    (login)
    (password)
    (fCookieIsOnServer)
    (fLogged);
    
    CDynStr str;
    if (NULL != encryptedCredentials)
    {
        str.AttachStr(encryptedCredentials);
        encryptedCredentials = NULL;
    }
    
    serializer(str);
    
    encryptedCredentials = str.ReleaseStr();
}

void Preferences::EBayPreferences::forgetCredentials()
{
    if (NULL != encryptedCredentials)
    {
        free(encryptedCredentials);
        encryptedCredentials = NULL;
    }
}

Preferences::EBayPreferences::EBayPreferences():
    encryptedCredentials(NULL)
{
    fCookieIsOnServer = false;
    fLogged = false;
}

Preferences::EBayPreferences::~EBayPreferences()
{
    if (NULL != encryptedCredentials)
        free(encryptedCredentials);
}

/**
 * This uses lookupManager->fetchUrl()
 */
status_t Preferences::EBayPreferences::sendLoginAndPasswordToServer()
{
    status_t err = errNone;
    DynStr *str = NULL, *str1 = NULL;
    if (NULL == encryptedCredentials)
    {        
        str = DynStrFromCharP3(login.c_str(), _T(";"), password.c_str());
        if (NULL == str)
        {
            err = memErrNotEnoughSpace;
            goto Exit;
        }   
    
        err = EncryptDynStr(str);
        if (errNone != err)
            goto Exit;
        
        str1 = DynStrNew(2 * DynStrLen(str) + 1);
        if (NULL == str1)
        {
            err = memErrNotEnoughSpace;
            goto Exit;
        }   
    
        long length = bufferToHexCode(DynStrGetData(str), DynStrLen(str), DynStrGetData(str1), 2 * DynStrLen(str) + 1);
        assert(length == DynStrLen(str) * 2);
        
        encryptedCredentials = DynStrReleaseStr(str1);
        
        DynStrDelete(str1);
        str1 = NULL;
        
        DynStrDelete(str);
        str = NULL;
    }
    
    str = DynStrFromCharP2(_T("s+ebaylogin:"), encryptedCredentials);    
    if (NULL == str)
    {
        err = memErrNotEnoughSpace;
        goto Exit;
    }   
        
    LookupManager* lookupManager = MoriartyApplication::instance().lookupManager;
    assert(NULL!=lookupManager);
    lookupManager->fetchUrl(DynStrGetCStr(str));

Exit:
    if (NULL != str)
        DynStrDelete(str);

    if (NULL != str1)
        DynStrDelete(str1);    
    
    return err;
}
