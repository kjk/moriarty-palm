#include "QuotesMainForm.hpp"
#include "MoriartyPreferences.hpp"
#include <SysUtils.hpp>
#include "LookupManager.hpp"
#include <Definition.hpp>
#include <Text.hpp>
#include <ByteFormatParser.hpp>


#pragma pcrelconstdata on

QuotesMainForm::QuotesMainForm(MoriartyApplication& app):
    MoriartyForm(app, quotesMainForm),
    randomButton_(*this),
    doneButton_(*this),
    dailyButton_(*this),
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


QuotesMainForm::~QuotesMainForm() {}

void QuotesMainForm::attachControls()
{
    MoriartyForm::attachControls();
    randomButton_.attach(randomButton);
    doneButton_.attach(doneButton);
    dailyButton_.attach(dailyButton);
    scrollBar_.attach(definitionScrollBar);
    textRenderer_.attach(textRenderer);
    textRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
}


bool QuotesMainForm::handleOpen()
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

void QuotesMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(bounds=screenBounds);

    textRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    dailyButton_.anchor(screenBounds, anchorLeftEdge, 90, anchorTopEdge, 14);
    randomButton_.anchor(screenBounds, anchorLeftEdge, 44, anchorTopEdge, 14);
    update();    
}

bool QuotesMainForm::handleEvent(EventType& event)
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

bool QuotesMainForm::handleMenuCommand(UInt16 itemId)
{
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            break;
            
        case dailyMenuItem:
            dailyButton_.hit();
            break;

        case randomMenuItem:
            randomButton_.hit();
            break;
            
        default:
            assert(false);
            return false;
    }
    return true;
}

void QuotesMainForm::showMain()
{
    UInt32  dataLen;
    char* data = getDataResource(quotationsStartPageText, &dataLen);
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

void QuotesMainForm::readUdf()
{
    UniversalDataFormat* udf = &application().lookupManager->quotesData;
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

            default:
                assert(false);
                break;
        }
    }
    update();
}

void QuotesMainForm::handleDaily()
{
    application().lookupManager->fetchUrl(_T("s+quotes:daily"));
}

void QuotesMainForm::handleRandom()
{
    application().lookupManager->fetchUrl(_T("s+quotes:random"));
}

void QuotesMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;
            
        case dailyButton:
            handleDaily();
            break;

        case randomButton:
            handleRandom();
            break;
            
        default:
            assert(false);
    }
}

void QuotesMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL!=lookupManager);
    
    switch (data.result)
    {
        case lookupResultQuotes:
            readUdf();
            MoriartyApplication::touchModule(moduleIdQuotes);
            break;

        // linked modules
        default:
            if (HandleCrossModuleLookup(event, NULL, quotesModuleName))
                return;
    }
    lookupManager->handleLookupFinishedInForm(data);
}

