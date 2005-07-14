#ifndef _NETFLIX_MAIN_FORM_HPP__
#define _NETFLIX_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include "MoriartyPreferences.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>
#include "HyperlinkHandler.hpp"
#include <PopupMenu.hpp>
#include <HistorySupport.hpp>

class NetflixMainForm: public MoriartyForm {

    TextRenderer textRenderer_;
    
    Preferences::NetflixPreferences* prefs_;

    HistorySupport historySupport_;

    Control historyButton_;
    Control doneButton_;
    Control searchButton_;
    Control prevButton_;
    Control nextButton_;
    ScrollBar scrollBar_;
    bool nextButtonEnabled_;
    bool prevButtonEnabled_;
    
    ArsLexis::String nextButtonString_;
    ArsLexis::String prevButtonString_;
    
    void updateNavigationButtons();
    
    void readUdf(bool queue=false);
    
public:

    explicit NetflixMainForm(MoriartyApplication& app);
    
    ~NetflixMainForm();
    
    void setDisplayMode();

    void showStartPage();

    void handleLogin();
    
    void handleLogout();
    
    void handleSearch();
    
    void handleQueue();
    
    void handleMoveOnPosition(const char_t* queueId);
    
private:

    void handleControlSelect(const EventType& data);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup(LookupManager& lookupManager);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
};

#endif