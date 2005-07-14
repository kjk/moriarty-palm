#ifndef _LYRICS2_MAIN_FORM_HPP__
#define _LYRICS2_MAIN_FORM_HPP__

#include <FormObject.hpp>
#include <TextRenderer.hpp>
#include <HistorySupport.hpp>
#include <UniversalDataFormat.hpp>
#include "MoriartyPreferences.hpp"
#include "MoriartyForm.hpp"

class Lyrics2MainForm: public MoriartyForm {
    
    TextRenderer    textRenderer_;

    HistorySupport  historySupport_;

    ScrollBar   scrollBar_;
    Control     doneButton_;
    Control     searchButton_;
    Control     historyButton_;
    
public:

    explicit Lyrics2MainForm(MoriartyApplication& app);
    
    ~Lyrics2MainForm();

    void setUDF(UniversalDataFormat *udf);

    void showStartText();

private:
    
    void handleControlSelect(const EventType& data);
    
    void handleLookupFinished(const EventType& event);
    
    void handleSearch();

protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
};

#endif
