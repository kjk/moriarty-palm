#include <Text.hpp>
#include <Definition.hpp>
#include <TextElement.hpp>
#include <LineBreakElement.hpp>

#include "MoriartyPreferences.hpp"
#include "LookupManager.hpp"
#include "HyperlinkHandler.hpp"
#include "DreamsMainForm.hpp"

#include "MoriartyStyles.hpp"

enum {
    dreamTitleIndex,
    dreamTextIndex
};

DreamsMainForm::DreamsMainForm(MoriartyApplication& app):
    MoriartyForm(app, dreamsMainForm),
    scrollBar_(*this),
    doneButton_(*this),
    dreamNameField_(*this),
    searchButton_(*this),
    displayMode_(showHelpText),
    graffitiState_(*this),
    helpText1Label_(*this),
    helpText2Label_(*this),
    helpText3Label_(*this),
    dreamRenderer_(*this, &scrollBar_)
{
    dreamRenderer_.setInteractionBehavior(
        TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavUpDownScroll
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    dreamRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    setFocusControlId(dreamNameField);
}

DreamsMainForm::~DreamsMainForm() {}

void DreamsMainForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    dreamRenderer_.attach(dreamRenderer);
    dreamRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
    
    doneButton_.attach(doneButton);
    dreamNameField_.attach(dreamNameField);
    searchButton_.attach(searchButton);
    helpText1Label_.attach(helpText1Label);
    helpText2Label_.attach(helpText2Label);
    helpText3Label_.attach(helpText3Label);
    graffitiState_.attachByIndex(getGraffitiStateIndex());
}

bool DreamsMainForm::handleOpen()
{
    bool result=MoriartyForm::handleOpen();
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(0!=lookupManager);
    
    if (!lookupManager->dream.empty())
        setDisplayMode(showDream);
    else
        setDisplayMode(displayMode_);

    return result;
}

void DreamsMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(bounds=screenBounds);
    
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

    update();    
}

bool DreamsMainForm::handleEvent(EventType& event)
{
    if (showDream == displayMode_ && dreamRenderer_.handleEventInForm(event))
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

bool DreamsMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled=false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            handled=true;
            break;
            
        default:
            assert(false);
    }
    return handled;
}

void DreamsMainForm::setHelpTextVisible(bool visible)
{
    if (visible)
    {
        helpText1Label_.show();         
        helpText2Label_.show();         
        helpText3Label_.show();         
    }
    else
    {
        helpText1Label_.hide();         
        helpText2Label_.hide();         
        helpText3Label_.hide();         
    }
}

    
void DreamsMainForm::setDisplayMode(DreamsMainForm::DisplayMode dm)
{
    switch (displayMode_=dm)
    {
        case showDream:
            if (dreamRenderer_.empty())
                prepareDream();
            scrollBar_.show();
            dreamRenderer_.show();
            setHelpTextVisible(false);
            scrollBar_.show();
            break;  
            
        case showHelpText:
            scrollBar_.hide();
            dreamRenderer_.hide();
            setHelpTextVisible(true);
            break;
            
        default:
            assert(false);
    }
}

void DreamsMainForm::handleSearch()
{
    char* dreamName = dreamNameField_.textCopy();
    if (NULL == dreamName)
        return;

    StrStrip(dreamName);

    if (StrEmpty(dreamName))
        goto Exit;

    LookupManager* lookupManager=application().lookupManager;
    assert(0!=lookupManager);
    lookupManager->fetchField(getDreamsField, dreamName);
Exit:
    if (NULL != dreamName)
        free(dreamName);
}

void DreamsMainForm::handleControlSelect(const EventType& event)
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

void DreamsMainForm::prepareDream()
{

    const LookupManager* lookupManager=application().lookupManager;
    assert(0!=lookupManager);

    const UniversalDataFormat& dream=lookupManager->dream;
    assert(!dream.empty());

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }

    Definition::Elements_t& elems = model->elements;
    TextElement* text;
    for (int i = 0; i < dream.getItemsCount(); i++)
    {
        if (2 == dream.getItemElementsCount(i))
        {
            elems.push_back(text=new TextElement(dream.getItemText(i, dreamTitleIndex)));
            text->setStyle(StyleGetStaticStyle(styleNameHeader));
            elems.push_back(new LineBreakElement());
    
            String str;

            str = dream.getItemText(i, dreamTextIndex);
            parseSimpleFormatting(elems, str, true, urlSchemaDream);
            elems.push_back(new LineBreakElement());
            elems.push_back(new LineBreakElement());
        }
        else if (1 == dream.getItemElementsCount(i))
        {
            elems.push_back(text=new TextElement(dream.getItemText(i, dreamTitleIndex)));
            text->setStyle(StyleGetStaticStyle(styleNamePageTitle));
            text->setJustification(DefinitionElement::justifyCenter);
            elems.push_back(new LineBreakElement());
        }
    }    
    dreamRenderer_.setModel(model, Definition::ownModel);
}


void DreamsMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    switch (data.result)
    {
        case lookupResultDreamData:
            prepareDream();
            if (showDream != displayMode_)
                setDisplayMode(showDream);
            update();
            MoriartyApplication::touchModule(moduleIdDreams);
            break;
    }
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(0!=lookupManager);
    lookupManager->handleLookupFinishedInForm(data);
}

bool DreamsMainForm::handleKeyPress(const EventType& event)
{
    bool handled = false;
    switch (event.data.keyDown.chr)
    {
        case chrLineFeed:
        case chrCarriageReturn:
            searchButton_.hit();
            handled=true;
    }
    return handled;
}
