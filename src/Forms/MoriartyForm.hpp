#ifndef __MORIARTY_HPP__
#define __MORIARTY_HPP__

#include <RichForm.hpp>
#include "MoriartyApplication.hpp"

class MoriartyForm: public RichForm
{

protected:
    bool handleEvent(EventType& event);

public:

    enum RedrawCode
    {
        redrawAll=frmRedrawUpdateCode,
        redrawProgressIndicator,
        redrawFirstAvailable
    };
    
    MoriartyForm(MoriartyApplication& app, uint_t formId, bool disableDiaTrigger = false);

    ~MoriartyForm();

    MoriartyApplication& application() 
    {return static_cast<MoriartyApplication&>(RichForm::application());}

    const MoriartyApplication& application() const
    {return static_cast<const MoriartyApplication&>(RichForm::application());}
    
};

#endif
