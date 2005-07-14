#ifndef __EPICURIOUS_PREFERENCES_FORM_HPP__
#define __EPICURIOUS_PREFERENCES_FORM_HPP__

#include "MoriartyForm.hpp"
#include <Table.hpp>

class EpicuriousPreferencesForm: public MoriartyForm {

    Control okButton_;
    Control cancelButton_;
    Table recipePartsTable_;
    
public:

    EpicuriousPreferencesForm(MoriartyApplication& app);
    
    ~EpicuriousPreferencesForm();
    
protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);

    bool handleOpen();
    
    bool handleEvent(EventType& event);
    
    void handleControlSelected(const EventType& event);
    
private:

    void handleOkButton();
   
};

#endif