#ifndef MORIARTY_STRING_SELECT_FORM_HPP__
#define MORIARTY_STRING_SELECT_FORM_HPP__

#include <FormObject.hpp>
#include <HmStyleList.hpp>
#include <Text.hpp>

#include "MoriartyForm.hpp"

class StringSelectForm: public MoriartyForm
{
protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleOpen();
    
public:

    void setSubtitle(const ArsLexis::char_t* subtitle) {subtitle_ = StringCopy2(subtitle);}
    
    struct StringSelectNotifyData 
    {
        int selection;
        
        StringSelectNotifyData(int aSelection): selection(aSelection) {}
    };
    
    StringSelectForm(uint_t notifyEvent, const ArsLexis::char_t* title);
    
    ~StringSelectForm();
    
    enum RendererOwnershipOption {
        rendererOwnerNot,
        rendererOwner
    };
    
    static int extractSelection(const EventType& event);
    
    void setItemRenderer(ExtendedList::ItemRenderer* itemRenderer, RendererOwnershipOption owner = rendererOwnerNot);

private:

    Field subtitleField_;
    HmStyleList choicesList_;
    Control okButton_;
    Control cancelButton_;
    ExtendedList::ItemRenderer* itemRenderer_;
    RendererOwnershipOption itemRendererOwner_;
    
    ArsLexis::char_t* subtitle_;
    ArsLexis::char_t* title_;
    uint_t notifyEvent_;
    

};

#endif