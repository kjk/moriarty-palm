#include <FormObject.hpp>
#include "MoriartyApplication.hpp"
#include "M411EnterZipForm.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>

using ArsLexis::String;

void M411EnterZipForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-78, screenBounds.width()-4, 76);
    setBounds(rect);
    locationField_.bounds(rect);
    rect.width()=screenBounds.width()-12;
    locationField_.setBounds(rect);
    update();
}

void M411EnterZipForm::attachControls()
{
    MoriartyForm::attachControls();
    locationField_.attach(locationField);
}

/**
 * check zip code 
 * (remove all non digits, if then it matches XXXXX,
 *   then return true)
 */
static bool parseLocation(String& location)
{
    String newLocation;
    removeNonDigits(location, newLocation);
    if (newLocation.length() != 5)
        return false;
    location.assign(newLocation);    
    return true;
}

void M411EnterZipForm::handleControlSelect(const EventType& event)
{
    if (okButton==event.data.ctlSelect.controlID)
    {
        const char* text = locationField_.text();
        if (NULL!=text)
        {
            String newLocation=text;
            if (parseLocation(newLocation))
            {
                LookupManager* lookupManager = application().lookupManager;
                assert(NULL!=lookupManager);
                switch (formMode_)
                {
                    case m411zipMode:
                        lookupManager->fetchReverseZip(newLocation);
                        break;
                    case gasPricesMode:
                        lookupManager->fetchField(getGasPricesField, newLocation.c_str());
                        break;
                }
            }
            else
            {
                MoriartyApplication::alert(zipCodeNotAcceptedAlert);
                return;            
            }
        }
    }
    closePopup();
    if (cancelButton==event.data.ctlSelect.controlID)
    {
        switch (formMode_)
        {
            case m411zipMode:
                break;
            case gasPricesMode:
            {
                Preferences& prefs = application().preferences();
                if (prefs.gasPricesPreferences.zipCode.empty())
                    application().runMainForm();
                break;
            }    
        }
    }
}

bool M411EnterZipForm::handleEvent(EventType& event)
{
    bool handled = false;
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
    
        case MoriartyApplication::appSetGasPriceEvent:
            formMode_ = gasPricesMode;
            Preferences& prefs = application().preferences();
            const String& location = prefs.gasPricesPreferences.zipCode;
            if (!location.empty())
            {
                locationField_.setEditableText(location);
                locationField_.select();
            }
            else
            {
                locationField_.setEditableText(_T(""));
            }
            setTitle(_T("Gas prices"));
            handled = true;
            break;
    
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

M411EnterZipForm::~M411EnterZipForm()
{}
