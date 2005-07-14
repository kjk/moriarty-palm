#include <Text.hpp>

#include "LookupManager.hpp"
#include "ByteFormatParser.hpp"
#include "HyperlinkHandler.hpp"
#include "History.hpp"
#include "MoriartyPreferences.hpp"

#include "DictMainForm.hpp"
#include "DictSearchForm.hpp"
#include <TextElement.hpp>

static PopupMenuModel* BuildSelectionMenuModel(const String& text)
{
    MoriartyApplication&    app = MoriartyApplication::instance();
    PopupMenuModel::Item*   items = NULL;
    ulong_t                 count = 2;
    CDynStr                 str;
    PopupMenuModel*         model = new_nt PopupMenuModel();

    if (NULL == model)
        goto NoMemory;

    items = new_nt PopupMenuModel::Item[2];
    if (NULL == items)
        goto NoMemory;

    items[0].text = StringCopy2("Search Dictionary");
    if (NULL == items[0].text)
        goto NoMemory;

    if (NULL == str.AppendCharP2(urlSchemaDictTerm urlSeparatorSchemaStr, app.preferences().dictionaryPreferences.dictionaryCode))
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

    model->setItems(items, count);
    return model;
NoMemory:
    app.alert(notEnoughMemoryAlert);
    delete [] items;
    delete model;
    return NULL;
}

DictMainForm::DictMainForm(MoriartyApplication& app):
    MoriartyForm(app, dictMainForm),
    scrollBar_(*this),
    doneButton_(*this),
    searchButton_(*this),
    historyButton_(*this),
    historySupport_(*this),
    textRenderer_(*this, &scrollBar_),
    searchTerm_(NULL)
{
    historySupport_.popupMenuFillHandlerData = (void*)(urlSchemaDict urlSeparatorSchemaStr pediaUrlPartHome);
    setFocusControlId(doneButton);

    textRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    //textRenderer_.setRenderingProgressReporter(renderingProgressReporter_);
    textRenderer_.setInteractionBehavior(
        TextRenderer::behavDoubleClickSelection
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
      | TextRenderer::behavUpDownScroll
      | TextRenderer::behavSelectionClickAction
    );
    textRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
    textRenderer_.setupSelectionMenu(BuildSelectionMenuModel, selectionMenu);

    historySupport_.popupMenuFillHandlerData = (void*)(urlSchemaDictForm _T(":main"));
    historySupport_.setup(dictHistoryCacheName, historyPopupMenu, historyButton, app.hyperlinkHandler, ReadUrlFromCache);
}

DictMainForm::~DictMainForm() 
{
    FreeCharP(&searchTerm_);
}

void DictMainForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    textRenderer_.attach(articleRenderer);
    searchButton_.attach(searchButton);
    doneButton_.attach(doneButton);
    historyButton_.attach(historyButton);    
}

bool DictMainForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL != lookupManager);

    textRenderer_.show();
    scrollBar_.show();
    showMain();
    return result;
}

void DictMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(bounds = screenBounds);

    textRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);

    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    searchButton_.anchor(screenBounds, anchorLeftEdge, 59, anchorTopEdge, 14);
    historyButton_.anchor(screenBounds, anchorLeftEdge, 13, anchorTopEdge, 14);

    update();    
}

void DictMainForm::showMain()
{
    DictionaryPreferences& prefs = application().preferences().dictionaryPreferences;

    textRenderer_.clear();

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }

    DefinitionModel::Elements_t& elems = model->elements;
    TextElement*  text;

    elems.push_back(text=new TextElement("Welcome to Dictionary."));
/*    text->setJustification(DefinitionElement::justifyCenter);
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

    elems.push_back(new TextElement("Press \"Search\" button to "));
    elems.back()->setJustification(DefinitionElement::justifyLeft);

    elems.push_back(text = new TextElement("find"));
    elems.back()->setJustification(DefinitionElement::justifyLeft);

    text->setHyperlink(urlSchemaEncyclopedia urlSeparatorSchemaStr pediaUrlPartSearchDialog, hyperlinkUrl);
    elems.push_back(new TextElement(" an article you want or use menu item \"Main/Random article\" to get a "));
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
    */
    
    textRenderer_.setModel(model, Definition::ownModel);
    update();
    return;
NoMemory:
    delete model;
    application().alert(notEnoughMemoryAlert);   
}

bool DictMainForm::handleEvent(EventType& event)
{
    if (historySupport_.handleEventInForm(event))
        return true;

    if (textRenderer_.handleEventInForm(event))
        return true;

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

        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

void DictMainForm::randomWord()
{
    MoriartyApplication& app = application();
    LookupManager*       lm;
    CDynStr              url;

    if (NULL == url.AppendCharP3(urlSchemaDictRandom, urlSeparatorSchemaStr, app.preferences().dictionaryPreferences.dictionaryCode))
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

bool DictMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled=false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            handled = true;
            break;

        case randomWordMenuItem:
            randomWord();
            return true;

        case homeMenuItem:
            showMain();
            update();
            return true;

        case copyMenuItem:
            assert(false); // not implemented yet
            textRenderer_.copySelectionOrAll();
            handled = true;
            break;

       case historyMenuItem:
           historyButton_.hit();
           return true;

       case forwardMenuItem:
           historySupport_.moveNext();
           return true;

       case backMenuItem:
           historySupport_.movePrevious();
           return true;

       case lookupClipboardMenuItem:
            assert(false); // not implemented yet
            handled = true;
            break;

        default:
            assert(false);
    }
    return handled;
}

void DictMainForm::handleHistory()
{
    historyButton_.hit();    
}

void DictMainForm::handleSearch()
{
    MoriartyApplication& app = application();
    DictSearchForm* searchForm = new_nt DictSearchForm(app);
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
    switch (buttonId)
    {
        case searchButton:
            search(searchForm->inputField.text());
            break;
    }

Exit:
    if (memErrNotEnoughSpace == err)
        app.alert(notEnoughMemoryAlert);
    delete searchForm;
}

void DictMainForm::search(const char_t* text)
{
    ReplaceCharP(&searchTerm_, StringCopy2(text));

    CDynStr         str;
    const char_t *  schema = urlSchemaDictTerm urlSeparatorSchemaStr;

    MoriartyApplication& app = application();
    LookupManager* lm = app.lookupManager;

    if (NULL == str.AppendCharP3(schema, app.preferences().dictionaryPreferences.dictionaryCode, text))
        goto NoMemory;

    if (memErrNotEnoughSpace == lm->fetchUrl(str.GetCStr()))
        goto NoMemory;

    return;
NoMemory:   
    app.alert(notEnoughMemoryAlert);
}

bool DictMainForm::handleControlSelect(const EventType& event)
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

void DictMainForm::readUdf()
{
    UniversalDataFormat* udf = &application().lookupManager->dictData;
    if (udf->empty())
    {
        showMain();
        return;
    }

    for (int i=0; i < udf->getItemsCount(); i++)
    {
        switch (udf->getItemText(i,0)[0])
        {
            case _T('D'): //definition
            {
                ByteFormatParser parser;
                ulong_t          dataLen;
                const char_t *   data = udf->getItemTextAndLen(i, 1, &dataLen);
                parser.parseAll(data, dataLen);
                DefinitionModel* model = parser.releaseModel();
                if (NULL == model)
                {
                    application().alert(notEnoughMemoryAlert);
                    return;
                }
                textRenderer_.setModel(model, Definition::ownModel);
                break;
            }

            case _T('H'):
                historySupport_.lookupFinished(true, udf->getItemText(i,1));
                break;

            default:
                assert(false);
                break;
        }
    }
    update();
}

void DictMainForm::handleLookupFinished(const EventType& event)
{
    MoriartyApplication & app = application();
    LookupManager *       lookupManager = app.lookupManager;
    assert(NULL != lookupManager);
    const LookupFinishedEventData& data = reinterpret_cast<const LookupFinishedEventData&>(event.data);

    switch (data.result)
    {
        case lookupResultDictDef:
            readUdf();
            break;

        // linked modules
        default:
            if (HandleCrossModuleLookup(event, dictHistoryCacheName, dictModuleName))
                return;
    }
    lookupManager->handleLookupFinishedInForm(data);
}

