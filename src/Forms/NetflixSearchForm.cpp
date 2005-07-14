#include "NetflixSearchForm.hpp"
#include "LookupManager.hpp"
#include <Text.hpp>
#include <SysUtils.hpp>

enum {
    maxMatchesLength = 8
};

typedef const char_t MatchesField_t[maxMatchesLength];

static const MatchesField_t matchesNames[]={
    "Popular",
    "Movie",
    "People",
    "Genre"
};

NetflixSearchForm::NetflixSearchForm(MoriartyApplication& app):
    MoriartyForm(app, netflixSearchForm),
    okButton_(*this),
    cancelButton_(*this),
    matchesPopupTrigger_(*this),
    keywordField_(*this),
    graffitiState_(*this),
    matchesPopupIndex_(0)
{
    setFocusControlId(keywordField);
}

NetflixSearchForm::~NetflixSearchForm() 
{
}


void NetflixSearchForm::attachControls()
{
    MoriartyForm::attachControls();
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
    matchesPopupTrigger_.attach(matchesPopupTrigger);
    keywordField_.attach(keywordField);
    graffitiState_.attachByIndex(getGraffitiStateIndex());
}

bool NetflixSearchForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();

    //get preferences
    prefs_ = &application().preferences().netflixPreferences; 
    
    //disable matches if not logged
    if (!prefs_->fLogged)
        matchesPopupTrigger_.hide();

    //popup trigger
    matchesPopupIndex_ = 0;

    return result;
}

void NetflixSearchForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-78, screenBounds.width()-4, 76);
    setBounds(rect);
    update();    
}

bool NetflixSearchForm::handleEvent(EventType& event)
{
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handled = handleControlSelected(event);
            break;

        case popSelectEvent:
            if (matchesPopupTrigger == event.data.popSelect.controlID)
                matchesPopupIndex_ = event.data.popSelect.selection;
            handled=false;
            break;            

        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool NetflixSearchForm::handleControlSelected(const EventType& event)
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

        case matchesPopupTrigger:
            break;
            
        default:
            assert(false);
    }
    return handled;
}

void NetflixSearchForm::handleOkButton()
{
    const char* text = keywordField_.text();
    String request;
    
    if (NULL!=text)
    {
        String sKeyword=text;
        replaceCharInString((char_t*)sKeyword.data(), _T(';'), _T(' '));
        
        Preferences::NetflixPreferences& prefs = application().preferences().netflixPreferences; 
        request = _T("s+netflixsearch:");
        request.append(sKeyword);
        request.append(1,_T(';')).append(matchesNames[matchesPopupIndex_]);
        if (prefs.fLogged)
        {
            request.append(_T(";T"));
        }
        else
        {
            request.append(_T(";F"));
        }
    }
    
    closePopup();

    if (!request.empty())
    {
        LookupManager* lookupManager=application().lookupManager;
        assert(NULL!=lookupManager);
        lookupManager->fetchUrl(request.c_str());
    }
}
