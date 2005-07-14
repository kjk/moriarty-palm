#include <SysUtils.hpp>
#include <Text.hpp>
#include <DynStr.hpp>
#include <USStates.hpp>

#include <FormObject.hpp>

#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"
#include "AmazonEnterWishlistForm.hpp"

void AmazonEnterWishlistForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-98, screenBounds.width()-4, 96);
    setBounds(rect);
    update();
}

void AmazonEnterWishlistForm::attachControls()
{
    MoriartyForm::attachControls();
    nameField_.attach(nameField);
    emailField_.attach(emailField);
    cityField_.attach(cityField);
    stateField_.attach(stateField);
}

void AmazonEnterWishlistForm::handleControlSelect(const EventType& event)
{
    DynStr * request = NULL;

    if (stateField==event.data.ctlSelect.controlID)
    {
        MoriartyApplication& app=application();
        app.popupForm(selectStateForm);
        return;
    }

    if (okButton==event.data.ctlSelect.controlID)
    {
        const char* name = nameField_.text();
        const char* email = emailField_.text();
        const char* city = cityField_.text();

        if (StrEmpty(email) && StrEmpty(name))
        {
            MoriartyApplication::alert(enterNameOrEmailAlert);
            return;
        }

        request = DynStrFromCharP(_T("s+amazonwishlist:"), 48);
        if (NULL == request)
            goto Exit;
        if (NULL != name)
        {
            if (NULL == DynStrAppendCharP(request, name))
                goto Exit;
        }
        if (NULL == DynStrAppendChar(request, _T(';')))
            goto Exit;

        if (NULL != email)
        {
            if (NULL == DynStrAppendCharP(request, email))
                goto Exit;
        }
        if (NULL == DynStrAppendChar(request, _T(';')))
            goto Exit;

        if (NULL != city)
        {
            if (NULL == DynStrAppendCharP(request, city))
                goto Exit;
        }
        if (NULL == DynStrAppendChar(request, _T(';')))
            goto Exit;

        if (NULL != stateSymbol_)
        {
            if (NULL == DynStrAppendCharP(request, stateSymbol_))
                goto Exit;
        }
        if (NULL == DynStrAppendCharP(request, _T(";1")))
            goto Exit;
            
        LookupManager* lookupManager = application().lookupManager;
        assert(NULL!=lookupManager);
        lookupManager->fetchUrl(DynStrGetCStr(request));
    }
Exit:
    if (NULL != request)
        DynStrDelete(request);
    closePopup();
}

bool AmazonEnterWishlistForm::handleEvent(EventType& event)
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
                stateSymbol_ = getStateSymbol(sel);
                stateField_.setLabel(stateSymbol_);
            }
            handled = true;
            break;
            
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

AmazonEnterWishlistForm::~AmazonEnterWishlistForm()
{}
