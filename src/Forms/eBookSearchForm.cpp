#include "EBookSearchForm.hpp"

EBookSearchForm::EBookSearchForm(MoriartyApplication& app):
    MoriartyForm(app, ebookSearchForm, true),
    inputField(*this),
    searchPhrase(NULL)
{
    setFocusControlId(termInputField);
}

EBookSearchForm::~EBookSearchForm()
{
}

void EBookSearchForm::attachControls()
{
    MoriartyForm::attachControls();
    inputField.attach(termInputField);
    if (NULL != searchPhrase)
    {
        inputField.setEditableText(searchPhrase, tstrlen(searchPhrase));
        inputField.select();
    }
    inputField.focus();
}


bool EBookSearchForm::handleEvent(EventType& event)
{
    switch (event.eType)
    {
        case keyDownEvent:
            if (chrCarriageReturn == event.data.keyDown.chr || chrLineFeed == event.data.keyDown.chr)
            {
                Control ctl(*this, searchButton);
                ctl.hit();
                return true;
            }
            return false;
            
        case ctlSelectEvent:
            if (cancelButton == event.data.ctlSelect.controlID)
                return false;
            if (0 == inputField.textLength())
                return true;
            // Intentional fall-through.            
        default:
            return MoriartyForm::handleEvent(event);
    }
}

/*
void EBookSearchForm::resize(const ArsRectangle& screenBounds)
{
// NOTE: although code below correctly repositions form, it leaves some rubbish on previous one, so I disable it.
    ArsRectangle rect(2, screenBounds.height() - 62, screenBounds.width() - 4, 60);
    setBounds(rect);
    update();
}
 */    
