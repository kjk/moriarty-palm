#ifndef SELECT_LOCATION_FORM_HPP_
#define SELECT_LOCATION_FORM_HPP_

#include <FormObject.hpp>
#include "MoriartyForm.hpp"
#include <HmStyleList.hpp>

class SelectLocationForm: public MoriartyForm {

    HmStyleList locationsList_;
    
    Control okButton_;
    Control cancelButton_;
    
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> DrawHandlerPtr;
    DrawHandlerPtr locationsListDrawHandler_;

    void handleControlSelected(const EventType& event);
    
    void handleListItemSelected(const EventType& event);

protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
public:

    SelectLocationForm(MoriartyApplication& app);
    
    ~SelectLocationForm();

private:
    enum OkMode
    {
        moviesMode,
        areaByCityMode,
        zipByCityMode,
        personSearchMode,
        weatherMultiselectMode
    };    
    OkMode okMode_;
};

#endif
