#include <SysUtils.hpp>
#include <Text.hpp>
#include <DynStr.hpp>
#include <USStates.hpp>
#include <FormObject.hpp>

#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"
#include "LyricsSearchForm.hpp"

void LyricsSearchForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle rect(2, screenBounds.height()-124, screenBounds.width()-4, 122);
    setBounds(rect);
    update();
}

void LyricsSearchForm::attachControls()
{
    MoriartyForm::attachControls();
    artistField_.attach(artistField);
    titleField_.attach(titleField);
    albumField_.attach(albumField);
    composerField_.attach(composerField);
    fullTextField_.attach(fullTextField);
}

void LyricsSearchForm::handleControlSelect(const EventType& event)
{
    DynStr *        req = NULL;
    DynStr *        tmpStr = NULL;
    const char_t *  fieldTxt = NULL;
    Boolean         fDoSearch = false;

    req = DynStrFromCharP(_T("s+lyricssearch:"), 128);
    if (NULL == req)
        goto Exit;

    tmpStr = DynStrNew(24);
    if (NULL == tmpStr)
        goto Exit;

    if (okButton != event.data.ctlSelect.controlID)
        goto Next;

    for (int i=0; i<=4; i++)
    {
        if (0 == i)
            fieldTxt = artistField_.text();
        else if (1 == i)
            fieldTxt = titleField_.text();
        else if (2 == i)
            fieldTxt = albumField_.text();
        else if (3 == i)
            fieldTxt = composerField_.text();
        else if (4 == i)
            fieldTxt = fullTextField_.text();

        if (NULL != fieldTxt)
        {
            // only do search if there's at least one non-empty field
            fDoSearch = true;
            if (NULL == DynStrAssignCharP(tmpStr, fieldTxt))
                goto Exit;

            DynStrReplace(tmpStr, _T(';'), _T(' '));

            if (NULL == DynStrAppendDynStr(req, tmpStr))
                goto Exit;
        }

        if (4 != i)
        {
            // append ';' but not after the last one
            if (NULL == DynStrAppendChar(req, _T(';')))
                goto Exit;
        }
    }

    if (fDoSearch)
    {
        LookupManager* lookupManager = application().lookupManager;
        assert(NULL != lookupManager);
        lookupManager->fetchUrl(DynStrGetCStr(req));
    }
    goto Exit;
Next:
    // handle next control
Exit:
    if (NULL != tmpStr)
        DynStrDelete(tmpStr);
    if (NULL != req)
        DynStrDelete(req);
    closePopup();
}

bool LyricsSearchForm::handleEvent(EventType& event)
{
    bool handled = false;
    switch (event.eType)
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled = true;
            break;

        case keyDownEvent:
            if (chrCarriageReturn==event.data.keyDown.chr || chrLineFeed==event.data.keyDown.chr)
            {
                Control control(*this, okButton);
                control.hit();
            }
            break;

        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

LyricsSearchForm::~LyricsSearchForm()
{}
