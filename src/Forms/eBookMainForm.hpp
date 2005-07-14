#ifndef MORIARTY_EBOOK_MAIN_FORM_HPP__
#define MORIARTY_EBOOK_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>
#include <HistorySupport.hpp>

//class CStrPListModel;

class EBookMainForm: public MoriartyForm
{
    ScrollBar       scrollBar_;
    TextRenderer    infoRenderer_;
    Control         doneButton_;
    Control         searchButton_;
    Control         historyButton_;
    
    DefinitionModel* searchResults_;
    DefinitionModel* browseResults_;

    HistorySupport  historySupport_;
    Definition::RenderingProgressReporter* renderingProgressReporter_;
    
    char* lastSearchPhrase_;

    void prepareDownloadedEBooks();

public:

    enum SearchType {
        searchAny,
        searchAuthor,
        searchTitle
    };

    explicit EBookMainForm(MoriartyApplication& app);

    ~EBookMainForm();

    enum DisplayMode {
        showSearchResults,
        showBrowseResults,
        showDownloadedEBooks,
    };

    void setDisplayMode(DisplayMode dm);

    DisplayMode displayMode() const
    {return displayMode_;}

    void handleAbout();
    
    void handleSearch();
    
    void manage();
    
    void refreshDownloadedEBooks();
    
private:

    void home();

    void search(const char_t* phrase, SearchType type = searchAny);
    
    DisplayMode displayMode_;

    bool handleControlSelect(const EventType& data);

    void handleLookupFinished(const EventType& event);

    void updateAfterLookup(LookupManager& lookupManager);

protected:

    void attachControls();

    bool handleOpen();

    void resize(const ArsRectangle& screenBounds);

    bool handleEvent(EventType& event);

    bool handleMenuCommand(UInt16 itemId);

};

#endif