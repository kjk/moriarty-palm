#ifndef MORIARTY_STOCKS_ENTER_STOCK_FORM_HPP__
#define MORIARTY_STOCKS_ENTER_STOCK_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class StocksEnterStockForm: public MoriartyForm
{
    Field nameField_;
    Field numberField_;
    Field helpText1Field_;
    Field helpText2Field_;
    
    ArsLexis::String helpText1String_;
    ArsLexis::String helpText2String_;
    ArsLexis::String request_;

    void handleControlSelect(const EventType& data);

    void setHelpTexts(const ArsLexis::String& str1, const ArsLexis::String& str2);

    void showNumberField();
    
    unsigned long getNumberFieldValueUL();
    
protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleOpen();
    
public:

    enum Mode
    {
        modeAddStock,
        modeAddPortfolio,
        modeRenamePortfolio,
        modeSetQuantity,
        modeNetflixPosition,
        modeEBayBid
    };

    StocksEnterStockForm(MoriartyApplication& app, Mode mode, const char_t* request=NULL);
    
    ~StocksEnterStockForm();

private:
    
    Mode mode_;
    
    void setMode(Mode mode);
    
};

#endif