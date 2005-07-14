# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  horoscopes
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

horoscopeTitle         = "T"
horoscopeSection       = "S"
horoscopeSmallSection  = "s"
horoscopeText          = "t"
horoscopeDate          = "D"
horoscopeUrlLink       = "L"

# htmlTxt is a html page
def parseHoroscope(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    outerList = []
    centerList = soup.fetch("center")
    for center in centerList:
        table = center.first("table", {"width":"90%"})
        if table:
            # here get all headers
            big = soup.first("big", {"class":"yastshdohdrtxt"})
            if big:
                title = getAllTextFromTag(big).replace("\n","").strip()
                outerList.append([horoscopeTitle,title])
                splitted = title.split(" for ")
                if len(splitted) > 1:
                    outerList.append([horoscopeDate, splitted[1].strip()])
                else:
                    #year?
                    if title.startswith("Year 20"): ## i will be retired before year 2100 :)
                        outerList.append([horoscopeDate, title[5:8]])
            # parse table
            for td in table.fetch("td"):
                bList = td.fetch("b")
                if 0 < len(bList):
                    index = 0
                    while index < len(bList):
                        section = getAllTextFromTag(bList[index]).replace("\n","").strip()
                        outerList.append([horoscopeSection, section])
                        if index == len(bList)-1:
                            last = getLastElementFromTag(td).next
                        else:
                            last = bList[index+1]
                        text = getAllTextFromTo(getLastElementFromTag(bList[index]).next,last).replace("\n","").strip()
                        outerList.append([horoscopeText, text])
                        index += 1
                else:
                    text = getAllTextFromToInBrFormat(td, getLastElementFromTag(td).next).replace("</b>","").replace("<b>","").replace("\n","").strip()
                    textList = text.split("<br>")
                    for text in textList:
                        outerList.append([horoscopeText, text.strip()])
            # links?
            # links have format: "yh;url" - yh is yahoo
            ##TODO:
            # outerList.append([horoscopeSection, "Forecasts"])
            # outerList.append([horoscopeUrlLink, "month", "yh;/astrology/careerfinance/monthly/aries"])
            section = horoscopeSection
            tableList = soup.fetch("table", {"width":"100%",  "cellpadding":"4"})
            for table in tableList:
                smallTableList = table.fetch("table", {"width":"100%", "cellpadding":"2"})
                for smallTable in smallTableList:
                    tdList = smallTable.fetch("td")
                    if len(tdList) > 1:
                        small = tdList[0].first("small", {"class":"yastshleftnavsubhdrtxt"})
                        if small:
                            outerList.append([section, getAllTextFromTag(small).replace("\n","").strip()])
                            section = horoscopeSmallSection
                            for td in tdList[1:]:
                                aItem = td.first("a", {"href":"%"})
                                if aItem:
                                    text = getAllTextFromTag(aItem).replace("\n","").strip()
                                    url = aItem['href']
                                    if text != "Yearly": ## this is not handled property :)
                                        outerList.append([horoscopeUrlLink, text, "yh;" + url])

    if len(outerList) == 0:
        return (UNKNOWN_FORMAT, str(soup))
    return (HOROSCOPE_DATA, universalDataFormatReplaceEntities(outerList))
