#ifndef __MAINFORM_HPP__
#define __MAINFORM_HPP__

#include <Graphics.hpp>
#include "MoriartyApplication.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <HmStyleList.hpp>
#include "MoviesData.hpp"
#include <UniversalDataFormat.hpp>
#include <TextRenderer.hpp>

class LookupManager;

class MoviesMainForm: public MoriartyForm
{
    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr theatresListDrawHandler_;
    ListDrawHandlerPtr moviesListDrawHandler_;
    
    HmStyleList  theatresList_;
    HmStyleList  moviesList_;
    ScrollBar    definitionScrollBar_;
    TextRenderer infoRenderer_;
    Control      theatresButton_;
    Control      moviesButton_;
    Control      doneBackButton_;
    
    void handleScrollRepeat(const EventType& data);
    
    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void scrollTheatresListToLetter(char l);
    
    void setControlsState(bool enabled);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup(LookupManager& lookupManager);
    
    void prepareTheatreInfo(uint_t theatre);
    
    void prepareMovieInfo(uint_t movie);
    
    void handleListItemSelect(UInt16 listId, UInt16 itemId);
    
    void handleSelectItemEvent(const EventType& event);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);

    void updateMoviesTitle(void);

public:
    
    const UniversalDataFormat* theatres;
    Movies_t movies;

    MoviesMainForm(MoriartyApplication& app);
    
    ~MoviesMainForm();
    
    enum DisplayMode
    {
        showTheatres,
        showMovies,
        showDetailedInfo
    };
    
    DisplayMode displayMode() const
    {return displayMode_;}

    void setDisplayMode(DisplayMode displayMode);
    
private:
    
    UInt32 lastPenDownTimestamp_;
    DisplayMode displayMode_:4;
    DisplayMode invisibleDisplayMode_:4;
  
    friend class MoviesHyperlinkHandler;

};

#endif
