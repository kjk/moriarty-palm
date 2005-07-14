#include "StocksEnterStockForm.hpp"
#include "MoriartyPreferences.hpp"
#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>


void StocksEnterStockForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-78, screenBounds.width()-4, 76);
    setBounds(rect);
    
    if (modeSetQuantity == mode_ || modeNetflixPosition == mode_ || modeEBayBid == mode_)
    {
        numberField_.bounds(rect);
        rect.x() = 4;
        rect.width() = screenBounds.width() - 12;
        numberField_.setBounds(rect);
    }
    else if (modeAddPortfolio == mode_ || modeRenamePortfolio == mode_)
    {
        nameField_.bounds(rect);
        rect.width() = screenBounds.width() - 12;
        nameField_.setBounds(rect);
    }
    else {
        numberField_.bounds(rect);
        rect.x() = screenBounds.width() - 46;
        rect.width() = 40;
        numberField_.setBounds(rect);
        
        nameField_.bounds(rect);
        rect.width() = screenBounds.width() - 54;
        nameField_.setBounds(rect);
    }
    update();
}

void StocksEnterStockForm::attachControls()
{
    MoriartyForm::attachControls();
    nameField_.attach(nameField);
    numberField_.attach(numberField);
    helpText1Field_.attach(helpText1Field);
    helpText2Field_.attach(helpText2Field);
}


bool StocksEnterStockForm::handleOpen()
{
    bool handled=MoriartyForm::handleOpen();
    setMode(mode_);
    RectangleType rect;
    getScreenBounds(rect);
    resize(rect);
    return handled;
}

void StocksEnterStockForm::setMode(Mode mode)
{
    mode_ = mode;
    Preferences::StocksPreferences* prefs = &application().preferences().stocksPreferences;
    switch (mode)
    {
        case modeSetQuantity: {
            nameField_.hide();
            numberField_.show();
            assert(prefs->noPortfolio != prefs->lastDownloadedPortfolio);
            unsigned long value = prefs->portfolios[prefs->lastDownloadedPortfolio]->quantities[prefs->lastDownloadedStock];
            char buffer[32];
            StrPrintF(buffer, "%lu", value);
            numberField_.setEditableText(buffer);
            numberField_.select();
            setTitle(_T("Set quantity"));
            String text = _T("for: ");
            text.append(prefs->portfolios[prefs->lastDownloadedPortfolio]->symbols[prefs->lastDownloadedStock]);
            setHelpTexts(_T("Enter quantity"), text);
            break;
        }

        case modeAddStock:
            nameField_.show();
            numberField_.show();
            numberField_.setEditableText(_T("0"));
            setTitle(_T("Add stock"));
            setHelpTexts(_T("Enter ticker symbol e.g.:"), _T("'^DJI' or 'YHOO' and set quantity."));
            break;

        case modeAddPortfolio:            
            numberField_.hide();
            nameField_.show();
            setTitle(_T("Add portfolio"));
            setHelpTexts(_T("Enter new portfolio name."),_T("It will contain 3 default stocks."));
            break;

        case modeRenamePortfolio:
            assert(prefs->noPortfolio != prefs->lastDownloadedPortfolio);
            numberField_.hide();
            nameField_.show();
            nameField_.setEditableText(prefs->portfolios[prefs->lastDownloadedPortfolio]->name);
            nameField_.select();
            setTitle(_T("Rename portfolio"));
            setHelpTexts(_T("Enter new name"),_T("for current portfolio."));
            break;

        case modeNetflixPosition:
            nameField_.hide();
            numberField_.show();
            setTitle(_T("Change position"));
            setHelpTexts(_T("Move movie in the queue"), _T("to position:"));
            break;
            
        case modeEBayBid:
            {
                nameField_.hide();
                numberField_.show();
                setTitle(_T("eBay - Place bid"));
                
                String text;
                uint_t pos1, pos2;
                pos1 = request_.find(_T(";"));
                pos2 = request_.find(_T(";"), pos1+1);
                text.assign(_T("item (greater than "));
                text.append(String(request_, pos1+1, pos2-pos1-1));
                text.append(String(request_, pos2+1, String::npos));
                text.append(_T(")."));
                setHelpTexts(_T("Place your maximum bid for this"), text);
                
                numberField_.setEditableText(String(request_, pos2+1, String::npos));
                
                // prepare request
                text.assign(_T("s+ebayno:bid;"));
                text.append(String(request_, 0, pos1+1));
                request_.assign(text);
            }
            break;
    }
}

unsigned long StocksEnterStockForm::getNumberFieldValueUL()
{
    const char* number=numberField_.text();
    if (NULL != number)
    {
        String sNumber = number;
        strip(sNumber);
        if (!sNumber.empty())
        {
            long result;
            if (errNone == numericValue(sNumber, result))
                return result;
        }
    }
    return 0;
}

void StocksEnterStockForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case okButton: {
            String sText;
            if (modeSetQuantity != mode_ && modeNetflixPosition != mode_ && modeEBayBid != mode_)
            {
                const char* text = nameField_.text();
                if (NULL != text)
                {
                    sText = text;
                    strip(sText);
                }
                if (sText.empty())
                    return;
            }
            ulong_t number;
            if (modeSetQuantity == mode_ || modeAddStock == mode_ || modeNetflixPosition == mode_)
                number = getNumberFieldValueUL();
            if (modeEBayBid == mode_)
            {
                const char* text = numberField_.text();
                if (NULL != text)
                    sText = text;
                if (sText.empty())
                    return;
            }
            closePopup();
            Preferences::StocksPreferences* prefs = &application().preferences().stocksPreferences;
            switch(mode_)
            {
                case modeAddStock: {
                    prefs->lastDownloadedStock = prefs->portfolios[prefs->lastDownloadedPortfolio]->symbols.size();
                    String stocks = join(prefs->portfolios[prefs->lastDownloadedPortfolio]->symbols, _T(";"));
                    stocks.append(1, _T(';'));
                    stocks.append(sText);
                    for (uint_t i = 0; i < sText.size(); i++)
                        if (_T(';') == sText[i] || _T(' ') == sText[i])
                            sText.erase(sText.begin()+i);
                    prefs->newQuantity = number;
                    LookupManager* lookupManager = application().lookupManager;
                    lookupManager->fetchStocksListValidateLast(stocks);
                    break;
                }

                case modeAddPortfolio:
                    prefs->addPortfolio(sText);
                    break;

                case modeRenamePortfolio:
                    assert(prefs->noPortfolio != prefs->lastDownloadedPortfolio);
                    prefs->portfolios[prefs->lastDownloadedPortfolio]->name = sText;
                    break;
                    
                case modeSetQuantity:
                    assert(prefs->noPortfolio != prefs->lastDownloadedPortfolio);
                    prefs->portfolios[prefs->lastDownloadedPortfolio]->quantities[prefs->lastDownloadedStock] = number;
                    break;
                    
                case modeNetflixPosition:
                    {
                        if (number != 0)
                        {
                            LookupManager* lookupManager = application().lookupManager;
                            request_.append(numberField_.text());
                            lookupManager->fetchUrl(request_.c_str());
                        }
                    }                    
                    break;
                    
                case modeEBayBid:
                    {
                        request_.append(sText);
                        LookupManager* lookupManager = application().lookupManager;
                        lookupManager->fetchUrl(request_.c_str());
                    }        
                    break;
        
                default:
                    break;
            }
            sendEvent(MoriartyApplication::appSetStocksEnterStockFormOkButtonEvent);
            break;
        }
            
        case cancelButton:
            closePopup();
            update();
            break;
            
    }
}

void StocksEnterStockForm::setHelpTexts(const ArsLexis::String& str1, const ArsLexis::String& str2)
{
    helpText1Field_.setText((const char*)NULL);
    helpText2Field_.setText((const char*)NULL);
    if (!str1.empty())
    {
        helpText1String_.assign(str1);
        helpText1Field_.setText(helpText1String_.c_str());
    }
    if (!str2.empty())
    {
        helpText2String_.assign(str2);
        helpText2Field_.setText(helpText2String_.c_str());
    }
    update();
}

bool StocksEnterStockForm::handleEvent(EventType& event)
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

StocksEnterStockForm::~StocksEnterStockForm()
{}

StocksEnterStockForm::StocksEnterStockForm(MoriartyApplication& app, Mode mode, const char_t* request):
    MoriartyForm(app, stocksEnterStockForm, true),
    nameField_(*this),
    numberField_(*this),
    helpText1Field_(*this),
    helpText2Field_(*this),
    mode_(mode)
{
    switch (mode) {
        case modeAddStock:
        case modeRenamePortfolio:
        case modeAddPortfolio:
            setFocusControlId(nameField);
            break;
            
        case modeSetQuantity:
            setFocusControlId(numberField);
            break;
            
        case modeNetflixPosition:
            request_.assign(_T("s+netflixqueue:mov;"));
            request_.append(request);
            request_.append(1, _T(';'));
            setFocusControlId(numberField);
            break;

        case modeEBayBid:
            request_.assign(request);
            break;
            
        default:
            assert(false);
    }
    
}    
