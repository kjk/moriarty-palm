#ifndef __BOXOFFICE_MAINFORM_HPP__
#define __BOXOFFICE_MAINFORM_HPP__

#include "MoriartyApplication.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <UniversalDataFormat.hpp>
#include <HmStyleList.hpp>

class LookupManager;

class BoxOfficeMainForm: public MoriartyForm
{
    UniversalDataFormat* boxOfficeData_;

    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr moviesListDrawHandler_;
    
    HmStyleList resultsList_;
    Control doneButton_;
    Control updateButton_;

    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void setControlsState(bool enabled);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup(LookupManager& lookupManager);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    void draw(UInt16 updateCode=frmRedrawUpdateCode);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);

public:
    
    BoxOfficeMainForm(MoriartyApplication& app);
    
    ~BoxOfficeMainForm();
      
};

#endif
