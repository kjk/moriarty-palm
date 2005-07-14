#ifndef _QUOTES_MAIN_FORM_HPP__
#define _QUOTES_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

#include <TextRenderer.hpp>
#include "HyperlinkHandler.hpp"
#include <PopupMenu.hpp>

class QuotesMainForm: public MoriartyForm {

    TextRenderer textRenderer_;
    
    Control doneButton_;
    Control dailyButton_;
    Control randomButton_;
    ScrollBar scrollBar_;
    
public:

    explicit QuotesMainForm(MoriartyApplication& app);
    
    ~QuotesMainForm();

    void handleDaily();

    void handleRandom();

    void showMain();

private:
    
    void readUdf();
    
    void handleControlSelect(const EventType& data);
    
    void handleLookupFinished(const EventType& event);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
};

#endif