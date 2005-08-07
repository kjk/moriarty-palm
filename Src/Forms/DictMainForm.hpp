#ifndef MORIARTY_DICT_MAIN_FORM_HPP__
#define MORIARTY_DICT_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>
#include <HistorySupport.hpp>

class DictMainForm: public MoriartyForm
{
    ScrollBar       scrollBar_;
    TextRenderer    textRenderer_;
    Control         doneButton_;
    Control         searchButton_;
    Control         historyButton_;
    HistorySupport  historySupport_;
    char_t *        searchTerm_;

public:

    explicit DictMainForm(MoriartyApplication& app);

    ~DictMainForm();

    void showMain();

    void randomWord();

    void changeDict(void);

    void handleSearch();

    void handleHistory();

private:

    bool handleControlSelect(const EventType& data);

    void handleLookupFinished(const EventType& event);

    void updateAfterLookup(LookupManager& lookupManager);

protected:

    void search(const char_t* text);

    void readUdf();

    void attachControls();

    bool handleOpen();

    void resize(const ArsRectangle& screenBounds);

    bool handleEvent(EventType& event);

    bool handleMenuCommand(UInt16 itemId);

};

#endif
