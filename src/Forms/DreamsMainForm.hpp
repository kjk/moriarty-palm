#ifndef MORIARTY_DREAMS_MAIN_FORM_HPP__
#define MORIARTY_DREAMS_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>

class Definition;

class DreamsMainForm: public MoriartyForm {

    ScrollBar scrollBar_;
    Control doneButton_;
    Field dreamNameField_;
    Control searchButton_;
    FormObject graffitiState_;
    
    FormObject helpText1Label_;
    FormObject helpText2Label_;
    FormObject helpText3Label_;
    
    TextRenderer dreamRenderer_;
    
    void setHelpTextVisible(bool visible);

public:

    explicit DreamsMainForm(MoriartyApplication& app);
    
    ~DreamsMainForm();

    enum DisplayMode {
        showHelpText,
        showDream
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
    
    void handleSearch();
    
    void prepareDream();

protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
    friend class DreamsHyperlinkHandler;
    
};

#endif