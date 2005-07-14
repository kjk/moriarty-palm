import os, sys, getopt, cgi, urllib, string, httplib, cPickle
from xml.dom import minidom
import cookielib, arsutils
import multiUserSupport
from xml.dom.minidom import parse, parseString
import urllib, urllib2, random, time, socket
from httplib import HTTPConnection, HTTPException
from arsutils import log, exceptionAsStr, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC, Timer
import parserErrorLogger
from parserErrorLogger import logParsingFailure, makePathIfNeeded
from ResultType import *
from parserUtils import *
from definitionBuilder import *
from popupMenu import *
import xml.sax
import ebooks
from Retrieve import getHttp
from xml.sax.handler import *
from xml.sax.xmlreader import InputSource
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import InfoManCrypto

## siteID = "0" - U.S. and nothing more!!! becouse this will be hardcore, to cache aprox 20 * 7 MB of xmlData and stuff...

## START OF CHANGE IN RELEASE DATA ################################################################
## our IDs and stuff...
g_appIndex = 0
g_DevID  = ["Y2Y7C61RR7K98I8AXDZIP4D16JDBEQ", "E431K94JW4V62AJ85E4M9TR9CKHFE1"]
g_AppID  = ["NONEL8MD6172UH28C6YKOJLH16OILF", "FOKAF3826YV7K2IHOQ2PPF21159H1S"]
g_CertID = ["H96J45YE691$E159SN6MU-R4ODV8L1", "C11I62HG122$A9FB4T575-4BE413LQ"]

g_eBayItemUrl = "http://cgi.sandbox.ebay.com/ws/eBayISAPI.dll?ViewItem&item="

# for unsigned users use this one (sone test account)
g_unsignedUser  = "pisakowyludek2"
g_unsignedPwd   = "444444"
# token = None, on startup load token
#TODO: = None (and run initEBay() at startup)
g_unsignedToken = "AgAAAA**AQAAAA**aAAAAA**5hxUQg**nY+sHZ2PrBmdj6wVnY+sEZ2PrA2dj6wJnY+lCpKKowqdj6x9nY+seQ**d0wAAA**AAMAAA**I8XsxlIaNP4AEpWaKCtkVlgLVosXNw4ND/lvubZsW+uMLFw8cgeaCn2aPqQddaU8YVRm1gIlGIvusCZOQWhNc7GJwzgoaP45OjOeiWP22SZrPMbKU2nM1d2+0VXTPGCYdV9odpTqLMQRL+4yakby/xMmhZmm1UBrvk3PxGh8XY9fIgNanXrC2CpY6Tvgl81zbF56Hg/HzpnXk/737ZxY+eucaffyN7yyxhjoyrG9vwcG3GwrnjyZYslawX7Ykm8i5UIDFkiQ9zv+VNHYmGNfPJNGOyM/pULHETwaqHsEFNPb5F0kYJhU6Z6q77381+wI6pvslYotVXEwqpp8FK1U53S4jrVUwoV4fndex9lhoBvwf1YzdSIWiN/mzjeXchdbFjeRRi/NnTYeXZXo2VRl8YRHFnJ785LAy6nzYImL0VY6eixvMHhKBbOpmhVBFQEYup7yyrOhWcAhPG4FZ2tDroQv6YnuTZPxIx+3D7j/pTMsEBYR/rozwpCNWiZ/d2uDueWQQBf5tqMjzDQzV+4rWqUU4Ir9scMCyu0niYz5PhuAY7A4eySl+BaoHs1vShX/y+7R7TBwcZZ1+tT9tCrj7j5LEeFuMYsVtFpUK9bBuffnPl5YyWYXxRVs2Z2KanXMRJ8uq97dSKoYKlOedLEnUJakLP3KMME1brgcJzpoBPQr7GoGrYpoWY8eZEviiPaLXYFD5L/H8e2SYXr9nMftSrs1j5cr1fxe0nDg0D78oblFa9pJLfKvrKB7GA5aFVW5"
## https:// ##
g_host = "api.sandbox.ebay.com"
g_hostUrl = "/ws/api.dll"
g_reqCount = 0

g_fEbayInited = False

def _eBayIsCalling():
    global g_reqCount
    g_reqCount += 1
    ## TODO: change g_appIndex every 50 (48) requests. (get more than one ID set - as we have multiple ind. applications)
    pass

## END OF CHANGE IN RELEASE DATA ################################################################
## SOME GLOBAL DATA - cache #####################################################################
g_eBayPath = os.path.join(multiUserSupport.getServerStorageDir(), "ebay")
g_eBayCachePath = os.path.join(g_eBayPath, "cache")
g_eBayXmlPath = os.path.join(g_eBayPath, "xml")
g_eBayTokensFileName = os.path.join(g_eBayPath, "tokens.pic")

from parserErrorLogger import makePathIfNeeded

makePathIfNeeded(g_eBayPath)
makePathIfNeeded(g_eBayCachePath)
makePathIfNeeded(g_eBayXmlPath)

# store user tokens: <userId> : [token, expired]
g_tokens = {}


## END OF GLOBAL DATA - cache ###################################################################
## TOKENS FUNCTIONS #############################################################################
def _loadTokens():
    global g_tokens
    sys.stdout.write(" load tokens ")
    try:
        fo = open(g_eBayTokensFileName, "rb")
        g_tokens = cPickle.load(fo)
        fo.close()
    except:
        sys.stdout.write("(file not found) ")
    print "DONE"

def _saveTokens():
    fo = open(g_eBayTokensFileName, "wb")
    cPickle.dump(g_tokens, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    fo.close()

# return True if token is no longer valid, else return False
#  (if warning than return False, but mark this in g_tokens!)
def testTokenExpired(xmlOut, userId, logged):
    errorCode = False
    warning = False
    # error code 932
    # <HardExpirationWarning>2005-01-14 03:34:00</HardExpirationWarning>
    soup = BeautifulSoup()
    soup.feed(xmlOut)
    errors = soup.fetch("error")
    for error in errors:
        code = getAllTextFromTag(error.first("code"))
        if code == "932":
            errorCode = True
    hew = soup.first("hardexpirationwarning")
    if hew:
        warning = True
    # errorCode and warning informations
    if False == errorCode and False == warning:
        return False
    assert errorCode != warning
    if logged:
        if warning:
            global g_tokens
            g_tokens[userId][1] = True
            return False
        else:
            return True
    else:
        # global unsigned token will expire 1 time each 18 months...
        # so we can allow one critical error :)
        initToken()
        return False
    assert False

# called by server, and if return True, server append request with EBAY_REQUEST_PASSWORD
def isTokenExpired(userId):
    try:
        return g_tokens[userId][1]
    except:
        return False

## CROSS MODULES FUNCTIONS ######################################################################
def _linkTitle(gtxt, title, itemId, logged, modulesInfo, fullCategory=""):
    eBayLink = ""
    if itemId != "":
        eBayLink = "Hs+ebay:item;%s;%s" % (itemId, logged)
    if modulesInfo != None:
        popupItems = []
        music = False
        books = False
        movies = False
        catWords = fullCategory.split()
        if "Books" in catWords:
            books = True
        if "Movies" in catWords:
            movies = True
        if "Music" in catWords:
            music = True
        if eBayLink != "":
            popupItems.append(["View details", eBayLink, False, True, False])
        if modulesInfo['Amazon']:
            popupItems.append(["Search Amazon", "s+amazonsearch:Blended;;1;"+title, False, False, False])
        if modulesInfo['Lyrics'] and music:
            popupItems.append(["Search Lyrics","s+lyricssearch:;;"+title+";;",False,False,False])
        if modulesInfo['Netflix'] and movies:
            popupItems.append(["Search Netflix","s+netflixsearch:"+title+";Movie;?",False,False,False])
        if modulesInfo['ListsOfBests'] and (music or books or movies):
            popupItems.append(["Search Lists of Bests","s+listsofbestssearch:"+title+";Everything;Title",False,False,False])
        if modulesInfo['eBooks'] and books:
            link = ebooks.create_search_title_link(title, formats = None)
            popupItems.append(["Search eBooks",link,False,False,False])

        if len(popupItems) > 1 or (len(popupItems) > 0 and "" == eBayLink):
            gtxt.setHyperlink(buildPopupMenu(popupItems))
        elif eBayLink != "":
            gtxt.setHyperlink(eBayLink)
    else:
        if eBayLink != "":
            gtxt.setHyperlink(eBayLink)
    
## XML RETRIEVE FUNCTIONS #######################################################################
## generate headers for post request
def _generateHeaders(functionName, detailLevel, siteId):
    headers = {"X-EBAY-API-COMPATIBILITY-LEVEL": "349",
               "X-EBAY-API-SESSION-CERTIFICATE": (g_DevID[g_appIndex]+";"+g_AppID[g_appIndex]+";"+g_CertID[g_appIndex]).encode("utf-8"),
               "X-EBAY-API-DEV-NAME": g_DevID[g_appIndex].encode("utf-8"),
               "X-EBAY-API-APP-NAME": g_AppID[g_appIndex].encode("utf-8"),
               "X-EBAY-API-CERT-NAME": g_CertID[g_appIndex].encode("utf-8"),
               "X-EBAY-API-CALL-NAME": functionName.encode("utf-8"),
               "X-EBAY-API-SITEID": siteId.encode("utf-8"),
               "X-EBAY-API-DETAIL-LEVEL": detailLevel.encode("utf-8"),
               "Content-Type": "text/xml; charset=utf-8"}
    return headers

def _getEBayXmlHelper(xmlIn, functionName, detailLevel, siteId):
    conn = httplib.HTTPSConnection(g_host)
    conn.request("POST", g_hostUrl, xmlIn.encode("utf-8"), _generateHeaders(functionName, detailLevel, siteId))
    response = conn.getresponse()
    xmlOut = response.read()
    conn.close()
    return xmlOut

def _getEBayXmlHandleException(xmlIn, functionName, detailLevel, siteId):
    xmlOut = None
    try:
        xmlOut = _getEBayXmlHelper(xmlIn, functionName, detailLevel, siteId)
    except Exception, ex:
        txt = exceptionAsStr(ex)
        log(SEV_EXC, "failed to retrieve data for ebay\nFonction:%s\nreason:%s\n" % (functionName, txt))
    return xmlOut

def _getEBayXml(xmlIn, functionName, detailLevel, siteId):
    return _getEBayXmlHandleException(xmlIn, functionName, detailLevel, siteId)

## requestData for example: "<UserId>user</UserId>"
def _createRequestXml(functionName, token, requestData, detailLevel, siteId):
    xmlIn =   "<?xml version='1.0' encoding='utf-8'?>"+\
              "<request>"+\
              requestData+\
              "<RequestToken>" + token + "</RequestToken>"+\
              "<DetailLevel>" + detailLevel + "</DetailLevel>"+\
              "<ErrorLevel>1</ErrorLevel>"+\
              "<SiteId>" + siteId + "</SiteId>"+\
              "<Verb>" + functionName + "</Verb>"+\
              "</request>"
    return xmlIn

## use this function to get xml from ebay (and only this one)
def eBayCall(functionName, token, requestData="", detailLevel="0", siteId="0"):
    _eBayIsCalling()
    xmlIn = _createRequestXml(functionName, token, requestData, detailLevel, siteId)
    return _getEBayXml(xmlIn, functionName, detailLevel, siteId)

## check if there are any errors in DOM
## if there is error(s), return True and log them (send?)
## else return False
def checkErrors(dom):
    tag = dom.getElementsByTagName('Error')
    if (tag.count!=0):
        prettyErrors = ""
        for error in tag:
            prettyErrors += "\n"+error.toprettyxml("  ")+"\n"
        if len(prettyErrors) > 0:
            logParsingFailure("eBay", "?", htmlText=prettyErrors, url=None)
            log(SEV_EXC, "Errors in eBay response:\n%s\n" % (prettyErrors))
            return True
    return False

## check if there are any errors in soup
## if there is error(s), return True and log them (send?)
## else return False
def checkErrorsInSoup(soup):
    errors = soup.fetch("error")
    prettyErrors = ""
    for error in errors:
        prettyErrors += str(error)
    if len(prettyErrors) > 0:
        logParsingFailure("eBay", "?", htmlText=prettyErrors, url=None)
        log(SEV_EXC, "Errors in eBay response:\n%s\n" % (prettyErrors))
        return True
    return False

def getToken(user, pwd):
    requestData = "<RequestUserId>" + user + "</RequestUserId>"+\
                  "<RequestPassword>" + pwd +"</RequestPassword>"
    xmlOut = eBayCall("GetToken", "", requestData)
    if None == xmlOut:
        return MODULE_DOWN, None
    responseDOM = parseString(xmlOut)
    tag = responseDOM.getElementsByTagName('Code')
    if len(tag) > 0:
        for code in tag:
            if "35" == code.childNodes[0].data:
                return EBAY_UNKNOWN_LOGIN, None
    if checkErrors(responseDOM):
        return MODULE_DOWN, None
    # check for the <Token> tag and get it
    token = None
    if (responseDOM.getElementsByTagName('Token')!=[]):
        token = responseDOM.getElementsByTagName('Token')[0].childNodes[0].data
    # force garbage collection of the DOM object
    responseDOM.unlink()
    if None == token:
        return MODULE_DOWN, None
    return EBAY_LOGIN_OK, token

def getOfficialEbayTime():
    xmlOut = eBayCall("GeteBayOfficialTime", g_unsignedToken)
    responseDOM = parseString(xmlOut)
    if checkErrors(responseDOM):
        return None
    time = ""
    if (responseDOM.getElementsByTagName('EBayTime')!=[]):
        time = responseDOM.getElementsByTagName('EBayTime')[0].childNodes[0].data
    # force garbage collection of the DOM object
    responseDOM.unlink()
    return time

def _sortByFirstElement(el1, el2):
    # el1 and el2 are tuples with first element being category name, 
    return cmp(el1[0], el2[0])

def buildBrowseListFromNode(node):
    global g_categories
    item = g_categories[node]
    browsePath = []
    browsePath.insert(0,[item[0], node])
    it = item
    actNode = node
    while it[1] != actNode and it[1] != "":
        actNode = it[1]
        it = g_categories[actNode]
        browsePath.insert(0,[it[0], actNode])
    return browsePath

def browseNode(args, modulesInfo, userId):
    if len(args.split(";")) != 2:
        return INVALID_REQUEST, None
    node, logged = args.split(";")
    global g_categories
    item = None
    try:
        item = g_categories[node]
    except:
        parserErrorLogger.mail("eBay category node invalid", "Node:"+node)
        return NO_RESULTS, None
    if len(item[2]) > 0:
        df = Definition()
        browsePath = buildBrowseListFromNode(node)

        searchText = "Home / "
        df.TextElement("Home", link="ebayform:main")
        df.TextElement(" / ")
        for br in browsePath[:-1]:
            df.TextElement(br[0], link="s+ebay:browse;"+br[1]+";"+logged)
            df.TextElement(" / ")
            searchText += br[0]+" / "

        df.TextElement(item[0])
        searchText += item[0]

        df.LineBreakElement(1,2)

        childItems = []
        for childNode in item[2]:
            childItems.append([g_categories[childNode][0], "s+ebay:browse;"+childNode+";"+logged])
        # sort
        childItems.sort(_sortByFirstElement)
        for child in childItems:
            df.BulletElement(False)
            df.TextElement(child[0], link=child[1])
            df.PopParentElement()

        controls = []
        searchString = "s+ebay:search;%s;%s;" % (node, logged)
        controls.append(["H", searchText.replace(" / ","/").replace("Home/","")])
        searchText = searchText.replace("Home / Browse / ", "Search ").replace("Home / Browse", "Search") + " for:"
        controls.append(["B", "S", searchText, searchString])
        return EBAY_DATA, universalDataFormatWithDefinition(df, controls)
    else:
        return searchEBay(args+";", modulesInfo, userId)

def getItemText(domItem, name):
    try:
        text = domItem.getElementsByTagName(name)[0].childNodes[0].data
    except:
        text = ""
    return text.encode("latin-1", "ignore")

def addListItemToDefinition(df, item, modulesInfo, logged, fullCategories):
    #print item.toprettyxml(" ")
    itemId = getItemText(item, 'Id')
    title = getItemText(item, 'Title')
    subtitleText = getItemText(item, 'SubtitleText')
    localizedCurrentPrice = getItemText(item, 'LocalizedCurrentPrice')
    if "" == localizedCurrentPrice:
        currency = getItemText(item, 'Currency')
        currentPrice = getItemText(item, 'CurrentPrice')
        if currency == "1":
            localizedCurrentPrice = "$"+currentPrice
        else:
            if "" == currency:
                currencyId = getItemText(item, 'CurrencyId')
                localizedCurrentPrice = currencyId + currentPrice
            if "" == localizedCurrentPrice:
                localizedCurrentPrice = "?"+currentPrice
    
    startTime = getItemText(item, 'StartTime')
    endTime = getItemText(item, 'EndTime')
    BINPrice = getItemText(item, 'BINPrice')

    timeLeftText = ""
    timeLeft = None
    try:
        timeLeft = item.getElementsByTagName('TimeLeft')[0]
    except:
        pass
    if timeLeft != None:
        hours = int(getItemText(timeLeft, 'Hours'))
        days = int(getItemText(timeLeft, 'Days'))
        minutes = int(getItemText(timeLeft, 'Minutes'))
        seconds = int(getItemText(timeLeft, 'Seconds'))
        timeLeftText = timeToText(days, hours, minutes, seconds)

    df.BulletElement(False)
    link = "Hs+ebay:item;%s;%s" % (itemId, logged)
    gtxt = df.TextElement(title)
    _linkTitle(gtxt, title, itemId, logged, modulesInfo, fullCategories)
    if "" != subtitleText:
        df.TextElement(" "+subtitleText)
    if "" != localizedCurrentPrice:
        gtxt = df.TextElement(localizedCurrentPrice)
        gtxt.setJustification(justRightLast)
    if "" != timeLeftText and "0 seconds" != timeLeftText:
        df.LineBreakElement()
        df.TextElement("Time left: "+timeLeftText)

    df.PopParentElement()
    

def parseSearchResults(xmlOut, modulesInfo, logged, argsTable):
    dom = parseString(xmlOut)
    if checkErrors(dom):
        return MODULE_DOWN, None
    items = dom.getElementsByTagName('Item')
    count = int(dom.getElementsByTagName('Count')[-1].childNodes[0].data)
    grandTotal = int(dom.getElementsByTagName('GrandTotal')[-1].childNodes[0].data)
    pageNumber = int(dom.getElementsByTagName('PageNumber')[-1].childNodes[0].data)

    if len(items) != count:
        dom.unlink()
        return UNKNOWN_FORMAT, None

    if count == 0:
        dom.unlink()
        return NO_RESULTS, None

    # build header
    df = Definition()
    browsePath = buildBrowseListFromNode(argsTable[0])
    searchText = "Home / "
    historyText = ""
    df.TextElement("Home", link="ebayform:main")
    df.TextElement(" / ")
    for br in browsePath[:-1]:
        df.TextElement(br[0], link="s+ebay:browse;"+br[1]+";"+logged)
        df.TextElement(" / ")
        searchText += br[0]+" / "

    br = browsePath[-1]
    gtxt = df.TextElement(br[0])
    searchText += br[0]
    if argsTable[2].strip() == "":
        historyText = searchText.replace(" / ","/").replace("Home/","")
    else:
        link="s+ebay:browse;"+br[1]+";"+logged
        gtxt.setHyperlink(link)
        df.TextElement(" / Search for: '%s'" % argsTable[2].strip())
        historyText = "Search for " + argsTable[2].strip()
    df.LineBreakElement(1,2)
    # build items
    for item in items:
        addListItemToDefinition(df, item, modulesInfo, logged, searchText[5:])
    df.LineBreakElement()

    # controls
    controls = []
    searchString = "s+ebay:search;%s;%s;" % (argsTable[0], argsTable[1])
    searchText = searchText.replace("Home / Browse / ", "Search ").replace("Home / Browse", "Search") + " for:"
    controls.append(["B", "S", searchText, searchString])
    controls.append(["H", historyText])

    dom.unlink()
    return EBAY_DATA, universalDataFormatWithDefinition(df, controls)

def timeToText(days, hours, minutes, seconds, howMany=2, showNextZero=True):
    oneTexts = ["1 day ", "1 hour ", "1 minute ", "1 second "]
    manyTexts = ["%d days ", "%d hours ", "%d minutes ", "%d secounds "]
    timeParts = [days, hours, minutes, seconds]
    text = ""
    for i in range(0,4):
        if howMany == 0:
            return text.strip()
        if timeParts[i] == 1:
            text += oneTexts[i]
        elif timeParts[i] > 1:
            text += manyTexts[i] % timeParts[i]
        elif showNextZero and "" != text:
            text += manyTexts[i] % timeParts[i]
        if "" != text:
            howMany -= 1
    if "" == text:
        return "0 seconds"
    return text.strip()

def parseItem(xmlOut, modulesInfo, logged):
    dom = parseString(xmlOut)
    if checkErrors(dom):
        return MODULE_DOWN, None

    item = dom.getElementsByTagName('Item')[0]
    itemName = getItemText(item, 'Title')
    itemId = getItemText(item, 'Id')
        
    df = Definition()
    df.TextElement("Home", link="ebayform:main")
    df.TextElement(" / ")
    gtxt = df.TextElement(itemName, style=styleNameBold)


    category = item.getElementsByTagName('Category')[0]
    categoryFullName = getItemText(category, 'CategoryFullName')
    _linkTitle(gtxt, itemName, "", logged, modulesInfo, categoryFullName)

    updateLink = "hs+ebay:item;%s;%s" % (itemId,logged)
    df.TextElement(" (")
    df.TextElement("Update", link=updateLink)
    df.TextElement(")")

    df.LineBreakElement(1,2)
    # subtitle text
    subtitleText = getItemText(item, 'SubtitleText')
    if subtitleText != "":
        df.LineBreakElement()
        df.TextElement(subtitleText)
        df.LineBreakElement(1,2)
        
    # prices...
    quantity = getItemText(item, 'Quantity')
    currencySymbol = getItemText(item, 'CurrencyId') # should be '$'
    currentPrice = getItemText(item, 'CurrentPrice')
    buyItNowPrice = getItemText(item, 'BuyItNowPrice')
    startPrice = getItemText(item, 'StartPrice')

    # times (get) to avoid Buy links for timeout items
    startTime = getItemText(item, 'StartTime')
    timeLeft = item.getElementsByTagName('TimeLeft')[0]
    hours = int(getItemText(timeLeft, 'Hours'))
    days = int(getItemText(timeLeft, 'Days'))
    minutes = int(getItemText(timeLeft, 'Minutes'))
    seconds = int(getItemText(timeLeft, 'Seconds'))
    leftText = timeToText(days, hours, minutes, seconds)
    timeOut = False
    if leftText == "" or leftText == "0 seconds":
        timeOut = True

    if "" != startPrice and "0.00" != startPrice:
        df.LineBreakElement()
        df.TextElement("Start price:")
        gtxt = df.TextElement("%s%s" % (currencySymbol ,startPrice))
        gtxt.setJustification(justRightLast)
        df.LineBreakElement()
        df.TextElement("Current price: ")
        gtxt = df.TextElement("%s%s" % (currencySymbol ,currentPrice))
        gtxt.setJustification(justRightLast)
        if logged == 'T' and not timeOut:
            minimumToBid = getItemText(item, 'MinimumToBid')
            gtxt.setHyperlink(buildPopupMenu([["Bid this item", "ebayform:bid;%s;%s;%s" % (itemId,currencySymbol,minimumToBid), False, False, False]]))

    if "" != buyItNowPrice and "0.00" != buyItNowPrice:
        df.LineBreakElement()
        df.TextElement("Buy it now price: ")
        gtxt = df.TextElement("%s%s" % (currencySymbol ,buyItNowPrice))
        gtxt.setJustification(justRightLast)
        if logged == 'T' and not timeOut:
            gtxt.setHyperlink(buildPopupMenu([["Buy it now", "s+ebayno:buy;"+itemId, False, False, False]]))

    if "" != quantity and "0" != quantity:
        df.LineBreakElement()
        df.TextElement("Quantity: "+quantity)
    df.LineBreakElement(1,2)

    # times
    df.LineBreakElement()
    if timeOut:
        df.TextElement("Auction ended")
    else:
        df.TextElement("Left: "+leftText)
    df.LineBreakElement(1,2)

    # location
    location = getItemText(item, 'Location')
    df.LineBreakElement()
    df.TextElement("Item location: "+location)
    df.LineBreakElement(1,2)

    ## TODO: more - buy/ ships/ ...
    fo = open('item.xml','wt')
    fo.write(xmlOut)
    fo.close()

    if logged == 'T':
        df.LineBreakElement()
        df.TextElement("Watch this item", link="ebayform:resend;s+ebayno:watch;%s;" % itemId)
        df.LineBreakElement(1,2)

    # controls    
    controls = []
    controls.append(["H", itemName])
    controls.append(["B", "U", updateLink])
    dom.unlink()
    return EBAY_DATA, universalDataFormatWithDefinition(df, controls)

def parseMyEBay(xmlOut, modulesInfo):
    dom = parseString(xmlOut)
    if checkErrors(dom):
        return MODULE_DOWN, None

    actTime = getItemText(dom, 'EBayTime')
    
    df = Definition()
    df.TextElement("Home", link="ebayform:main")
    df.TextElement(" / ")
    df.TextElement("My eBay", style=styleNameBold)
    df.LineBreakElement()
    df.TextElement(actTime)
    # update link
    updateLink = "hs+ebay:myebay"
    df.TextElement(" (")
    df.TextElement("Update", link=updateLink)
    df.TextElement(")")
    df.LineBreakElement(1,2)

    try:
        biddingWatching = dom.getElementsByTagName('BiddingWatching')[0]
    except:
        biddingWatching = None
    try:
        activeList = dom.getElementsByTagName('ActiveList')[0]
    except:
        activeList = None
    try:
        wonList = dom.getElementsByTagName('WonList')[0]
    except:
        wonList = None
    try:
        lostList = dom.getElementsByTagName('LostList')[0]
    except:
        lostList = None
    try:
        watchList = dom.getElementsByTagName('WatchList')[0]
    except:
        watchList= None

    anyItems = False
    lists = [activeList, wonList, lostList, watchList]
    names = ["Active:", "Won:", "Lost:", "Watch:"]
    for index in range(0,4):
        if lists[index] != None:
            count = int(getItemText(lists[index], 'Count'))
            if count > 0:
                anyItems = True
                df.LineBreakElement()
                df.TextElement(names[index], style=styleNameHeader)
                for item in lists[index].getElementsByTagName('Item'):
                    addListItemToDefinition(df, item, modulesInfo, 'T', "")
                df.LineBreakElement(1,2)
    if not anyItems:
        return NO_RESULTS, None

    # controls    
    controls = []
    controls.append(["H", "My eBay "+actTime])
    controls.append(["B", "U", updateLink])
    dom.unlink()
    return EBAY_DATA, universalDataFormatWithDefinition(df, controls)

## test if i can call this function...
g_categoryListings = {}
def listNode(token, category, logged, modulesInfo, userId):
    if category == "0":
        return NO_RESULTS, None
    global g_categoryListings
    xmlOut = None
    try:
        item = g_categoryListings[category]
        if time.time() < item[1] + 60*60:
            xmlOut = item[0]
    except:
        pass
    if None == xmlOut:
        callXml = "<CategoryId>%s</CategoryId>" % category
        callXml += ""
        xmlOut = eBayCall("GetCategoryListings", token, callXml)
        if None == xmlOut:
            return MODULE_DOWN, None
        if testTokenExpired(xmlOut, userId, logged):
            return EBAY_REQUEST_PASSWORD, None
        g_categoryListings[category] = [xmlOut, time.time()]
        
    resType, resBody = parseSearchResults(xmlOut, modulesInfo, logged, [category, logged, ""])
    if resType == UNKNOWN_FORMAT:
        logParsingFailure("eBay search or browse (cat listing)", category, xmlOut, "")        
    return resType, resBody

def searchEBay(args, modulesInfo, userId):
    # search args: <category "0"-all>;<logged>;<keywords>[;other?]
    try:
        table = args.split(";")
        category = table[0]
        logged = table[1]
        keywords = table[2]
        # else can be used to force update (not from history cache) on palm
    except:
        return INVALID_REQUEST, None
    # change logged if == '?'
    if logged == '?':
        global g_tokens
        try:
            token = g_tokens[userId][0]
            logged = 'T'
        except:
            logged = 'F'
        table[1] = logged
    # get token
    status, token = _getRequestToken(userId, logged)
    if status != EBAY_LOGIN_OK:
        return status, None
    if keywords.strip() == "":
        return listNode(token, category, logged, modulesInfo, userId)
    callXml = "<Query>%s</Query><MaxResults>5</MaxResults>" % keywords
    if category != "0":
        callXml += "<Category>%s</Category>" % category
    xmlOut = eBayCall("GetSearchResults", token, callXml)
    if None == xmlOut:
        return MODULE_DOWN, None
    if testTokenExpired(xmlOut, userId, logged):
        return EBAY_REQUEST_PASSWORD, None
    resType, resBody = parseSearchResults(xmlOut, modulesInfo, logged, table)
    if resType == UNKNOWN_FORMAT:
        logParsingFailure("eBay search", args, xmlOut, "")        
    return resType, resBody

def _getRequestToken(userId, logged):
    token = None
    if logged == "T":
        try:
            token = g_tokens[userId][0]
        except:
            return EBAY_REQUEST_PASSWORD, None
    elif logged == "F":
        token = g_unsignedToken
    else:
        return INVALID_REQUEST, None
    return EBAY_LOGIN_OK, token

def itemEBay(args, modulesInfo, userId):
    # search args: <category "0"-all>;<logged>;<keywords>[;other?]
    try:
        table = args.split(";")
        itemId = table[0]
        logged = table[1]
    except:
        return INVALID_REQUEST, None
    # get token
    status, token = _getRequestToken(userId, logged)
    if status != EBAY_LOGIN_OK:
        return status, None

    callXml = "<Id>%s</Id>" % itemId
    xmlOut = eBayCall("GetItem", token, callXml)
    if None == xmlOut:
        return MODULE_DOWN, None
    if testTokenExpired(xmlOut, userId, logged):
        return EBAY_REQUEST_PASSWORD, None
    resType, resBody = parseItem(xmlOut, modulesInfo, logged)
    if resType == UNKNOWN_FORMAT:
        logParsingFailure("eBay item", args, xmlOut, "")        
    return resType, resBody

def myEBay(args, modulesInfo, userId):
    # get token
    status, token = _getRequestToken(userId, 'T')
    if status != EBAY_LOGIN_OK:
        return status, None

    callXml = ""
    xmlOut = eBayCall("GetMyeBay", token, callXml)
    if None == xmlOut:
        return MODULE_DOWN, None
    if testTokenExpired(xmlOut, userId, 'T'):
        return EBAY_REQUEST_PASSWORD, None

    resType, resBody = parseMyEBay(xmlOut, modulesInfo)

    if resType == UNKNOWN_FORMAT:
        logParsingFailure("eBay myeBay", args, xmlOut, "")        
    return resType, resBody

## RETRIEVER
def retrieveEBay(fieldValue, modulesInfo, userId):
    global g_fEbayInited
    if not g_fEbayInited:
        return MODULE_DOWN, None

    index = fieldValue.find(";")
    if -1 != index:
        foo = fieldValue[:index]
        args = fieldValue[index+1:]
    else:
        foo = fieldValue
        args = ""

    if "browse" == foo:
        return browseNode(args, modulesInfo, userId)
    if "search" == foo:
        return searchEBay(args, modulesInfo, userId)
    if "item" == foo:
        return itemEBay(args, modulesInfo, userId)
    if "myebay" == foo:
        return myEBay(args, modulesInfo, userId)

    return INVALID_REQUEST, None


# first step in 'buy it now' transaction
def buyItNow1(itemId, userId):
    status, token = _getRequestToken(userId, 'T')
    if status != EBAY_LOGIN_OK:
        return status, None

    callXml = "<Id>%s</Id>" % itemId
    xmlOut = eBayCall("GetItem", token, callXml)
    if None == xmlOut:
        return MODULE_DOWN, None
    if testTokenExpired(xmlOut, userId, 'T'):
        return EBAY_REQUEST_PASSWORD, None

    dom = parseString(xmlOut)
    if checkErrors(dom):
        return MODULE_DOWN, None

    item = dom.getElementsByTagName('Item')[0]
    itemName = getItemText(item, 'Title')
    if itemId != getItemText(item, 'Id'):
        return MODULE_DOWN, None
        
    df = Definition()
    df.TextElement("Home", link="ebayform:main")
    df.LineBreakElement()
    df.TextElement("You are going to buy:")
    df.LineBreakElement()
    df.TextElement(itemName, style=styleNameBold)
    df.LineBreakElement(1,2)
    # subtitle text
    subtitleText = getItemText(item, 'SubtitleText')
    if subtitleText != "":
        df.TextElement(subtitleText)
        df.LineBreakElement(1,2)
        

    currencySymbol = getItemText(item, 'CurrencyId') # should be '$'
    buyItNowPrice = getItemText(item, 'BuyItNowPrice')

    if "" == buyItNowPrice or "0.00" == buyItNowPrice:
        return MODULE_DOWN, None
    
    df.LineBreakElement()
    df.TextElement("You will pay ")
    df.TextElement("%s%s" % (currencySymbol ,buyItNowPrice), style=styleNameBold)
    df.TextElement(" for that item.")
    df.LineBreakElement(1,2)

    # info about location and shipping...


    # location
    location = getItemText(item, 'Location')
    df.LineBreakElement()
    df.TextElement("Item location: "+location)
    df.LineBreakElement(1,2)

    # TODO:

    # buy link    
    buyLink = "ebayform:resend;s+ebayno:buy2;%s;" % itemId
    gtxt = df.TextElement("BUY", style=styleNamePageTitle, link=buyLink)
    gtxt.setJustification(justCenter)

    dom.unlink()
    return EBAY_DATA_NO_CACHE, universalDataFormatWithDefinition(df, [])

# second step in 'buy it now' transaction
def buyItNow2(args, userId):
    try:
        itemId, cred = args.split(";")        
    except:
        return INVALID_REQUEST, None

    decrypt = InfoManCrypto.decrypt_hexbin(cred)
    login, pwd = decrypt.split(";")
    # now press [buy it now >] button on site...
    url = g_eBayItemUrl + itemId
    jar = cookielib.CookieJar()
    htmlTxt = getHttp(url, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["1. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    form = soup.first("form", {"method":"get", "action":"http://offer.%"})
    if not form:
        span = soup.first("span", {"class":"sectiontitle"})
        if span:
            if getAllTextFromTag(span) == "Item has ended":
                df = Definition()
                df.TextElement("Home", link="ebayform:main")
                df.LineBreakElement(3,2)
                df.TextElement("Item has ended. We're sorry.")
                return EBAY_DATA_NO_CACHE, universalDataFormatWithDefinition(df, [])
        return MODULE_DOWN, ["2. no form", htmlTxt]
    url = form['action']
    getData = ""
    for inp in soup.fetch("input"):
        name = ""
        value = ""
        try:
            name = inp['name']
            value = inp['value']
        except:
            pass
        if name != "" and name != "Submit":
            if value == "BinConfirm":
                getData = ""
            getData += "&%s=%s" % (urllib.quote(name), urllib.quote(value))
    if len(getData) == 0:
        return MODULE_DOWN, ["3. no inputs", htmlTxt]
    url += "?" + getData[1:]
    
    htmlTxt = getHttp(url, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["4. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    form = soup.first("form", {"method":"post", "name":"SignInForm"})
    if not form:
        return MODULE_DOWN, ["5. no form", htmlTxt]
    url = form['action']
    postData = {}
    for inp in soup.fetch("input"):
        name = ""
        value = ""
        try:
            name = inp['name']
            value = inp['value']
        except:
            pass
        if name != "" and name != "Submit":
            if value == "SignInWelcome":
                postData = {}
            postData[name] = value.replace("&amp;","&")
    if len(postData) == 0:
        return MODULE_DOWN, ["6. no input", htmlTxt]
    postData['userid'] = login
    postData['pass'] = pwd

    htmlTxt = getHttp(url, postData=postData, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["7. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # redirect...
    aList = soup.fetch("a", {"href":"%"})
    url = aList[-1]['href'].replace("&amp;","&")

    htmlTxt = getHttp(url, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["8. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)


    postData = {}
    form = soup.first("form")
    if not form:
        return MODULE_DOWN, ["9. no form", htmlTxt]
    url = form['action']
    postData = {}
    for inp in soup.fetch("input"):
        name = ""
        value = ""
        try:
            name = inp['name']
            value = inp['value']
        except:
            pass
        if name != "" and name != "BIN_button":
            postData[name] = value.replace("&amp;","&")

    htmlTxt = getHttp(url, postData=postData, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["10. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    span = soup.first("span", {"class":"pagetitle"})
    if span:
        text = getAllTextFromTag(span)
        if text == "Buy It Now Confirmation":
            df = Definition()
            df.TextElement("You have buy this item.", style=styleNamePageTitle)
            df.LineBreakElement(3,2)
            df.TextElement("Press ")
            df.TextElement("Home", link="ebayform:main")
            df.TextElement(" to back to eBay module main page.")
            return EBAY_DATA_NO_CACHE, universalDataFormatWithDefinition(df, [])
    
    return MODULE_DOWN, ["11. no confirmation", htmlTxt]

# first step in bid transaction
def bid1(args, userId):
    itemId, userPrice = args.split(";")
    status, token = _getRequestToken(userId, 'T')
    if status != EBAY_LOGIN_OK:
        return status, None

    callXml = "<Id>%s</Id>" % itemId
    xmlOut = eBayCall("GetItem", token, callXml)
    if None == xmlOut:
        return MODULE_DOWN, None
    if testTokenExpired(xmlOut, userId, 'T'):
        return EBAY_REQUEST_PASSWORD, None

    dom = parseString(xmlOut)
    if checkErrors(dom):
        dom.unlink()
        return MODULE_DOWN, None

    item = dom.getElementsByTagName('Item')[0]
    itemName = getItemText(item, 'Title')
    if itemId != getItemText(item, 'Id'):
        dom.unlink()
        return MODULE_DOWN, None
        
    df = Definition()
    df.TextElement("Home", link="ebayform:main")
    df.LineBreakElement()
    df.TextElement("You are going to place bid for:")
    df.LineBreakElement()
    df.TextElement(itemName, style=styleNameBold)
    df.LineBreakElement(1,2)
    # subtitle text
    subtitleText = getItemText(item, 'SubtitleText')
    if subtitleText != "":
        df.TextElement(subtitleText)
        df.LineBreakElement(1,2)
        
    currencySymbol = getItemText(item, 'CurrencyId') # should be '$'
    currentPrice = getItemText(item, 'CurrentPrice')
    minimumToBid = getItemText(item, 'MinimumToBid')
    if float(minimumToBid) > float(userPrice):
        df = Definition()
        df.TextElement("Home", link="ebayform:main")
        df.LineBreakElement()
        df.TextElement("Your bid was not enought. You need to ")
        df.TextElement("place bid", link="ebayform:bid;%s;%s;%s" % (itemId,currencySymbol,minimumToBid))
        df.TextElement(" higher than %s%s." % (currencySymbol, minimumToBid))
        dom.unlink()
        return EBAY_DATA_NO_CACHE, universalDataFormatWithDefinition(df, [])
    
    df.LineBreakElement()
    df.TextElement("Your maximum bid for this item is ")
    df.TextElement("%s%s" % (currencySymbol ,userPrice), style=styleNameBold)
    df.TextElement(".")
    df.LineBreakElement(1,2)

    # info about location and shipping...


    # location
    location = getItemText(item, 'Location')
    df.LineBreakElement()
    df.TextElement("Item location: "+location)
    df.LineBreakElement(1,2)

    # TODO:
    

    # buy link    
    buyLink = "ebayform:resend;s+ebayno:bid2;%s;%s;" % (itemId, userPrice)
    gtxt = df.TextElement("PLACE BID", style=styleNamePageTitle, link=buyLink)
    gtxt.setJustification(justCenter)
    dom.unlink()
    return EBAY_DATA_NO_CACHE, universalDataFormatWithDefinition(df, [])

# second step in bid transaction
def bid2(args, userId):
    try:
        itemId, userPrice, cred = args.split(";")        
    except:
        return INVALID_REQUEST, None

    decrypt = InfoManCrypto.decrypt_hexbin(cred)
    login, pwd = decrypt.split(";")
    # now press [place bid >] button on site...
    url = g_eBayItemUrl + itemId
    jar = cookielib.CookieJar()
    htmlTxt = getHttp(url, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["1. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    form = soup.first("form", {"method":"get", "action":"http://offer.%"})
    if not form:
        span = soup.first("span", {"class":"sectiontitle"})
        if span:
            if getAllTextFromTag(span) == "Item has ended":
                df = Definition()
                df.TextElement("Home", link="ebayform:main")
                df.LineBreakElement(3,2)
                df.TextElement("Item has ended. We're sorry.")
                return EBAY_DATA_NO_CACHE, universalDataFormatWithDefinition(df, [])
        return MODULE_DOWN, ["2. no form", htmlTxt]
    url = form['action']
    getData = ""
    getDataTemp = ""
    for inp in soup.fetch("input"):
        name = ""
        value = ""
        try:
            name = inp['name']
            value = inp['value']
        except:
            pass
        if name != "" and name != "Submit":
            if value == "MakeBid":
                getDataTemp = ""
            if value == "BinConfirm":
                getData = getDataTemp
                getDataTemp = ""
            getDataTemp += "&%s=%s" % (urllib.quote(name), urllib.quote(value))
    if len(getData) == 0:
        getData = getDataTemp
    if len(getData) == 0:
        return MODULE_DOWN, ["3. no inputs", htmlTxt]
    url += "?" + getData[1:]
    
    htmlTxt = getHttp(url, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["4. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    form = soup.first("form", {"method":"post", "name":"SignInForm"})
    if not form:
        return MODULE_DOWN, ["5. no form", htmlTxt]
    url = form['action']
    postData = {}
    for inp in soup.fetch("input"):
        name = ""
        value = ""
        try:
            name = inp['name']
            value = inp['value']
        except:
            pass
        if name != "" and name != "Submit":
            if value == "SignInWelcome":
                postData = {}
            postData[name] = value.replace("&amp;","&")
    if len(postData) == 0:
        return MODULE_DOWN, ["6. no input", htmlTxt]
    postData['userid'] = login
    postData['pass'] = pwd

    htmlTxt = getHttp(url, postData=postData, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["7. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # redirect...
    aList = soup.fetch("a", {"href":"%"})
    url = aList[-1]['href'].replace("&amp;","&")

    htmlTxt = getHttp(url, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["8. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    postData = {}

    form = soup.first("form")
    if not form:
        return MODULE_DOWN, ["9. no form", htmlTxt]
    url = form['action']
    postData = {}
    for inp in soup.fetch("input"):
        name = ""
        value = ""
        try:
            name = inp['name']
            value = inp['value']
        except:
            pass
        if name != "":
            postData[name] = value.replace("&amp;","&")
    postData["maxbid"] = userPrice
    htmlTxt = getHttp(url, postData=postData, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["10. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # confirm...
    postData = {}
    form = soup.first("form")
    if not form:
        return MODULE_DOWN, ["11. no form", htmlTxt]
    url = form['action']
    postData = {}
    for inp in soup.fetch("input"):
        name = ""
        value = ""
        try:
            name = inp['name']
            value = inp['value']
        except:
            pass
        if name != "" and name != "BIN_button": # they have BIN_button, but should be Bid_button :)
            postData[name] = value.replace("&amp;","&")
    htmlTxt = getHttp(url, postData=postData, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["12. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    span = soup.first("span", {"class":"pagetitle"})
    if span:
        text = getAllTextFromTag(span)
        if text == "Bid Confirmation":
            df = Definition()
            df.TextElement("You have place bid for this item.", style=styleNamePageTitle)
            tdList = soup.fetch("td", {"nowrap":"yes"})
            for ind in range(len(tdList)):
                text = getAllTextFromTag(tdList[ind])
                if text in ["Your maximum bid:", "Current bid:"]:
                    text2 = getAllTextFromTag(tdList[ind+1])
                    df.TextElement(text + " " + text2)
            df.LineBreakElement(3,2)
            df.TextElement("Press ")
            df.TextElement("Home", link="ebayform:main")
            df.TextElement(" to back to eBay module main page.")
            return EBAY_DATA_NO_CACHE, universalDataFormatWithDefinition(df, [])
    
    return MODULE_DOWN, ["13. no confirmation", htmlTxt]

# watch item
def watch(args, userId):
    try:
        itemId, cred = args.split(";")
    except:
        return INVALID_REQUEST, None

    decrypt = InfoManCrypto.decrypt_hexbin(cred)
    login, pwd = decrypt.split(";")
    # now press watch link on site...
    url = g_eBayItemUrl + itemId
    jar = cookielib.CookieJar()
    htmlTxt = getHttp(url, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["1. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    url = ""
    aList = soup.fetch("a", {"title":"Keep%"})
    for aItem in aList:
        if getAllTextFromTag(aItem) == "Watch this item":
            url = aItem['href'].replace("&amp;","&")
            break

    if url == "":
        return MODULE_DOWN, ["2. no watch link", htmlTxt]

    htmlTxt = getHttp(url, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["4. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    form = soup.first("form", {"method":"post", "name":"SignInForm"})
    if not form:
        form = soup.first("form", {"method":"post", "action":"http://signin.%"})
        # they added sth like this?
        url = form['action'].replace("&amp;","&")
        postData = {}
        next = form.next
        submitFound = False
        while next and not submitFound:
            if isinstance(next, Tag):
                if next.name == "input":
                    try:
                        value = next['value']
                        name = next['name']
                    except:
                        pass
                    if value != "Sign In >":
                        postData[name] = value
                    else:
                        submitFound = True
            next = next.next
        htmlTxt = getHttp(url, postData=postData, cookieJar=jar)
        if None == htmlTxt:
            return MODULE_DOWN, ["4,5. no html", htmlTxt]
        soup = BeautifulSoup()
        soup.feed(htmlTxt)
            
    form = soup.first("form", {"method":"post", "name":"SignInForm"})
    if not form:
        return MODULE_DOWN, ["5. no form", htmlTxt]
    url = form['action'].replace("&amp;","&")
    postData = {}
    for inp in soup.fetch("input"):
        name = ""
        value = ""
        try:
            name = inp['name']
            value = inp['value']
        except:
            pass
        if name != "" and name != "Submit":
            if value == "SignInWelcome":
                postData = {}
            postData[name] = value.replace("&amp;","&")
    if len(postData) == 0:
        return MODULE_DOWN, ["6. no input", htmlTxt]
    postData['userid'] = login
    postData['pass'] = pwd

    htmlTxt = getHttp(url, postData=postData, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["7. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # redirect...
    aList = soup.fetch("a", {"href":"%"})
    url = aList[-1]['href'].replace("&amp;","&").replace("&amp;","&")
    htmlTxt = getHttp(url, cookieJar=jar)
    if None == htmlTxt:
        return MODULE_DOWN, ["7,5. no html", htmlTxt]
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    spanList = soup.fetch("span", {"class":"standard"})
    for span in spanList:
        text = getAllTextFromTag(span)
        if -1 != text.find("This item is being watched"):
            df = Definition()
            df.TextElement("This item is being watched in ")
            df.TextElement("My eBay.", link="hs+ebay:myebay")
            df.LineBreakElement(3,2)
            df.TextElement("Press ")
            df.TextElement("Home", link="ebayform:main")
            df.TextElement(" to back to eBay module main page.")
            return EBAY_DATA_NO_CACHE, universalDataFormatWithDefinition(df, [])
    
    return MODULE_DOWN, ["8. no confirmation", htmlTxt]

def retrieveEBayNoCache(fieldValue, modulesInfo, userId):
    global g_fEbayInited
    if not g_fEbayInited:
        return MODULE_DOWN, None

    index = fieldValue.find(";")
    if -1 != index:
        foo = fieldValue[:index]
        args = fieldValue[index+1:]
        if "buy" == foo:
            return buyItNow1(args, userId)
        if "buy2" == foo:
            res, body = buyItNow2(args, userId)
            if res == MODULE_DOWN:
                if body != None:
                    logParsingFailure("eBay buy it now", args, body[1], body[0])
                body = None
            return res, body
        if "bid" == foo:
            return bid1(args, userId)
        if "bid2" == foo:
            res, body = bid2(args, userId)
            if res == MODULE_DOWN:
                if body != None:
                    logParsingFailure("eBay bid", args, body[1], body[0])
                body = None
            return res, body
        if "watch" == foo:
            res, body = watch(args, userId)
            if res == MODULE_DOWN:
                if body != None:
                    logParsingFailure("eBay watch", args, body[1], body[0])
                body = None
            return res, body

    return INVALID_REQUEST, None

def retrieveLogin(fieldValue, userId):
    global g_tokens, g_fEbayInited
    if not g_fEbayInited:
        return MODULE_DOWN

    loginAndPwd = fieldValue
    userName = loginAndPwd[:loginAndPwd.find(";")]
    userPwd = loginAndPwd[loginAndPwd.find(";")+1:]
    # reset expiration if was
    try:
        item = g_tokens[userId]
        g_tokens[userId][1] = False
    except:
        pass
    # get token for that user
    status, token = getToken(userName, userPwd)
    expired = False
    if MODULE_DOWN == status:
        return MODULE_DOWN
    if EBAY_UNKNOWN_LOGIN == status:
        return EBAY_UNKNOWN_LOGIN
    if status == EBAY_LOGIN_OK and None != token:
        g_tokens[userId] = [token, expired]
        _saveTokens()
        return EBAY_LOGIN_OK
    assert 0

def main():
#    initCategories()
#    _loadTokens()

#    global g_tokens
#    g_tokens[0] = [g_unsignedToken, False]

    print "----------------------"
#    retrieveEBay("search;0;F;toy", None, 0)
    print "----------------------"
#    retrieveEBay("search;1;F;", None, 0)

    print "----------------------"
    retrieveEBay("item;4502518956;F", None, 0)
    print "----------------------"


# string.find() is faster than DOM or soup
def _getCategoryVersion(txt):
    ver = -1
    verTag = "<Version>"
    ind = txt.find(verTag)
    if ind != -1:
        ind += len(verTag)
        test = txt[ind:ind+10]
        test = test[:test.find("<")]
        ver = int(test)
    return ver

def _categoriesUpdate(fileName):
    sys.stdout.write(" updating cached categories.xml (it may take a while)")
    xmlOut = eBayCall("GetCategories", g_unsignedToken, "<ViewAllNodes>1</ViewAllNodes>", "1")
    fo = open(fileName,"wb")
    fo.write(xmlOut)
    fo.close()
    print "DONE"
    print "WARNING!!!"
    if len(xmlOut) > 1000000:
        # large file - inform other users
        emailContent = "You can find it here:\n"+fileName+"\nIt was done by: "+multiUserSupport.getServerUser()
        parserErrorLogger.mail("new eBay cache downloaded", emailContent)
        print "IF TESTING ON LOCAL MACHINE!!!"
        print "send email, and copy %s to server" % fileName
    else:
        print "someone have download new version of categories. Check your mail box to get location of new file."
    return xmlOut

class _CategoriesHandler(ContentHandler):
    def __init__(self):
        self.catId = "-1"
        self.parId = "-1"
        self.leaf = "0"
        self.name = ""
        self.expired = "0"
        self.virtual = "0"
        self.text = ""
        
    def startElement(self, name, attrs):
        self.text = ""

    def endElement(self, name):
        self.text = self.text.encode("latin-1", "ignore")
        if name == 'CategoryId':
            self.catId = self.text
        elif name == 'CategoryName':
            self.name = self.text
        elif name == 'CategoryParentId':
            self.parId = self.text
        elif name == 'IsExpired':
            self.expired = self.text
        elif name == 'IsVirtual':
            self.virtual = self.text
        elif name == 'LeafCategory':
            self.leaf = self.text
        elif name == 'Category':
            # add category to list
            global g_categories
            g_categories[self.catId] = [self.name, self.parId, []]
        self.text = ""
        
    def characters(self, ch):
        self.text += ch

def _categoriesBuild(xmlIn, fileName):
    global g_categories
    sys.stdout.write(" building categories (it may take a while) ")

    g_categories = {}
    g_categories["version"] = _getCategoryVersion(xmlIn)
    g_categories["0"] = ["Browse", "", []]

    parser = xml.sax.make_parser()
    handler = _CategoriesHandler()
    parser.setContentHandler(handler)
    inpsrc = InputSource()
    inpsrc.setByteStream(StringIO(xmlIn))
    parser.parse(inpsrc) 

    sys.stdout.write("(build category tree) ")

    for ind in g_categories:
        if ind != "version" and ind != "0":
            item = g_categories[ind]
            if item[1] == ind:
                g_categories["0"][2].append(ind)
                g_categories[ind][1] = "0"
            else:
                g_categories[item[1]][2].append(ind)

    if len(g_categories) > 4:
        fo = open(fileName, "wb")
        cPickle.dump(g_categories, fo, protocol = cPickle.HIGHEST_PROTOCOL)
        fo.close()
    else:
        fo = open(fileName, "rb")
        g_categories = cPickle.load(fo)
        fo.close()
        sys.stdout.write("(Copy categories.xml from your local machine to server. Please...) ")
    print "DONE"

def initCategories():
    global g_categories, g_fEbayInited
    # test version of cached categories (if file exists)
    fileName = os.path.join(g_eBayXmlPath, "categories.xml")
    fileNamePic = os.path.join(g_eBayCachePath, "categories.pic")
    xml = None
    if not arsutils.fFileExists(fileName):
        print " eBay may not be initiated, file %s missing (download can fail due to eBay req)" % fileName
    verCached = -1
    sys.stdout.write(" reading cached xml ")
    try:
        fo = open(fileName, "rb")
        xml = fo.read()
        fo.close()
        verCached = _getCategoryVersion(xml)
    except:
        verCached = -1
    xmlTest = eBayCall("GetCategories", g_unsignedToken, "<ViewAllNodes>0</ViewAllNodes>")
    verTest = _getCategoryVersion(xmlTest)
    print "DONE (version cached:%d, tested:%d)" % (verCached, verTest)
    if verTest > verCached:
        # need to update cache
        xml = _categoriesUpdate(fileName)
    # in xml we have actual categories...
    # load cPickled categories...
    sys.stdout.write(" reading cPickled categories ")    
    try:
        fo = open(fileNamePic, "rb")
        g_categories = cPickle.load(fo)
        fo.close()
    except:
        verCached = -1
    print "DONE"
    if verTest > verCached:
        _categoriesBuild(xml, fileNamePic)
    elif g_categories["version"] < verTest:
        _categoriesBuild(xml, fileNamePic)
    # else categories are current
    g_fEbayInited = True

def initToken():
    global g_unsignedUser, g_unsignedPwd, g_unsignedToken
    status, token = getToken(g_unsignedUser, g_unsignedPwd)
    if EBAY_LOGIN_OK != status or None == token:
        return False
    g_unsignedToken = token
    return True

def initEBay():
    print "initEBay() start"
    makePathIfNeeded(g_eBayCachePath)
    sys.stdout.write(" get unsigned token ")
    if not initToken():
        print ""
        print "FATAL ERROR IN eBay MODULE! - cannot connect to eBay"
        return
    print "DONE"

    initCategories()

    _loadTokens()
    print "initEBay() end"

def runTests():
    initEBay()
    print "---TESTS---\n"
    print "---OFFICIAL TIME---"
    print getOfficialEbayTime()
    print "-------------------"
    
def mainx():
    initEBay()
    print "---CATEGORIES---"
    cats = []
    for item in g_categories["0"][2]:
        cats.append(g_categories[item][0])
    cats.sort()
    for c in cats:
        print c
    
    print "----------------"


## TESTS...
def usage():
    print "Usage:"
    print " eBay.py <request>"
    print "  <request> := 'ebay:'...."

def main2():
    if 2 != len(sys.argv):
        usage()
        sys.exit(0)

    (schema, fieldValue) = sys.argv[1].split(":",1)
    if schema == "ebay":
        resultType, resultBody = retrieveEBay(fieldValue, None, 0)
    else:
        # TODO: add the rest of possible v-urls
        print "query %s not handled yet" % sys.argv[1]
        sys.exit(0)

    resultTypeTxt = resultTypeName(resultType)
    if None == resultTypeTxt:
        print "unknown result type %d" % resultType
    else:
        print "resultType: %s" % resultTypeTxt

if __name__ == "__main__":
    main()
