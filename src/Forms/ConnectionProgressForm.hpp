#ifndef MORIARTY_CONNECTION_PROGRESS_FORM_HPP__
#define MORIARTY_CONNECTION_PROGRESS_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class ConnectionProgressForm: public MoriartyForm {

    LookupManager* lookupManager_;
    Control cancelButton_;
    
    void handleLookupFinished(const EventType& event);
    
protected:

    void attachControls();

    void draw(UInt16 updateCode=frmRedrawUpdateCode);

    void resize(const ArsRectangle& screenBounds);

    bool handleEvent(EventType& event);
    
    void handleControlSelected(const EventType& event);
    
public:

    ConnectionProgressForm(MoriartyApplication& app);
    
    ~ConnectionProgressForm();
    
};

#endif