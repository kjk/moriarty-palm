#include <SysUtils.hpp>
#include <Text.hpp>
#include <DynStr.hpp>
#include <InternationalCountryCodes.hpp>
#include <StringListPayloadHandler.hpp>
#include <DeviceInfo.hpp>
#include <UniversalDataHandler.hpp>
#include <ByteFormatParser.hpp>

#include "LookupManager.hpp"
#include "ModulesData.hpp"
#include "MoriartyPreferences.hpp"
#include "HyperlinkHandler.hpp"
#include "MoriartyConnection.hpp"
#include "PediaArticleHandler.hpp"
#include "PediaMainForm.hpp"
#include "eBookFormats.hpp"

#include "flickr.hpp"

#if defined(__MWERKS__)
# pragma far_code
#endif

static void resetDisabledRemotelyForAll(uint_t modulesCount, MoriartyModule* modules)
{
    for (uint_t i = 0; i<modulesCount; ++i)
        modules[i].disabledRemotely = false;
}

class DisabledModulesHandler: public StringListPayloadHandler 
{
protected:
    status_t notifyFinished()
    {
        resetDisabledRemotelyForAll(MORIARTY_MODULES_COUNT, MoriartyApplication::modules());
        Strings_t::const_iterator end = strings.end();
        for (Strings_t::const_iterator it = strings.begin(); it != end; ++it)
        {
            const String& moduleName = *it;
            MoriartyModule* module = MoriartyApplication::getModuleByName(moduleName.c_str());
            if (NULL != module)
                module->disabledRemotely = true;
        }
        strings.clear();
        return errNone;
    }
};
    
static void replaceCommas(String& str) 
{
    std::replace(str.begin(), str.end(), _T(','), _T(' '));
}


#define FIELD_VALUE(name, handler) \
    {(name), FieldDescriptor::fieldValue, (handler), NULL, NULL, NULL, lookupResultNone, false}
#define FIELD_VALUE_RESULT(name, lookupResult) \
    {(name), FieldDescriptor::fieldValue, NULL, NULL, NULL, NULL, lookupResult, false}
#define FIELD_UDF(name, completionHandler, destinationContainer, streamName, writeToHistoryCache) \
    {(name), FieldDescriptor::fieldPayloadUDF, NULL, (completionHandler), (destinationContainer), (streamName), lookupResultNone, (writeToHistoryCache)}
 #define FIELD_UDF_RESULT(name, destinationContainer, streamName, lookupResult, writeToHistoryCache) \
    {(name), FieldDescriptor::fieldPayloadUDF, NULL, NULL, (destinationContainer), (streamName), (lookupResult), (writeToHistoryCache)}
#define FIELD_PAYLOAD(name, handler, completionHandler, streamName, writeToHistoryCache) \
    {(name), FieldDescriptor::fieldPayloadCustom, (handler), (completionHandler), NULL, (streamName), lookupResultNone, (writeToHistoryCache)}
    

#define disabledModulesField _T("Disabled-Modules")

#define noResultsField _T("No-Results")

#define moviesDataField     _T("Movies-Data")
#define locationUnknownField _T("Location-Unknown")
#define locationAmbiguousField _T("Location-Ambiguous")

#define getCurrencyConversionField _T("Get-Currency-Conversion")
#define currencyConversionField _T("Currency-Conversion")

#define currentBoxOfficeField _T("Current-Box-Office")

#define weatherDataField        _T("Weather")
#define weatherMultiselectField _T("Weather-Multiselect")
#define getWeatherField         _T("Get-Weather")

#define recipesListField    _T("Recipes-List")
#define recipeField         _T("Recipe")

#define dreamField          _T("Dream-Interpretation")

#define getHoroscopeField   _T("Get-Horoscope")
#define horoscopeField      _T("Horoscope")

#define gasPricesField          _T("Gas-Prices")

#define getJokesListField   _T("Get-Jokes-List")
#define getJokeField        _T("Get-Joke")
#define jokesListField      _T("Jokes-List")
#define jokeField           _T("Joke")

#define amazonField         _T("Amazon")

#define netflixField                _T("Netflix")
#define netflixQueueField           _T("Netflix-Queue")
#define netflixRequestPasswordField _T("Netflix-Password-Request")
#define netflixUnknownLoginField    _T("Netflix-Unknown-Login")
#define netflixLoginOkField         _T("Netflix-Login-Ok")
#define netflixAddOkField           _T("Netflix-Add-Ok")
#define netflixAddFailedField         _T("Netflix-Add-Failed")
#define netflixAddAlreadyInQueueField _T("Netflix-Add-Already-In-Queue")

#define listsOfBestsField    _T("Lists-Of-Bests")

#define lyricsField    _T("Lyrics")

#define quotesField    _T("Quotes")

#define flightsField    _T("Flights")

#define eBayField                _T("EBay")
#define eBayFieldNoCache         _T("EBay-No-Cache")
#define eBayRequestPasswordField _T("EBay-Password-Request")
#define eBayUnknownLoginField    _T("EBay-Unknown-Login")
#define eBayLoginOkField         _T("EBay-Login-Ok")

#define getStocksListField    _T("Get-Stocks-List")
#define getStockField         _T("Get-Stock")
#define getStockByNameField   _T("Get-Stock-By-Name")
#define stocksListField       _T("Stocks-List")
#define stockField            _T("Stock")
#define stocksListByNameField _T("Stocks-List-By-Name")
#define getStocksListValidateLastField  _T("Get-Stocks-List-Validate-Last")

#define noCity411Field _T("411-No-City")
#define tooManyResultsField _T("411-Too-Many-Results")
#define getReverseAreaField _T("411-Reverse-Area-Code")
#define reverseAreaField _T("411-Reverse-Area-Code-Result")
#define getReverseZipField _T("411-Reverse-Zip")
#define reverseZipField _T("411-Reverse-Zip-Result")
#define getAreaByCityField _T("411-Area-Code-By-City")
#define areaByCityField _T("411-Area-Code-By-City-Result")
#define areaByCityMultiselectField _T("411-Area-Code-By-City-Multiselect")
#define getZipByCityField _T("411-Zip-By-City")
#define zipByCityField _T("411-Zip-By-City-Result")
#define zipByCityMultiselectField _T("411-Zip-By-City-Multiselect")
#define getPersonSearchField _T("411-Person-Search")
#define personSearchField _T("411-Person-Search-Result")
#define personSearchCityMultiselectField _T("411-Person-Search-City-Multiselect")
#define getReversePhoneField _T("411-Reverse-Phone")
#define reversePhoneField _T("411-Reverse-Phone-Result")
#define getInternationalCodeField _T("411-International-Code")
#define internationalCodeField _T("411-International-Code-Result")
#define getBusinessSearchField _T("411-Business-Search")
#define businessSearchField _T("411-Business-Search-Result")
#define getBusinessSearchByUrlField _T("411-Business-Search-By-Url")
#define businessSearchMultiselectField _T("411-Business-Search-Multiselect")
#define regCodeDaysToExpireField _T("Reg-Code-Days-To-Expire")
#define regCodeValidField       _T("Registration-Code-Valid")

#define latestClientVersionField    _T("Latest-Client-Version")

#define getTvListingsProviders _T("Get-TvListings-Providers")
#define getTvListings _T("Get-TvListings")
#define tvListingsProviders _T("TvListings-Providers")
#define tvListingsPartial _T("TvListings-Partial")
#define tvListingsFull _T("TvListings")

#define getUrl _T("Get-Url")

#define dictionaryDefField    _T("Dict-Def")
#define dictionaryStatsField  _T("Dict-Stats")

#define pediaArticle _T("Pedia-Article")
#define pediaArticleCount _T("Pedia-Article-Count")
#define pediaArticleTitle _T("Pedia-Article-Title")
#define pediaDbDate _T("Pedia-Db-Date")
#define pediaLangs _T("Pedia-Langs")
#define pediaSearchResults _T("Pedia-Search-Results")


#define ebookSearchResults _T("eBook-Search-Results")
#define ebookDownload _T("eBook-Download")
#define ebookName _T("eBook-Name")
#define ebookVersionField _T("eBook-Version")
#define getUrlEBookBrowseField getUrl _T("-eBook-browse")
#define getUrlEBookHomeField getUrl _T("-eBook-home")


#define flickrPicturesUploadedField _T("Flickr-Pictures-Uploaded")

//! @note When adding fields ensure that their names are alphabetically ordered - we use binary search to lookup fields! 
const MoriartyConnection::FieldDescriptor MoriartyConnection::fields_[] = {
    
    FIELD_PAYLOAD(areaByCityMultiselectField, &MoriartyConnection::handleLocationAmbiguousField, &MoriartyConnection::completeLocationAmbiguousField<lookupResult411AreaByCityMultiselect>, NULL, false),
    FIELD_UDF(areaByCityField, &MoriartyConnection::complete411AreaByCityField, &LookupManager::universalDataZipAreaCity, NULL, false),
    FIELD_UDF_RESULT(businessSearchMultiselectField, &LookupManager::tempUDF, NULL, lookupResult411BusinessSearchMultiselect, false),
    FIELD_UDF(businessSearchField, &MoriartyConnection::complete411BusinessSearchField, &LookupManager::businessList, m411BusinessDataStream, false),
    FIELD_UDF(internationalCodeField, &MoriartyConnection::complete411InternationalCodeField, &LookupManager::internationalList, NULL, false),
    FIELD_VALUE_RESULT(noCity411Field, lookupResult411NoCity),
    FIELD_PAYLOAD(personSearchCityMultiselectField, &MoriartyConnection::handleLocationAmbiguousField, &MoriartyConnection::completeLocationAmbiguousField<lookupResult411PersonSearchCityMultiselect>, NULL, false),
    FIELD_UDF(personSearchField, &MoriartyConnection::complete411PersonSearchField, &LookupManager::personList, m411PersonDataStream, false),
    FIELD_UDF(reverseAreaField, &MoriartyConnection::complete411ReverseAreaField, &LookupManager::universalDataZipAreaCity, NULL, false),
    FIELD_UDF(reversePhoneField, &MoriartyConnection::complete411ReversePhoneField, &LookupManager::personList, NULL, false),
    FIELD_UDF(reverseZipField, &MoriartyConnection::complete411ReverseZipField, &LookupManager::universalDataZipAreaCity, NULL, false),
    FIELD_VALUE_RESULT(tooManyResultsField, lookupResult411TooManyResults),
    FIELD_PAYLOAD(zipByCityMultiselectField, &MoriartyConnection::handleLocationAmbiguousField, &MoriartyConnection::completeLocationAmbiguousField<lookupResult411ZipByCityMultiselect>, NULL, false),
    FIELD_UDF(zipByCityField, &MoriartyConnection::complete411ZipByCityField, &LookupManager::universalDataZipAreaCity, NULL, false),

    FIELD_UDF_RESULT(amazonField, &LookupManager::amazonData, amazonHistoryCacheName, lookupResultAmazon, true),
    FIELD_VALUE(cookieField, &MoriartyConnection::handleCookieField),
    FIELD_UDF_RESULT(currencyConversionField, &LookupManager::currencyData, currencyDataStream, lookupResultCurrency, false),
    FIELD_UDF_RESULT(currentBoxOfficeField, &LookupManager::boxOfficeData, boxOfficeDataStream, lookupResultBoxOfficeData, false),
    FIELD_UDF_RESULT(dictionaryDefField, &LookupManager::dictData, dictHistoryCacheName, lookupResultDictDef,true),
    FIELD_UDF(dictionaryStatsField, &MoriartyConnection::completeDictStatsField, &LookupManager::tempUDF, NULL, false),
    FIELD_PAYLOAD(disabledModulesField, &MoriartyConnection::handleDisabledModulesField, NULL, NULL, false),
    FIELD_UDF_RESULT(dreamField, &LookupManager::dream, dreamsDataStream, lookupResultDreamData, false),
    FIELD_UDF_RESULT(eBayField, &LookupManager::eBayData, eBayHistoryCacheName, lookupResultEBay, true),
    FIELD_VALUE_RESULT(eBayLoginOkField, lookupResultEBayLoginOk),
    FIELD_UDF_RESULT(eBayFieldNoCache, &LookupManager::tempUDF, NULL, lookupResultEBayNoCache, false),
    FIELD_VALUE_RESULT(eBayRequestPasswordField, lookupResultEBayRequestPassword),
    FIELD_VALUE_RESULT(eBayUnknownLoginField, lookupResultEBayLoginUnknown),
    
    FIELD_PAYLOAD(ebookDownload, &MoriartyConnection::handleEBookDownloadField, &MoriartyConnection::completeEBookDownloadField, NULL, false),
    FIELD_VALUE(ebookName, &MoriartyConnection::handleEBookNameField),
    FIELD_PAYLOAD(ebookSearchResults, &MoriartyConnection::handleByteFormatPayloadField, &MoriartyConnection::completeEBookSearchResultsField, ebookHistoryCacheName, true),    
    FIELD_VALUE(ebookVersionField, &MoriartyConnection::handleEBookVersionField),
    
    FIELD_VALUE(errorField, &MoriartyConnection::handleErrorField),
    FIELD_UDF_RESULT(flightsField, &LookupManager::flightsData, flightsDataStream, lookupResultFlights, false),
    FIELD_VALUE(formatVersionField, &MoriartyConnection::handleFormatVersionField),
    FIELD_UDF(gasPricesField, &MoriartyConnection::completeGasPricesDataField, &LookupManager::gasPrices, gasPricesStream, false),
    
    FIELD_PAYLOAD(getUrlEBookBrowseField, &MoriartyConnection::handleByteFormatPayloadField, &MoriartyConnection::completeEBookBrowseField, ebookHistoryCacheName, true),
    FIELD_PAYLOAD(getUrlEBookHomeField, &MoriartyConnection::handleByteFormatPayloadField, &MoriartyConnection::completeEBookBrowseField, ebookWelcomeCacheName, true),
    
    FIELD_UDF(horoscopeField, &MoriartyConnection::completeHoroscopesDataField, &LookupManager::horoscope, horoscopeDataStream, false),
    FIELD_UDF_RESULT(jokeField, &LookupManager::joke, jokesJokeStream, lookupResultJoke, false),
    FIELD_UDF_RESULT(jokesListField, &LookupManager::jokes, jokesJokesListStream, lookupResultJokesList, false),
    FIELD_VALUE(latestClientVersionField, &MoriartyConnection::handleLatestClientVersionField),
    FIELD_UDF_RESULT(listsOfBestsField, &LookupManager::listsOfBestsData, listsOfBestsHistoryCacheName, lookupResultListsOfBests, true),
    FIELD_PAYLOAD(locationAmbiguousField, &MoriartyConnection::handleLocationAmbiguousField, &MoriartyConnection::completeLocationAmbiguousField<lookupResultLocationAmbiguous>, NULL, false),
    FIELD_VALUE_RESULT(locationUnknownField, lookupResultLocationUnknown),
    FIELD_UDF_RESULT(lyricsField, &LookupManager::lyricsData, lyricsHistoryCacheName, lookupResultLyrics, true),
    FIELD_UDF(moviesDataField, &MoriartyConnection::completeMoviesDataField, &LookupManager::moviesData, moviesDataStream, false),
    FIELD_UDF_RESULT(netflixField, &LookupManager::netflixData, netflixHistoryCacheName, lookupResultNetflix, true),
    FIELD_VALUE_RESULT(netflixAddAlreadyInQueueField, lookupResultNetflixAddAlreadyInQueue),
    FIELD_VALUE_RESULT(netflixAddFailedField, lookupResultNetflixAddFailed),
    FIELD_VALUE_RESULT(netflixAddOkField, lookupResultNetflixAddOk),
    FIELD_VALUE_RESULT(netflixLoginOkField, lookupResultNetflixLoginOk),
    FIELD_VALUE_RESULT(netflixRequestPasswordField, lookupResultNetflixRequestPassword),
    FIELD_UDF_RESULT(netflixQueueField, &LookupManager::netflixQueue, netflixDataStream, lookupResultNetflixQueue, false),
    FIELD_VALUE_RESULT(netflixUnknownLoginField, lookupResultNetflixLoginUnknown),
    FIELD_VALUE_RESULT(noResultsField, lookupResultNoResults),
    
    FIELD_PAYLOAD(pediaArticle, &MoriartyConnection::handlePediaArticleField, &MoriartyConnection::completePediaArticleField, pediaHistoryCacheName, true),
    FIELD_VALUE(pediaArticleCount, &MoriartyConnection::handlePediaArticleCountField),
    FIELD_VALUE(pediaArticleTitle, &MoriartyConnection::handlePediaArticleTitleField),
    FIELD_VALUE(pediaDbDate, &MoriartyConnection::handlePediaDbDateField),
    FIELD_PAYLOAD(pediaLangs, &MoriartyConnection::handleByteFormatPayloadField, &MoriartyConnection::completePediaLanguagesField, NULL, false),
    FIELD_PAYLOAD(pediaSearchResults, &MoriartyConnection::handlePediaSearchField, &MoriartyConnection::completePediaSearchResultsField, pediaHistoryCacheName, true),
    
    FIELD_UDF_RESULT(quotesField, &LookupManager::quotesData, quotesDataStream, lookupResultQuotes, false),
    FIELD_UDF_RESULT(recipeField, &LookupManager::recipe, epicuriousRecipeStream, lookupResultRecipe, false),
    FIELD_UDF_RESULT(recipesListField, &LookupManager::recipeMetrics, epicuriousRecipesListStream, lookupResultRecipesList, false),
    FIELD_VALUE(regCodeDaysToExpireField, &MoriartyConnection::handleRegCodeDaysToExpire),
    FIELD_VALUE(regCodeValidField, &MoriartyConnection::handleRegCodeValidField),
    FIELD_UDF_RESULT(stockField, &LookupManager::stock, NULL, lookupResultStock, false),
    FIELD_UDF_RESULT(stocksListField, &LookupManager::stocks, stocksStocksListStream, lookupResultStocksList, false),
    FIELD_UDF_RESULT(stocksListByNameField, &LookupManager::tempUDF, NULL, lookupResultStocksListByName, false),
    FIELD_VALUE(transactionIdField, &MoriartyConnection::handleTransactionIdField),
    FIELD_UDF_RESULT(tvListingsProviders, &LookupManager::tvProviders, NULL, lookupResultTvProviders, false),
    FIELD_UDF(weatherDataField, &MoriartyConnection::completeWeatherDataField, &LookupManager::weatherData, weatherDataStream, false),
    FIELD_UDF_RESULT(weatherMultiselectField, &LookupManager::tempUDF, NULL, lookupResultWeatherMultiselect, false)
};

MoriartyConnection::MoriartyConnection(LookupManager& manager):
    FieldPayloadProtocolConnection(manager.connectionManager()),
    lookupManager_(manager),
    result_(lookupResultNone),
    serverError_(serverErrorNone),
    hasDisabledModules_(false),
    initialActiveModulesCount_(activeModulesCount(MORIARTY_MODULES_COUNT, MoriartyApplication::modules())),
    currentField_(NULL),
    url_(NULL),
    m411SurroundingAreas_(false),
    m411NameSearch_(false),
    m411InternationalCode_(-1),
    m411RequestType_(requestNot411),
    getCurrenciesRequest_(false),
    writer_(NULL),
    flickrPictureCount(0)
{    
    transactionId = random((ulong_t)-1);

#ifndef NDEBUG
    // Validate that fields_ are sorted.
    for (uint_t i = 0; i < ARRAY_SIZE(fields_); ++i)
    {
        if (i > 0 && fields_[i] < fields_[i-1])
        {
            const char_t* prevName = fields_[i-1].name;
            const char_t* nextName = fields_[i].name;
            assert(false);
        }
    }
#endif
    
#ifdef _PALM_OS
    setTransferTimeout(SysTicksPerSecond() * 15);
#elif defined(_WIN32)
    setTransferTimeout(15000); // Timeout after 15 seconds of inactivity
#endif

    if (!manager.flickrPictureCountSent)
    {
        flickrPictureCount = FlickrGetResetPictureCount();
        manager.flickrPictureCountSent;
    }
}

MoriartyConnection::~MoriartyConnection()
{
    if (NULL != url_)
        free(url_);
    
    delete writer_;
}

status_t MoriartyConnection::enqueue()
{
    status_t error=FieldPayloadProtocolConnection::enqueue();
    if (errNone==error)
    {
        lookupManager_.setStatusText("Resolving host...");
        sendEvent(lookupManager_.lookupStartedEvent);
    }        
    return error;
}

status_t MoriartyConnection::open()
{
    status_t error = prepareRequest();
    if (errNone!=error)
        return error;
    error=FieldPayloadProtocolConnection::open();
    if (errNone==error)
    {
        lookupManager_.setStatusText("Opening connection...");
        sendEvent(lookupManager_.lookupProgressEvent, 0, 0, true);
    }        
    return error;        
}

status_t MoriartyConnection::notifyProgress()
{
    status_t error=FieldPayloadProtocolConnection::notifyProgress();
    if (error)
        return error;
    lookupManager_.setStatusText("Retrieving data...");
    uint_t progress = LookupManager::percentProgressDisabled;
    if (inPayload_)
        progress=((payloadLength()-payloadLengthLeft()) * 100L)/payloadLength();
    lookupManager_.setPercentProgress(progress);
    sendEvent(LookupManager::lookupProgressEvent);
    return error;
}

status_t MoriartyConnection::notifyFinished()
{
    status_t error=FieldPayloadProtocolConnection::notifyFinished();
    if (errNone!=error)
        return error;
    lookupManager_.setStatusText("Finished");
    assert(lookupResultError!=result_);

    // if we didn't get any specific result frot the server
    // then change it into server failure error (shouldn't happen)
    if (lookupResultNone==result_)
    {
        result_ = lookupResultServerError;
        serverError_ = serverErrorFailure;
    }

    LookupFinishedEventData data(result_);
    if (lookupResultServerError==result_)
    {
        assert(serverErrorNone!=serverError_);
        data.serverError = serverError_;
    }
    if (!hasDisabledModules_)
        resetDisabledRemotelyForAll(MORIARTY_MODULES_COUNT, MoriartyApplication::modules());
    const uint_t activeMods = activeModulesCount(MORIARTY_MODULES_COUNT, MoriartyApplication::modules());
    if (activeMods != initialActiveModulesCount_)
        sendEvent(MoriartyApplication::appActiveModulesCountChangedEvent); 
    sendEvent(lookupManager_.lookupFinishedEvent, data);
    return error;        
}

void MoriartyConnection::handleError(status_t error)
{
    Log(eLogError, _T(" MoriartyConnection::handleError(): error code: "), false);
    LogUlong(eLogError, error, true);
    //log().error()<<"handleError(): error code: "<<error;
    sendEvent(lookupManager_.lookupFinishedEvent, LookupFinishedEventData(lookupResultError, error));
    FieldPayloadProtocolConnection::handleError(error);
}

status_t MoriartyConnection::handleField(const char_t* name, const char_t* value)
{
    currentField_ = NULL;
    FieldDescriptor toFind = {name};
    const FieldDescriptor* end = fields_+ARRAY_SIZE(fields_);
    const FieldDescriptor* field = std::lower_bound(fields_, end, toFind);
    if ((end == field) || (toFind != *field))
        return FieldPayloadProtocolConnection::handleField(name, value);
        
    currentField_ = field;
    if (FieldDescriptor::fieldPayloadUDF == currentField_->type)
    {
        assert(NULL == currentField_->fieldHandler);
        long length;
        status_t error = numericValue(value, length);
        if (errNone != error)
            return errResponseMalformed;
        
        prepareWriter();
        UniversalDataHandler* dataHandler = new_nt UniversalDataHandler();
        if (NULL != dataHandler)
            startPayload(dataHandler, length);
            
        return errNone;
    }
    if (NULL == currentField_->fieldHandler)
    {
        if (lookupResultNone != currentField_->lookupResult)
            setLookupResult(currentField_->lookupResult);
        return errNone;
    }
    FieldHandler handler = field->fieldHandler;
    String nameStr(name);
    String valueStr;
    if (NULL != value)
        valueStr.assign(value);
    status_t err = (this->*handler)(name, value);
    if (errNone != err)
        return err;
    if (lookupResultNone != currentField_->lookupResult)
        setLookupResult(currentField_->lookupResult);
    return errNone;
}

void MoriartyConnection::set411ReverseZip(const ArsLexis::String& zip)
{
    m411RequestType_ = requestGetReverseZip;
    m411Zip_ = zip;
}

void MoriartyConnection::set411ReverseArea(const ArsLexis::String& area)
{
    m411RequestType_ = requestGetReverseArea;
    m411Area_ = area;
}

void MoriartyConnection::set411ZipByCity(const ArsLexis::String& city, const ArsLexis::String& state)
{
    m411RequestType_ = requestGetZipByCity;
    m411City_ = city;
    replaceCommas(m411City_);
    m411State_ = state;
}

void MoriartyConnection::set411AreaByCity(const ArsLexis::String& city, const ArsLexis::String& state)
{
    m411RequestType_ = requestGetAreaByCity;
    m411City_ = city;
    replaceCommas(m411City_);
    m411State_ = state;
}

void MoriartyConnection::set411PersonSearch(const ArsLexis::String& firstName, const ArsLexis::String& lastName, const ArsLexis::String& cityOrZip, const ArsLexis::String& state)
{
    m411RequestType_ = requestGetPersonSearch;
    m411FirstName_ = firstName;
    replaceCommas(m411FirstName_);
    m411LastName_ = lastName;
    replaceCommas(m411LastName_);
    m411City_ = cityOrZip;
    replaceCommas(m411City_);
    m411State_ = state;
}

void MoriartyConnection::set411BusinessSearch(const ArsLexis::String& name, const ArsLexis::String& cityOrZip, const ArsLexis::String& state, bool surrounding, bool nameSearch)
{
    m411RequestType_ = requestGetBusinessSearch;
    m411Name_ = name;
    replaceCommas(m411Name_);
    m411City_ = cityOrZip;
    replaceCommas(m411City_);
    m411State_ = state;
    m411SurroundingAreas_ = surrounding;
    m411NameSearch_ = nameSearch;
}

void MoriartyConnection::set411BusinessSearchByUrl(const ArsLexis::String& url)
{
    m411RequestType_ = requestGetBusinessSearchByUrl;
    m411Url_ = url;    
}

void MoriartyConnection::set411ReversePhone(const ArsLexis::String& phone)
{
    m411RequestType_ = requestGetReversePhone;
    m411Phone_ = phone;
}

void MoriartyConnection::set411InternationalCodeSearch(int code)
{
    m411RequestType_ = requestGetInternational;
    m411InternationalCode_ = code;
}

status_t MoriartyConnection::prepareRequest()
{
    if (fRequestExists())
    {
        // if request has been set explicitly by the caller before we got here,
        // send that request, don't build another one
        return errNone;
    }

    DynStr *request = BuildRequestCommonFields(transactionId);
    if (NULL == request)
        goto Error;

    if (0 != flickrPictureCount)
    {
        if (NULL == DynStrAddField(request, flickrPicturesUploadedField, flickrPictureCount))
            goto Error;
    }        
    
    if (EBookPreferences::versionNotChecked == lookupManager_.ebookVersion)
    {
        if (NULL == DynStrAddField(request, ebookVersionField, (const char_t*)NULL))
            goto Error;
    }

    if (!moviesLocation_.empty())
    {
        if (NULL == DynStrAddField(request, getMoviesField, moviesLocation_.c_str()))
            goto Error;
    }

    if (getCurrenciesRequest_)
    {
        if (NULL == DynStrAddField(request, getCurrencyConversionField, (const char_t*)NULL))
            goto Error;
    }

    if (!stocksSymbols_.empty())
    {
        if (NULL == DynStrAddField(request, getStocksListField, stocksSymbols_.c_str()))
            goto Error;
    }

    if (!stocksSymbolsValidateLast_.empty())
    {
        if (NULL == DynStrAddField(request, getStocksListValidateLastField, stocksSymbolsValidateLast_.c_str()))
            goto Error;
    }

    if (!stockUrl_.empty())
    {
        if (NULL == DynStrAddField(request, getStockField, stockUrl_.c_str()))
            goto Error;
    }

    if (!stockName_.empty())
    {
        if (NULL == DynStrAddField(request, getStockByNameField, stockName_.c_str()))
            goto Error;
    }

    if (!horoscopeSearchQuery_.empty())
    {
        if (NULL == DynStrAddField(request, getHoroscopeField, horoscopeSearchQuery_.c_str()))
            goto Error;
    }

    if (!weatherInternalLocation_.empty())        
    {
        if (NULL == DynStrAddField(request, getWeatherField, weatherInternalLocation_.c_str()))
            goto Error;
    }

    if (!jokesSearchQuery_.empty())
    {
        if (NULL == DynStrAddField(request, getJokesListField, jokesSearchQuery_.c_str()))
            goto Error;
    }

    if (!jokeUrl_.empty())
    {
        if (NULL == DynStrAddField(request, getJokeField, jokeUrl_.c_str()))
            goto Error;
    }

    if (!tvProvidersZipCode_.empty())
    {
        if (NULL == DynStrAddField(request, getTvListingsProviders, tvProvidersZipCode_.c_str()))
            goto Error;
    }

    if (NULL != url_)
    {
        if (NULL == DynStrAddField(request, getUrl, url_))
            goto Error;
            
        // pedia - first request will download stats
        if (StrStartsWith(url_, urlSchemaEncyclopediaTerm) ||
            StrStartsWith(url_, urlSchemaEncyclopediaRandom) ||
            StrStartsWith(url_, urlSchemaEncyclopediaSearch))
        {
            PediaPreferences& prefs = MoriartyApplication::instance().preferences().pediaPrefs;
            if (8 != tstrlen(prefs.dbDate) || prefs.articleCountNotChecked == prefs.articleCount)
            {
                CDynStr str;
                if (NULL == str.AppendCharP3(urlSchemaEncyclopediaStats, urlSeparatorSchemaStr, prefs.languageCode))
                    goto Error;
                if (NULL == DynStrAddField(request, getUrl, str.GetCStr()))
                    goto Error;
            }
        }
        // EOP(edia)
        // dict - first request will download stats
        if (StrStartsWith(url_, urlSchemaDictTerm) ||
            StrStartsWith(url_, urlSchemaDictRandom))
        {
            DictionaryPreferences& prefs = MoriartyApplication::instance().preferences().dictionaryPreferences;
            if (prefs.wordsCountNotChecked == prefs.wordsCount || !prefs.fUpdated)
            {
                CDynStr str;
                if (NULL == str.AppendCharP3(urlSchemaDictStats, urlSeparatorSchemaStr, prefs.dictionaryCode))
                    goto Error;
                if (NULL == DynStrAddField(request, getUrl, str.GetCStr()))
                    goto Error;
            }
        }
        // EOD(ict)
    }

    if (requestNot411 != m411RequestType_)
    {        
        String cityState;
        String person;
        String newPhone;
        switch (m411RequestType_)
        {
            case requestGetReverseZip:
                if (NULL == DynStrAddField(request, getReverseZipField, m411Zip_.c_str()))
                    goto Error;
                break;
                
            case requestGetReverseArea:
                if (NULL == DynStrAddField(request, getReverseAreaField, m411Area_.c_str()))
                    goto Error;
                break;

            case requestGetInternational:
                {
                    const char_t *countryCode = getCountryCode(m411InternationalCode_);
                    if (NULL == DynStrAddField(request, getInternationalCodeField, countryCode))
                        goto Error;
                }
                break;

            case requestGetAreaByCity:
                cityState.assign(m411City_).append(1, _T(',')).append(m411State_);
                if (NULL == DynStrAddField(request, getAreaByCityField, cityState.c_str()))
                    goto Error;
                break;

            case requestGetZipByCity:
                cityState.assign(m411City_).append(1, _T(',')).append(m411State_);
                if (NULL == DynStrAddField(request, getZipByCityField, cityState.c_str()))
                    goto Error;
                break;

            case requestGetReversePhone:
                assert(m411Phone_.length() == 10);
                newPhone.assign(m411Phone_, 0, 3).append(1, _T('-'));
                newPhone.append(m411Phone_, 3, 3).append(1, _T('-'));
                newPhone.append(m411Phone_, 6, 4);
                if (NULL == DynStrAddField(request, getReversePhoneField, newPhone.c_str()))
                    goto Error;
                break;            

            case requestGetPersonSearch:
                assert(!m411LastName_.empty());
                person.assign(m411FirstName_).append(1, _T(','));
                person.append(m411LastName_).append(1, _T(','));
                person.append(m411City_).append(1, _T(','));
                person.append(m411State_);
                if (NULL == DynStrAddField(request, getPersonSearchField, person.c_str()))
                    goto Error;
                break;

            case requestGetBusinessSearch:
                assert(!m411Name_.empty());
                assert(!m411State_.empty());
                person.assign(m411Name_).append(1, _T(','));
                person.append(m411City_).append(1, _T(','));
                person.append(m411State_).append(1, _T(','));
                if (m411SurroundingAreas_)
                    person.append(_T("Yes"));
                else
                    person.append(_T("No"));
                person.append(1, _T(','));
                if (m411NameSearch_)
                    person.append(_T("Name"));
                else
                    person.append(_T("Category"));
                if (NULL == DynStrAddField(request, getBusinessSearchField, person.c_str()))
                    goto Error;
                break;

            case requestGetBusinessSearchByUrl:
                assert(!m411Url_.empty());
                if (NULL == DynStrAddField(request, getBusinessSearchByUrlField, m411Url_.c_str()))
                    goto Error;
                break;
        }
    }
    
    if (NULL == DynStrAppendChar(request, _T('\n')))
        goto Error;

// On WinCE char_t is utf16 unicode so we have to convert the string we've built
// to 8-bit ascii. On Palm it's already 8-bit ascii so we can just set the string
// as the request
#ifdef _PALM_OS
    ulong_t len = DynStrLen(request);
    setRequestOwn(DynStrReleaseStr(request), len); 
#else
    char *newReq = Utf16ToStr(DynStrGetCStr(request), DynStrLen(request));
    if (NULL == newReq)
        goto Error;
    setRequestOwn(newReq, strlen(newReq)); 
#endif
    DynStrDelete(request);
    return errNone;
Error:
    if (NULL != request)
        DynStrDelete(request);
    return memErrNotEnoughSpace;
}

status_t MoriartyConnection::notifyPayloadFinished()
{
    assert(NULL != currentField_);
    assert(FieldDescriptor::fieldPayloadUDF == currentField_->type || FieldDescriptor::fieldPayloadCustom == currentField_->type);
    if (FieldDescriptor::fieldPayloadUDF == currentField_->type && NULL != currentField_->destinationContainer)
    {
        UniversalDataHandler* handler = static_cast<UniversalDataHandler*>(payloadHandler());
        assert(NULL != handler);
        LookupManager& lm = lookupManager();
        UniversalDataFormat LookupManager::* dataMember = currentField_->destinationContainer;
        std::swap(lm.*dataMember, handler->universalData);
    }
    if (NULL != writer_)
    {
        delete writer_;
        writer_ = NULL;
        if (currentField_->sinkIsHistoryCache)
            cache_.close();
    }
    if (NULL != currentField_->payloadCompletionHandler)
    {
        PayloadCompletionHandler completionHandler = currentField_->payloadCompletionHandler;
        PayloadHandler* handler = payloadHandler();
        assert(NULL != handler);
        status_t error = (this->*completionHandler)(*handler);
        if (errNone != error)
            return error;
    }
    if (lookupResultNone != currentField_->lookupResult)
        setLookupResult(currentField_->lookupResult);
    return FieldPayloadProtocolConnection::notifyPayloadFinished();
}

status_t MoriartyConnection::handleCookieField(const String& name, const String& value)
{
    assert(value.length() == Preferences::cookieLength);
    if (value.length() != Preferences::cookieLength)
        return errResponseMalformed;
    MoriartyApplication::instance().preferences().cookie = value;
    return errNone;    
}

status_t MoriartyConnection::handleDisabledModulesField(const String& name, const String& value)
{
    long length;
    status_t error=numericValue(value, length);
    if (errNone != error)
        return errResponseMalformed;
    hasDisabledModules_ = true;
    startPayload(new DisabledModulesHandler(), length);
    return errNone;
}

status_t MoriartyConnection::handleFormatVersionField(const String& name, const String& value)
{
    long numValue;
    status_t error=numericValue(value, numValue);
    if (errNone != error)
        return errResponseMalformed;
    formatVersion_=numValue;
    return errNone;
}

status_t MoriartyConnection::handleRegCodeDaysToExpire(const ArsLexis::String& name, const String& value)
{
    long numValue;
    status_t error = numericValue(value, numValue, 10);
    assert(errNone == error);
    if (errNone != error)
        return errResponseMalformed;
    MoriartyApplication& app = MoriartyApplication::instance();
    // setting regCodeDaysToExpire to a value != REG_CODE_DAYS_NOT_SET
    // prevents getting it again
    app.regCodeDaysToExpire = numValue;    
    sendEvent(MoriartyApplication::appCheckRegCodeDaysToExpire); 
    return errNone;
}

status_t MoriartyConnection::handleLatestClientVersionField(const ArsLexis::String& name, const String& value)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    app.preferences().latestClientVersion = value;
    app.fLatestClientVersionRetrieved = true;
    return errNone;
}

status_t MoriartyConnection::handleTransactionIdField(const ArsLexis::String& name, const String& value)
{
    long numValue;
    status_t error = numericValue(value, numValue, 16);
    if (errNone != error || numValue != transactionId)
        return errResponseMalformed;
    return errNone;    
}

status_t MoriartyConnection::handleRegCodeValidField(const String& name, const String& value)
{
    long numValue;
    status_t error = numericValue(value, numValue);
    assert(errNone==error);
    if (error)
        return errResponseMalformed;
    assert((0==numValue) || (1==numValue));
    if (1==numValue)
    {
       setLookupResult(lookupResultRegCodeValid);
    }
    else if (0==numValue)
    {
       setLookupResult(lookupResultRegCodeInvalid);
    }
    else
        error = errResponseMalformed;
    return error;
}

status_t MoriartyConnection::handleErrorField(const String& name, const String& value)
{
    long numValue;
    status_t error=numericValue(value, numValue);
    if (errNone != error || serverErrorNone == numValue)
        return errResponseMalformed;
        
    serverError_ = static_cast<ServerError>(numValue);
    setLookupResult(lookupResultServerError);
    return errNone;
}

//! @todo Validate Movies-Data UDF
status_t MoriartyConnection::completeMoviesDataField(FieldPayloadProtocolConnection::PayloadHandler& handler)
{
    setLookupResult(lookupResultMoviesData);
    Preferences& prefs=MoriartyApplication::instance().preferences();
    prefs.moviesLocation = moviesLocation_;
    return errNone;
}

status_t MoriartyConnection::completeHoroscopesDataField(FieldPayloadProtocolConnection::PayloadHandler& handler)
{
    setLookupResult(lookupResultHoroscope);
    Preferences::HoroscopesPreferences* prefs = &MoriartyApplication::instance().preferences().horoscopesPreferences;
    prefs->downloadedQuery.assign(horoscopeSearchQuery_);    
    return errNone;
}

status_t MoriartyConnection::handleLocationAmbiguousField(const String& name, const String& value)
{
    long length;
    status_t error=numericValue(value, length);
    if (errNone != error)
        return errResponseMalformed;
    startPayload(new StringListPayloadHandler(), length);
    return errNone;
}

status_t MoriartyConnection::completeWeatherDataField(FieldPayloadProtocolConnection::PayloadHandler&)
{
    setLookupResult(lookupResultWeatherData);
    Preferences& prefs=MoriartyApplication::instance().preferences();
    prefs.weatherPreferences.weatherLocationToServer = weatherInternalLocation_;
    prefs.weatherPreferences.weatherLocation = weatherDisplayLocation_;
    return errNone;
}

status_t MoriartyConnection::completeGasPricesDataField(FieldPayloadProtocolConnection::PayloadHandler&)
{
    setLookupResult(lookupResultGasPrices);
    Preferences& prefs = MoriartyApplication::instance().preferences();
    prefs.gasPricesPreferences.zipCode = gasPricesZip;
    return errNone;
}

status_t MoriartyConnection::complete411ReverseZipField(FieldPayloadProtocolConnection::PayloadHandler&)
{
    setLookupResult(lookupResult411ReverseZip);
    String title;
    if (lookupManager().universalDataZipAreaCity.getItemsCount() > 1)
        title.append("Results for zip code ");
    else
        title.append("Result for zip code ");
    title.append(m411Zip_);
    lookupManager().setLast411Search(title, LookupManager::reverseZipCodeTitle);
    return errNone;
}

status_t MoriartyConnection::complete411ReverseAreaField(FieldPayloadProtocolConnection::PayloadHandler&)
{
    setLookupResult(lookupResult411ReverseArea);
    String title;
    if (lookupManager().universalDataZipAreaCity.getItemsCount() > 1)
        title.append("Results for area code ");
    else
        title.append("Result for area code ");
    title.append(m411Area_);
    lookupManager().setLast411Search(title, LookupManager::reverseAreaCodeTitle);
    return errNone;
}

status_t MoriartyConnection::complete411PersonSearchField(FieldPayloadProtocolConnection::PayloadHandler&)
{
    setLookupResult(lookupResult411PersonSearch);
    String personFound;
    personFound.assign(m411FirstName_).append(1, _T(' '));
    personFound.append(m411LastName_);
    if (!m411City_.empty() || !m411State_.empty())
    {
        personFound.append(_T(" in "));
        if (m411City_.empty() || m411State_.empty())
            personFound.append(m411City_).append(m411State_);        
        else
            personFound.append(m411City_).append(_T(", ")).append(m411State_);
    }
    lookupManager().setLast411Search(personFound, LookupManager::personSearchTitle);
    return errNone;
}

status_t MoriartyConnection::complete411BusinessSearchField(FieldPayloadProtocolConnection::PayloadHandler& )
{
    setLookupResult(lookupResult411BusinessSearch);
    String businessFound;
    if (!m411Name_.empty())
    {
        businessFound.assign(m411Name_);
        if (!m411City_.empty() || !m411State_.empty())
        {
            businessFound.append(_T(" in "));
            if (m411City_.empty() || m411State_.empty())
                businessFound.append(m411City_).append(m411State_);        
            else
                businessFound.append(m411City_).append(_T(", ")).append(m411State_);
        }
    }
    else
    {
        businessFound.assign(_T("Business category search"));
    }
    lookupManager().setLast411Search(businessFound, LookupManager::businessSearchTitle);
    return errNone;
}

status_t MoriartyConnection::complete411ReversePhoneField(FieldPayloadProtocolConnection::PayloadHandler& )
{
    setLookupResult(lookupResult411ReversePhone);
    String phoneFound;
    phoneFound.assign(_T("Phone: "));
    phoneFound.append(m411Phone_, 0, 3).append(1, _T('-'));
    phoneFound.append(m411Phone_, 3, 3).append(1, _T('-'));
    phoneFound.append(m411Phone_, 6, 4);
    lookupManager().setLast411Search(phoneFound, LookupManager::reversePhoneTitle);
    return errNone;
}

status_t MoriartyConnection::complete411InternationalCodeField(FieldPayloadProtocolConnection::PayloadHandler&)
{
    setLookupResult(lookupResult411InternationalCode);
    String countryCode = getCountryName(m411InternationalCode_);
    lookupManager().setLast411Search(countryCode, LookupManager::internationalCallingCodeTitle);
    return errNone;
}

status_t MoriartyConnection::complete411AreaByCityField(FieldPayloadProtocolConnection::PayloadHandler&)
{
    setLookupResult(lookupResult411AreaByCity);
    String title;
    if (lookupManager().universalDataZipAreaCity.getItemsCount() > 1)
        title += "Area codes for: ";
    else
        title += "Area code for: ";
    title.append(m411City_).append(_T(", ")).append(m411State_);
    lookupManager().setLast411Search(title, LookupManager::areaCodeByCityTitle);
    return errNone;
}

status_t MoriartyConnection::complete411ZipByCityField(FieldPayloadProtocolConnection::PayloadHandler&)
{
    setLookupResult(lookupResult411ZipByCity);
    String title;
    if (lookupManager().universalDataZipAreaCity.getItemsCount() > 1)
        title.append("Zip codes for: ");
    else
        title.append("Zip code for: ");
    title.append(m411City_).append(_T(", ")).append(m411State_);
    lookupManager().setLast411Search(title, LookupManager::zipByCityTitle);
    return errNone;
}

char_t* MoriartyConnection::setUrl(const ArsLexis::char_t *url) 
{
    ReplaceCharP(&url_, StringCopy2(url));
    return url_;
}

void MoriartyConnection::prepareWriter()
{
    status_t err;
    assert(NULL == writer_);
    if (NULL == currentField_->sinkName)
        return;
    if (currentField_->sinkIsHistoryCache)
    {
        if (errNone != (err = cache_.open(currentField_->sinkName)))
            return;
            
        ulong_t index;
        if (errNone != (err = cache_.appendEntry(url_, index)))
            return;
            
        writer_ = cache_.writerForEntry(index);
    }
    else
    {
        DataStore* ds = DataStore::instance();
        if (NULL == ds)
            return;
        
        DataStoreWriter* w = new_nt DataStoreWriter(*ds);
        if (NULL == w)
            return;
            
        if (errNone != (err = w->open(currentField_->sinkName)))
        {
            delete w;
            return;
        }
        
        writer_ = w;
    }
}

status_t MoriartyConnection::handlePayloadIncrement(const char_t* payload, ulong_t& length, bool finish)
{
    status_t err = FieldPayloadProtocolConnection::handlePayloadIncrement(payload, length, finish);
    if (errNone != err)
        return err;
    
    if (NULL == writer_)
        return errNone;
        
    if (errNone != (err = writer_->write(payload, length)))
    {
        delete writer_;
        writer_ = NULL;
    }
    return errNone;
}

status_t MoriartyConnection::handlePediaArticleTitleField(const String&, const String& value)
{
    char_t* str = StringCopy2N(value.data(), value.length());    
    if (NULL == str)
        return memErrNotEnoughSpace;
        
    lookupManager_.setLastPediaArticleTitle(str);

    ulong_t schLen = tstrlen(urlSchemaEncyclopediaRandom);
    ulong_t len = tstrlen(url_);
    if (schLen < len)
        len = schLen;
    
    if (0 != std::memcmp(url_, urlSchemaEncyclopediaRandom, len * sizeof(char_t)))
        return errNone;
        
    // If this was random term request, we have to replace url with valid one, otherwise
    // pressing link in history will give another random term, not the one from history.
    PediaPreferences& prefs = MoriartyApplication::instance().preferences().pediaPrefs;
    CDynStr url;
    if (NULL == url.AppendCharP3(urlSchemaEncyclopediaTerm urlSeparatorSchemaStr, prefs.languageCode, _T(":")))
        return memErrNotEnoughSpace;
            
    if (NULL == url.AppendCharP(str))
        return memErrNotEnoughSpace;
    
    ReplaceCharP(&url_, url.ReleaseStr());
    return errNone;
}

status_t MoriartyConnection::handlePediaArticleField(const String&, const String& value)
{
    long length;
    status_t error=numericValue(value, length);
    if (errNone != error)
        return errResponseMalformed;
    
    PediaArticleHandler* handler = new_nt PediaArticleHandler();
    if (NULL == handler)
        return memErrNotEnoughSpace;

    PediaPreferences& prefs = MoriartyApplication::instance().preferences().pediaPrefs;
    handler->defaultLanguage = prefs.languageCode;

    prepareWriter();
    startPayload(handler, length);
    return errNone;       
}


static void PediaInvalidateRenderers()
{
    MoriartyApplication& app = MoriartyApplication::instance();
    PediaMainForm* form = static_cast<PediaMainForm*>(app.getOpenForm(pediaMainForm));
    if (NULL != form)
        form->invalidateRenderers();
}

status_t MoriartyConnection::completePediaArticleField(FieldPayloadProtocolConnection::PayloadHandler& h)
{
    PediaArticleHandler& handler = static_cast<PediaArticleHandler&>(h);
    
    PediaInvalidateRenderers();

    delete lookupManager_.lastPediaArticle;
    lookupManager_.lastPediaArticle = handler.article;
    handler.article = NULL;
    
    delete lookupManager_.lastPediaLinkedArticles;
    lookupManager_.lastPediaLinkedArticles = handler.linkedArticles;
    handler.linkedArticles = NULL;
    
    delete lookupManager_.lastPediaLinkingArticles;
    lookupManager_.lastPediaLinkingArticles = handler.linkingArticles;
    handler.linkingArticles = NULL;
    
    setLookupResult(lookupResultPediaArticle);
    return errNone;
}

status_t MoriartyConnection::handleStringListPayloadField(const String&, const String& value)
{
    long length;
    status_t error=numericValue(value, length);
    if (errNone != error)
        return errResponseMalformed;
        
    StringListPayloadHandler* handler = new_nt StringListPayloadHandler();
    if (NULL == handler)
        return memErrNotEnoughSpace;
        
    startPayload(handler, length);
    return errNone;        
}

status_t MoriartyConnection::handleByteFormatPayloadField(const String& name, const String& value)
{
    long length;
    status_t error=numericValue(value, length);
    if (errNone != error)
        return errResponseMalformed;
        
        
    ByteFormatParser* handler = new_nt ByteFormatParser();
    if (NULL == handler)
        return memErrNotEnoughSpace;

    prepareWriter();
    startPayload(handler, length);
    return errNone;        
}


status_t MoriartyConnection::completePediaSearchResultsField(FieldPayloadProtocolConnection::PayloadHandler& handler)
{
    ByteFormatParser& h = static_cast<ByteFormatParser&>(handler);
    PediaInvalidateRenderers();
    delete lookupManager_.lastPediaSearchResults;
    lookupManager_.lastPediaSearchResults = h.releaseModel();
    if (NULL == lookupManager_.lastPediaSearchResults)
        return memErrNotEnoughSpace;

    setLookupResult(lookupResultPediaSearch);
    return errNone;
}

status_t MoriartyConnection::completePediaLanguagesField(FieldPayloadProtocolConnection::PayloadHandler& handler)
{
    ByteFormatParser& h = static_cast<ByteFormatParser&>(handler);
    PediaInvalidateRenderers();
    delete lookupManager_.lastPediaLanguages;
    lookupManager_.lastPediaLanguages = h.releaseModel();
    if (NULL == lookupManager_.lastPediaLanguages)
        return memErrNotEnoughSpace;

    setLookupResult(lookupResultPediaLanguages);
    return errNone;
}

static bool PediaUrlCurrentDatabase(const char_t* url_, const PediaPreferences& prefs)
{
    long pos = StrFind(url_, -1, urlSeparatorSchema);
    const char_t* code = url_ + pos + 1;
    pos = StrFind(code, -1, _T(':'));
    if (-1 == pos)
        pos = tstrlen(code);

    if (0 != tstrncmp(code, prefs.languageCode, pos))
        return false;
    return true;
}

status_t MoriartyConnection::handlePediaArticleCountField(const String& name, const String& value)
{
    long val;
    status_t error=numericValue(value, val);
    if (errNone != error)
        return errResponseMalformed;
        

    PediaPreferences& prefs = MoriartyApplication::instance().preferences().pediaPrefs;
    if (!PediaUrlCurrentDatabase(url_, prefs))
        return errNone;
        
    prefs.articleCount = val;
    
    if (lookupResultNone == result_)
        setLookupResult(lookupResultPediaStats);
    return errNone;
}

status_t MoriartyConnection::handlePediaDbDateField(const String& name, const String& value)
{
    PediaPreferences& prefs = MoriartyApplication::instance().preferences().pediaPrefs;
    if (!PediaUrlCurrentDatabase(url_, prefs))
        return errNone;

    if (value.length() > prefs.maxDbDateLen)
        return errResponseMalformed;
        
    memmove(prefs.dbDate, value.data(), value.length() * sizeof(char_t));
    prefs.dbDate[value.length()] = _T('\0');
    return errNone;    
}

status_t MoriartyConnection::handlePediaSearchField(const String& name, const String& value)
{
    ulong_t len = tstrlen(urlSchemaEncyclopediaTerm urlSeparatorSchemaStr);
    if (StrStartsWith(url_, -1, urlSchemaEncyclopediaTerm urlSeparatorSchemaStr, len))
    {
        CDynStr str;
        const char_t* rest = url_ + len;
        if (NULL == str.AppendCharP2(urlSchemaEncyclopediaSearch urlSeparatorSchemaStr, rest))
            return memErrNotEnoughSpace;
        ReplaceCharP(&url_, str.ReleaseStr());       
    }
    
    return handleByteFormatPayloadField(name, value);
}

status_t MoriartyConnection::handleEBookNameField(const String& name, const String& value)
{
    char_t* val = StringCopy2N(value.data(), value.length());
    if (NULL == val)
        return memErrNotEnoughSpace;
    
    ReplaceCharP(&lookupManager_.eBookDownloadInfo, val);
    return errNone;
}

status_t MoriartyConnection::handleEBookVersionField(const String& name, const String& value)
{
    long val;
    status_t err = numericValue(value, val);
    if (errNone != err || val < 0)
        return errResponseMalformed;
        
    lookupManager_.ebookVersion = val;
    eBook_ExpireCache(lookupManager_);
    return errNone;   
}

status_t MoriartyConnection::completeEBookSearchResultsField(FieldPayloadProtocolConnection::PayloadHandler& handler)
{
    ByteFormatParser& h = static_cast<ByteFormatParser&>(handler);
    DefinitionModel* model = h.releaseModel();
    PassOwnership(model, lookupManager_.eBookModel);
    if (NULL == lookupManager_.eBookModel)
        return memErrNotEnoughSpace;

    setLookupResult(lookupResultEBookSearchResults);
    return errNone;
}

status_t MoriartyConnection::completeEBookBrowseField(FieldPayloadProtocolConnection::PayloadHandler& handler)
{
    ByteFormatParser& h = static_cast<ByteFormatParser&>(handler);
    DefinitionModel* model = h.releaseModel();
    PassOwnership(model, lookupManager_.eBookModel);
    if (NULL == lookupManager_.eBookModel)
        return memErrNotEnoughSpace;

    if (NULL != url_ && StrStartsWith(url_, urlSchemaEBookHome))
        setLookupResult(lookupResultEBookHome);
    else
        setLookupResult(lookupResultEBookBrowse);
    return errNone;
}

status_t MoriartyConnection::handleEBookDownloadField(const String&, const String& value)
{
    long length;
    status_t error=numericValue(value, length);
    if (errNone != error)
        return errResponseMalformed;
        
        
    assert(NULL != lookupManager_.eBookDownloadInfo);
    
    eBookDownloadHandler* handler = new_nt eBookDownloadHandler();
    if (NULL == handler)
        return memErrNotEnoughSpace;

    const EBookPreferences& prefs = MoriartyApplication::instance().preferences().ebookPrefs;
    lookupManager_.eBookVfsVolume = vfsVolumeMainMemory;
    if (VFS_FeaturesPresent() && vfsVolumeMainMemory != prefs.targetVfsVolume)
    {
        UInt32 iterator = vfsIteratorStart;
        while (vfsIteratorStop != iterator)
        {
            UInt16 ref;
            Err err = VFSVolumeEnumerate(&ref, &iterator);
            if (errNone != err)
                break;
                
            if (prefs.targetVfsVolume == ref)
            {
                // targetVfsVolume is present - use it instead of main memory
                lookupManager_.eBookVfsVolume = ref;
                break;
            }
        }
    }
        
    error = handler->initialize(lookupManager_.eBookVfsVolume, lookupManager_.eBookDownloadInfo, length);
    if (errNone != error)
    {
        delete handler;
        return error;
    }

    ReplaceCharP(&lookupManager_.eBookFileName, StringCopy2(handler->fileName()));
    if (NULL == lookupManager_.eBookFileName)
        return memErrNotEnoughSpace;
    
    prepareWriter();
    startPayload(handler, length);
    return errNone;       
}

status_t MoriartyConnection::completeEBookDownloadField(FieldPayloadProtocolConnection::PayloadHandler& handler)
{
    setLookupResult(lookupResultEBookDownload);
    return errNone;
}

status_t MoriartyConnection::completeDictStatsField(FieldPayloadProtocolConnection::PayloadHandler& handler)
{
    assert(!lookupManager_.tempUDF.empty());
    DictionaryPreferences* prefs = &MoriartyApplication::instance().preferences().dictionaryPreferences;
    UniversalDataFormat* udf = &lookupManager_.tempUDF;
    prefs->fUpdated = true;
    for (int i = 0; i < udf->getItemsCount(); i++)
    {
        switch(udf->getItemText(i,0)[0])        {
            case 'N':
                std::strcpy(prefs->dictionaryName, udf->getItemText(i,1));
                break;
            case 'S':
                std::strcpy(prefs->dictionaryCode, udf->getItemText(i,1));
                break;
            case 'C':
                prefs->wordsCount = udf->getItemTextAsLong(i,1);                 break;
        }
    }
    return errNone;
}


