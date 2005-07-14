#ifndef __CHANGE_LOCATION_FORM_HPP__
#define __CHANGE_LOCATION_FORM_HPP__

#include "MoriartyForm.hpp"

class ChangeLocationForm: public MoriartyForm
{
    Field locationField_;

    void handleControlSelect(const EventType& data);

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleOpen();
    
    bool handleWindowEnter(const struct _WinEnterEventType& event);
    
public:

    ChangeLocationForm(MoriartyApplication& app):
        MoriartyForm(app, changeLocationForm, true),
        locationField_(*this),
        whenOk_(moviesMode)
    {}    
    
    ~ChangeLocationForm();

private:
    enum WhenOk
    {
        moviesMode,
        weatherMode
    };
    
    WhenOk whenOk_;
    
};

#endif