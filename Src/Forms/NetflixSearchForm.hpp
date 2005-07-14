#ifndef __NETFLIX_SEARCH_FORM_HPP__
#define __NETFLIX_SEARCH_FORM_HPP__

#include "MoriartyPreferences.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class NetflixSearchForm: public MoriartyForm 
{
    Control okButton_;
    Control cancelButton_;
    FormObject graffitiState_;
    Control matchesPopupTrigger_;

    Field keywordField_;
    int     matchesPopupIndex_;    
    
    Preferences::NetflixPreferences* prefs_;
    
public:

    NetflixSearchForm(MoriartyApplication& app);
    
    ~NetflixSearchForm();
    
protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);

    bool handleOpen();
    
    bool handleEvent(EventType& event);
    
private:

    bool handleControlSelected(const EventType& event);
    
    void handleOkButton();
   
};

#endif