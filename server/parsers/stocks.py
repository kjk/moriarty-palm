# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  finanses.yahoo.com
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

sUnknownFormatText = None
sNoResultsText = None
# to tests only
#sNoResultsText = "no results"
#sUnknownFormatText = "unknown format"

# this is test of no results pages
def testNoResults(soup):
    bigItem = soup.first("big",{"style":"color:red"})
    if bigItem:
        bItem = bigItem.first("b")
        if bItem:
            ##bContents = bItem.contents[0]
            ##if str(bContents).startswith("Error:"):
            return NO_RESULTS
    return STOCKS_DATA


# htmlTxt is a html page
# Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   STOCKS_LIST : resultBody is a stocks list in UDF
#   NO_RESULTS: no results found
#   UNKNOWN_FORMAT : resultBody is None
def parseList(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    noResults = testNoResults(soup)
    if NO_RESULTS == noResults:
        return (NO_RESULTS,sNoResultsText)

    tableList = soup.fetch("table", {"width":"100%", "cellpadding":"2", "cellspacing":"1", "border":"0"})
    if 1 != len(tableList):
        return (UNKNOWN_FORMAT, sUnknownFormatText)

    outerList = []
    trList = tableList[0].fetch("tr")
    resultsCount = 0
    for trItem in trList[1:]:
        tdList = trItem.fetch("td")
        if 8 == len(tdList):
            # found company
            symbol = getAllTextFromTag(tdList[0]).strip()
            time = getAllTextFromTag(tdList[1]).strip()
            trade = getAllTextFromTag(tdList[2]).strip()
            changeIcon = ""
            imgItem = tdList[3].first("img")
            if imgItem:
                changeIcon = imgItem['alt'].strip()
            change = getAllTextFromTag(tdList[3]).strip()
            percentChange = getAllTextFromTag(tdList[4]).strip()
            volume = getAllTextFromTag(tdList[5]).strip()
            # url
            aItem = tdList[0].first("a")
            url = aItem['href']

            resultsCount += 1
            outerList.append((url, symbol, time, trade, changeIcon, change, percentChange, volume))
        elif 1 == len(tdList):
            # no match
            text = getAllTextFromTag(tdList[0]).strip()
            if text.startswith("No such ticker symbol"):
                aItem = tdList[0].first("a")
                textSplitted = getAllTextFromTag(aItem).strip().split("\"")
                symbol = "?"
                if 2 < len(textSplitted):
                    symbol = string.join(textSplitted[1:-1],"\"").strip()
                url = aItem['href']
                
                resultsCount += 1
                outerList.append((url, symbol))
            # 'APPL' is no longer valid. It has changed to APPL.PK.
            elif text.find("is no longer valid. It has changed to"):
                aItem = tdList[0].first("a")
                if aItem:
                    symbol = getAllTextFromTag(aItem)
                    resultsCount += 1
                    outerList.append(("/l?s="+symbol, symbol))

    if 0 == resultsCount:
        return (NO_RESULTS, sNoResultsText)

    return (STOCKS_LIST, universalDataFormatReplaceEntities(outerList))


# htmlTxt is a html page
# Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   STOCKS_LIST : resultBody is a stocks list in UDF
#   VALIDATE_THIS : resultBody is url to validate
#   NO_RESULTS: no results found
#   UNKNOWN_FORMAT : resultBody is None
def parseListValidateLast(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    noResults = testNoResults(soup)
    if NO_RESULTS == noResults:
        return (NO_RESULTS,sNoResultsText)

    tableList = soup.fetch("table", {"width":"100%", "cellpadding":"2", "cellspacing":"1", "border":"0"})
    if 1 != len(tableList):
        return (UNKNOWN_FORMAT, sUnknownFormatText)

    outerList = []
    trList = tableList[0].fetch("tr")
    resultsCount = 0
    lastNeedValidate = 0
    for trItem in trList[1:]:
        tdList = trItem.fetch("td")
        if 8 == len(tdList):
            # found company
            symbol = getAllTextFromTag(tdList[0]).strip()
            time = getAllTextFromTag(tdList[1]).strip()
            trade = getAllTextFromTag(tdList[2]).strip()
            changeIcon = ""
            imgItem = tdList[3].first("img")
            if imgItem:
                changeIcon = imgItem['alt'].strip()
            change = getAllTextFromTag(tdList[3]).strip()
            percentChange = getAllTextFromTag(tdList[4]).strip()
            volume = getAllTextFromTag(tdList[5]).strip()
            # url
            aItem = tdList[0].first("a")
            url = aItem['href']

            resultsCount += 1
            lastNeedValidate = 0
            outerList.append((url, symbol, time, trade, changeIcon, change, percentChange, volume))
        elif 1 == len(tdList):
            # no match
            text = getAllTextFromTag(tdList[0]).strip()
            if text.startswith("No such ticker symbol"):
                aItem = tdList[0].first("a")
                textSplitted = getAllTextFromTag(aItem).strip().split("\"")
                symbol = "?"
                if 2 < len(textSplitted):
                    symbol = string.join(textSplitted[1:-1],"\"").strip()
                url = aItem['href']
                
                resultsCount += 1
                lastNeedValidate = 1
                outerList.append((url, symbol))

            # 'APPL' is no longer valid. It has changed to APPL.PK.
            elif text.find("is no longer valid. It has changed to"):
                aItem = tdList[0].first("a")
                if aItem:
                    symbol = getAllTextFromTag(aItem)
                    resultsCount += 1
                    outerList.append(("/l?s="+symbol, symbol))

    if 0 == resultsCount:
        return (NO_RESULTS, sNoResultsText)

    if 1 == lastNeedValidate:
        return (VALIDATE_THIS, outerList[-1][0])

    return (STOCKS_LIST, universalDataFormatReplaceEntities(outerList))

# htmlTxt is a html page
# Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   STOCKS_LIST : resultBody is a stocks list in UDF (name search)
#   NO_RESULTS: no results found
#   UNKNOWN_FORMAT : resultBody is None
def parseName(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # no results
    fontList = soup.fetch("font", {"face":"arial"})
    for fontItem in fontList:
        iItem = fontItem.first("i")
        if iItem:
            if str(iItem.contents[0]).startswith("Your search for"):
                return (NO_RESULTS, sNoResultsText)

    # get table data
    trList = soup.fetch("tr", {"bgcolor":"#ffffff"})
    resultsCount = 0
    outerList = []
    for trItem in trList:
        tdList = trItem.fetch("td")
        if 5 == len(tdList):
            symbol = getAllTextFromTag(tdList[0]).strip()
            url = tdList[0].first("a")['href']
            name = getAllTextFromTag(tdList[1]).strip()
            market = getAllTextFromTag(tdList[2]).strip()
            industry = getAllTextFromTag(tdList[3]).strip()
            outerList.append((url,symbol,name,market,industry))            
            resultsCount += 1
            
    # no results?
    if 0 == resultsCount:
        return (NO_RESULTS, sNoResultsText)
        
    return (STOCKS_LIST, universalDataFormatReplaceEntities(outerList))


# htmlTxt is a html page
# Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   STOCKS_DATA : resultBody is a stock data in UDF
#   UNKNOWN_FORMAT : resultBody is None
#   NO_RESULST : resultsBody in None (bad symbol)
def parseStock(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    noResults = testNoResults(soup)
    if NO_RESULTS == noResults:
        return (NO_RESULTS,sNoResultsText)

    # get name
    nameTag = soup.first("td", {"height":"30", "class":"ygtb"})
    if not nameTag:
        return (UNKNOWN_FORMAT, sUnknownFormatText)
    name = getAllTextFromTag(nameTag).strip()

    # get all data from table        
    bigTable = soup.fetch("table", {"width":"580", "id":"yfncsumtab"})
    if 1 != len(bigTable):
        return (UNKNOWN_FORMAT, sUnknownFormatText)
    tdDataList = bigTable[0].fetch("td", {"class":"yfnc_tabledata1"})
    innerList = [name]
    counter = 0
    for tdItem in tdDataList:
        if 2 == counter:
            # 3th element is with up down icon
            imgItem = tdDataList[2].first("img")  
            upDown = ""
            if imgItem:
                upDown = imgItem['alt']
            innerList.append(upDown)
            bItem = tdDataList[2].first("b")
            itemText = ""
            if bItem:
                itemText = getAllTextFromTag(bItem).strip()
            innerList.append(itemText)       
        else:            
            itemText = getAllTextFromTag(tdItem).strip()
            innerList.append(itemText)
        counter += 1

    # any results?
    if 0 == counter:
        return (UNKNOWN_FORMAT, sUnknownFormatText)

    # one-item UDF    
    outerList = [innerList]
    return (STOCKS_DATA, universalDataFormatReplaceEntities(outerList))

