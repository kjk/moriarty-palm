# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  http://www.gasbuddy.com/
#
import sys, os, os.path, string, re, pickle, arsutils, cookielib

try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise

from entities import convertNamedEntities, convertNumberedEntities
from parserUtils import *
from ResultType import *
from multiUserSupport import *
from Retrieve import *

g_fUseCache = True

gUnknownFormatText = None
gNoResultsText = None
gLocationUnknownText = None
# to tests only
#gNoResultsText = "no results"
#gUnknownFormatText = "unknown format"
#gLocationUnknownText = "location unknown"

g_zipUrlCachePath = os.path.join(getServerStorageDir(), "gasprices-cache.pickle")

# the cache maps zipcodes to urls
g_cache = {}

def loadCache():
    global g_zipUrlCachePath, g_cache
    assert 0 == len(g_cache)
    # restores all the variables that we want to persist across session from
    # the disk
    try:
        fo = open(g_zipUrlCachePath, "rb")
    except IOError:
        # it's ok to not have the file
        return
    g_cache = pickle.load(fo)
    fo.close()

loadCache()

# TODO: make it thread-safe
def saveCache():
    global g_zipUrlCachePath, g_cache
    # save all the variables that we want to persist across session on disk
    fo = open(g_zipUrlCachePath, "wb")
    pickle.dump(g_cache,fo)
    fo.close()

# htmlTxt is a html page
# Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   GAS_DATA : resultBody is a gas prices list (price, name, address, area, time) (UDF)
#   NO_RESULTS: no results found
#   UNKNOWN_FORMAT : resultBody is None
def parseGasOld(htmlTxt, url=None, dbgLevel=0):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    testTitle = soup.first("title")
    if testTitle:
        if getAllTextFromTag(testTitle).startswith("GasBuddy.com - Find cheap gas prices in your city"):
            return (LOCATION_UNKNOWN, gLocationUnknownText)

    outerList = []
    trList = soup.fetch("tr")
    for trItem in trList:
        tdList = trItem.fetch("td")
        if 8 == len(tdList):
            if tdList[1].first("table"):
                price = getAllTextFromTag(tdList[0]).strip()
                name = getAllTextFromTag(tdList[2]).strip()
                address = getAllTextFromTag(tdList[4]).strip()
                area = getAllTextFromTag(tdList[5]).strip()
                time = getAllTextFromTag(tdList[6]).strip()
                smallList = [price, name, address, area, time]
                outerList.append(smallList)
        else:
            if 0 != len(tdList):
                firstB = tdList[0].first("b")
                if firstB:
                    if getAllTextFromTag(firstB).startswith("No gas prices found."):
                        return (NO_RESULTS, gNoResultsText)

    if 0 == len(outerList):
        if dbgLevel > 0:
            print "len(outerList)==0"
        return parsingFailed(url, htmlTxt)

    return (GAS_DATA, universalDataFormatReplaceEntities(outerList))

def parseGas(htmlTxt, url=None, dbgLevel=0):
    soup = BeautifulSoup()

    # those people doing gasprices.com can't even produce valid html
    # fix html to make parsing later on easier
    htmlTxt = re.sub(r'</a></td>\s*?</td>', "</a></td>", htmlTxt)
    soup.feed(htmlTxt)

    testTitle = soup.first("title")
    if testTitle:
        if getAllTextFromTag(testTitle).startswith("GasBuddy.com - Find cheap gas prices in your city"):
            return (LOCATION_UNKNOWN, gLocationUnknownText)

    outerList = []
    trList = soup.fetch("tr", {"class" : "PTableRow"})

    # each item is in two consequitive <tr>. First one has <td> with:
    # - price, name, url, area, time, user
    # second <tr> has address
    if 0 != len(trList) % 2:
        if dbgLevel > 0:
            print "len(trList)=%d is not even" % len(trList)
        return parsingFailed(url, htmlTxt)
    listItems = len(trList)/2
    for pos in range(listItems):
        trOne = trList[pos*2]
        trTwo = trList[pos*2+1]

        tdList = trOne.fetch("td")
        if 6 == len(tdList):
            price = getAllTextFromTag(str(tdList[0].first("a").contents[0]))
            price = price.strip()
            #if dbgLevel > 0:
            #    print "price: %s" % price
            name = getAllTextFromTag(tdList[1]).strip()
            #if dbgLevel > 0:
            #    print "name: %s" % name

            area = getAllTextFromTag(tdList[3]).strip()
            #if dbgLevel > 0:
            #    print "area: %s" % area

            time = getAllTextFromTag(tdList[4]).strip()
            #if dbgLevel > 0:
            #    print "time: %s" % time
        else:
            return parsingFailed(url, htmlTxt)

        tdList = trTwo.fetch("td")
        if 1 != len(tdList):
            if dbgLevel > 0:
                print "len(tdList)=%d (!=1)" % len(tdList)
                print "str(trTwo)=%s" % str(trTwo)
                print "str(tdList)=%s" % str(tdList)
            return parsingFailed(url, htmlTxt)

        address = getAllTextFromTag(tdList[0]).strip()
        #if dbgLevel > 0:
        #    print "address: %s" % address

        smallList = [price, name, address, area, time]
        outerList.append(smallList)

    if 0 == len(outerList):
        if dbgLevel > 0:
            print "len(outerList)==0"
        td = soup.first("td", {"class":"PList"})
        if td:
            bItem = td.first("b")
            if bItem:
                if getAllTextFromTag(bItem).startswith("No gas prices found."):
                    return NO_RESULTS, None
        return parsingFailed(url, htmlTxt)

    return (GAS_DATA, universalDataFormatReplaceEntities(outerList))


def getGasPricesForZip(jar, zipCode, dbgLevel=0):
    global g_cache, g_fUseCache

    gasBuddyUrl = "http://www.gasbuddy.com/findsite.asp?zip=%s" % zipCode

    htmlTxt = ""
    if g_fUseCache and g_cache.has_key(zipCode):
        url = g_cache[zipCode]
        if 1 == dbgLevel:
            print "got url from cache, zipCode=%s, url=%s" % (zipCode, url)
    else:
        hdrs = None
        try:
            htmlTxt = getHttp(gasBuddyUrl, handleRedirect=False, dbgLevel=dbgLevel, cookieJar = jar, handleException = False)
        except urllib2.HTTPError, err:
            if 500 == err.code:
                # unfortunately the server just panics with 500 (Internal server error)
                # if we try to give it anything else than a number (e.g. "asdf")
                # but it really means an unknown location
                return (LOCATION_UNKNOWN, None)
            if 302 != err.code:
                raise err
            hdrs = err.headers

        assert hdrs != None
        url = hdrs[location_hdr]
        if url == "index.asp":
            # this means an uknown location
            return (LOCATION_UNKNOWN, None)

    # print "**** location: %s" % url
    htmlTxt = getHttp(url, referer=gasBuddyUrl, dbgLevel=dbgLevel, cookieJar = jar, retryCount=2)
    if None == htmlTxt:
        return retrieveFailed(url)

    #print htmlTxt
    # gasbuddy.com introduced stupid redirection, so let's redirect
    if dbgLevel > 0:
        print ":%s:" % htmlTxt
    didYouMeanPos = string.find(htmlTxt, "Did you mean to go to")
    if -1 != didYouMeanPos:
        serverEndPos = string.find(url, "/", len("http://"))
        if dbgLevel > 0:
            print "found serverEnd at pos %d"  % serverEndPos
        if -1 == serverEndPos:
            return parsingFailed(url, htmlTxt)
        server = url[:serverEndPos]
        if dbgLevel > 0:
            print "Server: %s" % server
        if dbgLevel > 0:
            print "found 'Did you mean to' at pos %d"  % didYouMeanPos
        urlStart = string.find(htmlTxt, "<a href=\"", didYouMeanPos)
        if dbgLevel > 0:
            print "urlStart is %d" % urlStart
        if -1 == urlStart:
            return parsingFailed(url, htmlTxt)
        urlStart += len("<a href=\"")
        urlEnd = string.find(htmlTxt, "\"", urlStart)
        if dbgLevel > 0:
            print "urlEnd is %d" % urlEnd
        if -1 == urlEnd:
            return parsingFailed(url, htmlTxt)
        url = "%s%s" % (server, htmlTxt[urlStart:urlEnd])
        if dbgLevel > 0:
            print "url: %s" % url
        htmlTxt = getHttp(url, referer=gasBuddyUrl, dbgLevel=dbgLevel, cookieJar = jar, retryCount=2)
        if None == htmlTxt:
            return retrieveFailed(url)

    (resultType, resultBody) = parseGas(htmlTxt, url, dbgLevel=dbgLevel)

    if GAS_DATA == resultType:
        g_cache[zipCode] = url
        saveCache()

    return (resultType, resultBody)

def usage():
    print "usage: gasprices.py [-dump-cache] [zipCode] [-file fileName]"

def dumpCache():
    global g_cache
    print "Dumping cache:\n"
    for (zipCode,url) in g_cache.items():
        print "%s : %s" % (zipCode, url)

def main():
    fDumpCache = arsutils.fDetectRemoveCmdFlag("-dump-cache")
    if not fDumpCache:
        fDumpCache = arsutils.fDetectRemoveCmdFlag("--dump-cache")

    if fDumpCache:
        dumpCache()
        sys.exit(0)

    fileName = arsutils.getRemoveCmdArg("-file")


    if None != fileName:
        if 1 != len(sys.argv):
            usage()
            print sys.argv
            sys.exit(0)
        fo = open(fileName, "rb")
        htmlTxt = fo.read()
        fo.close()
        (resultType, resultBody) = parseGas(htmlTxt, url=fileName, dbgLevel=1)
    else:
        if 2 != len(sys.argv):
            usage()
            sys.exit(0)
        zipCode = sys.argv[1]
        print "zipCode: %s" % zipCode
        (resultType, resultBody) = getGasPricesForZip(cookielib.CookieJar(), zipCode, dbgLevel=1)

    if RETRIEVE_FAILED == resultType:
        print "retrieve failed"
    if PARSING_FAILED == resultType:
        htmlTxt = resultBody[1]
        #print htmlTxt
        print "parsing failed"
    if NO_RESULTS == resultType:
        print "no results"
    if LOCATION_UNKNOWN == resultType:
        print "location unknown"
    if GAS_DATA == resultType:
        print udfPrettyPrint(resultBody)

if __name__ == "__main__":
    main()
