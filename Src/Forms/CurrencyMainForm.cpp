#include "CurrencyMainForm.hpp"
#include "SelectCurrencyForm.hpp"
#include "LookupManager.hpp"
#include <Currencies.hpp>
#include <SysUtils.hpp>
#include <algorithm>
#include <UniversalDataHandler.hpp>
#include <Text.hpp>
#include <Graphics.hpp>

CurrencyMainForm::~CurrencyMainForm()
{
}

CurrencyMainForm::CurrencyMainForm(MoriartyApplication& app):
    MoriartyForm(app, currencyMainForm),
    selCurrenciesList_(*this),
    doneButton_(*this),
    addButton_(*this),
    deleteButton_(*this),
    updateButton_(*this),
    amountField_(*this),
    amountLabel_(*this),
    graffitiState_(*this),
    rate_(1),
    amount_(1)
{
    selCurrenciesList_.setChangeSelectionNotification(true);
    setFocusControlId(amountField);
}

void CurrencyMainForm::attachControls()
{
    MoriartyForm::attachControls();
    selCurrenciesList_.attach(resultsList);
    doneButton_.attach(doneButton);
    updateButton_.attach(updateButton);
    addButton_.attach(addButton);
    deleteButton_.attach(deleteButton);
    amountField_.attach(amountField);
    amountLabel_.attach(amountLabel);
    graffitiState_.attachByIndex(getGraffitiStateIndex());
    
    selCurrenciesList_.setItemHeight(CurrencyListDrawHandler::currenciesListItemLines * CurrencyListDrawHandler::currenciesListLineHeight);
    selCurrenciesList_.setUpBitmapId(upBitmap);
    selCurrenciesList_.setDownBitmapId(downBitmap);

}

bool CurrencyMainForm::handleOpen()
{
    bool res=MoriartyForm::handleOpen();
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    Preferences::CurrencyPreferences& prefs = app.preferences().currencyPreferences;
    assert(NULL != lookupManager);

    this->currencyData_ = &lookupManager->currencyData;
    selCurrenciesListDrawHandler_.reset(new CurrencyListDrawHandler(*currencyData_, amount_ , rate_));
    selCurrenciesList_.setCustomDrawHandler(selCurrenciesListDrawHandler_.get());

    updateAmountField();

    if (!prefs.selectedCurrencies.empty())
    {
        uint_t currIndex = prefs.selectedCurrencies[0];
        rate_ = GetCurrencyRate(*currencyData_, currIndex);
        selCurrenciesList_.setSelection(0);
    }

    if (0 == currencyData_->getItemsCount())
        this->fetchCurrenciesList();

    amountField_.select();

    update();
    return res;
}

void CurrencyMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(screenBounds);

    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    updateButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    deleteButton_.anchor(screenBounds, anchorLeftEdge, 41, anchorTopEdge, 14);
    addButton_.anchor(screenBounds, anchorLeftEdge, 75, anchorTopEdge, 14);
    
    amountLabel_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 30);
    amountField_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 30);
    graffitiState_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 30);

    selCurrenciesList_.anchor(screenBounds, anchorRightEdge, 0, anchorBottomEdge, 52);

    selCurrenciesList_.adjustVisibleItems();
    update();
}

void CurrencyMainForm::handleControlSelect(const EventType& event)
{
    MoriartyApplication& app=application();
    Preferences::CurrencyPreferences& prefs = app.preferences().currencyPreferences;

    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;            

        case updateButton:
            fetchCurrenciesList();
            break;

        case addButton:
            app.popupForm(selectCurrencyForm);
            break;

        case deleteButton:
        {
            int sel = selCurrenciesList_.selection();
            if (noListSelection == sel)
                break;

            if (1 == prefs.selectedCurrencies.size())
            {
                MoriartyApplication::alert(noDestinationCurrency);
                break;
            }

            uint_t index = prefs.selectedCurrencies[sel];
            prefs.deselectCurrency(index);
            selCurrenciesList_.setSelection(0);
            break;
        }

        default:
            assert(false);
    }
}

void CurrencyMainForm::updateAfterLookup()
{
    MoriartyApplication& app=application();
    Preferences::CurrencyPreferences& prefs = app.preferences().currencyPreferences;
    int sel = selCurrenciesList_.selection();
    if (noListSelection == sel)
        sel = 0;
    assert(sel < prefs.selectedCurrencies.size());
    uint_t index = prefs.selectedCurrencies[sel];
    rate_ = GetCurrencyRate(*currencyData_, index);
    selCurrenciesList_.notifyItemsChanged();
    update();
}

void CurrencyMainForm::handleLookupFinished(const EventType& event)
{
    bool closeForm = false;

    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    Preferences::CurrencyPreferences& prefs = app.preferences().currencyPreferences;
    assert(NULL != lookupManager);

    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    if (lookupResultCurrency == data.result)
    {
        updateAfterLookup();
        MoriartyApplication::touchModule(moduleIdCurrency);
    }
    else
        closeForm = true;
    lookupManager->handleLookupFinishedInForm(data);
    update();
    if (closeForm && lookupManager->currencyData.empty())
        application().runMainForm();
}

bool CurrencyMainForm::handleEvent(EventType& event)
{
    bool handled = false;

    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    Preferences::CurrencyPreferences& prefs = app.preferences().currencyPreferences;

    switch (event.eType)
    {
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;

        case MoriartyApplication::appFieldChangedEvent:
            amountFieldChanged();
            break;

         case ExtendedList::selChangedEvent:
         {
            int sel = selCurrenciesList_.selection();
            if (noListSelection == sel)
                rate_ = 0;
            else
                changeSelection(sel);
            break;
         }
            
        case ctlSelectEvent:
            handleControlSelect(event);
            break;
               
        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled=true;
            break;     
                        
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool CurrencyMainForm::handleKeyPress(const EventType& event)
{
    int sel = selCurrenciesList_.selection();
    int option = List::optionScrollPagesWithLeftRight;
    if (application().runningOnTreo600())
        option = 0;
    bool handled = selCurrenciesList_.handleKeyDownEvent(event, List::optionFireListSelectOnCenter | option);
    if (handled)
    {
        int newSel = selCurrenciesList_.selection();
        if (newSel != sel) 
        {
            amountField_.select();
        }
    }
    else if (256 > event.data.keyDown.chr)
    {
        NumberFormatType numberFormat = static_cast<NumberFormatType>(PrefGetPreference(prefNumberFormat));
        char decSep = '.', ignore;
        LocGetNumberSeparators(numberFormat, &ignore, &decSep);
        if ((isDigit(event.data.keyDown.chr) || event.data.keyDown.chr == decSep) && !amountField_.hasFocus())
        {
            amountField_.focus();
            char chr = event.data.keyDown.chr;
            amountField_.setEditableText(&chr, 1);
            amountField_.setInsertionPoint(1);
        }
        sendEvent(MoriartyApplication::appFieldChangedEvent);
    }
    return handled;
}

bool CurrencyMainForm::handleMenuCommand(UInt16 itemId)
{
    bool    handled;
    switch (itemId)
    {
        case mainPageMenuItem:
             doneButton_.hit();
             handled = true;
             break;
        case mAddCurrency:
             addButton_.hit();
             handled = true;
             break;
        case mDeleteCurrency:
             deleteButton_.hit();
             handled = true;
             break;
        case mUpdateCurrencies:
             updateButton_.hit();
             handled = true;
             break;

        default:
            handled=MoriartyForm::handleMenuCommand(itemId);
            break;
    }
    return handled;
}

void CurrencyMainForm::updateAmountField()
{
    String strAmount = "0.00";
    if (amount_ >= 0.01)
    {
        char_t out[20];
        printDoubleRound(amount_,out, 0.005, 15, 2);
        strAmount = out;
    }
    localizeNumber(strAmount);
    lastAmount_= strAmount;
    amountField_.setEditableText(strAmount);
//    amountField_.select();
    if (visible())
        amountField_.draw();
}

void CurrencyMainForm::amountFieldChanged()
{
    const char* text = amountField_.text();
    if (NULL == text)
        return;
    String sText = text;
    delocalizeNumber(sText);
    if (sText == lastAmount_)
        return;
    lastAmount_ = sText;
    if (!strToDouble(sText.c_str(), &amount_))
        amount_ = 0;

    selCurrenciesList_.draw();
}

void CurrencyMainForm::fetchCurrenciesList()
{
    LookupManager* lookupManager=application().lookupManager;
    assert(NULL != lookupManager);
    lookupManager->fetchCurrencies();
}

void CurrencyMainForm::changeSelection(uint_t sel)
{   
    const Preferences::CurrencyPreferences& prefs = application().preferences().currencyPreferences;
    assert(sel < prefs.selectedCurrencies.size());
    uint_t index = prefs.selectedCurrencies[sel];
    double newRate = GetCurrencyRate(*currencyData_, index);
    if (0 != rate_ && 0 != newRate)
    {
        amount_ = newRate * amount_ / rate_;
        updateAmountField();
    }
    rate_ = newRate;
    selCurrenciesList_.draw();
}

