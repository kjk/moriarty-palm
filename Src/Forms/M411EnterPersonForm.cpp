#include <FormObject.hpp>
#include "MoriartyApplication.hpp"
#include "M411EnterPersonForm.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>
#include <USStates.hpp>

void M411EnterPersonForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-98, screenBounds.width()-4, 96);
    setBounds(rect);
    update();
}

void M411EnterPersonForm::attachControls()
{
    MoriartyForm::attachControls();
    firstNameField_.attach(firstNameField);
    lastNameField_.attach(lastNameField);
    cityOrZipField_.attach(cityOrZipField);
    stateField_.attach(stateField);
}

void M411EnterPersonForm::handleControlSelect(const EventType& event)
{
    if (stateField==event.data.ctlSelect.controlID)
    {
        MoriartyApplication& app=application();
        app.popupForm(selectStateForm);
        return;
    }

    if (okButton==event.data.ctlSelect.controlID)
    {
        const char* firstName = firstNameField_.text();
        const char* lastName = lastNameField_.text();
        const char* cityOrZip = cityOrZipField_.text();
        if (NULL != lastName)
        {
            String lastNameS = lastName;
            strip(lastNameS);
            if (lastNameS.empty())
            {
                MoriartyApplication::alert(enterLastNameAlert);
                return;
            }
            String cityOrZipS;
            String firstNameS;
            if (NULL != cityOrZip)
                cityOrZipS = cityOrZip;
            if (NULL != firstName)
                firstNameS = firstName;
            LookupManager* lookupManager = application().lookupManager;
            assert(NULL!=lookupManager);
            lookupManager->fetchPersonData(firstNameS, lastNameS, cityOrZipS, stateSymbol_);
        }
        else
        {
            MoriartyApplication::alert(enterLastNameAlert);
            return;            
        }
    }
    closePopup();
}

bool M411EnterPersonForm::handleEvent(EventType& event)
{
    bool handled=false;
    String title;
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
    
        case MoriartyApplication::appStateWasSelectedEvent:
            LookupManager* lookupManager = application().lookupManager;
            assert(NULL!=lookupManager);
            int sel = lookupManager->getSelectedState();
            if (sel >= 0 && sel < getStatesCount())
            {
                stateSymbol_.assign(getStateSymbol(sel));
                stateField_.setLabel(getStateSymbol(sel));
            }
            handled = true;
            break;
            
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

M411EnterPersonForm::~M411EnterPersonForm()
{}
