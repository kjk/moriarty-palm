#include <Text.hpp>
#include <LineBreakElement.hpp>
#include <BulletElement.hpp>
#include <DefinitionElement.hpp>
#include <DynStr.hpp>

#include "LookupManager.hpp"
#include "HyperlinkHandler.hpp"
#include "iPediaRenderingProgressReporter.hpp"
#include "History.hpp"
#include "MoriartyPreferences.hpp"

#include "eBookMainForm.hpp"
#include "eBookSearchForm.hpp"
#include "eBookFormats.hpp"
#include <SysUtils.hpp>
#include "eBookPreferencesForm.hpp"

#include "MoriartyStyles.hpp"

EBookMainForm::EBookMainForm(MoriartyApplication& app):
    MoriartyForm(app, ebookMainForm),
    scrollBar_(*this),
    doneButton_(*this),
    searchButton_(*this),
    infoRenderer_(*this, &scrollBar_),
    historyButton_(*this),
    historySupport_(*this),
    displayMode_(showBrowseResults),
    renderingProgressReporter_(new_nt iPediaRenderingProgressReporter(*this)),
    searchResults_(NULL),
    browseResults_(NULL),
    lastSearchPhrase_(NULL)
 {
    historySupport_.popupMenuFillHandlerData = (void*)(urlSchemaEBookHome urlSeparatorSchemaStr);
    
//    setFocusControlId(doneButton);
    historySupport_.setup(ebookHistoryCacheName, historyPopupMenu, historyButton, app.hyperlinkHandler, ReadUrlFromCache);
    infoRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    infoRenderer_.setInteractionBehavior(
        TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavUpDownScroll
    );
    infoRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);

    setupPopupMenu(linkPopupMenu, MoriartyApplication::extEventShowMenu, app.hyperlinkHandler);
    
}

EBookMainForm::~EBookMainForm() 
{
    delete renderingProgressReporter_;
    delete searchResults_;
    delete browseResults_;
    
    FreeCharP(&lastSearchPhrase_);
}

void EBookMainForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    infoRenderer_.attach(infoRenderer);
    searchButton_.attach(searchButton);
    doneButton_.attach(doneButton);
    historyButton_.attach(historyButton);    
}

void EBookMainForm::home()
{
    const char* url = urlSchemaEBookHome urlSeparatorSchemaStr;
    application().hyperlinkHandler->handleHyperlink(url, StrLen(url), NULL);
}


bool EBookMainForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    MoriartyApplication& app = application();
    LookupManager& lm = *app.lookupManager;
    if (!lm.crossModuleLookup)
        home();    
    return result;
}

void EBookMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(bounds = screenBounds);
    
    infoRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);

    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    searchButton_.anchor(screenBounds, anchorLeftEdge, 59, anchorTopEdge, 14);
    historyButton_.anchor(screenBounds, anchorLeftEdge, 13, anchorTopEdge, 14);

    update();    
}

bool EBookMainForm::handleEvent(EventType& event)
{
    if (historySupport_.handleEventInForm(event))
        return true;
        
    if (infoRenderer_.handleEventInForm(event))
        return true;

    MoriartyApplication& app = application();

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

void EBookMainForm::manage()
{
   if (showDownloadedEBooks == displayMode_)
        return;
    
    setDisplayMode(showDownloadedEBooks);
    update();
}

bool EBookMainForm::handleMenuCommand(UInt16 itemId)
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

        case searchResultsMenuItem:
            if (showSearchResults == displayMode_)
                return true;

            if (NULL == searchResults_)
            {
                // TODO: prepare appropriate alert
                app.alert(pediaNoSearchResultsAlert);
                return true;
            }

            setDisplayMode(showSearchResults);
            update();
            return true;
        
        case manageEBooksMenuItem:
            manage();
            return true;

        case homeMenuItem:
            home();
            return true;

        case copyMenuItem:
            infoRenderer_.copySelectionOrAll();
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
            
        case ebookPreferencesMenuItem:
        {
            Form* form = new_nt EBookPreferencesForm(app);
            if (NULL == form)
            {
                app.alert(notEnoughMemoryAlert);
                return true;
            }
            app.popupForm(form);
            return true;
        }

        default:
            assert(false);
    }
    return false;
}

void EBookMainForm::setDisplayMode(DisplayMode dm)
{
    LookupManager& lm = *application().lookupManager;
    CDynStr str;
    switch (displayMode_=dm)
    {
        case showBrowseResults: 
            assert(browseResults_ != NULL);        
            setTitle(browseResults_->title());
            infoRenderer_.setModel(browseResults_, Definition::ownModelNot);
            scrollBar_.show();
            infoRenderer_.show();
            doneButton_.show();
            searchButton_.show();
            break; 
    
        case showSearchResults:
            assert(searchResults_ != NULL);
            setTitle(searchResults_->title());
            infoRenderer_.setModel(searchResults_, Definition::ownModelNot);
            scrollBar_.show();
            infoRenderer_.show();
            doneButton_.show();
            searchButton_.show();
            break; 

        case showDownloadedEBooks:
            setTitle("eBooks - manage");
            scrollBar_.show();
            doneButton_.show();
            searchButton_.show();
            prepareDownloadedEBooks();
            infoRenderer_.show();
            break;
            
        default:
            assert(false);
    }
}

bool EBookMainForm::handleControlSelect(const EventType& event)
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

void EBookMainForm::handleLookupFinished(const EventType& event)
{
    MoriartyApplication& app = application();
    LookupManager* lookupManager = app.lookupManager;
    assert(NULL != lookupManager);

    const LookupFinishedEventData& data = reinterpret_cast<const LookupFinishedEventData&>(event.data);
    status_t err;
    switch (data.result)
    {
        case lookupResultEBookHome: 
            infoRenderer_.setModel(NULL);
            PassOwnership(lookupManager->eBookModel, browseResults_);
            
            if (EBookPreferences::versionNotChecked != lookupManager->ebookVersion)
                app.preferences().ebookPrefs.version = lookupManager->ebookVersion;
            
            setDisplayMode(showBrowseResults);
            update();
            break;

        case lookupResultEBookBrowse: 
            infoRenderer_.setModel(NULL);
            PassOwnership(lookupManager->eBookModel, browseResults_);

            historySupport_.lookupFinished(true, browseResults_->title());
            FinishCrossModuleLookup(historySupport_, ebookModuleName);

            setDisplayMode(showBrowseResults);
            update();
            break;
        
        case lookupResultEBookSearchResults:
            infoRenderer_.setModel(NULL);
            PassOwnership(lookupManager->eBookModel, searchResults_);
            
            historySupport_.lookupFinished(true, searchResults_->title());
            FinishCrossModuleLookup(historySupport_, ebookModuleName);
            
            setDisplayMode(showSearchResults);
            update();
            break;
            
        case lookupResultEBookDownload:
        {
            EBookFormat format = ebookFormat_Unknown;
            err = eBook_DetectDatabaseFormat(lookupManager->eBookVfsVolume, lookupManager->eBookFileName, format);
            if (errNone != err)
            {
                if (memErrNotEnoughSpace == err)
                    app.alert(notEnoughMemoryAlert);
                else
                    app.alert(unableToCompeleteOperationAlert);
                return;
            }
            const char_t* name = lookupManager->eBookDownloadInfo;
            const char_t* author;
            const char_t* title;
            ulong_t nameLen, authorLen, titleLen;
            bool r = eBook_ParseDatabaseInfo(name, nameLen, author, authorLen, title, titleLen);
            if (!r)
                return;
            
            EBookReader reader = eBook_DetectReaderForFormat(format);
            if (ebookReader_None == reader)
            {
                FrmCustomAlert(ebookDownloadFinishedNoReaderAlert, title, "", "");
                setDisplayMode(showDownloadedEBooks);
                update();
                return;
            }
            
            UInt16 res = FrmCustomAlert(ebookDownloadFinishedAlert, title, "", "");
            if (0 != res) // buttons are 0 - yes and 1 - no
            {
                setDisplayMode(showDownloadedEBooks);
                update();
                return;
            }
                
            err = eBook_LaunchReader(lookupManager->eBookVfsVolume, lookupManager->eBookFileName, reader);
            if (errNone != err)
            {
                if (memErrNotEnoughSpace == err)
                    app.alert(notEnoughMemoryAlert);
                else
                    app.alert(unableToCompeleteOperationAlert);
                return;
            }  
            break;
        }

        default:
            if (HandleCrossModuleLookup(event, ebookHistoryCacheName, ebookModuleName))
                return;

            assert(!lookupManager->crossModuleLookup);
            update();
    }
    lookupManager->handleLookupFinishedInForm(data);
    if (NULL == browseResults_)
        app.runMainForm();
        
}

void EBookMainForm::handleSearch()
{
    MoriartyApplication& app = application();
    EBookSearchForm* searchForm = new_nt EBookSearchForm(app);
    if (NULL == searchForm)
    {
        app.alert(notEnoughMemoryAlert);
        return;
    }
    Err err = searchForm->initialize();
    if (errNone != err)
        goto Exit;

    searchForm->searchPhrase = lastSearchPhrase_;

    Int16 buttonId = searchForm->showModal();
    update();
    if (searchButton == buttonId)
        search(searchForm->inputField.text());
        
Exit:
    if (memErrNotEnoughSpace == err)
        app.alert(notEnoughMemoryAlert);
    delete searchForm;
}

void EBookMainForm::search(const char* phrase, SearchType type)
{
    MoriartyApplication& app = application();
    assert(NULL != phrase);
    ReplaceCharP(&lastSearchPhrase_, StringCopy2(phrase));
    CDynStr str;
    if (NULL == lastSearchPhrase_)
        goto NoMemory;
    
    replaceCharInString(lastSearchPhrase_, ';', ' ');
    replaceCharInString(lastSearchPhrase_, ':', ' ');
    const char* typeStr = " any: ";
    if (searchAuthor == type)
        typeStr = " author: ";
    else if (searchTitle == type)
        typeStr = " title: ";
    
    if (NULL == str.AppendCharP3(urlSchemaEBook urlSeparatorSchemaStr ebookUrlPartSearch ": ", typeStr, lastSearchPhrase_))
        goto NoMemory;
    
    app.hyperlinkHandler->handleHyperlink(str.GetCStr(), str.Len(), NULL);       
    return;
NoMemory:   
    app.alert(notEnoughMemoryAlert);
}

static Err CreateVolNameHyperlink(CDynStr& out, const char_t* prefix, UInt16 srcVolume, const char* srcName, bool target, UInt16 targetVolume)
{
    if (NULL == out.AssignCharP(prefix))
        return memErrNotEnoughSpace;

    char buf[8];
    tprintf(buf, "%04x", srcVolume);
    if (NULL == out.AppendCharP3(buf, ":", srcName))
        return memErrNotEnoughSpace;

    if (!target)
        return errNone;
    
    tprintf(buf, "%04x", targetVolume);
    if (NULL == out.AppendCharP2(";", buf))
        return memErrNotEnoughSpace;
    return errNone;
}

static Err CreateEBookPopupMenuHyperlink(CDynStr& out, UInt16 vfsVolume, const char_t* name, const char_t* title, ulong_t titleLen, EBookFormat format, char** volNames, UInt16* volRefs, ulong_t volCount, EBookFormats formats)
{
    Err err;
    CDynStr link;
    CDynStr text;
    // Launch, Delete, Move to (volCount), Copy to (volCount), Search in amazon
    // ulong_t items = 2 + 2 * volCount;
    // Move to commented out
    ulong_t items = 2 + volCount;
    bool launchSupported = (0 != (formats & format));
    if (launchSupported)
        ++items;
    
    err = PopupMenuHyperlinkCreate(&out, urlSchemaMenu urlSeparatorSchemaStr, items);
    if (errNone != err)
        return err;
    
    if (launchSupported)
    {
        err = CreateVolNameHyperlink(link, urlSchemaEBook urlSeparatorSchemaStr ebookUrlPartLaunch ":", vfsVolume, name, false, 0);
        if (errNone != err)
            return err;

        err = PopupMenuHyperlinkAppendItem(&out, "Launch reader", link.GetCStr(), popupMenuItemBold);
        if (errNone != err)
            return err;
    }
    
    if (vfsVolumeMainMemory != vfsVolume)
    {
        err = CreateVolNameHyperlink(link, urlSchemaEBook urlSeparatorSchemaStr ebookUrlPartCopy ":", vfsVolume, name, true, vfsVolumeMainMemory);
        if (errNone != err)
            return err;
            
        err = PopupMenuHyperlinkAppendItem(&out, "Copy to main memory", link.GetCStr(), 0);
        if (errNone != err)
            return err;
    }
    
    for (ulong_t i = 0; i < volCount; ++i)
    {
        if (volRefs[i] == vfsVolume)
            continue;
            
        if (NULL == text.AssignCharP("Copy to "))
            return memErrNotEnoughSpace;
            
        if (NULL == text.AppendCharP(volNames[i]))
            return memErrNotEnoughSpace;
            
        err = CreateVolNameHyperlink(link, urlSchemaEBook urlSeparatorSchemaStr ebookUrlPartCopy ":", vfsVolume, name, true, volRefs[i]);
        if (errNone != err)
            return err;
            
        err = PopupMenuHyperlinkAppendItem(&out, text.GetCStr(), link.GetCStr(), 0);
        if (errNone != err)
            return err;
            
    }
/*    
    if (vfsVolumeMainMemory != vfsVolume)
    {
        err = CreateVolNameHyperlink(link, urlSchemaEBook urlSeparatorSchemaStr ebookUrlPartMove ":", vfsVolume, name, true, vfsVolumeMainMemory);
        if (errNone != err)
            return err;
            
        err = PopupMenuHyperlinkAppendItem(&out, "Move to main memory", link.GetCStr(), 0);
        if (errNone != err)
            return err;
    }
    
    for (ulong_t i = 0; i < volCount; ++i)
    {
        if (volRefs[i] == vfsVolume)
            continue;
            
        if (NULL == text.AssignCharP("Move to "))
            return memErrNotEnoughSpace;
            
        if (NULL == text.AppendCharP(volNames[i]))
            return memErrNotEnoughSpace;
            
        err = CreateVolNameHyperlink(link, urlSchemaEBook urlSeparatorSchemaStr ebookUrlPartMove ":", vfsVolume, name, true, volRefs[i]);
        if (errNone != err)
            return err;
            
        err = PopupMenuHyperlinkAppendItem(&out, text.GetCStr(), link.GetCStr(), 0);
        if (errNone != err)
            return err;
            
    }
 */    

    err = CreateVolNameHyperlink(link, urlSchemaEBook urlSeparatorSchemaStr ebookUrlPartDelete ":", vfsVolume, name, false, 0);
    if (errNone != err)
        return err;
        
    err = PopupMenuHyperlinkAppendItem(&out, "Delete", link.GetCStr(), 0);
    if (errNone != err)
        return err;
        
    link.Truncate(0);
    if (NULL == link.AppendCharP(urlSchemaAmazonSearch urlSeparatorSchemaStr "Books;;1;"))
        return memErrNotEnoughSpace;
    if (NULL == link.AppendCharPBuf(title, titleLen))
        return memErrNotEnoughSpace;
    err = PopupMenuHyperlinkAppendItem(&out, "Search in Amazon", link.GetCStr(), 0);
    if (errNone != err)
        return err;
    
    return errNone;
}

static Err CreateAuthorPopupMenuHyperlink(CDynStr& out, const char_t* author, ulong_t authorLen)
{
    Err err;
    CDynStr link;
    CDynStr text;
    
    err = PopupMenuHyperlinkCreate(&out, urlSchemaMenu urlSeparatorSchemaStr, 2);
    if (errNone != err)
        return err;
        
    if (NULL == text.AppendCharP("Find all books by "))
        return memErrNotEnoughSpace;
    if (NULL == text.AppendCharPBuf(author, authorLen))
        return memErrNotEnoughSpace;
        
    if (NULL == link.AppendCharP("eBook: search: author: "))    
        return memErrNotEnoughSpace;
    if (NULL == link.AppendCharPBuf(author, authorLen))
        return memErrNotEnoughSpace;
        
    err = PopupMenuHyperlinkAppendItem(&out, text.GetCStr(), link.GetCStr(), 0);
    if (errNone != err)
        return err;
            
    link.Truncate(0);
    if (NULL == link.AppendCharP(urlSchemaAmazonSearch urlSeparatorSchemaStr "Books;;1;"))
        return memErrNotEnoughSpace;
    if (NULL == link.AppendCharPBuf(author, authorLen))
        return memErrNotEnoughSpace;
    err = PopupMenuHyperlinkAppendItem(&out, "Search in Amazon", link.GetCStr(), 0);
    if (errNone != err)
        return err;

    return errNone;
}



static Err CreateEBookListEntry(DefinitionModel::Elements_t& elems, UInt16 vfsVolume, const char_t* path, const char_t* info, EBookFormat format, char** volNames, UInt16* volRefs, ulong_t volCount, EBookFormats formats)
{
    const char_t* author;
    const char_t* title;
    ulong_t nameLen, authorLen, titleLen;
    eBook_ParseDatabaseInfo(info, nameLen, author, authorLen, title, titleLen);

    CDynStr link;
    CDynStr authLink;
    Err err = CreateEBookPopupMenuHyperlink(link, vfsVolume, path, title, titleLen, format, volNames, volRefs, volCount, formats);
    if (errNone != err)
        return err;
    
    err = CreateAuthorPopupMenuHyperlink(authLink, author, authorLen);
    if (errNone != err)
        return err;
    
    BulletElement* b = new BulletElement();
    elems.push_back(b);
    
    if (vfsVolumeMainMemory != vfsVolume)
    {
        elems.push_back(new TextElement("\x1a "));
        elems.back()->setParent(b);
    }        
    elems.push_back(new TextElement(String(title, titleLen)));
    elems.back()->setParent(b);
    elems.back()->setStyle(StyleGetStaticStyle(styleNameBold));
    elems.back()->setHyperlink(String(link.GetCStr(), link.Len()), hyperlinkUrl);
    
    elems.push_back(new TextElement(" by "));
    elems.back()->setParent(b);
    elems.push_back(new TextElement(String(author, authorLen)));
    elems.back()->setParent(b);
    elems.back()->setHyperlink(String(authLink.GetCStr(), authLink.Len()), hyperlinkUrl);

    return errNone;
}

static Err ListMainMemoryEBooks(DefinitionModel::Elements_t& elems, const EBookPreferences& prefs, char** volNames, UInt16* volRefs, ulong_t volCount, EBookFormats formats)
{
    UInt16 count = DmNumDatabases(0);
    Err err = errNone;
    char* name = (char*)malloc(32);
    if (NULL == name)
        return memErrNotEnoughSpace;
    for (UInt16 i = 0; i < count; ++i)
    {
        LocalID id = DmGetDatabase(0, i);
        UInt32 type, creator;
        EBookFormat format;
        if (0 == id)
            goto Cleanup;
                    
        err = DmDatabaseInfo(0, id, name, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, &type, &creator);
        if (errNone != err)
        {
            err = errNone;
            continue;
        }
        format = eBook_DetectBookFormat(creator, type);
        if (ebookFormat_Unknown == format)
            continue;
            
        long i = StrArrFindPrefix(prefs.managedEBooks, prefs.managedEBooksSize, ';', name);
        if (-1 == i)
            continue;

        const char_t* info = prefs.managedEBooks[i];
        err = CreateEBookListEntry(elems, vfsVolumeMainMemory, name, info, format, volNames, volRefs, volCount, formats);
        if (errNone != err)
            goto Cleanup;
    }
Cleanup:
    free(name);
    return err;
}

static Err ListVFS_Volumes(char_t**& names, UInt16*& refs, ulong_t& count)
{
    count = 0;
    names = NULL;
    refs = NULL;
    
    Err err = errNone;
    UInt16 ref;
    UInt32 iterator = vfsIteratorStart;
    CDynStr str;
    char* label = (char*)malloc(256);
    if (NULL == label)
    {
        err = memErrNotEnoughSpace;
        goto Finish;
    }
    
    refs = (UInt16*)malloc(sizeof(UInt16) * 8);
    if (NULL == refs)
    {
        err = memErrNotEnoughSpace;
        goto Finish;
    }
    
    while (vfsIteratorStop != iterator)
    {
        err = VFSVolumeEnumerate(&ref, &iterator);
        if (errNone != err)
        {
            if (expErrEnumerationEmpty == err)
            {
                err = errNone;
                break;
            }
            else
                goto Finish;
                
        }
        refs[count++] = ref;
    }
    names = StrArrCreate(count);
    if (NULL == names)
    {
        count = 0;
        err = memErrNotEnoughSpace;
        goto Finish;
    }
    for (ulong_t i = 0; i < count; ++i)
    {
        err = VFSVolumeGetLabel(refs[i], label, 256);
        if (errNone != err)
            goto Finish;
        
        if ('\0' == *label)
            StrPrintF(label, "[Volume %ld]", i + 1);
        
        if (NULL == str.AppendCharP2("\x1a ", label))
        {
            err = memErrNotEnoughSpace;
            goto Finish;
        }
        
        
        
        names[i] = str.ReleaseStr();
    }
    
Finish:
    if (errNone != err)
    {
        if (NULL != refs)
        {
            free(refs);
            refs = NULL;
        }
        StrArrFree(names, count);
    }
    
    if (NULL != label)
        free(label);
        
    return err;  
}

static Err ListVFS_VolumeEBooks(DefinitionModel::Elements_t& elems, const EBookPreferences& prefs, UInt16 volume, char** volNames, UInt16* volRefs, ulong_t volCount, EBookFormats formats)
{   
    FileRef ref;
    Err err = VFSFileOpen(volume, eBook_DOWNLOAD_PATH, vfsModeRead, &ref);
    if (errNone != err)
        return errNone;

    FileInfoType fileInfo;
    UInt32 iterator = vfsIteratorStart;
    fileInfo.nameBufLen = 256;
    fileInfo.nameP = (char*)malloc(256);
    if (NULL == fileInfo.nameP)
        return memErrNotEnoughSpace;
        
    CDynStr str;
    
    while (vfsIteratorStop != iterator)
    {
        EBookFormat format;
        long len;
        const char* name;
        fileInfo.nameP[0] = chrNull;
        err = VFSDirEntryEnumerate(ref, &iterator, &fileInfo);
        if (errNone != err)
        {
            if (expErrEnumerationEmpty == err)
                err = errNone;
            goto Cleanup;
        }
        
        str.Truncate(0);
        if (NULL == str.AppendCharP2(eBook_DOWNLOAD_PATH "/", fileInfo.nameP))
        {
            err = memErrNotEnoughSpace;
            goto Cleanup;
        }
        
        err = eBook_DetectDatabaseFormat(volume, str.GetCStr(), format);
        if (errNone != err)
            continue;
         
        if (ebookFormat_Unknown == format)
            continue;
            
        name = fileInfo.nameP;
        len = tstrlen(name);
        if (len < 4)
            continue;
        len -= 4;
        
        long i = StrArrFindPrefix(prefs.managedEBooks, prefs.managedEBooksSize, ';', name, len);
        if (-1 == i)
            continue;
        
        const char_t* info = prefs.managedEBooks[i];
        err = CreateEBookListEntry(elems, volume, str.GetCStr(), info, format, volNames, volRefs, volCount, formats);
        if (errNone != err)
            goto Cleanup;
    }
Cleanup:    
    if (0 != ref)
        VFSFileClose(ref);
    free(fileInfo.nameP);
    return err;
}

static Err ListVFS_EBooks(DefinitionModel::Elements_t& elems, const EBookPreferences& prefs, char** volNames, UInt16* volRefs, ulong_t volCount, EBookFormats formats)
{
    for (ulong_t i = 0; i < volCount; ++i)
    {
        Err err = ListVFS_VolumeEBooks(elems, prefs, volRefs[i], volNames, volRefs, volCount, formats);
//        if (errNone != err)
//            return err;
                    
    }
    return errNone;
}

static Err ListAvailableEBooks(DefinitionModel::Elements_t& elems)
{
    EBookFormats formats = eBook_DetectAvailableFormats();
    EBookPreferences& prefs = MoriartyApplication::instance().preferences().ebookPrefs;
    char** names = NULL;
    UInt16* refs = NULL;
    ulong_t count = 0;
    Err err;
    bool vfs = VFS_FeaturesPresent();
    
    if (vfs)
    {
        err = ListVFS_Volumes(names, refs, count);
        if (errNone != err)
            return err;
    }
    
    err = ListMainMemoryEBooks(elems, prefs, names, refs, count, formats);
    if (errNone != err)
        goto Finish;
        
    if (vfs)
        err = ListVFS_EBooks(elems, prefs, names, refs, count, formats);

Finish:
    if (NULL != refs)
        free(refs);
    StrArrFree(names, count);
    return err;
}

void EBookMainForm::prepareDownloadedEBooks()
{
    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }

    DefinitionModel::Elements_t& elems = model->elements;

    elems.push_back(new TextElement("Home"));
    elems.back()->setHyperlink(urlSchemaEBookHome urlSeparatorSchemaStr, hyperlinkUrl);
    elems.push_back(new TextElement(" / Manage downloaded eBooks"));
    
    elems.push_back(new LineBreakElement());
    
    
    uint_t cnt = elems.size();
    if (memErrNotEnoughSpace == ListAvailableEBooks(elems))
        goto NoMemory;
        
    if (elems.size() == cnt)
    {
        elems.push_back(new LineBreakElement());
        elems.push_back(new TextElement("No downloaded eBooks were found on this device."));
    }
    
    infoRenderer_.setModel(model, Definition::ownModel);
    return;

NoMemory:
    delete model;
    application().alert(notEnoughMemoryAlert);   
}

void EBookMainForm::refreshDownloadedEBooks()
{
    if (showDownloadedEBooks != displayMode_)
    {
        setDisplayMode(showDownloadedEBooks);
        update();
    }
    else
    {
        prepareDownloadedEBooks();
        update();
    }
}
