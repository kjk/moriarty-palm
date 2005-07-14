#include <SysUtils.hpp>
#include <Definition.hpp>
#include <ByteFormatParser.hpp>
#include <Text.hpp>
#include "LookupManager.hpp"
#include "Forms/AmazonEnterWishlistForm.hpp"
#include "Forms/AmazonSearchForm.hpp"

#include <HistorySupport.hpp>
#include "History.hpp"
#include "AmazonMainForm.hpp"
#include "MoriartyPreferences.hpp"

#pragma pcrelconstdata on

AmazonMainForm::AmazonMainForm(MoriartyApplication& app):
    MoriartyForm(app, amazonMainForm),
    historyButton_(*this),
    doneButton_(*this),
    searchButton_(*this),
    prevButton_(*this),
    nextButton_(*this),
    scrollBar_(*this),
    informationField_(*this),
    fThisIsTheEndOfResults_(false),
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

    prefs_ = &app.preferences().amazonPreferences;

    historySupport_.popupMenuFillHandlerData = (void*)(urlSchemaAmazonForm _T(":main"));

    historySupport_.setup(amazonHistoryCacheName, historyPopupMenu, historyButton, app.hyperlinkHandler, ReadUrlFromCache);
}

AmazonMainForm::~AmazonMainForm()
{
}

void AmazonMainForm::attachControls()
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
    informationField_.attach(informationField);
}

bool AmazonMainForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();

    MoriartyApplication& app = application();
    LookupManager*       lookupManager = app.lookupManager;
    assert(NULL != lookupManager);

    if (lookupManager->crossModuleLookup)
        levelMain();
    else
        switchToLevel(prefs_->currentLevel);
    return result;
}

void AmazonMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
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

bool AmazonMainForm::handleEvent(EventType& event)
{
    if (textRenderer_.handleEventInForm(event) || historySupport_.handleEventInForm(event))
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

bool AmazonMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled = false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            handled = true;
            break;

        case backMenuItem:
            levelUp();
            handled = true;
            break;

        case forwardMenuItem:
            switchToLevel(prefs_->currentLevel+1);
            handled = true;
            break;

        case historyMenuItem:
            historyButton_.hit();
            handled = true;
            break;

        case categoryMenuItem:
            levelMain();
            handled = true;
            break;

        case searchMenuItem:
            handleSearch();
            handled = true;
            break;

        case wishlistMenuItem:
            (new AmazonEnterWishlistForm(application()))->popup();
            handled = true;
            break;
    }
    return handled;
}

void AmazonMainForm::showStartPage()
{
    prevButton_.hide();
    nextButton_.hide();
    informationField_.hide();

    searchTextString_.assign(_T("Search entire store for:"));
    searchButtonString_.assign(_T("s+amazonsearch:Blended;;1;"));

    char_t  *data;
    UInt32  dataLen;
    if (application().preferences().amazonPreferences.smallMain)
        data = getDataResource(amazonStartPageSmallText, &dataLen);
    else
        data = getDataResource(amazonStartPageText, &dataLen);
    if (NULL == data)
        return;

    Definition::Elements_t elems;
    ByteFormatParser parser;
    parser.parseAll(data, dataLen);
    assert(NULL != data);
    free(data);

    DefinitionModel* model = parser.releaseModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    textRenderer_.setModel(model, Definition::ownModel);            
}

void AmazonMainForm::readUdf()
{
    if (-1 == prefs_->currentLevel)
    {
        showStartPage();
        return;
    }

    UniversalDataFormat* udf = &application().lookupManager->amazonData;
    if (udf->empty())
    {
        showStartPage();
        return;
    }

    prevButton_.hide();
    nextButton_.hide();
    informationField_.hide();

    for (int i=0; i < udf->getItemsCount(); i++)
    {
        switch (udf->getItemText(i,0)[0])
        {
            case _T('B'): // button
            {
                // silly...
                switch(udf->getItemText(i,1)[0])
                {
                    case _T('P'):
                        prevButtonString_.assign(udf->getItemText(i,2));
                        prevButton_.show();
                        break;
                    case _T('N'):
                        nextButtonString_.assign(udf->getItemText(i,2));
                        nextButton_.show();
                        break;
                    case _T('D'):
                        break;
                    case _T('S'):
                        if (udf->getItemElementsCount(i) == 4)
                        {
                            // on item and stuff we only show search, but with previous settings
                            searchButtonString_.assign(udf->getItemText(i,2));
                            searchTextString_.assign(udf->getItemText(i,3));
                        }
                        break;
                    case _T('I'):
                        informationString_.assign(udf->getItemText(i,2));
                        informationField_.setText(informationString_);
                        informationField_.show();
                        break;
                }
                break;
            }

            case _T('D'): // definition
            {
                Definition::Elements_t elems;
                ByteFormatParser parser;
                const char_t *data;
                ulong_t dataLen;
                data = udf->getItemTextAndLen(i, 1, &dataLen);
                parser.parseAll(data, dataLen);
                DefinitionModel* model = parser.releaseModel();
                textRenderer_.setModel(model, Definition::ownModel);
                break;
            }

            case _T('H'): // history title
            {
                prefs_->currentLevel = historySupport_.lookupFinished(true, udf->getItemText(i,1));
                break;
            }

            default:
                assert(false);
                break;
        }
    }
}

void AmazonMainForm::setDisplayMode()
{
    readUdf();
    updateNavigationButtons();
    update();
}

void AmazonMainForm::handleSearch()
{
    if (searchButtonString_.empty() || searchTextString_.empty())
    {
        searchTextString_.assign(_T("Search entire store for:"));
        searchButtonString_.assign(_T("s+amazonsearch:Blended;;1;"));
    }    

    (new AmazonSearchForm(application(),
        searchButtonString_.c_str(),
        searchTextString_.c_str()
        ))->popup();
}

void AmazonMainForm::levelUp()
{
    switchToLevel(prefs_->currentLevel-1);
}

void AmazonMainForm::levelMain()
{
    prefs_->currentLevel = -1;
    setDisplayMode();
}

void AmazonMainForm::handleControlSelect(const EventType& event)
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

void AmazonMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data = reinterpret_cast<const LookupFinishedEventData&>(event.data);
    MoriartyApplication&           app = application();
    LookupManager*                 lookupManager = app.lookupManager;
    assert(NULL != lookupManager);

    fThisIsTheEndOfResults_ = false;
    switch (data.result)
    {
        case lookupResultAmazon:
            prefs_->currentLevel = 0; // !=-1
            setDisplayMode();
            FinishCrossModuleLookup(historySupport_, amazonModuleName);
            break;

        case lookupResultNoResults:
            fThisIsTheEndOfResults_ = true; 
            updateNavigationButtons();
            update();
            break;
            
        // linked modules
        default:
            if (HandleCrossModuleLookup(event, amazonHistoryCacheName, amazonModuleName))
                return;
    }
    lookupManager->handleLookupFinishedInForm(data);
}

/**
 * level is level in history - if (level==-1) setStartPage();
 */
void AmazonMainForm::switchToLevel(int level)
{
    LookupManager* lookupManager = application().lookupManager;
    assert(NULL != lookupManager);

    if (-1 >= level)
    {
        levelMain();
    }
    else
    {
        historySupport_.fetchHistoryEntry(level);
    }
}

void AmazonMainForm::updateNavigationButtons()
{
    bool enable = !prevButtonString_.empty();
    prevButton_.setGraphics(enable?backBitmap:backDisabledBitmap);
    prevButtonEnabled_ = enable;

    enable = !fThisIsTheEndOfResults_ && !nextButtonString_.empty();
    nextButton_.setGraphics(enable?forwardBitmap:forwardDisabledBitmap);
    nextButtonEnabled_ = enable;
}
