#include <SysUtils.hpp>
#include <SocketConnection.hpp>
#include <Text.hpp>

#include <DeviceInfo.hpp>
#include <FileReader.hpp>
#include <File.hpp>
#include <DataStore.hpp>
#include <Serializer.hpp>
#include <PrefsStore.hpp>

#ifdef DEBUG
#include "UnitTests.hpp"
#endif

#include "MoriartyApplication.hpp"
#include "MoriartyPreferences.hpp"

#include "ModulesData.hpp"
#include "LookupManager.hpp"

#include "Forms/MainForm.hpp"
#include "Forms/MoviesMainForm.hpp"
#include "Forms/WeatherMainForm.hpp"
#include "Forms/RegistrationForm.hpp"
#include "Forms/ChangeLocationForm.hpp"
#include "Forms/SelectLocationForm.hpp"
#include "Forms/SelectStateForm.hpp"
#include "Forms/ConnectionProgressForm.hpp"
#include "Forms/EpicuriousMainForm.hpp"
#include "Forms/AmazonMainForm.hpp"
#include "Forms/NotImplementedForm.hpp"
#include "Forms/M411MainForm.hpp"
#include "Forms/M411EnterZipForm.hpp"
#include "Forms/M411EnterAreaForm.hpp"
#include "Forms/M411EnterCityForm.hpp"
#include "Forms/M411EnterPersonForm.hpp"
#include "Forms/M411EnterBusinessForm.hpp"
#include "Forms/M411EnterPhoneForm.hpp"
#include "Forms/BoxOfficeMainForm.hpp"
#include "Forms/DreamsMainForm.hpp"
#include "Forms/JokesMainForm.hpp"
#include "Forms/JokesSearchForm.hpp"
#include "Forms/CurrencyMainForm.hpp"
#include "Forms/SelectCurrencyForm.hpp"
#include "Forms/EpicuriousPreferencesForm.hpp"
#include "Forms/StocksMainForm.hpp"
#include "Forms/GasPricesMainForm.hpp"
#include "Forms/NetflixMainForm.hpp"
#include "Forms/NetflixSearchForm.hpp"
#include "Forms/SimpleTextDoneForm.hpp"
#include "Forms/NetflixEnterLoginForm.hpp"
#include "Forms/HoroscopesMainForm.hpp"
#include "Forms/ListsOfBestsMainForm.hpp"
#include "Forms/ListsOfBestsSearchForm.hpp"
#include "Forms/Lyrics2MainForm.hpp"
#include "Forms/LyricsSearchForm.hpp"
#include "Forms/TvListingsMainForm.hpp"
#include "Forms/PediaMainForm.hpp"
#include "Forms/DictMainForm.hpp"
#include "Forms/QuotesMainForm.hpp"
#include "Forms/eBookMainForm.hpp"
#include "Forms/FlightsMainForm.hpp"
#include "Forms/FlightsSearchForm.hpp"
#include "Forms/EBayMainForm.hpp"

#ifndef SHIPPING
#include "Forms/TestWikiMainForm.hpp"
#endif

#include "Forms/PreferencesForm.hpp"

#include "HyperlinkHandler.hpp"

#include "flickr.hpp"

#include "Forms/FlickrMainForm.hpp"

IMPLEMENT_APPLICATION_CREATOR(appFileCreator)

uint_t activeModulesCount(uint_t modulesCount, const MoriartyModule* modules)
{
    uint_t count = 0;
    for (uint_t i=0; i<modulesCount; i++)
    {
        if (modules[i].active())
            ++count;
    }
    return count;
}   

MoriartyModule* getActiveModule(uint_t modulesCount, MoriartyModule* modules, uint_t moduleNo)
{
    assert(moduleNo<=activeModulesCount(modulesCount, modules));
    uint_t activeCount = 0;
    for (uint_t i=0; i<modulesCount; i++)
    {
        MoriartyModule& module=modules[i];
        if (module.active())
        {
            if (moduleNo == activeCount)
                return &module;
            ++activeCount;
        }
    }
    assert(false);
    return NULL;
}

MoriartyModule* getModuleByName(uint_t modulesCount, MoriartyModule* modules, const ArsLexis::char_t * name)
{
    for (uint_t i=0; i<modulesCount; i++)
    {
        if ( 0 == (StrCompare(modules[i].name, name)) )
            return &modules[i];
    }
    return NULL;
}

MoriartyApplication::MoriartyApplication():
    lookupManager(NULL),
    regCodeDaysToExpire(REG_CODE_DAYS_NOT_SET),
    preferences_(NULL),
    selectedActiveModuleIndex_(moduleNone),
    strList(NULL),
    strListSize(0),
    fLatestClientVersionRetrieved(false),
    standardFontId_(largeFont),
    hyperlinkHandler(NULL)
{
}

//#pragma inline_depth(2)

inline void MoriartyApplication::detectViewer()
{
    UInt16  cardNo;
    LocalID dbID;

    if (fDetectViewer(&cardNo,&dbID))
    {
        assert(dbID!=0);
    }
}

Err MoriartyApplication::initialize()
{
    Err error=RichApplication::initialize();
    detectViewer();
    return error;
}

MoriartyApplication::~MoriartyApplication()
{
    // This if below is here on purpose. Don't remove it. If you do so, expect crash on non-global launch.
    if (NULL != lookupManager)
        delete lookupManager;
    if (NULL != preferences_)
        delete preferences_;

    if (NULL != strList)
        FreeStringList(strList, strListSize);

}

// DEFINE_MORIARTY_MODULE
#define DEF_M_M(ID, NAME, SMALL_ICON, LARGE_ICON, FORM_ID, DATA_FUN, tracksUpdate, free) \
  { ID, NAME, NAME, SMALL_ICON, LARGE_ICON, FORM_ID, free, false, false, false, DATA_FUN, tracksUpdate, moduleNeverUpdated},

MoriartyModule MoriartyApplication::modules_[MORIARTY_MODULES_COUNT] =
{
    DEF_M_M(moduleIdWeather, "Weather", weatherSmallBitmap, frmInvalidObjectId, weatherMainForm, weatherDataRead, true, false)
    DEF_M_M(moduleId411, "Phone book", m411SmallBitmap, frmInvalidObjectId, m411MainForm, m411DataRead, false, false)
    DEF_M_M(moduleIdMovies, "Movie times", moviesSmallBitmap, frmInvalidObjectId, moviesMainForm, moviesDataRead, true, false)
    DEF_M_M(moduleIdAmazon, "Amazon", amazonSmallBitmap, frmInvalidObjectId, amazonMainForm, NULL, false, false)
    DEF_M_M(moduleIdBoxOffice, "Box office", boxofficeSmallBitmap, frmInvalidObjectId, boxOfficeMainForm, boxOfficeDataRead, true, true)
    DEF_M_M(moduleIdNetflix, "Netflix", netflixSmallBitmap, frmInvalidObjectId, netflixMainForm, netflixDataRead, false, false)
    DEF_M_M(moduleIdCurrency, "Currency", currencySmallBitmap, frmInvalidObjectId, currencyMainForm, currencyDataRead, true, false)
    DEF_M_M(moduleIdStocks, "Stocks", stocksSmallBitmap, frmInvalidObjectId, stocksMainForm, stocksDataRead, true, false)
    DEF_M_M(moduleIdJokes, "Jokes", jokesSmallBitmap, frmInvalidObjectId, jokesMainForm, jokesDataRead, false, true)
    DEF_M_M(moduleIdGasPrices, "Gas prices", gasPricesSmallBitmap, frmInvalidObjectId, gasPricesMainForm, gasPricesDataRead, true, false)
    DEF_M_M(moduleIdHoroscopes, "Horoscopes", horoscopesSmallBitmap, frmInvalidObjectId, horoscopesMainForm, horoscopeDataRead, true, true) 
    DEF_M_M(moduleIdDreams, "Dreams", dreamsSmallBitmap, frmInvalidObjectId, dreamsMainForm, dreamsDataRead, false, true)
    DEF_M_M(moduleIdAbout, "About", aboutSmallBitmap, frmInvalidObjectId, frmInvalidObjectId, NULL, false, false)
#ifndef SHIPPING
    // this one's special: it never ships
    DEF_M_M(moduleIdTestWiki, "Test parser", aboutSmallBitmap, frmInvalidObjectId, testWikiMainForm, NULL, true, false)
#endif
#ifndef SHIPPING

    // WARNING!!!
    // When changing module to appear in "shipping" version remember to change this in MoriartyPreferences.cpp as well
    // (Preferences::serialize) and MoriartyApplication::createForm() in this file
    
    DEF_M_M(moduleIdPedia, "Encyclopedia", encyclopediaSmallBitmap, frmInvalidObjectId, pediaMainForm, NULL, true, false)
    DEF_M_M(moduleIdDict, "Dictionary", dictionarySmallBitmap, frmInvalidObjectId, dictMainForm, NULL, true, false)
    DEF_M_M(moduleIdLyrics, "Lyrics", lyricsSmallBitmap, frmInvalidObjectId, lyrics2MainForm, NULL, false, false)
    DEF_M_M(moduleIdRecipes, "Recipes", epicuriousSmallBitmap, frmInvalidObjectId, epicuriousMainForm, epicuriousDataRead, false, false)
    DEF_M_M(moduleIdListsOfBests, "Lists of bests", listofbestsSmallBitmap, frmInvalidObjectId, listsOfBestsMainForm, NULL, false, false) 
    DEF_M_M(moduleIdTvListings, "TV Listings", tvListingsSmallBitmap, frmInvalidObjectId, tvListingsMainForm, NULL, true, false)
    DEF_M_M(moduleIdQuotes, "Quotes", quotationsSmallBitmap, frmInvalidObjectId, quotesMainForm, quotesDataRead, true, true) 
    DEF_M_M(moduleIdEBooks, "eBooks",  ebooksSmallBitmap, frmInvalidObjectId, ebookMainForm, NULL, false, false) 
    DEF_M_M(moduleIdFlights, "Flights",  flightsSmallBitmap, frmInvalidObjectId, flightsMainForm, flightsDataRead, true, false) 
    DEF_M_M(moduleIdEBay, "eBay", eBaySmallBitmap, frmInvalidObjectId, eBayMainForm, NULL, false, false)
    DEF_M_M(moduleIdFlickr, "Flickr", flickrSmallBitmap, frmInvalidObjectId, flickrMainForm, NULL, false, true)
#endif
};

// Another possibility: init the list at runtime, instead of statically
/*
// DEFINE_MORIARTY_MODULE
#define DEF_M_M(NAME, SMALL_ICON, LARGE_ICON, FORM_ID, DATA_FUN) \
    modules_[moduleNo].name_ = NAME; \
    modules_[moduleNo].displayName_ = NAME; \
    modules_[moduleNo].smallIconId_ = SMALL_ICON; \
    modules_[moduleNo].largeIconId_ = LARGE_ICON; \
    modules_[moduleNo].mainFormId_ = FORM_ID; \
    modules_[moduleNo].free_ = false; \
    modules_[moduleNo].dataRead_ = false; \
    modules_[moduleNo].active_ = true; \
    modules_[moduleNo].moduleDataReadFunction_ = DATA_FUN; \
    ++moduleNo

void MoriartyApplication::prepareModules()
{
    uint_t  moduleNo = 0;
    DEF_M_M("Movies", moviesSmallBitmap, frmInvalidObjectId, moviesMainForm, moviesDataRead);
    DEF_M_M("Weather", weatherSmallBitmap, frmInvalidObjectId, weatherMainForm, weatherDataRead);
    DEF_M_M("Recipes", epicuriousSmallBitmap, frmInvalidObjectId, epicuriousMainForm, epicuriousDataRead);
    DEF_M_M("411", m411SmallBitmap, frmInvalidObjectId, m411MainForm, NULL);
    DEF_M_M("Alert", frmInvalidObjectId, frmInvalidObjectId, notImplementedForm, NULL);
} */

Err MoriartyApplication::normalLaunch()
{
    Err err = errNone;
    UInt16 cardNo = 0;
    DmOpenRef fontDb = NULL;
    MemHandle fontHandle = NULL;
    FontPtr font = NULL;
//    LocalID localId = DmFindDatabase(cardNo, "NimbusSans15");
//    if (0 != localId)
//        fontDb = DmOpenDatabase(cardNo, localId, dmModeReadOnly);
//    if (NULL != fontDb)
//        fontHandle = DmGet1Resource('nfnt', 1572);
//    fontHandle = DmGetResource('NFNT', tahomaFont);
    if (NULL != fontHandle)
        font = static_cast<FontPtr>(MemHandleLock(fontHandle));
    if (NULL != font) {
        FontID id = fntAppFontCustomBase;
        Err error = FntDefineFont(id, font);
        if (errNone == error)
            standardFontId_ = id;
    }        

#ifndef SHIPPING
    InitLogging();
    LogAddMemoLog(eLogEverything);
#ifdef DEBUG
    LogAddFileLog(_T("\\var\\log\\moriarty.log"), eLogEverything);
    LogAddDebuggerLog(eLogEverything);
#endif    
#endif

    DataStore::initialize(appDataFile);
    
    preferences_ = new_nt Preferences();
    if (NULL == preferences_)
    {   
        err = memErrNotEnoughSpace;
        goto NoMemory;
    }
    
    loadPreferences();

    lookupManager = new_nt LookupManager();
    if (NULL == lookupManager)
    {
        err = memErrNotEnoughSpace;
        goto NoMemory;
    }

    hyperlinkHandler = new_nt HyperlinkHandler();
    if (NULL == hyperlinkHandler)
    {
        err = memErrNotEnoughSpace;
        goto NoMemory;
    }

#ifdef DEBUG
    RunAllUnitTests();
#endif

    gotoForm(mainForm);
    runEventLoop();

NoMemory:
    if (memErrNotEnoughSpace == err)
        alert(notEnoughMemoryAlert);
    
    savePreferences();
    DataStore::dispose();
    DeinitLogging();
    
    delete hyperlinkHandler;
    hyperlinkHandler = NULL;

    if (NULL != font)
        MemHandleUnlock(fontHandle);
    if (NULL != fontHandle)
        DmReleaseResource(fontHandle);
    if (NULL != fontDb)
        DmCloseDatabase(fontDb);
 
    return err;
}

void MoriartyApplication::waitForEvent(EventType& event)
{
    SocketConnectionManager& connManager = lookupManager->connectionManager();
    if (connManager.active())
    {
#ifdef ARSLEXIS_USE_SELECT_EVENTS
        if (!underSimulator())
            connManager.waitForEvent(event, evtWaitForever);
        else 
        {
#else
        {
#endif        
        setEventTimeout(0);
        Application::waitForEvent(event);
        if (nilEvent==event.eType)
            connManager.manageConnectionEvents(ticksPerSecond()/20);
        }
    }
    else
    {
        setEventTimeout(evtWaitForever);
        Application::waitForEvent(event);
    }        
}

Form* MoriartyApplication::createForm(UInt16 formId)
{
    Form* form = NULL;
    switch (formId)
    {
        case moviesMainForm:
            form = new_nt MoviesMainForm(*this);
            break;

        case weatherMainForm:
            form=new_nt WeatherMainForm(*this);
            break;
            
        case registrationForm:
            form=new_nt RegistrationForm(*this);
            break;

        case changeLocationForm:
            form=new_nt ChangeLocationForm(*this);
            break;
            
        case selectLocationForm:
            form=new_nt SelectLocationForm(*this);
            break;

        case selectStateForm:
            form=new_nt SelectStateForm(*this);
            break;

        case mainForm:
            form=new_nt MainForm(*this);
            break;
            
        case connectionProgressForm:
            form=new_nt ConnectionProgressForm(*this);
            break;

        case m411MainForm:
            form=new_nt M411MainForm(*this);
            break;
            
        case boxOfficeMainForm:
            form=new_nt BoxOfficeMainForm(*this);
            break;

        case stocksMainForm:
            form=new_nt StocksMainForm(*this);
            break;

        case m411EnterZipForm:
            form=new_nt M411EnterZipForm(*this);
            break;

        case m411EnterAreaForm:
            form=new_nt M411EnterAreaForm(*this);
            break;

        case m411EnterPhoneForm:
            form=new_nt M411EnterPhoneForm(*this);
            break;

        case m411EnterPersonForm:
            form=new_nt M411EnterPersonForm(*this);
            break;

        case m411EnterBusinessForm:
            form=new_nt M411EnterBusinessForm(*this);
            break;

        case m411EnterCityForm:
            form=new_nt M411EnterCityForm(*this);
            break;

        case notImplementedForm:
            form=new_nt NotImplementedForm(*this);
            break;
            
        case preferencesForm:
            form = new_nt PreferencesForm(*this);
            break;

        case jokesMainForm:
            form = new_nt JokesMainForm(*this);
            break;

        case jokesSearchForm:
            form = new_nt JokesSearchForm(*this);
            break;

        case selectCurrencyForm:
            form = new_nt SelectCurrencyForm(*this);
            break;

        case currencyMainForm:
            form = new_nt CurrencyMainForm(*this);
            break;

        case gasPricesMainForm:
            form = new_nt GasPricesMainForm(*this);
            break;

        case horoscopesMainForm:
            form = new_nt HoroscopesMainForm(*this);
            break;

        case dreamsMainForm:
            form = new_nt DreamsMainForm(*this);
            break;

        case amazonMainForm:
            form = new_nt AmazonMainForm(*this);
            break;

        case netflixMainForm:
            form = new_nt NetflixMainForm(*this);
            break;

        case netflixSearchForm:
            form = new_nt NetflixSearchForm(*this);
            break;

        case netflixEnterLoginForm:
            form = new_nt NetflixEnterLoginForm(*this);
            break;

#ifndef SHIPPING
        case epicuriousMainForm:
            form=new_nt EpicuriousMainForm(*this);
            break;

        case epicuriousPreferencesForm:
            form = new_nt EpicuriousPreferencesForm(*this);
            break;

        case listsOfBestsMainForm:
            form = new_nt ListsOfBestsMainForm(*this);
            break;

        case listsOfBestsSearchForm:
            form = new_nt ListsOfBestsSearchForm(*this);
            break;

        case lyrics2MainForm:
            form = new_nt Lyrics2MainForm(*this);
            break;

        case lyricsSearchForm:
            form = new_nt LyricsSearchForm(*this);
            break;
            
        case tvListingsMainForm:
            form = new_nt TvListingsMainForm(*this);
            break;

        case pediaMainForm:
            form = new_nt PediaMainForm(*this);
            break;

        case dictMainForm:
            form = new_nt DictMainForm(*this);
            break;

        case quotesMainForm:
            form = new_nt QuotesMainForm(*this);
            break;
            
        case ebookMainForm:
            form = new_nt EBookMainForm(*this);
            break;
        
        case flightsMainForm:
            form = new_nt FlightsMainForm(*this);
            break;

        case flightsSearchForm:
            form = new_nt FlightsSearchForm(*this);
            break;

        case eBayMainForm:
            form = new_nt EBayMainForm(*this);
            break;

        case flickrMainForm:
            form = new_nt FlickrMainForm(*this);
            break;
            
#endif
          
#ifndef SHIPPING
        case testWikiMainForm:
            form = new_nt TestWikiMainForm(*this);
            break;
#endif
        default:
            assert(false);
    }
    return form;            
}

bool MoriartyApplication::handleApplicationEvent(EventType& event)
{
    bool handled=false;
    if (appFetchMoviesEvent==event.eType)
    {
        handleFetchMoviesEvent();
        handled=true;
    }
    if (appFetchWeatherEvent==event.eType)
    {
        handleFetchWeatherEvent();
        handled=true;
    }
    if (NULL != lookupManager && appLookupEventFirst<=event.eType && appLookupEventLast>=event.eType)
        lookupManager->handleLookupEvent(event);
    else
        handled=RichApplication::handleApplicationEvent(event);
    return handled;
}

void MoriartyApplication::loadPreferences()
{
    DataStore* ds = DataStore::instance();
    if (NULL == ds)
        return;
    DataStoreReader reader(*ds);
    status_t error = reader.open(globalPrefsStream);
    if (errNone != error)
        return;
    Preferences prefs;
    Serializer serializer(reader);
    error = prefs.serialize(serializer);
    if (errNone != error)
    {
        LogStrUlong(eLogError, "MoriartyApplication::loadPreferences(): prefs.serialize() returned error: ", error);
        return;
    }
    assert(prefs.horoscopesPreferences.downloadedSign != -1);
    preferences_->swap(prefs);
}

void MoriartyApplication::savePreferences()
{
    DataStore* ds = DataStore::instance();
    if (NULL == ds)
        return;
    DataStoreWriter writer(*ds);
    status_t error = writer.open(globalPrefsStream);
    if (errNone != error)
        return;
    Serializer serializer(writer);
    error = preferences_->serialize(serializer);
    if (errNone != error)
        LogStrUlong(eLogError, "MoriartyApplication::savePreferences(): prefs.serialize() returned error: ", error);
}

void MoriartyApplication::handleFetchMoviesEvent()
{
    if (lookupManager->lookupInProgress())
        sendDisplayAlertEvent(connectionInProgressAlert);
    else
    {
        MoriartyApplication& app = MoriartyApplication::instance();
        Preferences& prefs = app.preferences();
        lookupManager->fetchMovies(prefs.moviesLocation.c_str());
    }
}

void MoriartyApplication::handleFetchWeatherEvent()
{
    if (lookupManager->lookupInProgress())
        sendDisplayAlertEvent(connectionInProgressAlert);
    else
        lookupManager->fetchWeather();
}

void MoriartyApplication::runMainForm()
{
    gotoForm(mainForm);
}

void MoriartyApplication::runModule(uint_t index)
{
    assert(moduleNone!=index);  // use runMainForm() for that

    assert(index<activeModulesCount(MORIARTY_MODULES_COUNT, modules()));
    MoriartyModule * activeModule = getActiveModule(MORIARTY_MODULES_COUNT, modules_, index);

    if (!activeModule->dataRead && (NULL != activeModule->moduleDataReadFunction))
    {
        activeModule->dataRead = true;
        activeModule->moduleDataReadFunction(*this);
    }
    selectedActiveModuleIndex_ = index;
    if (moduleIdAbout == activeModule->id)
    {
        (new SimpleTextDoneForm(*this, SimpleTextDoneForm::showAboutMain, 0))->popup();
    }
    else
        gotoForm(activeModule->mainFormId);
}

void MoriartyApplication::runModuleById(ModuleID id)
{
    MoriartyModule * module = getModuleById(id);
    assert(NULL != module);
    
    if (!module->dataRead && (NULL != module->moduleDataReadFunction))
    {
        module->dataRead = true;
        module->moduleDataReadFunction(*this);
    }
    selectedActiveModuleIndex_ = 0;
    for (int i=0; i < MORIARTY_MODULES_COUNT; i++)
    {
        if (modules_[i].active())
        {
            if (id == modules_[i].id)
                break;
            selectedActiveModuleIndex_++;
        }
    }
    
    if (moduleIdAbout == id)
    {
        (new SimpleTextDoneForm(*this, SimpleTextDoneForm::showAboutMain, 0))->popup();
    }
    else
        gotoForm(module->mainFormId);
}

MoriartyModule* MoriartyApplication::getModuleById(ModuleID moduleId)
{

    for (int i=0; i<MORIARTY_MODULES_COUNT; i++)
    {
        if (modules_[i].id == moduleId)
            return &(modules_[i]);
    }
    return NULL;
}

MoriartyModule& MoriartyApplication::getModule(uint_t index)
{
    assert(MORIARTY_MODULES_COUNT > index);
    return modules_[index];
}

uint_t MoriartyApplication::modulesCount() 
{
    return ARRAY_SIZE(modules_);
}

void MoriartyApplication::touchModule(ModuleID moduleId)
{
    MoriartyModule* module = getModuleById(moduleId);
    if (NULL == module)
        return;
    if (!module->tracksUpdateTime)
        return;
    module->lastUpdateTime = TimGetSeconds();
}

Err MoriartyApplication::handleLaunchCode(UInt16 cmd, MemPtr cmdPBP, UInt16 launchFlags)
{
#if FLICKR_ENABLED
    if (sysAppLaunchCmdSystemReset == cmd || sysAppLaunchCmdSyncNotify == cmd || sysAppLaunchCmdNormalLaunch == cmd)
    {
        status_t err = FlickrInitialize();
    }
#endif
    return RichApplication::handleLaunchCode(cmd, cmdPBP, launchFlags);    
}

bool MoriartyApplication::isNewVersionAvailable()
{
    if ( !preferences_->latestClientVersion.empty() )
    {
        const char_t *latestVersion = preferences_->latestClientVersion.c_str();
        if (versionNumberCmp(latestVersion, appVersion) > 0)
            return true;
    }        
    return false;
}
