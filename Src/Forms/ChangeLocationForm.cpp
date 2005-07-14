#include <SysUtils.hpp>
#include <Text.hpp>
#include <FormObject.hpp>

#include "LookupManager.hpp"
#include "MoriartyPreferences.hpp"
#include "MoriartyApplication.hpp"

#include "ChangeLocationForm.hpp"

void ChangeLocationForm::attachControls()
{
    MoriartyForm::attachControls();
    locationField_.attach(locationField);
}

void ChangeLocationForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-78, screenBounds.width()-4, 76);
    setBounds(rect);
    
    locationField_.anchor(screenBounds, anchorRightEdge, 12, anchorNot, 0);
    
    FormObject gsi(*this);
    gsi.attachByIndex(getGraffitiStateIndex());
    gsi.anchor(screenBounds, anchorLeftEdge, 16, anchorNot, 0);
    
    update();
}

bool ChangeLocationForm::handleOpen()
{
    bool handled=MoriartyForm::handleOpen();

    Preferences& prefs=application().preferences();

    // TODO: this should be factored out to Field class as Field.setTextCopy(String txt)
    // TODO: what happens if string is longer than max number allowed by text field?
    //       Should we guard against that?
    if (!prefs.moviesLocation.empty())
    {
        locationField_.setEditableText(prefs.moviesLocation);
        locationField_.select();        
    }
    locationField_.focus();
    return handled;
}

bool ChangeLocationForm::handleWindowEnter(const struct _WinEnterEventType& event)
{
    const FormType* form=*this;
    if (static_cast<const void*>(form) == event.enterWindow)
        locationField_.focus();
    return MoriartyForm::handleWindowEnter(event);    
}

void ChangeLocationForm::handleControlSelect(const EventType& event)
{
    bool pretendCancelPressed = true;
    char_t * newLocation = NULL;

    if (okButton == event.data.ctlSelect.controlID)
    {
        newLocation = locationField_.textCopy();
        if (NULL == newLocation)
            goto ClosePopup;

        StrStrip(newLocation);
        if (StrEmpty(newLocation))
            goto ClosePopup;

        LookupManager* lookupManager = application().lookupManager;
        Preferences& prefs = application().preferences();
        switch (whenOk_)
        {
            case moviesMode:
            {
                const String& curLocation = prefs.moviesLocation;
                // TODO: now that there's a chance, that the text we use is
                //   different than the string user gave, maybe it's a good idea
                //   to popup a confirmation dialog box with "Get movies for location $FOO"
                //   and "OK", "Cancel" so that the user has a chance to preview
                //   location he gave. Changing locations shouldn't be frequent so
                //   we can annoy users like that.
                //   "Cancel" would get us back to entering location form

                // change only if different than previous
                if (!equalsIgnoreCase(newLocation, curLocation))
                    lookupManager->fetchMovies(newLocation);
                break;
            }
            case weatherMode:
            {
                const String& curLocation = prefs.weatherPreferences.weatherLocation;
                // change only if different than previous
                if (!equalsIgnoreCase(curLocation, newLocation))
                    lookupManager->fetchWeather(newLocation, newLocation);
                break;
            }    
        }
        pretendCancelPressed = false;
    }

ClosePopup:
    if( NULL != newLocation)
        free(newLocation);
    closePopup();

    if (cancelButton == event.data.ctlSelect.controlID || pretendCancelPressed)
    {
        Preferences& prefs = application().preferences();
        switch (whenOk_)
        {
            case moviesMode:
                if (prefs.moviesLocation.empty())
                    application().runMainForm();
                break;
            case weatherMode:
                if (prefs.weatherPreferences.weatherLocationToServer.empty())
                    application().runMainForm();
                break;
        }
    }
}

bool ChangeLocationForm::handleEvent(EventType& event)
{
    bool handled=false;
    switch (event.eType)
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled=true;
            break;
            
        case keyDownEvent:
            if (chrCarriageReturn==event.data.keyDown.chr || chrLineFeed==event.data.keyDown.chr)
            {
                Control control(*this, okButton);
                control.hit();
            }
            break;
            
        case MoriartyApplication::appSetWeatherEvent:
            //change form to be weatherSelectLocationForm
            whenOk_ = weatherMode;            
            Preferences& prefs=application().preferences();
            const String& location = prefs.weatherPreferences.weatherLocation;
            if (!prefs.weatherPreferences.weatherLocation.empty())
            {
                locationField_.setEditableText(prefs.weatherPreferences.weatherLocation);
                locationField_.select();
            }
            else
            {
                locationField_.setEditableText(_T(""));
            }
            handled = true;
            break;
    
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

ChangeLocationForm::~ChangeLocationForm()
{}
