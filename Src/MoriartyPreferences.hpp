#ifndef MORIARTY_PREFERENCES_HPP__
#define MORIARTY_PREFERENCES_HPP__

#include <Debug.hpp>
#include <BaseTypes.hpp>
#include <Serializer.hpp>
#include <vector>
#include <set>
#include <Utility.hpp>
#include <Currencies.hpp>
#include "CurrencyUtils.h"

#ifdef SHIPPING
#define SERVER_ARSLEXIS   "infoman.arslexis.com:4000"
#else
#define SERVER_IM_ANDRZEJ "infoman.arslexis.com:5012"
#define SERVER_IM_SZYMON  "infoman.arslexis.com:5010"
#define SERVER_IM_KJK     "infoman.arslexis.com:5014"
#define SERVER_LOCALHOST  "127.0.0.1:4000"
#define SERVER_LOCAL      "192.168.0.1:4000"
#define SERVER_ARSLEXIS   "infoman.arslexis.com:4000"
#define SERVER_ANDRZEJ_BT   "192.168.2.1:4000"
#define SERVER_ANDRZEJ_INTERNET "rabban.no-ip.org:4000"
#endif

class MoriartyApplication;

struct PediaPreferences: public Serializable
{
    enum {
        maxLanguageCodeLen = 10, 
        maxDbDateLen = 31
    };
    
    char_t languageCode[maxLanguageCodeLen + 1];
    char_t dbDate[maxDbDateLen + 1];
    
    enum {articleCountNotChecked = ulong_t(-1)};
    
    ulong_t articleCount;
    
    PediaPreferences();
    
    void serialize(Serializer& ser);
    
};

struct DictionaryPreferences: public Serializable
{
    enum {
        maxDictionaryCodeLen = 16,
        maxDictionaryNameLen = 32
    };
    
    char_t dictionaryCode[maxDictionaryCodeLen + 1];
    
    char_t dictionaryName[maxDictionaryNameLen + 1];
    
    enum {wordsCountNotChecked = ulong_t(-1)};
    
    ulong_t wordsCount;
    
    int     randomWordSufix;
    
    bool    fUpdated;
    
    DictionaryPreferences();
    
    void serialize(Serializer& ser);
    
};

struct EBookPreferences: public Serializable
{
    UInt16 targetVfsVolume;
    char_t** managedEBooks;
    ulong_t managedEBooksSize;
    char_t* requestedFormats;
    bool dontConfirmDownloadWithNoReader;
    
    enum {versionNotChecked = -1L};
    
    long version;
    
    EBookPreferences();
    
    ~EBookPreferences();
    
    void serialize(Serializer& ser);
    
    void replaceRequestedFormats(char* newStr);
    
    void swap(EBookPreferences& other);
    
};

struct Preferences: private NonCopyable
{
    struct EpicuriousPreferences: public Serializable
    {
        enum RecipePartIndex
        {
            recipeName,
            recipeNote,
            recipeIngredients,
            recipePreperation,
            recipeReviews,
            recipeGlobalNote,
            recipePartsCount
        };
        
        EpicuriousPreferences();
        
        bool fDisplayRecipePart[recipePartsCount];

        void serialize(Serializer& ser);
    };
       
    struct WeatherPreferences: public Serializable
    {
        ArsLexis::String weatherLocation;

        ArsLexis::String weatherLocationToServer;
    
        bool fDegreesModeCelsius;
        
        WeatherPreferences();
        
        void serialize(Serializer& ser);
    };
       
    struct JokesPreferences: public Serializable
    {
        enum TableSize
        {
            categoryTableSize = 23,
            typeTableSize = 6,
            explicitnessTableSize = 3
        };
        
        bool fCategory[categoryTableSize];

        bool fType[typeTableSize];

        bool fExplicitness[explicitnessTableSize];

        int  minimumRating;
        
        int  sortOrder;
        
        JokesPreferences();
        
        void serialize(Serializer& ser);
    };
    
    struct StocksPreferences: public Serializable, private NonCopyable
    {
        struct Portfolios: public Serializable
        {
            ArsLexis::String name;
            
            std::vector<ArsLexis::String> symbols;
            std::vector<unsigned long> quantities;
            
            ArsLexis::String totalValue;
            
            Portfolios();
            
            ~Portfolios();
            
            void serialize(Serializer& ser);
        };
           
        enum
        {
            totalNumberOfPortfolios = 10,
            defaultPortfolio = 0,
            noPortfolio = uint_t(-1)
        };

        int currentPortfolio;
        
        int lastDownloadedPortfolio;
        
        int lastDownloadedStock; // to get it form stockDetailedDoneUpdateForm
        
        unsigned long newQuantity;
        
        std::vector<Portfolios*> portfolios;
        
        int portfoliosCount() { return portfolios.size();};
        
        //return index or noPortfolio if failed
        int addPortfolio(const ArsLexis::String name);
        
        void deletePortfolio(int index);
        
        uint_t portfoliosCountLimit() { return totalNumberOfPortfolios; };

        StocksPreferences();

        ~StocksPreferences();
        
        void serialize(Serializer& ser);
        
        void swap(StocksPreferences& other);
        
    };

    struct CurrencyPreferences: public Serializable
    {
    
        SelectedCurrencies_t selectedCurrencies;
        
        CurrencyPreferences();
        
        ~CurrencyPreferences();
        
        void selectCurrency(uint_t index);
        
        void deselectCurrency(uint_t index);
        
        bool isCurrencySelected(uint_t index) const;

        void serialize(Serializer& ser);
    private:
    
        uint_t commonCurrenciesCount_;
    };

    struct AmazonPreferences: public Serializable
    {
        bool smallMain;
        
        int currentLevel;
        
        AmazonPreferences();
        
        ~AmazonPreferences() {};

        uint_t schemaVersion() const;

        bool serializeInFromVersion(Serializer& ser, uint_t version);

        void serialize(Serializer& ser);
        
    };

    struct GasPricesPreferences: public Serializable
    {
        enum Version
        {
            popupVersion,
            downInfoVersion
        };
        
        int version;

        ArsLexis::String zipCode;

        int afterPriceIndex;
        
        GasPricesPreferences();
        
        void serialize(Serializer& ser);
    };

    struct NetflixPreferences: public Serializable
    {
        ArsLexis::String login;
        
        ArsLexis::String password;

        bool    fCookieIsOnServer;
        
        bool    fLogged;
                        
        bool    fNeedToUpdateQueue;
        
        char_t* encryptedCredentials;
                        
        NetflixPreferences();
        
        ~NetflixPreferences();

        void serialize(Serializer& ser);
        
        ArsLexis::status_t sendLoginAndPasswordToServer();
        
        void forgetCredentials();
    };

    struct ListsOfBestsPreferences: public Serializable
    {
        ArsLexis::String lastSearchKeyword_;

        ListsOfBestsPreferences();

        ~ListsOfBestsPreferences() {};

        void serialize(Serializer& ser);
    };

    struct HoroscopesPreferences: public Serializable
    {
        int downloadedSign;
        
        ArsLexis::String downloadedQuery;
        
        HoroscopesPreferences();
        
        ~HoroscopesPreferences() {};

        void serialize(Serializer& ser);
    };

    struct LyricsPreferences: public Serializable
    {
        LyricsPreferences();
        
        ~LyricsPreferences() {};

        void serialize(Serializer& ser);
    };
    
    struct TvListingsPreferences: public Serializable
    {
        ArsLexis::String zipCode;
        ulong_t providerId;
        
        enum {providerIdInvalid = ulong_t(-1)};
        
        TvListingsPreferences();
        
        ~TvListingsPreferences();

        void serialize(Serializer& ser);
    };

    // this preferences are not stored - just used to fill search form
    struct FlightsPreferences: public Serializable
    {
        ArsLexis::String    flightNo;
        ArsLexis::String    airlines;
        ArsLexis::String    from;
        ArsLexis::String    to;
        Int16               year;
        Int16               month;
        Int16               day;
        Int16               hour;
        Int16               minutes;
        bool                valid;
        
        FlightsPreferences();
        
        ~FlightsPreferences() {};

        void serialize(Serializer& ser);
    };

    struct EBayPreferences: public Serializable
    {
        ArsLexis::String login;
        
        ArsLexis::String password;

        bool    fCookieIsOnServer;
        
        bool    fLogged;
                        
        char_t* encryptedCredentials;
                        
        EBayPreferences();
        
        ~EBayPreferences();

        void serialize(Serializer& ser);
        
        ArsLexis::status_t sendLoginAndPasswordToServer();
        
        void forgetCredentials();
    };

    void swap(Preferences& other);

    HoroscopesPreferences   horoscopesPreferences; 
    GasPricesPreferences    gasPricesPreferences;
    CurrencyPreferences     currencyPreferences;
    StocksPreferences       stocksPreferences;
    JokesPreferences        jokesPreferences;
    WeatherPreferences      weatherPreferences;

    TvListingsPreferences   tvListingsPreferences;
    NetflixPreferences      netflixPreferences;
    AmazonPreferences       amazonPreferences;
    PediaPreferences        pediaPrefs;
    DictionaryPreferences   dictionaryPreferences;
    LyricsPreferences       lyricsPreferences; 
    EpicuriousPreferences   epicuriousPreferences;
    ListsOfBestsPreferences listsOfBestsPreferences; 
    FlightsPreferences      flightsPreferences;
    EBookPreferences        ebookPrefs;
    EBayPreferences         eBayPreferences;
    
       
    ArsLexis::String moviesLocation;

    bool fBoxOfficeCompactView;

    ArsLexis::char_t *serverAddress;

    enum {cookieLength=32};
    ArsLexis::String cookie;
    
    enum {regCodeLength=32};
    ArsLexis::String regCode;

    bool fKeyboardLaunchEnabled;

    // we persist the last thing we got for latest client version
    ArsLexis::String latestClientVersion;

    int  mainFormView;

#ifndef SHIPPING
    bool fServerSelected;
#endif

    Preferences();
    
    ArsLexis::status_t serialize(Serializer& serializer);
    
    struct ModulesState: public Serializable 
    {
        MoriartyApplication& application;
        
        ModulesState(MoriartyApplication& app): application(app) {}
        
        ~ModulesState();
        
        void serialize(Serializer& ser);
        
        uint_t schemaVersion() const;
    
        bool serializeInFromVersion(Serializer& ser, uint_t version);
    
    private:
    
        void serializeIn(Serializer& ser);
        
        void serializeOut(Serializer& ser);
        
    };
    
    
};

template<> inline 
void std::swap<Preferences>(Preferences& p1, Preferences& p2) 
{p1.swap(p2);}

template<> inline
void std::swap<Preferences::StocksPreferences>(Preferences::StocksPreferences& sp1, Preferences::StocksPreferences& sp2) 
{sp1.swap(sp2);}

#endif
