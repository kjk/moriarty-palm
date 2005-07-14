# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk
#
# Purpose:
#  parses html data from listsofbests.com
#
import string
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise

from parserUtils import *
from ResultType import *
from Retrieve import *
from definitionBuilder import *
from popupMenu import *
from parserErrorLogger import logParsingFailure
import ebooks

## this is used to give info about category
g_catTable = {
    "Books":"B",
    "Music":"M",
    "Movies":"V"
    }

def _categoryToSymbol(category):
    return g_catTable[category]

def _symbolToCategory(symbol):
    for name in g_catTable:
        if g_catTable[name] == symbol:
            return name
    assert 0
    return ""

## cross modules links
def titleLink(gtxt, title, lobId, category, amazonAsin, modulesInfo):
    lobUrl = ""
    if lobId != "":
        lobUrl = "s+listsofbestsitem:"+lobId+";"+_categoryToSymbol(category)
    popupItems = []
    if modulesInfo != None:
        if lobUrl != "":
            popupItems.append(['View details',lobUrl,False,True,False])
        if modulesInfo['Amazon']:
            if amazonAsin != "":
                popupItems.append(['Search Amazon','s+amazonitem:'+amazonAsin,False,False,False])
            else:
                if "Books" == category:
                    popupItems.append(['Search Amazon','s+amazonsearch:Books;;1;'+title,False,False,False])
                elif "Movies" == category:
                    popupItems.append(['Search Amazon','s+amazonsearch:DVD;;1;'+title,False,False,False])
                elif "Music" == category:
                    popupItems.append(['Search Amazon','s+amazonsearch:Music;;1;'+title,False,False,False])
        if modulesInfo['Netflix'] and "Movies" == category:
            popupItems.append(['Search Netflix','s+netflixsearch:'+title+';Movie;?',False,False,False])
        if modulesInfo['Lyrics'] and "Music" == category:
            # title is album title!
            popupItems.append(['Search Lyrics','s+lyricssearch:;;'+title+';;',False,False,False])
        if modulesInfo['Encyclopedia']:
            popupItems.append(['Search Encyclopedia','s+pediasearch:'+title,False,False,False])
        if modulesInfo['eBooks'] and "Books" == category:
            link = ebooks.create_search_title_link(title)
            popupItems.append(['Search eBooks',link,False,False,False])
        if modulesInfo['eBay']:
            popupItems.append(['Search eBay',"s+ebay:search;0;?;"+title,False,False,False])
            
    if len(popupItems) > 1:
        gtxt.setHyperlink(buildPopupMenu(popupItems))
    elif lobUrl != "":
        gtxt.setHyperlink(lobUrl)
    
def authorLink(gtxt, author, category, modulesInfo):
    lobUrl = "s+listsofbestssearch:%s;%s;Creator" % (author, category)
    popupItems = []
    if modulesInfo != None:
        popupItems.append(['Search Lists of Bests',lobUrl,False,True,False])
        if modulesInfo['Amazon']:
            if "Books" == category:
                popupItems.append(['Search Amazon','s+amazonsearch:Books;;1;'+author,False,False,False])
            elif "Movies" == category:
                popupItems.append(['Search Amazon','s+amazonsearch:DVD;;1;'+author,False,False,False])
            elif "Music" == category:
                popupItems.append(['Search Amazon','s+amazonsearch:Music;;1;'+author,False,False,False])
        if modulesInfo['Netflix'] and "Movies" == category:
            popupItems.append(['Search Netflix','s+netflixsearch:'+author+';People;?',False,False,False])
        if modulesInfo['Lyrics'] and "Music" == category:
            popupItems.append(['Search Lyrics','s+lyricssearch:'+author+';;;;',False,False,False])
        if modulesInfo['Encyclopedia']:
            popupItems.append(['Search Encyclopedia','s+pediasearch:'+author,False,False,False])
        if modulesInfo['eBooks'] and category == "Books":
            link = ebooks.create_search_author_link(author)
            popupItems.append(['Search eBooks',link,False,False,False])
        if modulesInfo['eBay']:
            popupItems.append(['Search eBay',"s+ebay:search;0;?;"+author,False,False,False])
    if len(popupItems)>1:
        gtxt.setHyperlink(buildPopupMenu(popupItems))
    else:
        gtxt.setHyperlink(lobUrl)

# try parsing pages coming from http://listsofbests.com/lists/ url
# i.e. a list of lists
def tryParseLists(htmlTxt, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    cont = soup.first("div", {"class":"content"})
    if not cont:
        return UNKNOWN_FORMAT, None
    h2 = soup.first("h2")
    if not h2:
        return UNKNOWN_FORMAT, None
    h2Text = getAllTextFromTag(h2)
    category = ""
    if -1 != h2Text.find("Book"):
        category = "Books"
    elif -1 != h2Text.find("Music"):
        category = "Music"
    elif -1 != h2Text.find("Movie"):
        category = "Movies"
    else:
        return UNKNOWN_FORMAT, None
    results = []
    h4List = cont.fetch("h4")
    for h4 in h4List:
        section = getAllTextFromTag(h4).strip()
        ul = getLastElementFromTag(h4).next
        if isinstance(ul, Tag):
            if ul.name == "ul":
                listUrlStart = "http://listsofbests.com/list/"
                liList = ul.fetch("li")
                aList = []
                for li in liList:
                    aItem = li.first("a", {"href": listUrlStart+"%"})
                    if aItem:
                        aList.append(aItem)
                if len(aList) > 0:
                    results.append(["",section])
                    for aItem in aList:
                        title = getAllTextFromTag(aItem)
                        if 0 == len(title.strip()):
                            span = aItem.next
                            title = getAllTextFromTag(span)
                        url = aItem['href']
                        if url[-1] == "/":
                            listNum = url[len(listUrlStart):-1]
                            results.append([listNum, title])
    if 0==len(results):
        return UNKNOWN_FORMAT, None
    # definition
    df = Definition()
    df.TextElement("Home", link='listsofbestsform:main')
    df.TextElement(' / ')
    df.TextElement(category)
    for item in results:
        if item[0] == "":
            df.LineBreakElement(3,2)
            df.TextElement(item[1], style=styleNameBold)
        else:
            df.BulletElement(False)
            df.TextElement(item[1], link="s+listsofbestsbrowse:"+item[0]+";"+_categoryToSymbol(category))
            df.PopParentElement()
    return LISTSOFBESTS_LISTS, universalDataFormatWithDefinition(df, [["H", category]])

def cmpSortItemsByYear(a,b):
    aYear = int(a[4])
    bYear = int(b[4])
    return cmp(bYear,aYear)

# try parsing pages coming from http://listsofbests.com/list/7/ url i.e. a list
# of items
def tryParseList(htmlTxt, category, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    cont = soup.first("div", {"class":"content"})
    if not cont:
        return UNKNOWN_FORMAT, None
    
    # title
    h3 = cont.first("h3")
    if not h3:
        return UNKNOWN_FORMAT, None
    listTitle = getAllTextFromTag(h3).strip()
    
    # description
    descriptionDiv = cont.first("div", {"class":"list-desc"})
    if not descriptionDiv:
        return UNKNOWN_FORMAT, None
    description = getAllTextFromTag(descriptionDiv)
    description = description.split("Find out more")[0]

    # items in table...
    table = cont.first("table")
    if not table:
        return UNKNOWN_FORMAT, None
    trList = table.fetch("tr")
    if len(trList) < 2:
        return UNKNOWN_FORMAT, None
    thList = trList[0].fetch("th")
    numberOfColumns = len(thList) # should be 3 or 4
    if not numberOfColumns in [3,4]:
        return UNKNOWN_FORMAT, None
    itemCounts = 0
    items = []
    for tr in trList[1:]:
        tdList = tr.fetch("td")
        if len(tdList) == numberOfColumns:
            itemCounts += 1
            (numberTd, nameTd, authorTd, buyTd) = (None, None, None, None)
            if numberOfColumns == 3:
                (nameTd, authorTd, buyTd) = tdList
            else: ## numberOfColumns == 4
                (numberTd, nameTd, authorTd, buyTd) = tdList
            # name and url
            itemUrlStart = "http://listsofbests.com/details.cgi?id="
            aItem = nameTd.first("a", {"href":itemUrlStart+"%"})
            name, id = "",""
            if aItem:
                name = getAllTextFromTag(aItem)
                url = aItem['href']
                id = url[len(itemUrlStart):]
            # author/artist/director
            author = getAllTextFromTag(authorTd)
            # amazon asin
            amazon = ""
            amazonUrlStart = "http://www.amazon.com/exec/obidos/asin/"
            aItem = buyTd.first("a", {"href":amazonUrlStart+"%"})
            if aItem:
                amazon = (aItem['href'])[len(amazonUrlStart):].split("/")[0]
            item = [id, name, author, amazon]
            # year/number on list
            if numberTd != None:
                item.append(getAllTextFromTag(numberTd))
            items.append(item)
    if itemCounts == 0:
        return UNKNOWN_FORMAT, None
    fYear = False
    if getAllTextFromTag(thList[0]) in ["Year", "YR"]:
        fYear = True
        items.sort(cmpSortItemsByYear)
    if 0==len(items):
        return UNKNOWN_FORMAT, None

    # definition
    df = Definition()
    df.TextElement("Home", link='listsofbestsform:main')
    df.TextElement(' / ')
    df.TextElement(category, link='s+listsofbestsbrowse:'+category)
    df.TextElement(' / ')
    gtxt = df.TextElement(listTitle, style=styleNameBold)
    df2 = Definition()
    df2.TextElement(description)
    gtxt.setHyperlink("simpleform:Lists of Bests;"+df2.serialize())
    df.LineBreakElement(1,2)
    for item in items:
        ## item = [id, name, author, amazon] [number]
        if len(item) == 5:
            li = df.ListNumberElement(item[4], False)
            if fYear:
                li.setTotalCount(2000)
            else:
                li.setTotalCount(len(items))
        else:
            df.BulletElement(False)
        gtxt = df.TextElement(item[1], style=styleNameBold)
        titleLink(gtxt, item[1], item[0], category, item[3], modulesInfo)
        df.TextElement(" by ")
        gtxt = df.TextElement(item[2])
        authorLink(gtxt, item[2], category, modulesInfo)
        df.PopParentElement()
    return LISTSOFBESTS_LIST, universalDataFormatWithDefinition(df, [["H", category+"/"+listTitle]])

def tryParseDetails(htmlTxt, category, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    cont = soup.first("div", {"class":"content"})
    if not cont:
        return UNKNOWN_FORMAT, None
    
    # amazon asin, name and creator
    table = cont.first("table", {"class":"details"})
    if not table:
        return UNKNOWN_FORMAT, None
    asin = ""
    td = table.first("td", {"class":"detail-img"})
    if td:
        amazonUrlStart = "http://www.amazon.com/exec/obidos/asin/"
        aItem = td.first("a", {"href":amazonUrlStart+"%"})
        if aItem:
            asin = aItem['href'][len(amazonUrlStart):].split("/")[0]
    td = table.first("td", {"class":"detail-data"})
    if not td:
        return UNKNOWN_FORMAT, None
    titleSpan = td.first("span", {"class":"detail-title"})
    if titleSpan:
        title = getAllTextFromTag(titleSpan).strip()
        bItem = td.first("b")
        if bItem:
            creator = getAllTextFromTag(bItem).strip()
            # remove Director:
            dirTxt = "Director:"
            if creator.startswith(dirTxt):
                creator = creator[len(dirTxt):].replace("&nbsp;"," ").strip()            
    else:
        return UNKNOWN_FORMAT, None

    # definition
    df = Definition()
    df.TextElement("Home", link='listsofbestsform:main')
    df.TextElement(' / ')
    gtxt = df.TextElement(title, style=styleNameBold)
    titleLink(gtxt, title, "", category, asin, modulesInfo)
    df.TextElement(' by ')
    gtxt = df.TextElement(creator)
    authorLink(gtxt, creator, category, modulesInfo)
    df.LineBreakElement(1,2)

    # lists that contains this item
    results = []
    aItem = soup.first("a", {"name":"lists"})
    if aItem:
        next = aItem.next
        while next and not isinstance(next, Tag):
            next = next.next
        if next:
            if next.name == "div":
                liList = next.fetch("li")
                items = []
                listUrlStart = "http://listsofbests.com/list/"
                for li in liList:
                    aItem = li.first("a", {"href":listUrlStart+"%"})
                    if aItem:
                        listId = aItem['href'][len(listUrlStart):].split("/")[0]
                        listName = getAllTextFromTag(aItem).strip()
                        listPrefix = getAllTextFromTo(li,aItem)
                        smallList = [listId,listName]
                        if len(listPrefix) > 0:
                            smallList.append(listPrefix)
                        items.append(smallList)
                if len(items) > 0:
                    for item in items:
                        results.append(item)
    # definition
    if len(results) > 0:
        df.LineBreakElement()
        df.TextElement("Lists that contains it:", style=styleNameHeader)
        for item in results:
            ## item is [listId, listName] [listPrefix]
            df.BulletElement(False)
            if len(item) == 3:
                df.TextElement(item[2])
            df.TextElement(item[1], link='s+listsofbestsbrowse:'+item[0]+';'+_categoryToSymbol(category))
            df.PopParentElement()
        df.LineBreakElement(1,2)
   
    # amazon info
    results = []
    aItem = soup.first("a", {"name":"amzn-meta"})
    if aItem:
        next = aItem.next
        while next and not isinstance(next, Tag):
            next = next.next
        if next:
            if next.name == "div":
                liList = next.fetch("li")
                for li in liList:
                    info = getAllTextFromTag(li).strip()
                    if not info.startswith("More information available "):
                        results.append(info)
    # definition
    if len(results) > 0:
        df.LineBreakElement()
        gtxt = df.TextElement("Amazon informations", style=styleNameHeader)
        df2 = Definition()
        for info in results:
            df2.BulletElement(False)
            df2.TextElement(info)
            df2.PopParentElement()
        gtxt.setHyperlink("simpleform:Amazon informations;"+df2.serialize())
    
    return LISTSOFBESTS_DETAILS, universalDataFormatWithDefinition(df, [["H", title]])

def parseListsOfBests(htmlTxt, category, modulesInfo):
    type, body = tryParseLists(htmlTxt, modulesInfo)
    if UNKNOWN_FORMAT != type:
        return (type, body)

    type, body = tryParseList(htmlTxt, category, modulesInfo)
    if UNKNOWN_FORMAT != type:
        return (type, body)

    type, body = tryParseDetails(htmlTxt, category, modulesInfo)
    if UNKNOWN_FORMAT != type:
        return (type, body)

    return type, body

def parseListsOfBestsSearch(htmlTxt, keyword, category, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    cont = soup.first("div", {"class":"content"})
    if not cont:
        return UNKNOWN_FORMAT, None
    form = cont.first("form", {"name":"siteform", "action":"?", "method":"post"})
    if not form:
        return UNKNOWN_FORMAT, None
    results = []
    ul = cont.first("ul")
    if ul:
        itemUrlStart = "http://listsofbests.com/details.cgi?id="
        for li in ul.fetch("li"):
            aItem = li.first("a",{"href":itemUrlStart+"%"})
            if aItem:
                id = aItem['href'][len(itemUrlStart):]
                name = getAllTextFromTag(aItem)
                creator = getAllTextFromTo(getLastElementFromTag(aItem).next,getLastElementFromTag(li).next).strip()
                if creator.startswith(", by "):
                    creator = creator[5:]
                cat = category
                if creator[-1] == ')':
                    brace = creator.rfind('(')
                    if brace != -1:
                        if creator[brace:] == '(Book)':
                            creator = creator[:brace].strip()
                            cat = 'Books'
                        elif creator[brace:] == '(Movie)':
                            creator = creator[:brace].strip()
                            cat = 'Movies'
                        elif creator[brace:] == '(Music)':
                            creator = creator[:brace].strip()
                            cat = 'Music'
                smallList = [id, name, creator, cat]
                results.append(smallList)
    
    if 0==len(results):
        return NO_RESULTS, None

    # definition
    df = Definition()
    df.TextElement("Home", link='listsofbestsform:main')
    df.TextElement(" / Search results for '"+keyword+"':")
    df.LineBreakElement(1,2)
    #todo: try to group results (by creator, by category?)

    for item in results:
        #[id, name, creator, cat]
        df.BulletElement(False)
        gtxt = df.TextElement(item[1], style=styleNameBold)
        titleLink(gtxt, item[1], item[0], item[3], "", modulesInfo)
        df.TextElement(" by ")
        gtxt = df.TextElement(item[2])
        authorLink(gtxt, item[2], item[3], modulesInfo)
        if item[3] != category:
            df.TextElement(" ("+item[3]+")")
        df.PopParentElement()

    history = "Search for "+keyword
    if category != "Everything":
        history += ' ('+category+')'
    return LISTSOFBESTS_SEARCH, universalDataFormatWithDefinition(df, [["H", history]])

def retrieveListsOfBestsSearch(fieldValue, modulesInfo):
    parts = fieldValue.split(";")
    if 3 != len(parts):
        return INVALID_REQUEST, None
    mediaTable = {
        "Everything":"0",
        "Books": "1",
        "Movies": "2",
        "Music": "3"
        }
    titleTable = {
        "Both":"0",
        "Title":"1",
        "Creator":"2"
        }
    try:
        media, title, keywords = mediaTable[parts[1]], titleTable[parts[2]], parts[0]
    except:
        return INVALID_REQUEST, None
    postData = {
        "full_qry":keywords,
        "media":media,
        "which":title,
        "srch":"Search",
        "":"Clear"
        }
    url = "http://listsofbests.com/?"
    htmlTxt = getHttp(url, postData=postData)
    # parse it
    if None == htmlTxt:
        return MODULE_DOWN, None
    resultType, resultBody = parseListsOfBestsSearch(htmlTxt, keywords, parts[1], modulesInfo)
    if UNKNOWN_FORMAT == resultType:
        logParsingFailure("listsofbestssearch", fieldValue, url, htmlTxt)
    return resultType, resultBody

def retrieveListsOfBestsItem(fieldValue, modulesInfo):
    (id, category) = fieldValue.split(";")
    category = _symbolToCategory(category)
    url = "http://listsofbests.com/details.cgi?id=%s" % id
    htmlTxt = getHttp(url)
    if None == htmlTxt:
        return MODULE_DOWN, None
    resultType, resultBody = parseListsOfBests(htmlTxt, category, modulesInfo)
    if UNKNOWN_FORMAT == resultType:
        logParsingFailure("listsofbestsitem", fieldValue, url, htmlTxt)
    return resultType, resultBody

def retrieveListsOfBestsBrowse(fieldValue, modulesInfo):
    translate = {
        "books":"http://listsofbests.com/lists/1/",
        "movies":"http://listsofbests.com/lists/2/",
        "music":"http://listsofbests.com/lists/3/"
        }
    url = ""
    category = "Books"
    try:
        url = translate[fieldValue.lower()]
    except:
        (id, category) = fieldValue.split(";")
        category = _symbolToCategory(category)
        url = "http://listsofbests.com/list/%s/" % id

    htmlTxt = getHttp(url)
    if None == htmlTxt:
        return MODULE_DOWN, None
    resultType, resultBody = parseListsOfBests(htmlTxt, category, modulesInfo)
    if UNKNOWN_FORMAT == resultType:
        logParsingFailure("listsofbestsbrowse", fieldValue, url, htmlTxt)
    return resultType, resultBody

    
    
