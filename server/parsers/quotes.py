# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
#
import string
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise

import time
from parserUtils import *
from ResultType import *
from Retrieve import *
from definitionBuilder import *
from popupMenu import *
from parserErrorLogger import logParsingFailure

def addQuotesToDefinition(df, items, modulesInfo):
    first = True
    for item in items:
        if first:
            first = False
        else:
            df.LineBreakElement(3,2)
        df.TextElement(item[1])
        te = df.TextElement(item[0], style=styleNameBold)
        te.setJustification(justRight)

# one of them can be None...
def parseDailyQuotes(htmlTxt1, htmlTxt2, modulesInfo):
    daily = []
    mDaily = []
    dailyDate = ""
    
    if htmlTxt1:
        soup = BeautifulSoup()
        soup.feed(htmlTxt1)
        items = soup.fetch("item")
        if len(items) < 4:
            return UNKNOWN_FORMAT, None
        for item in items:
            title = getAllTextFromTag(item.first("title"))
            desc = getAllTextFromTag(item.first("description"))
            daily.append([title, desc])
        dailyDate = getAllTextFromTag(soup.first("pubdate"))
    if htmlTxt2:
        soup = BeautifulSoup()
        soup.feed(htmlTxt2)
        items = soup.fetch("item")
        if len(items) < 4:
            return UNKNOWN_FORMAT, None
        for item in items:
            title = getAllTextFromTag(item.first("title"))
            desc = getAllTextFromTag(item.first("description"))
            mDaily.append([title, desc])
        if "" == dailyDate:
            dailyDate = getAllTextFromTag(soup.first("pubdate"))

    if dailyDate == "":
        return UNKNOWN_FORMAT, None
    dailyDate = string.join(dailyDate.split(" ")[:3], " ")
    # build definition
    df = Definition()

    if len(daily) > 0:
        te = df.TextElement("Quotes of the Day", style=styleNamePageTitle)
        te.setJustification(justCenter)
        df.LineBreakElement()
        addQuotesToDefinition(df, daily[:4], modulesInfo)
        if len(daily) > 4:
            df2 = Definition()
            addQuotesToDefinition(df2, daily[4:], modulesInfo)
            te = df.TextElement("Older", link="simpleform:Quotes;"+df2.serialize())
            te.setJustification(justCenter)
    if len(mDaily) > 0:
        if len(daily) > 0:
            df.LineBreakElement()
        te = df.TextElement("Motivational Quotes", style=styleNamePageTitle)
        te.setJustification(justCenter)
        df.LineBreakElement()
        addQuotesToDefinition(df, mDaily[:4], modulesInfo)
        if len(mDaily) > 4:
            df2 = Definition()
            addQuotesToDefinition(df2, mDaily[4:], modulesInfo)
            te = df.TextElement("Older", link="simpleform:Quotes;"+df2.serialize())
            te.setJustification(justCenter)

    df.LineBreakElement()
    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    df.TextElement("Update", link="s+quotes:daily")
    df.TextElement(" \x95 ", style=styleNameGray)
    df.TextElement("Random", link="s+quotes:random")
    df.PopParentElement()
    return QUOTES_DATA, universalDataFormatWithDefinition(df, [])

# daily quotes cache
#  (this is hack, we store 2 xml, instead of UDF, because of modulesInfo)
g_quotesDataCached = None
g_quotesDataWhenCached = None
g_quotesCacheExpiration = float(60*60*60)*2 # every 2 hours

def quotesCacheExpired():
    global g_quotesDataWhenCached, g_quotesCacheExpiration
    curTime = time.time()
    secondsSinceCached = curTime - g_quotesDataWhenCached
    if secondsSinceCached > g_quotesCacheExpiration:
        return True
    return False

def retrieveDaily(modulesInfo):
    global g_quotesDataCached, g_quotesDataWhenCached, g_quotesCacheExpiration
    resultType, resultBody = RETRIEVE_FAILED, None
    # get data
    url1 = "http://www.quotationspage.com/data/qotd.rss"
    url2 = "http://www.quotationspage.com/data/mqotd.rss"
    htmlTxt1, htmlTxt2 = None, None
    
    if None != g_quotesDataCached:
        if not quotesCacheExpired():
            htmlTxt1, htmlTxt2 = g_quotesDataCached
            print "from cache"
    else:
        ### TODO: remove this!
##        try:
##            fo = open("c:\\tmp\\t1.txt","rt")
##            htmlTxt1 = fo.read()
##            fo.close()
##            fo = open("c:\\tmp\\t2.txt","rt")
##            htmlTxt2 = fo.read()
##            fo.close()
##        except:
        htmlTxt1 = getHttp(url1)
        htmlTxt2 = getHttp(url2)
##            fo = open("c:\\tmp\\t1.txt","wt")
##            fo.write(htmlTxt1)
##            fo.close()
##            fo = open("c:\\tmp\\t2.txt","wt")
##            fo.write(htmlTxt2)
##            fo.close()

    if None == htmlTxt1 and None == htmlTxt2:
        return RETRIEVE_FAILED, None
    if None == htmlTxt1 or None == htmlTxt2:
        # one is down - print sth or what?
        print "One is down"

    resultType, resultBody = parseDailyQuotes(htmlTxt1, htmlTxt2, modulesInfo)
    if UNKNOWN_FORMAT == resultType:
        logParsingFailure("quotes", "daily", htmlTxt1+"\n----\n"+htmlTxt2, url1)
    if QUOTES_DATA == resultType and None != htmlTxt1 and None != htmlTxt2:
        # cache it (but only if both pages are good
        g_quotesDataWhenCached = time.time()
        g_quotesDataCached = (htmlTxt1, htmlTxt2)
    else:
        # no data? so maybe from cache? (older)
        if None != g_quotesDataCached:
            resultType, resultBody = parseDailyQuotes(g_quotesDataCached[0], g_quotesDataCached[1], modulesInfo)
            logParsingFailure("quotes", "daily", None, "Using old cache - retrieve failed")
    return resultType, resultBody

def parseRandomQuotes(htmlTxt, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    quotes = []
    dtList = soup.fetch("dt", {"class":"quote"})
    ddList = soup.fetch("dd", {"class":"author"})
    if len(dtList) == len(ddList) and len(dtList) > 0:
        for i in range(len(ddList)):
            quote = getAllTextFromTag(dtList[i])
            next = ddList[i]
            bItem = None
            while next and None == bItem:
                next = next.next
                if isinstance(next, Tag):
                    if next.name == "b":
                        bItem = next
                    elif next.name == "dt":
                        next = None
                    elif next.name == "select":
                        next = None
            if bItem:
                aItem = bItem.first("a")
                if aItem:
                    author = getAllTextFromTag(aItem)
                else:
                    author = getAllTextFromTag(bItem)
            quotes.append([author, "\""+quote.strip()+"\""])

    if 0 == len(quotes):
        return UNKNOWN_FORMAT, None
    # build definition
    df = Definition()

    te = df.TextElement("Random Quotes", style=styleNamePageTitle)
    te.setJustification(justCenter)
    df.LineBreakElement()
    addQuotesToDefinition(df, quotes, modulesInfo)
    df.LineBreakElement()
    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    df.TextElement("Daily", link="s+quotes:daily")
    df.TextElement(" \x95 ", style=styleNameGray)
    df.TextElement("Random", link="s+quotes:random")
    df.PopParentElement()
    return QUOTES_DATA, universalDataFormatWithDefinition(df, [])
    

def retrieveRandom(modulesInfo):
    # get data
    url = "http://www.quotationspage.com/random.php3"
    # all?
    postData = {
        "number":"4",
        "collection[]":"mgm",
        "collection[]":"motivate",
        "collection[]":"classic",
        "collection[]":"coles",
        "collection[]":"lindsly",
        "collection[]":"poorc",
        "collection[]":"altq",
        "collection[]":"20thcent",
        "collection[]":"bywomen",
        "collection[]":"devils",
        "collection[]":"contrib"
        }
    htmlTxt = getHttp(url, postData=postData)
    if None == htmlTxt:
        return RETRIEVE_FAILED, None
    # parse
    resultType, resultBody = parseRandomQuotes(htmlTxt, modulesInfo)
    if UNKNOWN_FORMAT == resultType:
        logParsingFailure("quotes", "random", htmlTxt, url)
    return resultType, resultBody

def retrieveQuotes(fieldValue, modulesInfo):
    if "daily" == fieldValue:
        resultType, resultBody = retrieveDaily(modulesInfo)
    elif "random" == fieldValue:
        resultType, resultBody = retrieveRandom(modulesInfo)
    else:
        assert 0
    return resultType, resultBody

    
    
