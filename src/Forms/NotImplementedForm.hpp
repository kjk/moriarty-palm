#ifndef __NOT_IMPLEMENTED_FORM_HPP__
#define __NOT_IMPLEMENTED_FORM_HPP__

#include <Graphics.hpp>
#include "MoriartyApplication.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class NotImplementedForm: public MoriartyForm
{
    Control doneButton_;
       
    void handleControlSelect(const EventType& data);
    
protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    void draw(UInt16 updateCode=frmRedrawUpdateCode);
    
    bool handleEvent(EventType& event);
    
public:
    
    NotImplementedForm(MoriartyApplication& app);
    
    ~NotImplementedForm();
};

#endif
