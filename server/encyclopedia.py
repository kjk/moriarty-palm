
from definitionBuilder import *
import re
from entities import convertEntities23

_g_langNames = {
    "ab": "Abkhazian",
    "aa": "Afar",
    "af": "Afrikaans",
    "ak": "Akan",
    "als": "Alemannic",
    "am": "Amharic",
    "ang": "Anglo-Saxon (Old English)",
    "ar": "Arabic",
    "an": "Aragonese",
    "arc": "Aramaic",
    "hy": "Armenian",
    "roa-rup": "Aromanian",
    "as": "Assamese",
    "ast": "Asturian",
    "av": "Avar",
    "ay": "Aymara",
    "az": "Azeri",
    "bm": "Bambara",
    "ba": "Bashkir",
    "eu": "Basque",
    "be": "Belarusian",
    "bn": "Bengali",
    "bh": "Bhojpuri",
    "bi": "Bislama",
    "bs": "Bosnian",
    "br": "Breton",
    "bg": "Bulgarian",
    "my": "Burmese",
    "ca": "Catalan",
    "ch": "Chamorro",
    "ce": "Chechen",
    "chr": "Cherokee",
    "chy": "Cheyenne",
    "ny": "Chichewa",
    "zh": "Chinese",
    "cho": "Choctaw",
    "cv": "Chuvash",
    "kw": "Cornish",
    "co": "Corsican",
    "cr": "Cree",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "dv": "Dhivehi",
    "nl": "Dutch",
    "dz": "Dzongkha",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "ee": "Ewe",
    "fo": "Faeroese",
    "fj": "Fijian",
    "fi": "Finnish",
    "fr": "French",
    "fy": "Frisian",
    "fur": "Friulian",
    "ff": "Fulfulde",
    "gl": "Galician",
    "ka": "Georgian",
    "de": "German",
    "got": "Gothic",
    "el": "Greek",
    "kl": "Greenlandic",
    "gn": "Guarani",
    "gu": "Gujarati",
    "ht": "Haitian",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "he": "Hebrew",
    "hz": "Herero",
    "hi": "Hindi",
    "ho": "Hiri",
    "hu": "Hungarian",
    "is": "Icelandic",
    "io": "Ido",
    "ig": "Igbo",
    "id": "Indonesian",
    "ia": "Interlingua",
    "ie": "Interlingue",
    "iu": "Inuktitut",
    "ik": "Inupiaq",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "jv": "Javanese",
    "kn": "Kannada",
    "kr": "Kanuri",
    "csb": "Kashubian",
    "ks": "Kashmiri",
    "kk": "Kazakh",
    "km": "Khmer",
    "ki": "Kikuyu",
    "rw": "Kinyarwanda",
    "rn": "Kirundi",
    "tlh": "Klingon",
    "kv": "Komi",
    "kg": "Kongo",
    "ko": "Korean",
    "ku": "Kurdish",
    "ky": "Kyrgyz",
    "lo": "Lao",
    "la": "Latin",
    "li": "Limburgish",
    "ln": "Lingala",
    "lt": "Lithuanian",
    "nds": "Low Saxon",
    "lg": "Luganda",
    "lb": "Luxembourgish",
    "mk": "Macedonian",
    "mg": "Malagasy",
    "ms": "Malay",
    "ml": "Malayalam",
    "mt": "Maltese",
    "gv": "Manx",
    "mi": "Maori",
    "mh": "Marshallese",
    "zh-min-nan": "Min Nan",
    "mo": "Moldovan",
    "mn": "Mongolian",
    "mus": "Muscogee",
    "nah": "Nahuatl",
    "na": "Nauruan",
    "nv": "Navajo",
    "ne": "Nepali",
    "no": "Norwegian",
    "nn": "Nynorsk",
    "oc": "Occitan",
    "or": "Oriya",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese",
    "pa": "Punjabi",
    "ps": "Pushtu",
    "qu": "Quechua",
    "ro": "Romanian",
    "rm": "Romansh",
    "ru": "Russian",
    "sm": "Samoan",
    "sg": "Sango",
    "sa": "Sanskrit",
    "sc": "Sardinian",
    "gd": "Scottish Gaelic",
    "sr": "Serbian",
    "sh": "Serbo-Croatian",
    "st": "Sesotho",
    "tn": "Setswana",
    "scn": "Sicilian",
    "simple": "Simple English",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "st": "Sotho",
    "es": "Spanish",
    "su": "Sundanese",
    "sw": "Swahili",
    "ss": "Swati",
    "sv": "Swedish",
    "tl": "Tagalog",
    "ty": "Tahitian",
    "tg": "Tajik",
    "ta": "Tamil",
    "tt": "Tatar",
    "te": "Telugu",
    "th": "Thai",
    "bo": "Tibetan",
    "ti": "Tigrignan",
    "tpi": "Tok Pisin",
    "tum": "Tumbuka",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "ug": "Uyghur",
    "uz": "Uzbek",
    "ve": "Venda",
    "vi": "Vietnamese",
    "vo": "Volapuk",
    "wa": "Walloon",
    "cy": "Welsh",
    "wo": "Wolof",
    "ii": "Yi",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "za": "Zhuang",
    "zu": "Zulu"
}

def languageName(code):
    return _g_langNames.get(code, None)

def _appendBullet(df, title, target):
    df.BulletElement(False)
    df.TextElement(title, close = True, link = target)
    df.PopParentElement()

def _appendPediaLink(df, title, res):
    df.LineBreakElement()
    url = "pedia:" + res
    txtEl = df.TextElement(title, close = True, link = url)
    txtEl.setJustification(justCenter);

def _prepareByteCode(linked, links, title):
    df = Definition()

    if 0 == len(links):
        if linked:
            df.TextElement("There are no articles linked by '" + title + "'.", True)
        else:
            df.TextElement("There are no articles linking to '" + title + "'.", True)
        df.LineBreakElement(1, 10)
        _appendPediaLink(df, "Back", "article")
        df.LineBreakElement(1, 10)
        return df.serialize()

    if linked:
        df.TextElement("Articles linked by '" + title + "':", True)
    else:
        df.TextElement("Articles linking to '" + title + "':", True)

    for title, target in links:
        _appendBullet(df, title, target)

    df.LineBreakElement(1, 10)
    _appendPediaLink(df, "Back", "article")
    df.LineBreakElement(1, 10)
    return df.serialize()

def _transformTitle(title, currLangCode):
    code = currLangCode
    url = None
    pos = title.find(":")
    langName = None
    if -1 != pos:
        code = title[:pos]
        langName = languageName(code)
        if langName is None:
            code = currLangCode
            url = code + ":" + title.replace("_", " ")
        else:
            url = title.replace("_", " ")
            title = title[pos + 1:]
    else:
        url = code + ":" + title.replace("_", " ")

    url = "s+pediaterm:" + url

    if code != currLangCode:
        title += (" ("+ langName + ")")

    title = title.replace("_", " ")

    return (title, url)

def _transformTitles(titles, currLangCode):
    titles = sorted(set(titles))
    t = [_transformTitle(title, currLangCode) for title in titles]
    return t

_g_term_link_re = re.compile(r"\[\[(.+?)\]\]", re.S)
_g_http_link_re = re.compile(r"\[(http:.+?)\]", re.S + re.I)

def extractLinkedArticles(article, code):
    links = {}

    term_links = _g_term_link_re.findall(article)
    for link in term_links:
        ll = link.split("|")
        caption, target = _transformTitle(convertEntities23(ll[0]), code)
        links[caption] = target

    http_links = _g_http_link_re.findall(article)
    for link in http_links:
        ll = link.split(None, 1)
        target = ll[0]
        caption = ll[0]
        if 1 != len(ll):
            caption = ll[1]
        caption = convertEntities23(caption)

        links[caption] = target

    links = links.items()
    pred = lambda x, y: cmp(x[0], y[0])
    links.sort(pred)
    return links

def linkedArticlesByteCode(linkedArticles, langCode, title):
    return _prepareByteCode(True, linkedArticles, title)

def linkingArticlesByteCode(linkingArticles, langCode, title):
    links = []
    if linkingArticles is not None:
        titles = linkingArticles.split()
        links = _transformTitles(titles, langCode)
    pred = lambda x, y: cmp(x[0], y[0])
    links.sort(pred)

    return _prepareByteCode(False, links, title)

def searchResultsByteCode(terms, langCode, title, offset):
    df = Definition()
    assert 0 != len(terms)
    last = offset + len(terms)
    lastTxt = "(%d - %d)" % (offset + 1, last)

    df.TextElement("Extended search results for '" + title + "' " + lastTxt+ ":", True)
    for term in terms:
        url = "s+pediaterm:" + langCode + ":" + term
        _appendBullet(df, term, url)

    df.LineBreakElement(1, 1)

    fShowPrev = False
    if offset != 0:
        fShowPrev = True

    fShowNext = False
    if 100 == len(terms):
        fShowNext = True

    # do "[prev page] - [next page]"
    if fShowPrev or fShowNext:
        prevPageLink = "s+pediasearch:" + langCode + ":" + title + ";" + str(offset - 100)
        nextPageLink = "s+pediasearch:" + langCode + ":" + title + ";" + str(last)

        par = df.ParagraphElement(False)
        par.setJustification(justCenter)
        if fShowPrev:
            df.TextElement("prev page", link=prevPageLink)
        else:
            df.TextElement("prev page")
        df.TextElement(" \x95 ", style='gray')
        if fShowNext:
            df.TextElement("next page", link=nextPageLink)
        else:
            df.TextElement("next page")
        df.PopParentElement()

    return df.serialize()

def create_search_link(term, lang_code = None):
    link = None
    if lang_code is None:
        link = "s+pediasearch:en:%s" % term
    else:
        link = "s+pediasearch:%s:%s" % (lang_code, term)
    return link


def languagesByteCode(langs):
    langs = langs.split()
    df = Definition()
    df.TextElement("Available languages:", True)
    for lang in langs:
        url = "pedia:lang:" + lang
        name = languageName(lang)
        assert name is not None
        _appendBullet(df, name, url)

    df.LineBreakElement(1, 10)
    _appendPediaLink(df, "Home", "home")
    df.LineBreakElement(1, 10)
    return df.serialize()

def preparePayload(article, linkingArticles, langCode, title):
    linkedArticles = linkedArticlesByteCode(extractLinkedArticles(article, langCode), langCode, title)
    linkingArticles = linkingArticlesByteCode(linkingArticles, langCode, title)
    parts = [longtob(len(article)), longtob(len(linkedArticles)), longtob(len(linkingArticles)), article, linkedArticles, linkingArticles]
    return "".join(parts);
