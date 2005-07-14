#ifndef MORIARTY_STOCKS_MAIN_FORM_HPP__
#define MORIARTY_STOCKS_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include "MoriartyPreferences.hpp"
#include <FormObject.hpp>
#include <HmStyleList.hpp>

class Definition;

class StocksMainForm: public MoriartyForm {

    Preferences::StocksPreferences* preferences_;
    
    HmStyleList stocksList_;
    Control doneButton_;
    Control updateButton_;
    Control addButton_;
    
    bool fIsAddingPortfolio_;
    
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr stocksListDrawHandler_;
    
    uint_t currentStockIndex_;
    uint_t downloadingStockIndex_;
    uint_t byNameDownloadingStockIndex_;
    enum {stockIndexNone=uint_t(-1)};

    void updateTitle();
        
public:

    explicit StocksMainForm(MoriartyApplication& app);
    
    ~StocksMainForm();

private:
    
    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup(LookupManager& lookupManager);
    
    void handleSearch();
    
    void handleListItemSelect(uint_t listId, uint_t itemId);
    
    void updateStocks();
    
    void updateTotalValue();

    void showStock();
    
    void switchPortfolio();
    
    void synchronizePortfolio(Preferences::StocksPreferences::Portfolios& portfolio, const std::vector<ArsLexis::String>& vec);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
};

#endif