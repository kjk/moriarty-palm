#include "NotImplementedForm.hpp"
#include <SysUtils.hpp>
#include <Geometry.hpp>
#include <Text.hpp>

#if defined(__MWERKS__)
# pragma far_code
#endif

NotImplementedForm::~NotImplementedForm()
{
}

NotImplementedForm::NotImplementedForm(MoriartyApplication& app):
    MoriartyForm(app, notImplementedForm),
    doneButton_(*this)
{}

void NotImplementedForm::attachControls()
{
    MoriartyForm::attachControls();
    doneButton_.attach(doneButton);
}

void NotImplementedForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(screenBounds);
    bounds=screenBounds;
    bounds.explode(2, 17, -4, -37);

    doneButton_.bounds(bounds);
    bounds.y()=screenBounds.height()-14;
    doneButton_.setBounds(bounds);
   
    update();    
}

void NotImplementedForm::draw(UInt16 updateCode)
{
    MoriartyForm::draw(updateCode);
    if (redrawAll!=updateCode)
        return;

    Graphics graphics(windowHandle());
    ArsRectangle rect(bounds());

    rect.explode(0, 15, 0, -33);
    graphics.erase(rect);
    Point point(rect.x(), rect.y()+20);

    PalmFont font(largeFont);

    Graphics::FontSetter setFont(graphics, font);
    graphics.drawCenteredText("Implement me!", point, rect.width());

}

void NotImplementedForm::handleControlSelect(const EventType& event)
{
    MoriartyApplication& app=application();
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;            

        default:
            assert(false);
    }
}

bool NotImplementedForm::handleEvent(EventType& event)
{
    bool handled=false;
    switch (event.eType)
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            break;
                        
        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

