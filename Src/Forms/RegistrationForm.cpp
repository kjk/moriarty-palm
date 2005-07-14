#include <Text.hpp>
#include <SysUtils.hpp>
#include <FormObject.hpp>

#include "LookupManager.hpp"
#include "MoriartyPreferences.hpp"
#include "MoriartyApplication.hpp"

#include "RegistrationForm.hpp"

#include "flickr.hpp"

void RegistrationForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-66, screenBounds.width()-4, 64);
    setBounds(rect);
    
    FormObject object(*this, regCodeFormField);
    object.bounds(rect);
    rect.width()=screenBounds.width()-12;
    object.setBounds(rect);
    
    object.attachByIndex(getGraffitiStateIndex());
    object.anchor(screenBounds, anchorLeftEdge, 16, anchorNot, 0);
    
    update();
}

void RegistrationForm::attachControls()
{
    MoriartyForm::attachControls();
}

bool RegistrationForm::handleOpen()
{
    bool handled=MoriartyForm::handleOpen();
    Field field(*this, regCodeFormField);

    Preferences& prefs=application().preferences();
    MemHandle handle=MemHandleNew(Preferences::regCodeLength+1);
    if (!handle)
        return handled;
    char* text=static_cast<char*>(MemHandleLock(handle));
    if (text)
    {
        assert(prefs.regCode.length()<=Preferences::regCodeLength);
        StrNCopy(text, prefs.regCode.data(), prefs.regCode.length());
        text[prefs.regCode.length()] = chrNull;
        MemHandleUnlock(handle);
    }
    field.setText(handle);        
    return handled;
}

void RegistrationForm::handleControlSelect(const EventType& event)
{
    if (registerButton != event.data.ctlSelect.controlID)
    {
        assert(laterButton == event.data.ctlSelect.controlID);
        closePopup();
        return;
    }

    MoriartyApplication& app = static_cast<MoriartyApplication&>(application());

    // verify that reg code is correct using Verify-Registration-Code request
    Field field(*this, regCodeFormField);

    if (NULL != newRegCode_)
    {
        free(newRegCode_);
        newRegCode_ = NULL;
    }

    newRegCode_ = field.textCopy();
    if (StrEmpty(newRegCode_))
    {
        // don't even bother asking the server, it must be wrong
        return;
    }

    // get lookup manager, create if doesn't exist. We might not have lookupManager
    // at this point (if we didn't do any query before registration query)
    LookupManager* lookupManager = app.lookupManager;
    assert(lookupManager);
    if (NULL == lookupManager)
    {
        // shouldn't happen, but just in case
        return;
    }

    ::removeNonDigitsInPlace(newRegCode_);
    if (StrEmpty(newRegCode_))
        return;
    lookupManager->fetchField(verifyRegCodeField, newRegCode_);
}

void RegistrationForm::handleLookupFinished(const EventType& event)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    Preferences& prefs=app.preferences();

    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    if (lookupResultRegCodeValid == data.result)
    {
        assert(!StrEmpty(newRegCode_));
        // TODO: assert that it consists of numbers only
        if (0 != tstrcmp(newRegCode_, prefs.regCode.c_str()))
        {
            assert(tstrlen(newRegCode_) <= prefs.regCodeLength);
            prefs.regCode = newRegCode_;
            app.savePreferences();
        }
#if FLICKR_ENABLED
        FlickrSynchronizeRegistrationStatus();
#endif            
        FrmAlert(alertRegistrationOk);
        closePopup();
        sendEvent(MoriartyApplication::appRegistrationFinished);
    }
    else if (lookupResultRegCodeInvalid == data.result)
    {
        UInt16 buttonId = FrmAlert(alertRegistrationFailed);

        prefs.regCode.clear();
#if FLICKR_ENABLED
        FlickrSynchronizeRegistrationStatus();
#endif            
        if (0 == buttonId)
        {
            // this is "Ok" button. Clear-out registration code (since it was invalid)
            app.savePreferences();
            closePopup();
            return;
        }
        // this must be "Re-enter registration code" button
        assert(1 == buttonId);
        Field field(*this, regCodeFormField);
        field.select();        
        field.focus();
    }
    else
    {
        assert((lookupResultServerError == data.result) || (lookupResultError == data.result) || (lookupResultConnectionCancelledByUser == data.result));
        // an alert will be shown for server errors
        update();
        prefs.regCode.clear();
#if FLICKR_ENABLED
        FlickrSynchronizeRegistrationStatus();
#endif            
        LookupManager* lookupManager = app.lookupManager;
        lookupManager->handleLookupFinishedInForm(data);
        closePopup();
    }
}

bool RegistrationForm::handleEvent(EventType& event)
{
    bool handled = false;
    switch (event.eType)
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled = true;
            break;
            
        case keyDownEvent:
            if (chrCarriageReturn==event.data.keyDown.chr || chrLineFeed==event.data.keyDown.chr)
            {
                Control control(*this, registerButton);
                control.hit();
            }
            break;

        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled = true;
            break;
            
/*            
    These events won't happen - ConnectionProgressForm intercepts them.
    
        case LookupManager::lookupStartedEvent:
            //TODO: disable controls during lookup
            //setControlsState(false);            // No break is intentional.
            
        case LookupManager::lookupProgressEvent:
            update(redrawProgressIndicator);
            break;
*/
    
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

RegistrationForm::~RegistrationForm()
{
    if (NULL != newRegCode_)
        free(newRegCode_);
}
