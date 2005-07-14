#include "ListsOfBestsMainForm.hpp"
#include "MoriartyPreferences.hpp"
#include <SysUtils.hpp>
#include "LookupManager.hpp"
#include <Definition.hpp>
#include <Text.hpp>
#include <ByteFormatParser.hpp>
#include "History.hpp"


#pragma pcrelconstdata on

ListsOfBestsMainForm::ListsOfBestsMainForm(MoriartyApplication& app):
    MoriartyForm(app, listsOfBestsMainForm),
    historyButton_(*this),
    doneButton_(*this),
    searchButton_(*this),
    scrollBar_(*this),
    historySupport_(*this),
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
    
    historySupport_.popupMenuFillHandlerData = (void*)(urlSchemaListsOfBestsForm _T(":main"));
    
    historySupport_.setup(listsOfBestsHistoryCacheName, historyPopupMenu, historyButton, app.hyperlinkHandler, ReadUrlFromCache);
}


ListsOfBestsMainForm::~ListsOfBestsMainForm() {}

void ListsOfBestsMainForm::attachControls()
{
    MoriartyForm::attachControls();
    historyButton_.attach(historyButton);
    doneButton_.attach(doneButton);
    searchButton_.attach(searchButton);
    scrollBar_.attach(definitionScrollBar);
    textRenderer_.attach(textRenderer);
    textRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
}


bool ListsOfBestsMainForm::handleOpen()
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

void ListsOfBestsMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(bounds=screenBounds);

    textRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    searchButton_.anchor(screenBounds, anchorLeftEdge, 59, anchorTopEdge, 14);
    historyButton_.anchor(screenBounds, anchorLeftEdge, 13, anchorTopEdge, 14);
    update();    
}

bool ListsOfBestsMainForm::handleEvent(EventType& event)
{
    if (textRenderer_.handleEventInForm(event) || historySupport_.handleEventInForm(event))
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

bool ListsOfBestsMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled=false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            handled=true;
            break;
            
        case backMenuItem:
            historySupport_.movePrevious();
            handled=true;
            break;

        case forwardMenuItem:
            historySupport_.moveNext();
            handled=true;
            break;

        case historyMenuItem:
            historyButton_.hit();
            handled=true;
            break;

        case categoryMenuItem:
            showMain();
            handled=true;
            break;

    }
    return handled;
}

void ListsOfBestsMainForm::showMain()
{
    UInt32  dataLen;
    char* data = getDataResource(listsOfBestsStartPageText, &dataLen);
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

void ListsOfBestsMainForm::readUdf()
{
    UniversalDataFormat* udf = &application().lookupManager->listsOfBestsData;
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

            case _T('H'):
                {
                    historySupport_.lookupFinished(true, udf->getItemText(i,1));
                }
                break;
            default:
                assert(false);
                break;
        }
    }
    update();
}

void ListsOfBestsMainForm::handleSearch()
{
    Application::popupForm(listsOfBestsSearchForm);
}

void ListsOfBestsMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;
            
        case searchButton:
            handleSearch();
            break;
            
        default:
            assert(false);
    }
}

void ListsOfBestsMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL!=lookupManager);
    
    // lookupManager->lookupPending = false;
    
    switch (data.result)
    {
        case lookupResultListsOfBests:
            readUdf();
            break;

        // linked modules
        default:
            if (HandleCrossModuleLookup(event, listsOfBestsHistoryCacheName, listsOfBestsModuleName))
                return;
    }
    lookupManager->handleLookupFinishedInForm(data);
}

