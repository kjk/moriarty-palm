#ifndef _SELECT_CURRENCY_FORM_HPP_
#define _SELECT_CURRENCY_FORM_HPP_

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <HmStyleList.hpp>
#include "MoriartyPreferences.hpp"

class UniversalDataFormat;

class CurrencyListDrawHandler: public ExtendedList::CustomDrawHandler 
{
    const Preferences& prefs_;
    const UniversalDataFormat& currencyData_;
    double* amount_;
    double* rate_;
    
public: 

    enum {
        currenciesListItemLines = 1,
        currenciesListLineHeight = 12
    };
        
    enum Mode
    {
        modeAvailable,
        modeSelected
    };
    
private:

    Mode mode_;
    
public:

    CurrencyListDrawHandler(const UniversalDataFormat& currencyData);

    CurrencyListDrawHandler(const UniversalDataFormat& currencyData, double& amount, double& rate);

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);

    uint_t itemsCount() const;
    
    ~CurrencyListDrawHandler();
};
    

class SelectCurrencyForm: public MoriartyForm {

    HmStyleList currenciesList_;
    Control okButton_;
    Control cancelButton_;

    
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr currenciesListDrawHandler_;

    void handleControlSelected(const EventType& event);
    
    void handleListItemSelected(const EventType& event);

protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
public:

    SelectCurrencyForm(MoriartyApplication& app);
    
    ~SelectCurrencyForm();

private:

/*
    enum OkMode
    {
        defaultMode, //one selection possible
        multiselectMode
    };
    OkMode okMode_;
*/
};


#endif // _SELECT_CURRENCY_FORM_HPP_
