
#include "SelectLocationForm.hpp"
#include "MoriartyPreferences.hpp"
#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"
#include <SysUtils.hpp>

class LocationsListDrawHandler: public ExtendedList::CustomDrawHandler {
    LookupManager::Locations_t* locations_;
    UniversalDataFormat* udf_;

public: 
        
    enum Mode
    {
        locationMode,
        firstFromUDFMode
    };
    
private:

    Mode mode_;
    
public:

    LocationsListDrawHandler(LookupManager::Locations_t* locations):
        locations_(locations), mode_(locationMode)
    {}

    LocationsListDrawHandler(UniversalDataFormat* udf):
        udf_(udf), mode_(firstFromUDFMode)
    {}
    
    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
    {
        uint_t width=itemBounds.width();
        String text;
        switch (mode_)
        {
            case locationMode:
                assert(item<locations_->size());
                text.assign((*locations_)[item]);
                break;
            case firstFromUDFMode:
                assert(item<udf_->getItemsCount());
                text.assign(udf_->getItemText(item,0));
                break;
        }
        uint_t length=text.length();
        graphics.charsInWidth(text.c_str(), length, width);
        graphics.drawText(text.c_str(), length, itemBounds.topLeft);
    }
    
    uint_t itemsCount() const
    {
        switch (mode_)
        {
            case locationMode:
                return locations_->size();
            case firstFromUDFMode:
                return udf_->getItemsCount();
        }
        return 0;
    }
    
    ~LocationsListDrawHandler()
    {}
    
};

SelectLocationForm::SelectLocationForm(MoriartyApplication& app):
    MoriartyForm(app, selectLocationForm),
    locationsList_(*this),
    okButton_(*this),
    cancelButton_(*this),
    okMode_(moviesMode)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL!=lm);
    if(!lm->locations.empty())
        locationsListDrawHandler_.reset(new LocationsListDrawHandler(&(lm->locations)));
    else if (!lm->tempUDF.empty())
        locationsListDrawHandler_.reset(new LocationsListDrawHandler(&(lm->tempUDF)));
    setFocusControlId(locationsList);
}
    
SelectLocationForm::~SelectLocationForm()
{}

void SelectLocationForm::attachControls()
{
    MoriartyForm::attachControls();
    locationsList_.attach(locationsList);
    
    locationsList_.setUpBitmapId(upBitmap);
    locationsList_.setDownBitmapId(downBitmap);
    locationsList_.setItemHeight(12);
    
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
}

bool SelectLocationForm::handleOpen()
{
    bool res=MoriartyForm::handleOpen();
    assert(NULL != locationsListDrawHandler_.get());
    locationsList_.setCustomDrawHandler(locationsListDrawHandler_.get());
    if (0 != locationsList_.itemsCount())
        locationsList_.setSelection(0);
    return res;
}

void SelectLocationForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(screenBounds);
    bounds.explode(2, 2, -4, -4);        
    setBounds(bounds);
    
    ArsRectangle objBounds(0, 52, screenBounds.width()-4, screenBounds.height()-74);
    locationsList_.setBounds(objBounds);
    locationsList_.adjustVisibleItems();

    okButton_.bounds(bounds);
    bounds.y()=screenBounds.height()-18;
    okButton_.setBounds(bounds);

    cancelButton_.bounds(bounds);
    bounds.y()=screenBounds.height()-18;
    cancelButton_.setBounds(bounds);
    update();
}

bool SelectLocationForm::handleEvent(EventType& event)
{
    bool handled=false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelected(event);
            handled=true;
            break;
            
        case lstSelectEvent:
            assert(locationsList==event.data.lstSelect.listID);
            okButton_.hit();
            handled=true;
            break;
        
        // for 411
        case MoriartyApplication::app411SetAreaByCityEvent:
            okMode_ = areaByCityMode;
            handled = true;
            break;    

        // for 411
        case MoriartyApplication::app411SetZipByCityEvent:
            okMode_ = zipByCityMode;
            handled = true;
            break;    
            
        // for 411
        case MoriartyApplication::app411SetPersonSearchEvent:
            okMode_ = personSearchMode;
            handled = true;
            break;    

        // weather multiselect
        case MoriartyApplication::appSetWeatherEvent:
            okMode_ = weatherMultiselectMode;
            LookupManager* lm=application().lookupManager;
            locationsListDrawHandler_.reset(new LocationsListDrawHandler(&(lm->tempUDF)));
            locationsList_.setCustomDrawHandler(locationsListDrawHandler_.get());
            locationsList_.adjustVisibleItems();
            if (0 != locationsList_.itemsCount())
                locationsList_.setSelection(0);
            update();
            handled = true;
            break;    
            
        case keyDownEvent:  {
            int option = ExtendedList::optionScrollPagesWithLeftRight;
            if (application().runningOnTreo600())
                option = 0;
            if (locationsList_.handleKeyDownEvent(event, option | ExtendedList::optionFireListSelectOnCenter))
                return true;
        }
        // watch out for fall through here!

        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

void SelectLocationForm::handleControlSelected(const EventType& event)
{
    bool pretendCancelPressed = false;

    if (okButton == event.data.ctlSelect.controlID) 
    {
        int sel = locationsList_.selection();
        if (noListSelection == sel)
        {
            pretendCancelPressed = true;
        }
        else
        {
            closePopup();
            MoriartyApplication& app = application();
            LookupManager* lm = app.lookupManager;
            assert (NULL!=lm);
            switch (okMode_)
            {
                case moviesMode:
                    assert(sel < lm->locations.size());
                    lm->fetchMovies(lm->locations[sel].c_str());
                    break;
                case areaByCityMode:
                    assert(sel < lm->locations.size());
                    lm->fetchAreaByCity(lm->locations[sel]);
                    break;
                case zipByCityMode:
                    assert(sel < lm->locations.size());
                    lm->fetchZipByCity(lm->locations[sel]);
                    break;
                case personSearchMode:
                    assert(sel < lm->locations.size());
                    lm->fetchPersonData(lm->locations[sel]);
                    break;
                case weatherMultiselectMode:
                    assert(sel < lm->tempUDF.getItemsCount());
                    lm->fetchWeather(lm->tempUDF.getItemText(sel,0), lm->tempUDF.getItemText(sel,1));
                    break;
            }
        }
    }

    if (cancelButton == event.data.ctlSelect.controlID || pretendCancelPressed)
    {
        closePopup();
        Preferences& prefs = application().preferences();
        switch (okMode_)
        {
            case moviesMode:
                if (prefs.moviesLocation.empty())
                    application().runMainForm();
                break;
            case weatherMultiselectMode:
                if (prefs.weatherPreferences.weatherLocationToServer.empty())
                    application().runMainForm();
                break;
        }
    }
}
