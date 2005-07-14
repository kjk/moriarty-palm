#ifndef _LISTS_OF_BESTS_MAIN_FORM_HPP__
#define _LISTS_OF_BESTS_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

#include <TextRenderer.hpp>
#include "HyperlinkHandler.hpp"
#include <PopupMenu.hpp>
#include <HistorySupport.hpp>

class ListsOfBestsMainForm: public MoriartyForm {

    TextRenderer textRenderer_;
    
    HistorySupport historySupport_;

    Control doneButton_;
    Control searchButton_;
    Control historyButton_;
    ScrollBar scrollBar_;
    
public:

    explicit ListsOfBestsMainForm(MoriartyApplication& app);
    
    ~ListsOfBestsMainForm();

    void handleSearch();

    void showMain();

private:
    
    void readUdf();
    
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