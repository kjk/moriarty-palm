#include "StockDetailedDoneUpdateForm.hpp"
#include "MoriartyPreferences.hpp"
#include "LookupManager.hpp"
#include <Definition.hpp>
#include <TextElement.hpp>
#include <LineBreakElement.hpp>
#include <BulletElement.hpp>
#include <Text.hpp>
#include <SysUtils.hpp>
#include "Forms/SimpleTextDoneForm.hpp"
#include "HyperlinkHandler.hpp"

#include "MoriartyStyles.hpp"

#pragma pcrelconstdata on

enum {
    stocksNameIndex,
    stocksLastTradeIndex,
    stocksTradeTimeIndex,
    stocksChangeIconIndex,
    stocksChangeIndex,
    stocksPrevCloseIndex,
    stocksOpenIndex,
    stocksBidIndex,
    stocksAskIndex,
    stocks1yTargetEstIndex,
    stocksDaysRangeIndex,
    stocks52wkRangeIndex,
    stocksVolumeIndex,
    stocksAvgVolIndex,
    stocksMarketCapIndex,
    stocksPEIndex,
    stocksEPSIndex,
    stocksDivYieldIndex,
    stocksStockElementsCount
};

enum {
    maxStockPartNameLength=15
};

typedef const char_t StockInformationField_t[maxStockPartNameLength];

static const StockInformationField_t stockInformationNames[]={
    "Name:",
    "Last Trade:",
    "Trade Time:",
    "Change icon:",
    "Change:",
    "Prev Close:",
    "Open:",
    "Bid:",
    "Ask:",
    "1y Target Est:",
    "Day's Range:",
    "52wk Range:",
    "Volume:",
    "Avg Vol (3m):",
    "Market Cap:",
    "P/E (ttm):",
    "EPS (ttm):",
    "Div & Yield:" 
};

enum { shortNamesCount = 9 };
static const StockInformationField_t stockInformationShortNames[]={
    "Name:",
    "Index Value:",
    "Trade Time:",
    "Change icon:",
    "Change:",
    "Prev Close:",
    "Open:",
    "Day's Range:",
    "52wk Range:" 
};

static const StockInformationField_t stockInformationQuantityNames[]={
    "Quantity:",
    "Value:"    
};

StockDetailedDoneUpdateForm::StockDetailedDoneUpdateForm(MoriartyApplication& app, DisplayMode mode):
    MoriartyForm(app, stockDetailedDoneUpdateForm),
    scrollBar_(*this),
    doneButton_(*this),
    backButton_(*this),
    updateButton_(*this),
    displayMode_(mode),
    stocksDetailsRenderer_(*this, &scrollBar_)
{
    setFocusControlId(doneButton);
    stocksDetailsRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
}

StockDetailedDoneUpdateForm::~StockDetailedDoneUpdateForm() {}

void StockDetailedDoneUpdateForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    doneButton_.attach(doneButton);
    backButton_.attach(backButton);
    updateButton_.attach(updateButton);
    stocksDetailsRenderer_.attach(stocksDetailsRenderer);
    stocksDetailsRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
    
}

bool StockDetailedDoneUpdateForm::handleOpen()
{
    bool result=MoriartyForm::handleOpen();
    setDisplayMode(displayMode_);
    return result;
}
    
void StockDetailedDoneUpdateForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(2, 2, screenBounds.width()-4, screenBounds.height()-4);
    setBounds(bounds);

    stocksDetailsRenderer_.anchor(screenBounds, anchorRightEdge, 12, anchorBottomEdge, 38);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 11, anchorBottomEdge, 38);
    
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    backButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    updateButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    update();    
}

bool StockDetailedDoneUpdateForm::handleEvent(EventType& event)
{
    if (showNothing != displayMode_ && stocksDetailsRenderer_.handleEventInForm(event))
        return true;
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled = true;
            break;
            
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;

        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled = true;
            break;
            
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

void StockDetailedDoneUpdateForm::setDisplayMode(StockDetailedDoneUpdateForm::DisplayMode dm)
{
    backButton_.hide();
    updateButton_.hide();
    displayMode_ = dm;
    switch (dm)
    {
        case showStockDetailed:
            {   
                Preferences::StocksPreferences* prefs = &application().preferences().stocksPreferences;
                UniversalDataFormat* stocks = &application().lookupManager->stocks;
                updateString_.assign(stocks->getItemText(prefs->lastDownloadedStock, 0));
                setTitle(stocks->getItemText(prefs->lastDownloadedStock, 1));
            }
            prepareStock();
            stocksDetailsRenderer_.show();
            updateButton_.show();
            scrollBar_.show();
            break;  

        case showNothing:
            stocksDetailsRenderer_.hide();
            scrollBar_.hide();
            break;  

        default:
            assert(false);
    }
}

void StockDetailedDoneUpdateForm::handleUpdateButton()
{
    LookupManager* lookupManager=application().lookupManager;
    assert(0 != lookupManager);
    switch (displayMode_)
    {
        case showNothing:
            break;
            
        case showStockDetailed:
            lookupManager->fetchStock(updateString_);
            break;
            
        default:
            assert(false);
            break;
    }
}

void StockDetailedDoneUpdateForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton: //same as back (no break)
        case backButton:
            closePopup();
            break;
            
        case updateButton:
            handleUpdateButton();
            break;

        default:
            assert(false);
    }
}

void StockDetailedDoneUpdateForm::prepareStock()
{
    stocksDetailsRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    stocksDetailsRenderer_.setHyperlinkHandler(NULL);
    
    const LookupManager* lookupManager=application().lookupManager;
    assert(0!=lookupManager);

    const UniversalDataFormat& stock=lookupManager->stock;
    assert(!stock.empty());

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    Definition::Elements_t& elems = model->elements;

    TextElement* text;

    int count = stock.getItemElementsCount(0);
    String value;
    for (int i=0; i < count && i < stocksStockElementsCount; i++)
    {
        switch (i)
        {
            case stocksNameIndex:        
                elems.push_back(text=new TextElement(stock.getItemText(0, i)));
                if (startsWith(stock.getItemText(0, stocksChangeIconIndex), _T("D")))
                    text->setStyle(StyleGetStaticStyle(styleNameStockPriceDown));
                else if (startsWith(stock.getItemText(0, stocksChangeIconIndex), _T("U")))
                    text->setStyle(StyleGetStaticStyle(styleNameStockPriceUp));
                else
                    text->setStyle(StyleGetStaticStyle(styleNameHeader));
                text->setJustification(DefinitionElement::justifyCenter);
                break;
        
            case stocksChangeIconIndex:
                break;            
        
            case stocksChangeIndex: 
                elems.push_back(new LineBreakElement());
                elems.push_back(text=new TextElement(stockInformationNames[i]));
                value = stock.getItemText(0, i);
                localizeNumber(value);
                elems.push_back(text=new TextElement(value));

                if (startsWith(stock.getItemText(0, stocksChangeIconIndex),_T("D")))
                    text->setStyle(StyleGetStaticStyle(styleNameStockPriceDown));
                else if (startsWith(stock.getItemText(0, stocksChangeIconIndex),_T("U")))
                    text->setStyle(StyleGetStaticStyle(styleNameStockPriceUp));
                else
                    text->setStyle(StyleGetStaticStyle(styleNameBold));
                text->setJustification(DefinitionElement::justifyRightLastElementInLine);
                break;
                    
            default:
                elems.push_back(new LineBreakElement());
                if (shortNamesCount == stock.getItemElementsCount(0))
                    elems.push_back(text=new TextElement(stockInformationShortNames[i]));
                else
                    elems.push_back(text=new TextElement(stockInformationNames[i]));

                value = stock.getItemText(0, i);
                localizeNumber(value);
                elems.push_back(text=new TextElement(value));
                text->setStyle(StyleGetStaticStyle(styleNameBold));
                text->setJustification(DefinitionElement::justifyRightLastElementInLine);
                break;
        }    
    }
    
    Preferences::StocksPreferences* prefs = &application().preferences().stocksPreferences;
    unsigned long quantity = prefs->portfolios[prefs->lastDownloadedPortfolio]->quantities[prefs->lastDownloadedStock];
    if (quantity > 0)
    {
        elems.push_back(new LineBreakElement());
        elems.push_back(text=new TextElement(stockInformationQuantityNames[0]));

        elems.push_back(text=new TextElement(convertUnsignedLongWithCommaToString(quantity,0)));
        text->setStyle(StyleGetStaticStyle(styleNameBold));
        text->setJustification(DefinitionElement::justifyRightLastElementInLine);

        elems.push_back(new LineBreakElement());
        elems.push_back(text=new TextElement(stockInformationQuantityNames[1]));
        
        double value;
        strToDouble(stock.getItemText(0, stocksLastTradeIndex), &value);
        value *= quantity;
        char_t cValue[32];
        printDoubleRound(value, cValue, 0.005, 15, 2, true);
        localizeNumber(cValue, cValue + tstrlen(cValue));
        elems.push_back(text=new TextElement(cValue));
        text->setStyle(StyleGetStaticStyle(styleNameBold));
        text->setJustification(DefinitionElement::justifyRightLastElementInLine);
    }
    stocksDetailsRenderer_.setModel(model, Definition::ownModel);            
}

void StockDetailedDoneUpdateForm::handleLookupFinished(const EventType& event)
{
    bool close = true;
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    switch (data.result)
    {
        case lookupResultStock:
            prepareStock();
            setDisplayMode(showStockDetailed);
            close = false;    
            update();
            break;
    }
    MoriartyApplication& app=application();
    LookupManager* lookupManager = app.lookupManager;
    assert(0 != lookupManager);
    lookupManager->handleLookupFinishedInForm(data);
    if (close)
        doneButton_.hit();
}

bool StockDetailedDoneUpdateForm::handleKeyPress(const EventType& event)
{
    bool handled = false;
    switch (event.data.keyDown.chr)
    {
        case chrLineFeed:
        case chrCarriageReturn:
            doneButton_.hit();
            handled = true;
            break;
    }
    return handled;
}
