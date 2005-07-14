# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#
import random, string, urllib, urllib2, ServerErrors, Retrieve
try:
    from BeautifulSoup import BeautifulSoup, NavigableText
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise

from entities import convertNamedEntities
from entities import convertNumberedEntities

from parserUtils import *
from ResultType import *


def parseWeather(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # location unknown ?
    divU = soup.first("div" , {"class":"moduleTitleBarc"})
    if divU:
        fontU = divU.first("font", {"class":"inDentA"})
        if fontU:
            if str(fontU.contents[0]).startswith("Your Search:"):
                return (LOCATION_UNKNOWN,None)

    # secound <table width="100%" cellpadding="0" cellspacing="0" border="0" id="f2">
    listT = soup.fetch("table", {"id":"f2", "width":"100%", "cellpadding":"0", "cellspacing":"0", "border":"0"})
    if (not listT):
        return (UNKNOWN_FORMAT, None)
    if (len(listT) != 2):
        return (UNKNOWN_FORMAT, None)

    # returned = first day info
    firstDayTables = soup.fetch("table", {"width":"100%", "border":"0", "cellpadding":"0" ,"cellspacing":"0"})
    firstTableOffset = -1
    currentOffset = 0
    # find table with 2*<tr> and 4*<td>
    while currentOffset < len (firstDayTables):
        test = firstDayTables[currentOffset]
        if len(test.fetch("tr")) == 2:
            if len(test.fetch("td")) == 4:
                firstTableOffset = currentOffset
                currentOffset = len (firstDayTables)
        currentOffset += 1
    if firstTableOffset == -1:
        return (UNKNOWN_FORMAT, None)

    smallList = []
    # first part
    first = firstDayTables[firstTableOffset]
    counter = 0
    for itemTD in first.fetch("td"):
        if counter == 1:
            smallList.append(str(itemTD.first("b").contents[0]).replace("\n","").replace("&deg;F","").strip())
        if counter == 2:
            smallList.append(str(itemTD.first("b").contents[0]).replace("\n","").strip())
        if counter == 3:
            smallList.append(str(itemTD.first("b").contents[2]).replace("\n","").replace("&deg;F","").strip())
        counter += 1
    # secound part
    secound = firstDayTables[firstTableOffset+1]
    counter = 1
    for itemTD in secound.fetch("td"):
        if counter == 2:
            smallList.append(str(itemTD.contents[0]).replace("\n","").strip())
        if counter == 4:
            smallList.append(str(itemTD.contents[0]).replace("&deg;F","").replace("\n","").strip())
        if counter == 6:
            smallList.append(str(itemTD.contents[0]).replace("%","").replace("\n","").strip())
        if counter == 8:
            smallList.append(str(itemTD.contents[0]).replace("\n","").strip())
        if counter == 10:
            smallList.append(str(itemTD.contents[0]).replace("\n","").strip())
        if counter == 12:
            smallList.append(str(itemTD.contents[0]).replace("\n","").strip())
        counter += 1

    returned.append(smallList)
    secoundT = listT[1]
    # ok we have table with informations (10 days) - or 9 days without Today
    counterTR = 0
    for eachTR in secoundT.fetch("tr"):
        tonight = 0
        smallList = []
        if counterTR < 10:
            counter = 0
            for eachTD in eachTR.fetch("td"):
                # day <br> date
                if counter == 0:
                    day = eachTD.first("a").contents[0]
                    date = eachTD.first("br").next
                    smallList.append(str(day).replace("\n","").strip())
                    smallList.append(str(date).replace("\n","").strip())
                    # detect 9 days case
                    if (not (str(day).strip() == "Today")) and counterTR == 0:
                        counterTR += 1   # skip one day
                    if (str(day).strip() == "Tonight"):
                        tonight = 1
                # after image text ("cloudy")
                if counter == 2:
                    imageTxt = eachTD.contents[0]
                    smallList.append(str(imageTxt).replace("\n","").strip())

                # temp: <B>73&deg;/56&deg;</B>
                if counter == 3:
                    temp = eachTD.first("b").contents[0]
                    temp = str(temp).split("/")
                    tempUp = temp[0].strip()
                    tempDown = temp[0].strip()
                    if tonight == 0:
                        tempDown = temp[1].strip()
                    smallList.append(str(tempUp).replace("\n","").replace("&deg;","").strip())
                    smallList.append(str(tempDown).replace("\n","").replace("&deg;","").strip())

                # precip
                if counter == 4:
                    precip = str(eachTD.contents[0])
                    smallList.append(str(precip).replace("\n","").replace("%","").strip())
                    returned.append(smallList)
                counter += 1
        counterTR += 1

    return (WEATHER_DATA,universalDataFormatReplaceEntities(returned))


def parseMultiselect(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    aList = soup.fetch("a", {"href":"/weather/local/%"})
    aList += soup.fetch("a", {"href":"/outlook/travel/local/%"})
    aList += soup.fetch("a", {"href":"/outlook/travel/businesstraveler/local/%"})


    lastCode = ""
    resultsCount = 0
    for aItem in aList:
        afterLocal = aItem['href'].split("local/")
        if 2 == len(afterLocal):
            textAfterLocal = afterLocal[1]
            if 8 < len(textAfterLocal):
                code = textAfterLocal[:8]
                textAfterLocal = textAfterLocal[8:]
                if textAfterLocal.startswith("?from=search_"):
                    if -1 == lastCode.find(code):
                        lastCode += code
                        text = getAllTextFromTag(aItem)
                        resultsCount += 1
                        returned.append((text,code))
    if 0 == resultsCount:
        return (LOCATION_UNKNOWN,None)
    return (LOCATION_MULTISELECT,universalDataFormatReplaceEntities(returned))

#define detailedTemperatureInUDF 0
#define detailedSkyInUDF 1
#define detailedFeelsLikeInUDF 2
#define detailedUVIndexInUDF 3
#define detailedDevPointInUDF 4
#define detailedHumidityInUDF 5
#define detailedVisibilityInUDF 6
#define detailedPressureInUDF 7
#define detailedWindInUDF 8

#define dailyDayInUDF 0
#define dailyDateInUDF 1
#define dailySkyInUDF 2
#define dailyTemperatureDayInUDF 3
#define dailyTemperatureNightInUDF 4
#define dailyPrecipInUDF 5

def getListFromText(text, count):
    ret = []
    index = 0
    while count >= 0:
        small = ""
        index2 = index
        index = text.find("'",index)
        if index >= 0:
            index2 = text.find("'",index+1)
            if index2 >= 0:
                small = text[index+1:index2]
            else:
                index2 = index
        index = index2 + 1
        ret.append(small)
        count -= 1
    return ret

def parseFirstDayHtml(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # sky, now, feelsLike, wind, hum, preasure, dev point, visibility
    returned = [None, None, None, None, None, None, None, "N/A"]

    bItems = soup.fetch("b", {"class":"obsTextA"})
    if len(bItems) == 2:
        returned[0] = getAllTextFromTag(bItems[0]).strip()
        temp = getAllTextFromTag(bItems[1]).strip().split("Like ")
        if len(temp) > 1:
            returned[2] = temp[1].replace("&deg;F","").strip()

    bItem = soup.first("b", {"class":"obsTempTextA"})
    if bItem:
        returned[1] = getAllTextFromTag(bItem).replace("&deg;F","").strip()

    tdList = soup.fetch("td", {"class":"obsTextA"})
    if len(tdList) == 8:
        tdList = tdList[1::2]
        assert (len(tdList) == 4)
        returned[3] = getAllTextFromTag(tdList[0]).strip()
        returned[4] = getAllTextFromTag(tdList[1]).replace("%","").strip()
        returned[5] = getAllTextFromTag(tdList[2]).replace("in.","inches").strip() ##todo: down, up, ...
        returned[6] = getAllTextFromTag(tdList[3]).replace("&deg;F","").strip()

    for r in returned:
        if r == None or r == "":
            return None
    return returned

def parseFirstDayHtmlYahoo(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # sky, now, feelsLike, wind, hum, preasure, dev point, visibility
    returned = [None, None, None, None, None, None, None, None]

    fontList = soup.fetch("font",{"face":"Arial", "size":"2"})
    list = []
    wasFeelsLike = False
    for f in fontList:
        text = getAllTextFromTag(f).strip()
        if wasFeelsLike:
            list.append(text)
        else:
            if text == "Feels Like:":
                list.append(text)
                wasFeelsLike = True
    if len(list) >= 16:
        smallList = list[1::2]
        returned[0] = ""
        returned[1] = smallList[0].replace("&deg;","")
        returned[2] = smallList[0].replace("&deg;","")
        returned[3] = smallList[3]
        returned[4] = smallList[4].replace("%","")
        returned[5] = smallList[2]
        returned[6] = smallList[1].replace("&deg;","")
        returned[7] = smallList[6]

    for r in returned:
        if r == None:
            return None
    return returned


g_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def parseWeatherComNew(htmlTxt, htmlTxtFirstDay=None):
    returned = []

    firstDay = None
    text = htmlTxt
    beforeDate = "new mpdFDObj(new Date('"
    while len(text) > 0:
        index = text.find("mpdData['dayf'].day[")
        if index >= 0:
            text = text[index:]
            index = text.find(beforeDate)
            if index >= 0:
                text = text[index+len(beforeDate)-1:]
                #2005','0','15','0','0','0'),'Sat','36','32','1','5','PM Rain / Snow Showers / Wind','17','Northeast','NE','30', '62');
                values = getListFromText(text,16)
                date = ""
                if len(values[6]) == 3:
                    date = g_months[int(values[1])] + " " + values[2]
                if values[6] == "Tonight":
                    values[7] = values[8]
                anyDay = [values[6].strip(),date.strip(),values[11].strip(),values[7].strip(),values[8].strip(),values[15].strip()]
                returned.append(anyDay)
                if firstDay == None:
                    # do first day:
                    wind = values[13]
                    if len(values[12]) > 0:
                        wind = values[13]+" at "+values[12]+ " mph"
                    tempAvg = ""
                    if values[6] == "Tonight":
                        tempAvg = values[8]
                    else:
                        tempAvg = str((int(values[7]) + int(values[8])) /2)
                    firstDay = [tempAvg.strip(),values[11].strip(),tempAvg,values[9].strip(),"N/A",values[16].strip(),"N/A","N/A",wind]
        if index == -1:
            text = ""

#    firstDay = ["35"-now,"Skydet","36"-feels,"UV low","37"-dev point,"HUM","visible","preasure","Wind"]
    if htmlTxtFirstDay != None:
        ret = parseFirstDayHtmlYahoo(htmlTxtFirstDay)
        if ret != None:
            if ret[1] != "":
                firstDay[0] = ret[1].strip()
            if ret[0] != "":
                firstDay[1] = ret[0].strip()
            if ret[2] != "":
                firstDay[2] = ret[2].strip()
            if ret[6] != "":
                firstDay[4] = ret[6].strip()
            if ret[4] != "":
                firstDay[5] = ret[4].strip()
            if ret[5] != "":
                firstDay[7] = ret[5].strip()
            if ret[3] != "":
                firstDay[8] = ret[3].strip()
            if ret[7] != "":
                firstDay[6] = ret[7].strip()

    if firstDay == None:
        return (LOCATION_UNKNOWN,None)
    returned = [firstDay] + returned
    return (WEATHER_DATA,universalDataFormatReplaceEntities(returned))

weatherServerUrlFirstDay    = "http://weather.yahoo.com/forecast/%s.html"
weatherServerUrl            = "http://www.weather.com/weather/mpdwcr/tenday?locid=%s"
weatherMultiselectServerUrl = "http://www.weather.com/search/enhanced?where=%s"
weatherTopUrl             = "http://www.weather.com/activities/other/other/weather/tenday.html?locid=%s"
weatherCookieUrl    = "http://www.w3.weather.com/RealMedia/ads/adstream_mjx.ads/www.weather.com/5day/%s@PageCounter,HeaderSpon,Feature,PageSpon,PageSpon2,LocalAd,UberButton1,UberButton2,SpotButton1,SpotButton2,Hidden1?context=undcl_tenday"

def retrieveWeather(jar, location):

    cookieHandler = urllib2.HTTPCookieProcessor(jar)

    opener = urllib2.build_opener(cookieHandler)
    opener.addheaders = [("User-Agent", "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322)")]

    zipOr8Code = False
    if 5 == len(location):
        if location.isdigit():
            zipOr8Code = True
    if 8 == len(location):
        if location[4:].isdigit():
            if location[:3].isalpha():
                if location[:3].isupper():
                    zipOr8Code = True

    topUrl = weatherTopUrl % urllib.quote(location)

    request = urllib2.Request(topUrl)
    request.add_header("Referer", "http://www.weather.com")
    response = opener.open(request)
    response.close()

    request = urllib2.Request(weatherCookieUrl % str(random.randint(0, 2147483647)))
    request.add_header("Referer", topUrl)
    response = opener.open(request)
    response.close()

    if zipOr8Code:
        request = urllib2.Request(weatherServerUrl % urllib.quote(location))
        request.add_header("Referer", topUrl)
        response = opener.open(request)
        htmlText = None
        try:
            htmlText = response.read()
        finally:
            response.close()

        request = urllib2.Request(weatherServerUrlFirstDay % urllib.quote(location))
        response = opener.open(request)

        htmlText2 = None
        try:
            htmlText2 = response.read()
        finally:
            response.close()

        return parseWeatherComNew(htmlText, htmlText2)
    else:
        request = urllib2.Request(weatherMultiselectServerUrl % urllib.quote(location))
        request.add_header("Referer", topUrl)
        response = opener.open(request)
        htmlText = None
        try:
            htmlText = response.read()
        finally:
            response.close()

        if None == htmlText:
            return ServerErrors.moduleTemporarilyDown
        return parseMultiselect(htmlText)

def main():
    if len(sys.argv) != 2:
        print "usage: weather.py file.html"
        sys.exit(1)
    fileName = sys.argv[1]
    fo = open(fileName, "rb")
    htmlTxt = fo.read()
    fo.close()
    (resType, data) = parseWeather(htmlTxt)
    if WEATHER_DATA == resType:
        print "data:"
        print data
    else:
        resTypeName = resultTypeName(resType)
        if None == resTypeName:
            print "result type: %d" % resType
        else:
            print "result type: %s" % resTypeName

import sys
def main2():
    if len(sys.argv) != 2:
        print "usage: weather.py file.html"
        sys.exit(1)
    fileName = sys.argv[1]
    fo = open(fileName, "rb")
    htmlTxt = fo.read()
    fo.close()
    print parseFirstDayHtmlYahoo(htmlTxt)

def main3():
    import cookielib
    jar = cookielib.CookieJar()
    print retrieveWeather(jar, "98101")

if __name__ == "__main__":
    main3()
