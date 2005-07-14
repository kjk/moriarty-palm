#include "FlightsMainForm.hpp"
#include "MoriartyPreferences.hpp"
#include <SysUtils.hpp>
#include "LookupManager.hpp"
#include <Definition.hpp>
#include <Text.hpp>
#include <ByteFormatParser.hpp>

#pragma pcrelconstdata on

FlightsMainForm::FlightsMainForm(MoriartyApplication& app):
    MoriartyForm(app, flightsMainForm),
    updateButton_(*this),
    doneButton_(*this),
    searchButton_(*this),
    scrollBar_(*this),
    textRenderer_(*this, &scrollBar_)
{
    textRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    textRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    
    setupPopupMenu(linkPopupMenu, MoriartyApplication::extEventShowMenu, app.hyperlinkHandler);
}

FlightsMainForm::~FlightsMainForm() {}

void FlightsMainForm::attachControls()
{
    MoriartyForm::attachControls();
    updateButton_.attach(updateButton);
    doneButton_.attach(doneButton);
    searchButton_.attach(searchButton);
    scrollBar_.attach(definitionScrollBar);
    textRenderer_.attach(textRenderer);
    textRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
}


bool FlightsMainForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();

    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL!=lookupManager);

    if (lookupManager->crossModuleLookup)
        showMain();
    else
        readUdf();
    return result;
}

void FlightsMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(bounds=screenBounds);

    textRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    updateButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    searchButton_.anchor(screenBounds, anchorLeftEdge, 44, anchorTopEdge, 14);
    update();    
}

bool FlightsMainForm::handleEvent(EventType& event)
{
    if (textRenderer_.handleEventInForm(event))
        return true;
        
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelect(event);
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

bool FlightsMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled=false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            handled=true;
            break;
            
        case searchMenuItem:
            searchButton_.hit();
            handled=true;
            break;
    }
    return handled;
}

void FlightsMainForm::showMain()
{
    updateButton_.hide();
    UInt32  dataLen;
    char* data = getDataResource(flightsStartPageText, &dataLen);
    if (NULL == data)
        return;

    ByteFormatParser parser;
    parser.parseAll(data, dataLen);
    assert(NULL != data);
    free(data);
    
    DefinitionModel* model = parser.releaseModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    textRenderer_.setModel(model, Definition::ownModel);
    update();
}

void FlightsMainForm::readUdf()
{
    updateButton_.hide();
    UniversalDataFormat* udf = &application().lookupManager->flightsData;
    if (udf->empty())
    {
        showMain();
        return;
    }
    
    for (int i=0; i < udf->getItemsCount(); i++)
    {
        switch (udf->getItemText(i,0)[0])
        {
            case _T('D'): //definition
                {
                    ByteFormatParser parser;
                    ulong_t dataLen;
                    const char_t *data = udf->getItemTextAndLen(i, 1, &dataLen);
                    parser.parseAll(data, dataLen);
                    DefinitionModel* model = parser.releaseModel();
                    if (NULL == model)
                    {
                        application().alert(notEnoughMemoryAlert);
                        return;
                    }
                    textRenderer_.setModel(model, Definition::ownModel);
                }
                break;

            case _T('U'):
                {
                    updateString_.assign(udf->getItemText(i,1));
                    updateButton_.show();
                }
                break;
            default:
                assert(false);
                break;
        }
    }
    update();
}

void FlightsMainForm::handleSearch()
{
    Application::popupForm(flightsSearchForm);
}

void FlightsMainForm::handleUpdateButton()
{
    assert(!updateString_.empty());
    LookupManager* lookupManager = application().lookupManager;
    assert(NULL!=lookupManager);
    lookupManager->fetchUrl(updateString_.c_str());
}

void FlightsMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;
            
        case searchButton:
            handleSearch();
            break;

        case updateButton:
            handleUpdateButton();
            break;
            
        default:
            assert(false);
    }
}

void FlightsMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL!=lookupManager);
    
    switch (data.result)
    {
        case lookupResultFlights:
            readUdf();
            MoriartyApplication::touchModule(moduleIdFlights);            
            break;
    }
    lookupManager->handleLookupFinishedInForm(data);
}

