#include "JokesSearchForm.hpp"
#include "LookupManager.hpp"
#include <SysUtils.hpp>

enum {
    maxTypeLength=11,
    maxCategoryLength=14,
    maxExplicitnessLength = 6,
    maxRatingLength = 2,
    maxSortLength = 7
};

typedef const char_t TypeField_t[maxTypeLength];
typedef const char_t CategoryField_t[maxCategoryLength];
typedef const char_t ExplicitnessField_t[maxExplicitnessLength];
typedef const char_t RatingField_t[maxRatingLength];
typedef const char_t SortField_t[maxSortLength];

static const CategoryField_t categoryNames[]={
    "Blonde",
    "Entertainment",
    "Men/Women",
    "Insults",
    "Yo-Mama",
    "Lawyer",
    "News&Politics",
    "Redneck",
    "Barroom",
    "Gross",
    "Sports",
    "Foreign",
    "Whatever",
    "Medical",
    "Sexuality",
    " Animals",
    "Children",
    "Anti-Joke",
    "Bush",
    "College",
    "Farm",
    "Business",
    "Religious",
    "Tech"
};

static const TypeField_t typeNames[]={
    "Articles",
    "One-Liners",
    "QandA",
    "Sketches",
    "Stories",
    "Lists"
};

static const ExplicitnessField_t explicitnessNames[]={
    "Clean",
    "Tame",
    "Racy"
};

static const RatingField_t ratingNames[]={
    "0",
    "1",
    "2",
    "3",
    "4"
};
enum 
{
    ratingNamesCount = 5
};

static const SortField_t sortNames[]={
    "rating",
    "rank"
};
enum 
{
    sortNamesCount = 2
};

static void makeJokeStrings(String& category, String& type, String& explicitness, const Preferences::JokesPreferences& prefs)
{
    category.clear();
    type.clear();        
    explicitness.clear();
    for (int i=0; i < prefs.typeTableSize; i++)
    {
        if (prefs.fType[i])
            type.append(typeNames[i]).append(_T(" "));        
    }
    for (int i=0; i < prefs.categoryTableSize; i++)
    {
        if (prefs.fCategory[i])
            category.append(categoryNames[i]).append(_T(" "));        
    }
    for (int i=0; i < prefs.explicitnessTableSize; i++)
    {
        if (prefs.fExplicitness[i])
            explicitness.append(explicitnessNames[i]).append(_T(" "));        
    }
}

class PopupListDrawHandler: public List::CustomDrawHandler {

public:
    enum PopupMode
    {
        ratingMode,
        sortMode
    };

private:    
    PopupMode popupMode_;
                
public:
    
    PopupListDrawHandler(PopupMode mode):
        popupMode_(mode) {}
        
    uint_t itemsCount() const
    {
        switch(popupMode_)
        {
            case ratingMode:
                return ratingNamesCount;
            case sortMode:
                return sortNamesCount;
        }
        return 0;
    }

    void drawItem(Graphics& graphics, List& list, uint_t item, const ArsRectangle& itemBounds);

    ~PopupListDrawHandler() {};
    
};

void PopupListDrawHandler::drawItem(Graphics& graphics, List& list, uint_t item, const ArsRectangle& itemBounds)
{
    if (item>=itemsCount())
        return;
    uint_t width=itemBounds.width();
    String text;
    switch(popupMode_)
    {
        case ratingMode:
            text.assign(ratingNames[item]);
            break;
        case sortMode:
            text.assign(sortNames[item]);
            break;
    }
    uint_t length=text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    graphics.drawText(text.c_str(), length, itemBounds.topLeft);
}

class TableDrawHandler: public ExtendedList::CustomDrawHandler 
{
    const Preferences::JokesPreferences& prefs_;
    
public:
    
    enum TableMode
    {
        typeMode,
        categoryMode,
        explicitnessMode
    };    
    
private:

    TableMode tableMode_;
        
public:

    TableDrawHandler(const Preferences::JokesPreferences& prefs, TableMode mode): 
        tableMode_(mode),
        prefs_(prefs) {}

    ~TableDrawHandler() {};

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);

    uint_t itemsCount() const;
};

uint_t TableDrawHandler::itemsCount() const
{
    switch (tableMode_)
    {
        case typeMode:
            return prefs_.typeTableSize;
        case categoryMode:
            return prefs_.categoryTableSize;
        case explicitnessMode:
            return prefs_.explicitnessTableSize;
    }    
    return 0;
}

void TableDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    if (item>=itemsCount())
        return;
    
    String text;
    bool   checkState;
    
    switch (tableMode_)
    {
        case typeMode:
            checkState = prefs_.fType[item];
            text.assign(typeNames[item]);
            break;
        case categoryMode:
            checkState = prefs_.fCategory[item];
            text.assign(categoryNames[item]);
            break;
        case explicitnessMode:
            checkState = prefs_.fExplicitness[item];
            text.assign(explicitnessNames[item]);
            break;
    }    
    
    uint_t width=itemBounds.width();
    uint_t iconId = (checkState)?checkBoxSetBitmap:checkBoxUnsetBitmap;

    uint_t margin = 0;
    if (frmInvalidObjectId != iconId)
    {
        MemHandle handle=DmGet1Resource(bitmapRsc, iconId);
        if (handle) 
        {
            BitmapType* bmp=static_cast<BitmapType*>(MemHandleLock(handle));
            if (bmp) 
            {
                Coord bmpW, bmpH;
                UInt16 rowSize;
                BmpGetDimensions(bmp, &bmpW, &bmpH, &rowSize);
                int y = itemBounds.y()+(itemBounds.height()-bmpH)/2;
                WinDrawBitmap(bmp, itemBounds.x()+margin, y);
                width -= (margin += bmpW + 1);
                MemHandleUnlock(handle);
            }
            DmReleaseResource(handle);
        }
    }

    uint_t length = text.length();

    Graphics::FontSetter setFont(graphics, stdFont);
    graphics.charsInWidth(text.c_str(), length, width);
    Point p = itemBounds.topLeft;
    p.x += margin;
    p.y = itemBounds.y();
    graphics.drawText(text.c_str(), length, p);
}

JokesSearchForm::JokesSearchForm(MoriartyApplication& app):
    MoriartyForm(app, jokesSearchForm),
    okButton_(*this),
    cancelButton_(*this),
    categoryTable_(*this),
    typeTable_(*this),
    explicitnessTable_(*this),
    jokeRatingPopupTrigger_(*this),
    jokeRatingPopupList_(*this),
    jokeSortPopupTrigger_(*this),
    jokeSortPopupList_(*this),
    keywordField_(*this),
    graffitiState_(*this),
    jokeRatingPopupIndex_(0),
    jokeSortPopupIndex_(0)
{
    setFocusControlId(jokeKeywordField);
}

JokesSearchForm::~JokesSearchForm() 
{
}


void JokesSearchForm::attachControls()
{
    MoriartyForm::attachControls();
    //attach
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
    categoryTable_.attach(categoryTable);
    typeTable_.attach(typesTable);
    explicitnessTable_.attach(explicitnessTable);
    jokeRatingPopupTrigger_.attach(jokeRatingPopupTrigger);
    jokeRatingPopupList_.attach(jokeRatingPopupList);
    jokeSortPopupTrigger_.attach(jokeSortPopupTrigger);
    jokeSortPopupList_.attach(jokeSortPopupList);
    keywordField_.attach(jokeKeywordField);
    graffitiState_.attachByIndex(getGraffitiStateIndex());


    //set selection color - white    
    RGBColorType col;
    col.r = col.g = col.b = 255;

    categoryTable_.setBreakColor(col);
    categoryTable_.selectedItemBackgroundColor = col;

    typeTable_.setBreakColor(col);
    typeTable_.selectedItemBackgroundColor = col;

    explicitnessTable_.setBreakColor(col);
    explicitnessTable_.selectedItemBackgroundColor = col;

    //set up down bitmaps
    categoryTable_.setUpBitmapId(upBitmap); 
    categoryTable_.setDownBitmapId(downBitmap); 

    typeTable_.setUpBitmapId(upBitmap); 
    typeTable_.setDownBitmapId(downBitmap); 

    explicitnessTable_.setUpBitmapId(upBitmap); 
    explicitnessTable_.setDownBitmapId(downBitmap); 

}

bool JokesSearchForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();

    //hide popup lists
    jokeSortPopupList_.hide();
    jokeRatingPopupList_.hide();
   
    ratingPopupListDrawHandler_.reset(new PopupListDrawHandler(PopupListDrawHandler::ratingMode));
    jokeRatingPopupList_.setCustomDrawHandler(ratingPopupListDrawHandler_.get());
   
    sortPopupListDrawHandler_.reset(new PopupListDrawHandler(PopupListDrawHandler::sortMode));
    jokeSortPopupList_.setCustomDrawHandler(sortPopupListDrawHandler_.get());

    //get preferences
    prefs_ = application().preferences().jokesPreferences; 

    //popup triggers
    jokeSortPopupIndex_ = prefs_.sortOrder;
    if (0 > jokeSortPopupIndex_ || sortNamesCount <= jokeSortPopupIndex_)
        jokeSortPopupIndex_ = 0;
    jokeSortPopupTrigger_.setLabel(sortNames[jokeSortPopupIndex_]);

    jokeRatingPopupIndex_ = prefs_.minimumRating;
    if (0 > jokeRatingPopupIndex_ || ratingNamesCount <= jokeRatingPopupIndex_)
        jokeRatingPopupIndex_ = 0;
    jokeRatingPopupTrigger_.setLabel(ratingNames[jokeRatingPopupIndex_]);

    //set draw handlers
    typeTable_.setItemHeight(10);
    typeTableDrawHandler_.reset(new TableDrawHandler(prefs_, TableDrawHandler::typeMode));
    typeTable_.setCustomDrawHandler(typeTableDrawHandler_.get());

    categoryTable_.setItemHeight(10);
    categoryTableDrawHandler_.reset(new TableDrawHandler(prefs_, TableDrawHandler::categoryMode));
    categoryTable_.setCustomDrawHandler(categoryTableDrawHandler_.get());

    explicitnessTable_.setItemHeight(10);
    explicitnessTableDrawHandler_.reset(new TableDrawHandler(prefs_, TableDrawHandler::explicitnessMode));
    explicitnessTable_.setCustomDrawHandler(explicitnessTableDrawHandler_.get());

    //show tables    
    explicitnessTable_.show();
    categoryTable_.show();
    typeTable_.show();

    return result;
}

void JokesSearchForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(2, 2, screenBounds.width()-4, screenBounds.height()-4);
    setBounds(bounds);

    typeTable_.bounds(bounds);
    bounds.dy() = screenBounds.height()-112;
    bounds.dy() -= (bounds.dy() % 10);
    typeTable_.setBounds(bounds);
    typeTable_.adjustVisibleItems();

    categoryTable_.bounds(bounds);
    bounds.dy() = screenBounds.height()-70;
    bounds.dy() -= (bounds.dy() % 10);
    categoryTable_.setBounds(bounds);
    categoryTable_.adjustVisibleItems();

    graffitiState_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 16);
    cancelButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    update();    
}

bool JokesSearchForm::handleEvent(EventType& event)
{
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handled = handleControlSelected(event);
            break;

        case popSelectEvent:
            switch (event.data.popSelect.controlID)
            {
                case jokeRatingPopupTrigger:
                    jokeRatingPopupIndex_ = event.data.popSelect.selection;
                    jokeRatingPopupTrigger_.setLabel("");
                    jokeRatingPopupTrigger_.setLabel(ratingNames[jokeRatingPopupIndex_]);
                    break;
                case jokeSortPopupTrigger:
                    jokeSortPopupIndex_ = event.data.popSelect.selection;
                    jokeSortPopupTrigger_.setLabel("");
                    jokeSortPopupTrigger_.setLabel(sortNames[jokeSortPopupIndex_]);
                    break;
                default:
                    assert(false);
                    break;
            }
            handled=true;
            break;            
            
        case lstSelectEvent:
            handleListItemSelect(event.data.lstSelect.listID, event.data.lstSelect.selection);
            handled=true;
            break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool JokesSearchForm::handleMenuCommand(UInt16 itemId)
{
    bool handled=true;
    switch (itemId)
    {
        case categorySelectMenuItem:
            for (int i = 0; i < prefs_.categoryTableSize; i++)
                prefs_.fCategory[i] = true;
            categoryTable_.draw();
            break;
            
        case categoryClearMenuItem:
            for (int i = 0; i < prefs_.categoryTableSize; i++)
                prefs_.fCategory[i] = false;
            categoryTable_.draw();
            break;
            
        case typeSelectMenuItem:
            for (int i = 0; i < prefs_.typeTableSize; i++)
                prefs_.fType[i] = true;
            typeTable_.draw();
            break;
            
        case typeClearMenuItem:
            for (int i = 0; i < prefs_.typeTableSize; i++)
                prefs_.fType[i] = false;
            typeTable_.draw();
            break;

        case explicitnessSelectMenuItem:
            for (int i = 0; i < prefs_.explicitnessTableSize; i++)
                prefs_.fExplicitness[i] = true;
            explicitnessTable_.draw();
            break;
            
        case explicitnessClearMenuItem:
            for (int i = 0; i < prefs_.explicitnessTableSize; i++)
                prefs_.fExplicitness[i] = false;
            explicitnessTable_.draw();
            break;
            
        default:
            assert(false);
    }
    return handled;
}

bool JokesSearchForm::handleControlSelected(const EventType& event)
{
    bool handled = false;
    switch (event.data.ctlSelect.controlID)
    {
        case okButton:
            handleOkButton();
            handled = true;
            break;

        case cancelButton:
            closePopup();
            handled = true;
            break;

        case jokeRatingPopupTrigger:
        case jokeSortPopupTrigger:
            break;
            
        default:
            assert(false);
    }
    return handled;
}

void JokesSearchForm::handleListItemSelect(UInt16 listId, UInt16 itemId)
{
    if (jokeRatingPopupList == listId)
        jokeRatingPopupIndex_ = itemId;
    else if (jokeSortPopupList == listId)
        jokeSortPopupIndex_ = itemId;
    else
    {
        switch (listId)
        {
            case typesTable:
                prefs_.fType[itemId] = !prefs_.fType[itemId];
                typeTable_.setSelection(noListSelection);
                typeTable_.draw();
                break;            
            case categoryTable:
                prefs_.fCategory[itemId] = !prefs_.fCategory[itemId];
                categoryTable_.setSelection(noListSelection);
                categoryTable_.draw();
                break;            
            case explicitnessTable:   
                prefs_.fExplicitness[itemId] = !prefs_.fExplicitness[itemId];
                explicitnessTable_.setSelection(noListSelection);
                explicitnessTable_.draw();
                break;            
            default:
                assert(false);
                break;
        }
    }    
}

void JokesSearchForm::handleOkButton()
{
    Preferences::JokesPreferences& prefs = application().preferences().jokesPreferences; 

    prefs = prefs_;

    prefs.minimumRating = jokeRatingPopupIndex_;
    prefs.sortOrder = jokeSortPopupIndex_;
    
    String category;
    String type;
    String explicitness;
    makeJokeStrings(category,type,explicitness,prefs);

    // but btw www.jokes.com find all when no one is selected
    if (category.empty())
    {
        MoriartyApplication::alert(noCategorySelectedAlert);
        return;
    }
    if (explicitness.empty())
    {
        MoriartyApplication::alert(noExplicitnessSelectedAlert);
        return;
    }
    if (type.empty())
    {
        MoriartyApplication::alert(noTypeSelectedAlert);
        return;
    }        
    
    String request;
    request.assign(jokeRatingPopupTrigger_.label()).append(1,_T(';'));
    request.append(jokeSortPopupTrigger_.label()).append(1,_T(';'));
    request.append(explicitness).append(1,_T(';'));
    request.append(type).append(1,_T(';'));
    request.append(category).append(1,_T(';'));
    if (NULL != keywordField_.text())
        request.append(keywordField_.text());
    else
        request.append(_T(" "));

    closePopup();
    LookupManager* lookupManager=application().lookupManager;
    assert(NULL!=lookupManager);
    lookupManager->fetchJokesList(request);
}

