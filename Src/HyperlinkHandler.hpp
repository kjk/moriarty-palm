#ifndef HYPERLINK_HANDLER_HPP__
#define HYPERLINK_HANDLER_HPP__

#include <Definition.hpp>

#define urlSchemaHttp                         _T("http")
#define urlSchemaDream                        _T("dream")
#define urlSchemaMovie                        _T("movie")
#define urlSchemaTheatre                      _T("theatre")
#define urlSchemaLyricsForm                   _T("lyricsform")
#define urlSchemaMenu                         _T("menu")
#define urlSchemaRunModule                    _T("runmodule")

#define urlSchemaAmazonPreferences            _T("amazonpreferences")
#define urlSchemaAmazonForm                   _T("amazonform")
#define urlSchemaAmazonSearch               _T("s+amazonsearch")

#define urlSchemaSimpleFormWithDefinition     _T("simpleform")
#define urlSchemaNetflixForm                  _T("netflixform")
#define urlSchemaListsOfBestsForm             _T("listsofbestsform")

#define urlSchemaEncyclopediaTerm             _T("s+pediaterm")
#define urlSchemaEncyclopediaRandom           _T("s+pediarandom")
#define urlSchemaEncyclopediaSearch           _T("s+pediasearch")
#define urlSchemaEncyclopediaLangs            _T("s+pedialangs")
#define urlSchemaEncyclopediaStats            _T("s+pediastats")

#define urlSchemaEncyclopedia                 _T("pedia")

#define urlSchemaDict                         _T("dict")
#define urlSchemaDictTerm                     _T("s+dictterm")
#define urlSchemaDictRandom                   _T("s+dictrandom")
#define urlSchemaDictForm                     _T("dictform")
#define urlSchemaDictStats                    _T("s+dictstats")

#define urlSchemaEBookSearch            _T("s+eBook-search")
#define urlSchemaEBookDownload          _T("s+eBook-download")
#define urlSchemaEBookBrowse            _T("s+eBook-browse")
#define urlSchemaEBookHome              _T("s+eBook-home")
#define urlSchemaEBook                      _T("eBook")

#define urlSchemaEBayForm                     _T("ebayform")

#define urlSchemaClipboardCopy                _T("clipbrdcopy")

#define urlSeparatorSchema                    _T(':')
#define urlSeparatorFlags                     _T('+')
#define urlSeparatorSchemaStr                 _T(":")
#define urlSeparatorFlagsStr                  _T("+")

#define urlFlagServer                         _T('s')
#define urlFlagClosePopup                   _T('c')
#define urlFlagHistory                        _T('h')
#define urlFlagHistoryInCache                 _T('H')

#define pediaUrlPartSetLang                   _T("lang")
#define pediaUrlPartHome                      _T("home")
#define pediaUrlPartSearchDialog              _T("search")
#define pediaUrlPartShowArticle               _T("article")

#define ebookUrlPartSearch _T("search")
#define ebookUrlPartMove _T("move")
#define ebookUrlPartDelete _T("delete")
#define ebookUrlPartCopy _T("copy")
#define ebookUrlPartLaunch _T("launch")
#define ebookUrlPartManage _T("manage")
#define ebookUrlPartBrowse _T("browse")
#define ebookUrlPartDownload _T("download")

#define urlSchemaFlickr         _T("flickr")

#define flickrUrlPartAbout      _T("about")

const ArsLexis::char_t* hyperlinkData(const char_t* hyperlink, ulong_t& length);

class HyperlinkHandler: public HyperlinkHandlerBase
{
public:

    typedef void (HyperlinkHandler::* HandlerFunction)(const char_t* hyperlink, ulong_t len, const Point*);

private:

    static HandlerFunction findHandler(const char_t* schema, ulong_t len);
    
    static void closePopup(uint_t id);

    static void closePopup();
        
    enum HandlerFlag {
        flagServerHyperlink = 1,
        flagClosePopupForm = 2,
        flagHistory = 4,
        flagHistoryInCache = 8
    };
    
    static uint_t interpretFlag(ArsLexis::char_t flag);
    
    void handleRunModule(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleHttp(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleDream(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleMovie(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleTheatre(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleLyricsForm(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleDictForm(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleMenu(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleAmazonForm(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleAmazonPreferences(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleSimpleFormWithDefinition(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleClipboardCopy(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleListsOfBestsForm(const char_t* hyperlink, ulong_t len, const Point* point);
    void handleEBayForm(const char_t* hyperlink, ulong_t len, const Point* point);
    
    void handlePedia(const char_t* hyperlink, ulong_t len, const Point* point);
    
    void handlePediaHome(const char_t* hyperlink, ulong_t len, const Point* point);
    void handlePediaLang(const char_t* hyperlink, ulong_t len, const Point* point);
    void handlePediaSearch(const char_t* hyperlink, ulong_t len, const Point* point);
    void handlePediaArticle(const char_t* hyperlink, ulong_t len, const Point* point);
    
    void handleEBook(const char_t* hyperlink, ulong_t len, const Point* point);
    
    void handleEBookDownload(const char_t* data, ulong_t len);

    void handleNetflixForm(const char_t* hyperlink, ulong_t len, const Point* point);
    
    void handleFlickr(const  char_t* hyperlink, ulong_t len, const Point* point);

public:

    void handleHyperlink(const char_t* hyperlink, ulong_t len, const Point* point);
    
    virtual ~HyperlinkHandler();
    
};

ArsLexis::String buildUrl(const ArsLexis::char_t* schema, const ArsLexis::char_t* data);

#endif // HYPERLINK_HANDLER_HPP__
