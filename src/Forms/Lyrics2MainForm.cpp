#include "Lyrics2MainForm.hpp"
#include "MoriartyPreferences.hpp"
#include <SysUtils.hpp>
#include "LookupManager.hpp"
#include <Definition.hpp>
#include <History.hpp>
#include <Text.hpp>
#include <ByteFormatParser.hpp>
#include "HyperlinkHandler.hpp"

Lyrics2MainForm::Lyrics2MainForm(MoriartyApplication& app):
    MoriartyForm(app, lyrics2MainForm),
    scrollBar_(*this),
    doneButton_(*this),
    searchButton_(*this),
    historyButton_(*this),
    historySupport_(*this),
    textRenderer_(*this, &scrollBar_)
{
    setFocusControlId(doneButton);
    textRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    textRenderer_.setHyperlinkHandler(app.hyperlinkHandler);

    setupPopupMenu(linkPopupMenu, MoriartyApplication::extEventShowMenu, app.hyperlinkHandler);

    historySupport_.popupMenuFillHandlerData = (void*)(urlSchemaLyricsForm _T(":main"));

    historySupport_.setup(lyricsHistoryCacheName, historyPopupMenu, historyButton, app.hyperlinkHandler, ReadUrlFromCache);
}

Lyrics2MainForm::~Lyrics2MainForm() {}

void Lyrics2MainForm::attachControls()
{
    MoriartyForm::attachControls();
    doneButton_.attach(doneButton);
    scrollBar_.attach(definitionScrollBar);
    searchButton_.attach(searchButton);
    historyButton_.attach(historyButton);
    textRenderer_.attach(textRenderer);
    textRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
}


bool Lyrics2MainForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();

    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL!=lookupManager);

    // TODO: should show last item
    showStartText();

    return result;
}

void Lyrics2MainForm::resize(const ArsRectangle& screenBounds)
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

bool Lyrics2MainForm::handleEvent(EventType& event)
{
    if (textRenderer_.handleEventInForm(event) || historySupport_.handleEventInForm(event))
        return true;
        
    bool handled=false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled=true;
            break;
            
        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled=true;
            break;
            
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool Lyrics2MainForm::handleMenuCommand(UInt16 itemId)
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
            showStartText();
            handled=true;
            break;

        default:
            assert(false);
    }
    return handled;
}

void Lyrics2MainForm::showStartText()
{
    char_t  *data;
    UInt32  dataLen;
    data = getDataResource(lyricsStartPageText, &dataLen);
    if (NULL == data)
        return;
    Definition::Elements_t elems;
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

void Lyrics2MainForm::setUDF(UniversalDataFormat *udf)
{
    for (int i=0; i < udf->getItemsCount(); i++)
    {
        switch (udf->getItemText(i,0)[0])
        {
            case _T('H'): // history
                historySupport_.lookupFinished(true, udf->getItemText(i,1));
                break;

            case _T('D'): // definition
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
        }
    }
    update();
}

void Lyrics2MainForm::handleSearch()
{
    Application::popupForm(lyricsSearchForm);
}

void Lyrics2MainForm::handleControlSelect(const EventType& event)
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

void Lyrics2MainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL!=lookupManager);

    switch (data.result)
    {
        case lookupResultLyrics:
            setUDF(&lookupManager->lyricsData);
            break;    

        // linked modules
        default:
            if (HandleCrossModuleLookup(event, lyricsHistoryCacheName, lyricsModuleName))
                return;
    }
    lookupManager->handleLookupFinishedInForm(data);
}
