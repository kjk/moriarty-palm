#include <SysUtils.hpp>
#include <Text.hpp>
#include <DynStr.hpp>

#include <Definition.hpp>
#include <TextElement.hpp>
#include <LineBreakElement.hpp>

#include "LookupManager.hpp"
#include "StocksEnterStockForm.hpp"
#include "Forms/StockDetailedDoneUpdateForm.hpp"
#include "StocksMainForm.hpp"

enum {
    stocksListItemUrlIndex,
    stocksListItemSymbolIndex,
    stocksListItemTimeIndex,
    stocksListItemTradeIndex,
    stocksListItemChangeIconIndex,
    stocksListItemChangeIndex,
    stocksListItemPercentChangeIndex,
    stocksListItemVolumeIndex,
    stocksListElementsCount
};
enum {
    stocksListNotFoundElementsCount = 2
};

#define notFoundText        _T("Look up symbol for: ")
#define portfolioValueText  _T("Portfolio value: ")

class StocksListDrawHandler: public BasicStringItemRenderer {

    UniversalDataFormat* listUDF_;
    Preferences::StocksPreferences::Portfolios* portfolio_;
    
public:
    
    explicit StocksListDrawHandler(UniversalDataFormat* udf, Preferences::StocksPreferences::Portfolios* portfolio): listUDF_(udf), portfolio_(portfolio) {}
    
    uint_t itemsCount() const
    {
        return listUDF_->getItemsCount() + 1;
    }

    ~StocksListDrawHandler();

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);
    
protected:
    
    void getItem(String& out, uint_t item)
    {
        assert( item != portfolioValueItemNo());
        out.assign(listUDF_->getItemText(item, stocksListItemSymbolIndex));
    }

    uint_t portfolioValueItemNo()
    {
        return listUDF_->getItemsCount();
    }
    
};

StocksListDrawHandler::~StocksListDrawHandler() {}

#define MARGIN_LEFT 2

void StocksListDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    uint_t          width = itemBounds.width();
    String          text;
    uint_t          length;

    if (item == portfolioValueItemNo())
    {
        Point p = itemBounds.topLeft;

        length = tstrlen(portfolioValueText);
        graphics.charsInWidth(portfolioValueText, length, width);
        p.x += MARGIN_LEFT;
        graphics.drawText(portfolioValueText, length, p);
        p.x -= MARGIN_LEFT;

        width = itemBounds.width();
        text = portfolio_->totalValue;
        if (text.empty())
            text.assign(_T("0"));
        localizeNumber(text);
        length = text.length();
        graphics.charsInWidth(text.c_str(), length, width);
        p.x = itemBounds.x() + itemBounds.width() - width;
        graphics.drawText(text.c_str(), length, p);

        return;
    }

    RGBColorType oldColor;
    RGBColorType newColor;

    if (stocksListNotFoundElementsCount == listUDF_->getItemElementsCount(item))
    {
        setRgbColor(newColor,255,0,0);    
        WinSetTextColorRGB(&newColor, &oldColor);

        text = notFoundText;
        text.append(listUDF_->getItemText(item, stocksListItemSymbolIndex));
        length = text.length();
        graphics.charsInWidth(text.c_str(), length, width);
        graphics.drawText(text.c_str(), length, itemBounds.topLeft);
        WinSetTextColorRGB(&oldColor, &newColor);
    }
    else
    {
        text = listUDF_->getItemText(item, stocksListItemTradeIndex);
        localizeNumber(text);
        text += _T("; ");
        String tmp = listUDF_->getItemText(item, stocksListItemChangeIndex);
        localizeNumber(tmp); 
        text += tmp;
        text += _T("; ");
        tmp = listUDF_->getItemText(item, stocksListItemPercentChangeIndex);
        localizeNumber(tmp);
        text+= tmp;
        length = text.length();
        graphics.charsInWidth(text.c_str(), length, width);
        Point newRight = itemBounds.topLeft;
        newRight.x = itemBounds.x() + itemBounds.width() - width;
        graphics.drawText(text.c_str(), length, newRight);

        text = listUDF_->getItemText(item, stocksListItemChangeIconIndex);

        if (startsWith(text,_T("D")))
            setRgbColor(newColor,255,0,0);    
        else if (startsWith(text,_T("U")))
            setRgbColor(newColor,0,196,0);    
        else
            setRgbColor(newColor,0,0,0);    

        WinSetTextColorRGB(&newColor, &oldColor);
        Font oldFont = graphics.setFont(boldFont);
        text = listUDF_->getItemText(item, stocksListItemSymbolIndex);
        // change default indexes to texts
        if (text == _T("^DJI"))
            text.assign(_T("Dow"));
        else if (text == _T("^IXIC"))
            text.assign(_T("Nasdaq"));
        else if (text == _T("^GSPC"))
            text.assign(_T("S&P 500"));

        length = text.length();
        graphics.charsInWidth(text.c_str(), length, width);
        Point p = itemBounds.topLeft;
        p.x += MARGIN_LEFT;
        graphics.drawText(text.c_str(), length, p);
        graphics.setFont(oldFont);
         
        WinSetTextColorRGB(&oldColor, &newColor);
    }
}

StocksMainForm::StocksMainForm(MoriartyApplication& app):
    MoriartyForm(app, stocksMainForm),
    stocksList_(*this),
    doneButton_(*this),
    addButton_(*this),
    updateButton_(*this),
    downloadingStockIndex_(stockIndexNone),
    currentStockIndex_(stockIndexNone),
    byNameDownloadingStockIndex_(stockIndexNone)
{
    setFocusControlId(stocksList);
}

StocksMainForm::~StocksMainForm() {}

void StocksMainForm::attachControls()
{
    MoriartyForm::attachControls();
    doneButton_.attach(doneButton);
    updateButton_.attach(updateButton);
    addButton_.attach(addButton);

    stocksList_.attach(stocksList);
    stocksList_.setUpBitmapId(upBitmap);
    stocksList_.setDownBitmapId(downBitmap);

    stocksList_.setItemHeight(12);
}

bool StocksMainForm::handleOpen()
{
    bool result=MoriartyForm::handleOpen();
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(0!=lookupManager);

    preferences_ = &app.preferences().stocksPreferences;

    bool portfolioDownloaded = false;
    if (preferences_->currentPortfolio == preferences_->lastDownloadedPortfolio && preferences_->currentPortfolio != preferences_->noPortfolio)
        portfolioDownloaded = true;

    if (!lookupManager->stocks.empty() && portfolioDownloaded)
        updateStocks();
    else if (preferences_->currentPortfolio != preferences_->noPortfolio)
        lookupManager->fetchStocksList(join(preferences_->portfolios[preferences_->currentPortfolio]->symbols, _T(";")));
    else
    {
        MoriartyApplication::popupForm(selectStateForm);
        sendEvent(MoriartyApplication::appSetStocksPortfolioEvent);
    }
    return result;
}

void StocksMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(bounds = screenBounds);

    stocksList_.anchor(screenBounds, anchorRightEdge, 0, anchorBottomEdge, 36);
    stocksList_.adjustVisibleItems();

    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    updateButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    addButton_.anchor(screenBounds, anchorLeftEdge, 52, anchorTopEdge, 14);

    update();    
}

void StocksMainForm::showStock()
{
    preferences_->lastDownloadedStock = currentStockIndex_;
    (new StockDetailedDoneUpdateForm(application(), StockDetailedDoneUpdateForm::showStockDetailed))->popup();
}

void StocksMainForm::switchPortfolio()
{
    if (1 == preferences_->portfoliosCount())
    {
        MoriartyApplication::alert(onlyOnePortfolioAlert);
        return;
    }

    MoriartyApplication::popupForm(selectStateForm);
    sendEvent(MoriartyApplication::appSetStocksPortfolioEvent);
}

bool StocksMainForm::handleEvent(EventType& event)
{
    bool handled=false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled = true;
            break;

        case lstSelectEvent:
            handleListItemSelect(event.data.lstSelect.listID, event.data.lstSelect.selection);
            handled = true;
            break;

        case keyDownEvent:
            handled = handleKeyPress(event);
            break;

        case MoriartyApplication::appSetStocksEnterStockFormOkButtonEvent:
            if (fIsAddingPortfolio_)
            {
                preferences_->currentPortfolio = preferences_->portfoliosCount()-1;
                application().lookupManager->fetchStocksList(join(preferences_->portfolios[preferences_->currentPortfolio]->symbols,_T(";")));
            }
            else
            {
                updateTotalValue();
                stocksList_.adjustVisibleItems();
                updateTitle();
                update();
            }
            handled = true;
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

bool StocksMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled = true;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            break;

        case addStockMenuItem:
            addButton_.hit();
            break;

        case deleteStockMenuItem:
            {
                uint_t selection = stocksList_.selection();
                if (application().lookupManager->stocks.getItemsCount() == selection)
                    break;
                std::vector<String> vec = preferences_->portfolios[preferences_->lastDownloadedPortfolio]->symbols;
                if (0 <= selection && vec.size() > selection)
                {
                    if (1 < vec.size())
                    {
                        vec.erase(vec.begin() + selection);
                        LookupManager* lookupManager = application().lookupManager;
                        assert(NULL!=lookupManager);
                        lookupManager->fetchStocksList(join(vec, _T(";")));
                    }
                    else
                        MoriartyApplication::alert(cantDeleteLastStockAlert);
                }       
            }
            break;

        case updateMenuItem:
            updateButton_.hit();
            break;
            
        case switchPortfolioMenuItem:
            switchPortfolio();
            break;
            
        case addPortfolioMenuItem:
            fIsAddingPortfolio_ = true;
            StocksEnterStockForm* form = new StocksEnterStockForm(application(), StocksEnterStockForm::modeAddPortfolio);   
            form->popup();  
            break;

        case setQuantityMenuItem:
            fIsAddingPortfolio_ = false;
            if (noListSelection == stocksList_.selection())
                break;
            if (stocksList_.selection() == application().lookupManager->stocks.getItemsCount())
                break;
            preferences_->lastDownloadedStock = stocksList_.selection();
            (new StocksEnterStockForm(application(), StocksEnterStockForm::modeSetQuantity))->popup();   
            break;

        case deletePortfolioMenuItem:
            if (preferences_->portfoliosCount() > 1)
            {
                preferences_->lastDownloadedPortfolio = preferences_->noPortfolio;
                preferences_->deletePortfolio(preferences_->currentPortfolio);
                preferences_->currentPortfolio = preferences_->defaultPortfolio;
                LookupManager* lookupManager = application().lookupManager;
                assert(0!=lookupManager);
                lookupManager->fetchStocksList(join(preferences_->portfolios[preferences_->currentPortfolio]->symbols, _T(";")));
            }
            else
                MoriartyApplication::alert(cantDeleteLastPortfolioAlert);
            break;

        case renamePortfolioMenuItem:
            fIsAddingPortfolio_ = false;
            (new StocksEnterStockForm(application(), StocksEnterStockForm::modeRenamePortfolio))->popup();  
            break;

        default:
            handled=false;
            assert(false);
    }
    return handled;
}

void StocksMainForm::updateStocks()
{
    updateTotalValue();
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(0!=lookupManager);
    int selection = stocksList_.selection();
    stocksListDrawHandler_.reset(new StocksListDrawHandler(&lookupManager->stocks, preferences_->portfolios[preferences_->lastDownloadedPortfolio]));
    stocksList_.setCustomDrawHandler(stocksListDrawHandler_.get());
    if (0 != stocksList_.itemsCount())
    {
        if (0 <= selection && selection < stocksList_.itemsCount())
            stocksList_.setSelection(selection);
        else
            stocksList_.setSelection(0);
    }
    stocksList_.adjustVisibleItems();
    stocksList_.notifyItemsChanged();
    stocksList_.show();
    updateTitle();
    update();
}

void StocksMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;
            
        case addButton:
            fIsAddingPortfolio_ = false;
            (new StocksEnterStockForm(application(), StocksEnterStockForm::modeAddStock))->popup();
            break;
            
        case updateButton:
            LookupManager* lookupManager = application().lookupManager;
            lookupManager->fetchStocksList(join(preferences_->portfolios[preferences_->currentPortfolio]->symbols, _T(";")));
            break;
            
        default:
            assert(false);
            break;
    }
}

void StocksMainForm::updateTotalValue()
{
    double   totalValue = 0;
    UniversalDataFormat* stocks = &application().lookupManager->stocks;
    Preferences::StocksPreferences::Portfolios* portfolio = preferences_->portfolios[preferences_->lastDownloadedPortfolio];
    int count = stocks->getItemsCount();
    for (int i = 0; i < count; i++)
    {
        if (stocksListElementsCount == stocks->getItemElementsCount(i))
        {
            if (0 < portfolio->quantities[i])
            {
                unsigned long quantity = portfolio->quantities[i];
                const char_t* sValue = stocks->getItemText(i, stocksListItemTradeIndex);
                double dValue = 0;
                strToDouble(sValue, &dValue);
                totalValue += double(quantity) * dValue;
            }
        }
    }
    char_t cValue[32];
    printDoubleRound(totalValue, cValue, 0.005, 15, 2, true);
    if (totalValue > 0)
        portfolio->totalValue = cValue;
    else
        portfolio->totalValue.clear();
}

void StocksMainForm::synchronizePortfolio(Preferences::StocksPreferences::Portfolios& portfolio, const std::vector<String>& vec)
{
    uint_t portfolioSize = portfolio.symbols.size();
    assert(portfolio.quantities.size() == portfolioSize);
    uint_t vecSize = vec.size();
    /*  this is simple function - 
        we relay on actual method of adding and deleting methods
        add no more than one index
        delete no more than one index
    */
    if (vecSize > portfolioSize)
    {
        //add some stocks
        for (uint_t i = portfolioSize; i < vecSize; i++)
        {   
            portfolio.symbols.push_back(vec[i]);
            portfolio.quantities.push_back(preferences_->newQuantity);
        }
    }
    else if (vecSize < portfolioSize)
    {
        //delete some stocks
        for (uint_t i = 0; i < portfolio.symbols.size(); /*nothing!*/)
        {
            if (portfolio.symbols[i] == vec[i])
                i++;
            else
            {
                portfolio.symbols.erase(portfolio.symbols.begin()+i);
                portfolio.quantities.erase(portfolio.quantities.begin()+i);
            }        
        }
    }
    else
    {
        //changes? (quantities without change)
        for (uint_t i = 0; i<vecSize; i++)
            if(portfolio.symbols[i] != vec[i])
                portfolio.symbols[i] = vec[i];
    }   
    assert(vec.size() == portfolio.symbols.size());
}

void StocksMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    bool handled = false;
    switch (data.result)
    {
        case lookupResultStocksList:
            {
                preferences_->lastDownloadedPortfolio = preferences_->currentPortfolio;
                std::vector<String> vec;
                LookupManager* lookupManager = application().lookupManager;
                assert(NULL != lookupManager);
                for (int i = 0; i < lookupManager->stocks.getItemsCount(); i++)
                    vec.push_back(lookupManager->stocks.getItemText(i,stocksListItemSymbolIndex));
                synchronizePortfolio(*preferences_->portfolios[preferences_->lastDownloadedPortfolio], vec);
                downloadingStockIndex_ = stockIndexNone;
                currentStockIndex_ = stockIndexNone;
                updateStocks();
                handled = true;
                MoriartyApplication::touchModule(moduleIdStocks);
            }
            break;

        case lookupResultStock:
            currentStockIndex_ = downloadingStockIndex_;
            showStock();
            handled = true;
            break;

        case lookupResultStocksListByName:
            downloadingStockIndex_ = stockIndexNone;
            currentStockIndex_ = stockIndexNone;
            if (stockIndexNone != byNameDownloadingStockIndex_)
                preferences_->lastDownloadedStock = byNameDownloadingStockIndex_;
            byNameDownloadingStockIndex_ = stockIndexNone;
            MoriartyApplication::popupForm(selectStateForm);
            sendEvent(MoriartyApplication::appSetStocksNameMatchingEvent);
            handled = true;
            break;

        default:
            break;
    }
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(0 != lookupManager);
    lookupManager->handleLookupFinishedInForm(data);
    if (!handled)
    {
        //user use cancel, or error ocured:
        if (!lookupManager->stocks.empty() && preferences_->noPortfolio!=preferences_->lastDownloadedPortfolio)
        {
            //was some data, so switch back to that data
            preferences_->currentPortfolio = preferences_->lastDownloadedPortfolio;
            updateStocks();
        }
        else
        {
            //no data? - so user use cancel or sth when downloading data
            //we need to close form
            doneButton_.hit();
        }
    }    
}

void StocksMainForm::handleListItemSelect(uint_t listId, uint_t itemId)
{
    LookupManager* lookupManager = application().lookupManager;
    if (itemId >= lookupManager->stocks.getItemsCount())
        return;
    if (stocksListNotFoundElementsCount == lookupManager->stocks.getItemElementsCount(itemId))
    {
        //no symbol
        byNameDownloadingStockIndex_ = itemId;
        lookupManager->fetchStocksByName(lookupManager->stocks.getItemText(itemId,stocksListItemUrlIndex));
    }
    else
    {
        //download stock informations
        if (currentStockIndex_ == itemId)
            showStock();
        else
        {
            downloadingStockIndex_ = itemId;
            lookupManager->fetchStock(lookupManager->stocks.getItemText(itemId,stocksListItemUrlIndex));
        }
    }
}

bool StocksMainForm::handleKeyPress(const EventType& event)
{
    bool handled = stocksList_.handleKeyDownEvent(event, List::optionFireListSelectOnCenter);
    return handled;
}

void StocksMainForm::updateTitle(void)
{
    DynStr *title = DynStrFromCharP(_T("Stocks - "), 32);
    if (NULL == title)
        return;

    if (preferences_->noPortfolio != preferences_->lastDownloadedPortfolio)
        DynStrAppendCharP(title, preferences_->portfolios[preferences_->lastDownloadedPortfolio]->name.c_str());
    else
        DynStrAppendCharP(title,_T("press update"));
    setTitle(DynStrGetCStr(title));
    DynStrDelete(title);
}
