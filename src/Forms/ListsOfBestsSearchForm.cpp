#include "ListsOfBestsSearchForm.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>

ListsOfBestsSearchForm::ListsOfBestsSearchForm(MoriartyApplication& app):
    MoriartyForm(app, listsOfBestsSearchForm),
    okButton_(*this),
    cancelButton_(*this),
    titlePopupTrigger_(*this),
    mediaPopupTrigger_(*this),
    keywordField_(*this),
    graffitiState_(*this)
{
    setFocusControlId(keywordField);
}

ListsOfBestsSearchForm::~ListsOfBestsSearchForm() 
{}

void ListsOfBestsSearchForm::attachControls()
{
    MoriartyForm::attachControls();
    //attach
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
    mediaPopupTrigger_.attach(mediaPopupTrigger);
    titlePopupTrigger_.attach(titlePopupTrigger);
    keywordField_.attach(keywordField);
    graffitiState_.attachByIndex(getGraffitiStateIndex());
}

bool ListsOfBestsSearchForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    Preferences::ListsOfBestsPreferences* prefs = &application().preferences().listsOfBestsPreferences;
    if (!prefs->lastSearchKeyword_.empty())
    {
        std::vector<String> vec = split(prefs->lastSearchKeyword_, _T(";"));
        assert(vec.size() == 3);
        keywordField_.setEditableText(vec[0]);
        mediaPopupTrigger_.setLabel(_T(""));
        titlePopupTrigger_.setLabel(_T(""));
        mediaPopupTriggerText_ = vec[1];
        titlePopupTriggerText_ = vec[2];
        mediaPopupTrigger_.setLabel(mediaPopupTriggerText_.c_str());
        titlePopupTrigger_.setLabel(titlePopupTriggerText_.c_str());
    }
    return result;
}

void ListsOfBestsSearchForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-90, screenBounds.width()-4, 88);
    setBounds(rect);
    update();    
}

bool ListsOfBestsSearchForm::handleEvent(EventType& event)
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

bool ListsOfBestsSearchForm::handleControlSelected(const EventType& event)
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

        case titlePopupTrigger:
        case mediaPopupTrigger:
            break;
            
        default:
            assert(false);
    }
    return handled;
}

void ListsOfBestsSearchForm::handleOkButton()
{
    Preferences::ListsOfBestsPreferences* prefs = &application().preferences().listsOfBestsPreferences;
    const char* text = keywordField_.text();
    String request;
    
    if (NULL!=text)
    {
        request = text;
        replaceCharInString((char_t*)request.data(), _T(';'), _T(' '));
        request.append(1,_T(';')).append(mediaPopupTrigger_.label());
        request.append(1,_T(';')).append(titlePopupTrigger_.label());
        prefs->lastSearchKeyword_.assign(request);
    }
    
    closePopup();

    if (!request.empty())
    {
        LookupManager* lookupManager=application().lookupManager;
        assert(NULL!=lookupManager);
        request.assign(_T("s+listsofbestssearch:")).append(prefs->lastSearchKeyword_);
        lookupManager->fetchUrl(request.c_str());
    }
}
