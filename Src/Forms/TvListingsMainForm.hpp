#ifndef MORIARTY_TV_LISTINGS_MAIN_FORM_HPP__
#define MORIARTY_TV_LISTINGS_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class UniversalDataFormat;

class TvListingsMainForm: public MoriartyForm {

    ScrollBar horizScrollBar_;
    ScrollBar vertScrollBar_;
    Control doneButton_;
public:

    explicit TvListingsMainForm(MoriartyApplication& app);
    
    ~TvListingsMainForm();

    enum DisplayMode {
        showGrid
    };
    
    void setDisplayMode(DisplayMode dm);
    
    DisplayMode displayMode() const
    {return displayMode_;}
    
private:
    
    DisplayMode displayMode_;

    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup(LookupManager& lookupManager);
    
    void selectProvider(const UniversalDataFormat& providers);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
};

#endif