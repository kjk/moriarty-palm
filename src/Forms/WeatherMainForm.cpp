#include <algorithm>

#include <SysUtils.hpp>
#include <Text.hpp>
#include <DynStr.hpp>

#include <Definition.hpp>
#include <TextElement.hpp>
#include <LineBreakELement.hpp>
#include <HorizontalLineElement.hpp>
#include <BulletElement.hpp>

#include "LookupManager.hpp"
#include "MoriartyPreferences.hpp"
#include "WeatherMainForm.hpp"
#include <SysUtils.hpp>

#if defined(__MWERKS__)
# pragma far_code
#endif

/***
IMPORTANT:
- weatherData in UDF
- in UDF first item is detailed info about today/tonight so:
    when you get item from UDF get by itemNo:
        currentWeatherNumber_ + 1
    when you get days count use:
        weatherData_->getItemsCount() - 1
 */

#define prefixSky               _T("Sky: ")
#define prefixTemperatureDay    _T("Day: ")
#define betweenDayAndNight      _T("     ")
#define prefixTemperatureNight  _T("Night: ")
#define prefixPrecip            _T("Precipitation: ")

#define prefixFTemperature  _T("Now: ")
#define prefixFSky          _T("Sky: ")
#define prefixFFeelsLike    _T("Feels like: ")
#define prefixFUVIndex      _T("UV index: ")
#define prefixFDewPoint     _T("Dew point: ")    //ignored
#define prefixFHumidity     _T("Humidity: ")
#define prefixFVisibility   _T("Visibility: ")
#define prefixFPressure     _T("Pressure: ")
#define prefixFWind         _T("Wind: ")

//indexes in UDF
#define detailedTemperatureInUDF 0
#define detailedSkyInUDF 1
#define detailedFeelsLikeInUDF 2
#define detailedUVIndexInUDF 3
#define detailedDevPointInUDF 4
#define detailedHumidityInUDF 5
#define detailedVisibilityInUDF 6
#define detailedPressureInUDF 7
#define detailedWindInUDF 8

#define dailyDayInUDF 0
#define dailyDateInUDF 1
#define dailySkyInUDF 2
#define dailyTemperatureDayInUDF 3
#define dailyTemperatureNightInUDF 4
#define dailyPrecipInUDF 5


const uint_t bitmapX=10;
const uint_t bitmapXFirstDay=110;
const uint_t bitmapY=60;
const uint_t bitmapYFirstDay=65;

const char_t degSymbol=_T('\xB0');
const char_t fahrenheitSymbol=_T('F');
const char_t celsiusSymbol=_T('C');

inline int toCelsius(int f)
{
    //this is return round((10*(f-32))/18);
    if(f-32 >= 0)
        return (int)((10*(f-32) + 5)/18);
    else
        return (int)((10*(f-32) - 5)/18);
} 

class WeatherPopupListDrawHandler: public List::CustomDrawHandler {

private:    
    UniversalDataFormat* weatherData_;
        
public:
    
    WeatherPopupListDrawHandler(UniversalDataFormat* weatherData):
        weatherData_(weatherData) {}
        
    uint_t itemsCount() const
    {
        if (weatherData_->empty())
            return 0;
        else
            return weatherData_->getItemsCount()-1;
    }

    void drawItem(Graphics& graphics, List& list, uint_t item, const ArsRectangle& itemBounds);

    ~WeatherPopupListDrawHandler();
    
};

void WeatherPopupListDrawHandler::drawItem(Graphics& graphics, List& list, uint_t item, const ArsRectangle& itemBounds)
{
    if (item>=weatherData_->getItemsCount()-1)
        return;
    uint_t width = itemBounds.width();

    bool willBeMonth = true;

    const char_t* text;
    ulong_t lengthLong;
    uint_t length;

    text = weatherData_->getItemTextAndLen(item+1, dailyDayInUDF, &lengthLong);
    length = lengthLong;

    // if the first item is "Tonight", then we don't have the month
    if ((0 == item) && (0 == tstrncmp(text, _T("To"), 2)))
            willBeMonth = false;

    graphics.charsInWidth(text, length, width);
    graphics.drawText(text, length, itemBounds.topLeft);

    if (!willBeMonth)
        return;

    text = weatherData_->getItemTextAndLen(item+1, dailyDateInUDF, &lengthLong);
    length = lengthLong;
    width = (itemBounds.width()*3)/5;
    Point newLeft = itemBounds.topLeft;
    newLeft.x += (itemBounds.width()*2)/5;
    graphics.charsInWidth(text, length, width);
    graphics.drawText(text, length, newLeft);
}

WeatherPopupListDrawHandler::~WeatherPopupListDrawHandler()
{}

class WeatherListDrawHandler: public ExtendedList::ItemRenderer {

private:    
    UniversalDataFormat* weatherData_;
    const WeatherMainForm::DegreesMode& degreesMode_;
public:
    
    WeatherListDrawHandler(UniversalDataFormat* weatherData, const WeatherMainForm::DegreesMode& degreesMode):
        weatherData_(weatherData), degreesMode_(degreesMode) {}
        
    uint_t itemsCount() const
    {
        if (weatherData_->empty())
            return 0;
        else
            return weatherData_->getItemsCount()-1;
    }

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);

    ~WeatherListDrawHandler();
    
};

#define LEFT_MARGIN 2

void WeatherListDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    if (item >= weatherData_->getItemsCount()-1)
        return;

    Point newTop = itemBounds.topLeft;
    Point newTopAligned;
    // set display offsets:
    uint_t display1 = itemBounds.width()/3;
    uint_t display2 = itemBounds.width()/5;
    uint_t display3 = itemBounds.width() - display2 - display1;

    // day
    uint_t width = display1;
    bool willBeMonth = true;

    const char_t* text2;
    uint_t length;
    ulong_t lengthLong;

    text2 = weatherData_->getItemTextAndLen(item+1, dailyDayInUDF, &lengthLong);
    length = lengthLong;

    // if the first item is "Tonight", then we don't have the month
    // "Today/Tonight Jul 13" is too long!
    if ((0 == item) && (0 == tstrncmp(text2, _T("To"), 2)))
            willBeMonth = false;

    Point p = itemBounds.topLeft;
    p.x += LEFT_MARGIN;

    graphics.charsInWidth(text2, length, width);
    graphics.drawText(text2, length, p);

    if (willBeMonth)
    {
        text2 = weatherData_->getItemTextAndLen(item+1, dailyDateInUDF, &lengthLong);
        length = lengthLong;
        width = (display1 * 3) / 5;
        newTopAligned = newTop;
        newTopAligned.x += (display1 - width);
        newTopAligned.x += LEFT_MARGIN;
        graphics.charsInWidth(text2, length, width);
        graphics.drawText(text2, length, newTopAligned);
    }

    String text;

    // temperature "day/night"
    newTop.x += display1;
    newTopAligned = newTop;
    width = display2 - 6;
    char_t buffer[32];
    if (WeatherMainForm::fahrenheitMode == degreesMode_)
        StrPrintF(buffer, "%d", (int) (weatherData_->getItemTextAsLong(item+1,dailyTemperatureDayInUDF)));
    else
        StrPrintF(buffer, "%d", toCelsius(weatherData_->getItemTextAsLong(item+1,dailyTemperatureDayInUDF)));
    text.assign(_T(buffer));
    text.append(1, degSymbol);

    if (WeatherMainForm::fahrenheitMode == degreesMode_)
        text.append(1, fahrenheitSymbol);
    else
        text.append(1, celsiusSymbol);

    length = text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    newTopAligned.x += display2 - 6 - width;
    graphics.drawText(text.c_str(), length, newTopAligned);

    // sky
    newTop.x += display2;
    width = display3;
    text2 = weatherData_->getItemTextAndLen(item+1, dailySkyInUDF, &lengthLong);
    length = lengthLong;
    graphics.charsInWidth(text2, length, width);
    graphics.drawText(text2, length, newTop);
}

WeatherListDrawHandler::~WeatherListDrawHandler()
{}

WeatherMainForm::~WeatherMainForm()
{}

WeatherMainForm::WeatherMainForm(MoriartyApplication& app):
    MoriartyForm(app, weatherMainForm),
    weatherData_(0),
    displayMode_(weatherSummaryView),
    ignoreNextPenUp_(false),
    nextDayButton_(*this),
    prevDayButton_(*this),
    weatherList_(*this),
    weatherSummaryButton_(*this),
    updateButton_(*this),
    weatherDoneButton_(*this),
    weatherPopupTrigger_(*this),
    weatherPopupList_(*this),
    currentWeatherNumber_(0),
    degreesMode_(fahrenheitMode),
    weatherRenderer_(*this, NULL)
{
    weatherRenderer_.setInteractionBehavior(0);
    
    setFocusControlId(weatherList);
}

void WeatherMainForm::attachControls()
{
    MoriartyForm::attachControls();
    nextDayButton_.attach(nextDayButton);
    prevDayButton_.attach(prevDayButton);
    weatherDoneButton_.attach(doneButton);
    weatherList_.attach(weatherList);
    weatherPopupTrigger_.attach(weatherPopupTrigger);
    weatherPopupList_.attach(weatherPopupList);
    weatherSummaryButton_.attach(summaryButton);
    weatherRenderer_.attach(weatherRenderer);
    weatherRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);    
    updateButton_.attach(updateButton);
}

bool WeatherMainForm::handleOpen()
{
    bool res=MoriartyForm::handleOpen();

    weatherList_.setItemHeight(12);
    
    MoriartyApplication& app=application();
    if (app.preferences().weatherPreferences.fDegreesModeCelsius)
        degreesMode_ = celsiusMode;
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL != lookupManager);

    weatherData_ = &lookupManager->weatherData;
    setDisplayMode(displayMode_);

    if (0 == lookupManager->weatherData.getItemsCount() && !app.preferences().weatherPreferences.weatherLocation.empty())
        sendEvent(MoriartyApplication::appFetchWeatherEvent);
    else if (app.preferences().weatherPreferences.weatherLocation.empty())
    {
        Application::popupForm(changeLocationForm);
        sendEvent(MoriartyApplication::appSetWeatherEvent);
    }
    else if (!lookupManager->weatherData.empty())
    {
        weatherList_.notifyItemsChanged();
        weatherList_.setSelection(0, weatherList_.redrawNot);
    }

    updateTitle();
    return res;
}

void WeatherMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(screenBounds);
    weatherDoneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    updateButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    weatherSummaryButton_.anchor(screenBounds, anchorLeftEdge, 52, anchorTopEdge, 14);
    weatherPopupTrigger_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    weatherPopupList_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 114);
    weatherList_.anchor(screenBounds, anchorRightEdge, 0, anchorBottomEdge, 36);
    weatherRenderer_.anchor(screenBounds, anchorRightEdge, 0, anchorBottomEdge, 36);
    prevDayButton_.anchor(screenBounds, anchorLeftEdge, 26, anchorNot, 0);
    nextDayButton_.anchor(screenBounds, anchorLeftEdge, 14, anchorNot, 0);

    update();    
}

uint_t WeatherMainForm::getBitmapIdFromSky(const String& sky)
{
    bool sun = (sky.npos!=sky.find(_T("Sun")));
    bool rain = (sky.npos!=sky.find(_T("Rain"))) 
             || (sky.npos!=sky.find(_T("Showers")));
    bool snow = (sky.npos!=sky.find(_T("Snow"))); 
    bool storm = (sky.npos!=sky.find(_T("Storm")))
              || (sky.npos!=sky.find(_T("Thunder")));
    bool cloud = (sky.npos!=sky.find(_T("Cloud")));

    //sunny
    bool light = (sky.npos!=sky.find(_T("Isolated")))
              || (sky.npos!=sky.find(_T("Partly")))
              || (sky.npos!=sky.find(_T("Scattered")));


    //analyze this
    if (snow)
    {
        if (light || sun)
            return weatherSky_SunnySnow;
        return weatherSky_Snow;
    }
    if (storm)
    {
        if (light || sun)
            return weatherSky_SunnyStorm;
        return weatherSky_Storm;
    }
    if (rain)
    {
        if (light || sun)
            return weatherSky_SunnyRain;
        return weatherSky_Rain;
    }
    if (cloud)
    {
        if (light || sun)
            return weatherSky_SunnyClouds;
        return weatherSky_Clouds;
    }
    if (sun)
        return weatherSky_Sunny;
   
    return weatherSky_NA;
}

void WeatherMainForm::drawSkyBitmap(Graphics& graphics, const ArsRectangle& bounds)
{
    if (0 == weatherData_->getItemsCount())
        return;
    //ignore Tonight (we dont have moon images)    
    if (currentWeatherNumber_ == 0)
        if (0 == tstrcmp(_T("Tonight"), weatherData_->getItemText(currentWeatherNumber_+1,dailyDayInUDF)))
            return;

    uint_t iconId=getBitmapIdFromSky(weatherData_->getItemText(currentWeatherNumber_+1,dailySkyInUDF));
    if (frmInvalidObjectId!=iconId)
    {
        MemHandle handle=DmGet1Resource(bitmapRsc, iconId);
        if (handle) 
        {
            BitmapType* bmp=static_cast<BitmapType*>(MemHandleLock(handle));
            if (bmp) 
            {
                //TODO: if can - set bitmapY if it is possible
                WinDrawBitmap(bmp, bounds.x()+((currentWeatherNumber_==0)?bitmapXFirstDay:bitmapX), bounds.y()+((currentWeatherNumber_==0)?bitmapYFirstDay:bitmapY));
                MemHandleUnlock(handle);
            }
            DmReleaseResource(handle);
        }
    } 
}

void WeatherMainForm::redrawSkyBitmap() 
{
    Graphics graphics(windowHandle());
    ArsRectangle rect(bounds());
    if (weatherDailyView == displayMode_ && !weatherRenderer_.empty())
        drawSkyBitmap(graphics, rect);
}

void WeatherMainForm::showControls(bool show)
{
    if (!show)
    {
        enableControls(show);
        prevDayButton_.hide();
        nextDayButton_.hide();
        weatherList_.hide();
        weatherPopupTrigger_.hide();
        weatherPopupList_.hide();
        updateButton_.hide();
        return;
    }

    switch (displayMode())
    {
        case weatherDailyView:
            prevDayButton_.show();
            nextDayButton_.show();
            updateButton_.hide();
            weatherList_.hide();
            weatherPopupTrigger_.show();
            weatherPopupList_.hide();
            weatherSummaryButton_.show();
            weatherRenderer_.show();
            break;

        case weatherSummaryView:
            weatherRenderer_.hide();
            prevDayButton_.hide();
            nextDayButton_.hide();
            weatherList_.show();
            weatherPopupTrigger_.hide();
            weatherPopupList_.hide();
            weatherSummaryButton_.hide();
            updateButton_.show();
            break;
           
        default:
            assert(false);
    }
    enableControls(show);
}

void WeatherMainForm::enableControls(bool enable)
{
    if (!enable)
    {
        prevDayButton_.hide();
        nextDayButton_.hide();
        weatherList_.hide();
        weatherPopupTrigger_.hide();
        weatherPopupList_.hide();
        updateButton_.hide();
        return;
    }

    switch (displayMode())
    {
        case weatherDailyView:
            bool enable = false;

            if (currentWeatherNumber_ > 0)
                enable = true;

            if (enable)
                prevDayButton_.setGraphics(backBitmap);
            else
                prevDayButton_.setGraphics(backDisabledBitmap);

            enable = false;
            if ((weatherData_->getItemsCount()-2) > currentWeatherNumber_)
                enable = true;

            if (enable)
                nextDayButton_.setGraphics(forwardBitmap);
            else
                nextDayButton_.setGraphics(forwardDisabledBitmap);

            if (weatherPopupList_.itemsCount()>currentWeatherNumber_)
                weatherPopupList_.setSelection(currentWeatherNumber_);
            weatherPopupTrigger_.setLabel("");
            weatherPopupTriggerText_.assign(weatherData_->getItemText(currentWeatherNumber_+1,dailyDayInUDF));

            if (0 != tstrncmp(weatherData_->getItemText(currentWeatherNumber_+1, dailyDayInUDF), _T("To"), 2))
            {
                weatherPopupTriggerText_.append(1, ' ');
                weatherPopupTriggerText_.append(weatherData_->getItemText(currentWeatherNumber_+1, dailyDateInUDF));
            }
            weatherPopupTrigger_.setLabel(weatherPopupTriggerText_.c_str());
            break;

        case weatherSummaryView:
            break;

        default:
            assert(false);
    }
}

void WeatherMainForm::goToNextDay()
{
    if (currentWeatherNumber_ < (weatherData_->getItemsCount()-2))
    {
       ++currentWeatherNumber_;
       prepareWeatherInfo(currentWeatherNumber_);
       enableControls(true);
       update();
    }
}

void WeatherMainForm::goToPrevDay()
{
    if (currentWeatherNumber_ > 0)
    {
       --currentWeatherNumber_;
       prepareWeatherInfo(currentWeatherNumber_);
       enableControls(true);
       update();
    }
}

void WeatherMainForm::handleControlSelect(const EventType& event)
{
    MoriartyApplication& app = application();
    switch (event.data.ctlSelect.controlID)
    {
        case nextDayButton:
            goToNextDay();
            break;

        case prevDayButton:
            goToPrevDay();
            break;

        case weatherPopupTrigger:
            break;

        case summaryButton:
            if (!weatherData_)
                break;
            // disallow when no data available
            if (weatherData_->empty())
                break;
            setDisplayMode(weatherSummaryView);
            weatherList_.setSelection(currentWeatherNumber_);
            //update();
            break;

        /*case changeLocationButton:
            Application::popupForm(changeLocationForm);
            sendEvent(MoriartyApplication::appSetWeatherEvent);
            break;*/

        case updateButton:
            MoriartyApplication& app=application();
            if (!app.preferences().weatherPreferences.weatherLocation.empty())
                sendEvent(MoriartyApplication::appFetchWeatherEvent);
            break;

        case doneButton:
            application().runMainForm();
            break;
        default:
            assert(false);
    }
}

void WeatherMainForm::updateTitle(void)
{
    DynStr *title = DynStrFromCharP(_T("Weather"), 48);
    if (NULL == title)
        return;

    if (!weatherData_->empty())
    {
        const MoriartyApplication& app=application(); 
        if (app.preferences().weatherPreferences.weatherLocation == app.preferences().weatherPreferences.weatherLocationToServer)
        {
            if (NULL == DynStrAppendCharP3(title, _T(" for '"), app.preferences().weatherPreferences.weatherLocation.c_str(), _T("\'")))
                goto Exit;
        }
        else
        {
            if (NULL == DynStrAssignCharP(title, app.preferences().weatherPreferences.weatherLocation.c_str()))
                goto Exit;
        }
    }
    // to make sure that title will not cover prev/next buttons
    uint_t width = bounds().width()-30;
    uint_t length = DynStrLen(title);
    Graphics graphics;
    Font oldFont = graphics.setFont(boldFont);
    graphics.stripToWidthWithEllipsis(DynStrGetCStr(title), length, width, false);
    graphics.setFont(oldFont);
    setTitle(DynStrGetCStr(title));
Exit:
    if (NULL != title)
        DynStrDelete(title);
}

void WeatherMainForm::updateAfterLookup(LookupManager& lookupManager)
{
    weatherData_ = &lookupManager.weatherData;
    if (currentWeatherNumber_ >= weatherData_->getItemsCount()-1)
        currentWeatherNumber_ = weatherData_->getItemsCount()-2;
    setDisplayMode(weatherSummaryView);
    if (noListSelection == weatherList_.selection())
    {
        weatherList_.notifyItemsChanged();
        weatherList_.setSelection(0, weatherList_.redrawNot);
    }
    showControls(true);
    updateTitle();
    update();
}

void WeatherMainForm::handleLookupFinished(const EventType& event)
{
    bool closeForm = false;
    showControls(true);

    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL!=lookupManager);

    const LookupFinishedEventData& data = reinterpret_cast<const LookupFinishedEventData&>(event.data);
    switch (data.result)
    {
        case lookupResultWeatherData:
            MoriartyApplication::touchModule(moduleIdWeather);
            updateAfterLookup(*lookupManager);
            break;

        case lookupResultWeatherMultiselect:
            Application::popupForm(selectLocationForm);
            sendEvent(MoriartyApplication::appSetWeatherEvent);
            break;

        default:
            if (application().preferences().weatherPreferences.weatherLocation.empty())
                closeForm = true;
            update();            
    }
    lookupManager->handleLookupFinishedInForm(data);
    
    if (closeForm)
        application().runMainForm();
}

/**
 *  build definition filled with weather informations
 *  @weather - index in weather table
 */
void WeatherMainForm::prepareWeatherInfo(uint_t weather)
{
    assert(weather >= 0 && weather < weatherData_->getItemsCount()-1);
    
    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {   
        application().alert(notEnoughMemoryAlert);
        return;
    }
    Definition::Elements_t& elems = model->elements;

    if (weatherData_->empty())
    {
        // no data - insert only one element
        elems.push_back(new LineBreakElement());
        return;
    }
    TextElement* text;
    String toDisplay;
    char buffer[32];
    
    // sky
    toDisplay.assign(prefixSky).append(weatherData_->getItemText(weather+1,dailySkyInUDF));
    elems.push_back(text=new TextElement(toDisplay));
    elems.push_back(new LineBreakElement());
    // temperature day
    if(!startsWith(weatherData_->getItemText(weather+1,dailyDayInUDF),_T("Tonight")))
    {
        toDisplay.assign(prefixTemperatureDay);
        if(degreesMode_==fahrenheitMode)
            StrPrintF(buffer, "%d",(int) weatherData_->getItemTextAsLong(weather+1,dailyTemperatureDayInUDF));
        else
            StrPrintF(buffer, "%d",toCelsius((int) weatherData_->getItemTextAsLong(weather+1,dailyTemperatureDayInUDF)));
        toDisplay.append(buffer);
        toDisplay.append(1, degSymbol);
        toDisplay.append(1,(degreesMode_==fahrenheitMode)?fahrenheitSymbol:celsiusSymbol);
        toDisplay.append(betweenDayAndNight);
        elems.push_back(text=new TextElement(toDisplay));
    }
    // temperature night
    toDisplay.assign(prefixTemperatureNight);
    if (degreesMode_==fahrenheitMode)
        StrPrintF(buffer, "%d",(int) weatherData_->getItemTextAsLong(weather+1,dailyTemperatureNightInUDF));
    else
        StrPrintF(buffer, "%d",toCelsius((int) weatherData_->getItemTextAsLong(weather+1,dailyTemperatureNightInUDF)));
    toDisplay.append(buffer);
    toDisplay.append(1,degSymbol);
    toDisplay.append(1,(degreesMode_==fahrenheitMode)?fahrenheitSymbol:celsiusSymbol);
    elems.push_back(text=new TextElement(toDisplay));
    elems.push_back(new LineBreakElement());
    // precip.
    toDisplay.assign(prefixPrecip);
    StrPrintF(buffer, "%d",(int) weatherData_->getItemTextAsLong(weather+1,dailyPrecipInUDF));
    toDisplay.append(buffer);
    toDisplay.append(1, _T('%'));
    elems.push_back(text=new TextElement(toDisplay));
    elems.push_back(new LineBreakElement());

    if (0 == weather)
    {
        // sky
        toDisplay.assign(prefixFSky).append(weatherData_->getItemText(0,detailedSkyInUDF));
        elems.push_back(text=new TextElement(toDisplay));
        elems.push_back(new LineBreakElement());
        // temperature
        toDisplay.assign(prefixFTemperature);
        if(degreesMode_==fahrenheitMode)
            StrPrintF(buffer, "%d",(int) weatherData_->getItemTextAsLong(0,detailedTemperatureInUDF));
        else
            StrPrintF(buffer, "%d",toCelsius((int) weatherData_->getItemTextAsLong(0,detailedTemperatureInUDF)));
        toDisplay.append(buffer);
        toDisplay.append(1,degSymbol);
        toDisplay.append(1,(degreesMode_==fahrenheitMode)?fahrenheitSymbol:celsiusSymbol);
        elems.push_back(text=new TextElement(toDisplay));
        elems.push_back(new LineBreakElement());
        // feels like
        toDisplay.assign(prefixFFeelsLike);
        if(degreesMode_==fahrenheitMode)
            StrPrintF(buffer, "%d",(int) weatherData_->getItemTextAsLong(0,detailedFeelsLikeInUDF));
        else
            StrPrintF(buffer, "%d",toCelsius((int) weatherData_->getItemTextAsLong(0,detailedFeelsLikeInUDF)));
        toDisplay.append(buffer);
        toDisplay.append(1,degSymbol);
        toDisplay.append(1,(degreesMode_==fahrenheitMode)?fahrenheitSymbol:celsiusSymbol);
        elems.push_back(text=new TextElement(toDisplay));
        elems.push_back(new LineBreakElement());
        // humidity
        toDisplay.assign(prefixFHumidity);
        StrPrintF(buffer, "%d",(int) weatherData_->getItemTextAsLong(0,detailedHumidityInUDF));
        toDisplay.append(buffer);
        toDisplay.append(1, _T('%'));
        elems.push_back(text=new TextElement(toDisplay));
        elems.push_back(new LineBreakElement());
        // UV index
        toDisplay.assign(prefixFUVIndex).append(weatherData_->getItemText(0,detailedUVIndexInUDF));
        elems.push_back(text=new TextElement(toDisplay));
        elems.push_back(new LineBreakElement());
        // visibility
        toDisplay.assign(prefixFVisibility).append(weatherData_->getItemText(0,detailedVisibilityInUDF));
        localizeNumber(toDisplay);
        elems.push_back(text=new TextElement(toDisplay));
        elems.push_back(new LineBreakElement());
        // pressure
        toDisplay.assign(prefixFPressure).append(weatherData_->getItemText(0,detailedPressureInUDF));
        localizeNumber(toDisplay);
        elems.push_back(text=new TextElement(toDisplay));
        elems.push_back(new LineBreakElement());
        // wind
        toDisplay.assign(prefixFWind).append(weatherData_->getItemText(0,detailedWindInUDF));
        elems.push_back(text=new TextElement(toDisplay));
        elems.push_back(new LineBreakElement());

    }    
    weatherRenderer_.setModel(model, Definition::ownModel);
}

bool WeatherMainForm::handleEvent(EventType& event)
{
    if (weatherDailyView == displayMode_ && weatherRenderer_.handleEventInForm(event))
    {
//        redrawSkyBitmap();
        return true;
    }

    bool handled = false;
    switch (event.eType)
    {
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;
            
        case ctlSelectEvent:
            handleControlSelect(event);
            break;
        
        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled = true;
            break;     
            
        case lstSelectEvent:
            handleListItemSelect(event.data.lstSelect.listID, event.data.lstSelect.selection);
            handled = true;
            break;

        case MoriartyApplication::appSelectWeatherEvent:
            handleSelectItemEvent(event);
            handled = true;
            break;
            
        case popSelectEvent:
            assert(weatherPopupTrigger==event.data.popSelect.controlID);
            sendEvent(MoriartyApplication::appSelectWeatherEvent, MoriartyApplication::SelectItemEventData(event.data.popSelect.selection));
            handled = true;
            break;

        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

void WeatherMainForm::handleListItemSelect(UInt16 listId, UInt16 itemId)
{
     sendEvent(MoriartyApplication::appSelectWeatherEvent, MoriartyApplication::SelectItemEventData(itemId));
}

void WeatherMainForm::handleSelectItemEvent(const EventType& event)
{
    const MoriartyApplication::SelectItemEventData& data=reinterpret_cast<const MoriartyApplication::SelectItemEventData&>(event.data);
    currentWeatherNumber_ = data.item;
    prepareWeatherInfo(data.item);
    setDisplayMode(weatherDailyView);
    update();
}

bool WeatherMainForm::handleKeyPress(const EventType& event)
{
    bool onTreo = application().runningOnTreo600();
    if (weatherDailyView == displayMode() && !onTreo)
    {
        if (fiveWayLeftPressed(&event))
        {
            goToPrevDay();
            return true;
        }
        else if (fiveWayRightPressed(&event))
        {
            goToNextDay();            
            return true;
        }
    }

    if (weatherSummaryView == displayMode())    
    {
        int option = List::optionScrollPagesWithLeftRight;
        if (onTreo)
            option = 0;
        if (weatherList_.handleKeyDownEvent(event, option | List::optionFireListSelectOnCenter))
            return true;
    }
    return false;
}

bool WeatherMainForm::handleMenuCommand(UInt16 itemId)
{
    bool    handled = false;

    switch (itemId)
    {
        case changeLocationMenuItem:
            Application::popupForm(changeLocationForm);
            sendEvent(MoriartyApplication::appSetWeatherEvent);
            handled = true;
            break;

        case viewTableMenuItem:
            weatherSummaryButton_.hit();            
            handled = true;
            break;
            
        case viewOneDayMenuItem:
            if (!weatherData_)
            {
                handled = true;
                break;
            }
            //disallow when no data available
            if (weatherData_->empty())
            {
                handled = true;
                break;
            }
            if (noListSelection != weatherList_.selection())
                currentWeatherNumber_ = weatherList_.selection();
            prepareWeatherInfo(currentWeatherNumber_);
            setDisplayMode(weatherDailyView);
            update();
            handled = true;
            break;
            
        case refreshDataMenuItem:
            MoriartyApplication& app=application();
            if (!app.preferences().weatherPreferences.weatherLocation.empty())
                sendEvent(MoriartyApplication::appFetchWeatherEvent);
            handled = true;
            break;

        case mainPageMenuItem:
            weatherDoneButton_.hit();
            handled = true;
            break;
            
        case celsiusMenuItem:
            application().preferences().weatherPreferences.fDegreesModeCelsius = true;
            if (celsiusMode != degreesMode_)
            {
                degreesMode_ = celsiusMode;
                if (weatherDailyView == displayMode_)
                    prepareWeatherInfo(currentWeatherNumber_);
                update();
            }
            handled = true;
            break;    

        case fahrenheitMenuItem:
            application().preferences().weatherPreferences.fDegreesModeCelsius = false;
            if (fahrenheitMode != degreesMode_)
            {
                degreesMode_ = fahrenheitMode;
                if (weatherDailyView == displayMode_)
                    prepareWeatherInfo(currentWeatherNumber_);
                update();
            }
            handled = true;
            break;

        default:
            handled = MoriartyForm::handleMenuCommand(itemId);
    }
    return handled;
}

void WeatherMainForm::setDisplayMode(DisplayMode displayMode)
{
    displayMode_ = displayMode;
    showControls(true);
    switch (displayMode)
    {
        case weatherDailyView:
            prepareWeatherInfo(currentWeatherNumber_);
            if (NULL == weatherPopupListDrawHandler_.get())
            {
                weatherPopupListDrawHandler_.reset(new WeatherPopupListDrawHandler(weatherData_));
                weatherPopupList_.setCustomDrawHandler(weatherPopupListDrawHandler_.get());
            }
            else
                weatherPopupList_.updateItemsCount(*weatherPopupListDrawHandler_);
            weatherRenderer_.show();
            weatherSummaryButton_.focus();
            break;

        case weatherSummaryView:
            weatherRenderer_.hide();
            if (NULL == weatherListDrawHandler_.get())
            {
                weatherListDrawHandler_.reset(new WeatherListDrawHandler(weatherData_, degreesMode_));
                weatherList_.setCustomDrawHandler(weatherListDrawHandler_.get());
            }
            weatherList_.focus();
            break;

        default:
            assert(false);
    }            
}

bool WeatherMainForm::handleClose() 
{
    weatherPopupTrigger_.setLabel("");
    return MoriartyForm::handleClose();
}

void WeatherMainForm::afterGadgetDraw()
{
    redrawSkyBitmap();
}

