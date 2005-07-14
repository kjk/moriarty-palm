#include "StringSelectForm.hpp"
#include <SysUtils.hpp>

StringSelectForm::StringSelectForm(uint_t notifyEvent, const char_t* title):
    MoriartyForm(MoriartyApplication::instance(), selectStringForm),
    subtitleField_(*this),
    choicesList_(*this),
    okButton_(*this),
    cancelButton_(*this),
    itemRenderer_(NULL),
    subtitle_(NULL),
    itemRendererOwner_(rendererOwnerNot),
    notifyEvent_(notifyEvent)
{
    title_ = StringCopy2(title);
    setFocusControlId(choicesList);
}    

StringSelectForm::~StringSelectForm()
{
    if (NULL != title_)
        free(title_);
    if (NULL != subtitle_)
        free(subtitle_);
    if (rendererOwner == itemRendererOwner_)
        delete itemRenderer_;
}

void StringSelectForm::attachControls()
{
    MoriartyForm::attachControls();
    subtitleField_.attach(subtitleField);
    choicesList_.attach(choicesList);
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
}

bool StringSelectForm::handleOpen()
{
    bool res = MoriartyForm::handleOpen();
    if ((NULL==subtitle_) || (0==tstrlen(subtitle_)))
        subtitleField_.hide();
    else
    {
        subtitleField_.setText(subtitle_);
        subtitleField_.show();
    }
    setTitle(title_);
    assert(NULL != itemRenderer_);
    choicesList_.setItemHeight(13);
    choicesList_.setUpBitmapId(upBitmap);
    choicesList_.setDownBitmapId(downBitmap);
    choicesList_.setItemRenderer(itemRenderer_, ExtendedList::redrawNot);
    if (0 != choicesList_.itemsCount())
        choicesList_.setSelection(0);
 
    RectangleType r;
    getScreenBounds(r);
    resize(r);
        
    return res;
}

bool StringSelectForm::handleEvent(EventType& event)
{
    int selection = noListSelection;
    switch (event.eType)
    {
        case lstSelectEvent:
            okButton_.hit();
            return true;
            
        case ctlSelectEvent: 
            if (okButton == event.data.ctlSelect.controlID)
                selection = choicesList_.selection();
            if (noListSelection != selection || cancelButton == event.data.ctlSelect.controlID)
            {
                closePopup();
                StringSelectNotifyData notifyData(selection);
                sendEvent(notifyEvent_, notifyData);
            }
            return true;
        
        case keyDownEvent:
        {
            int option = ExtendedList::optionScrollPagesWithLeftRight;
            if (application().runningOnTreo600())
                option = 0;
            if (choicesList_.handleKeyDownEvent(event, option | ExtendedList::optionFireListSelectOnCenter))
                return true;
            if (chrCarriageReturn == event.data.keyDown.chr || chrLineFeed == event.data.keyDown.chr)
            {
                okButton_.hit();
                return true;
            }
            // intentional fall-through
        }
        
        default:
            return MoriartyForm::handleEvent(event);
    }
}

void StringSelectForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(screenBounds.x() + 2, screenBounds.y() + 2, screenBounds.width() - 4, screenBounds.height() - 4);
    setBounds(bounds);
    
    bounds.x() = 0;
    bounds.width() = screenBounds.width() - 4;
    if ((NULL == subtitle_) || (0==tstrlen(subtitle_)))
    {
        bounds.y() = 16;
        bounds.height() = screenBounds.height() - 40;
    }
    else
    {
        bounds.y() = 32;
        bounds.height() = screenBounds.height() - 56;
    }
    choicesList_.setBounds(bounds);
    
    subtitleField_.anchor(screenBounds, anchorRightEdge, 6, anchorNot, 0);
    
    okButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    cancelButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    
    update();
}

int StringSelectForm::extractSelection(const EventType& event)
{
    const StringSelectNotifyData& data =reinterpret_cast<const StringSelectNotifyData&>(event.data);
    return data.selection;
}

void StringSelectForm::setItemRenderer(ExtendedList::ItemRenderer* itemRenderer, RendererOwnershipOption owner)
{
    choicesList_.setItemRenderer(itemRenderer_ = itemRenderer, ExtendedList::redrawNot);
    itemRendererOwner_ = owner;
}
