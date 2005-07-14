#include <Text.hpp>
#include <SysUtils.hpp>
#include <FormObject.hpp>

#include "LookupManager.hpp"
#include "MoriartyApplication.hpp"
#include "M411EnterAreaForm.hpp"

using ArsLexis::String;

void M411EnterAreaForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-78, screenBounds.width()-4, 76);
    setBounds(rect);
    locationField_.bounds(rect);
    rect.width()=screenBounds.width()-12;
    locationField_.setBounds(rect);
    update();
}

void M411EnterAreaForm::attachControls()
{
    MoriartyForm::attachControls();
    locationField_.attach(locationField);
}

/**
 * check area code 
 * (remove all non digits, if then it matches XXX,
 *   then return true)
 */
static bool parseLocation(String& location)
{
    String newLocation;
    removeNonDigits(location, newLocation);
    if (newLocation.length() != 3)
        return false;
    location.assign(newLocation);    
    return true;
}

void M411EnterAreaForm::handleControlSelect(const EventType& event)
{
    if (okButton==event.data.ctlSelect.controlID)
    {
        const char* text=locationField_.text();
        if (NULL!=text)
        {
            String newLocation=text;
            if (parseLocation(newLocation))
            {
                LookupManager* lookupManager=application().lookupManager;
                assert(NULL!=lookupManager);
                lookupManager->fetchReverseArea(newLocation);
            }
            else
            {
                MoriartyApplication::alert(areaCodeNotAcceptedAlert);
                return;            
            }
        }
    }
    closePopup();
}

bool M411EnterAreaForm::handleEvent(EventType& event)
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
    
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

M411EnterAreaForm::~M411EnterAreaForm()
{}
