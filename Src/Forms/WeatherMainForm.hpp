#ifndef __WEATHER_MAINFORM_HPP__
#define __WEATHER_MAINFORM_HPP__

#include <Graphics.hpp>
#include "MoriartyApplication.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <HmStyleList.hpp>
#include <UniversalDataFormat.hpp>
#include <TextRenderer.hpp>

class LookupManager;

class WeatherMainForm: public MoriartyForm
{
    UniversalDataFormat* weatherData_;
    size_t currentWeatherNumber_;

    typedef std::auto_ptr<List::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr weatherPopupListDrawHandler_;
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ExtendedListDrawHandlerPtr;
    ExtendedListDrawHandlerPtr weatherListDrawHandler_;

    bool ignoreNextPenUp_;

    Control weatherDoneButton_;
    Control weatherSummaryButton_;
    Control updateButton_;

    Control nextDayButton_;
    Control prevDayButton_;

    HmStyleList weatherList_;
    Control weatherPopupTrigger_;
    List weatherPopupList_;
    ArsLexis::String weatherPopupTriggerText_;

    TextRenderer weatherRenderer_;
    
    void handleControlSelect(const EventType& data);

    bool handleKeyPress(const EventType& event);

    uint_t getBitmapIdFromSky(const ArsLexis::String& sky);

    void drawSkyBitmap(Graphics& graphics, const ArsRectangle& bounds);
    
    void redrawSkyBitmap();

    void goToNextDay();

    void goToPrevDay();

    void enableControls(bool enable);

    void showControls(bool show);

    void handleLookupFinished(const EventType& event);

    void updateAfterLookup(LookupManager& lookupManager);

    void prepareWeatherInfo(uint_t weather);

    void handleSelectItemEvent(const EventType& event);

    void handleListItemSelect(UInt16 listId, UInt16 itemId);

    void updateTitle();

protected:

    void attachControls();

    bool handleOpen();

    void resize(const ArsRectangle& screenBounds);

    bool handleEvent(EventType& event);

    bool handleMenuCommand(UInt16 itemId);

    bool handleClose();
    
    void afterGadgetDraw();

public:

    WeatherMainForm(MoriartyApplication& app);

    ~WeatherMainForm();

    enum DisplayMode
    {
        weatherSummaryView,
        weatherDailyView
    };

    DisplayMode displayMode() const
    {return displayMode_;}

    void setDisplayMode(DisplayMode displayMode);

    enum DegreesMode
    {
        fahrenheitMode,
        celsiusMode
    };

    DegreesMode degreesMode() const
    {return degreesMode_;}
    
private:

    DisplayMode displayMode_;
    DegreesMode degreesMode_;
};

#endif
