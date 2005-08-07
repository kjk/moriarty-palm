#include <Text.hpp>

#include "LookupManager.hpp"
#include "ByteFormatParser.hpp"
#include "HyperlinkHandler.hpp"
#include "History.hpp"
#include "MoriartyPreferences.hpp"

#include "DictMainForm.hpp"
#include "DictSearchForm.hpp"
#include <TextElement.hpp>
#include <LineBreakElement.hpp>

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

    if (NULL == str.AppendCharP3(urlSchemaDictTerm urlSeparatorSchemaStr, app.preferences().dictionaryPreferences.dictionaryCode, _T(":")))
        goto NoMemory;

    // remove '\n' from text
    replaceCharInString((char_t*) text.data(), _T('\n'), _T(' '));

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
    text->setJustification(DefinitionElement::justifyCenter);
    text->setStyle(StyleGetStaticStyle(styleNameHeader));

    elems.push_back(new LineBreakElement(3, 2));

    elems.push_back(text=new TextElement("You are using "));
    elems.push_back(text=new TextElement(prefs.dictionaryName));
    
    if (prefs.wordsCountNotChecked != prefs.wordsCount)
    {
        //elems.push_back(new LineBreakElement());
        elems.push_back(text=new TextElement(" with "));
        char_t buffer[24];
        int len = formatNumber(prefs.wordsCount, buffer, sizeof(buffer));
        elems.push_back(text=new TextElement(buffer));
        elems.push_back(text=new TextElement(" definitions"));
    }
    elems.push_back(text=new TextElement("."));

    elems.push_back(new LineBreakElement(3, 2));
    elems.push_back(text=new TextElement("You can "));
    elems.push_back(text=new TextElement("search"));
    text->setHyperlink(_T("dictform:search") , hyperlinkUrl);
    elems.push_back(text=new TextElement(" for definitions, get "));
    elems.push_back(text=new TextElement("random"));
    text->setHyperlink(_T("dictform:random") , hyperlinkUrl);
    elems.push_back(text=new TextElement(" word definition, "));
    elems.push_back(text=new TextElement("see history"));
    text->setHyperlink(_T("dictform:history") , hyperlinkUrl);
    elems.push_back(text=new TextElement(" of searches or use "));
    elems.push_back(text=new TextElement("another dictionary"));
#ifdef SHIPPING
    text->setHyperlink(urlSchemaDictChangeDict , hyperlinkUrl);
#else
    text->setHyperlink(urlSchemaDictChangeDictNonShip , hyperlinkUrl);
#endif
    elems.push_back(text=new TextElement("."));

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
    
    DictionaryPreferences& prefs = app.preferences().dictionaryPreferences;

    if (NULL == url.AppendCharP3(urlSchemaDictRandom, urlSeparatorSchemaStr, prefs.dictionaryCode))
        goto NoMemory;

    // add increasing sufix - to make url unique
    prefs.randomWordSufix = (prefs.randomWordSufix+1) % 100;
    char_t buffer[16];    
    StrPrintF(buffer, ":%d", prefs.randomWordSufix);

    if (NULL == url.AppendCharP(buffer))
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

void DictMainForm::changeDict(void)
{
    MoriartyApplication& app = application();
    LookupManager*       lm;
    CDynStr              url;

    lm = app.lookupManager;
    if (NULL == lm)
        goto NoMemory;
    
    DictionaryPreferences& prefs = app.preferences().dictionaryPreferences;

    if (memErrNotEnoughSpace == lm->fetchUrl(urlSchemaDictChangeDict))
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

        case changeDictMenuItem:
            changeDict();
            return true;

        case homeMenuItem:
            showMain();
            update();
            return true;

        case copyMenuItem:
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
            { 
                UInt16 length = 0;
                
                MemHandle handle = ClipboardGetItem(clipboardText, &length);
                if (handle)
                {
                    const char_t* text = (const char_t*) MemHandleLock(handle);
                    if (NULL != text)
                    {
                        String textS = String(text, length);
                        MemHandleUnlock(handle); 
                        replaceCharInString((char_t*) textS.data(), _T('\n'), _T(' '));
                        search(textS.data());
                    }
                }
            }                   
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

    if (NULL == str.AppendCharP(schema))
        goto NoMemory;

    if (NULL == str.AppendCharP3(app.preferences().dictionaryPreferences.dictionaryCode, _T(":"), text))
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
            
        case lookupResultDictStats:
            showMain();
            break;

        // linked modules
        default:
            if (HandleCrossModuleLookup(event, dictHistoryCacheName, dictModuleName))
                return;
    }
    lookupManager->handleLookupFinishedInForm(data);
}

