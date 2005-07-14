#ifndef _AMAZON_MAIN_FORM_HPP__
#define _AMAZON_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include "MoriartyPreferences.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>
#include "HyperlinkHandler.hpp"
#include <PopupMenu.hpp>
#include <HistorySupport.hpp>

class AmazonMainForm: public MoriartyForm 
{
    Preferences::AmazonPreferences* prefs_;

    TextRenderer     textRenderer_;
    HistorySupport   historySupport_;
    Control          historyButton_;
    Control          doneButton_;
    Field            informationField_;
    Control          searchButton_;
    Control          prevButton_;
    Control          nextButton_;
    ScrollBar        scrollBar_;
    bool             nextButtonEnabled_;
    bool             prevButtonEnabled_;

    // used to disable next button (when no info about total results available)
    bool             fThisIsTheEndOfResults_;

    ArsLexis::String informationString_;    
    ArsLexis::String searchButtonString_;
    ArsLexis::String searchTextString_;
    ArsLexis::String nextButtonString_;
    ArsLexis::String prevButtonString_;

    void updateNavigationButtons();

    void showStartPage();

    void readUdf();

public:

    explicit AmazonMainForm(MoriartyApplication& app);

    ~AmazonMainForm();

    void setDisplayMode();

    void levelUp();

    void levelMain();

    void handleSearch();

    void switchToLevel(int level);

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
