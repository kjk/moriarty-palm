#ifndef __MORIARTY_APPLICATION_HPP__
#define __MORIARTY_APPLICATION_HPP__

#include "Moriarty.h"
#include <RichApplication.hpp>

#define REG_CODE_DAYS_NOT_SET -1

class LookupManager;

using ArsLexis::char_t;

class MoriartyApplication;
class HyperlinkHandler;

typedef void (*ModuleDataReadFunction_t)(MoriartyApplication&);

// NOTE: only add new ids at the end so that we preserve module ids across
// different versions of InfoMan so that preferences aren't screwed
enum ModuleID {
    moduleIdAbout,
    moduleId411,
    moduleIdAmazon,
    moduleIdBoxOffice,
    moduleIdCurrency,
    moduleIdDreams,
    moduleIdGasPrices,
    moduleIdJokes,
    moduleIdListsOfBests,
    moduleIdMovies,
    moduleIdNetflix,
    moduleIdRecipes,
    moduleIdStocks,
    moduleIdWeather,
    moduleIdHoroscopes,
    moduleIdLyrics,
    moduleIdTestWiki,
    moduleIdTvListings,
    moduleIdPedia,
    moduleIdDict,
    moduleIdQuotes,
    moduleIdEBooks,
    moduleIdFlights,
    moduleIdEBay,
    moduleIdFlickr
};

struct MoriartyModule {
    ModuleID id;
    const ArsLexis::char_t *    name;
    const ArsLexis::char_t *    displayName;
    uint_t      smallIconId;
    uint_t      largeIconId;
    uint_t      mainFormId;
    bool        free;
    bool        dataRead;
    bool        disabledRemotely;
    bool        disabledByUser;
    
    ModuleDataReadFunction_t moduleDataReadFunction;    

    bool active() const {return !(disabledByUser || disabledRemotely);}
    
    bool        tracksUpdateTime;
    UInt32    lastUpdateTime;
};

static const UInt32 moduleNeverUpdated = UInt32(-1);

#ifdef SHIPPING
#define MORIARTY_MODULES_COUNT 12
#else
#define MORIARTY_MODULES_COUNT 25
#endif

uint_t activeModulesCount(uint_t modulesCount, const MoriartyModule* modules);
MoriartyModule* getActiveModule(uint_t modulesCount, MoriartyModule* modules, uint_t moduleNo);
MoriartyModule* getModuleByName(uint_t modulesCount, MoriartyModule* modules, const ArsLexis::char_t * name);

struct Preferences;

class MoriartyApplication: public RichApplication 
{

    void detectViewer();
    
    void loadPreferences();

    
    void handleFetchMoviesEvent();
    
    void handleFetchWeatherEvent();

protected:

    Err normalLaunch();

    void waitForEvent(EventType& event);
    
    Form* createForm(UInt16 formId);

    bool handleApplicationEvent(EventType& event);

    //void prepareModules();

public:

    static const UInt32 requiredRomVersion=sysMakeROMVersion(3,5,0,sysROMStageDevelopment,0);
    static const UInt32 creatorId=appFileCreator;
    static const UInt16 notEnoughMemoryAlertId=notEnoughMemoryAlert;
    static const UInt16 romIncompatibleAlertId=romIncompatibleAlert;
    
    MoriartyApplication();
    
    ~MoriartyApplication();
    
    Err initialize();

    static const uint_t lookupEventsCount=3;
    
    enum Event
    {
        appLookupEventFirst=appFirstAvailableEvent,
        appLookupEventLast=appLookupEventFirst+lookupEventsCount,
        appFetchMoviesEvent,
        appSelectMovieEvent,
        appSelectTheatreEvent,
        appFetchWeatherEvent,
        appSelectWeatherEvent,
        appSelect411SearchEvent,
        app411SetAreaByCityEvent, //switch form function
        app411SetZipByCityEvent, //switch form function
        app411SetPersonSearchEvent, //switch form function
        app411SetInternationalCodeEvent, //switch form function
        appSetWeatherEvent, //switch form function
        appStateWasSelectedEvent, //returned by selectStateForm
        app411SetBusinessMultiselectEvent, //switch select state form to use tempUDF (0 - name, 1 - url)
        appActiveModulesCountChangedEvent,
        appRecipePartsChangedEvent,
//        appCurrencySetMultiselectModeEvent,
//        appCurrencyWasSelectedEvent,
//        appMultiCurrencyWasSelectedEvent,
        appSetStocksPortfolioEvent, //swich form function
        appSetStocksEnterStockFormOkButtonEvent, //when form closed by ok button
        appFieldChangedEvent,
        appSetStocksStockDetailedEvent, //swich form function
        appSetGasPriceEvent, //swich form function
        appSetStocksNameMatchingEvent, //swich form function
        appSetWishlistSelectEvent, //switch form function
        appCheckRegCodeDaysToExpire, // we got regCodeDaysToExpire and we need to check it
        appRegistrationFinished,
        appChangeServer,
        appSelectText,
        appSelectTvProviderEvent,
        appFirstAvailableEvent
    };
    
    enum ExtendedEvent
    {
        extEventShowMenu
    };
    
    struct SelectItemEventData
    {
        uint_t item;
        explicit SelectItemEventData(uint_t i): item(i) {}
    };
    
    static MoriartyApplication& instance()
    {return static_cast<MoriartyApplication&>(RichApplication::instance());}
    
    LookupManager* lookupManager;

    long regCodeDaysToExpire;

    bool fLatestClientVersionRetrieved;
    
    bool hasPreferences() const {return NULL != preferences_;}

    Preferences& preferences() 
    {
        assert(NULL != preferences_);
        return *preferences_;
    }

    const Preferences& preferences() const
    {
        assert(NULL != preferences_);
        return *preferences_;
    }

    enum {moduleNone=uint_t(-1)};
    void runModule(uint_t index);

    void runModuleById(ModuleID id);
    
    void runMainForm();

    static MoriartyModule* modules() { return modules_; }

    // TODO: used by MainForm. should we pass it explicitly?
    uint_t selectedActiveModuleIndex() const { return selectedActiveModuleIndex_; }

    static MoriartyModule* getModuleByName(const char_t *name) {return ::getModuleByName(MORIARTY_MODULES_COUNT, modules_, name);}
    
    static MoriartyModule* getModuleById(ModuleID moduleId);
    
    static MoriartyModule& getModule(uint_t index);
    
    static void touchModule(ModuleID moduleId);
    
    static uint_t modulesCount();

    void savePreferences();    
    
    FontID standardFontId() const {return standardFontId_;}

    int         strListSize;
    char_t**    strList;
    
    HyperlinkHandler* hyperlinkHandler;
    
    Err handleLaunchCode(UInt16 cmd, MemPtr cmdPBP, UInt16 launchFlags);
    
    bool isNewVersionAvailable();
    
private:

    static MoriartyModule modules_[MORIARTY_MODULES_COUNT];

    uint_t          selectedActiveModuleIndex_;   
    Preferences*    preferences_;
    FontID          standardFontId_;
    
};

#endif
