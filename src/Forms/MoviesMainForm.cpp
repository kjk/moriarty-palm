#include <algorithm>
#include <SysUtils.hpp>
#include <Text.hpp>
#include <DynStr.hpp>

#include <TextElement.hpp>
#include <LineBreakELement.hpp>
#include <HorizontalLineElement.hpp>
#include <BulletElement.hpp>

#include "LookupManager.hpp"
#include "MoriartyPreferences.hpp"

#include "MoviesMainForm.hpp"
#include "HyperlinkHandler.hpp"

#include "MoriartyStyles.hpp"

class TheatreListDrawHandler: public BasicStringItemRenderer {
    
    const UniversalDataFormat& theatres_;
        
public:
    
    TheatreListDrawHandler(const UniversalDataFormat& th):
        theatres_(th) {}
        
    uint_t itemsCount() const
    {return theatres_.getItemsCount()/2;}

    ~TheatreListDrawHandler();

protected:

    void getItem(String& out, uint_t item)
    {
        assert(item < theatres_.getItemsCount()/2);
        out.assign(theatres_.getItemText(item*2, 0));
    }
    
};

TheatreListDrawHandler::~TheatreListDrawHandler()
{}

class MovieListDrawHandler: public BasicStringItemRenderer {
    
    const Movies_t& movies_;
        
public:
    
    MovieListDrawHandler(const Movies_t& mv):
        movies_(mv) {}
        
    uint_t itemsCount() const
    {return movies_.size();}

    ~MovieListDrawHandler();
    
protected:

    void getItem(String& out, uint_t item)
    {out.assign(movies_[item]->title);}
    
};

MovieListDrawHandler::~MovieListDrawHandler()
{}

struct MovieTitleFirstLetterLess {
    bool operator()(const Movie* m1, const Movie* m2) const
    {
        return toLower(m1->title[0]) < toLower(m2->title[0]);
    }
};

MoviesMainForm::~MoviesMainForm()
{
    std::for_each(movies.begin(), movies.end(), ObjectDeleter<Movie>());
}

MoviesMainForm::MoviesMainForm(MoriartyApplication& app):
    MoriartyForm(app, moviesMainForm),
    theatres(NULL),
    displayMode_(showTheatres),
    invisibleDisplayMode_(showTheatres),
    theatresList_(*this),
    moviesList_(*this),
    definitionScrollBar_(*this),
    theatresButton_(*this),
    moviesButton_(*this),
    doneBackButton_(*this),
    infoRenderer_(*this, &definitionScrollBar_)
{
    infoRenderer_.setInteractionBehavior(
        TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavUpDownScroll
      | TextRenderer::behavMenuBarCopyButton
    );  

    infoRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    setFocusControlId(theatresList);
}

void MoviesMainForm::attachControls()
{
    MoriartyForm::attachControls();
    theatresList_.attach(theatresList);
    moviesList_.attach(moviesList);
    definitionScrollBar_.attach(definitionScrollBar);
    infoRenderer_.attach(infoRenderer);
    infoRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
    
    theatresButton_.attach(theatresButton);
    moviesButton_.attach(moviesButton);
    doneBackButton_.attach(doneBackButton);

    moviesList_.setUpBitmapId(upBitmap);
    moviesList_.setDownBitmapId(downBitmap);
    moviesList_.setItemHeight(12);

    theatresList_.setUpBitmapId(upBitmap);
    theatresList_.setDownBitmapId(downBitmap);
    theatresList_.setItemHeight(12);
}

bool MoviesMainForm::handleOpen()
{
    bool res = MoriartyForm::handleOpen();
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL != lookupManager);
    theatres = &lookupManager->moviesData;
    theatresList_.notifyItemsChanged();

    setDisplayMode(displayMode_);
    if (theatres->empty()  && !app.preferences().moviesLocation.empty())
        sendEvent(MoriartyApplication::appFetchMoviesEvent);
    else if (app.preferences().moviesLocation.empty())
        Application::popupForm(changeLocationForm);
    else
        updateMoviesTitle();
        
    return res;
}

void MoviesMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(screenBounds);
    
    theatresList_.anchor(screenBounds, anchorRightEdge, 0, anchorBottomEdge, 36);
    theatresList_.adjustVisibleItems();

    moviesList_.anchor(screenBounds, anchorRightEdge, 0, anchorBottomEdge, 36);
    moviesList_.adjustVisibleItems();

    definitionScrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);

    infoRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);

    static const uint_t buttonsTopEdge = 14;
    
    doneBackButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, buttonsTopEdge);

    moviesButton_.bounds(bounds);
    bounds.y() = screenBounds.dy() - buttonsTopEdge;
    bounds.x() = screenBounds.dx() - bounds.dx() - 2;
    moviesButton_.setBounds(bounds);
    int moviesX = bounds.x();

    theatresButton_.bounds(bounds);
    bounds.y() = screenBounds.dy() - buttonsTopEdge;
    bounds.x() = moviesX - bounds.dx() - 4;
    theatresButton_.setBounds(bounds);

    update();    
}

void MoviesMainForm::handleControlSelect(const EventType& event)
{
    MoriartyApplication& app=application();
    switch (event.data.ctlSelect.controlID)
    {
        case theatresButton:
            if (showTheatres==displayMode())
                break;
            infoRenderer_.clear();
            if (NULL != theatres)
            {
                setDisplayMode(showTheatres);
                update();
            }
            break;

        case moviesButton:
            if (showMovies==displayMode())
                break;
            infoRenderer_.clear();
            if (NULL != theatres)
            {
                setDisplayMode(showMovies);
                update();
            }
            break;

        case doneBackButton:
            if (showDetailedInfo == displayMode_ )
            {
                if (showMovies == invisibleDisplayMode_)
                    setDisplayMode(showMovies);
                else
                    setDisplayMode(showTheatres);
                update();
            }
            else
                application().runMainForm();
            break;            

        default:
            assert(false);
    }
}

// TODO: check that updateMoviesTitle() is called in correct places (i.e. we
// need to have the location present, either from previous cached data or
// after changing the location
void MoviesMainForm::updateMoviesTitle(void)
{
    DynStr *title = DynStrFromCharP(_T("Movies for '"), 32);
    if (NULL == title)
        goto Exit;

    const MoriartyApplication& app=application(); 
    
    if (NULL == DynStrAppendCharP(title, app.preferences().moviesLocation.c_str()))
        goto Exit;
    
    if (NULL == DynStrAppendChar(title, _T('\'')))
        goto Exit;
    setTitle(DynStrGetCStr(title));
Exit:
    if (NULL != title)
        DynStrDelete(title);
}

void MoviesMainForm::updateAfterLookup(LookupManager& lookupManager)
{
    std::for_each(movies.begin(), movies.end(), ObjectDeleter<Movie>());
    movies.clear();
    theatres = &lookupManager.moviesData;
    theatresList_.notifyItemsChanged();
    moviesList_.notifyItemsChanged();            
    setDisplayMode(invisibleDisplayMode_);
    updateMoviesTitle();
    update();
}

void MoviesMainForm::handleLookupFinished(const EventType& event)
{
    bool closeForm = false;
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(0!=lookupManager);
    
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    switch (data.result)
    {
        case lookupResultMoviesData:
            updateAfterLookup(*lookupManager);
            MoriartyApplication::touchModule(moduleIdMovies);
            break;

        case lookupResultLocationAmbiguous:
            Application::popupForm(selectLocationForm);
            break;

        default:
            if (application().preferences().moviesLocation.empty())
                closeForm = true;
            update();
    }

    lookupManager->handleLookupFinishedInForm(data);

    if (closeForm)
        application().runMainForm();
}

void MoviesMainForm::prepareTheatreInfo(uint_t theatreRow)
{
    assert(NULL != theatres);
    theatreRow *= 2;
    assert(theatreRow < theatres->getItemsCount());
    
    const char_t* theatreName = theatres->getItemText(theatreRow, theatreNameIndex);
    const char_t* theatreAddress = theatres->getItemText(theatreRow, theatreAddressIndex);

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    Definition::Elements_t& elems = model->elements;
    TextElement* text;
    elems.push_back(text=new TextElement(theatreName));
    text->setStyle(StyleGetStaticStyle(styleNamePageTitle));
    if (0 != tstrlen(theatreAddress))
    {
        elems.push_back(new LineBreakElement());
        elems.push_back(text=new TextElement(theatreAddress));
    }
    elems.push_back(new LineBreakElement());
    const uint_t moviesRow = theatreRow + 1;
    const uint_t moviesCount = theatres->getItemElementsCount(moviesRow)/2;
    for (uint_t i = 0; i<moviesCount; ++i)
    {   
        const char_t* movieTitle = theatres->getItemText(moviesRow, i*2);
        const char_t* movieHours = theatres->getItemText(moviesRow, i*2+1);
        BulletElement* bull;
        elems.push_back(bull = new BulletElement());
        bull->setStyle(StyleGetStaticStyle(styleNameHeader));
        elems.push_back(text=new TextElement(movieTitle));
        text->setParent(bull);
        text->setStyle(StyleGetStaticStyle(styleNameHeader));
        text->setHyperlink(buildUrl(urlSchemaMovie, movieTitle), hyperlinkUrl);
        elems.push_back(new LineBreakElement());
        elems.push_back(text=new TextElement(movieHours));
        text->setParent(bull);
    }
    infoRenderer_.setModel(model, Definition::ownModel);
}

void MoviesMainForm::prepareMovieInfo(uint_t movie)
{
    assert(movie < movies.size());
    const Movie& mv=*(movies[movie]);
    
    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    Definition::Elements_t& elems = model->elements;

    TextElement* text;
    elems.push_back(text=new TextElement(mv.title));
    text->setStyle(StyleGetStaticStyle(styleNamePageTitle));

    elems.push_back(new LineBreakElement());

    Movie::TheatresByMovie_t::const_iterator end=mv.theatres.end();
    for (Movie::TheatresByMovie_t::const_iterator it=mv.theatres.begin(); it!=end; ++it)
    {   
        const TheatreByMovie& th=*(*it);
        BulletElement* bull;
        elems.push_back(bull=new BulletElement());
        bull->setStyle(StyleGetStaticStyle(styleNameHeader));
        elems.push_back(text=new TextElement(th.name));
        text->setParent(bull);
        text->setStyle(StyleGetStaticStyle(styleNameHeader));
        text->setHyperlink(buildUrl(urlSchemaTheatre, th.name.c_str()), hyperlinkUrl);
        elems.push_back(new LineBreakElement());
        elems.push_back(text=new TextElement(th.hours));
        text->setParent(bull);
    }
    infoRenderer_.setModel(model, Definition::ownModel);
}

void MoviesMainForm::handleListItemSelect(UInt16 listId, UInt16 itemId)
{
    switch (displayMode())
    {
        case showTheatres:
            sendEvent(MoriartyApplication::appSelectTheatreEvent, MoriartyApplication::SelectItemEventData(itemId));
            break;
            
        case showMovies:
            sendEvent(MoriartyApplication::appSelectMovieEvent, MoriartyApplication::SelectItemEventData(itemId));            
            break;
            
        default:
            assert(false);
    }
}

void MoviesMainForm::handleSelectItemEvent(const EventType& event)
{
    const MoriartyApplication::SelectItemEventData& data = reinterpret_cast<const MoriartyApplication::SelectItemEventData&>(event.data);
    if (MoriartyApplication::appSelectMovieEvent == event.eType)
        prepareMovieInfo(data.item);
    else
        prepareTheatreInfo(data.item);
    setDisplayMode(showDetailedInfo);
    update();
}

bool MoviesMainForm::handleEvent(EventType& event)
{

    if (showDetailedInfo == displayMode_ && infoRenderer_.handleEventInForm(event))
        return true;
        
    bool handled = false;
    switch (event.eType)
    {
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;
            
        case ctlSelectEvent:
            handleControlSelect(event);
            break;
        
        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled = true;
            break;     
            
        case lstSelectEvent:
            handleListItemSelect(event.data.lstSelect.listID, event.data.lstSelect.selection);
            break;

        case MoriartyApplication::appSelectMovieEvent:
        case MoriartyApplication::appSelectTheatreEvent:
            handleSelectItemEvent(event);
            handled = true;
            break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool MoviesMainForm::handleKeyPress(const EventType& event)
{
    if (showTheatres == displayMode_ || showMovies == displayMode_)
    {
        ExtendedList& list = (showTheatres==displayMode()?theatresList_:moviesList_);
        int option = ExtendedList::optionScrollPagesWithLeftRight;
        if (application().runningOnTreo600())
            option = 0;
        if (list.handleKeyDownEvent(event, option | ExtendedList::optionFireListSelectOnCenter))
            return true;
        if (isAlNum(event.data.keyDown.chr) && 256 > event.data.keyDown.chr)
        {
            if (showMovies == displayMode_)
            {
                Movie m;
                m.title.assign(1, event.data.keyDown.chr);
                int pos = std::lower_bound(movies.begin(), movies.end(), &m, MovieTitleFirstLetterLess()) - movies.begin();
                if (pos == movies.size())
                    --pos;
                moviesList_.setSelection(pos, ExtendedList::redraw);
            }
            else 
                scrollTheatresListToLetter(event.data.keyDown.chr);
            return true;
        }
    }
    return false;
}

bool MoviesMainForm::handleMenuCommand(UInt16 itemId)
{
    bool    handled = false;

    switch (itemId)
    {
        case changeLocationMenuItem:
            Application::popupForm(changeLocationForm);
            handled = true;
            break;

        case viewTheatresMenuItem:
            theatresButton_.hit();
            handled = true;
            break;

        case viewMoviesMenuItem:
            moviesButton_.hit();
            handled = true;
            break;

        case refreshDataMenuItem:
            MoriartyApplication& app=application();
            if (!app.preferences().moviesLocation.empty())
                sendEvent(MoriartyApplication::appFetchMoviesEvent);
            handled = true;
            break;

        case mainPageMenuItem:
            doneBackButton_.hit();
            handled = true;
            break;

        default:
            handled = MoriartyForm::handleMenuCommand(itemId);
    }
    return handled;
}

void MoviesMainForm::setDisplayMode(DisplayMode displayMode)
{
    switch (displayMode)
    {
        case showTheatres:
            invisibleDisplayMode_ = showTheatres;
            assert(NULL != theatres);
            if (0 == theatresListDrawHandler_.get())
            {
                theatresListDrawHandler_.reset(new TheatreListDrawHandler(*theatres));
                theatresList_.setCustomDrawHandler(theatresListDrawHandler_.get());
            }
            infoRenderer_.hide();
            definitionScrollBar_.hide();
            moviesList_.hide();
            theatresButton_.hide();
            moviesButton_.show();

            doneBackButton_.setLabel("Done");

            if (noListSelection == theatresList_.selection() && 0 != theatresList_.itemsCount())
                theatresList_.setSelection(0);
            theatresList_.show();
            theatresList_.focus();
            break;

        case showMovies:
            invisibleDisplayMode_ = showMovies;
            assert(NULL != theatres);
            if (movies.empty() && !theatres->empty()) 
                createMoviesFromTheatres(movies, *theatres);
            if (NULL == moviesListDrawHandler_.get())
            {
                moviesListDrawHandler_.reset(new MovieListDrawHandler(movies));
                moviesList_.setCustomDrawHandler(moviesListDrawHandler_.get());
            }
            else
                moviesList_.notifyItemsChanged();
            infoRenderer_.hide();
            definitionScrollBar_.hide();
            theatresList_.hide();
            theatresButton_.show();
            moviesButton_.hide();

            doneBackButton_.setLabel("Done");

            if (noListSelection == moviesList_.selection() && 0 != moviesList_.itemsCount())
                moviesList_.setSelection(0);
            moviesList_.show();
            moviesList_.focus();
            break;

        case showDetailedInfo:
            if (showDetailedInfo != displayMode_)
                invisibleDisplayMode_ = displayMode_;
            theatresList_.hide();
            moviesList_.hide();
            infoRenderer_.show();
            theatresButton_.show();
            moviesButton_.show();

            doneBackButton_.setLabel("Back");

            if (showMovies == invisibleDisplayMode_)
                moviesButton_.focus();
            else
                theatresButton_.focus();
            break;

        default:
            assert(false);
    }            
    displayMode_ = displayMode;
}

void MoviesMainForm::scrollTheatresListToLetter(char l) 
{
    assert(showTheatres == displayMode_);
    if (NULL == theatres || theatres->empty())
        return;
    l = toLower(l);
    uint_t index = 0;
    const uint_t theatresCount = theatres->getItemsCount()/2;
    while (index < theatresCount) 
    {
        const char* text = theatres->getItemText(index * 2, 0);
        if (toLower(*text) >= l)
            break;
        ++index;
    }
    if (theatresCount == index)
        --index;
    theatresList_.setSelection(index, ExtendedList::redraw);
}
