#include <Text.hpp>

#include <LineBreakElement.hpp>
#include <TextElement.hpp>

#include "FlickrAboutForm.hpp"
#include "HyperlinkHandler.hpp"
#include "MoriartyStyles.hpp"

#include <SysUtils.hpp>

FlickrAboutForm::FlickrAboutForm(MoriartyApplication& app):
    MoriartyForm(app, flickrAboutForm),
    scrollBar_(*this),
    infoRenderer_(*this, &scrollBar_),
    doneButton_(*this)
 {
    setFocusControlId(doneButton);
    infoRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    infoRenderer_.setInteractionBehavior(   
        TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavUpDownScroll
    );
    infoRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
}

FlickrAboutForm::~FlickrAboutForm() 
{
}

void FlickrAboutForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(textScrollBar);
    infoRenderer_.attach(infoRenderer);
    doneButton_.attach(doneButton);
}

bool FlickrAboutForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    prepareAbout();
    return result;
}

void FlickrAboutForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds(screenBounds);
    bounds.explode(2, 2, -4, -4);        
    setBounds(bounds);
    
    infoRenderer_.anchor(screenBounds, anchorRightEdge, 15, anchorBottomEdge, 37);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 13, anchorBottomEdge, 37);
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 18);
    update();    
}

bool FlickrAboutForm::handleEvent(EventType& event)
{
    if (infoRenderer_.handleEventInForm(event))
        return true;
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handled = handleControlSelect(event);
            break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool FlickrAboutForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            closePopup();
            return true;

        default: 
            assert(false);
    }
    return false;
}

void FlickrAboutForm::prepareAbout()
{
    infoRenderer_.clear();

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }

    DefinitionModel::Elements_t& elems = model->elements;
    
    TextElement* text = new_nt TextElement("Flickr.com is an on-line photo sharing site which allows you to upload photos and share them with other people. To learn more about Flickr, please visit ");
    elems.push_back(text);

    text = new_nt TextElement("http://flickr.com");
    elems.push_back(text);
    text->setHyperlink("http://flickr.com", hyperlinkUrl);
    
    elems.push_back(new_nt TextElement("."));
    elems.push_back(new_nt LineBreakElement());
    elems.push_back(new_nt LineBreakElement());

    text = new_nt TextElement("InfoMan's flickr module allows you to post photos directly from your device to your flickr account. You need to provide your flickr.com account e-mail address and password. To upload a picture go to Treo's camera application, select a picture to upload and use 'Send...' menu item. You'll see a list of applications to use, select \"flickr (InfoMan)\". Wait until upload is finished. Go to your flickr album - the picture will be waiting for you!");
    elems.push_back(text);
    elems.push_back(new_nt LineBreakElement());
    elems.push_back(new_nt LineBreakElement());

    text = new_nt TextElement("To learn more about InfoMan visit ");
    elems.push_back(text);
    text = new_nt TextElement("http://arslexis.com");
    elems.push_back(text);
    text->setHyperlink("http://arslexis.com", hyperlinkUrl);
    elems.push_back(new_nt TextElement("."));
    
    infoRenderer_.setModel(model, Definition::ownModel);
    return;
}
