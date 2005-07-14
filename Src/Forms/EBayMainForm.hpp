#ifndef _EBAY_MAIN_FORM_HPP__
#define _EBAY_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include "MoriartyPreferences.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>
#include "HyperlinkHandler.hpp"
#include <PopupMenu.hpp>
#include <HistorySupport.hpp>

class EBayMainForm: public MoriartyForm {

    TextRenderer textRenderer_;
    
    Preferences::EBayPreferences* prefs_;

    HistorySupport historySupport_;

    Control historyButton_;
    Control doneButton_;
    Control updateButton_;
    Control searchButton_;
    Control prevButton_;
    Control nextButton_;
    ScrollBar scrollBar_;
    bool nextButtonEnabled_;
    bool prevButtonEnabled_;
    
    ArsLexis::String updateButtonString_;
    ArsLexis::String nextButtonString_;
    ArsLexis::String prevButtonString_;
    ArsLexis::String searchServerString_;
    ArsLexis::String searchDisplayString_;
    
    void updateNavigationButtons();
    
    void readUdf(bool noCache=false);
    
public:

    explicit EBayMainForm(MoriartyApplication& app);
    
    ~EBayMainForm();
    
    void showStartPage();

    void handleLogin();
    
    void handleLogout();
    
    void handleSearch();
    
    void handleUpdateButton();
    
    void handleBid(const char_t* args);
    
private:

    void handleControlSelect(const EventType& data);
    
    void handleLookupFinished(const EventType& event);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
};

#endif