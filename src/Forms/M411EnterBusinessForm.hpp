#ifndef __M411_ENTER_BUSINESS_FORM_HPP__
#define __M411_ENTER_BUSINESS_FORM_HPP__

#include "MoriartyForm.hpp"

class M411EnterBusinessForm: public MoriartyForm
{
    Field nameField_;
    Field cityOrZipField_;
    Control stateField_;
    Control categoryCheckBox_;
    ArsLexis::String stateSymbol_;

    void handleControlSelect(const EventType& data);

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
public:

    M411EnterBusinessForm(MoriartyApplication& app):
        MoriartyForm(app, m411EnterBusinessForm, true),
        nameField_(*this),
        cityOrZipField_(*this),
        stateField_(*this),
        categoryCheckBox_(*this)
    {
        setFocusControlId(nameField);
    }    
    
    ~M411EnterBusinessForm();

};

#endif
