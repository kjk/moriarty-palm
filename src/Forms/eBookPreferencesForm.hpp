#ifndef EBOOK_PREFERENCES_FORM_HPP__
#define EBOOK_PREFERENCES_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class EBookPreferencesForm: public MoriartyForm {

    Control     okButton_;
    Control     cancelButton_;
    List        downloadDestinationList_;
    char**  downloadDestinations_;
    ulong_t downloadDestinationsSize_;
    ulong_t volumeCount_;
    UInt16* volumes_;

    
public:

    EBookPreferencesForm(MoriartyApplication& app);
    
    ~EBookPreferencesForm();
    
protected:

    void attachControls();

    bool handleOpen();
    
    bool handleEvent(EventType& event);
    
    bool handleControlSelected(const EventType& event);
    
private:

    void handleOkButton();
   
};

#endif