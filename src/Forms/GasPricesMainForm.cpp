#include <SysUtils.hpp>
#include <Text.hpp>
#include <DynStr.hpp>

#include <Definition.hpp>
#include <TextElement.hpp>
#include <LineBreakElement.hpp>

#include "LookupManager.hpp"
#include "Forms/SimpleTextDoneForm.hpp"
#include "GasPricesMainForm.hpp"

enum {
    gasListItemPriceIndex,
    gasListItemNameIndex,
    gasListItemAddressIndex,
    gasListItemAreaIndex,
    gasListItemTimeIndex,
    gasListElementsCount
};

class GasListDrawHandler: public BasicStringItemRenderer {

    UniversalDataFormat* listUDF_;
    Preferences::GasPricesPreferences* prefs_;
    
public:
    
    explicit GasListDrawHandler(UniversalDataFormat* udf, Preferences::GasPricesPreferences* prefs): listUDF_(udf), prefs_(prefs) {}
    
    uint_t itemsCount() const
    {
        return listUDF_->getItemsCount();
    }

    ~GasListDrawHandler();

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);
    
protected:
    
    void getItem(String& out, uint_t item)
    {
        out.assign(listUDF_->getItemText(item, gasListItemPriceIndex));
    }
    
};

GasListDrawHandler::~GasListDrawHandler() {}

#define LEFT_MARGIN 2

void GasListDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    uint_t width = itemBounds.width();
    String text = _T("$");
    text += listUDF_->getItemText(item, gasListItemPriceIndex);
    localizeNumber(text);
    uint_t length = text.length();
    graphics.charsInWidth(text.c_str(), length, width);

    Point p = itemBounds.topLeft;
    p.x += LEFT_MARGIN;
    graphics.drawText(text.c_str(), length, p);

    ulong_t lengthLong;
    const char_t *name = listUDF_->getItemTextAndLen(item, prefs_->afterPriceIndex, &lengthLong);
    length = lengthLong;

    Point newRight = itemBounds.topLeft;
    newRight.x += width+10;
    width = itemBounds.width() - width - 10;
    graphics.charsInWidth(name, length, width);
    graphics.drawText(name, length, newRight);
}

GasPricesMainForm::GasPricesMainForm(MoriartyApplication& app):
    MoriartyForm(app, gasPricesMainForm),
    gasList_(*this),
    doneButton_(*this),
    changeLocationButton_(*this),
    updateButton_(*this)
{
    setFocusControlId(gasList);
}

GasPricesMainForm::~GasPricesMainForm() {}

void GasPricesMainForm::attachControls()
{
    MoriartyForm::attachControls();
    doneButton_.attach(doneButton);
    updateButton_.attach(updateButton);
    changeLocationButton_.attach(changeLocationButton);

    gasList_.attach(gasList);
    gasList_.setUpBitmapId(upBitmap);
    gasList_.setDownBitmapId(downBitmap);

    gasList_.setItemHeight(12);
}

bool GasPricesMainForm::handleOpen()
{
    bool result=MoriartyForm::handleOpen();
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(0!=lookupManager);
    
    preferences_ = &app.preferences().gasPricesPreferences;
    gasList_.setChangeSelectionNotification(true); //this should be after this, to avoid crush

    setVersion((Preferences::GasPricesPreferences::Version)preferences_->version);
    if (lookupManager->gasPrices.empty())
    {
        Application::popupForm(m411EnterZipForm);
        sendEvent(MoriartyApplication::appSetGasPriceEvent);
    }
    else
    {
        updateGasList();
    }
    return result;
}

void GasPricesMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    setBounds(bounds = screenBounds);

    // version
    switch (preferences_->version)
    {
        case preferences_->popupVersion:
            gasList_.anchor(screenBounds, anchorRightEdge, 0, anchorBottomEdge, 36);
            gasList_.adjustVisibleItems();
            break;
            
        case preferences_->downInfoVersion:
            gasList_.anchor(screenBounds, anchorRightEdge, 0, anchorBottomEdge, 60);
            {
                //make it fit to items heigth
                gasList_.bounds(bounds);
                int freeSpace = bounds.dy() % gasList_.itemHeight();
                bounds.dy()-=freeSpace;
                gasList_.setBounds(bounds);
            }
            gasList_.adjustVisibleItems();
            break;
    }

    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    updateButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    changeLocationButton_.anchor(screenBounds, anchorLeftEdge, 72, anchorTopEdge, 14);
    
    update();    
}

void GasPricesMainForm::updateGasList()
{
    LookupManager* lookupManager = application().lookupManager;
    assert(0!=lookupManager);
    gasListDrawHandler_.reset(new GasListDrawHandler(&lookupManager->gasPrices, preferences_));
    gasList_.setCustomDrawHandler(gasListDrawHandler_.get());
    gasList_.notifyItemsChanged();
    gasList_.setSelection(0);
    gasList_.show();
    updateTitle();
    update();
}

bool GasPricesMainForm::handleEvent(EventType& event)
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

        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled=  true;
            break;
            
        case ExtendedList::selChangedEvent:
            if (preferences_->downInfoVersion == preferences_->version)
                inlineInformation(gasList_.selection());
            handled = true;
            break;

        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool GasPricesMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled = true;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            break;
            
        case updateMenuItem:
            updateButton_.hit();
            break;

        case changeLocationMenuItem:
            changeLocationButton_.hit();
            break;

        case nameMenuItem:
            preferences_->afterPriceIndex = gasListItemNameIndex;
            update();
            break;
            
        case addressMenuItem:
            preferences_->afterPriceIndex = gasListItemAddressIndex;
            update();
            break;
            
        case areaMenuItem:
            preferences_->afterPriceIndex = gasListItemAreaIndex;
            update();
            break;
            
        case popupMenuItem:
            setVersion(preferences_->popupVersion);
            break;

        case inlineMenuItem:
            setVersion(preferences_->downInfoVersion);
            break;
            
        default:
            handled=false;
            assert(false);
    }
    return handled;
}

void GasPricesMainForm::handleUpdateButton()
{
    LookupManager* lm = application().lookupManager;
    assert(NULL != lm);
    lm->fetchField(getGasPricesField, preferences_->zipCode.c_str());
}

void GasPricesMainForm::handleChangeLocationButton()
{
    Application::popupForm(m411EnterZipForm);
    sendEvent(MoriartyApplication::appSetGasPriceEvent);
}

void GasPricesMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;
            
        case changeLocationButton:
            handleChangeLocationButton();
            break;
            
        case updateButton:
            handleUpdateButton();
            break;
            
        default:
            assert(false);
            break;
    }
}

void GasPricesMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    bool handled = false;
    switch (data.result)
    {
        case lookupResultGasPrices:
            updateGasList();
            handled = true;
            MoriartyApplication::touchModule(moduleIdGasPrices);
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
        if (lookupManager->gasPrices.empty())
        {
            //no data? - so user use cancel or sth when downloading data
            //we need to close form
            doneButton_.hit();
        }
    }    
}

void GasPricesMainForm::setVersion(Preferences::GasPricesPreferences::Version ver)
{
    preferences_->version = ver;
    resize(bounds());
}

void GasPricesMainForm::inlineInformation(uint_t item)
{
    if (!visible())
        return;
        
    enum 
    {
        minimumSpace = 10
    };
    
    //clear
    ArsRectangle informationBounds;
    ArsRectangle bounds;
    gasList_.bounds(bounds);
    informationBounds.x() = bounds.x();
    informationBounds.y() = bounds.y() + bounds.dy() + 2;
    informationBounds.dx() = bounds.dx();
    doneButton_.bounds(bounds);
    informationBounds.dy() = bounds.y() - informationBounds.y() - 1;
    Graphics graphics;
    //set area
    informationBounds.y() += 1;
    informationBounds.dy() -= 3;   
    informationBounds.x() += 1;
    informationBounds.dx() -= 2;
    
    RGBColorType oldBackColor;
    RGBColorType newBackColor;
    setRgbColor(newBackColor,255,255,127);    //yellow (light)
    WinSetBackColorRGB(&newBackColor, &oldBackColor);
    
    graphics.erase(informationBounds);

    informationBounds.x() += 1;
    informationBounds.dx() -= 2;

    if (noListSelection == item)
    {
        WinSetBackColorRGB(&oldBackColor, &newBackColor);
        return;
    }    
    //draw
    //we have 2 lines only...
    UniversalDataFormat* listUDF_ = &application().lookupManager->gasPrices;
    Point newPoint = informationBounds.topLeft;
    uint_t width;
    uint_t widthTaken = 0;
    String text;
    uint_t length;
    RGBColorType oldColor;
    RGBColorType newColor;
    setRgbColor(newColor,0,127,0);    
    int position = 0;

    // draw address (only address can take 2 lines (1st + pice of 2nd))
    if (gasListItemAddressIndex != preferences_->afterPriceIndex)
    {
        width = informationBounds.width();
        text = listUDF_->getItemText(item, gasListItemAddressIndex);
        length = text.length();
        graphics.charsInWidth(text.c_str(), length, width);
        graphics.drawText(text.c_str(), length, newPoint);
        newPoint.y += informationBounds.dy()/2;
        if (length < text.length())
        {
            String restOfText(text, length);
            width = informationBounds.width();
            length = restOfText.length();
            graphics.charsInWidth(restOfText.c_str(), length, width);
            graphics.drawText(restOfText.c_str(), length, newPoint);
            widthTaken = width;
        }
        position++; 
    }

    // draw name
    if (gasListItemNameIndex != preferences_->afterPriceIndex)
    {
        if (1 == position)
            WinSetTextColorRGB(&newColor, &oldColor);
        text = listUDF_->getItemText(item, gasListItemNameIndex);
        length = text.length();
        if (0 < widthTaken)
            widthTaken += minimumSpace; //set space
        width = informationBounds.width() - widthTaken;
        graphics.charsInWidth(text.c_str(), length, width);
        newPoint.x += widthTaken;
        graphics.drawText(text.c_str(), length, newPoint);
        widthTaken += width;
        if (newPoint.y == informationBounds.topLeft.y)
        {
            newPoint.y += informationBounds.dy()/2;
            widthTaken = 0;
        }
        if (1 == position)
            WinSetTextColorRGB(&oldColor, &newColor);
        position++; 
    }    
    
    // draw area
    if (gasListItemAreaIndex != preferences_->afterPriceIndex)
    {
        if (1 == position)
            WinSetTextColorRGB(&newColor, &oldColor);
        text = listUDF_->getItemText(item, gasListItemAreaIndex);
        length = text.length();
        if (0 < widthTaken)
            widthTaken += minimumSpace; //set space
        width = informationBounds.width() - widthTaken;
        graphics.charsInWidth(text.c_str(), length, width);
        newPoint.x += widthTaken;
        graphics.drawText(text.c_str(), length, newPoint);
        widthTaken += width;
        if (1 == position)
            WinSetTextColorRGB(&oldColor, &newColor);
    }    

    // draw time
    {
        width = informationBounds.width() - widthTaken;
        if (minimumSpace < width)
        {
            width -= minimumSpace;
            text = listUDF_->getItemText(item, gasListItemTimeIndex);
            length = text.length();
            graphics.charsInWidth(text.c_str(), length, width);
            if (length >= text.length())
            {
                newPoint.x = informationBounds.x() + informationBounds.dx() - width;
                graphics.drawText(text.c_str(), length, newPoint);
            }
        }
    }
    //restore background color
    WinSetBackColorRGB(&oldBackColor, &newBackColor);
}

void GasPricesMainForm::popupFormInformation(uint_t item)
{
    (new SimpleTextDoneForm(application(), SimpleTextDoneForm::showGasPricesDetails, item))->popup();
}

void GasPricesMainForm::handleListItemSelect(uint_t listId, uint_t itemId)
{
    LookupManager* lookupManager = application().lookupManager;
    //version!!!
    switch (preferences_->version)
    {
        case preferences_->popupVersion:
            popupFormInformation(itemId);
            break;
            
        case preferences_->downInfoVersion:
            inlineInformation(itemId);
            break;
    }
}

bool GasPricesMainForm::handleKeyPress(const EventType& event)
{
    bool handled = gasList_.handleKeyDownEvent(event, List::optionFireListSelectOnCenter);
    return handled;
}

void GasPricesMainForm::updateTitle(void)
{    
    DynStr *title = DynStrFromCharP3(_T("Gas Prices for '"), preferences_->zipCode.c_str(), _T("\'"));
    if (NULL == title)
        return;
    setTitle(DynStrGetCStr(title));
    DynStrDelete(title);
}

void GasPricesMainForm::draw(UInt16 updateCode)
{
    Graphics graphics(windowHandle());
    ArsRectangle rect;
    bounds(rect);
    if (redrawAll==updateCode)
    {
        MoriartyForm::draw(updateCode);
        if (preferences_->downInfoVersion == preferences_->version)
            inlineInformation(gasList_.selection());
    }
}

