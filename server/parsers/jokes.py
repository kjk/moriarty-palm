# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  www.jokes.com
#
import string
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise

from entities import convertNamedEntities
from entities import convertNumberedEntities
from parserUtils import *
from ResultType import *

from Retrieve import *
from parserErrorLogger import logParsingFailure
import random
from threading import Lock



jUnknownFormatText = None
jNoResultsText = None
# to tests only
#jNoResultsText = "no results"
#jUnknownFormatText = "unknown format"

# htmlTxt is a html page
# Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   JOKES_LIST : resultBody is a jokes list - (rank, title, rating, explicitness, url) items in UDF
#   NO_RESULTS: no results found
#   UNKNOWN_FORMAT : resultBody is None
def parseList(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # find table with results
    tableList = soup.fetch("table", {"cellpadding":"0", "cellspacing":"0", "border":"0", "width":"100%"})
    if 0 == len(tableList):
        return (UNKNOWN_FORMAT, jUnknownFormatText)

    outerList = []
    for table in tableList:
        trList = table.fetch("tr")
        if 2 <= len(trList):
            tdCount = len(trList[0].fetch("td"))
            if 3 > tdCount:
                return (UNKNOWN_FORMAT, jUnknownFormatText)
            for tr in trList[1:]:
                tdList = tr.fetch("td")
                rank = ""
                if 4 == tdCount:
                    rank = getAllTextFromTag(tdList[0])
                title = getAllTextFromTag(tdList[-3])
                rating = getAllTextFromTag(tdList[-2])
                explicitness = getAllTextFromTag(tdList[-1])
                url = tdList[-3].first("a")['href']
                if not url:
                    return (UNKNOWN_FORMAT, jUnknownFormatText)
                outerList.append((rank, title, rating, explicitness, url))

    if 0 == len(outerList):
        return (NO_RESULTS, jNoResultsText)

    return (JOKES_LIST, universalDataFormatReplaceEntities(outerList))

# htmlTxt is a html page
# Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   JOKE_DATA : resultBody is a joke (title,text) in UDF
#   UNKNOWN_FORMAT : resultBody is None
def parseJoke(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    table = soup.first("table", {"width":"328", "id":"Table2"})
    if not table:
        return (UNKNOWN_FORMAT, jUnknownFormatText)
    tdList = table.fetch("td",{"colspan":"3", "valign":"top", "class":"body"})
    if 3 != len(tdList):
        return (UNKNOWN_FORMAT, jUnknownFormatText)

    # simple format - simple parser
    title = getAllTextFromTag(tdList[0]).strip()
    text = getAllTextFromToInBrFormat(tdList[1], tdList[2].previous)
    smallList = [title,text]
    # add rating information
    if len(title) + len(text) > 16: # in random joke sometimes it returns small nothing... so to be sure
        span = soup.first("span", {"class":"body"})
        if span:
            text = getAllTextFromTag(span).replace("\n","").strip()
            img = span.first("img", {"src":"%"})
            if text.startswith("CURRENT RATING") and img:
                src = img['src']
                src = src.split("/")[-1]
                src = src.replace(".gif","")
                translator = {
                    "iconrate_one":"1",
                    "iconrate_two":"2",
                    "iconrate_three":"3",
                    "iconrate_four":"4",
                    "iconrate_five":"5",
                    "iconrate_one_half":"1.5",
                    "iconrate_two_half":"2.5",
                    "iconrate_three_half":"3.5",
                    "iconrate_four_half":"4.5",
                    "iconrate_zero_half":"0.5",
                    }
                rating = "not rated"
                try:
                    rating = translator[src]
                except:
                    pass
                smallList.append(rating)    
    outerList = [smallList]    
    return (JOKE_DATA, universalDataFormatReplaceEntities(outerList))

## NEW JOKES COM



# cache random joke udf (thread safe)
class RandomJokeCache:
    RANDOM_JOKES_TO_CACHE = 20
    CACHE_UPDATE_THRESHOLD = 10
    def __init__(self):
        self._lock = Lock()
        self._cachedItems = []
        self._itemsCount = 0
        self._someoneIsFillingCache = False

    def canIFillCache(self):
        self._lock.acquire()
        canI = False
        if not self._someoneIsFillingCache:
            canI = True
            self._someoneIsFillingCache = True
        self._lock.release()
        return canI

    def finishedCacheFilling(self):
        self._lock.acquire()
        self._someoneIsFillingCache = False
        self._lock.release()

    def getRandomJokeUDF(self):
        self._lock.acquire()
        udf = None
        if 1 < self._itemsCount:
            udf = self._cachedItems.pop(0)
            self._itemsCount -= 1
        elif 1 == self._itemsCount:
            udf = self._cachedItems[0]
            self._itemsCount -= 1
        self._lock.release()
        return udf

    # this is dirty get - even if data is not actual it will be returned
    def getRandomJokeUDFOld(self):
        self._lock.acquire()
        udf = None
        if 1 < self._itemsCount:
            udf = self._cachedItems.pop(0)
            self._itemsCount -= 1
        elif 1 == len(self._cachedItems):
            udf = self._cachedItems[0]
            if 1 == self._itemsCount:
                self._itemsCount -= 1
        udf = self._cachedItems[0]
        self._lock.release()
        return udf

    def setRandomJokeUDF(self, udf):
        self._lock.acquire()
        self._cachedItems.append(udf)
        if 0 == self._itemsCount and 1 < len(self._cachedItems):
            # remove item if it was used in dirty read
            self._cachedItems.pop(0)
        self._itemsCount = len(self._cachedItems)
        self._lock.release()

    def getItemsCount(self):
        self._lock.acquire()
        count = self._itemsCount
        self._lock.release()
        return count

g_randomJokeCache = RandomJokeCache()

def _parseRandomJoke(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    table = soup.first("table", {"id":"jokeIframeTable2"})
    if not table:
        return UNKNOWN_FORMAT, None
    # title
    titleSpan = table.first("span", {"class":"jokeTitle_v2"})
    if not titleSpan:
        return UNKNOWN_FORMAT, None
    title = getAllTextFromTag(titleSpan)
    # text
    trList = table.fetch("tr")
    text = ""
    if len(trList) > 6:
        tdList = trList[5].fetch("td")
        if len(tdList) == 3:
            text = getAllTextFromToInBrFormat(tdList[1], tdList[2])
            if len(text.replace("&nbsp;"," ").strip()) < 2:
                text = ""
    if "" == text:
        return UNKNOWN_FORMAT, None
    smallList = [title,text]
    # rating
    table = soup.first("table", {"id":"Table5"})
    if table:
        td = table.first("td")
        if td:
            imgList = td.fetch("img", {"src":"%"})
            rating = "not rated"
            translator = {
                "iconrate_one":"1",
                "iconrate_two":"2",
                "iconrate_three":"3",
                "iconrate_four":"4",
                "iconrate_five":"5",
                "iconrate_one_half":"1.5",
                "iconrate_two_half":"2.5",
                "iconrate_three_half":"3.5",
                "iconrate_four_half":"4.5",
                "iconrate_zero_half":"0.5",
                }
            for img in imgList:
                src = img['src']
                src = src.split("/")[-1]
                src = src.replace(".gif","")
                try:
                    rat = translator[src]
                    rating = rat
                except:
                    pass
            smallList.append(rating)
    outerList = [smallList]
    return (JOKE_DATA, universalDataFormatReplaceEntities(outerList))

g_randomJokesParseFailed = 0

def _retrieveRandomJoke():
    global g_randomJokesParseFailed
    # for some reason some jokes are empty...
    counter = 6
    res, body = UNKNOWN_FORMAT, None
    while 0 < counter and res != JOKE_DATA:
        randomJokeNumber = random.randint(1, 11073)
        url = "http://jokes.comedycentral.com/index_joke.asp?initRand=true&sql=12&rand_id=%s" % str(randomJokeNumber)
        htmlTxt = getHttp(url)
        if None == htmlTxt:
            return MODULE_DOWN, None
        res, body = _parseRandomJoke(htmlTxt)
        counter -= 1
        if 0 == counter and res != JOKE_DATA:
            udf = [["No joke", "Please try again. It may be module problem. If you seen this screen more than 3 times, please wait some time (one day) before you press 'Random joke' button."]]
            res = universalDataFormatReplaceEntities(udf)

    if UNKNOWN_FORMAT == res:
        if g_randomJokesParseFailed < 5:
            logParsingFailure("Get-Joke", "random", htmlTxt, url)
            g_randomJokesParseFailed += 1
    return res, body

def _addRandomJokeToCache():
    global g_randomJokeCache
    res, body = _retrieveRandomJoke()
    if res == JOKE_DATA or not (body in [None, ""]):
        g_randomJokeCache.setRandomJokeUDF(body)
    log(SEV_MED, "Jokes cache items count: %d\n" % g_randomJokeCache.getItemsCount())

def fillJokesCache():
    global g_randomJokeCache
    if g_randomJokeCache.CACHE_UPDATE_THRESHOLD < g_randomJokeCache.getItemsCount():
        return
    # not all threads need to fill cache... just select one for that job
    if not g_randomJokeCache.canIFillCache():
        return
    try:
        for i in range(g_randomJokeCache.RANDOM_JOKES_TO_CACHE - g_randomJokeCache.getItemsCount()):
            _addRandomJokeToCache()
    finally:
        g_randomJokeCache.finishedCacheFilling()

def getRandomJoke():
    global g_randomJokeCache
    resultBody = g_randomJokeCache.getRandomJokeUDF()
    if None == resultBody:
        # need to call it if no cache present...
        _addRandomJokeToCache()
        resultBody = g_randomJokeCache.getRandomJokeUDFOld()
    # no data? why?
    if None == resultBody:
        return MODULE_DOWN, None
    return JOKE_DATA, resultBody

def _parseList(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    trList = soup.fetch("tr")
    outerList = []
    for tr in trList:
        if len(tr.fetch("tr")) == 0:
            tdList = tr.fetch("td")
            if len(tdList) == 4:
                if tdList[0].first("span",{"class":"title"}):
                    rank = getAllTextFromTag(tdList[0])
                    title = getAllTextFromTag(tdList[1])
                    rating = getAllTextFromTag(tdList[2])
                    explicitness = getAllTextFromTag(tdList[3])
                    aItem = tdList[1].first("a")
                    if aItem:
                        url = aItem['href']
                        outerList.append((rank, title, rating, explicitness, url))
    if 0 == len(outerList):
        return (NO_RESULTS, jNoResultsText)
    return (JOKES_LIST, universalDataFormatReplaceEntities(outerList))

def getJokesList(fieldValue):
    parts = fieldValue.split(";")
    if 6 > len(parts):
        return INVALID_REQUEST, None

    userRating = parts[0].strip()
    userOrder = parts[1].strip()
    userExplicitnessList = parts[2].strip().split(" ")
    userTypesList = parts[3].strip().split(" ")
    userCategoriesList = parts[4].strip().split(" ")
    userKeyword = string.join(parts[5:],";").strip()

    if "rating" != userOrder and "rank" != userOrder:
        return INVALID_REQUEST, None
    if "0" > userRating or "9" < userRating or 1 != len(userRating):
        return INVALID_REQUEST, None
    # rating
    rating = str(int(userRating)*2)
    # sort order
    order = ""
    if "rating" == userOrder:
        order = "rtd"
    elif "rank" == userOrder and 0 < len(userKeyword):
        order = "rd"
    # keyword
    keyword = userKeyword
    # explicitness
    explicitnessList = ["Clean","Tame","Racy"]
    explicitnessOut = []
    for item in userExplicitnessList:
        if 2 < len(item):
            index = explicitnessList.index(item)
            if -1 < index and len(explicitnessList) > index:
                explicitnessOut.append(str(index))
            else:
                return INVALID_REQUEST, None
    explicitness = string.join(explicitnessOut,",")
    # category
    categoriesList = ["Blonde", "Entertainment", "Men/Women", "Insults", "Yo-Mama", "Lawyer", "News&Politics", "Redneck", "Barroom", "Gross", "Sports", "Foreign", "Whatever", "Medical", "Sexuality", "Animals", "Children", "Anti-Joke", "Bush", "College", "Farm", "Business", "Religious", "Tech"]
    categoriesOut = []
    for item in userCategoriesList:
        if 2 < len(item):
            index = categoriesList.index(item)
            if -1 < index and len(categoriesList) > index:
                categoriesOut.append(str(index+14)) # categories are in <14;37> range
            else:
                return INVALID_REQUEST, None

    categories = string.join(categoriesOut,",")
    # type
    typesList = ["Articles", "One-Liners", "QandA", "Sketches", "Stories", "Lists"]
    typesOut = []
    for item in userTypesList:
        if 2 < len(item):
            index = typesList.index(item)
            if -1 < index and len(typesList) > index:
                typesOut.append(str(index))
            else:
                return INVALID_REQUEST, None
    types = string.join(typesOut,",")

    jokesUrl = "http://jokes.comedycentral.com/search/results_output.asp?p=1&c=%s&e=%s&t=%s&r=%s&o=%s&k=%s"
    url = jokesUrl % (categories, explicitness, types, rating, order, urllib.quote(keyword))
    htmlTxt = retrieveHttpResponseWithRedirectionHandleException(url)
    if None == htmlTxt:
        return MODULE_DOWN, None

    resultType, resultBody = _parseList(htmlTxt)

    if resultType == UNKNOWN_FORMAT:
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
    return resultType, resultBody

def getJoke(fieldValue):
    url = fieldValue.replace("/results/detail.asp", "http://jokes.comedycentral.com/index_joke.asp")
    htmlTxt = getHttp(url)
    if None == htmlTxt:
        return MODULE_DOWN, None
    res, body = _parseRandomJoke(htmlTxt)
    if UNKNOWN_FORMAT == res:
        logParsingFailure("Get-Joke", fieldValue, htmlTxt, url)
    return res, body

def main():
    print "test joke module"

    print "*"
##    getRandomJoke()
    getJokesList("2;rating;;;;")
    print "done"

##    fo = open('file.html','wt')
##    fo.write(htmlTxt)
##    fo.close()

    

if __name__ == "__main__":
    main()

