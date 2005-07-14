#ifndef __LISTS_OF_BESTS_SEARCH_FORM_HPP__
#define __LISTS_OF_BESTS_SEARCH_FORM_HPP__

#include "MoriartyPreferences.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class ListsOfBestsSearchForm: public MoriartyForm 
{
    Control okButton_;
    Control cancelButton_;
    FormObject graffitiState_;
    Control mediaPopupTrigger_;
    Control titlePopupTrigger_;

    ArsLexis::String mediaPopupTriggerText_; //just one time used
    ArsLexis::String titlePopupTriggerText_; //just one time used

    Field keywordField_;
    
    Preferences::ListsOfBestsPreferences* prefs_;
    
public:

    ListsOfBestsSearchForm(MoriartyApplication& app);
    
    ~ListsOfBestsSearchForm();
    
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