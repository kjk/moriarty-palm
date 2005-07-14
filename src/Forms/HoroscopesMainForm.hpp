#ifndef MORIARTY_HOROSCOPES_MAIN_FORM_HPP__
#define MORIARTY_HOROSCOPES_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <HmStyleList.hpp>
#include <TextRenderer.hpp>

class HoroscopesMainForm: public MoriartyForm {

    HmStyleList horoscopesList_;
    ScrollBar scrollBar_;
    Control doneBackButton_;
    Control updateButton_;
    
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr horoscopesListDrawHandler_;
    
    uint_t currentHoroscopeIndex_;
    uint_t downloadingHoroscopeIndex_;
    enum {horoscopeIndexNone=uint_t(-1)};
    
    TextRenderer horoscopeRenderer_;

    ArsLexis::String dateString_;
    
public:

    explicit HoroscopesMainForm(MoriartyApplication& app);
    
    ~HoroscopesMainForm();

    enum DisplayMode {
        showHoroscopesList,
        showHoroscope
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
    
    void prepareHoroscope();

    void handleUpdateButton();

    void handleListItemSelect(uint_t listId, uint_t itemId);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
};

#endif