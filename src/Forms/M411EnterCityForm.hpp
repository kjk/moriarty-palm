#ifndef __M411_ENTER_CITY_FORM_HPP__
#define __M411_ENTER_CITY_FORM_HPP__

#include "MoriartyForm.hpp"

class M411EnterCityForm: public MoriartyForm
{
    Field cityField_;
    Control stateField_;
    ArsLexis::String stateSymbol_;

    void handleControlSelect(const EventType& data);

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
public:

    enum WhenOk
    {
        areaByCity,
        zipByCity    
    };
    
    void setWhenOk(WhenOk whenOk)
    {whenOk_ = whenOk;};
    
    M411EnterCityForm(MoriartyApplication& app):
        MoriartyForm(app, m411EnterCityForm, true),
        cityField_(*this),
        stateField_(*this)
    {   
        setFocusControlId(cityField);
    }    
    
    ~M411EnterCityForm();

private:
    WhenOk whenOk_;
    
};

#endif