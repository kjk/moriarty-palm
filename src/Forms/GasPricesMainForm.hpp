#ifndef MORIARTY_GAS_PRICES_MAIN_FORM_HPP__
#define MORIARTY_GAS_PRICES_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include "MoriartyPreferences.hpp"
#include <FormObject.hpp>
#include <HmStyleList.hpp>

class GasPricesMainForm: public MoriartyForm {

    Preferences::GasPricesPreferences* preferences_;
    
    HmStyleList gasList_;
    Control doneButton_;
    Control updateButton_;
    Control changeLocationButton_;
    
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr gasListDrawHandler_;
    
    void updateTitle();
        
public:

    explicit GasPricesMainForm(MoriartyApplication& app);
    
    ~GasPricesMainForm();

private:
    
    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup(LookupManager& lookupManager);
    
    void handleListItemSelect(uint_t listId, uint_t itemId);
    
    void handleUpdateButton();

    void handleChangeLocationButton();

    void updateGasList();
    
    void setVersion(Preferences::GasPricesPreferences::Version version);
    
    void inlineInformation(uint_t item);

    void popupFormInformation(uint_t item);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
    void draw(UInt16 updateCode=frmRedrawUpdateCode);
    
};

#endif