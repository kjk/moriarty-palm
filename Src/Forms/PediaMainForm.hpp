#ifndef MORIARTY_PEDIA_MAIN_FORM_HPP__
#define MORIARTY_PEDIA_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>
#include <HistorySupport.hpp>

//class CStrPListModel;

class PediaMainForm: public MoriartyForm
{
    ScrollBar       scrollBar_;
    TextRenderer    infoRenderer_;
    TextRenderer    articleRenderer_;
//    CStrPListModel* listModel_;
    Control         doneButton_;
    Control         searchButton_;
    Control         historyButton_;

    HistorySupport  historySupport_;
    Definition::RenderingProgressReporter* renderingProgressReporter_;

    void clearLangCodes();

    char_t** availLangCodes_;
    ulong_t availLangCodesCount_;

    char_t* searchTerm_;

    char_t* articleTitle_;
    char_t* searchTitle_;

    void search(const char_t * term, bool extended);

    void prepareAbout();

    void fetchStats() const;

public:

    explicit PediaMainForm(MoriartyApplication& app);

    ~PediaMainForm();

    enum DisplayMode {
        showArticle,
        showSearchResults,
        showLinkingArticles,
        showLinkedArticles,
        showLanguages,
        showAbout
    };

    void invalidateRenderers();

    void setDisplayMode(DisplayMode dm);

    DisplayMode displayMode() const
    {return displayMode_;}

    void handleSearch();

    void handleAbout();

    void handleArticle();

    void changeLanguage(const char_t* code);

private:

    DisplayMode displayMode_;

    bool handleControlSelect(const EventType& data);

    void handleLookupFinished(const EventType& event);

    void updateAfterLookup(LookupManager& lookupManager);

    void randomArticle();

    void switchListDisplayMode(DisplayMode dm, char_t** list, ulong_t count);

protected:

    void attachControls();

    bool handleOpen();

    void resize(const ArsRectangle& screenBounds);

    bool handleEvent(EventType& event);

    bool handleMenuCommand(UInt16 itemId);

};

#endif