#include "EBookNoReaderForm.hpp"
#include "MoriartyPreferences.hpp"
#include <SysUtils.hpp>
#include "eBookFormats.hpp"

EBookNoReaderForm::EBookNoReaderForm(MoriartyApplication& app):
    MoriartyForm(app, ebookNoReaderForm, true),
    downloadButton_(*this),
    cancelButton_(*this),
    dontAskAgainCheckbox_(*this)
{}

EBookNoReaderForm::~EBookNoReaderForm() 
{
}

void EBookNoReaderForm::attachControls()
{
    MoriartyForm::attachControls();
    downloadButton_.attach(downloadButton);
    cancelButton_.attach(cancelButton);
    dontAskAgainCheckbox_.attach(dontAskAgainCheckbox);
}

bool EBookNoReaderForm::handleEvent(EventType& event)
{
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            if (downloadButton == event.data.ctlSelect.controlID)
                handleDownloadButton();
            break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

void EBookNoReaderForm::handleDownloadButton()
{
    EBookPreferences& prefs = application().preferences().ebookPrefs;
    if (0 != dontAskAgainCheckbox_.value())
        prefs.dontConfirmDownloadWithNoReader = true;
}


