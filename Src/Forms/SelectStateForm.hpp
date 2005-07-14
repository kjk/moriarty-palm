#ifndef _SELECT_STATE_FORM_HPP_
#define _SELECT_STATE_FORM_HPP_

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <HmStyleList.hpp>

class SelectStateForm: public MoriartyForm {

    HmStyleList statesList_;
    Control okButton_;
    Control cancelButton_;
    
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> DrawHandlerPtr;
    DrawHandlerPtr statesListDrawHandler_;

    void handleControlSelected(const EventType& event);
    
    void handleListItemSelected(const EventType& event);

protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
public:

    SelectStateForm(MoriartyApplication& app);
    
    ~SelectStateForm();

private:
    enum OkMode
    {
        statesMode,
        internationalCodeMode,
        businessSearchByUrlMode,
        stocksPortfolioMode,
        stocksNameMatchingMode
    };
    OkMode okMode_;

};

#endif
