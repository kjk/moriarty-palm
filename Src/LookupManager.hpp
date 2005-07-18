#ifndef __MORIARTY_LOOKUP_MANAGER_HPP__
#define __MORIARTY_LOOKUP_MANAGER_HPP__

#include <DynStr.hpp>
#include <Currencies.hpp>
#include <Definition.hpp>
#include <UniversalDataFormat.hpp>
#include <StringListPayloadHandler.hpp>

#include "MoviesData.hpp"
#include "MoriartyPreferences.hpp"
#include "ModulesData.hpp"
#include "MoriartyApplication.hpp"

#include <LookupManagerBase.hpp>

#define protocolVersion _T("1")

#define getDreamsField          _T("Get-Dream-Interpretation")
#define getMoviesField          _T("Get-Movies")
#define verifyRegCodeField      _T("Verify-Registration-Code")
#define getGasPricesField       _T("Get-Gas-Prices")

#define getRegCodeDaysToExpireField _T("Get-Reg-Code-Days-To-Expire")
#define getLatestClientVersionField _T("Get-Latest-Client-Version")

DynStr *DynStrAddField(DynStr *dstr, const char_t *fieldName, const char_t *fieldValue);
DynStr* DynStrAddField(DynStr* dstr, const char_t* fieldName, long numValue);
DynStr *BuildRequestCommonFields(ulong_t transactionId);
char *  BuildRequestOneField(ulong_t transactionId, const char_t *fieldName, const char_t *fieldValue);

class MoriartyConnection;

enum LookupResult {
    lookupResultNone,
    
    lookupResultMoviesData,
    lookupResultLocationUnknown,
    lookupResultLocationAmbiguous,
    
    lookupResultWeatherData,
    lookupResultWeatherMultiselect,
    
    lookupResultRecipe,
    lookupResultRecipesList,

    lookupResult411NoCity, 
    lookupResult411TooManyResults,
    lookupResult411ReverseZip,
    lookupResult411ReverseArea,    
    lookupResult411AreaByCity,
    lookupResult411AreaByCityMultiselect,
    lookupResult411ZipByCity,
    lookupResult411ZipByCityMultiselect,
    lookupResult411PersonSearch,
    lookupResult411PersonSearchCityMultiselect, 
    lookupResult411ReversePhone,
    lookupResult411InternationalCode,
    lookupResult411BusinessSearch,
    lookupResult411BusinessSearchMultiselect,
    
    lookupResultBoxOfficeData,
    
    lookupResultDreamData,

    lookupResultJoke,
    lookupResultJokesList,

    lookupResultStock,
    lookupResultStocksList,
    lookupResultStocksListByName,

    lookupResultAmazon,

    lookupResultNetflix,
    lookupResultNetflixRequestPassword,
    lookupResultNetflixLoginUnknown,
    lookupResultNetflixLoginOk,
    lookupResultNetflixQueue,
    lookupResultNetflixAddOk,
    lookupResultNetflixAddFailed,
    lookupResultNetflixAddAlreadyInQueue,

    lookupResultListsOfBests,

    lookupResultQuotes,

    lookupResultLyrics,

    lookupResultCurrency,

    lookupResultGasPrices,

    lookupResultFlights,

    lookupResultEBay,
    lookupResultEBayNoCache,
    lookupResultEBayRequestPassword,
    lookupResultEBayLoginUnknown,
    lookupResultEBayLoginOk,

    lookupResultHoroscope,
    
    lookupResultConnectionCancelledByUser,

    lookupResultNoResults,  //to handle all no results from many modules

    lookupResultServerError,
    lookupResultError,

    lookupResultRegCodeValid,
    lookupResultRegCodeInvalid,
    
    lookupResultTvProviders,
    lookupResultTvListingsPartial,
    lookupResultTvListingsFull,

    lookupResultDictDef,
    lookupResultDictStats,
    
    lookupResultPediaArticle,
    lookupResultPediaSearch,
    lookupResultPediaLanguages,
    lookupResultPediaStats,
    
    lookupResultEBookSearchResults,
    lookupResultEBookDownload,
    lookupResultEBookBrowse,
    lookupResultEBookHome,
};

#undef DEF_SERVER_ERR
#define DEF_SERVER_ERR(error,code,alert) \
    error = code,

enum ServerError {
#include "ServerErrors.hpp"
};

struct LookupFinishedEventData
{

    LookupResult result;
        
    union
    {
        ServerError serverError;
        ArsLexis::status_t error;
    };        
    
    LookupFinishedEventData(LookupResult res=lookupResultNone, ArsLexis::status_t err=errNone):
        result(res),
        error(err)
    {}
    
};

class LookupManager: public LookupManagerBase<MoriartyApplication::appLookupEventFirst, LookupFinishedEventData> 
{
public:

    LookupManager();

    ~LookupManager();

    ArsLexis::status_t fetchWeather(const ArsLexis::String& location, const ArsLexis::String& locationToServer);

private:

    void handleConnectionError(ArsLexis::status_t error);

    void handleServerError(ServerError serverError);

public:

    enum M411Indexes
    {
        personSearchTitle = 0,
        businessSearchTitle,
        reversePhoneTitle,
        reverseAreaCodeTitle,
        reverseZipCodeTitle,
        zipByCityTitle,
        areaCodeByCityTitle,
        internationalCallingCodeTitle,
        m411ModulesCount    
    };

private:

    ArsLexis::String last411Search_[m411ModulesCount];
    bool    fLast411SearchActual_[m411ModulesCount];

    //411 - person search - when city is ambigous we need repeat search
    ArsLexis::String lastName_;
    ArsLexis::String firstName_;

public:

    void set411IncompleteSearch(const ArsLexis::String& first, const ArsLexis::String& last)
    {lastName_ = last; firstName_ = first;};

    bool isLast411SearchAvailable(M411Indexes index) {return fLast411SearchActual_[index];}

    void setLast411Search(const ArsLexis::String& lastSearch, M411Indexes index);

    const char_t* getLast411Search(M411Indexes index);

    const char_t* getLast411SearchAreaCityZip();

    ArsLexis::status_t fetchWeather();
    
    ArsLexis::status_t fetchMovies(const char_t* location);
        
    bool handleLookupFinishedInForm(const LookupFinishedEventData& data);
    
    friend class MoriartyConnection;

    UniversalDataFormat moviesData;
    
    UniversalDataFormat weatherData;
    
    typedef std::vector<ArsLexis::String> Locations_t;
    Locations_t locations;

    UniversalDataFormat recipe;
    UniversalDataFormat recipeMetrics;
    
    UniversalDataFormat universalDataZipAreaCity;
    UniversalDataFormat personList;
    UniversalDataFormat businessList;
    UniversalDataFormat internationalList;

    UniversalDataFormat tempUDF;
    
    ArsLexis::status_t fetchReverseZip(const ArsLexis::String& zip);

    ArsLexis::status_t fetchReverseArea(const ArsLexis::String& area);

    ArsLexis::status_t fetchAreaByCity(const ArsLexis::String& cityState);
    ArsLexis::status_t fetchAreaByCity(const ArsLexis::String& city, const ArsLexis::String& state);

    ArsLexis::status_t fetchZipByCity(const ArsLexis::String& cityState);
    ArsLexis::status_t fetchZipByCity(const ArsLexis::String& city, const ArsLexis::String& state);

    ArsLexis::status_t fetchPersonData(const ArsLexis::String& firstName, const ArsLexis::String& lastName, const ArsLexis::String& cityOrZip, const ArsLexis::String& state);
    ArsLexis::status_t fetchPersonData(const ArsLexis::String& cityState);

    ArsLexis::status_t fetchReversePhone(const ArsLexis::String& phone);

    ArsLexis::status_t fetchInternationalCode(int countryIndex);

    ArsLexis::status_t fetchBusinessData(const ArsLexis::String& name, const ArsLexis::String& cityOrZip, const ArsLexis::String& state, bool surrounding, bool nameSearch);

    ArsLexis::status_t fetchBusinessDataByUrl(const ArsLexis::String& url);

    UniversalDataFormat boxOfficeData;

    ArsLexis::status_t fetchField(const char_t *fieldName, const char_t *fieldValue);

    UniversalDataFormat dream;

    UniversalDataFormat jokes;
    UniversalDataFormat joke;
    ArsLexis::status_t fetchJoke(const ArsLexis::String& url);
    ArsLexis::status_t fetchJokesList(const ArsLexis::String& jokesListQuery);

    UniversalDataFormat stocks;
    UniversalDataFormat stock;

    ArsLexis::status_t fetchStock(const ArsLexis::String& url);
    ArsLexis::status_t fetchStocksList(const ArsLexis::String& symbols);
    ArsLexis::status_t fetchStocksListValidateLast(const ArsLexis::String& symbols);
    ArsLexis::status_t fetchStocksByName(const ArsLexis::String& url);

    UniversalDataFormat currencyData;
    ArsLexis::status_t fetchCurrencies();
    
    UniversalDataFormat amazonData;

    UniversalDataFormat flightsData;

    UniversalDataFormat eBayData;

    UniversalDataFormat gasPrices;

    UniversalDataFormat netflixData;
    UniversalDataFormat netflixQueue;

    UniversalDataFormat listsOfBestsData;
    
    UniversalDataFormat quotesData;

    UniversalDataFormat dictData;
    
    UniversalDataFormat horoscope;
    ArsLexis::status_t  fetchHoroscope(const ArsLexis::String& str);

    UniversalDataFormat lyricsData;
    
    UniversalDataFormat tvProviders;
    
    ArsLexis::status_t fetchTvProviders(const ArsLexis::String& zipCode);
    
    ArsLexis::status_t fetchUrl(const ArsLexis::char_t* url);
    
private:

    int selectedState_;
    
    MoriartyConnection* createConnection();
    
    ArsLexis::status_t enqueueConnection(MoriartyConnection* conn);
    
public:

    bool flickrPictureCountSent;

    int getSelectedState()
    { return selectedState_;}
    
    void setSelectedState(int state)
    { selectedState_ = state;}

    DefinitionModel* lastPediaArticle;
    DefinitionModel* lastPediaLinkedArticles;
    DefinitionModel* lastPediaLinkingArticles;
    DefinitionModel* lastPediaSearchResults;
    DefinitionModel* lastPediaLanguages;
    
    char_t** lastPediaLangCodes;
    int lastPediaLangCodesCount;
    
    char_t* lastPediaArticleTitle;
    // Passes ownership of title to LookupManager. Deletes previous title.
    void setLastPediaArticleTitle(char_t* title) {ReplaceCharP(&lastPediaArticleTitle, title);}
    
    bool crossModuleLookup;
    const char_t* lastHistoryCacheName;
    const char_t* lastModuleName;
    long ebookVersion;



    char_t* eBookDownloadInfo;
    char_t* eBookFileName;
    UInt16 eBookVfsVolume;
    DefinitionModel* eBookModel;
};

bool HandleCrossModuleLookup(const EventType& event, const char_t* moduleCacheName, const char_t* moduleName);

class HistorySupport;

// This should be called after you call HistorySupport::lookupFinished(true) no matter 
// if this was cross-module lookup or not.
void FinishCrossModuleLookup(HistorySupport& history, const char_t* moduleName);

#endif
