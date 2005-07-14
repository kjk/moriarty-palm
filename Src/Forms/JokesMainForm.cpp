#include <SysUtils.hpp>
#include <Text.hpp>
#include <DynStr.hpp>

#include <Definition.hpp>
#include <TextElement.hpp>
#include <LineBreakElement.hpp>

#include "MoriartyPreferences.hpp"
#include "LookupManager.hpp"
#include "JokesMainForm.hpp"

#include "MoriartyStyles.hpp"

enum {
    jokesListItemRankIndex,
    jokesListItemTitleIndex,
    jokesListItemRatingIndex,
    jokesListItemExplicitnessIndex,
    jokesListItemUrlIndex,
    jokesListItemElementsCount
};

enum {
    jokeTitleIndex,
    jokeTextIndex,
    jokeElementsCount
};

class JokesListDrawHandler: public BasicStringItemRenderer {

    const UniversalDataFormat& jokes_;
    
public:
    
    explicit JokesListDrawHandler(const UniversalDataFormat& m): jokes_(m) {}
    
    uint_t itemsCount() const
    {
        return jokes_.getItemsCount();
    }

    ~JokesListDrawHandler();

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);
    
protected:
    
    void getItem(String& out, uint_t item)
    {
        assert(item < jokes_.getItemsCount());
        assert(jokesListItemElementsCount == jokes_.getItemElementsCount(item));
        out.assign(jokes_.getItemText(item, jokesListItemTitleIndex));
    }
    
};

JokesListDrawHandler::~JokesListDrawHandler() {}

void JokesListDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    assert(item < jokes_.getItemsCount());
    assert(jokesListItemElementsCount == jokes_.getItemElementsCount(item));
    
    uint_t width = itemBounds.width();
    uint_t length;
    ulong_t lengthLong;

    const char_t *text = jokes_.getItemTextAndLen(item,jokesListItemTitleIndex, &lengthLong);
    length = lengthLong;
    graphics.charsInWidth(text, length, width);
    graphics.drawText(text, length, itemBounds.topLeft);

    Point newPoint = itemBounds.topLeft;
    newPoint.y += itemBounds.height()/2;

    text = jokes_.getItemTextAndLen(item,jokesListItemRankIndex, &lengthLong);
    length = lengthLong;
    width = itemBounds.width();
    graphics.charsInWidth(text, length, width);
    graphics.drawText(text, length, newPoint);
    if (0 != length)
        newPoint.x += itemBounds.width()/4;

    text = jokes_.getItemTextAndLen(item, jokesListItemRatingIndex, &lengthLong);
    length = lengthLong;
    char_t *textCopy = StringCopy(text);
    if (NULL == textCopy)
        return;
    localizeNumberStrInPlace(textCopy);
    width = itemBounds.width();
    graphics.charsInWidth(textCopy, length, width);
    graphics.drawText(textCopy, length, newPoint);
    delete [] textCopy;

    text = jokes_.getItemTextAndLen(item,jokesListItemExplicitnessIndex, &lengthLong);
    length = lengthLong;
    width = itemBounds.width();
    graphics.charsInWidth(text, length, width);
    newPoint.x = itemBounds.width() - width - 1;
    graphics.drawText(text, length, newPoint);
}

JokesMainForm::JokesMainForm(MoriartyApplication& app):
    MoriartyForm(app, jokesMainForm),
    jokesList_(*this),
    scrollBar_(*this),
    doneButton_(*this),
    searchButton_(*this),
    listButton_(*this),
    randomButton_(*this),
    displayMode_(showJokesList),
    downloadingJokeIndex_(jokeIndexNone),
    currentJokeIndex_(jokeIndexNone),
    jokeRenderer_(*this, &scrollBar_)
{
    jokeRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    setFocusControlId(randomButton);
}

JokesMainForm::~JokesMainForm() 
{
}

void JokesMainForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    doneButton_.attach(doneButton);
    randomButton_.attach(randomButton);
    searchButton_.attach(searchButton);
    listButton_.attach(listButton);
    jokeRenderer_.attach(jokeRenderer);
    jokeRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);

    jokesList_.attach(jokesList);
    jokesList_.setUpBitmapId(upBitmap);
    jokesList_.setDownBitmapId(downBitmap);
}

bool JokesMainForm::handleOpen()
{
    bool result=MoriartyForm::handleOpen();
    
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL != lookupManager);
    jokesList_.setItemHeight(24);
    jokesListDrawHandler_.reset(new JokesListDrawHandler(lookupManager->jokes));
    jokesList_.setCustomDrawHandler(jokesListDrawHandler_.get());
    if (0 != jokesList_.itemsCount())
        jokesList_.setSelection(0);
    
    if (0 != lookupManager->joke.getItemsCount())
        setDisplayMode(showJoke);
    else if (0 != jokesList_.itemsCount())
        setDisplayMode(showJokesList);
    else
        setDisplayMode(displayMode_);

    return result;
}

void JokesMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(bounds = screenBounds);

    jokesList_.anchor(screenBounds, anchorRightEdge, 0, anchorBottomEdge, 36);
    jokesList_.adjustVisibleItems();

    jokeRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    searchButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    listButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    randomButton_.anchor(screenBounds, anchorLeftEdge, 66, anchorTopEdge, 14);
    update();    
}

bool JokesMainForm::handleEvent(EventType& event)
{
        
    if (showJoke == displayMode_ && jokeRenderer_.handleEventInForm(event))
        return true;
        
    bool handled=false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled = true;
            break;
            
        case lstSelectEvent:
            handleListItemSelect(event.data.lstSelect.listID, event.data.lstSelect.selection);
            handled = true;
            break;
            
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;

        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled = true;
            break;
            
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool JokesMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled = false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            handled = true;
            break;

        case viewJokeMenuItem:
            handled = true;
            if (showJoke == displayMode_)
                break;
            LookupManager* lookupManager = application().lookupManager;
            assert(NULL != lookupManager);
            if (!lookupManager->joke.empty())
            {
                setDisplayMode(showJoke);
                update();
            }
            break;

        case viewJokesListMenuItem:
            handled = true;
            if (showJokesList == displayMode_)
                break;
            if (1 > jokesList_.itemsCount())
                break;
            setDisplayMode(showJokesList);
            update();
            break;

        case viewFindJokeMenuItem:
            handled = true;
            searchButton_.hit();
            break;

        case randomMenuItem:
            handled = true;
            randomButton_.hit();
            break;

        default:
            assert(false);
    }
    return handled;
}

void JokesMainForm::setDisplayMode(JokesMainForm::DisplayMode dm)
{
    switch (displayMode_=dm)
    {
        case showJokesList:
            jokeRenderer_.hide();
            scrollBar_.hide();
            listButton_.hide();
            jokesList_.notifyItemsChanged();
            jokesList_.show();
            randomButton_.show();
            searchButton_.show();
            if (0 != jokesList_.itemsCount())
                jokesList_.focus();
            else
                randomButton_.focus();
            break;
            
        case showJoke:
            if (jokeRenderer_.empty())
                prepareJoke();
            jokesList_.hide();
            LookupManager* lookupManager = application().lookupManager;
            assert(NULL != lookupManager);
            if (lookupManager->jokes.empty())
            {
                listButton_.hide();
                searchButton_.show();
            }
            else
            {
                searchButton_.hide();
                listButton_.show();
            }
            jokeRenderer_.show();
            scrollBar_.show();
            randomButton_.show();
            randomButton_.focus();
            break;  
            
        default:
            assert(false);
    }
    updateTitle();    
}

void JokesMainForm::handleSearch()
{
    Application::popupForm(jokesSearchForm);
}

void JokesMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;
            
        case searchButton:
            handleSearch();
            break;
        case listButton:
            setDisplayMode(showJokesList);
            break;

        case randomButton:
            {
                LookupManager* lookupManager=application().lookupManager;
                assert(NULL != lookupManager);
                lookupManager->fetchJoke(_T("random"));
            }
            break;

        default:
            assert(false);
    }
}

void JokesMainForm::prepareJoke()
{
    const LookupManager* lookupManager=application().lookupManager;
    assert(0!=lookupManager);

    const UniversalDataFormat& joke=lookupManager->joke;
    assert(!joke.empty());
    
    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    
    Definition::Elements_t& elems = model->elements;
    TextElement* text;

    elems.push_back(text=new TextElement(joke.getItemText(0, jokeTitleIndex)));
    text->setStyle(StyleGetStaticStyle(styleNamePageTitle));
    text->setJustification(DefinitionElement::justifyCenter);
  
    elems.push_back(new LineBreakElement());
    elems.push_back(new LineBreakElement());

    String str;
    str = joke.getItemText(0, jokeTextIndex);
    parseSimpleFormatting(elems, str);
    jokeRenderer_.setModel(model, Definition::ownModel);
}

void JokesMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    switch (data.result)
    {
        case lookupResultJokesList:
            jokesList_.notifyItemsChanged();
            if (jokesList_.itemsCount()>0) 
                jokesList_.setSelection(0);
            else
                jokesList_.setSelection(noListSelection);
            if (showJokesList != displayMode_)
                setDisplayMode(showJokesList);
            else 
                jokesList_.draw();
            currentJokeIndex_ = jokeIndexNone;
            downloadingJokeIndex_ = jokeIndexNone;
            break;
            
        case lookupResultJoke:
            currentJokeIndex_ = downloadingJokeIndex_;
            prepareJoke();
            if (showJoke != displayMode_)
                setDisplayMode(showJoke);
            else
                updateTitle();
            break;
    }
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(0!=lookupManager);
    lookupManager->handleLookupFinishedInForm(data);
}

void JokesMainForm::handleListItemSelect(uint_t listId, uint_t itemId)
{
    assert(jokesList==listId);
    LookupManager* lookupManager=application().lookupManager;
    assert(0!=lookupManager);
    assert(itemId < lookupManager->jokes.getItemsCount());
    assert(jokesListItemElementsCount == lookupManager->jokes.getItemElementsCount(itemId));
    if (currentJokeIndex_!=itemId)
    {
        downloadingJokeIndex_=itemId;
        lookupManager->fetchJoke(lookupManager->jokes.getItemText(itemId, jokesListItemUrlIndex));
    }
    else
    {
        setDisplayMode(showJoke);
        update();
    }
}

bool JokesMainForm::handleKeyPress(const EventType& event)
{
    bool handled = false;
    int option = List::optionScrollPagesWithLeftRight;
    if (application().runningOnTreo600())
        option = 0;
    if (showJokesList == displayMode_ && jokesList_.handleKeyDownEvent(event, option | List::optionFireListSelectOnCenter))
        return true;

    if (!application().runningOnTreo600() && fiveWayCenterPressed(&event))
    {
        randomButton_.hit();
        handled = true;
    }
    return handled;
}

void JokesMainForm::updateTitle()
{
    DynStr *title = NULL;
    char_t *number = NULL;

    switch (displayMode_)
    {
        case showJokesList:
            setTitle(_T("Jokes"));
            break;
            
        case showJoke:
            LookupManager* lookupManager = application().lookupManager;
            assert(NULL != lookupManager);
            if (2 < lookupManager->joke.getItemElementsCount(0))
            {
                title = DynStrFromCharP(_T("Joke rating: "), 16);
                if (NULL == title)
                    goto Exit;
                number = StringCopy2(lookupManager->joke.getItemText(0,2));
                if (NULL == number)
                    goto Exit;
                localizeNumberStrInPlace(number);
                if (NULL == DynStrAppendCharP(title, number))
                    goto Exit;
                setTitle(DynStrGetCStr(title));
            }    
            else
                setTitle(_T("Jokes"));
            break;
    }
    update();
Exit:
    if (NULL != title)
        DynStrDelete(title);
    if (NULL != number)
        free(number);
}

