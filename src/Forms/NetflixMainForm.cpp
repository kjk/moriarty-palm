#include "NetflixMainForm.hpp"
#include "MoriartyPreferences.hpp"
#include <SysUtils.hpp>
#include "LookupManager.hpp"
#include <Definition.hpp>
#include <ByteFormatParser.hpp>
#include <Text.hpp>
#include "Forms/NetflixEnterLoginForm.hpp"
#include "Forms/NetflixSearchForm.hpp"
#include "Forms/StocksEnterStockForm.hpp"
#include <HistorySupport.hpp>
#include "History.hpp"

#pragma pcrelconstdata on

NetflixMainForm::NetflixMainForm(MoriartyApplication& app):
    MoriartyForm(app, netflixMainForm),
    historyButton_(*this),
    doneButton_(*this),
    searchButton_(*this),
    prevButton_(*this),
    nextButton_(*this),
    scrollBar_(*this),
    historySupport_(*this),
    textRenderer_(*this, &scrollBar_)
{
    textRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    textRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    
    setupPopupMenu(linkPopupMenu, MoriartyApplication::extEventShowMenu, app.hyperlinkHandler);
    
    prefs_ = &app.preferences().netflixPreferences;

    historySupport_.popupMenuFillHandlerData = (void*)(urlSchemaNetflixForm _T(":main"));
    
    historySupport_.setup(netflixHistoryCacheName, historyPopupMenu, historyButton, app.hyperlinkHandler, ReadUrlFromCache);
}

NetflixMainForm::~NetflixMainForm()
{
}

void NetflixMainForm::attachControls()
{
    MoriartyForm::attachControls();
    historyButton_.attach(historyButton);
    doneButton_.attach(doneButton);
    searchButton_.attach(searchButton);
    prevButton_.attach(prevButton);
    nextButton_.attach(nextButton);
    scrollBar_.attach(definitionScrollBar);
    textRenderer_.attach(textRenderer);
    textRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
}

bool NetflixMainForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    showStartPage();
    return result;
}

void NetflixMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(bounds=screenBounds);

    textRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    searchButton_.anchor(screenBounds, anchorLeftEdge, 59, anchorTopEdge, 14);
    historyButton_.anchor(screenBounds, anchorLeftEdge, 13, anchorTopEdge, 14);

    prevButton_.anchor(screenBounds, anchorLeftEdge, 26, anchorNot, 0);
    nextButton_.anchor(screenBounds, anchorLeftEdge, 14, anchorNot, 0);
    update();    
}

bool NetflixMainForm::handleEvent(EventType& event)
{
    if (textRenderer_.handleEventInForm(event))
        return true;
        
    if (historySupport_.handleEventInForm(event))
        return true;
        
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled = true;
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

bool NetflixMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled=false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            handled=true;
            break;
            
        case backMenuItem:
            historySupport_.movePrevious();
            handled=true;
            break;

        case forwardMenuItem:
            historySupport_.moveNext();
            handled=true;
            break;

        case historyMenuItem:
            historyButton_.hit();
            handled=true;
            break;

        case categoryMenuItem:
            showStartPage();
            handled=true;
            break;

        case changeNameMenuItem:
            handleLogin();
            handled=true;
            break;
            
        case queueMenuItem:
            handleQueue();
            handled=true;
            break;
    }
    return handled;
}

void NetflixMainForm::showStartPage()
{
    prevButton_.hide();
    nextButton_.hide();

    ByteFormatParser* parser = NULL;
    char_t  *data;
    UInt32  dataLen;
    if (application().preferences().netflixPreferences.fLogged)
        data = getDataResource(netflixStartPageTextLogged, &dataLen);
    else
        data = getDataResource(netflixStartPageText, &dataLen);
    
    if (NULL == data)
    {
        application().alert(notEnoughMemoryAlert);
        goto Cleanup;
    }

    parser = new_nt ByteFormatParser();
    if (NULL == parser)
    {
        application().alert(notEnoughMemoryAlert);
        goto Cleanup;
    }

    parser->parseAll(data, dataLen);

    DefinitionModel* model = parser->releaseModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        goto Cleanup;
    }
    textRenderer_.setModel(model, Definition::ownModel);            

    update();
Cleanup:
    if (NULL != data)
        free(data);
    delete parser;
}

void NetflixMainForm::readUdf(bool queue)
{
    UniversalDataFormat* udf;
    if (queue)
        udf = &application().lookupManager->netflixQueue;
    else
        udf = &application().lookupManager->netflixData;
    if (udf->empty())
    {
        showStartPage();
        return;
    }
    
    prevButton_.hide();
    nextButton_.hide();

    for (int i=0; i < udf->getItemsCount(); i++)
    {
        switch (udf->getItemText(i, 0)[0])
        {
            case _T('B'): //button
                {
                    // silly...
                    switch(udf->getItemText(i, 1)[0])
                    {
                        case _T('P'):
                            prevButtonString_.assign(udf->getItemText(i, 2));
                            prevButton_.show();
                            break;
                        case _T('N'):
                            nextButtonString_.assign(udf->getItemText(i, 2));
                            nextButton_.show();
                            break;
                    }
                }
                break;
            
            case _T('D'): //definition
                {
                    ByteFormatParser parser;
                    ulong_t dataLen;
                    const char_t *data = udf->getItemTextAndLen(i, 1, &dataLen);
                    parser.parseAll(data, dataLen);
                    DefinitionModel* model = parser.releaseModel();
                    if (NULL == model)
                    {
                        application().alert(notEnoughMemoryAlert);
                        return;
                    }
                    textRenderer_.setModel(model, Definition::ownModel);            
                }
                break;

            case _T('H'): //history title
                {
                    historySupport_.lookupFinished(true, udf->getItemText(i, 1));
                }
                break;
                
            default:
                assert(false);
                break;
        }
    }
    updateNavigationButtons();
    update();
}

void NetflixMainForm::handleLogin()
{
    (new NetflixEnterLoginForm(application()))->popup();
}
    
void NetflixMainForm::handleLogout()
{
    prefs_->fLogged = false;
    prefs_->fCookieIsOnServer = false;
    showStartPage();
}
    
void NetflixMainForm::handleSearch()
{
    (new NetflixSearchForm(application()))->popup();
}

void NetflixMainForm::handleQueue()
{
    if (!prefs_->fLogged)
    {
        handleLogin();
        return;    
    }
    else
    {
        LookupManager* lookupManager=application().lookupManager;
        assert(NULL!=lookupManager);
        if (!prefs_->fNeedToUpdateQueue && !lookupManager->netflixQueue.empty())
        {
            readUdf(true);
        }
        else
        {
            lookupManager->fetchUrl(_T("s+netflixqueue:"));
        }
    }
}

void NetflixMainForm::handleMoveOnPosition(const char_t* queueId)
{
    (new StocksEnterStockForm(application(), StocksEnterStockForm::modeNetflixPosition, queueId))->popup();
}

void NetflixMainForm::handleControlSelect(const EventType& event)
{
    MoriartyApplication& app = application();
    Point center;
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;

        case searchButton:
            handleSearch();
            break;

        case prevButton:
            if (prevButtonEnabled_)
            {
                prevButton_.bounds().center(center);
                if (NULL != app.hyperlinkHandler)
                    app.hyperlinkHandler->handleHyperlink(prevButtonString_.c_str(), prevButtonString_.length(), &center);
            }
            break;
        
        case nextButton:
            if (nextButtonEnabled_)
            {
                nextButton_.bounds().center(center);
                if (NULL != app.hyperlinkHandler)
                    app.hyperlinkHandler->handleHyperlink(nextButtonString_.c_str(), nextButtonString_.length(), &center);
            }
            break;

        default:
            assert(false);
    }
}

void NetflixMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data = reinterpret_cast<const LookupFinishedEventData&>(event.data);
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL != lookupManager);
    
    // lookupManager->lookupPending = false;
    
    switch (data.result)
    {
        case lookupResultNetflix:
            readUdf();
            break;
            
        case lookupResultNetflixLoginUnknown:
            prefs_->fLogged = false;
            prefs_->fCookieIsOnServer = false;
            MoriartyApplication::alert(loginUnknownAlert);
            handleLogin();
            break;

        case lookupResultNetflixRequestPassword:
            {
                prefs_->fCookieIsOnServer = false;
                status_t err = prefs_->sendLoginAndPasswordToServer();
                if (err != errNone)
                    MoriartyApplication::alert(notEnoughMemoryAlert);
            }
            break;

        case lookupResultNetflixLoginOk:
            if (!prefs_->fLogged)
            {
                prefs_->fLogged = true;
                showStartPage();
            }
            else
                prefs_->fLogged = true;
            prefs_->fCookieIsOnServer = true;
            break;

        case lookupResultNetflixAddOk:
            MoriartyApplication::alert(netflixAddOkAlert);
            prefs_->fNeedToUpdateQueue = true;
            break;

        case lookupResultNetflixAddFailed:
            MoriartyApplication::alert(failedAlert);
            break;

        case lookupResultNetflixAddAlreadyInQueue:
            MoriartyApplication::alert(netflixAddAlreadyInQueueAlert);
            break;

        case lookupResultNetflixQueue:
            prefs_->fNeedToUpdateQueue = false;
            readUdf(true);
            break;


        // linked modules
        default:
            if (HandleCrossModuleLookup(event, netflixHistoryCacheName, netflixModuleName))
                return;
    }
    lookupManager->handleLookupFinishedInForm(data);
}

void NetflixMainForm::updateNavigationButtons()
{
    bool enable = !prevButtonString_.empty();
    prevButton_.setGraphics(enable?backBitmap:backDisabledBitmap);
    prevButtonEnabled_ = enable;
        
    enable = !nextButtonString_.empty();
    nextButton_.setGraphics(enable?forwardBitmap:forwardDisabledBitmap);
    nextButtonEnabled_ = enable;
}
