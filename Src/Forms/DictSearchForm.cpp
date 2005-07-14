#include "DictSearchForm.hpp"

DictSearchForm::DictSearchForm(MoriartyApplication& app):
    MoriartyForm(app, dictSearchForm, true),
    inputField(*this),
    searchButton_(*this),
    searchTerm(NULL)
{
    setFocusControlId(termInputField);
}

DictSearchForm::~DictSearchForm()
{
}

void DictSearchForm::attachControls()
{
    MoriartyForm::attachControls();
    inputField.attach(termInputField);
    if (NULL != searchTerm)
    {
        inputField.setEditableText(searchTerm, tstrlen(searchTerm));
        inputField.select();
    }
    inputField.focus();

    searchButton_.attach(searchButton);
}

bool DictSearchForm::handleEvent(EventType& event)
{
    switch (event.eType)
    {
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

void DictSearchForm::resize(const ArsRectangle& screenBounds)
{
// NOTE: although code below correctly repositions form, it leaves some rubbish on previous one, so I disable it.
/*
    ArsRectangle rect(2, screenBounds.height() - 62, screenBounds.width() - 4, 60);
    setBounds(rect);
    update();
 */    
}
