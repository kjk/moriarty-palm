#ifndef __JOKES_SEARCH_FORM_HPP__
#define __JOKES_SEARCH_FORM_HPP__

#include "MoriartyForm.hpp"
#include "MoriartyPreferences.hpp"
#include <HmStyleList.hpp>

class JokesSearchForm: public MoriartyForm {

    Control okButton_;
    Control cancelButton_;
    HmStyleList categoryTable_;
    HmStyleList typeTable_;
    HmStyleList explicitnessTable_;
    FormObject graffitiState_;

    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr categoryTableDrawHandler_;
    ListDrawHandlerPtr typeTableDrawHandler_;
    ListDrawHandlerPtr explicitnessTableDrawHandler_;

    typedef std::auto_ptr<List::CustomDrawHandler> PopupListDrawHandlerPtr;
    PopupListDrawHandlerPtr ratingPopupListDrawHandler_;
    PopupListDrawHandlerPtr sortPopupListDrawHandler_;

    Control jokeRatingPopupTrigger_;
    List jokeRatingPopupList_;
    ArsLexis::String jokeRatingPopupTriggerText_;

    Control jokeSortPopupTrigger_;
    List jokeSortPopupList_;
    ArsLexis::String jokeSortPopupTriggerText_;
    
    Field keywordField_;
    int     jokeRatingPopupIndex_;
    int     jokeSortPopupIndex_;    
    
    Preferences::JokesPreferences prefs_;
    
public:

    JokesSearchForm(MoriartyApplication& app);
    
    ~JokesSearchForm();
    
protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);

    bool handleOpen();
    
    bool handleEvent(EventType& event);
    
    void handleListItemSelect(UInt16 listId, UInt16 itemId);

    bool handleMenuCommand(UInt16 itemId);
    
private:

    bool handleControlSelected(const EventType& event);
    
    void handleOkButton();
   
};

#endif