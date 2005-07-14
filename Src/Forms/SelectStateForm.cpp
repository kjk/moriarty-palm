
#include "SelectStateForm.hpp"
#include "MoriartyPreferences.hpp"
#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"
#include <SysUtils.hpp>
#include <USStates.hpp>
#include <InternationalCountryCodes.hpp>
#include <Text.hpp>

enum {
    stocksByNameItemUrlIndex,
    stocksByNameItemSymbolIndex,
    stocksByNameItemNameIndex,
    stocksByNameItemMarketIndex,
    stocksByNameItemIndustryIndex,
    stocksByNameElementsCount
};

class StatesListDrawHandler: public ExtendedList::CustomDrawHandler  
{
    UniversalDataFormat* udf_;
    Preferences::StocksPreferences* sPrefs_;

public: 
        
    enum Mode
    {
        stateMode,
        internationalMode,
        businessSearchByUrlMode,
        stocksPortfolioMode,
        stocksNameMatchingMode
    };
    
private:

    Mode mode_;
    
public:

    StatesListDrawHandler(): mode_(stateMode)
    {}

    StatesListDrawHandler(Mode mode): mode_(mode)
    {
        if (businessSearchByUrlMode == mode)
        {
            MoriartyApplication& app=MoriartyApplication::instance();
            LookupManager* lookupManager=app.lookupManager;
            assert(NULL!=lookupManager);
            udf_ = &lookupManager->tempUDF;
        }        
        else if (stocksPortfolioMode == mode)
        {
            sPrefs_ = &MoriartyApplication::instance().preferences().stocksPreferences;
        }
        else if (stocksNameMatchingMode == mode)
        {
            MoriartyApplication& app=MoriartyApplication::instance();
            LookupManager* lookupManager=app.lookupManager;
            assert(NULL!=lookupManager);
            udf_ = &lookupManager->tempUDF;
            sPrefs_ = &MoriartyApplication::instance().preferences().stocksPreferences;
        }            
    }

    void drawStateItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
    {
        uint_t      width = itemBounds.width();
        char_t *    textSymbol;
        char_t *    textName;

        assert(item < getStatesCount());

        textSymbol = getStateSymbol(item);
        textName = getStateName(item);
        uint_t length = tstrlen(textName);
        graphics.charsInWidth(textName, length, width);
        graphics.drawText(textName, length, itemBounds.topLeft);
        width = itemBounds.width();
        length = tstrlen(textSymbol);
        graphics.charsInWidth(textSymbol, length, width);
        Point rightText;
        rightText.x = itemBounds.x() + itemBounds.width();
        rightText.y = itemBounds.y();
        rightText.x -= width + 2; //+2 just to be nice
        graphics.drawText(textSymbol, length, rightText);
    }

    void drawCountryItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
    {
        assert(item < getCountryCodesCount());
        uint_t width=itemBounds.width();
        const char_t* textSymbol = getCountryCode(item);
        const char_t* textName = getCountryName(item);
        uint_t length = tstrlen(textName);
        graphics.charsInWidth(textName, length, width);
        graphics.drawText(textName, length, itemBounds.topLeft);
        width = itemBounds.width();
        length = tstrlen(textSymbol);
        graphics.charsInWidth(textSymbol, length, width);
        Point rightText;
        rightText.x = itemBounds.x() + itemBounds.width();
        rightText.y = itemBounds.y();
        rightText.x -= width + 2; //+2 just to be nice
        graphics.drawText(textSymbol, length, rightText);
    }

    void drawBusinessItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
    {
        assert(item < udf_->getItemsCount());
        uint_t width=itemBounds.width();
        String textName = udf_->getItemText(item,0);
        uint_t length=textName.length();
        graphics.charsInWidth(textName.c_str(), length, width);
        graphics.drawText(textName.c_str(), length, itemBounds.topLeft);
    }

    void drawPortfolioItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
    {
        assert(item < sPrefs_->portfoliosCount());
        uint_t width=itemBounds.width();
        String textName = sPrefs_->portfolios[item]->name;
        uint_t length=textName.length();
        graphics.stripToWidthWithEllipsis(textName, length, width, false);
        graphics.drawText(textName.c_str(), length, itemBounds.topLeft);
    }

    void drawStockMatchItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
    {
        assert(item < udf_->getItemsCount());
        uint_t width=itemBounds.width();
        String textName = udf_->getItemText(item,stocksByNameItemNameIndex);
        uint_t length=textName.length();
        graphics.stripToWidthWithEllipsis(textName, length, width);
        graphics.drawText(textName.c_str(), length, itemBounds.topLeft);

        Point newPoint = itemBounds.topLeft;
        newPoint.y += itemBounds.height()/2;
        width=itemBounds.width();
        textName.assign(udf_->getItemText(item,stocksByNameItemSymbolIndex));
        length=textName.length();
        graphics.charsInWidth(textName.c_str(), length, width);
        graphics.drawText(textName.c_str(), length, newPoint);

        width=itemBounds.width() - width - 8;
        textName.assign(udf_->getItemText(item,stocksByNameItemMarketIndex));
        textName.append(_T(" "));
        textName.append(udf_->getItemText(item,stocksByNameItemIndustryIndex));
        strip(textName);
        length=textName.length();
        graphics.charsInWidth(textName.c_str(), length, width);
        newPoint.x = itemBounds.x() + itemBounds.width() - width;
        graphics.drawText(textName.c_str(), length, newPoint);
    }

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
    {
        switch(mode_)
        {
            case stateMode:
                drawStateItem(graphics, list, item, itemBounds);
                break;
            case internationalMode:
                drawCountryItem(graphics, list, item, itemBounds);
                break;
            case businessSearchByUrlMode:
                drawBusinessItem(graphics, list, item, itemBounds);
                break;
            case stocksPortfolioMode:
                drawPortfolioItem(graphics, list, item, itemBounds);
                break;
            case stocksNameMatchingMode:
                drawStockMatchItem(graphics, list, item, itemBounds);
                break;
        }
    }
    
    uint_t itemsCount() const
    {
        switch(mode_)
        {
            case stateMode:
                return getStatesCount();
            case internationalMode:
                return getCountryCodesCount();
            case businessSearchByUrlMode:
                return udf_->getItemsCount();
            case stocksPortfolioMode:
                return sPrefs_->portfoliosCount();
            case stocksNameMatchingMode:
                return udf_->getItemsCount();
        }
        return 0;
    }
    
    ~StatesListDrawHandler()
    {}        
};

SelectStateForm::SelectStateForm(MoriartyApplication& app):
    MoriartyForm(app, selectStateForm, true),
    statesList_(*this),
    okButton_(*this),
    cancelButton_(*this),
    okMode_(statesMode)    
{
    statesListDrawHandler_.reset(new StatesListDrawHandler());
    setFocusControlId(statesList);
}
    
SelectStateForm::~SelectStateForm()
{}

void SelectStateForm::attachControls()
{
    MoriartyForm::attachControls();
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);

    statesList_.attach(statesList);
    statesList_.setUpBitmapId(upBitmap); 
    statesList_.setDownBitmapId(downBitmap); 
    statesList_.setItemHeight(12);
}

bool SelectStateForm::handleOpen()
{
    bool res=MoriartyForm::handleOpen();
    assert(NULL!=statesListDrawHandler_.get());
    statesList_.setCustomDrawHandler(statesListDrawHandler_.get());

    LookupManager* lm=application().lookupManager;
    assert(NULL!=lm);
    int sel = lm->getSelectedState();
    if (sel >= 0 && sel < getStatesCount())
    {
        statesList_.setSelection(sel);
        if (sel >= statesList_.visibleItemsCount())
        {
            if (sel > statesList_.itemsCount() - statesList_.visibleItemsCount())
                sel = statesList_.itemsCount() - statesList_.visibleItemsCount();
            statesList_.setTopItem(sel);
        }        
    }
    else
        statesList_.setSelection(0);
    return res;
}

void SelectStateForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(screenBounds);
    bounds.explode(2, 2, -4, -4);        
    setBounds(bounds);
    
    statesList_.anchor(screenBounds, anchorRightEdge, 4, anchorBottomEdge, 40);
    okButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    cancelButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);

    update();
}

bool SelectStateForm::handleEvent(EventType& event)
{
    bool handled=false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelected(event);
            handled=true;
            break;
            
        case lstSelectEvent:
            assert(statesList==event.data.lstSelect.listID);
            okButton_.hit();
            handled=true;
            break;
        
        case MoriartyApplication::app411SetInternationalCodeEvent:
            okMode_ = internationalCodeMode;
            setTitle(_T("Select Country"));
            statesList_.setSelection(0);
            statesListDrawHandler_.reset(new StatesListDrawHandler(StatesListDrawHandler::internationalMode));
            statesList_.setCustomDrawHandler(statesListDrawHandler_.get());
            statesList_.setSelection(0);
            statesList_.setTopItem(0);
            statesList_.adjustVisibleItems();
            update();
            handled = true;
            break;    

        case MoriartyApplication::app411SetBusinessMultiselectEvent:
            okMode_ = businessSearchByUrlMode;
            setTitle(_T("Select category"));
            statesList_.setSelection(0);
            statesListDrawHandler_.reset(new StatesListDrawHandler(StatesListDrawHandler::businessSearchByUrlMode));
            statesList_.setCustomDrawHandler(statesListDrawHandler_.get());
            statesList_.setSelection(0);
            statesList_.setTopItem(0);
            statesList_.adjustVisibleItems();
            update();
            handled = true;
            break;    
        
        case MoriartyApplication::appSetStocksPortfolioEvent:
            okMode_ = stocksPortfolioMode;
            setTitle(_T("Select portfolio"));
            statesList_.setSelection(0);
            statesListDrawHandler_.reset(new StatesListDrawHandler(StatesListDrawHandler::stocksPortfolioMode));
            statesList_.setCustomDrawHandler(statesListDrawHandler_.get());
            statesList_.setSelection(0);
            statesList_.setTopItem(0);
            statesList_.adjustVisibleItems();
            update();
            handled = true;
            break;    

        case MoriartyApplication::appSetStocksNameMatchingEvent:
            okMode_ = stocksNameMatchingMode;
            setTitle(_T("Select stock"));
            statesList_.setItemHeight(statesList_.itemHeight()*2);
            statesList_.setSelection(0);
            statesListDrawHandler_.reset(new StatesListDrawHandler(StatesListDrawHandler::stocksNameMatchingMode));
            statesList_.setCustomDrawHandler(statesListDrawHandler_.get());
            statesList_.setSelection(0);
            statesList_.setTopItem(0);
            statesList_.adjustVisibleItems();
            update();
            handled = true;
            break;    
            
        case keyDownEvent: 
            {
                int option = List::optionScrollPagesWithLeftRight;
                if (application().runningOnTreo600())
                    option = 0;
                handled=statesList_.handleKeyDownEvent(event, option | List::optionFireListSelectOnCenter);
            }
            if (handled)
                break;
            if (256 > event.data.keyDown.chr && isAlpha(event.data.keyDown.chr))
            {
                int newIndex;
                switch (okMode_)
                {
                    case statesMode:
                        newIndex = getIndexByFirstChar(event.data.keyDown.chr);
                        break;
                    case internationalCodeMode:
                        newIndex = getCountryIndexByFirstChar(event.data.keyDown.chr);
                        break;
                    default:
                        return true;
                }
                statesList_.setSelection(newIndex);
                if (newIndex > statesList_.itemsCount() - statesList_.visibleItemsCount())
                    newIndex = statesList_.itemsCount() - statesList_.visibleItemsCount();
                statesList_.setTopItem(newIndex, ExtendedList::redraw);
                handled = true;
                break;
            }
            
            // watch out for fall through here!
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

void SelectStateForm::handleControlSelected(const EventType& event)
{
    switch (event.data.ctlSelect.controlID) 
    {
        case okButton:
            int sel=statesList_.selection();
            if (noListSelection!=sel)
            {
                String countryCode;
                MoriartyApplication& app=application();
                LookupManager* lm=app.lookupManager;
                assert(NULL!=lm);
                switch (okMode_)
                {   
                    case statesMode:
                        assert(sel < getStatesCount());
                        lm->setSelectedState(sel);
                        sendEvent(MoriartyApplication::appStateWasSelectedEvent);
                        break;
                    case internationalCodeMode:
                        assert(sel < getCountryCodesCount());
                        lm->fetchInternationalCode(sel);
                        break;
                    case businessSearchByUrlMode:
                        assert(sel < lm->tempUDF.getItemsCount());
                        lm->fetchBusinessDataByUrl(lm->tempUDF.getItemText(sel,1));
                        break;
                        
                    case stocksPortfolioMode:
                        Preferences::StocksPreferences* prefs = &app.preferences().stocksPreferences;
                        assert(sel < prefs->portfoliosCount());
                        if (prefs->currentPortfolio != sel)
                        {
                            prefs->currentPortfolio = sel;
                            lm->fetchStocksList(join(prefs->portfolios[sel]->symbols,_T(";")));
                        }                        
                        break;

                    case stocksNameMatchingMode:    
                        {
                            Preferences::StocksPreferences* prefs = &app.preferences().stocksPreferences;
                            std::vector<String> vec = prefs->portfolios[prefs->lastDownloadedPortfolio]->symbols;
                            if (prefs->lastDownloadedStock == vec.size())
                                vec.push_back(_T("ss"));
                            assert(prefs->lastDownloadedStock < vec.size());
                            vec[prefs->lastDownloadedStock] = lm->tempUDF.getItemText(sel,stocksByNameItemSymbolIndex);
                            lm->fetchStocksList(join(vec,_T(";")));
                        }
                        break;
                }
            }
            closePopup();
            break;
                        
        case cancelButton:
            closePopup();
            if (stocksPortfolioMode == okMode_)
                sendEvent(lookupResultConnectionCancelledByUser);
            break;
                        
        default:
            assert(false);
    }
}
