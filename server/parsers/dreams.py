# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  dreams dictionary
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

dUnknownFormatText = None
dNoResultsText = None
# to tests only
#dNoResultsText = "no interpretation"
#dUnknownFormatText = "unknown format"

# htmlTxt is a html page
# Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   DREAM_DATA : resultBody is a dream interpretation
#   NO_RESULTS : nothing found
#   UNKNOWN_FORMAT : resultBody is None
def parseDream(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    tdMain = soup.first("td", {"width":"437", "height":"1", "colspan":"3", "valign":"top", "rowspan":"2", "align":"left"}) 
    if not tdMain:
        return (UNKNOWN_FORMAT, dUnknownFormatText)

    fList = tdMain.fetch("font", {"face":"Arial", "size":"4", "color":"#6500CA"})
    definitionsCount = len(fList) - 3
    if 0 >= definitionsCount:
        return (NO_RESULTS,dNoResultsText)

    outerList = []
    realDefinitionsCount = 0
    for fItem in fList[:-3] :
        bItem = fItem.first("b")
        if bItem:
            itemTitle = getAllTextFromTag(bItem).replace("\n","").strip()
            itemText = getAllTextFromToInBrFormat(getLastElementFromTag(fItem).next,fList[realDefinitionsCount+1])
            itemText = itemText.replace("\n","").strip()
            outerList.append((itemTitle,itemText))
            realDefinitionsCount += 1
        
    if 0 == realDefinitionsCount:
        return (UNKNOWN_FORMAT, dUnknownFormatText)

    return (DREAM_DATA, universalDataFormatReplaceEntities(outerList))

# with <a> </a>
# soup screw this <a><font>...</font></a> into <a></a><font>...</font>
# so we need to extract <a> form <font>
def getAllTextFromTagWithA(tag):
    if None == tag:
        return ""
    if not isinstance(tag, Tag):
        return str(tag).replace("\n"," ")
    returned = []
    for cont in tag.contents:
        if not isinstance(cont, Tag):
            returned.append(str(cont).replace("\n"," "))
        else:
            if cont.name == "font":
                text = getAllTextFromTagWithA(cont).strip()
                returned.append("<a>" + text + "</a>")
            else:
                returned.append(getAllTextFromTagWithA(cont))
    return string.join(returned," ").replace("  "," ").replace("  "," ")

# return as parseDream, but for secound url...
def parseDream2(htmlTxt):
    soup = BeautifulSoup()
    # TODO: this is temporary:
    htmlTxt = htmlTxt.replace("/*<![CDATA[*/ @import \"/knowledge/stylesheets/monobook/main.css\"; /*]]>*/","")

    soup.feed(htmlTxt)

    tableMain = soup.fetch("table", {"width":"768", "align":"center", "cellspacing":"0", "cellpadding":"0"})
    if not tableMain:
        return (UNKNOWN_FORMAT, dUnknownFormatText)
    td = None
    for table in tableMain:
        tr = table.first("tr")
        if tr:
            tdTest = tr.first("td", {"width":"100%", "valign":"top"})
            if tdTest:
                td = tdTest
    if not td:
        return (UNKNOWN_FORMAT, dUnknownFormatText)
    # why without this it is not working?
    soup2 = BeautifulSoup()    
    soup2.feed(str(td).replace("<br />>",""))
    td = soup2.first("td")
    # no results?
    if td.first("center"):
        return (NO_RESULTS,dNoResultsText)

    # results
    bTable = td.fetch("b")
    if not bTable:
        return (UNKNOWN_FORMAT, dUnknownFormatText)

    outerList = []
    for bItem in bTable:
        title = getAllTextFromTag(bItem)
        next = getLastElementFromTag(bItem)
        pItem = None
        while next and not pItem:
            if isinstance(next, Tag):
                if next.name == "p":
                    pItem = next
            next = next.next
        if pItem:
            text = getAllTextFromTagWithA(pItem.first("font"))
            if text.startswith("Interpretation: "):
                text = text[len("Interpretation: "):]
            outerList.append((title,text))

    if 0 == len(outerList):
        return (NO_RESULTS,dNoResultsText)
    return (DREAM_DATA, universalDataFormatReplaceEntities(outerList))

def main():
    pass

if __name__ == "__main__":
    main()

