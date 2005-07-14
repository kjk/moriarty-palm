# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  flights schedule
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

def removeCloseTagAttr(htmlTxt):
    parts = htmlTxt.split("</table ")
    htmlTxt = parts[0]
    for part in parts:
        htmlTxt += "</table"
        htmlTxt += part[part.find(">"):]
    return htmlTxt

def removeAllNonAlfaFromStr(txt):
    i = 0
    while i < len(txt):
        if txt[i].isalpha():
            i += 1
        else:
            txt = txt[:i]+txt[i+1:]
    return txt

def tryParseList(htmlTxt, updateString, queryList):
    htmlTxt = removeCloseTagAttr(htmlTxt)
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    title = getAllTextFromTag(soup.first("title"))
    if title.startswith("Unable to Find Departure"):
        return NO_RESULTS, None
    span = soup.first("span", {"class":"minus1red"})
    if span:
        # problems!
        txt = getAllTextFromTag(span)
        if txt.startswith("There is no flight schedule available for the date"):
            return NO_RESULTS, None
        if txt.startswith("No commercial airline flies"):
            return NO_RESULTS, None
        return UNKNOWN_FORMAT, None
    # multiple city!
    if title.startswith("Similar Cities"):
        if queryList == None:
            return NO_RESULTS, None
        # we check only one similar city.
        tableA = soup.first("table", {"name":"matchA1"})
        tableB = soup.first("table", {"name":"matchB2"})
        if tableA and tableB:
            bItem = tableA.first("b")
            bList = tableB.fetch("b")
            if bItem and len(bList) > 0:
                city = getAllTextFromTag(bItem).lower().strip()
                index = 0
                if city == queryList[2].lower().strip():
                    index = 2
                elif city == queryList[3].lower().strip():
                    index = 3
                else:
                    # ok, so try to gues witch one is unknown...
                    c2 = queryList[2].lower().strip()
                    c3 = queryList[3].lower().strip()
                    # remove .,/ and other from c2 and c3
                    city = removeAllNonAlfaFromStr(city)
                    c2 = removeAllNonAlfaFromStr(c2)
                    c3 = removeAllNonAlfaFromStr(c3)
                    if city == c2:
                        index = 2
                    elif city == c3:
                        index = 3
                    else:
                        return UNKNOWN_FORMAT, None
                items = []
                for bItem in bList:
                    items.append(getAllTextFromTag(bItem))
                df = Definition()
                df.TextElement("Multiple matches for: '"+queryList[index]+"', please select one from list:", style=styleNameBold)
                df.LineBreakElement(1,2)
                for item in items:
                    df.BulletElement(False)
                    code = ""
                    try:
                        code = item.split("(")[1].split(")")[0]
                    except:
                        return UNKNOWN_FORMAT, None
                    queryList[index] = code
                    link = "s+flights:"+string.join(queryList, ";")
                    df.TextElement(item, link=link)
                    df.PopParentElement()
                return RESULTS_DATA, universalDataFormatWithDefinition(df, [])
        return UNKNOWN_FORMAT, None

    results = []
    options = 0
    for table in soup.fetch("table", {"name":"%"}):
        if table["name"].startswith("option"):
            results.append([""])
            options += 1
        elif table["name"].startswith("flight"):
            trList = table.fetch("tr")
            if len(trList) != 4:
                return UNKNOWN_FORMAT, None
            aItem = trList[1].first("a", {"href":"http://dps1.travelocity.com%"})
            if aItem:
                url = aItem["href"]
                td = trList[1].first("td", {"width":"100%"})
                if td:
                    bItem = td.first("b")
                    if bItem:
                        name = getAllTextFromTag(bItem).replace("&nbsp;"," ").strip()
                        plane = getAllTextFromTo(getLastElementFromTag(bItem).next, getLastElementFromTag(td).next).replace("&nbsp;"," ").strip()
                    else:
                        name = getAllTextFromTag(td).replace("&nbsp;"," ").strip()
                        plane = ""
                    tdList = trList[2].fetch("td")
                    if len(tdList) == 2:
                        depart = getAllTextFromTag(tdList[1])
                        tdList = trList[3].fetch("td")
                        if len(tdList) == 2:
                            arrive = getAllTextFromTag(tdList[1])
                            results.append([url, name, plane, depart, arrive])

    if 0==len(results):
        return UNKNOWN_FORMAT, None

    # definition
    df = Definition()
    df.TextElement("Search results:", style=styleNameBold)
    df.LineBreakElement(1,2)
    index = 0
    wasNumber = False
    for item in results:
        if len(item) == 1:
            if index > 0:
                df.PopParentElement()
            index += 1
            li = df.ListNumberElement(index, False)
            li.setTotalCount(options)
            wasNumber = True
        else:
            # [url, name, plane, depart, arrive]
            if not wasNumber:
                df.HorizontalLineElement()
            wasNumber = False    
            df.TextElement(item[1], link="s+flights:toc;"+item[0])
            if item[2] != "":
                df.TextElement(" "+item[2])
            df.LineBreakElement()
            df.TextElement("From: "+item[3])
            df.LineBreakElement()
            df.TextElement("To: "+item[4])
    df.PopParentElement()
    return RESULTS_DATA, universalDataFormatWithDefinition(df, [["U",updateString]])

def tryParseDetails(htmlTxt, updateString):
    htmlTxt = removeCloseTagAttr(htmlTxt)
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    flightInfo = []
    table = soup.first("table", {"name":"flight_info"})
    trList = []
    if table:
        for tr in table.fetch("tr"):
            if len(tr.fetch("td")) == 4:
                trList.append(tr)
            elif len(tr.fetch("td")) == 1:
                img = tr.first("img", {"alt":"Continuing on To"})
                if img:
                    trList.append(tr)
    for tr in trList:
        tdList = tr.fetch("td")
        if len(tdList)==4:
            info = getAllTextFromTag(tdList[0]).replace("&nbsp;"," ").strip()
            infoFrom = getAllTextFromTag(tdList[1]).replace("&nbsp;"," ").strip()
            infoTo = getAllTextFromTag(tdList[3]).replace("&nbsp;"," ").strip()
            if info != "":
                flightInfo.append([info, infoFrom, infoTo])
        else:
            flightInfo.append([""])

    flight = ""
    table = soup.first("table", {"name":"headbar2"})
    if table:
        bItem = table.first("b")
        if bItem:
            flight = getAllTextFromTag(bItem)

    if 0==len(flightInfo) or ""==flight:
        return UNKNOWN_FORMAT, None
    # definition
    df = Definition()
    df.TextElement(flight, style=styleNameBold)
    df.LineBreakElement(1,2)
    index = 0
    for item in flightInfo:
        # info, from, to
        if len(item) == 3:
            df.TextElement(item[0], style=styleNameHeader)
            if item[1] != "":
                df.LineBreakElement()
                df.TextElement(item[1])
            if item[2] != "":
                gtxt = df.TextElement(item[2])
                gtxt.setJustification(justRight)
            else:
                df.LineBreakElement()
        else:
            df.HorizontalLineElement()

    return RESULTS_DATA, universalDataFormatWithDefinition(df, [["U",updateString]])

def parseTravelocity(htmlTxt, updateString, queryList):
    type, body = tryParseList(htmlTxt, updateString, queryList)
    if UNKNOWN_FORMAT != type:
        return (type, body)
    type, body = tryParseDetails(htmlTxt, updateString)
    return type, body


def monthFromNumber(month):
    data = {
        1:"Jun",
        2:"Feb",
        3:"Mar",
        4:"Apr",
        5:"May",
        6:"Jun",
        7:"Jul",
        8:"Aug",
        9:"Sep",
        10:"Oct",
        11:"Nov",
        12:"Dec"
        }
    return data[int(month)]

g_airlinesTable = {
    ""                                  :"",
    "ATA Airlines"                      :"TZ",
    "Aer Lingus"                        :"EI",
    "Aero California"                   :"JR",
    "Aerolineas Argentinas"             :"AR",
    "Aeromexico"                        :"AM",
    "Aeropostal"                        :"VH",
    "Air Aruba"                         :"FQ",
    "Air Canada"                        :"AC",
    "Air France"                        :"AF",
    "Air Jamaica"                       :"JM",
    "Air New Zealand"                   :"NZ",
    "Air Tahiti Nui"                    :"TN",
    "Alaska Airlines"                   :"AS",
    "Alpi-Eagles"                       :"E8",
    "America West Airlines"             :"HP",
    "American Airlines/American Eagle"  :"AA",
    "American Airlines"                 :"AA",
    "American Eagle"                    :"AA",
    "AmericanConnection"                :"AX",
    "Ansett Airlines"                   :"AN",
    "Aserca"                            :"R7",
    "Asiana"                            :"OZ",
    "Aviacsa"                           :"6A",
    "BWIA International"                :"BW",
    "British Airways"                   :"BA",
    "British Midland"                   :"BD",
    "Canadian Airlines"                 :"CP",
    "China Airlines"                    :"CI",
    "Continental Airlines"              :"CO",
    "Cronus Airlines"                   :"X5",
    "Delta Air Lines"                   :"DL",
    "Dinar Lineas"                      :"D7",
    "Eva Air"                           :"BR",
    "Federico II Airways"               :"2D",
    "Finnair"                           :"AY",
    "Frontier Airlines"                 :"F9",
    "Hawaiian Airlines"                 :"HA",
    "Iberia"                            :"IB",
    "Icelandair"                        :"FI",
    "Jet Airways India"                 :"9W",
    "KLM"                               :"KL",
    "LACSA"                             :"LR",
    "LOT Polish"                        :"LO",
    "Lan Chile"                         :"LA",
    "Legend Airlines"                   :"LC",
    "Lufthansa"                         :"LH",
    "Martinair Holland"                 :"MP",
    "Mexicana de Aviacion"              :"MX",
    "Midway Airlines"                   :"JI",
    "Midwest Express"                   :"YX",
    "Northwest Airlines"                :"NW",
    "Oman Air"                          :"WY",
    "Qantas Airlines"                   :"QF",
    "Royal Air Maroc"                   :"AT",
    "TACA"                              :"TA",
    "TAM Meridional"                    :"JJ",
    "TAM Regional"                      :"KK",
    "US Airways"                        :"US",
    "United Airlines"                   :"UA",
    "Varig"                             :"RG",
    "Virgin Atlantic"                   :"VS"
    }

def retrieveFullSearch(flyNo, airlines, airportFrom, airportTo, dateUp, timeUp):
    global g_airlinesTable
    query = [flyNo, airlines, airportFrom, airportTo, dateUp, timeUp]
    # date in format: m/d/year
    # time in hh:mm format
    month, day, year = dateUp.split("/")
    hour, minutes = timeUp.split(":")
    apm = "am"
    hour = int(hour)
    if hour >= 12:
        apm = "pm"
        if hour > 12:
            hour -= 12
    elif hour == 0:
        hour = 12
    timeUp = "%d:%s%s" % (hour, minutes.zfill(2), apm)
    if airlines == "select airlines":
        airlines = ""

    airportFrom = airportFrom.strip().replace(" ", "+")
    airportTo   = airportTo.strip().replace(" ", "+")
    airlines = g_airlinesTable[airlines]
    
    url = "http://dps1.travelocity.com/dparflifo.ctl?CMonth=%s&CDayOfMonth=%s&CYear=%s&LANG=EN&last_pgd_page=dparrqst.pgd&dep_arp_name=%s&arr_arp_name=%s&dep_dt_mn_1=%s&dep_dt_dy_1=%s&dep_tm_1=%s&aln_name=%s&flt_num=%s&CDayOfMonth=%s&x=66&y=10" % (month, day, year, airportFrom, airportTo, monthFromNumber(month), day, urllib.quote(timeUp), airlines, flyNo, day)

    htmlTxt = getHttp(url)
    if None == htmlTxt:
        return MODULE_DOWN, None
    resultType, resultBody = parseTravelocity(htmlTxt, "s+flights:toc;"+url, query)
    if UNKNOWN_FORMAT == resultType:
        logParsingFailure("flights", (flyNo+";"+airlines+";"+airportFrom+";"+airportTo+";"+dateUp+";"+timeUp), htmlTxt, url)
    return resultType, resultBody

def retrieveUrlToc(url):
    htmlTxt = getHttp(url)
    if None == htmlTxt:
        return MODULE_DOWN, None
    resultType, resultBody = parseTravelocity(htmlTxt, "s+flights:toc;"+url, None)
    if UNKNOWN_FORMAT == resultType:
        logParsingFailure("flights", "toc;"+url, htmlTxt, url)
    return resultType, resultBody
    
def retrieveFlights(fieldValue):
    # (flyNo, airlines, airportFrom, airportTo, dateUp, timeUp)
    # (webCode; url)
    flyNo = None
    webCode = None
    try:
        flyNo, airlines, airportFrom, airportTo, dateUp, timeUp = fieldValue.split(";")
    except:
        try:
            webCode, url = fieldValue.split(";")
        except:
            pass
    if flyNo != None:
        return retrieveFullSearch(flyNo, airlines, airportFrom, airportTo, dateUp, timeUp)
    if webCode != None:
        if webCode == "toc":
            return retrieveUrlToc(url)
    return INVALID_REQUEST, None

## tests
def main():
    print "tests started-"

    retrieveFlights(";;new+mexico;dallas;3/25/2005;9:00")

    retrieveFlights(";;mexico;california;3/25/2005;9:00")

    print "tests end"


if __name__ == "__main__":
    main()
    
    
