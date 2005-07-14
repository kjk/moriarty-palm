#include <FormObject.hpp>
#include "MoriartyApplication.hpp"
#include "NetflixEnterLoginForm.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>

#define assignedText _T("-ASSIGNED-")
using ArsLexis::String;

NetflixEnterLoginForm::NetflixEnterLoginForm(MoriartyApplication& app):
    MoriartyForm(app, netflixEnterLoginForm, true),
    loginField_(*this),
    passwordField_(*this)
{
    setFocusControlId(loginField);
}    

void NetflixEnterLoginForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-91, screenBounds.width()-4, 89);
    setBounds(rect);
    update();
}

void NetflixEnterLoginForm::attachControls()
{
    MoriartyForm::attachControls();
    loginField_.attach(loginField);
    passwordField_.attach(passwordField);
}

bool NetflixEnterLoginForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    Preferences::NetflixPreferences* prefs = &application().preferences().netflixPreferences;
    if (!prefs->login.empty())
        loginField_.setEditableText(prefs->login);
    if (!prefs->password.empty())
        passwordField_.setEditableText(assignedText);
    return result;
}


void NetflixEnterLoginForm::handleControlSelect(const EventType& event)
{
    if (okButton==event.data.ctlSelect.controlID)
    {
        const char* text = loginField_.text();
        const char* pwd = passwordField_.text();
        if (NULL != text && NULL != pwd)
        {
            if (StrEmpty(text) || StrEmpty(pwd))
            {
                MoriartyApplication::alert(noLoginaOrPasswordAlert);
                return;            
            }
            Preferences::NetflixPreferences* prefs = &application().preferences().netflixPreferences;
            prefs->forgetCredentials();
            prefs->login.assign(text);
            if (prefs->password.empty() || tstrcmp(pwd, assignedText) != 0)
                prefs->password.assign(pwd);
            status_t err = prefs->sendLoginAndPasswordToServer();
            if (errNone != err)
                MoriartyApplication::alert(notEnoughMemoryAlert);
        }
    }
    closePopup();
}

bool NetflixEnterLoginForm::handleEvent(EventType& event)
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
        
        case fldEnterEvent: //no break
            if (passwordField == event.data.fldEnter.fieldID)
            {
                const char_t* pwd = passwordField_.text();
                if (NULL != pwd)
                {
                    if (0 == tstrcmp(pwd, assignedText))
                        passwordField_.erase();                
                }
            }        
    
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

NetflixEnterLoginForm::~NetflixEnterLoginForm()
{}
