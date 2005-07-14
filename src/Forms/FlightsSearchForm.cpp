#include "FlightsSearchForm.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>

FlightsSearchForm::FlightsSearchForm(MoriartyApplication& app):
    MoriartyForm(app, flightsSearchForm),
    okButton_(*this),
    cancelButton_(*this),
    airlinesPopupTrigger_(*this),
    dateTrigger_(*this),
    timeTrigger_(*this),
    flightNoField_(*this),
    fromField_(*this),
    toField_(*this),
    graffitiState_(*this)
{
    setFocusControlId(flightNoField);
}

FlightsSearchForm::~FlightsSearchForm() 
{}

void FlightsSearchForm::attachControls()
{
    MoriartyForm::attachControls();
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
    airlinesPopupTrigger_.attach(airlinesPopupTrigger);
    dateTrigger_.attach(dateTrigger);
    timeTrigger_.attach(timeTrigger);

    flightNoField_.attach(flightNoField);
    fromField_.attach(fromField);
    toField_.attach(toField);
    graffitiState_.attachByIndex(getGraffitiStateIndex());
}

bool FlightsSearchForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();

    getDate(&month_, &day_, &year_);
    getTime(&hour_, &minutes_);
    
    Preferences::FlightsPreferences* prefs = &application().preferences().flightsPreferences;
    if (prefs->valid)
    {
        month_   = prefs->month;
        day_     = prefs->day;
        year_    = prefs->year;
        hour_    = prefs->hour;
        minutes_ = prefs->minutes;
        flightNoField_.setEditableText(prefs->flightNo);
        fromField_.setEditableText(prefs->from);
        toField_.setEditableText(prefs->to);
        airlinesPopupTrigger_.setLabel(prefs->airlines.c_str());
    }
    updateDateTrigger();
    updateTimeTrigger();
    return result;
}

void FlightsSearchForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-158, screenBounds.width()-4, 156);
    setBounds(rect);
    update();    
}

void FlightsSearchForm::updateDateTrigger()
{
    char buffer[32];
    localizeDate(buffer, month_, day_, year_);
    dateTriggerString_.assign(buffer);
    dateTrigger_.setLabel(dateTriggerString_.c_str());
}

void FlightsSearchForm::updateTimeTrigger()
{
    char buffer[32];
    localizeTime(buffer, hour_, minutes_);
    timeTriggerString_.assign(buffer);
    timeTrigger_.setLabel(timeTriggerString_.c_str());
}

bool FlightsSearchForm::handleEvent(EventType& event)
{
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handled = handleControlSelected(event);
            break;

        case popSelectEvent:
            handled=false;
            break;            
            
        case lstSelectEvent:
            handled=false;
            break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool FlightsSearchForm::handleControlSelected(const EventType& event)
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

        case airlinesPopupTrigger:
            break;

        case dateTrigger:
            if (selectDate(_T("Select date"), &month_, &day_, &year_))
                updateDateTrigger();
            handled = true;
            break;

        case timeTrigger:
            if (selectTime(_T("Select time"), &hour_, &minutes_))
                updateTimeTrigger();
            handled = true;
            break;
            
        default:
            assert(false);
    }
    return handled;
}

void FlightsSearchForm::handleOkButton()
{
    const char* flightNo = flightNoField_.text();
    const char* from     = fromField_.text();
    const char* to       = toField_.text();
    char buffer[32];
    // test input
    if ((NULL == flightNo || 0==tstrcmp(airlinesPopupTrigger_.label(), _T("select airlines"))) && (NULL == from || NULL == to))
    {
        MoriartyApplication::alert(alertFlightInputMissing);
        return;
    }
    
    String request = _T("s+flights:");
    if (NULL != flightNo)
        request.append(flightNo);
    request.append(1, _T(';'));
    request.append(airlinesPopupTrigger_.label());
    request.append(1, _T(';'));
    if (NULL != from)
        request.append(from);
    request.append(1, _T(';'));
    if (NULL != to)
        request.append(to);
    request.append(1, _T(';'));
    // add month/day/year
    StrPrintF(buffer,"%d/%d/%d", month_, day_, year_);
    request.append(buffer);
    request.append(1, _T(';'));
    // add hh:mm
    StrPrintF(buffer,"%d:%d", hour_,minutes_);
    request.append(buffer);

    // store preferences
    Preferences::FlightsPreferences* prefs = &application().preferences().flightsPreferences;
    prefs->valid   = true;
    prefs->month   = month_;
    prefs->day     = day_;
    prefs->year    = year_;
    prefs->hour    = hour_;
    prefs->minutes = minutes_;
    if (NULL != flightNo)
        prefs->flightNo.assign(flightNo);
    if (NULL != from)
        prefs->from.assign(from);
    if (NULL != to)
        prefs->to.assign(to);
    prefs->airlines.assign(airlinesPopupTrigger_.label());
    
    // exit and send
    closePopup();

    LookupManager* lookupManager=application().lookupManager;
    assert(NULL!=lookupManager);
    lookupManager->fetchUrl(request.c_str());
}
