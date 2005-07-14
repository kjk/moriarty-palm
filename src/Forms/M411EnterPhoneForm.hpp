#ifndef __M411_ENTER_PHONE_FORM_HPP__
#define __M411_ENTER_PHONE_FORM_HPP__

#include "MoriartyForm.hpp"

class M411EnterPhoneForm: public MoriartyForm
{
    Field phoneField_;

    void handleControlSelect(const EventType& data);

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
public:

    M411EnterPhoneForm(MoriartyApplication& app):
        MoriartyForm(app, m411EnterPhoneForm, true),
        phoneField_(*this)
    {
        setFocusControlId(phoneField);
    }    
    
    ~M411EnterPhoneForm();
    
};

#endif