#include <Text.hpp>
#include <LangNames.hpp>
#include <LineBreakElement.hpp>
#include <BulletElement.hpp>
#include <DefinitionElement.hpp>

#include "LookupManager.hpp"
#include "HyperlinkHandler.hpp"
#include "iPediaRenderingProgressReporter.hpp"
#include "History.hpp"
#include "MoriartyPreferences.hpp"

#include "PediaSearchForm.hpp"
#include "PediaMainForm.hpp"

/*
class CStrPListModel: public ExtendedList::ItemRenderer
{
public:

    ulong_t count;
    char_t** list;

    CStrPListModel();
    
    ~CStrPListModel();
    
    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);
    
    uint_t itemsCount() const;
    
    void setList(char_t** list, ulong_t count)
    {   
        this->list = list;
        this->count = count;
    }
    
};

CStrPListModel::CStrPListModel():
    count(0),
    list(NULL)
{
}

CStrPListModel::~CStrPListModel()
{
}

void CStrPListModel::drawItem(Graphics& graphics, ExtendedList&, uint_t item, const ArsRectangle& itemBounds)
{
    assert(item < count);
    const char_t* text = list[item];
    uint_t length = tstrlen(text);
    uint_t boundsDx = itemBounds.dx()-2;
    graphics.charsInWidth(text, length, boundsDx);
    Point p = itemBounds.topLeft;
    p.x += 2;

    uint_t height = itemBounds.height();
    uint_t fontHeight = graphics.fontHeight();

    p.y = itemBounds.y();

    if (height > fontHeight)
        p.y += (height - fontHeight) / 2;
    else
        p.y -= (height - fontHeight) / 2;

    graphics.drawText(text, length, p);
}

uint_t CStrPListModel::itemsCount() const 
{
    return count;
}
 */
 
/*
static bool ExtractLinksFromDefinition(const Definition& def, char_t**& dispNames, char_t**& urls, ulong_t& count)
{
    PediaPreferences& prefs = MoriartyApplication::instance().preferences().pediaPrefs;
    
    typedef char_t* cstr;
    ulong_t strCount;
    CDynStr str;
    for (int phase = 0; phase <= 1; phase++)
    {
        if (1 == phase)
        {
            count = strCount;
            urls = NULL;
            dispNames = new_nt cstr[strCount];
            if (NULL == dispNames)
                goto NoMemory;
            memzero(dispNames, sizeof(cstr) * count);
            urls = new_nt cstr[count];
            if (NULL == urls)
                goto NoMemory;
            memzero(urls, sizeof(cstr) * count);
        }
        strCount = 0;

        ulong_t termSchemaLen = tstrlen(urlSchemaEncyclopediaTerm urlSeparatorSchemaStr);

        Definition::const_iterator end = def.end();
        for (Definition::const_iterator it = def.begin(); it != end; ++it)
        {
            DefinitionElement* elem = *it;
            if (elem->isHyperlink())
            {
                const DefinitionElement::HyperlinkProperties* props = elem->hyperlinkProperties();
                bool term = false;
                if ((term = (0 == props->resource.find(urlSchemaEncyclopediaTerm urlSeparatorSchemaStr))) 
                  || 0 == props->resource.find(urlSchemaHttp urlSeparatorSchemaStr))
                {
                    if (1 == phase)
                    {
                        ulong_t pos = termSchemaLen;
                        const char_t* name = props->resource.c_str();
                        if (term)
                        {
                            name += termSchemaLen;
                            pos = props->resource.find(":", termSchemaLen);
                            if (String::npos != pos)
                            {
                                const char_t* langName = GetLangNameByLangCode(name, pos - termSchemaLen);
                                if (NULL != langName)
                                {
                                    const char_t* code = name;
                                    ulong_t codeLen = pos - termSchemaLen;
                                    name += (codeLen + 1);
                                    if (0 != tstrncmp(code, prefs.languageCode, codeLen))
                                    {
                                        if (NULL == (str.AssignCharP(name)))
                                            goto NoMemory;
                                        if (NULL == (str.AppendCharP3(" (", langName, ")")))
                                            goto NoMemory;
                                        name = str.GetCStr();
                                    }
                                }
                            }
                        }
                        if (NULL == (dispNames[strCount] = StringCopy(name)))
                            goto NoMemory;
                            
                        if (term)
                            replaceCharInString(dispNames[strCount], '_', ' ');
                        
                        if (NULL == (urls[strCount] = StringCopy(props->resource)))
                            goto NoMemory;
                    }
                    ++strCount;
                }                    
            }
        }
    }
    return true;
NoMemory:
    if (NULL != dispNames)
        FreeStringList(dispNames, count);
    dispNames = NULL;
    if (NULL != urls)
        FreeStringList(urls, count);
    urls = NULL;
    count = 0;
    return false;
}
 */

/* 
static char_t** LangCodesListToLangNames(char_t** codes, ulong_t count)
{
    typedef char_t* cstr;
    cstr* names = new_nt cstr[count];
    if (NULL == names)
        return NULL;
    memzero(names, sizeof(cstr) * count);
    for (ulong_t i = 0; i < count; ++i)
    {
        const char_t* name = GetLangNameByLangCode(codes[i], tstrlen(codes[i]));
        names[i] = StringCopy(name);
        if (NULL == names[i])
            goto NoMemory;
    }
    return names;
NoMemory:
    FreeStringList(names, count);
    return NULL;
}
 */
 
static PopupMenuModel* BuildSelectionMenuModel(const String& text)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    PopupMenuModel::Item* items = NULL;
#ifdef NDEBUG
    static const ulong_t count = 2;    
#else
    static const ulong_t count = 3;
#endif    
    CDynStr str;
    PopupMenuModel* model = new_nt PopupMenuModel();
    if (NULL == model)
        goto NoMemory;
    
    items = new_nt PopupMenuModel::Item[count];
    if (NULL == items)
        goto NoMemory;
    
    items[0].text = StringCopy2("Search Encyclopedia");
    if (NULL == items[0].text)
        goto NoMemory;
    
    if (NULL == str.AppendCharP3(urlSchemaEncyclopediaSearch urlSeparatorSchemaStr, app.preferences().pediaPrefs.languageCode, ":"))
        goto NoMemory;
    
    if (NULL == str.AppendCharPBuf(text.data(), text.length()))
        goto NoMemory;
    
    items[0].hyperlink = str.ReleaseStr();
    items[0].active = true;
    items[0].bold = true;
    
    items[1].text = StringCopy2("Copy");
    if (NULL == items[1].text)
        goto NoMemory;
        
    if (NULL == str.AssignCharP(urlSchemaClipboardCopy urlSeparatorSchemaStr))
        goto NoMemory;
        
    if (NULL == str.AppendCharPBuf(text.data(), text.length()))
        goto NoMemory;
        
    items[1].hyperlink = str.ReleaseStr();
    items[1].active = true;

#ifndef NDEBUG

    items[2].text = StringCopy2("Search in Amazon store");
    if (NULL == items[2].text)
        goto NoMemory;
        
    if (NULL == str.AssignCharP(urlSchemaAmazonSearch urlSeparatorSchemaStr))
        goto NoMemory;
        
    if (NULL == str.AppendCharP(_T("Blended;;1;")))
        goto NoMemory;
        
    if (NULL == str.AppendCharPBuf(text.data(), text.length()))
        goto NoMemory;

    items[2].hyperlink = str.ReleaseStr();
    items[2].active = true;

#endif    
        
    model->setItems(items, count);
    return model;
NoMemory:
    app.alert(notEnoughMemoryAlert);
    delete [] items;
    delete model;
    return NULL;
}
 
static const char* bootstrapLangCodes[] = {
    "en",
    "de",
    "fr"
};

static char** ExtractLangCodesFromElements(const Definition::Elements_t& elems, ulong_t& count)
{
    typedef char_t* cstr;
    cstr* arr = NULL;
    ulong_t len;
    ulong_t prefixLen = tstrlen(urlSchemaEncyclopedia urlSeparatorSchemaStr pediaUrlPartSetLang urlSeparatorSchemaStr);
    Definition::Elements_t::const_iterator end = elems.end();
    for (uint_t phase = 0; phase < 2; ++phase)
    {
        if (1 == phase)
        {
            count = len;
            arr = new_nt cstr[len];
            if (NULL == arr)
                goto Error;
            memzero(arr, sizeof(cstr) * len);
        }
        len = 0;
        for (Definition::Elements_t::const_iterator it = elems.begin(); it != end; ++it)
        {
            const DefinitionElement* elem = *it;
            if (!elem->isHyperlink())
                continue;
            
            const DefinitionElement::HyperlinkProperties& props = *elem->hyperlinkProperties();
            if (!StrStartsWith(props.resource.data(), props.resource.length(), urlSchemaEncyclopedia urlSeparatorSchemaStr pediaUrlPartSetLang urlSeparatorSchemaStr, prefixLen))
                continue;
            
            if (1 == phase)
            {
                const char* code = props.resource.c_str() + prefixLen;
                arr[len] = StringCopy(code);
                if (NULL == arr[len])
                    goto Error;
            }
            
            ++len;            
        }
    }
    return arr;
Error:
    if (NULL != arr)
        FreeStringList(arr, count);
    count = ARRAY_SIZE(bootstrapLangCodes);
    return (char**)bootstrapLangCodes;    
}
 
PediaMainForm::PediaMainForm(MoriartyApplication& app):
    MoriartyForm(app, pediaMainForm),
    scrollBar_(*this),
    doneButton_(*this),
    searchButton_(*this),
    articleRenderer_(*this, &scrollBar_),
    infoRenderer_(*this, &scrollBar_),
    historyButton_(*this),
    historySupport_(*this),
    displayMode_(showAbout),
    renderingProgressReporter_(new_nt iPediaRenderingProgressReporter(*this)),
    searchTerm_(NULL),
    articleTitle_(NULL),
    searchTitle_(NULL),
    availLangCodes_((char**)bootstrapLangCodes),
    availLangCodesCount_(ARRAY_SIZE(bootstrapLangCodes))
 {
    historySupport_.popupMenuFillHandlerData = (void*)(urlSchemaEncyclopedia urlSeparatorSchemaStr pediaUrlPartHome);
    
//    setFocusControlId(doneButton);
    historySupport_.setup(pediaHistoryCacheName, historyPopupMenu, historyButton, app.hyperlinkHandler, ReadUrlFromCache);
    infoRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    infoRenderer_.setInteractionBehavior(
        TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavUpDownScroll
    );
    infoRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
    
    articleRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    articleRenderer_.setRenderingProgressReporter(renderingProgressReporter_);
    articleRenderer_.setInteractionBehavior(
        TextRenderer::behavDoubleClickSelection
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
      | TextRenderer::behavUpDownScroll
      | TextRenderer::behavSelectionClickAction
    );
    articleRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
    articleRenderer_.setupSelectionMenu(BuildSelectionMenuModel, selectionMenu);
}

void PediaMainForm::clearLangCodes()
{
    if (bootstrapLangCodes != availLangCodes_)
    {
        FreeStringList(availLangCodes_, availLangCodesCount_);
        availLangCodes_ = (char**)bootstrapLangCodes;
        availLangCodesCount_ = ARRAY_SIZE(bootstrapLangCodes);
    }
}

PediaMainForm::~PediaMainForm() 
{
    delete renderingProgressReporter_;
    FreeCharP(&searchTerm_);
    FreeCharP(&articleTitle_);
    FreeCharP(&searchTitle_);
    clearLangCodes();
}

void PediaMainForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    articleRenderer_.attach(articleRenderer);
    infoRenderer_.attach(infoRenderer);
    searchButton_.attach(searchButton);
    doneButton_.attach(doneButton);
    historyButton_.attach(historyButton);    
}

bool PediaMainForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    setDisplayMode(showAbout);
    return result;
}

void PediaMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(bounds = screenBounds);
    
    articleRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    infoRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);

    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    searchButton_.anchor(screenBounds, anchorLeftEdge, 59, anchorTopEdge, 14);
    historyButton_.anchor(screenBounds, anchorLeftEdge, 13, anchorTopEdge, 14);

    update();    
}

bool PediaMainForm::handleEvent(EventType& event)
{
    if (historySupport_.handleEventInForm(event))
        return true;
        
    if ((showAbout == displayMode_ 
    || showLinkedArticles == displayMode_ 
    || showLinkingArticles == displayMode_
    || showSearchResults == displayMode_
    )
         && infoRenderer_.handleEventInForm(event))
        return true;

    if (showArticle == displayMode_ && articleRenderer_.handleEventInForm(event))
        return true;
        
    MoriartyApplication& app = application();
//    PediaPreferences& prefs = app.preferences().pediaPrefs;

    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handled = handleControlSelect(event);
            break;
            
        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled = true;
            break;

/*            
        case lstSelectEvent:
            if (resultsList == event.data.lstSelect.listID)
            {
                if (noListSelection == event.data.lstSelect.selection)
                    return true;
                
                if (showLanguages == displayMode_)
                {
                    const char_t* str = availLangCodes_[event.data.lstSelect.selection];
                    changeLanguage(str);
                }
                return true;
            }
            // Intentional fall-through
 */
             
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

void PediaMainForm::randomArticle()
{
    MoriartyApplication& app = application();
    LookupManager*       lm;
    CDynStr              url;

    if (NULL == url.AppendCharP3(urlSchemaEncyclopediaRandom, urlSeparatorSchemaStr, app.preferences().pediaPrefs.languageCode))
        goto NoMemory;

    lm = app.lookupManager;
    if (NULL == lm)
        goto NoMemory;

    if (memErrNotEnoughSpace == lm->fetchUrl(url.GetCStr()))
        goto NoMemory;

    return;
NoMemory:
     app.alert(notEnoughMemoryAlert);
     return;
}

bool PediaMainForm::handleMenuCommand(UInt16 itemId)
{
    MoriartyApplication& app = application();
    LookupManager& lm = *app.lookupManager;

    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            return true;

        case searchMenuItem:
            searchButton_.hit();
            return true;

        case randomArticleMenuItem:
            randomArticle();
            return true;

        case searchResultsMenuItem:
            if (showSearchResults == displayMode_)
                return true;

            if (NULL == lm.lastPediaSearchResults)
            {
                app.alert(pediaNoSearchResultsAlert);
                return true;
            }

            setDisplayMode(showSearchResults);
            update();
            return true;

        case homeMenuItem:
            if (showAbout == displayMode_)
                return true;

            setDisplayMode(showAbout);
            update();
            return true;

        case copyMenuItem:
            if (showArticle != displayMode_)
                return true;
            articleRenderer_.copySelectionOrAll();
            return true;

        case historyMenuItem:
            historyButton_.hit();
            return true;

        case forwardMenuItem:
            historySupport_.moveNext();
            return true;

        case backMenuItem:
            historySupport_.movePrevious();
            return true;

        case linkedArticlesMenuItem:
            if (showLinkedArticles == displayMode_)
                return true;

            if (NULL == lm.lastPediaArticle)
            {
                app.alert(pediaNoArticleAlert);
                return true;
            }
            assert(NULL != lm.lastPediaLinkedArticles);

            setDisplayMode(showLinkedArticles);
            update();
            return true;

        case linkingArticlesMenuItem:
            if (showLinkingArticles == displayMode_)
                return true;

            if (NULL == lm.lastPediaArticle)
            {
                app.alert(pediaNoArticleAlert);
                return true;
            }
            assert(NULL != lm.lastPediaLinkingArticles);

            setDisplayMode(showLinkingArticles);
            update();
            return true;

        case changeDatabaseMenuItem:
            if (NULL == application().lookupManager->lastPediaLanguages)
            {
                application().lookupManager->fetchUrl(urlSchemaEncyclopediaLangs urlSeparatorSchemaStr);
                return true;                
            }
            setDisplayMode(showLanguages);
            update();
            return true;

#ifdef INTERNAL_BUILD                    
        case toggleStressModeMenuItem:
            assert(false);
            break;
#endif            

        default:
            assert(false);
    }
    return false;
}

void PediaMainForm::setDisplayMode(DisplayMode dm)
{
    LookupManager& lm = *application().lookupManager;
    CDynStr str;
    switch (displayMode_=dm)
    {
        case showArticle:
            infoRenderer_.hide();

            if (NULL != articleTitle_)
                setTitle(articleTitle_);
            else
                setTitle("Encyclopedia");

            scrollBar_.show();
            doneButton_.show();
            searchButton_.show();
            articleRenderer_.setModel(lm.lastPediaArticle, Definition::ownModelNot);
            articleRenderer_.show();
//            articleRenderer_.focus();
            break;

        case showSearchResults:
            articleRenderer_.hide();
            scrollBar_.hide();

            if (NULL != searchTerm_ && NULL != str.AppendCharP3("'", searchTerm_, "' - search results"))
                setTitle(str.GetCStr());
            else
                setTitle("Search results");

            infoRenderer_.setModel(lm.lastPediaSearchResults, Definition::ownModelNot);
            scrollBar_.show();
            infoRenderer_.show();

            doneButton_.show();
            searchButton_.show();
//            infoRenderer_.focus();
            break; 

        case showLinkingArticles:
            articleRenderer_.hide();
            scrollBar_.hide();

            if (NULL != articleTitle_ && NULL != str.AppendCharP3("'", articleTitle_, "' - linking articles"))
                setTitle(str.GetCStr());
            else
                setTitle("Linking articles");                    

            infoRenderer_.setModel(lm.lastPediaLinkingArticles, Definition::ownModelNot);
            scrollBar_.show();
            infoRenderer_.show();
            doneButton_.show();
            searchButton_.show();
//            infoRenderer_.focus();
            break; 

        case showLinkedArticles:
            articleRenderer_.hide();
            scrollBar_.hide();

            if (NULL != articleTitle_ && NULL != str.AppendCharP3("'", articleTitle_, "' - linked articles"))
                setTitle(str.GetCStr());
            else
                setTitle("Linked articles");                    

            infoRenderer_.setModel(lm.lastPediaLinkedArticles, Definition::ownModelNot);
            scrollBar_.show();
            infoRenderer_.show();
            doneButton_.show();
            searchButton_.show();
 //           infoRenderer_.focus();
            break;

        case showLanguages:
            articleRenderer_.hide();

            setTitle("Available languages");

            infoRenderer_.setModel(lm.lastPediaLanguages, Definition::ownModelNot);
            infoRenderer_.show();
            scrollBar_.show();
            doneButton_.show();
 //           infoRenderer_.focus();
            break;            

        case showAbout:
            articleRenderer_.hide();        
            setTitle("Encyclopedia");

            scrollBar_.show();
            doneButton_.show();
            searchButton_.show();
            prepareAbout();
            infoRenderer_.show();
//            infoRenderer_.focus();
            break;

        default:
            assert(false);
    }
}

bool PediaMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            return true;

        case searchButton:
            handleSearch();
            return true;

        default:
            assert(false);
    }
    return false;
}

static void StripUnderscoresInList(char_t** list, ulong_t count)
{   
    for (ulong_t i = 0; i < count; ++i)
    {
        char_t* str = list[i];
        replaceCharInString(str, '_', ' ');
    }
}

void PediaMainForm::handleLookupFinished(const EventType& event)
{
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL != lookupManager);

    const LookupFinishedEventData& data = reinterpret_cast<const LookupFinishedEventData&>(event.data);
    CDynStr str;

    switch (data.result)
    {
        case lookupResultPediaArticle:
            ReplaceCharP(&articleTitle_, lookupManager->lastPediaArticleTitle);
            lookupManager->lastPediaArticleTitle = NULL;

            ReplaceCharP(&searchTerm_, StringCopy2(articleTitle_));

            historySupport_.lookupFinished(true, articleTitle_);
            FinishCrossModuleLookup(historySupport_, pediaModuleName);
            setDisplayMode(showArticle);
            update();
            break;

        case lookupResultPediaSearch:
            ReplaceCharP(&searchTitle_, lookupManager->lastPediaArticleTitle);
            lookupManager->lastPediaArticleTitle = NULL;

            if (NULL == str.AppendCharP3("Search for '", searchTitle_, "'"))
            {
                app.alert(notEnoughMemoryAlert);
                return;
            }

            ReplaceCharP(&searchTerm_, StringCopy2(searchTitle_));

            historySupport_.lookupFinished(true, str.GetCStr());
            FinishCrossModuleLookup(historySupport_, pediaModuleName);

            setDisplayMode(showSearchResults);
            update();
            break;

        case lookupResultPediaLanguages:
            assert(!lookupManager->crossModuleLookup);
            clearLangCodes();
            if (NULL != lookupManager->lastPediaLanguages)
                availLangCodes_ = ExtractLangCodesFromElements(lookupManager->lastPediaLanguages->elements, availLangCodesCount_);
            setDisplayMode(showLanguages);
            update();
            break;

        case lookupResultPediaStats:
            //assert(!lookupManager->crossModuleLookup);
            if (showAbout == displayMode_)
            {
                prepareAbout();
                update();
            }
            break;

        default:
            if (HandleCrossModuleLookup(event, pediaHistoryCacheName, pediaModuleName))
                return;

            assert(!lookupManager->crossModuleLookup);
            update();
    }
    lookupManager->handleLookupFinishedInForm(data);
}

void PediaMainForm::handleSearch()
{
    MoriartyApplication& app = application();
    PediaSearchForm* searchForm = new_nt PediaSearchForm(app);
    if (NULL == searchForm)
    {
        app.alert(notEnoughMemoryAlert);
        return;
    }
    Err err = searchForm->initialize();
    if (errNone != err)
        goto Exit;

    searchForm->searchTerm = searchTerm_;

    Int16 buttonId = searchForm->showModal();
    update();
    bool extended = false;
    switch (buttonId)
    {
        case extendedSearchButton:
            extended = true;
            // Intentional fall-through
        case searchButton:
            search(searchForm->inputField.text(), extended);
            break;
    }
    
Exit:
    if (memErrNotEnoughSpace == err)
        app.alert(notEnoughMemoryAlert);
    delete searchForm;
}

void PediaMainForm::search(const char* text, bool extended)
{
    ReplaceCharP(&searchTerm_, StringCopy2(text));
    
    CDynStr str;
    const char_t* schema = urlSchemaEncyclopediaTerm urlSeparatorSchemaStr;
    if (extended)
        schema = urlSchemaEncyclopediaSearch urlSeparatorSchemaStr;

    MoriartyApplication& app = application();
    LookupManager* lm = app.lookupManager;

/*    
    if (extended)
    {
        if (NULL == str.AppendCharP3("Search for '", text, "'"))
            goto NoMemory;
        
        lm->setLastPediaSearchTitle(str.ReleaseStr());
    }
 */ 
        
    if (NULL == str.AppendCharP3(schema, app.preferences().pediaPrefs.languageCode, _T(":")))
        goto NoMemory;

    if (NULL == str.AppendCharP(text))
        goto NoMemory;

    if (memErrNotEnoughSpace == lm->fetchUrl(str.GetCStr()))
        goto NoMemory;

    return;
NoMemory:   
    app.alert(notEnoughMemoryAlert);
}

void PediaMainForm::fetchStats() const
{
    const MoriartyApplication& app = application();
    CDynStr str;
    if (NULL == str.AppendCharP3(urlSchemaEncyclopediaStats, urlSeparatorSchemaStr, app.preferences().pediaPrefs.languageCode))
        goto NoMem;

    if (memErrNotEnoughSpace == app.lookupManager->fetchUrl(str.GetCStr()))
        goto NoMem;

    return;
NoMem:
    app.alert(notEnoughMemoryAlert);
}

void PediaMainForm::prepareAbout()
{
    PediaPreferences& prefs = application().preferences().pediaPrefs;

    infoRenderer_.clear();

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }

    DefinitionModel::Elements_t& elems = model->elements;
    TextElement*  text;

    elems.push_back(text=new TextElement("Welcome to Encyclopedia."));
    text->setJustification(DefinitionElement::justifyCenter);
    text->setStyle(StyleGetStaticStyle(styleNameHeader));

    elems.push_back(new LineBreakElement(1, 2));
    elems.push_back(new LineBreakElement(1, 2));

    CDynStr str;
    const char_t* lang = GetLangNameByLangCode(prefs.languageCode, tstrlen(prefs.languageCode));
    if (NULL == str.AppendCharP3("You're using ", lang, " encyclopedia"))
        goto NoMemory;

    bool noStats = false;
    if (8 == tstrlen(prefs.dbDate))
    {
        if (NULL == str.AppendCharP(" last updated on "))
            goto NoMemory;
        if (NULL == str.AppendCharPBuf(prefs.dbDate, 4))
            goto NoMemory;
        if (NULL == str.AppendCharP("-"))
            goto NoMemory;
        if (NULL == str.AppendCharPBuf(&prefs.dbDate[4], 2))
            goto NoMemory;
        if (NULL == str.AppendCharP("-"))
            goto NoMemory;
        if (NULL == str.AppendCharPBuf(&prefs.dbDate[6], 2))
            goto NoMemory;
    }
    else
        noStats = true;

    if (prefs.articleCountNotChecked != prefs.articleCount)
    {
        char_t buffer[24];
        int len = formatNumber(prefs.articleCount, buffer, sizeof(buffer));
        if (NULL == str.AppendCharP(" with "))
            goto NoMemory;
        if (NULL == str.AppendCharPBuf(buffer, len))
            goto NoMemory;
        if (NULL == str.AppendCharP(" articles"))
            goto NoMemory;
    }
    else
        noStats = true;

//    if (noStats)
//        fetchStats();

    if (NULL == str.AppendCharP("."))
        goto NoMemory;

    elems.push_back(text = new TextElement(str.GetCStr()));
    text->setJustification(DefinitionElement::justifyLeft);

    uint_t l = 0;
    elems.push_back(text = new TextElement(" You can change encyclopedia to "));
    elems.back()->setJustification(DefinitionElement::justifyLeft);
    for (ulong_t i = 0; i < availLangCodesCount_; ++i)
    {
        const char_t* code = availLangCodes_[i];
        if (0 == tstrcmp(code, prefs.languageCode))
            continue;

        const char_t* name = GetLangNameByLangCode(code, tstrlen(code));
        assert(NULL != name);
        if (NULL == name)
            continue;

        text = new_nt TextElement(name);
        if (NULL == text)
            goto NoMemory;
        elems.push_back(text);
        elems.back()->setJustification(DefinitionElement::justifyLeft);

        if (NULL == str.AssignCharP(urlSchemaEncyclopedia urlSeparatorSchemaStr pediaUrlPartSetLang urlSeparatorSchemaStr))
            goto NoMemory;

        if (NULL == str.AppendCharP(code))
            goto NoMemory;

        text->setHyperlink(str.GetCStr(), hyperlinkUrl);

        const char_t* delim = _T(", ");
        ++l;
        if (availLangCodesCount_ - 2 == l)
            delim = _T(" or ");                        
        else if (availLangCodesCount_ - 1 == l)
            delim = NULL;

        if (NULL != delim)
        {
            text = new_nt TextElement(delim);
            if (NULL == text)
                goto NoMemory;
            elems.push_back(text);
            elems.back()->setJustification(DefinitionElement::justifyLeft);
        }    
    }

    elems.push_back(new LineBreakElement(1, 2));
    elems.push_back(new LineBreakElement(1, 2));
    //elems.back()->setJustification(DefinitionElement::justifyLeft);

    elems.push_back(new TextElement("You can "));
    elems.back()->setJustification(DefinitionElement::justifyLeft);

    elems.push_back(text = new TextElement("search"));
    elems.back()->setJustification(DefinitionElement::justifyLeft);

    text->setHyperlink(urlSchemaEncyclopedia urlSeparatorSchemaStr pediaUrlPartSearchDialog, hyperlinkUrl);
    elems.push_back(new TextElement(" for articles or get a "));
    elems.back()->setJustification(DefinitionElement::justifyLeft);

    elems.push_back(text = new TextElement("random"));
    if (NULL == str.AssignCharP(urlSchemaEncyclopediaRandom urlSeparatorSchemaStr))
        goto NoMemory;
    if (NULL == str.AppendCharP(prefs.languageCode))
        goto NoMemory;
    text->setHyperlink(str.GetCStr(), hyperlinkUrl);
    elems.back()->setJustification(DefinitionElement::justifyLeft);
    elems.push_back(new TextElement(" article."));
    elems.back()->setJustification(DefinitionElement::justifyLeft);
    infoRenderer_.setModel(model, Definition::ownModel);
    return;
NoMemory:
    delete model;
    application().alert(notEnoughMemoryAlert);   
}

void PediaMainForm::handleAbout()
{   
    if (showAbout != displayMode_)
    {
        setDisplayMode(showAbout);
        update();
    }
}

void PediaMainForm::handleArticle()
{
    if (showArticle != displayMode_)
    {
        setDisplayMode(showArticle);
        update();
    }
}

void PediaMainForm::changeLanguage(const char_t* code)
{
    PediaPreferences& prefs = application().preferences().pediaPrefs;
    if (0 != tstrcmp(code, prefs.languageCode))
    {
        prefs.articleCount = prefs.articleCountNotChecked;
        memmove(prefs.languageCode, code, tstrlen(code) * sizeof(char_t));
        prefs.dbDate[0] = '\0';
    }
    setDisplayMode(showAbout);
    update();
}

void PediaMainForm::invalidateRenderers()
{
    infoRenderer_.setModel(NULL);
    articleRenderer_.setModel(NULL);
}
