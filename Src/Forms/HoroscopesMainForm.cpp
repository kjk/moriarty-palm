#include "HoroscopesMainForm.hpp"
#include "MoriartyPreferences.hpp"
#include "LookupManager.hpp"
#include <Definition.hpp>
#include <TextElement.hpp>
#include <LineBreakElement.hpp>
#include <Text.hpp>

#include "MoriartyStyles.hpp"

enum {
    maxNameLength=12,
    maxDateLength=12,
    signsCount=12 // this will probably remain 12:)
};

typedef const char_t NameField_t[maxNameLength];
typedef const char_t DateField_t[maxDateLength];

struct ArrayEntry {
    const NameField_t  name;
    const DateField_t  date; 
};

static const ArrayEntry signNames[] = {
    {_T("Aries"), _T("03/21-04/19")},
    {_T("Taurus"), _T("04/20-05/20")},
    {_T("Gemini"), _T("05/21-06/21")},
    {_T("Cancer"), _T("06/22-07/22")},
    {_T("Leo"), _T("07/23-08/22")},
    {_T("Virgo"), _T("08/23-09/22")},
    {_T("Libra"), _T("09/23-10/22")},
    {_T("Scorpio"), _T("10/23-11/21")},
    {_T("Sagittarius"), _T("11/22-12/21")},
    {_T("Capricorn"), _T("12/22-01/19")},
    {_T("Aquarius"), _T("01/20-02/18")},
    {_T("Pisces"), _T("02/19-03/20")}
};    

class HoroscopesListDrawHandler: public ExtendedList::ItemRenderer {

public:
    
    explicit HoroscopesListDrawHandler() {}
    
    uint_t itemsCount() const
    {
        return signsCount;
    }

    ~HoroscopesListDrawHandler();

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);
    
};

HoroscopesListDrawHandler::~HoroscopesListDrawHandler() {}

#define LEFT_MARGIN 2
#define RIGHT_MARGIN 2

void HoroscopesListDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    assert(item < signsCount);
    
    uint_t width = itemBounds.width();
    const char_t *text = signNames[item].name;
    uint_t length = tstrlen(text);
    graphics.charsInWidth(text, length, width);

    Point p = itemBounds.topLeft;
    p.x += LEFT_MARGIN;

    graphics.drawText(text, length, p);

    text = signNames[item].date;
    length = tstrlen(text);
    width = itemBounds.width() - width;
    Point newLeft = itemBounds.topLeft;
    graphics.charsInWidth(text, length, width);
    newLeft.x += (itemBounds.width() - (width+RIGHT_MARGIN) );
    graphics.drawText(text, length, newLeft);
}

HoroscopesMainForm::HoroscopesMainForm(MoriartyApplication& app):
    MoriartyForm(app, horoscopesMainForm),
    horoscopesList_(*this),
    scrollBar_(*this),
    doneBackButton_(*this),
    updateButton_(*this),
    displayMode_(showHoroscopesList),
    currentHoroscopeIndex_(horoscopeIndexNone),
    downloadingHoroscopeIndex_(horoscopeIndexNone),
    horoscopeRenderer_(*this, &scrollBar_)
{
    horoscopeRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  

}

HoroscopesMainForm::~HoroscopesMainForm() {}

void HoroscopesMainForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    doneBackButton_.attach(doneBackButton);
    updateButton_.attach(updateButton);
    horoscopeRenderer_.attach(horoscopesRenderer);
    horoscopeRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);

    horoscopesList_.attach(horoscopesList);
    horoscopesList_.setUpBitmapId(upBitmap);
    horoscopesList_.setDownBitmapId(downBitmap);    
}

bool HoroscopesMainForm::handleOpen()
{
    bool handled = MoriartyForm::handleOpen();
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL != lookupManager);
    
    horoscopesList_.setItemHeight(12);
    horoscopesListDrawHandler_.reset(new HoroscopesListDrawHandler());
    horoscopesList_.setCustomDrawHandler(horoscopesListDrawHandler_.get());

    // on startup, always show the list (since that's almost always where user
    // left. But select the item on the list that was viewed the last time
    if (!lookupManager->horoscope.empty())
    {
        Preferences::HoroscopesPreferences* prefs = &app.preferences().horoscopesPreferences;
        assert(-1 != prefs->downloadedSign);
        horoscopesList_.setSelection(prefs->downloadedSign);
    }
    else
        horoscopesList_.setSelection(0);

    setDisplayMode(showHoroscopesList);

    return handled;
}

void HoroscopesMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(bounds = screenBounds);

    bounds.explode(0, 17, 0, -37);
    horoscopesList_.setBounds(bounds);
    horoscopesList_.adjustVisibleItems();

    horoscopeRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);
    
    doneBackButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    updateButton_.anchor(screenBounds, anchorLeftEdge, 44, anchorTopEdge, 14);
    
    update();    
}

bool HoroscopesMainForm::handleEvent(EventType& event)
{
    if (showHoroscope == displayMode_ && horoscopeRenderer_.handleEventInForm(event))
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

bool HoroscopesMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled = false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneBackButton_.hit();
            handled = true;
            break;
        case horoscopeMenuItem:
            setDisplayMode(showHoroscope);
            update();
            handled = true;
            break;

        default:
            assert(false);
    }
    return handled;
}

void HoroscopesMainForm::setDisplayMode(HoroscopesMainForm::DisplayMode dm)
{
    displayMode_ = dm;
    switch (dm)
    {
        case showHoroscopesList:
            horoscopeRenderer_.hide();
            doneBackButton_.setLabel("Done");
            scrollBar_.hide();
            updateButton_.hide();
            horoscopesList_.notifyItemsChanged();
            if (horoscopeIndexNone != currentHoroscopeIndex_)
                horoscopesList_.setSelection(currentHoroscopeIndex_);
            horoscopesList_.show();
            horoscopesList_.focus();
            setTitle(_T("Horoscopes"));
            break;

        case showHoroscope:
            doneBackButton_.setLabel("Back");
            if (horoscopeRenderer_.empty())
                prepareHoroscope();
            horoscopesList_.hide();
            horoscopeRenderer_.show();
            scrollBar_.show();
            updateButton_.show();
            doneBackButton_.focus();
            setTitle(dateString_.c_str());
            break;

        default:
            assert(false);
    }
}

void HoroscopesMainForm::handleUpdateButton()
{
    LookupManager* lookupManager=application().lookupManager;
    Preferences::HoroscopesPreferences* prefs = &application().preferences().horoscopesPreferences;
    assert(0!=lookupManager);
    //TODO? (popup)
    if (!prefs->downloadedQuery.empty())
        lookupManager->fetchHoroscope(prefs->downloadedQuery);
    else
        setDisplayMode(showHoroscopesList);
}

void HoroscopesMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneBackButton:
            if (showHoroscopesList == displayMode_)
            {
                application().runMainForm();
            }
            else
            {
                setDisplayMode(showHoroscopesList);
                update();
            }                
            break;
            
        case updateButton:
            handleUpdateButton();
            break;

        default:
            assert(false);
    }
}

#define horoscopeTitle         _T("T")
#define horoscopeSection       _T("S")
#define horoscopeSmallSection  _T("s")
#define horoscopeText          _T("t")
#define horoscopeDate          _T("D")
#define horoscopeUrlLink       _T("L")

static void horoscopeLinkCallback(void* data)
{
    LookupManager* lm = MoriartyApplication::instance().lookupManager;
    assert(NULL!=lm);
    String text = (char_t*) data;
    lm->fetchHoroscope(text);
}


void HoroscopesMainForm::prepareHoroscope()
{
    
    horoscopeRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    horoscopeRenderer_.setHyperlinkHandler(NULL);
    
    dateString_.clear();

    const LookupManager* lookupManager=application().lookupManager;
    assert(NULL!=lookupManager);

    const UniversalDataFormat& item=lookupManager->horoscope;
    assert(!item.empty());

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    Definition::Elements_t& elems = model->elements;
    TextElement* text;

    for (int i=0; i < item.getItemsCount(); i++)
    {
        String compare = item.getItemText(i,0);
        if (horoscopeTitle == compare)
        {
            elems.push_back(text=new TextElement(item.getItemText(i,1)));
            text->setStyle(StyleGetStaticStyle(styleNameBold));
            text->setJustification(DefinitionElement::justifyCenter);
        }
        else if (horoscopeText == compare)
        {
            elems.push_back(new LineBreakElement());
            elems.push_back(text=new TextElement(item.getItemText(i,1)));
        }
        else if (horoscopeSection == compare)
        {
            elems.push_back(new LineBreakElement());
            elems.push_back(new LineBreakElement());
            elems.push_back(text=new TextElement(item.getItemText(i,1)));
            text->setStyle(StyleGetStaticStyle(styleNameBold));
        }
        else if (horoscopeSmallSection == compare)
        {
            elems.push_back(new LineBreakElement());
            elems.push_back(text=new TextElement(item.getItemText(i,1)));
            text->setStyle(StyleGetStaticStyle(styleNameBold));
        }
        else if (horoscopeDate == compare)
        {
            dateString_ = item.getItemText(i,1);
        }
        else if (horoscopeUrlLink == compare)
        {
            elems.push_back(new LineBreakElement());
            elems.push_back(text=new TextElement(item.getItemText(i,1)));
            String empty;
            text->setHyperlink(empty, hyperlinkCallback);
            text->setActionCallback(horoscopeLinkCallback, (void*) ((char_t*)item.getItemText(i,2)));
        }            
        else
        {
            assert(false);        
        }
    }   
    horoscopeRenderer_.setModel(model, Definition::ownModel);
}

void HoroscopesMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    switch (data.result)
    {
        case lookupResultHoroscope:
            if (horoscopeIndexNone != downloadingHoroscopeIndex_)
                currentHoroscopeIndex_ = downloadingHoroscopeIndex_;
            prepareHoroscope();
            if (showHoroscope!=displayMode_)
                setDisplayMode(showHoroscope);
            downloadingHoroscopeIndex_ = horoscopeIndexNone;
            Preferences::HoroscopesPreferences* prefs = &application().preferences().horoscopesPreferences;
            prefs->downloadedSign = currentHoroscopeIndex_;
            assert( -1 != prefs->downloadedSign );
            update();
            MoriartyApplication::touchModule(moduleIdHoroscopes);
            break;
    }
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(0!=lookupManager);
    lookupManager->handleLookupFinishedInForm(data);
}

void HoroscopesMainForm::handleListItemSelect(uint_t listId, uint_t itemId)
{
    assert(horoscopesList==listId);
    LookupManager* lookupManager=application().lookupManager;
    assert(0!=lookupManager);

    if (currentHoroscopeIndex_ == itemId)
    {
        setDisplayMode(showHoroscope);
        update();
    }
    else
    {   
        //TODO: ? (add popup style)
        downloadingHoroscopeIndex_ = itemId;
        lookupManager->fetchHoroscope(signNames[itemId].name);
    }
}

bool HoroscopesMainForm::handleKeyPress(const EventType& event)
{
    int option = List::optionScrollPagesWithLeftRight;
    if (application().runningOnTreo600())
        option = 0;
    if (showHoroscopesList == displayMode_ && horoscopesList_.handleKeyDownEvent(event, option | List::optionFireListSelectOnCenter))
        return true;
    return false;
}

