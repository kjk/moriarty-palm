#include "TvListingsMainForm.hpp"
#include "MoriartyPreferences.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include "StringSelectForm.hpp"

enum {
    providerIdIndex,
    providerNameIndex
};

TvListingsMainForm::TvListingsMainForm(MoriartyApplication& app):
    MoriartyForm(app, tvListingsMainForm),
    horizScrollBar_(*this),
    vertScrollBar_(*this),
    doneButton_(*this),
    displayMode_(showGrid)
 {
    setFocusControlId(doneButton);
}

TvListingsMainForm::~TvListingsMainForm() {}

void TvListingsMainForm::attachControls()
{
    MoriartyForm::attachControls();
    horizScrollBar_.attach(tvGridHorizScrollBar);
    vertScrollBar_.attach(tvGridVertScrollBar);
    
    doneButton_.attach(doneButton);
}

bool TvListingsMainForm::handleOpen()
{
    bool result=MoriartyForm::handleOpen();
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL != lookupManager);
    Preferences::TvListingsPreferences& prefs = app.preferences().tvListingsPreferences;
    if (prefs.zipCode.empty())
    {
        prefs.zipCode = "98101";
    }
    if (prefs.providerIdInvalid == prefs.providerId)
    {
        if (lookupManager->tvProviders.empty())
        {
            assert(!prefs.zipCode.empty());
            lookupManager->fetchTvProviders(prefs.zipCode);
        }
        else
            selectProvider(lookupManager->tvProviders);
    }
/*    
    if (!lookupManager->dream.empty())
        setDisplayMode(showGrid);
    else
        setDisplayMode(displayMode_);
 */
 
    return result;
}

void TvListingsMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(bounds = screenBounds);

/*    
    dreamRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);
    
    doneButton_.bounds(bounds);
    bounds.y()=screenBounds.height()-14;
    doneButton_.setBounds(bounds);

    dreamNameField_.bounds(bounds);
    bounds.y()=screenBounds.height()-14;
    bounds.width()=screenBounds.width()-94;
    dreamNameField_.setBounds(bounds);

    searchButton_.bounds(bounds);
    bounds.y()=screenBounds.height()-14;
    bounds.x()=screenBounds.width()-44;
    searchButton_.setBounds(bounds);
    
    graffitiState_.bounds(bounds);
    bounds.y() = screenBounds.height() - 13;
    bounds.x() = screenBounds.width() - 55;
    graffitiState_.setBounds(bounds);
    
    helpText1Label_.bounds(bounds);
    bounds.y() = screenBounds.height() - 53;
    helpText1Label_.setBounds(bounds);
    
    helpText2Label_.bounds(bounds);
    bounds.y() = screenBounds.height() - 41;
    helpText2Label_.setBounds(bounds);

    helpText3Label_.bounds(bounds);
    bounds.y() = screenBounds.height() - 29;
    helpText3Label_.setBounds(bounds);
 */
    update();    
}

bool TvListingsMainForm::handleEvent(EventType& event)
{
/*
    if (showGrid == displayMode_ && tvGrid_.handleEventInForm(event))
        return true;
 */
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
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool TvListingsMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled=false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            handled = true;
            break;

        default:
            assert(false);
    }
    return handled;
}

void TvListingsMainForm::setDisplayMode(DisplayMode dm)
{
    displayMode_ = dm;
    switch (dm)
    {
        case showGrid:
/*        
            if (dreamRenderer_.empty())
                prepareDream();
            
            tvGrid_.show();
 */                
            horizScrollBar_.show();
            vertScrollBar_.show();
            break;  
            
        default:
            assert(false);
    }
}

void TvListingsMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;
            
        default:
            assert(false);
    }
}

void TvListingsMainForm::handleLookupFinished(const EventType& event)
{
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL != lookupManager);
    const LookupFinishedEventData& data = reinterpret_cast<const LookupFinishedEventData&>(event.data);
    switch (data.result)
    {
        case lookupResultTvProviders:
            selectProvider(lookupManager->tvProviders);
            break;
            
/*
        case lookupResultDreamData:
            prepareDream();
            if (showDream != displayMode_)
                setDisplayMode(showDream);
            update();
            MoriartyApplication::touchModule(moduleIdDreams);
            break;
 */
    }
    lookupManager->handleLookupFinishedInForm(data);
}

bool TvListingsMainForm::handleKeyPress(const EventType& event)
{
    bool handled = false;
    switch (event.data.keyDown.chr)
    {
/*
        case chrLineFeed:
        case chrCarriageReturn:
            searchButton_.hit();
            handled=true;
*/
    }
    return handled;
}

class TvProvidersListRenderer: public BasicStringItemRenderer
{
    const UniversalDataFormat& providers_;
public:
    TvProvidersListRenderer(const UniversalDataFormat& providers): providers_(providers) {}
    
    uint_t itemsCount() const {return providers_.getItemsCount();}

protected:

    void getItem(String& out, uint_t item)
    {
        assert(item < providers_.getItemsCount());
        out = providers_.getItemText(item, providerNameIndex);
    }
};

void TvListingsMainForm::selectProvider(const UniversalDataFormat& providers)
{
    ExtendedList::ItemRenderer* renderer = new TvProvidersListRenderer(providers);
    StringSelectForm* selectForm = new StringSelectForm(MoriartyApplication::appSelectTvProviderEvent, _T("Choose your provider"));
    selectForm->setItemRenderer(renderer, StringSelectForm::rendererOwner);
    selectForm->popup();
}
