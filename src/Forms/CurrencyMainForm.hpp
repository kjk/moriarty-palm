#ifndef __CURRENCY_MAINFORM_HPP__
#define __CURRENCY_MAINFORM_HPP__

#include "MoriartyApplication.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <UniversalDataFormat.hpp>
#include <HmStyleList.hpp>

class LookupManager;

class CurrencyMainForm: public MoriartyForm
{
    UniversalDataFormat* currencyData_;
    double rate_;
    double amount_;
    
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr selCurrenciesListDrawHandler_;
    
    HmStyleList selCurrenciesList_;
    Control doneButton_;
    Control updateButton_;
    Control addButton_;
    Control deleteButton_;
    Field amountField_;
    Control amountLabel_;
    FormObject graffitiState_;

    ArsLexis::String lastAmount_;
    
    void updateAmountField();

    void changeSelection(uint_t sel);

    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup();

    void fetchCurrenciesList();
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
public:
    
    void amountFieldChanged();
    
    CurrencyMainForm(MoriartyApplication& app);
    
    ~CurrencyMainForm();
      
};

#endif
