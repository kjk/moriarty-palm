#ifndef __M411_ENTER_PERSON_FORM_HPP__
#define __M411_ENTER_PERSON_FORM_HPP__

#include "MoriartyForm.hpp"

class M411EnterPersonForm: public MoriartyForm
{
    Field firstNameField_;
    Field lastNameField_;
    Field cityOrZipField_;
    Control stateField_;
    ArsLexis::String stateSymbol_;

    void handleControlSelect(const EventType& data);

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
public:

    M411EnterPersonForm(MoriartyApplication& app):
        MoriartyForm(app, m411EnterPersonForm, true),
        firstNameField_(*this),
        lastNameField_(*this),
        cityOrZipField_(*this),
        stateField_(*this)
    {
        setFocusControlId(lastNameField);
    }    
    
    ~M411EnterPersonForm();

};

#endif