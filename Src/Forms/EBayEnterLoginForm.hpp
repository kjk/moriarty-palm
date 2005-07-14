#ifndef __EBAY_ENTER_LOGIN_FORM_HPP__
#define __EBAY_ENTER_LOGIN_FORM_HPP__

#include "MoriartyForm.hpp"

class EBayEnterLoginForm: public MoriartyForm
{
    Field loginField_;

    Field passwordField_;

    void handleControlSelect(const EventType& data);

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleOpen();
    
public:

    EBayEnterLoginForm(MoriartyApplication& app);
    
    ~EBayEnterLoginForm();
    
};

#endif