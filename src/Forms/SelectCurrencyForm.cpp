#include "SelectCurrencyForm.hpp"
#include "MoriartyPreferences.hpp"
#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"
#include <SysUtils.hpp>
#include <Currencies.hpp>
#include <Text.hpp>
#include <Graphics.hpp>
#include <UniversalDataFormat.hpp>

#include "MoriartyStyles.hpp"

CurrencyListDrawHandler::CurrencyListDrawHandler(const UniversalDataFormat& data): 
    prefs_(MoriartyApplication::instance().preferences()),
    currencyData_(data),
    mode_(modeAvailable)
{}

CurrencyListDrawHandler::CurrencyListDrawHandler(const UniversalDataFormat& data, double& amount, double& rate):
    prefs_(MoriartyApplication::instance().preferences()),
    currencyData_(data),
    mode_(modeSelected),
    amount_(&amount),
    rate_(&rate)
{}

#define notAvailableText _T("N/A")

#define MARGIN_LEFT 2

void CurrencyListDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    const Preferences::CurrencyPreferences& prefs = prefs_.currencyPreferences;
    
    uint_t          index;    
    const char_t*   symbol;
    String          amount;
    IndexedColorType color;
    bool            selected = false;

    if (modeSelected == mode_)
    {
        assert(item < prefs.selectedCurrencies.size());
        index = prefs.selectedCurrencies[item];
        symbol = getCurrencySymbol(index);
        amount = notAvailableText;
        
        double rate = GetCurrencyRate(currencyData_, symbol);
        if (0 != rate && 0 != *rate_)
        {
            double r = rate * (*amount_)/(*rate_);
            // User doesn't care about numbers in form 9.12 e-3, it's zero
            if (r >= 0.01)
            {
                char_t out[20];
                printDoubleRound(r, out, 0.005, 15, 2);
                amount  = out;
            }
            else
                amount= "0.00";
            localizeNumber(amount);
        }
    }
    else
    {
        symbol = currencyData_.getItemText(item, currencySymbolIndex);
        int i = getCurrencyIndex(symbol);
        assert( -1 != i);
        index = i;
        selected = prefs.isCurrencySelected(index);
        
        if (selected)
            color = WinSetTextColor(WinRGBToIndex(&StyleGetStaticStyle(styleNameGreen)->foregroundColor));
    }

    String name = getCurrencyName(index);
    name.append(" - ", 3).append(getCurrencyRegion(index));
    
    uint_t margin = 1;

    Point rightText;
    rightText = itemBounds.topLeft;
    rightText.x += margin;
    uint_t totalWidth = itemBounds.width() - 2 * margin;
    uint_t width = totalWidth;
    uint_t length;

    if (modeSelected == mode_)
    {
        length = amount.length();
        graphics.charsInWidth(amount.c_str(), length, width);
        Point leftText = rightText;
        leftText.x += totalWidth - width;
        graphics.drawText(amount.c_str(), length, leftText);
        totalWidth -= width;
        width = totalWidth;                                
    }        

    length = tstrlen(symbol);
    graphics.charsInWidth(symbol, length, width);
    rightText.x += MARGIN_LEFT;
    graphics.drawText(symbol, length, rightText);
    rightText.x -= MARGIN_LEFT;

    // Make 2nd column (currency names) indented with max. width of symbol + 1 space
    // 'M' is the widest letter, so it should suffice to indent it with 3 M's.
    width = graphics.textWidth(_T("MMM "), 4);

    rightText.x += width;
    totalWidth -= width;
    width = totalWidth;
    length = name.length();
    graphics.charsInWidth(name.c_str(), length, width);
    if (length < name.length() && length > 3)
    {
        name.erase(length - 3);
        name.append(_T("..."));
        graphics.drawText(name.c_str(), length, rightText);
    }
    else
        graphics.drawText(name.c_str(), length, rightText);
        
    if (modeAvailable == mode_ && selected)
        WinSetTextColor(color);
    
/*  
    rightText.x += width;
    totalWidth -= width;
    width = totalWidth;
    length = currCountries.length();
    graphics.charsInWidth(currCountries.c_str(), length, width);
    if (length < currCountries.length() && length>3)
    {
        currCountries.erase(length-3);
        currCountries.append(_T("..."));
    }
    graphics.drawText(currCountries.c_str(), length, rightText);             
 */    
}

uint_t CurrencyListDrawHandler::itemsCount() const
{
    switch (mode_)
    {
        case modeSelected:
            return MoriartyApplication::instance().preferences().currencyPreferences.selectedCurrencies.size();
            
        case modeAvailable:
            return currencyData_.getItemsCount();
    };
    assert(false);
    return currencyData_.getItemsCount();
}
    
CurrencyListDrawHandler::~CurrencyListDrawHandler()
{}        

SelectCurrencyForm::SelectCurrencyForm(MoriartyApplication& app):
    MoriartyForm(app, selectCurrencyForm, true),
    currenciesList_(*this),
    okButton_(*this),
    cancelButton_(*this)
{
    const LookupManager* lookupManager = app.lookupManager;
    currenciesListDrawHandler_.reset(new CurrencyListDrawHandler(lookupManager->currencyData));
    setFocusControlId(okButton);
}
    
SelectCurrencyForm::~SelectCurrencyForm()
{}

void SelectCurrencyForm::attachControls()
{
    MoriartyForm::attachControls();
    currenciesList_.attach(currenciesList);
    
    currenciesList_.setItemHeight(CurrencyListDrawHandler::currenciesListItemLines * CurrencyListDrawHandler::currenciesListLineHeight);
    currenciesList_.setUpBitmapId(upBitmap);
    currenciesList_.setDownBitmapId(downBitmap);

    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);

}



bool SelectCurrencyForm::handleOpen()
{
    bool res=MoriartyForm::handleOpen();
    assert(NULL != currenciesListDrawHandler_.get());
    currenciesList_.setCustomDrawHandler(currenciesListDrawHandler_.get());
    if (0 != currenciesList_.itemsCount())
        currenciesList_.setSelection(0);
    return res;
}

void SelectCurrencyForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(screenBounds);
    bounds.explode(2, 2, -4, -4);        
    setBounds(bounds);
    
    ArsRectangle objBounds(0, 14, screenBounds.width()-4, screenBounds.height()-35);
    currenciesList_.setBounds(objBounds);
    currenciesList_.adjustVisibleItems();

    okButton_.bounds(bounds);
    bounds.y()=screenBounds.height()-18;
    okButton_.setBounds(bounds);

    cancelButton_.bounds(bounds);
    bounds.y()=screenBounds.height()-18;
    cancelButton_.setBounds(bounds);
    update();
}

bool SelectCurrencyForm::handleEvent(EventType& event)
{
    bool handled=false;
    switch (event.eType) 
    {
        case lstSelectEvent:
            assert(currenciesList == event.data.lstSelect.listID);
            int itemID = event.data.lstSelect.selection;
            okButton_.hit();
            handled=true;
            break;
            
        case ctlSelectEvent:
            handleControlSelected(event);
            handled=true;
            break;

        case keyDownEvent: {
            int option = List::optionScrollPagesWithLeftRight;
            if (application().runningOnTreo600())
                option = 0;
            handled = currenciesList_.handleKeyDownEvent(event, option|List::optionFireListSelectOnCenter);
            if (handled)
                break;
            if (event.data.keyDown.chr < 256 && isAlpha(event.data.keyDown.chr))
            {
                const LookupManager* lookupManager = application().lookupManager;
                uint_t index = GetIndexOfCurrencyByFirstCharInUDF(lookupManager->currencyData, event.data.keyDown.chr);
                currenciesList_.setSelection(index, ExtendedList::redrawNot);
                uint_t count = currenciesList_.itemsCount();
                uint_t visible = currenciesList_.height() / currenciesList_.itemHeight();
                uint_t below = count - index - 1;
                if (below >= visible)
                    currenciesList_.setTopItem(index, ExtendedList::redraw);
                else
                {
                    if (count > visible)
                        currenciesList_.setTopItem(count - visible, ExtendedList::redraw);
                    else
                        currenciesList_.draw();
                }
                break;
            }
        }            
            // watch out for fall through here!
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

void SelectCurrencyForm::handleControlSelected(const EventType& event)
{
    switch (event.data.ctlSelect.controlID) 
    {
        case okButton:
        {
            int sel = currenciesList_.selection();
            if (noListSelection == sel)
                break;
            MoriartyApplication& app = application();
            LookupManager* lm = app.lookupManager;
            assert(NULL != lm);
            const char* symbol = lm->currencyData.getItemText(sel, currencySymbolIndex);
            uint_t index = getCurrencyIndex(symbol);
            if (!app.preferences().currencyPreferences.isCurrencySelected(index))
            {                
                app.preferences().currencyPreferences.selectCurrency(index);
                closePopup();
            }
            break;
        }
                                    
        case cancelButton:
            closePopup();
            break;
                        
        default:
            assert(false);
    }
}
