#ifndef __REGISTRATION_FORM_HPP__
#define __REGISTRATION_FORM_HPP__

#include "MoriartyForm.hpp"
#include "MoriartyApplication.hpp"

class RegistrationForm: public MoriartyForm
{
    void handleControlSelect(const EventType& data);

    void handleLookupFinished(const EventType& event);

    ArsLexis::char_t * newRegCode_;

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleOpen();
    
public:

    RegistrationForm(MoriartyApplication& app):
        MoriartyForm(app, registrationForm, true)
    {
        newRegCode_ = NULL;
        setFocusControlId(regCodeFormField);
    }    
    
    ~RegistrationForm();
    
};

#endif
