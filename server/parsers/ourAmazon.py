import os, sys, getopt, cgi, urllib, string
from xml.dom import minidom
try:
    import timeoutsocket # http://www.timo-tasi.org/python/timeoutsocket.py
    timeoutsocket.setDefaultSocketTimeout(10)
except ImportError:
    pass

import arsutils

from ResultType import *
from parserUtils import *
from Retrieve import getHttp
from definitionBuilder import *
from popupMenu import *
import ebooks

ARSLEXIS_LICENSE_KEY = "0BQBVJXTZGZT1Y49GQR2"

LICENSE_KEY = None
ASSOCIATE = "webservices-20"
HTTP_PROXY = None
LOCALE = "us"

# don't touch the rest of these constants
class AmazonError(Exception): pass
class NoLicenseKey(Exception): pass
_amazonfile1 = ".amazonkey"
_amazonfile2 = "amazonkey.txt"
_licenseLocations = (
    (lambda key: key, 'passed to the function in license_key variable'),
    (lambda key: LICENSE_KEY, 'module-level LICENSE_KEY variable (call setLicense to set it)'),
    (lambda key: os.environ.get('AMAZON_LICENSE_KEY', None), 'an environment variable called AMAZON_LICENSE_KEY'),
    (lambda key: _contentsOf(os.getcwd(), _amazonfile1), '%s in the current directory' % _amazonfile1),
    (lambda key: _contentsOf(os.getcwd(), _amazonfile2), '%s in the current directory' % _amazonfile2),
    (lambda key: _contentsOf(os.environ.get('HOME', ''), _amazonfile1), '%s in your home directory' % _amazonfile1),
    (lambda key: _contentsOf(os.environ.get('HOME', ''), _amazonfile2), '%s in your home directory' % _amazonfile2),
    (lambda key: _contentsOf(_getScriptDir(), _amazonfile1), '%s in the amazon.py directory' % _amazonfile1),
    (lambda key: _contentsOf(_getScriptDir(), _amazonfile2), '%s in the amazon.py directory' % _amazonfile2)
    )
_supportedLocales = {
        "us" : (None, "xml.amazon.com"),
        "uk" : ("uk", "xml-eu.amazon.com"),
        "de" : ("de", "xml-eu.amazon.com"),
        "jp" : ("jp", "xml.amazon.co.jp")
    }

## administrative functions
def version():
    print """PyAmazon %(__version__)s
%(__copyright__)s
released %(__date__)s
""" % globals()

def setAssociate(associate):
    global ASSOCIATE
    ASSOCIATE=associate

def getAssociate(override=None):
    return override or ASSOCIATE

## utility functions

def _checkLocaleSupported(locale):
    if not _supportedLocales.has_key(locale):
        raise AmazonError, ("Unsupported locale. Locale must be one of: %s" %
            string.join(_supportedLocales, ", "))

def setLocale(locale):
    """set locale"""
    global LOCALE
    _checkLocaleSupported(locale)
    LOCALE = locale

def getLocale(locale=None):
    """get locale"""
    return locale or LOCALE

def setLicense(license_key):
    """set license key"""
    global LICENSE_KEY
    LICENSE_KEY = license_key

def getLicense(license_key = None):
    """get license key

    license key can come from any number of locations;
    see module docs for search order"""
    for get, location in _licenseLocations:
        rc = get(license_key)
        if rc: return rc
    return ARSLEXIS_LICENSE_KEY
    ## never do it...
    raise NoLicenseKey, 'get a license key at http://www.amazon.com/webservices'

def setProxy(http_proxy):
    """set HTTP proxy"""
    global HTTP_PROXY
    HTTP_PROXY = http_proxy

def getProxy(http_proxy = None):
    """get HTTP proxy"""
    return http_proxy or HTTP_PROXY

def getProxies(http_proxy = None):
    http_proxy = getProxy(http_proxy)
    if http_proxy:
        proxies = {"http": http_proxy}
    else:
        proxies = None
    return proxies

def _contentsOf(dirname, filename):
    filename = os.path.join(dirname, filename)
    if not os.path.exists(filename): return None
    fsock = open(filename)
    contents =  fsock.read().strip()
    fsock.close()
    return contents

def _getScriptDir():
    if __name__ == '__main__':
        return os.path.abspath(os.path.dirname(sys.argv[0]))
    else:
        return os.path.abspath(os.path.dirname(sys.modules[__name__].__file__))

class Bag: pass

def unmarshal(element):
    rc = Bag()
    if isinstance(element, minidom.Element) and (element.tagName == 'Details'):
        rc.URL = element.attributes["url"].value
    childElements = []
    for e in element.childNodes:
        if isinstance(e, minidom.Element):
            childElements.append(e)
    if childElements:
        for child in childElements:
            key = child.tagName
            if hasattr(rc, key):
                if type(getattr(rc, key)) <> type([]):
                    setattr(rc, key, [getattr(rc, key)])
                setattr(rc, key, getattr(rc, key) + [unmarshal(child)])
            elif isinstance(child, minidom.Element) and (child.tagName == 'Details'):
                # make the first Details element a key
                setattr(rc,key,[unmarshal(child)])
                #dbg: because otherwise 'hasattr' only tests
                #dbg: on the second occurence: if there's a
                #dbg: single return to a query, it's not a
                #dbg: list. This module should always
                #dbg: return a list of Details objects.
            else:
                setattr(rc, key, unmarshal(child))
    else:
        rc = "".join([e.data for e in element.childNodes if isinstance(e, minidom.Text)])
        if element.tagName == 'SalesRank':
            rc = rc.replace('.', '')
            rc = rc.replace(',', '')
            rc = int(rc)
    return rc

## our functions:
def buildURLToGetItem(asin,reviewPage, license_key):
    url = "http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&SubscriptionId=%s" % license_key.strip()
    url += "&Operation=ItemLookup&ItemId=%s" % asin
    url += "&ReviewPage=%s" % str(reviewPage)
    url += "&ResponseGroup=Large"
    return url

def buildURLToGetList(listType, listId, page, license_key):
    url = "http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&SubscriptionId=%s" % license_key.strip()
    url += "&Operation=ListLookup&ListType=%s" % listType
    url += "&ListId=%s" % listId
    url += "&ProductPage=%s" % page
    url += "&ResponseGroup=ItemAttributes,OfferSummary"
    return url

def buildURLToSearchNode(keyword, search_index, browse_node, page, license_key):
    url = "http://webservices.amazon.com/onca/xml?Service=AWSECommerceService"
    url += "&SubscriptionId=%s" % license_key.strip()
    url += "&Operation=ItemSearch&Keywords=%s" % urllib.quote(keyword)
    url += "&SearchIndex=%s" % search_index
    url += "&ItemPage=%s" % page
    #if search_index not in ("Blended","Apparel","HealthPersonalCare","SportingGoods","Jewelry","GourmetFood","DigitalMusic"):
    #    url += "&Sort=titlerank"
    if browse_node != "":
        url += "&BrowseNode=%s" % browse_node
    url += "&ResponseGroup=OfferSummary,ItemAttributes"
    # http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&SubscriptionId=0BQBVJXTZGZT1Y49GQR2&Operation=ItemSearch&Keywords=bb&SearchIndex=Blended&ItemPage=1&ResponseGroup=OfferSummary,ItemAttributes
    return url

def searchByKeywordInNode(keyword, search_index, browse_node, page, fDebug=False):
    license_key = getLicense(None)
    url = buildURLToSearchNode(keyword, search_index, browse_node, page, license_key)
    proxies = getProxies(None)
    u = urllib.FancyURLopener(proxies)
    usock = u.open(url)
    xmldoc = minidom.parse(usock)
    usock.close()
    if fDebug:
        print xmldoc.toprettyxml(" ")
    data = unmarshal(xmldoc).ItemSearchResponse
    if hasattr(data, 'Error'):
        raise AmazonError, data.Error
    else:
        totalResults = ""
        try:
            totalResults = data.Items.TotalResults.encode('latin_1')
        except:
            pass
        return makeListFrom(data.Items.Item), totalResults

def getAmazonList(listType, listId, page, fDebug=False):
    license_key = getLicense(None)
    url = buildURLToGetList(listType, listId, page, license_key)
    proxies = getProxies(None)
    u = urllib.FancyURLopener(proxies)
    usock = u.open(url)
    xmldoc = minidom.parse(usock)
    usock.close()
    if fDebug:
        print xmldoc.toprettyxml(" ")
    data = unmarshal(xmldoc).ListLookupResponse
    if hasattr(data, 'Error'):
        raise AmazonError, data.Error
    else:
        # http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&SubscriptionId=0BQBVJXTZGZT1Y49GQR2&Operation=ListLookup&ListType=Listmania&ListId=1WOW1VSS7JWSN&ResponseGroup=ItemAttributes,OfferSummary
        if not isinstance(data.Lists.List.ListItem, list):
            return [data.Lists.List.ListItem.Item]
        temp = []
        for listItem in data.Lists.List.ListItem:
            temp.append(listItem.Item)
        return temp

def buildURLToGetWishlist(name, email, city, state, page, license_key):
    url = "http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&SubscriptionId=%s" % license_key.strip()
    url += "&Operation=ListSearch&ResponseGroup=ListInfo&ListType=WishList"
    url += "&Name=%s" % urllib.quote(name)
    url += "&Email=%s" % urllib.quote(email)
    url += "&City=%s" % urllib.quote(city)
    url += "&State=%s" % urllib.quote(state)
    url += "&ListPage=%s" % str(page)
    return url

def getAmazonWishlist(name, email, city, state, page, fDebug=False):
    license_key = getLicense(None)
    url = buildURLToGetWishlist(name, email, city, state, page, license_key)
    # http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&SubscriptionId=0BQBVJXTZGZT1Y49GQR2&Operation=ListSearch&ResponseGroup=ListInfo&ListType=WishList&Name=krzysztof%20kowalczyk&Email=&City=&State=
    proxies = getProxies(None)
    u = urllib.FancyURLopener(proxies)
    usock = u.open(url)
    xmldoc = minidom.parse(usock)

    usock.close()
    data = unmarshal(xmldoc).ListSearchResponse

    if fDebug:
        print xmldoc.toprettyxml(" ")

    if hasattr(data, 'Error'):
        raise AmazonError, data.Error
    else:
        temp = makeListFrom(data.Lists.List)
        test = temp[-1].CustomerName
        totalPages = data.Lists.TotalPages.encode('latin_1')
        return temp, totalPages

def getAmazonItemByAsin(asin, reviewPage, fDebug=False):
    license_key = getLicense(None)
    url = buildURLToGetItem(asin, reviewPage, license_key)
    # print url
    # http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&SubscriptionId=0BQBVJXTZGZT1Y49GQR2&Operation=ItemLookup&ItemId=0679723420&ResponseGroup=Large
    proxies = getProxies(None)
    u = urllib.FancyURLopener(proxies)
    usock = u.open(url)
    xmldoc = minidom.parse(usock)

    usock.close()
    data = unmarshal(xmldoc).ItemLookupResponse
    if fDebug:
        print xmldoc.toprettyxml(" ")
    if hasattr(data, 'Error'):
        raise AmazonError, data.Error
    else:
        return data.Items.Item

g_dict = [ ## show, search_index, webpage
    ["Books", "Books", "books"],
    ["Music", "Music", "music"],
    ["DVD", "DVD", "dvd"],
    ["Video", "Video", "video"],
    ["VHS", "VHS", "vhs"],
    ["Video Games", "VideoGames", "videogames"],
    ["Photo", "Photo", "photo"],
    ["Electronics", "Electronics", "electronics"],
    ["Toys", "Toys", "toys"],
    ["Tools", "Tools", "tools"],
    ["Computers", "PCHardware", "computers"],
    ["Sports & Outdoors", "SportingGoods", "sportinggoods"],
    ["Software", "Software", "software"],
    ["Health & Personal Care", "HealthPersonalCare", "health"],
    ["Wireless", "Wireless", "wireless"],
    ["Office Products", "OfficeProducts", "office"],
    ["Baby", "Baby", "baby"],
    ["Outdoor Living", "OutdoorLiving", "outdoorliving"],
    ["Musical Instruments", "MusicalInstruments", "musicalinstruments"],
    ["Kitchen", "Kitchen", "kitchen"],
    ["Wireless Accessories", "WirelessAccessories", "wirelessaccessories"],
    ["Beauty", "Beauty", "beauty"],
    ["Apparel", "Apparel", "apparel"],
    ["Magazines", "Magazines", "magazines"],
    ["Jewelry", "Jewelry", "jewelry"],
    ["Gourmet Food", "GourmetFood", "gourmetfood"]]

def parseAmazonBrowseHtml(htmlTxt, historyUrl, indexInGDict=0, browse_node=None):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    liList = soup.fetch("li")
    resultsCount = 0
    outerList = []
    for liItem in liList:
        aItem = liItem.first("a",{"href":"/exec/obidos/tg/browse/-/%"})
        if aItem:
            url = aItem['href']
            urlSplitted = url.split("/-/")
            if 1 < len(urlSplitted):
                name = getAllTextFromTag(aItem).strip()
                if 1 < len(urlSplitted[1].split("/")):
                    node = urlSplitted[1].split("/")[0]
                else:
                    node = urlSplitted[1]
                if 0 < len(name):
                    resultsCount += 1
                    outerList.append((node, name))

    if 0 == resultsCount:
        for liItem in liList:
            aItem = liItem.first("a", {"href":"/exec/obidos%"})
            if aItem:
                url = aItem['href']
                urlSplitted = url.split("field-browse=")
                if 1 < len(urlSplitted):
                    name = getAllTextFromTag(aItem).strip()
                    if 1 < len(urlSplitted[1].split("&")):
                        node = urlSplitted[1].split("&")[0]
                    else:
                        node = urlSplitted[1]
                    if 0 < len(name):
                        resultsCount += 1
                        outerList.append((node, name))

    if 0 == resultsCount:
        return (NO_RESULTS, None)

    # get current category
    title = ""
    pageTitle = getAllTextFromTag(soup.first("title"))
    if None != pageTitle:
        pageTitle = pageTitle.split("Amazon.com")
        if len(pageTitle) > 1:
            title = pageTitle[1].strip()
            # TODO: remove print's
            print "--------"
            print title
            print "--------"
            title = title.split("/")[-1].strip()
            print title
            print "--------"

    # build Definition from outerList = (node, name)
    df = Definition()
    df.TextElement("Home", link='amazonform:main')
    df.TextElement(" / ")
    if None == browse_node:
        df.TextElement(g_dict[indexInGDict][0])
    else:
        df.TextElement(g_dict[indexInGDict][0], link='s+amazonbrowse:Blended;'+g_dict[indexInGDict][2]+';1')
        if title == "":
            df.TextElement(" / "+"...")
        else:
            df.TextElement(" / "+title)
    df.LineBreakElement(1,2)

    for item in outerList:
        df.BulletElement(False)
        gtxt = df.TextElement(item[1])
        gtxt.setHyperlink("s+amazonbrowse:"+g_dict[indexInGDict][1]+";"+item[0]+";1")
        df.PopParentElement()

    # build controls

    buttons = []
    buttons.append(["B","Done"])
    historyText = g_dict[indexInGDict][0]
    if None == browse_node:
        searchRequest = "s+amazonsearch:"+g_dict[indexInGDict][1]+";;1;"
        searchText = "Search "+g_dict[indexInGDict][0]+" for:"
    else:
        searchRequest = "s+amazonsearch:"+g_dict[indexInGDict][1]+";"+browse_node+";1;"
        searchText = "Search "+g_dict[indexInGDict][0]
        if title == "":
            searchText += " / ... for:"
            historyText += "/..."
        else:
            searchText += " / "+title+" for:"
            historyText += "/"+title
    buttons.append(["H",historyText,historyUrl])
    buttons.append(["B","Search",searchRequest,searchText])

    return (AMAZON_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def parseAmazonBrowseMainHtml(htmlTxt, historyUrl, indexInGDict = 0):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # find "Browse" text or gif or whatever...
    tdList = soup.fetch("td")
    browse = None
    for td in tdList:
        text = getAllTextFromTag(td).strip()
        if text == "Browse" or text == "BROWSE":
            browse = td
        img = td.first("img")
        if img:
            src = img['src']
            if 1 < len(src.split("browse.gif")):
                browse = td
            elif 1 < len(src.split("browse")):
                lastPart = src.split("/")[-1]
                if 1 < lastPart.split("browse"):
                    browse = td
    if not browse:
        return (UNKNOWN_FORMAT, None)
    # find table after browse
    tableList = soup.fetch("table")
    resultsCount = 0
    outerList = []
    index = 0
    table = None
    next = browse
    while next and table == None:
        if isinstance(next,Tag):
            if "table" == next.name:
                table = next
        next = next.next
    if not table:
        return (UNKNOWN_FORMAT, None)
    table2 = None
    for tbl in tableList:
        tdList = tbl.fetch("td")
        for td in tdList:
            if td == browse:
                table2 = tbl
                break
        if table2:
           break
    # get items
    for aItem in table.fetch("a",{"href":"/exec/obidos/tg/browse/-/%"}):
        url = aItem['href']
        urlSplitted = url.split("/-/")
        if 1 < len(urlSplitted):
            name = getAllTextFromTag(aItem).strip()
            if 1 < len(urlSplitted[1].split("/")):
                node = urlSplitted[1].split("/")[0]
            else:
                node = urlSplitted[1]
            if 0 < len(name):
                resultsCount += 1
                outerList.append((node, name))

    if 0 == resultsCount:
        aList = table.fetch("a")
        if table2:
             aList += table2.fetch("a")
        for aItem in aList:
            url = aItem['href']
            urlSplitted = url.split("&node=")
            if 1 < len(urlSplitted):
                name = getAllTextFromTag(aItem).strip()
                if 1 < len(urlSplitted[1].split("&")):
                    node = urlSplitted[1].split("&")[0]
                else:
                    node = urlSplitted[1]
                if 0 < len(name):
                    resultsCount += 1
                    outerList.append((node, name))
    if 0 == resultsCount:
        return (NO_RESULTS, None)

    # build Definition from outerList = (node, name)
    df = Definition()
    df.TextElement("Home", link='amazonform:main')
    df.TextElement(" / "+g_dict[indexInGDict][0])
    df.LineBreakElement(1,2)

    for item in outerList:
        df.BulletElement(False)
        gtxt = df.TextElement(item[1])
        gtxt.setHyperlink("s+amazonbrowse:"+g_dict[indexInGDict][1]+";"+item[0]+";1")
        df.PopParentElement()

    # build controls
    buttons = []
    buttons.append(["B","Done"])
    searchRequest = "s+amazonsearch:"+g_dict[indexInGDict][1]+";;1;"
    searchText = "Search "+g_dict[indexInGDict][0]+" for:"
    buttons.append(["B","Search",searchRequest,searchText])
    buttons.append(["H",g_dict[indexInGDict][0],historyUrl])

    return (AMAZON_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def joinFromListOrString(input, joiner=", "):
    if isinstance(input, list):
        encodedList = []
        for item in input:
            encodedList.append(item.encode('latin_1'))
        # 2 lines to remove duplicates
        #keys = {}.fromkeys(encodedList)
        #encodedList = keys.keys()
        ret = string.join(encodedList, joiner)
        return ret
    else:
        return input.encode('latin_1')

# remove all text between first and last '(' ')'
# "test (text)" -> "test"
def cleanupTitle(title):
    opening = title.find("(")
    ending = title.rfind(")")
    if opening != ending and opening != -1 and ending != -1:
        title = title[:opening] + title[ending+1:]
    return title.strip()

def getSearchListElement(bag): ##bag is <Item>
    asin = ""
    name = ""
    beforeAuthor = "by"
    author = [] #or producent, or artist, or manufacter...
    category = ""
    price = ""
    ## this 2 need to be
    asin = bag.ASIN.encode('latin_1')
    name = bag.ItemAttributes.Title.encode('latin_1')
    ## try and catch...
    try:
        price = bag.ItemAttributes.ListPrice.FormattedPrice.encode('latin_1')
    except:
        pass
    if "" == price:
        try:
            price = bag.OfferSummary.LowestNewPrice.FormattedPrice.encode('latin_1')
        except:
            pass
    try:
        category = bag.ItemAttributes.ProductGroup.encode('latin_1')
    except:
        pass
    try:
        author = makeListFrom(bag.ItemAttributes.Author)
        index = 0
        while index < len(author):
            author[index] = makeTitleCase(author[index])
            index+=1
    except:
        pass
    if [] == author:
        try:
            author = makeListFrom(bag.ItemAttributes.Artist)
            index = 0
            while index < len(author):
                author[index] = makeTitleCase(author[index])
                index+=1
        except:
            pass
    if [] == author:
        try:
            author = makeListFrom(bag.ItemAttributes.Actor)
            index = 0
            while index < len(author):
                author[index] = makeTitleCase(author[index])
                index+=1
            beforeAuthor = "with"
        except:
            pass
    if [] == author:
        try:
            author = makeListFrom(bag.ItemAttributes.Director)
            index = 0
            while index < len(author):
                author[index] = makeTitleCase(author[index])
                index+=1
        except:
            pass
    if [] == author:
        try:
            author = makeListFrom(bag.ItemAttributes.Publisher)
        except:
            pass
    if [] == author:
        try:
            author = makeListFrom(bag.ItemAttributes.Manufacturer)
        except:
            pass
    if [] == author:
        try:
            author = makeListFrom(bag.ItemAttributes.Brand)
        except:
            pass
    if [] == author:
        try:
            author = makeListFrom(bag.ItemAttributes.Studio)
        except:
            pass

    # finaly...
    return (asin, cleanupTitle(name), beforeAuthor, author, category, price)

## All cross modules popups here
def setCrossModulesLinksToAuthor(gtxt, author, search_index, modulesInfo, category):
    amazonHyperlink = "s+amazonsearch:%s;;1;%s" % (search_index,author)
    if None != modulesInfo:
        popupItems = []
        popupItems.append(["Search Amazon",amazonHyperlink,False,True,False])
        if modulesInfo['Lyrics'] and (search_index == "Music" or category == "Music"):
            popupItems.append(["Search Lyrics","s+lyricssearch:"+author+";;;;",False,False,False])
        if modulesInfo['ListsOfBests'] and (search_index in ["Books","Music","DVD","VHS","Video"] or category in ["Book","Music","DVD","VHS","Video"]):
            cat = "Movies"
            if search_index == "Books" or category == "Books":
                cat = "Books"
            elif "Music" in [category, search_index]:
                cat = "Music"
            popupItems.append(["Search Lists of Bests","s+listsofbestssearch:"+author+";"+cat+";Creator",False,False,False])
        if modulesInfo['Netflix'] and (search_index in ["DVD","VHS","Video"] or category in ["DVD","VHS","Video"]):
            popupItems.append(["Search Netflix","s+netflixsearch:"+author+";People;?",False,False,False])
        if modulesInfo['Encyclopedia']:
            popupItems.append(["Search Encyclopedia","s+pediasearch:"+author,False,False,False])
        if modulesInfo['eBooks'] and (search_index == "Books" or category == "Book"):
            link = ebooks.create_search_author_link(author)
            popupItems.append(['Search eBooks',link,False,False,False])
        if modulesInfo['eBay']:
            popupItems.append(['Search eBay',"s+ebay:search;0;?;"+author,False,False,False])

        if len(popupItems) > 1:
            gtxt.setHyperlink(buildPopupMenu(popupItems))
        else:
            gtxt.setHyperlink(amazonHyperlink)
    else:
        gtxt.setHyperlink(amazonHyperlink)

def setCrossModulesLinksToUnlinkedTitle(gtxt, title, search_index, modulesInfo, category):
    if None != modulesInfo:
        popupItems = []
        if modulesInfo['Lyrics'] and (search_index == "Music" or category == "Music"):
            # title is album title
            popupItems.append(["Search Lyrics","s+lyricssearch:;;"+title+";;",False,False,False])
        if modulesInfo['ListsOfBests'] and (search_index in ["Books","Music","DVD","VHS","Video"] or category in ["Book","Music","DVD","VHS","Video"]):
            cat = "Movies"
            if search_index == "Books" or category == "Books":
                cat = "Books"
            elif "Music" in [category, search_index]:
                cat = "Music"
            popupItems.append(["Search Lists of Bests","s+listsofbestssearch:"+title+";"+cat+";Title",False,False,False])
        if modulesInfo['Netflix'] and (search_index in ["DVD","VHS","Video"] or category in ["DVD","VHS","Video"]):
            popupItems.append(["Search Netflix","s+netflixsearch:"+title+";Movie;?",False,False,False])
        if modulesInfo['eBooks'] and (search_index == "Books" or category == "Book"):
            link = ebooks.create_search_title_link(title)
            popupItems.append(['Search eBooks',link,False,False,False])
        if modulesInfo['eBay']:
            popupItems.append(['Search eBay',"s+ebay:search;0;?;"+title,False,False,False])

        if len(popupItems) > 0:
            gtxt.setHyperlink(buildPopupMenu(popupItems))

def setCrossModulesLinksToTrack(gtxt, track, artist, modulesInfo):
    if None != modulesInfo:
        if modulesInfo['Lyrics']:
            gtxt.setHyperlink(buildPopupMenu([["Lyrics Search","cs+lyricssearch:"+artist+";"+track+";;;",False,False,False]]))

## end of cross modules popups
            
def retriveAmazonSearchByKeyword(keyword, search_index, browse_node, page, modulesInfo, fDebug=False, browse=False):
    historyUrl = "s+amazonsearch:%s;%s;%s;%s" % (search_index, browse_node, page, keyword)
    if browse:
        historyUrl = "s+amazonbrowse:%s;%s;%s" % (search_index, browse_node, page)
    try:
        indexInGDict = 0
        category = search_index.strip().lower()
        while indexInGDict < len(g_dict):
            if g_dict[indexInGDict][1].lower() == category:
                break
            indexInGDict += 1

        counter = 5
        while counter > 0:
           try:
               bags, totalResults = searchByKeywordInNode(keyword, search_index, browse_node, page, fDebug=fDebug)
               counter = -20
           except:
               counter -= 1
        if 0 == counter:
            bags, totalResults = searchByKeywordInNode(keyword, search_index, browse_node, page, fDebug=fDebug)
    except:
        ## TODO: make sure it is no results...
        return (NO_RESULTS, None)

    totalResultsTable = None
    # get all data from bags:
    outerList = []
    for bag in bags:
        try:
            innerList = getSearchListElement(bag)
            outerList.append(innerList)
        except:
            pass ## no title in results?
    if totalResults != "" and search_index != "Blended":
        total = int(totalResults)
        start = (int(page)-1)*10
        end = int(page)*10
        if end > total:
            end = total
        if end >= start:
            totalResultsTable = [start,end,total]

    # build Definition from outerList = (asin, name, author, category, price)
    historyText = ""
    df = Definition()
    df.TextElement("Home", link='amazonform:main')
    if "Blended" != search_index:
        df.TextElement(" / ")
        df.TextElement(g_dict[indexInGDict][0], link='s+amazonbrowse:Blended;'+g_dict[indexInGDict][2]+';1')
        historyText += g_dict[indexInGDict][0] + " "
    if keyword != "":
        df.TextElement(" / Search results for '"+keyword+"':")
        historyText += "Search for "+keyword
    df.LineBreakElement(1,2)

    for item in outerList:
        df.BulletElement(False)
        gtxt = df.TextElement(item[1])
        gtxt.setHyperlink("s+amazonitem:"+item[0])
        gtxt.setStyle('bold')
        if item[3] != []:
            df.TextElement(" "+item[2]+" ")
            first = True
            for it in item[3]:
                if not first:
                    df.TextElement(", ")
                else:
                    first = False
                gtxt = df.TextElement(it)
                setCrossModulesLinksToAuthor(gtxt, it, search_index, modulesInfo, item[4])
        if item[4] != "" and search_index == "Blended":
            df.TextElement(" ("+item[4]+")")
        gtxt = df.TextElement(item[5], style='bold')
        gtxt.setJustification(justRightLast)
        df.PopParentElement()

    # build controls
    buttons = []
    buttons.append(["B","Done"])
    prevPageLink = ""
    if int(page) > 1:
        prevPageLink = "s+amazonsearch:%s;%s;%s;%s" % (search_index, browse_node, str(int(page)-1), keyword)

    buttons.append(["B", "Prev", prevPageLink])

    if None != totalResultsTable:

        nextPageLink = ""
        if totalResultsTable[1] != totalResultsTable[2]:
            nextPageLink = "s+amazonsearch:%s;%s;%s;%s" % (search_index, browse_node, str(int(page)+1), keyword)

        buttons.append(["B","Info",str(totalResultsTable[0])+"-"+str(totalResultsTable[1])+"/"+str(totalResultsTable[2])])

        buttons.append(["B", "Next", nextPageLink])

        # add google like links at the bottom of page:
        currPage = int(page)
        totalPages = totalResultsTable[2]/10
        if totalResultsTable[2] % 10 != 0:
            totalPages += 1
        startRange = max(1,currPage-4)
        endRange = min(totalPages, startRange+8)

        # dont show "Page: 1" when only one page is available
        if startRange != endRange:
            df.LineBreakElement(1,2)
            par = df.ParagraphElement(False)
            par.setJustification(justCenter)
            df.TextElement("Page: ")

            counter = startRange
            while counter <= endRange:
                if counter != startRange:
                    df.TextElement(" ")
                gtxt = df.TextElement(str(counter))
                if counter != currPage:
                    gtxt.setHyperlink("s+amazonsearch:"+search_index+";"+browse_node+";"+str(counter)+";"+keyword)
                else:
                    gtxt.setStyle('bold')
                counter+=1
            df.PopParentElement()

        # do "[prev page] - [next page]"
        if startRange != endRange:
            par = df.ParagraphElement(False)
            par.setJustification(justCenter)
            if "" == prevPageLink:
                df.TextElement("prev page")
            else:
                df.TextElement("prev page", link=prevPageLink)
            df.TextElement(" \x95 ", style='gray')
            if "" == nextPageLink:
                df.TextElement("next page")
            else:
                df.TextElement("next page", link=nextPageLink)
            df.PopParentElement()

        # end of google like bottom
    else:
        nextPageLink = "s+amazonsearch:"+search_index+";"+browse_node+";"+str(int(page)+1)+";"+keyword
        # add just "[prev page] - [next page]"
        buttons.append(["B","Next",nextPageLink])
        df.LineBreakElement(1,2)
        par = df.ParagraphElement(False)
        par.setJustification(justCenter)
        if "" == prevPageLink:
            df.TextElement("prev page")
        else:
            df.TextElement("prev page", link=prevPageLink)
        df.TextElement(" \x95 ", style='gray')
        if "" == nextPageLink:
            df.TextElement("next page")
        else:
            df.TextElement("next page", link=nextPageLink)
        df.PopParentElement()
    buttons.append(["B","Search"])
    if len(historyText) > 30:
        historyText = historyText[:30]+"..."
    buttons.append(["H",historyText+" ("+str(page)+")" ,historyUrl])
    return (AMAZON_SEARCH_LIST, universalDataFormatWithDefinition(df, buttons))

def retriveAmazonList(listString, page, modulesInfo, fDebug=False):
    historyUrl = "s+amazonlist:%s;%s" % (listString, page)
    listId = listString[1:]
    listType = listString[0]
    if "L" == listType:
        listType = "Listmania"
        historyText = "Listmania"
    if "W" == listType:
        listType = "WishList"
        historyText = "Wishlist"
    historyText += " (" + page +")"
    try:
        counter = 10
        while counter > 0:
           try:
               bags = getAmazonList(listType, listId, page, fDebug=fDebug)
               counter = -20
           except:
               counter -= 1
        if 0 == counter:
            bags = getAmazonList(listType, listId, page, fDebug=fDebug)
    except:
        ## TODO: make sure it is no results...
        return (NO_RESULTS, None)

    # get all data from bags:
    outerList = []
    for bag in bags:
        try:
            innerList = getSearchListElement(bag)
            outerList.append(innerList)
        except:
            pass ## no title in results?

    # build Definition from outerList = (asin, name, author, category, price)
    df = Definition()
    df.TextElement("Home", link='amazonform:main')
    df.TextElement(" / ")
#    df.TextElement("Back", link='amazonform:up')
    if "L" == listString[0]:
        df.TextElement("Listmania")
    else:
        df.TextElement("Wishlist")
    df.LineBreakElement(1,2)

    for item in outerList:
        df.BulletElement(False)
        gtxt = df.TextElement(item[1])
        gtxt.setHyperlink("s+amazonitem:"+item[0])
        gtxt.setStyle('bold')
        if item[3] != []:
            df.TextElement(" "+item[2]+" ")
            first = True
            for it in item[3]:
                if not first:
                    df.TextElement(", ")
                else:
                    first = False
                gtxt = df.TextElement(it)
                setCrossModulesLinksToAuthor(gtxt, it, getSearchIndexByProductGroup(item[4]), modulesInfo, item[4])
        if item[4] != "":
            df.TextElement(" ("+item[4]+")")
        gtxt = df.TextElement(item[5], style='bold')
        gtxt.setJustification(justRightLast)
        df.PopParentElement()

    prevQuery = ""
    if int(page) > 1:
        prevQuery = "s+amazonlist:"+listString+";"+str(int(page)-1)
    nextQuery = "s+amazonlist:"+listString+";"+str(int(page)+1)
    # add just "[prev page] - [next page]"
    df.LineBreakElement(1,2)
    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    if "" == prevQuery:
        df.TextElement("prev page")
    else:
        df.TextElement("prev page", link=prevQuery)
    df.TextElement(" \x95 ", style='gray')
    if "" == nextQuery:
        df.TextElement("next page")
    else:
        df.TextElement("next page", link=nextQuery)
    df.PopParentElement()

    # butons
    buttons = []
    buttons.append(["B","Done"])
    buttons.append(["B","Prev",prevQuery])
    buttons.append(["B","Next",nextQuery])
    buttons.append(["B","Search"])
    buttons.append(["H",historyText,historyUrl])
    return (AMAZON_SEARCH_LIST, universalDataFormatWithDefinition(df, buttons))

def retriveAmazonWishlist(name, email, city, state, page, fDebug=False):
    try:
        counter = 10
        while counter > 0:
            try:
                bags, totalPages = getAmazonWishlist(name, email, city, state, page, fDebug=fDebug)
                counter = -20
            except:
                counter -= 1
        if 0 == counter:
            bags, totalPages = getAmazonWishlist(name, email, city, state, page, fDebug=fDebug)
    except:
        ## TODO: make sure it is no results...
        return (NO_RESULTS, None)

    # get all data from bags:
    # http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&SubscriptionId=0BQBVJXTZGZT1Y49GQR2&Operation=ListSearch&ResponseGroup=ListInfo&ListType=WishList&Name=kowalczyk&City=&State=DC&Email=krzysztofk
    outerList = []
    for bag in bags:
        listId = bag.ListId.encode('latin_1')
        listType = bag.ListType.encode('latin_1')
        totalItems = bag.TotalItems.encode('latin_1')
        dateCreated = bag.DateCreated.encode('latin_1')
        customerName = makeTitleCase(bag.CustomerName.encode('latin_1'))
        innerList = ["s+amazonlist:W" + listId+";1", customerName, totalItems, dateCreated]
        outerList.append(innerList)

    # build Definition from outerList = (listid, name, totalitems, datecreated)
    df = Definition()
    df.TextElement("Home", link='amazonform:main')
    df.TextElement(" / ")
    text = [name, email, city, state]
    textSearch = ""
    for t in text:
        if t != "":
            if textSearch != "":
                textSearch += ", "
            textSearch += t
    df.TextElement("Wishlist search for: "+ textSearch)
    df.LineBreakElement(1,2)

    for item in outerList:
        df.BulletElement(False)
        gtxt = df.TextElement(item[1])
        gtxt.setHyperlink(item[0])
        gtxt.setStyle('bold')
        df.TextElement(" ("+item[2]+") Wishlist created: "+item[3])
        df.PopParentElement()
    # total pages:
    total = int(totalPages)
    curPage = int(page)
    prevQuery = ""
    nextQuery = ""
    if curPage < total:
        nextQuery = "s+amazonwishlist:"+name+";"+email+";"+city+";"+state+";"+str(curPage+1)
    if curPage > 1:
        prevQuery = "s+amazonwishlist:"+name+";"+email+";"+city+";"+state+";"+str(curPage-1)

    # add just "[prev page] - [next page]"
    df.LineBreakElement(1,2)
    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    if "" == prevQuery:
        df.TextElement("prev page")
    else:
        df.TextElement("prev page", link=prevQuery)
    df.TextElement(" \x95 ", style='gray')
    if "" == nextQuery:
        df.TextElement("next page")
    else:
        df.TextElement("next page", link=nextQuery)
    df.PopParentElement()

    # butons
    buttons = []
    buttons.append(["B","Info","Page: "+str(curPage)+"/"+str(totalPages)])
    buttons.append(["B","Done"])
    buttons.append(["B","Prev",prevQuery])
    buttons.append(["B","Next",nextQuery])
    buttons.append(["B","Search"])
    buttons.append(["H","Wishlists: "+ textSearch[:38]+ " ("+str(curPage)+")","s+amazonwishlist:"+name+";"+email+";"+city+";"+state+";"+str(curPage)])
    return (RESULTS_DATA, universalDataFormatWithDefinition(df, buttons))

def putSpacesBetweenWords(text):
    i = 1
    while i < len(text):
        if text[i].isupper():
            text = text[:i] + " " + text[i:]
            i += 1
        i += 1
    return text

def getSearchIndexByProductGroup(productGroup):
    dictionary = {
        'Book':'Books',
        'Music':'Music',
        'DVD':'DVD',
        'VHS':'VHS',
        'Video':'Video',
        'Photography':'Photo',
        'Video Games':'VideoGames',
        'CE':'Electronics',
        'Toy':'Toys',
        'Baby Product':'Baby',
        'Home Improvement':'Tools',
        'Apparel':'Apparel',
        'Software':'Software',
        'Health and Beauty':'HealthPersonalCare',
        'Wireless':'Wireless',
        'Office Product':'OfficeProducts',
        'Kitchen':'Kitchen',
        'Musical Instruments':'MusicalInstruments',
        'Wireless Phone Accessory':'WirelessAccessories',
        'Beauty':'Beauty',
        'Magazine':'Magazines',
        'Gourmet':'GourmetFood',
        'Watch':'Jewelry',

        ## what is this?
        'Lawn & Patio':'Blended'
        }
        ## TODO:?
        ###MusicTracks, OutdoorLiving, DigitalMusic, PCHardware, SportingGoods, Classical, Restaurants, Miscellaneous, Merchants

    if dictionary.has_key(productGroup):
        return dictionary[productGroup]

    if None != productGroup:
        print "unknown productGroup: %s" % productGroup

    return "Blended"

def makeListFrom(input):
    if isinstance(input, list):
        encodedList = []
        for item in input:
            if isinstance(item, (str, unicode)):
                encodedList.append(item.encode('latin_1'))
            else:
                encodedList.append(item)
        return encodedList
    else:
        if isinstance(input, (str, unicode)):
            return [input.encode('latin_1')]
        else:
            return [input]

# given xmldom instance representing Amazon webservice item result
# return /ItemAttributes/Title in latin_1 encoding or None if it doesn't
# exists
def getItemTitle(item):
    title = None
    try:
        title = item.ItemAttributes.Title.encode('latin_1')
    except:
        pass
    return title

# given xmldom instance representing Amazon webservice item result
# return /ItemAttributes/ListPrice/FormattedPrice in latin_1 encoding
# or None if it doesn't exists
def getItemListPrice(item):
    listPrice = None
    try:
        listPrice = item.ItemAttributes.ListPrice.FormattedPrice.encode('latin_1')
    except:
        pass
    return listPrice

# given xmldom instance representing Amazon webservice item result
# return /ItemAttributes/ProductGroup in latin_1 encoding
# or None if it doesn't exists
def getItemProductGroup(item):
    productGroup = None
    try:
        productGroup = item.ItemAttributes.ProductGroup.encode('latin_1')
    except:
        pass
    return productGroup

# given xmldom instance representing Amazon webservice item result
# return a list of /ItemAttributes/ItemAttributes/Artist in latin_1 encoding
# or empty list if it doesn't exists
def getItemArtistList(item):
    artistList = []
    try:
        artistList = makeListFrom(item.ItemAttributes.Artist)
    except:
        pass
    for i in range(0,len(artistList)):
        artistList[i] = makeTitleCase(artistList[i])
    return artistList

# given xmldom instance representing Amazon webservice item result
# return a list of /ItemAttributes/ItemAttributes/Author in latin_1 encoding
# or empty list if it doesn't exists
def getItemAuthorList(item):
    authorList = []
    try:
        authorList = makeListFrom(item.ItemAttributes.Author)
    except:
        pass
    # TODO: cleanup author name so that "VLADIMIR NABOKOV" gets changed
    # to "Vladimir Nabokov"
    for i in range(0,len(authorList)):
        authorList[i] = makeTitleCase(authorList[i])
    return authorList

def retriveAmazonItemByAsin(asin, modulesInfo, fDebug=False):
    historyUrl = "s+amazonitem:"+asin
    parts = asin.split(";")
    reviewPage = 1
    if 2 == len(parts):
        asin = parts[0]
        reviewPage = int(parts[1])

    counter = 10
    while counter > 0:
       try:
           item = getAmazonItemByAsin(asin, reviewPage, fDebug=fDebug)
           counter = -20
       except:
           counter -= 1
    if 0 == counter:
        item = getAmazonItemByAsin(asin, reviewPage, fDebug=fDebug)

    df = Definition()
    df.TextElement("Home", link='amazonform:main')
    #df.TextElement("Back", link='amazonform:up')
    df.TextElement(" / ")

    # title - should always exist!
    title = getItemTitle(item)
    if title == None:
        return UNKNOWN_FORMAT, None
    title = cleanupTitle(title)
    gtxt = df.TextElement(title,style='bold')

    historyText = title
    if len(title) > 40:
        historyText = title[:40]+"..."
    if reviewPage > 1:
        historyText += " (" + str(reviewPage)+")"

    productGroup = getItemProductGroup(item)
    searchIndex = getSearchIndexByProductGroup(productGroup)

    setCrossModulesLinksToUnlinkedTitle(gtxt, title, searchIndex, modulesInfo, productGroup)

    artistList = getItemArtistList(item)
    authorList = getItemAuthorList(item)

    artistOrAuthorList = artistList
    if 0 == len(artistOrAuthorList):
        artistOrAuthorList = authorList
    else:
        # we don't expect to get a list of both author and artist
        assert 0 == len(authorList)

    if len(artistOrAuthorList) > 0:
        df.TextElement(" by ")
        first = True
        for artistOrAuthor in artistOrAuthorList:
            if first:
                first = False
            else:
                df.TextElement(", ")
            gtxt = df.TextElement(artistOrAuthor)
            setCrossModulesLinksToAuthor(gtxt, artistOrAuthor, searchIndex, modulesInfo, productGroup)

    df.LineBreakElement()

    # prices:
    listPrice = getItemListPrice(item)
    amazonPrice = None

    try:
        valuePrice = -1
        price = None
        for offer in makeListFrom(item.Offers.Offer):
            value = int(offer.OfferListing.Price.Amount.encode('latin_1'))
            if valuePrice == -1 or valuePrice > value:
                valuePrice = value
                price = offer.OfferListing.Price.FormattedPrice.encode('latin_1')
        if price != None:
            amazonPrice = price
    except:
        pass

    if None != amazonPrice:
        df.LineBreakElement(1,2)
        txt = "Amazon price: %s" % amazonPrice
        if None != listPrice and amazonPrice != listPrice:
            txt = "%s, list price: %s" % (txt, listPrice)

            listPrice = float(listPrice[1:].replace(",",""))
            amazonPrice = float(amazonPrice[1:].replace(",",""))
            saving = listPrice - amazonPrice
            if saving > 0:
                savingPercent = (saving * 100.0) / listPrice
                txt = "%s, you save: $%.2f (%.0f%%)" % (txt, saving, savingPercent)
        df.TextElement(txt)
        df.LineBreakElement(1,2)
    elif None != listPrice:
        df.LineBreakElement(1,2)
        df.TextElement("List price: %s" % listPrice)
        df.LineBreakElement(1,2)
    else:
        # we have no price at all. Can we get the price from somewhere else?
        pass

##        try:
##            price = item.OfferSummary.LowestNewPrice.FormattedPrice.encode('latin_1')
##            outerList.append((amazonLeftRight, "Lowest new price", price))
##        except:
##            pass
##        try:
##            price = item.OfferSummary.LowestUsedPrice.FormattedPrice.encode('latin_1')
##            outerList.append((amazonLeftRight, "Lowest used price", price))
##        except:
##            pass
##        try:
##            price = item.OfferSummary.LowestCollectiblePrice.FormattedPrice.encode('latin_1')
##            outerList.append((amazonLeftRight, "Lowest collectible price", price))
##        except:
##            pass

##        # model
##        try:
##            model = joinFromListOrString(item.ItemAttributes.Model, " ")
##            outerList.append((amazonLeftRight,"Model",model))
##        except:
##            pass

    # actors/ authors/ ... and more form ItemAttributes

    # actor
    try:
        data = item.ItemAttributes.Actor
        text = "Actor(s): "
        data2 = makeListFrom(data)
        df.LineBreakElement()
        df.TextElement(text, style='bold')
        first = True
        for dt in data2:
            if not first:
                df.TextElement(", ")
            gtxt = df.TextElement(dt)
            setCrossModulesLinksToAuthor(gtxt, dt, searchIndex, modulesInfo, productGroup)
            first = False
        df.LineBreakElement(1,2)
    except:
        pass

    # director
    try:
        data = item.ItemAttributes.Director
        text = "Director: "
        data2 = makeListFrom(data)
        df.LineBreakElement()
        df.TextElement(text, style='bold')
        first = True
        for dt in data2:
            if not first:
                df.TextElement(", ")
            gtxt = df.TextElement(dt)
            setCrossModulesLinksToAuthor(gtxt, dt, searchIndex, modulesInfo, productGroup)
            first = False
        df.LineBreakElement(1,2)
    except:
        pass
##        # Publisher
##        try:
##            data = item.ItemAttributes.Publisher
##            text = "Publisher: "
##            data2 = makeListFrom(data)
##            df.LineBreakElement()
##            df.TextElement(text, style='bold')
##            first = True
##            for dt in data2:
##                if not first:
##                    df.TextElement(", ")
##                df.TextElement(dt, link="s+amazonsearch:"+searchIndex+";;1;"+dt)
##                first = False
##            df.LineBreakElement(1,2)
##        except:
##            pass
    # Manufacturer
    try:
        data = item.ItemAttributes.Manufacturer
        text = "Manufacturer: "
        data2 = makeListFrom(data)
        df.LineBreakElement()
        df.TextElement(text, style='bold')
        first = True
        for dt in data2:
            if not first:
                df.TextElement(", ")
            df.TextElement(dt, link="s+amazonsearch:"+searchIndex+";;1;"+dt)
            first = False
        df.LineBreakElement(1,2)
    except:
        pass
##        # Studio
##        try:
##            data = item.ItemAttributes.Studio
##            text = "Studio: "
##            data2 = makeListFrom(data)
##            df.LineBreakElement()
##            df.TextElement(text, style='bold')
##            first = True
##            for dt in data2:
##                if not first:
##                    df.TextElement(", ")
##                df.TextElement(dt, link="s+amazonsearch:"+searchIndex+";;1;"+dt)
##                first = False
##            df.LineBreakElement(1,2)
##        except:
##            pass

    # features
    try:
        df2 = Definition()
        for feature in makeListFrom(item.ItemAttributes.Feature):
            text = feature.encode('latin_1')
            df2.BulletElement(False)
            df2.TextElement(text)
            df2.PopParentElement()
        df.LineBreakElement()
        df.TextElement("Features",style='bold',link='simpleform:Features;'+df2.serialize())
        df.LineBreakElement(1,2)
    except:
        pass

    # tracks on disks... (linked to lyrics if lyrics module available)
    try:
        discs = makeListFrom(item.Tracks.Disc)
        artistToSearch = ""
        if None != artistOrAuthorList:
            if [] != artistOrAuthorList:
                artistToSearch = string.join(artistOrAuthorList,",")
        print artistToSearch
        if len(discs) > 1:
            index = 1
            for disc in discs:
                df2 = Definition()
                for track in makeListFrom(disc.Track):
                    text = track.encode('latin_1')
                    df2.BulletElement(False)
                    gtxt = df2.TextElement(text)
                    setCrossModulesLinksToTrack(gtxt, text, artistToSearch, modulesInfo)
                    df2.PopParentElement()
                df.LineBreakElement(1,2)
                df.TextElement("Tracks on disc " + str(index),style='bold',link='simpleform:Tracks;'+df2.serialize())
                df.LineBreakElement()
                index += 1
        else:
            df2 = Definition()
            for track in makeListFrom(discs[0].Track):
                text = track.encode('latin_1')
                df2.BulletElement(False)
                gtxt = df2.TextElement(text)
                setCrossModulesLinksToTrack(gtxt, text, artistToSearch, modulesInfo)
                df2.PopParentElement()
            df.LineBreakElement()
            df.TextElement("Tracks on disc",style='bold',link='simpleform:Tracks;'+df2.serialize())
            df.LineBreakElement(1,2)
    except:
        pass

    editorialReviewText = None
    # editorial review
    try:
        df2 = Definition()
        smallList = []
        reviewList = makeListFrom(item.EditorialReviews)
        for reviews in reviewList:
            for review in makeListFrom(reviews.EditorialReview):
                try:
                    source = review.Source.encode('latin_1').strip()
                    smallList.append([source])
                except:
                    pass
                content = review.Content.encode('latin_1')
                content = getTextFromDirtyText(content)
                if 1 < len(content.split("\n")):
                    for contentItem in content.split("\n"):
                        smallList.append(contentItem)
                else:
                    smallList.append(content)
        wasFirst = False
        for text in smallList:
            if wasFirst:
                df2.LineBreakElement()
            if isinstance(text,list):
                if wasFirst:
                    df2.LineBreakElement()
                df2.TextElement(text[0], style='bold')
            else:
                if "" != text:
                    df2.TextElement(text)
            wasFirst = True
        editorialReviewText = df2.serialize()
    except:
        pass

    # reviews
    try:
        agraveRating = item.CustomerReviews.AverageRating.encode('latin_1')
        moreReviews = int(item.CustomerReviews.TotalReviews.encode('latin_1'))
        moreReviewsText = None
        if moreReviews > 5 * reviewPage:
            if moreReviews == 5 * reviewPage+1:
                # THINK: Krzysztof do you like it? or you want to have 11-11/11 ?
                moreReviewsText = "Last review ("+str(moreReviews)+")"
            else:
                moreReviewsText = "More reviews ("+str(5 * reviewPage + 1)+"-"+str(min(5 * (reviewPage+1),moreReviews))+"/"+str(moreReviews)+")"
            moreReviews = "s+amazonitem:"+asin+";"+str(reviewPage+1)
        else:
            moreReviews = None
        tempList = []
        for review in makeListFrom(item.CustomerReviews.Review):
            rating = review.Rating.encode('latin_1')
            summary = review.Summary.encode('latin_1')
            content = review.Content.encode('latin_1')
            smallList = [summary,rating]
            content = getTextFromDirtyText(content)
            if isinstance(content.split("\n"),list):
                for con in content.split("\n"):
                    smallList.append(con)
            else:
                smallList.append(content)
            tempList.append(smallList)
        if len(tempList) > 0:
            df.LineBreakElement()
            df.TextElement("Reviews:",style='bold')
            df.TextElement(" (average rating is "+agraveRating+")")
            if editorialReviewText != None:
                df.BulletElement(False)
                df.TextElement("Editorial review",style='bold',link='simpleform:Editorial review;'+editorialReviewText)
                df.PopParentElement()
                editorialReviewText = None
        for tempItem in tempList:
            df2 = Definition()
            wasFirst = False
            for con in tempItem[2:]:
                if wasFirst:
                    df2.LineBreakElement()
                else:
                    wasFirst = True
                if "" != con:
                    df2.TextElement(con)
            df.BulletElement(False)
            df.TextElement(tempItem[1]+' - ')
            df.TextElement(tempItem[0],link='simpleform:Review;'+df2.serialize())
            df.PopParentElement()
        if moreReviews != None:
            df.BulletElement(False)
            df.TextElement(moreReviewsText,link=moreReviews)
            df.PopParentElement()
        df.LineBreakElement(1,2)
    except:
        pass

    if editorialReviewText != None:
        df.LineBreakElement()
        df.TextElement("Editorial review",style='bold',link='simpleform:Editorial review;'+editorialReviewText)
        df.LineBreakElement(1,2)

    # similar items
    try:
        tempList = []
        for product in makeListFrom(item.SimilarProducts.SimilarProduct):
            asin = product.ASIN.encode('latin_1')
            title = product.Title.encode('latin_1')
            tempList.append((cleanupTitle(title),asin))

        if len(tempList) > 0:
            df.LineBreakElement()
            df.TextElement("Similar products:", style='bold')
        for tempItem in tempList:
            df.BulletElement(False)
            df.TextElement(tempItem[0], link="s+amazonitem:"+tempItem[1])
            df.PopParentElement()
        if len(tempList) > 0:
            df.LineBreakElement(1,2)
    except:
        pass
    # listmania...
    try:
        tempList = []
        for product in makeListFrom(item.ListmaniaLists.ListmaniaList):
            asin = product.ListId.encode('latin_1')
            title = product.ListName.encode('latin_1')
            tempList.append((title,asin))

        if len(tempList) > 0:
            df.LineBreakElement()
            df.TextElement("Listmania lists:", style='bold')
        for tempItem in tempList:
            df.BulletElement(False)
            df.TextElement(tempItem[0], link="s+amazonlist:L"+tempItem[1]+";1")
            df.PopParentElement()
        if len(tempList) > 0:
            df.LineBreakElement(1,2)
    except:
        pass

    # build controls
    buttons = []
    buttons.append(["B","Done"])
    buttons.append(["B","Search"])
    buttons.append(["H",historyText,historyUrl])
    return (AMAZON_ITEM, universalDataFormatWithDefinition(df, buttons))

def retriveAmazonBrowseNode(search_index, browse_node, page, modulesInfo):
    historyUrl = "s+amazonbrowse:%s;%s;%s" % (search_index, browse_node, page)
    if "Blended" == search_index and not browse_node.isdigit():
        # in browse_node name of category
        i = 0
        category = browse_node.strip().lower()
        while i < len(g_dict):
            if g_dict[i][2].lower() == category:
                break
            i += 1
        if i == len(g_dict):
            return (NO_RESULTS, None)
        url = "http://www.amazon.com/%s" % category
        htmlTxt = getHttp(url, referer="http://www.amazon.com/")
        if None == htmlTxt:
            return (NO_RESULTS, None)
        resultType2, resultBody2 = parseAmazonBrowseHtml(htmlTxt,historyUrl, i)
        resultType3, resultBody3 = parseAmazonBrowseMainHtml(htmlTxt,historyUrl, i)
        if AMAZON_BROWSE_LIST == resultType3:
            return (resultType3, resultBody3)
        if AMAZON_BROWSE_LIST == resultType2:
            return (resultType2, resultBody2)
        return (resultType3, resultBody3)
    else:
        i = 0
        category = search_index.strip().lower()
        while i < len(g_dict):
            if g_dict[i][1].lower() == category:
                break
            i += 1
        if i == len(g_dict):
            return (NO_RESULTS, None)

        # just like search
        resultType, resultBody = retriveAmazonSearchByKeyword("", search_index, browse_node, page, modulesInfo, fDebug=False, browse=True)
        # parse html...
        url = "http://www.amazon.com/exec/obidos/tg/browse/-/%s" % browse_node.strip()
        htmlTxt = getHttp(url, referer="http://www.amazon.com/")
        if None == htmlTxt:
            htmlTxt = ""
        resultType2, resultBody2 = parseAmazonBrowseHtml(htmlTxt,historyUrl,i,browse_node)
        resultType3, resultBody3 = parseAmazonBrowseMainHtml(htmlTxt,historyUrl,i)

        if AMAZON_BROWSE_LIST == resultType2:
            return (resultType2, resultBody2)
        if AMAZON_BROWSE_LIST == resultType3:
            return (resultType3, resultBody3)
        if AMAZON_SEARCH_LIST == resultType:
            return (resultType, resultBody)
        return (resultType2, resultBody2)

def mainOld():
    dict = [
#    ["Toys", "Toys", "Toys"],
    ["Health & Personal Care", "HealthPersonalCare", "health"],
#    ["Baby", "Baby", "Baby"],
    ["Musical Instruments", "MusicalInstruments", "MusicalInstruments"],
#    ["Wireless Accessories", "WirelessAccessories", "WirelessAccessories"],
    ["Beauty", "Beauty", "Beauty"],
#    ["Magazines", "Magazines", "Magazines"],
    ["Jewelry", "Jewelry", "Jewelry"],
    ]

    for item in g_dict:
        type, body = retriveAmazonBrowseNode("Blended", item[2], "1", None)
        if type == AMAZON_BROWSE_LIST:
            print "ok for:" + item[0]
        elif type == AMAZON_SEARCH_LIST:
            print "search list only! for:" + item[0]
        else:
            print "fatal error for:" + item[0]

def usage():
    print "usage: ourAmazon.py searchTerm (e.g. 's+amazonitem:B0000065JZ')"

# Test cases for amazon module
# s+amazonitem:B0000065JZ
#  Music, Morcheba, "Big Calm"
# s+amazonitem:B00000JSBR
#  Music, Pearl Jam, Beck, Mcartney, Setzer, "Vol. 3-Mom"
# s+amazonitem:0679723161
#  Books, Nabokov, "Lolita"
# s+amazonsearch:Books;;2;nabokov
#  search in books for nabokov, second page
# s+amazonlist:L1IE0G11DKDT1B;1
#  some amazon listmania list
def main():
    if 2 != len(sys.argv):
        usage()
        sys.exit(0)

    (schema, fieldValue) = sys.argv[1].split(":",1)
    if -1 != schema.find("amazonitem"):
        (resultType, resultBody) = retriveAmazonItemByAsin(fieldValue, None, fDebug=True)

    elif -1 != schema.find("amazonsearch"):
        parts = fieldValue.split(";")
        if len(parts) < 4:
            print "%s must be 4 ';'-separated values" % fieldValue
            sys.exit(0)
        if len(parts) > 4:
            parts[3] = string.join(parts[3:],";")
        (search_index,browse_node,page,keyword) = parts[:4]

        resultType, resultBody = retriveAmazonSearchByKeyword(keyword, search_index, browse_node, page, None, fDebug=True)

    elif -1 != schema.find("amazonlist"):
        parts = fieldValue.split(";")
        if 2 != len(parts):
            print "%s must be 2 ';'-separated values" % fieldValue
            sys.exit(0)
        resultType, resultBody = retriveAmazonList(parts[0],parts[1], None, fDebug=True)

    elif -1 != schema.find("amazonwishlist"):
        parts = fieldValue.split(";")
        if 5 != len(parts):
            print "%s must be 5 ';'-separated values" % fieldValue
            sys.exit(0)

        resultType, resultBody = retriveAmazonWishlist(parts[0],parts[1],parts[2],parts[3], parts[4], fDebug=True)

    else:
        # TODO: add the rest of possible v-urls
        print "query %s not handled yet" % sys.argv[1]
        sys.exit(0)

    resultTypeTxt = resultTypeName(resultType)
    if None == resultTypeTxt:
        print "unknown result type %d" % resultType
    else:
        print "resultType: %s" % resultTypeTxt

#getUrlAmazonBrowse = getUrl + "-amazonbrowse"
#getUrlAmazonList = getUrl + "-amazonlist"

if __name__ == "__main__":
    main()
