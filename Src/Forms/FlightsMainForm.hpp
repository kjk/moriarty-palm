#ifndef _FLIGHTS_MAIN_FORM_HPP__
#define _FLIGHTS_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

#include <TextRenderer.hpp>
#include "HyperlinkHandler.hpp"
#include <PopupMenu.hpp>

class FlightsMainForm: public MoriartyForm {

    TextRenderer textRenderer_;
    
    Control     doneButton_;
    Control     searchButton_;
    Control     updateButton_;
    ScrollBar   scrollBar_;
    
    ArsLexis::String updateString_;
public:

    explicit FlightsMainForm(MoriartyApplication& app);
    
    ~FlightsMainForm();

    void handleSearch();

    void handleUpdateButton();

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