#include <Text.hpp>
#include <SysUtils.hpp>
#include <FormObject.hpp>

#include "LookupManager.hpp"
#include "MoriartyApplication.hpp"
#include "M411EnterPhoneForm.hpp"

using ArsLexis::String;

void M411EnterPhoneForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-78, screenBounds.width()-4, 76);
    setBounds(rect);
    phoneField_.bounds(rect);
    rect.width()=screenBounds.width()-12;
    phoneField_.setBounds(rect);
    update();
}

void M411EnterPhoneForm::attachControls()
{
    MoriartyForm::attachControls();
    phoneField_.attach(phoneField);
}

/**
 * check phone
 * (remove all non digits, if then it matches xxxyyyzzzz,
 *   then return true)
 */
static bool parsePhone(String& phone)
{
    String newPhone;
    removeNonDigits(phone, newPhone);
    if (newPhone.length() != 10)
        return false;
    phone.assign(newPhone);    
    return true;
}

void M411EnterPhoneForm::handleControlSelect(const EventType& event)
{
    if (okButton==event.data.ctlSelect.controlID)
    {
        const char* text=phoneField_.text();
        if (NULL!=text)
        {
            String newPhone=text;
            if (parsePhone(newPhone))
            {
                LookupManager* lookupManager=application().lookupManager;
                assert(NULL!=lookupManager);
                lookupManager->fetchReversePhone(newPhone);
            }
            else
            {
                MoriartyApplication::alert(phoneNotAcceptedAlert);
                return;            
            }
        }
    }
    closePopup();
}

bool M411EnterPhoneForm::handleEvent(EventType& event)
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

M411EnterPhoneForm::~M411EnterPhoneForm()
{}
