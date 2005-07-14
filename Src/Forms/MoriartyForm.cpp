#include <Text.hpp>
#include "MoriartyForm.hpp"
#include "MoriartyApplication.hpp"


MoriartyForm::~MoriartyForm()
{}

MoriartyForm::MoriartyForm(MoriartyApplication& app, uint_t formId, bool disableDiaTrigger):
    RichForm(app, formId, disableDiaTrigger)
{}


bool MoriartyForm::handleEvent(EventType& event)
{
    ArsLexis::char_t   numBuf[32];

    bool handled = false;

    switch (event.eType)
    {            
        case MoriartyApplication::appCheckRegCodeDaysToExpire:
            if (application().regCodeDaysToExpire < 7)
            {
                formatNumber(application().regCodeDaysToExpire, numBuf, sizeof(numBuf));
                FrmCustomAlert(regCodeWillExpireSoonAlert, numBuf, "", "");
            }
            update();
            handled = true;
            break;
        default:
            handled = RichForm::handleEvent(event);
            break;
    }
    return handled;
}

