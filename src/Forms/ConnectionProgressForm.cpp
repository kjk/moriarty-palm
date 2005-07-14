#include "ConnectionProgressForm.hpp"
#include "MoriartyPreferences.hpp"
#include "LookupManager.hpp"
#include "MoriartyApplication.hpp"
#include <SysUtils.hpp>

class MoriartyLookupProgressReporter: public LookupProgressReporter {
    
    uint_t lastPercent_;

public:
        
    MoriartyLookupProgressReporter():
        lastPercent_(0) {}

    void showProgress(const LookupProgressReportingSupport& support, Graphics& graphics, const ArsRectangle& bounds, bool clearBkg);
    
    ~MoriartyLookupProgressReporter();
    
};

void MoriartyLookupProgressReporter::showProgress(const LookupProgressReportingSupport& support, Graphics& graphics, const ArsRectangle& bounds, bool clearBkg)
{
    if (clearBkg) 
        graphics.erase(bounds);
    ArsRectangle rect(bounds);
    rect.explode(2, 2, -4, -4);
    Graphics::FontSetter setFont(graphics, Font());
    const char_t* text=support.statusText;
    uint_t length=tstrlen(text);
    uint_t width=rect.width();
    graphics.charsInWidth(text, length, width);
    graphics.drawText(text, length, rect.topLeft);
    uint_t percent=support.percentProgress();
    if (support.percentProgressDisabled==percent)
        percent=0;
    lastPercent_=percent=std::max(percent, lastPercent_);
    rect.y()+=(graphics.fontHeight()+2);
    rect.height()=12;

    PatternType oldPattern=WinGetPatternType();
    WinSetPatternType(blackPattern);
    RectangleType nativeRec=toNative(rect);
    nativeRec.extent.x*=percent;
    nativeRec.extent.x/=100;
    WinPaintRectangle(&nativeRec, 0);
    nativeRec.topLeft.x+=nativeRec.extent.x;
    nativeRec.extent.x=rect.width()-nativeRec.extent.x;
    WinSetPatternType(grayPattern);
    WinPaintRectangle(&nativeRec, 0);
    WinSetPatternType(oldPattern);        
}

MoriartyLookupProgressReporter::~MoriartyLookupProgressReporter()
{}

void ConnectionProgressForm::attachControls()
{
    MoriartyForm::attachControls();
    cancelButton_.attach(cancelButton);
}

void ConnectionProgressForm::draw(UInt16 updateCode)
{
    Graphics graphics(windowHandle());
    MoriartyForm::draw(updateCode);
    ArsRectangle rect;
    bounds(rect);
    rect.explode(2, 16, -4, -34);
    if (lookupManager_->lookupInProgress())
    {
        WinDisplayToWindowPt(reinterpret_cast<Coord*>(&rect.topLeft.x), reinterpret_cast<Coord*>(&rect.topLeft.y));
        lookupManager_->showProgress(graphics, rect);       
    }
}

void ConnectionProgressForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    bounds.x()=2;
    bounds.y()=screenBounds.height()-62;
    bounds.width()=screenBounds.width()-4;
    bounds.height()=60;
    
    setBounds(bounds);
    
    cancelButton_.anchor(bounds, anchorLeftEdge, 44, anchorTopEdge, 15);
    
    update();        
}

bool ConnectionProgressForm::handleEvent(EventType& event)
{
    bool handled=false;
    switch (event.eType)
    {
        case ctlSelectEvent:
            handleControlSelected(event);
            handled=true;
            break;
            
        case LookupManager::lookupStartedEvent:
        case LookupManager::lookupProgressEvent:
            update();
            handled=true;
            break;
        
        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled=true;
            break;
        
        default: 
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

ConnectionProgressForm::ConnectionProgressForm(MoriartyApplication& app):
    MoriartyForm(app, connectionProgressForm, true),
    lookupManager_(app.lookupManager),
    cancelButton_(*this)
{
    assert(0!=lookupManager_);
    lookupManager_->setProgressReporter(new MoriartyLookupProgressReporter());
}

ConnectionProgressForm::~ConnectionProgressForm()
{
    lookupManager_->setProgressReporter(0);
}

void ConnectionProgressForm::handleControlSelected(const EventType& event)
{
    assert(cancelButton==event.data.ctlSelect.controlID);
    if (lookupManager_->lookupInProgress())
        lookupManager_->abortConnections();
    closePopup();
    sendEvent(LookupManager::lookupFinishedEvent,LookupFinishedEventData(lookupResultConnectionCancelledByUser));
}

void ConnectionProgressForm::handleLookupFinished(const EventType& event)
{   
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    closePopup();
    sendEvent(LookupManager::lookupFinishedEvent, data);
}
