#include <FormObject.hpp>
#include "MoriartyApplication.hpp"
#include "M411EnterBusinessForm.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>
#include <USStates.hpp>

void M411EnterBusinessForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-98, screenBounds.width()-4, 96);
    setBounds(rect);
    update();
}

void M411EnterBusinessForm::attachControls()
{
    MoriartyForm::attachControls();
    nameField_.attach(nameField);
    cityOrZipField_.attach(cityOrZipField);
    stateField_.attach(stateField);
    categoryCheckBox_.attach(categoryCheckBox);
}

void M411EnterBusinessForm::handleControlSelect(const EventType& event)
{
    if (stateField==event.data.ctlSelect.controlID)
    {
        MoriartyApplication& app=application();
        app.popupForm(selectStateForm);
        return;
    }

    if(categoryCheckBox==event.data.ctlSelect.controlID)
        return;

    if (okButton==event.data.ctlSelect.controlID)
    {
        const char* name = nameField_.text();
        const char* cityOrZip = cityOrZipField_.text();
        if (NULL != name && !stateSymbol_.empty())
        {
            String nameS = name;
            strip(nameS);
            if (nameS.empty())
            {
                MoriartyApplication::alert(enterNameAlert);
                return;            
            }            
            String cityOrZipS;
            if (NULL != cityOrZip)
                cityOrZipS = cityOrZip;
            LookupManager* lookupManager = application().lookupManager;
            assert(NULL != lookupManager);
            lookupManager->fetchBusinessData(nameS, cityOrZipS, stateSymbol_, false, !categoryCheckBox_.value());
        }
        else
        {
            if (NULL == name)
                MoriartyApplication::alert(enterNameAlert);
            else if (stateSymbol_.empty())
                MoriartyApplication::alert(selectStateAlert);
            return;            
        }
    }
    closePopup();
}

bool M411EnterBusinessForm::handleEvent(EventType& event)
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

M411EnterBusinessForm::~M411EnterBusinessForm()
{}
