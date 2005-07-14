#include <FormObject.hpp>
#include "MoriartyApplication.hpp"
#include "M411EnterCityForm.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>
#include <USStates.hpp>

void M411EnterCityForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-78, screenBounds.width()-4, 76);
    setBounds(rect);
    update();
}

void M411EnterCityForm::attachControls()
{
    MoriartyForm::attachControls();
    cityField_.attach(cityField);
    stateField_.attach(stateField);
}

void M411EnterCityForm::handleControlSelect(const EventType& event)
{
    if (stateField==event.data.ctlSelect.controlID)
    {
        MoriartyApplication& app=application();
        app.popupForm(selectStateForm);
        return;
    }

    if (okButton==event.data.ctlSelect.controlID)
    {
        const char* text = cityField_.text();
        if (NULL!=text && !stateSymbol_.empty())
        {
            String newCity = text;
            strip(newCity);
            if (newCity.empty())
            {
                MoriartyApplication::alert(enterCityAlert);
                return;            
            }
            LookupManager* lookupManager = application().lookupManager;
            assert(NULL!=lookupManager);
            switch(whenOk_)
            {
                case areaByCity:
                    lookupManager->fetchAreaByCity(newCity, stateSymbol_);
                    break;
                case zipByCity:
                    lookupManager->fetchZipByCity(newCity, stateSymbol_);
                    break;
            }
        }
        else
        {
            if (NULL==text)
            {
                MoriartyApplication::alert(enterCityAlert);
                return;            
            }
            if (stateSymbol_.empty())
            {
                MoriartyApplication::alert(selectStateAlert);
                return;            
            }
        }
    }
    closePopup();
}

bool M411EnterCityForm::handleEvent(EventType& event)
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
    
        case MoriartyApplication::app411SetAreaByCityEvent:
            whenOk_ = areaByCity;
            setTitle(_T("Area code by city"));
            handled = true;
            break;    

        case MoriartyApplication::app411SetZipByCityEvent:
            whenOk_ = zipByCity;
            setTitle(_T("Zip code by city"));
            handled = true;
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

M411EnterCityForm::~M411EnterCityForm()
{}
