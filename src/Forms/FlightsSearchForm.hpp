#ifndef __FLIGHTS_SEARCH_FORM_HPP__
#define __FLIGHTS_SEARCH_FORM_HPP__

#include "MoriartyPreferences.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class FlightsSearchForm: public MoriartyForm 
{
    Control okButton_;
    Control cancelButton_;
    FormObject graffitiState_;

    Control airlinesPopupTrigger_;

    ArsLexis::String airlinesPopupTriggerText_;

    Field flightNoField_;
    Field fromField_;
    Field toField_;

    Control dateTrigger_;
    Control timeTrigger_;
    ArsLexis::String dateTriggerString_;
    ArsLexis::String timeTriggerString_;
    
    Int16  day_;
    Int16  month_;
    Int16  year_;
    
    Int16  hour_;
    Int16  minutes_;
    
public:

    FlightsSearchForm(MoriartyApplication& app);
    
    ~FlightsSearchForm();
    
protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);

    bool handleOpen();
    
    bool handleEvent(EventType& event);
    
private:

    bool handleControlSelected(const EventType& event);
    
    void handleOkButton();

    void updateDateTrigger();

    void updateTimeTrigger();

};

#endif