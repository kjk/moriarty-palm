#ifndef MORIARTY_JOKES_MAIN_FORM_HPP__
#define MORIARTY_JOKES_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <HmStyleList.hpp>
#include <TextRenderer.hpp>

class JokesMainForm: public MoriartyForm {

    HmStyleList jokesList_;
    ScrollBar scrollBar_;
    Control doneButton_;
    Control searchButton_;
    Control listButton_;
    Control randomButton_;
    
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr jokesListDrawHandler_;
    
    TextRenderer jokeRenderer_;
    
    uint_t currentJokeIndex_;
    uint_t downloadingJokeIndex_;
    enum {jokeIndexNone=uint_t(-1)};
    
public:

    explicit JokesMainForm(MoriartyApplication& app);
    
    ~JokesMainForm();

    enum DisplayMode {
        showJokesList,
        showJoke
    };
    
    void setDisplayMode(DisplayMode dm);
    
    DisplayMode displayMode() const
    {return displayMode_;}
    
private:
    
    DisplayMode displayMode_;

    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup(LookupManager& lookupManager);
    
    void handleSearch();
    
    void prepareJoke();

    void handleListItemSelect(uint_t listId, uint_t itemId);
    
    void updateTitle();
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
};

#endif