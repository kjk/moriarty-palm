#ifndef __M411_ENTER_ZIP_FORM_HPP__
#define __M411_ENTER_ZIP_FORM_HPP__

#include "MoriartyForm.hpp"

class M411EnterZipForm: public MoriartyForm
{
    Field locationField_;

    void handleControlSelect(const EventType& data);

public:
    enum FormMode
    {
        m411zipMode,
        gasPricesMode    
    };

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);

private:

    FormMode formMode_;
    
public:

    M411EnterZipForm(MoriartyApplication& app):
        MoriartyForm(app, m411EnterZipForm, true),
        locationField_(*this),
        formMode_(m411zipMode)
    {
        setFocusControlId(locationField);
    }    
    
    ~M411EnterZipForm();

};

#endif