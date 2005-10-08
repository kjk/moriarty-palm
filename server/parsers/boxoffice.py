# Copyright: Krzysztof Kowalczyk
# Owner: Szymon
#
# Purpose:
#  box office information taken from yahoo!
#
import sys, string, arsutils
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise
from parserUtils import *
from ResultType import *
from Retrieve import getHttp

boxOfficeNoResultsText = None # flag - just for tests

# TODO: needs to add an alternative http://www.boxofficemojo.com/,
# http://www.boxofficemojo.com/weekend/chart/

def retrieveBoxOffice(fDebug=False):
    url = "http://movies.yahoo.com/mv/boxoffice/weekend/"
    refererUrl = "http://movies.yahoo.com" # TODO: this is not really a good referer
    htmlTxt = getHttp(url, referer=refererUrl)
    if None == htmlTxt:
        return retrieveFailed(url)

    resultType, resultBody = parseYahooBoxOffice(htmlTxt, url,fDebug=fDebug)
    return resultType, resultBody

def parseYahooBoxOfficeOld(htmlTxt, url=None):
    returned = []
    # this is funy
    htmlTxt = htmlTxt.replace("<! -- ", "<!---")
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    findTable = soup.fetch("table",{"border":"0", "cellpadding":"4", "cellspacing":"0", "width":"100%"})
    if not findTable:
        return parsingFailed(url, htmlTxt)

    resultsCounter = 0
    itemTable = findTable[0];
    findTableTR = itemTable.fetch("tr")
    
    if len(findTableTR) < 2:
        return parsingFailed(url, htmlTxt)
    
    for itemTR in findTableTR:
        findTD = itemTR.fetch("td") 
        if 8 != len(findTD):
            return parsingFailed(url, htmlTxt)
        
        smallList = []
        resultsCounter += 1
        if resultsCounter == 1:
            continue
        if resultsCounter == 12:
            break
        
        lastWeekPos = str(findTD[1].first("font").contents[0]).replace("\n","").strip()
        title = ""
        if findTD[2].first("a"):
            title = str(findTD[2].first("a").contents[0]).replace("\n","").strip()
        else:
            title = str(findTD[2].first("b").contents[0]).replace("\n","").strip()

        weekGross = str(findTD[4].first("font").contents[0]).replace("\n","").replace("$","").replace(",","").strip()
        cumulativeGross = str(findTD[5].first("font").contents[0]).replace("\n","").replace("$","").replace(",","").strip()
        releaseWeeks = str(findTD[6].first("font").contents[0]).replace("\n","").strip()
        theatersNumber = str(findTD[7].first("font").contents[0]).replace("\n","").strip()
        # Theoretically if weekGross > 1 mln then cumulative also, but who knows
        abbrevGross = ""

        try:
            floatWeekGross = float(weekGross)
            if (floatWeekGross > 1000000):
                abbrevGross = "$" + str(round(floatWeekGross/1000000, 1)) + " mln/"
            else:
                abbrevGross = "$" + weekGross + "/"
        except:
            abbrevGross += "(n/a) " + "/"
            
        try:
            floatCumulativeGross = float(cumulativeGross)        
            if (floatCumulativeGross > 1000000):
                abbrevGross += "$" + str(round(floatCumulativeGross/1000000, 1)) + " mln"
            else:
                abbrevGross += "$" + cumulativeGross
        except:
            abbrevGross += "(n/a)"
        
        smallList = (lastWeekPos, title, weekGross, cumulativeGross, releaseWeeks, theatersNumber, abbrevGross)
        returned.append(smallList)

    return (RESULTS_DATA, universalDataFormatReplaceEntities(returned))

def parseYahooBoxOffice(htmlTxt, url=None, fDebug=False):
    # stupid Yahoo! changed the format for box office charts and doesn't properly
    # close tr tag. hopefully this won't break things even when they (if) fix
    # their format
    # this is funy
    htmlTxt = htmlTxt.replace("<! -- ", "<!---")
    htmlTxt = string.replace(htmlTxt, "Theaters</a></B></Font></TD>", "Theaters</a></B></Font></TD></TR>")
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    findTable = soup.fetch("table",{"border":"0", "cellpadding":"4", "cellspacing":"0", "width":"100%"})
    if not findTable:
        if fDebug:
            print "didn't find table"
        return parsingFailed(url, htmlTxt)

    resultsCounter = 0
    itemTable = findTable[0];
    findTableTR = itemTable.fetch("tr")
    
    if len(findTableTR) < 2:
        if fDebug:
            print "len(findTableTR) < 2"
        return parsingFailed(url, htmlTxt)
    
    for itemTR in findTableTR:
        findTD = itemTR.fetch("td") 
        if 8 != len(findTD):
            if fDebug:
                print "8 != len(findTD)"
                print "len(findTD) = %d" % len(findTD)
                print str(findTD)
            return parsingFailed(url, htmlTxt)
        
        smallList = []
        resultsCounter += 1
        if resultsCounter == 1:
            continue
        if resultsCounter == 12:
            break
        
        lastWeekPos = str(findTD[1].first("font").contents[0]).replace("\n","").strip()
        title = ""
        if findTD[2].first("b"):
            title = str(findTD[2].first("b").contents[0]).replace("\n","").strip()
        else:
            assert findTD[2].first("a")
            title = str(findTD[2].first("a").contents[0]).replace("\n","").strip()

        weekGross = str(findTD[4].first("font").contents[0]).replace("\n","").replace("$","").replace(",","").strip()
        cumulativeGross = str(findTD[5].first("font").contents[0]).replace("\n","").replace("$","").replace(",","").strip()
        releaseWeeks = str(findTD[6].first("font").contents[0]).replace("\n","").strip()
        theatersNumber = str(findTD[7].first("font").contents[0]).replace("\n","").strip()
        # Theoretically if weekGross > 1 mln then cumulative also, but who knows
        abbrevGross = ""

        try:
            floatWeekGross = float(weekGross)
            if (floatWeekGross > 1000000):
                abbrevGross = "$" + str(round(floatWeekGross/1000000, 1)) + " mln/"
            else:
                abbrevGross = "$" + weekGross + "/"
        except:
            abbrevGross += "(n/a) " + "/"
            
        try:
            floatCumulativeGross = float(cumulativeGross)        
            if (floatCumulativeGross > 1000000):
                abbrevGross += "$" + str(round(floatCumulativeGross/1000000, 1)) + " mln"
            else:
                abbrevGross += "$" + cumulativeGross
        except:
            abbrevGross += "(n/a)"
        
        smallList = (lastWeekPos, title, weekGross, cumulativeGross, releaseWeeks, theatersNumber, abbrevGross)
        returned.append(smallList)

    return (RESULTS_DATA, universalDataFormatReplaceEntities(returned))

def usage():
    print "usage: boxoffice.py [-file $fileToParse]"

def main():
    fileName = arsutils.getRemoveCmdArg("-file")

    if 1 != len(sys.argv):
        usage()
        sys.exit(0)

    if None != fileName:
        fo = open(fileName, "rb")
        htmlTxt = fo.read()
        fo.close()
        (resultType, resultBody) = parseYahooBoxOffice(htmlTxt, fileName, fDebug=True)
    else:
        (resultType, resultBody) = retrieveBoxOffice(fDebug=True)

    if MODULE_DOWN == resultType:
        print "module down"
    if PARSING_FAILED == resultType:
        print "parsing failed"
    if RESULTS_DATA == resultType:
        print "got BOXOFFICE"
        print udfPrettyPrint(resultBody)
        #print resultBody

if __name__ == "__main__":
    main()
