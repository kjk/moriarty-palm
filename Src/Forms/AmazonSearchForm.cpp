#include <FormObject.hpp>
#include "MoriartyApplication.hpp"
#include "AmazonSearchForm.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>
#include <DynStr.hpp>
#include <TextElement.hpp>

using ArsLexis::String;

AmazonSearchForm::AmazonSearchForm(MoriartyApplication& app, const char_t* requestString, const char_t* displayText):
    MoriartyForm(app, amazonSearchForm, true),
    searchField_(*this),
    textRenderer_(*this, NULL),
    okButton_(*this),
    cancelButton_(*this),
    graffitiState_(*this)
{
    textRenderer_.setInteractionBehavior(0);
    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL != model)
    {
        model->elements.push_back(new TextElement(displayText));
    }
    textRenderer_.setModel(model, Definition::ownModel);

    // we assume that requestString will be available when 
    // AmazonSearchForm::handleControlSelect() is called
    assert( NULL != requestString);
    request_ = requestString;
    setFocusControlId(searchField);
}   

bool AmazonSearchForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    afterFormOpen();
    return result;
}

#define LINE_HEIGHT 14

void AmazonSearchForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-64, screenBounds.width()-4, 62);
    textRenderer_.calculateLayout();
    int lines = textRenderer_.linesCount();
    if (lines > 1)
    {
        lines--;
        rect.y() -= lines*LINE_HEIGHT;
        rect.dy() += lines*LINE_HEIGHT;
    }    
    setBounds(rect);
    update();
}

void AmazonSearchForm::attachControls()
{
    MoriartyForm::attachControls();
    searchField_.attach(searchField);
    textRenderer_.attach(textRenderer);
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
    graffitiState_.attachByIndex(getGraffitiStateIndex());
}

void AmazonSearchForm::handleControlSelect(const EventType& event)
{
    if (okButton==event.data.ctlSelect.controlID)
    {
        const char_t* text = searchField_.text();
        assert( NULL != request_);
        if (NULL != text)
        {
            DynStr *tmpStr = DynStrFromCharP2(request_, text);
            if (NULL != tmpStr)
            {
                LookupManager* lookupManager=application().lookupManager;
                assert(NULL!=lookupManager);
                lookupManager->fetchUrl(DynStrGetCStr(tmpStr));
                DynStrDelete(tmpStr);
            }
        }
    }
    closePopup();
}

void AmazonSearchForm::afterFormOpen()
{
    // resize form if text have more than one line
    textRenderer_.calculateLayout();
    int lines = textRenderer_.linesCount();
    if (lines > 1)
    {
        lines--;
        ArsRectangle rect;
        
        okButton_.bounds(rect);
        rect.y() += lines*LINE_HEIGHT;
        okButton_.setBounds(rect);
        cancelButton_.bounds(rect);
        rect.y() += lines*LINE_HEIGHT;
        cancelButton_.setBounds(rect);
        graffitiState_.bounds(rect);
        rect.y() += lines*LINE_HEIGHT;
        graffitiState_.setBounds(rect);
        searchField_.bounds(rect);
        rect.y() += lines*LINE_HEIGHT;
        searchField_.setBounds(rect);
        textRenderer_.bounds(rect);
        rect.dy() += lines*LINE_HEIGHT;
        textRenderer_.setBounds(rect);

        bounds(rect);
        rect.y() -= lines*LINE_HEIGHT;
        rect.dy() += lines*LINE_HEIGHT;
        rect = rect.explode(2,2,-4,-4);
        setBounds(rect);
    
        update();
    }
}

bool AmazonSearchForm::handleEvent(EventType& event)
{
    bool handled=false;
    switch (event.eType)
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled=true;
            break;
            
        case keyDownEvent:
            if (chrCarriageReturn==event.data.keyDown.chr || chrLineFeed==event.data.keyDown.chr)
            {
                Control control(*this, okButton);
                control.hit();
            }
            break;

        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

AmazonSearchForm::~AmazonSearchForm()
{
}
