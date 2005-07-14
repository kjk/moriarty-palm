#ifndef __M411_ENTER_AREA_FORM_HPP__
#define __M411_ENTER_AREA_FORM_HPP__

#include "MoriartyForm.hpp"

class M411EnterAreaForm: public MoriartyForm
{
    Field locationField_;

    void handleControlSelect(const EventType& data);

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
public:

    M411EnterAreaForm(MoriartyApplication& app):
        MoriartyForm(app, m411EnterAreaForm, true),
        locationField_(*this)
    {
        setFocusControlId(locationField);
    }    
    
    ~M411EnterAreaForm();
    
};

#endif