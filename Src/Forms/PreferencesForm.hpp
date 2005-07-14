#ifndef MORIARTY_PREFERENCES_FORM_HPP__
#define MORIARTY_PREFERENCES_FORM_HPP__

#include "MoriartyForm.hpp"
#include <Table.hpp>

class PreferencesForm: public MoriartyForm {

    Control okButton_;
    Control cancelButton_;
    ScrollBar scrollBar_;
    Table modulesTable_;
    
    Control modulesButton_;
    
    Control displayButton_;
    Control layoutPopupTrigger_;
    Control layoutLabel_;
    int     layoutPopupIndex_;
    
public:

    PreferencesForm(MoriartyApplication& app);
    
    ~PreferencesForm();
    
    enum DisplayPage {
        pageModules,
        pageDisplay
    };

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);

    bool handleOpen();
    
    bool handleEvent(EventType& event);
    
    bool handleControlSelected(const EventType& event);
    
private:

    DisplayPage displayPage_;
    
    void setDisplayPage(DisplayPage page);
    
    void handleOkButton();
    
};

#endif