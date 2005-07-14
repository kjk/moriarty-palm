#include <SysUtils.hpp>
#include "PediaArticleHandler.hpp"
#include "MoriartyApplication.hpp"
#include "LookupManager.hpp"
#include "PediaCacheDataRead.hpp"
#include "PediaMainForm.hpp"
#include "History.hpp"

status_t PediaCacheDataRead(const char_t* title, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;

    CDynStr str;
    PediaArticleHandler* parser = new_nt PediaArticleHandler();
    if (NULL == parser)
        return memErrNotEnoughSpace;
        
    const PediaPreferences& prefs = app.preferences().pediaPrefs;
    parser->defaultLanguage = prefs.languageCode;
    
    status_t err = FeedHandlerFromReader(*parser, reader);
    if (errNone != err)
    {
        delete parser;    
        return err;
    }

    PediaMainForm* form = static_cast<PediaMainForm*>(app.getOpenForm(pediaMainForm));
    if (NULL != form)
        form->invalidateRenderers();
    
    std::swap(parser->article, lm->lastPediaArticle);
    std::swap(parser->linkedArticles, lm->lastPediaLinkedArticles);
    std::swap(parser->linkingArticles, lm->lastPediaLinkingArticles);
    
    delete parser;
    
    lm->setLastPediaArticleTitle(StringCopy2(title));
    if (NULL == lm->lastPediaArticleTitle)
        return memErrNotEnoughSpace;
    
    LookupFinishedEventData data(lookupResultPediaArticle);
    sendEvent(LookupManager::lookupFinishedEvent, data);
    return errNone;
}

status_t PediaSearchDataRead(const char_t* title, Reader& reader)
{
    MoriartyApplication& app = MoriartyApplication::instance();
    LookupManager* lm = app.lookupManager;
    DefinitionModel* model;
    status_t err = ReadByteFormatFromReader(reader, model);
    if (errNone != err)
        return err;
        
    PediaMainForm* form = static_cast<PediaMainForm*>(app.getOpenForm(pediaMainForm));
    if (NULL != form)
        form->invalidateRenderers();

    PassOwnership(model, lm->lastPediaSearchResults);    
    
    assert(StrStartsWith(title, _T("Search for '")));
    ulong_t len = tstrlen(_T("Search for '"));
    title += len;
    len = tstrlen(title) - 1;
    
    lm->setLastPediaArticleTitle(StringCopy2N(title, len));
    if (NULL == lm->lastPediaArticleTitle)
        return memErrNotEnoughSpace;
    
    LookupFinishedEventData data(lookupResultPediaSearch);
    sendEvent(LookupManager::lookupFinishedEvent, data);
    return errNone;
}
