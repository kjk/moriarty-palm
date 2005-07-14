#ifndef MORIARTY_STOCKS_DETAILED_DONE_UPDATE_FORM_HPP__
#define MORIARTY_STOCKS_DETAILED_DONE_UPDATE_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>

class StockDetailedDoneUpdateForm: public MoriartyForm {

    ScrollBar scrollBar_;
    Control doneButton_;
    Control backButton_;
    Control updateButton_;

    ArsLexis::String updateString_;

    TextRenderer stocksDetailsRenderer_;
    
public:

    enum DisplayMode {
        showNothing,
        showStockDetailed
    };

    explicit StockDetailedDoneUpdateForm(MoriartyApplication& app, DisplayMode mode);
    
    ~StockDetailedDoneUpdateForm();

    void setDisplayMode(DisplayMode dm);
    
    DisplayMode displayMode() const
    {return displayMode_;}
    
private:
    
    DisplayMode displayMode_;

    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void handleLookupFinished(const EventType& event);

    void updateAfterLookup(LookupManager& lookupManager);
    
    void prepareStock();

    void handleUpdateButton();
    
protected:
    
    bool handleOpen();

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);

};

#endif