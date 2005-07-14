#ifndef __NETFLIX_ENTER_LOGIN_FORM_HPP__
#define __NETFLIX_ENTER_LOGIN_FORM_HPP__

#include "MoriartyForm.hpp"

class NetflixEnterLoginForm: public MoriartyForm
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

    NetflixEnterLoginForm(MoriartyApplication& app);
    
    ~NetflixEnterLoginForm();
    
};

#endif