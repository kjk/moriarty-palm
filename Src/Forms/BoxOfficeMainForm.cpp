#include "BoxOfficeMainForm.hpp"
#include "LookupManager.hpp"
#include <SysUtils.hpp>
#include <algorithm>
#include <UniversalDataHandler.hpp>
#include <Text.hpp>
#include <Graphics.hpp>

#if defined(__MWERKS__)
# pragma far_code
#endif

// indexes in UDF
#define lastWeekPosIndexInUDF 0
#define titleIndexInUDF 1
#define weekGrossIndexInUDF 2
#define cumulativeGrossIndexInUDF 3
#define releaseWeeksIndexInUDF 4
#define theatersNumberIndexInUDF 5
#define abbrevGrossIndexInUDF 6

#define moviesListItemLines 2
#define moviesListLineHeight 12

class MoviesListDrawHandler: public ExtendedList::ItemRenderer {

    UniversalDataFormat* results_;
   
public:

    MoviesListDrawHandler(UniversalDataFormat* res):
        results_(res) {}
        
    uint_t itemsCount() const
    { 
        return results_->getItemsCount();
    }

    ~MoviesListDrawHandler();

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);

};

MoviesListDrawHandler::~MoviesListDrawHandler()
{}

#define MARGIN_LEFT 2

void MoviesListDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    uint_t width = itemBounds.width();
    uint_t displayWidth = width;

    char_t buffer[32];
    formatNumber(item+1, buffer, 32);

    String text;
    text.assign(buffer);
    text.append(_T(". "));
    text.append(results_->getItemText(item, titleIndexInUDF));
    uint_t length=text.length();

    Point newTop = itemBounds.topLeft;
    newTop.x += MARGIN_LEFT;

    graphics.charsInWidth(text.c_str(), length, width);
    graphics.drawText(text.c_str(), length, newTop);

    newTop = itemBounds.topLeft;
    newTop.x += MARGIN_LEFT;
    newTop.y += itemBounds.height()/moviesListItemLines;

    width = displayWidth;
    //text.assign(_T("Gross: "));
    text.assign(results_->getItemText(item,abbrevGrossIndexInUDF));
    localizeNumber(text);
    text.append(_T(" (week/total)"));
    length = text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    graphics.drawText(text.c_str(), length, newTop);

    /*newTop = itemBounds.topLeft;
    newTop.y += itemBounds.height()*2/moviesListItemLines;
    width = displayWidth;
    text.assign(_T("Total gross: "));
    text.append(results_->getItemText(item,cumulativeGrossIndexInUDF));
    text.append(_T("$"));
    length=text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    graphics.drawText(text.c_str(), length, newTop);*/
}

BoxOfficeMainForm::~BoxOfficeMainForm()
{
}

BoxOfficeMainForm::BoxOfficeMainForm(MoriartyApplication& app):
    MoriartyForm(app, boxOfficeMainForm),
    resultsList_(*this),
    doneButton_(*this),
    updateButton_(*this)
{
    setFocusControlId(resultsList);
}

void BoxOfficeMainForm::attachControls()
{
    MoriartyForm::attachControls();
    resultsList_.attach(resultsList);
    resultsList_.setItemHeight(moviesListItemLines*moviesListLineHeight);
    resultsList_.setUpBitmapId(upBitmap);
    resultsList_.setDownBitmapId(downBitmap);

    doneButton_.attach(doneButton);
    updateButton_.attach(updateButton);
}

#define getCurrentBoxOfficeField _T("Get-Current-Box-Office")

bool BoxOfficeMainForm::handleOpen()
{
    bool res = MoriartyForm::handleOpen();
    
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL!=lookupManager);
    this->boxOfficeData_ = &lookupManager->boxOfficeData;

    resultsList_.setCustomDrawHandler(moviesListDrawHandler_.get());

    if (0 == lookupManager->boxOfficeData.getItemsCount())
        lookupManager->fetchField(getCurrentBoxOfficeField, NULL);
    else
        updateAfterLookup(*lookupManager);
    updateButton_.show();
    doneButton_.show();
    update();
    return res;
}

#define BUTTON_DY 12
void BoxOfficeMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(screenBounds);
    bounds=screenBounds;
    bounds.explode(0, 17, 0, -37);

    resultsList_.setBounds(bounds);
    resultsList_.adjustVisibleItems();

    doneButton_.bounds(bounds);
    bounds.y() = screenBounds.dy()-BUTTON_DY-2;
    bounds.x() = 2;
    doneButton_.setBounds(bounds);
    ArsRectangle doneBounds(bounds);

    updateButton_.bounds(bounds);
    bounds.y()=doneBounds.y();
    bounds.x()=doneBounds.x() + doneBounds.dx() + 4;
    updateButton_.setBounds(bounds);

    update();
}

void BoxOfficeMainForm::draw(UInt16 updateCode)
{
    Graphics graphics(windowHandle());
    ArsRectangle rect(bounds());
    if (redrawAll==updateCode)
    {
        MoriartyForm::draw(updateCode);
    }
}

void BoxOfficeMainForm::handleControlSelect(const EventType& event)
{
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL!=lookupManager);

    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
                application().runMainForm();
                break;            

        case updateButton:
                lookupManager->fetchField(getCurrentBoxOfficeField, NULL);
                break;            

        default:
            assert(false);
    }
}

inline void BoxOfficeMainForm::setControlsState(bool enabled)
{
    doneButton_.setEnabled(enabled);
    updateButton_.setEnabled(enabled);
}

void BoxOfficeMainForm::updateAfterLookup(LookupManager& lookupManager)
{
    boxOfficeData_ = &lookupManager.boxOfficeData;
    moviesListDrawHandler_.reset(new MoviesListDrawHandler(boxOfficeData_));
    resultsList_.setCustomDrawHandler(moviesListDrawHandler_.get());
    resultsList_.notifyItemsChanged();
    resultsList_.setSelection(0, ExtendedList::redraw);
    resultsList_.show();

    update();    
}

void BoxOfficeMainForm::handleLookupFinished(const EventType& event)
{
    bool closeForm = false;
    setControlsState(true);
    
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL!=lookupManager);
    
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    if (lookupResultBoxOfficeData == data.result)
    {
        updateAfterLookup(*lookupManager);
        MoriartyApplication::touchModule(moduleIdBoxOffice);
    }
    else
        closeForm = true;
    lookupManager->handleLookupFinishedInForm(data);
    update();
    if (closeForm && lookupManager->boxOfficeData.empty())
        application().runMainForm();
}

bool BoxOfficeMainForm::handleEvent(EventType& event)
{
    bool handled=false;
    switch (event.eType)
    {
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;

        case ctlSelectEvent:
            handleControlSelect(event);
            break;
               
        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled = true;
            break;     
            
        //case lstSelectEvent:
            //handleListItemSelect(event.data.lstSelect.listID, event.data.lstSelect.selection);
            //break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool BoxOfficeMainForm::handleKeyPress(const EventType& event)
{
    ExtendedList& list = resultsList_;
    if (list.handleKeyDownEvent(event, ExtendedList::optionFireListSelectOnCenter))
        return true;
    return false;
}

bool BoxOfficeMainForm::handleMenuCommand(UInt16 itemId)
{
    bool    handled;
    switch (itemId)
    {
        case mainPageMenuItem:
             doneButton_.hit();
             handled = true;
             break;
        case updateBoxOfficeList:
             updateButton_.hit();
             handled = true;
             break;
        default:
            handled = MoriartyForm::handleMenuCommand(itemId);
            break;
    }
    return handled;
}
