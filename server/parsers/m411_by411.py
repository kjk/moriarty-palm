# Purpose: handle parsing of 411 queries from http://www.411.com
import string, urllib, urllib2
try:
    import BeautifulSoup21
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise
from ResultType import *
from entities import convertNamedEntities, convertNumberedEntities, convertEntities23
from parserUtils import *
from Retrieve import getHttp, getHttpCached
from parserErrorLogger import logParsingFailure

# flags - just for tests
m411NoResultsText = None
m411UnknownFormatText = None
m411TooManyResults = None
m411NoCity = None
#m411NoResultsText = "no results"
#m411UnknownFormatText = "unknown format"
#m411TooManyResults = "too many results"
#m411NoCity = "no city"

def testNoResults(soup):
    tdTestNoResults = soup.first("td", {"class":"supertextb", "style":"color:#CC0000"})
    if tdTestNoResults:
        text = getAllTextFromTag(tdTestNoResults).strip()
        if text.startswith("Your search returned too many"):
            return TOO_MANY_RESULTS
        elif text.startswith("Your search returned no"):
            return NO_RESULTS
        elif text.startswith("No selection made"):
            return NO_RESULTS
        elif text.startswith("No listing was found"): ##  for the phone number you've entered
            return NO_RESULTS
        elif text.startswith("We did not find a listing"): ##  for the phone number you entered
            return NO_RESULTS
        else:
            return UNKNOWN_FORMAT
    div = soup.first("div",{"id":"error"})
    if div:
        text = getAllTextFromTag(div).strip()
        if text.startswith("We\'re sorry."):
            return NO_RESULTS
        if text.startswith("No selection made."):
            return NO_RESULTS
        if text.startswith("Your search returned too many"):
            return TOO_MANY_RESULTS
    return RESULTS_DATA

def personSearch2(htmlTxt):
    returned = []
    soup = BeautifulSoup21.BeautifulSoup(htmlTxt)

    res = testNoResults(soup)
    if RESULTS_DATA != res:
        return (res, None)

    divTag = soup.first("div", {"id" : "subtext"})
    if not divTag:
        print "No divTag"
        return (UNKNOWN_FORMAT, None)
    #print "Found divTag"
    #print divTag
    #print
    #print divTag.span
    #print
    #print divTag.span.strong
    spanTag = divTag.span
    strongTag = divTag.span.strong
    nameStr = convertNumberedEntities(strongTag.string.strip()) #.strip() #.string.strip()
    print nameStr
    addrStreetTag = spanTag.nextSibling
    addrStreet = addrStreetTag.string.strip()
    print addrStreet
    addrCityTag = addrStreetTag.nextSibling.nextSibling
    addrCity = addrCityTag.string.strip()
    print addrCity
    addrPhoneTag = addrCityTag.nextSibling.nextSibling
    addrPhone = addrPhoneTag.string.strip()
    print addrPhone
    #print strongTag.nextSibling
    #print strongTag.nextSibling.nextSibling
    return (UNKNOWN_FORMAT, None)

# Returns data in format:
# [name, address, city, phone]+ in UDF
def personSearch(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    res = testNoResults(soup)
    if RESULTS_DATA != res:
        return (res, None)

    # TODO: different search
    tableSummaryList = soup.first("table", {"id":"listings"})
    if tableSummaryList:
        for tr in tableSummaryList.fetch("tr"):
            td = tr.first("td")
            if td:
                spanList = td.fetch("span",{"id":"subtext"})
                if len(spanList) == 2:
                    spanTextB = spanList[0]
                    spanText = spanList[1]
                    if spanText and spanTextB:
                        name = getAllTextFromTag(spanTextB).replace("\t"," ").replace("\n"," ").replace("   "," ").replace("  "," ").strip()
                        textToSplit = getAllTextFromToInBrFormat(spanText,getLastElementFromTag(spanText).next)
                        textSplitted = textToSplit.split("<br>")
                        if len(textSplitted) > 2:
                            address = textSplitted[0].strip()
                            city = textSplitted[1].strip()
                            phone = textSplitted[2].strip()
                            returned.append([name, address, city, phone])
                        elif len(textSplitted) == 2:
                            address = ""
                            city = textSplitted[0].strip()
                            phone = textSplitted[1].strip()
                            returned.append([name, address, city, phone])
        if len(returned>0):
            return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))
        
    # some special numbers...
    tableSummaryList = soup.first("table", {"id":"listings"})
    name = ""
    if tableSummaryList:
        for tr in tableSummaryList.fetch("tr"):
            td = tr.first("td")
            if td:
                spanList = td.fetch("span",{"id":"subtext"})
                if 0 == len(spanList):
                    spanList = td.fetch("div",{"id":"subtext"})
                if len(spanList) == 1:
                    name = getAllTextFromTag(spanList[0])
                elif len(spanList) % 4 == 0:
                    ind = 0
                    while ind < len(spanList):
                        smallName = getAllTextFromTag(spanList[ind])
                        textToSplit = getAllTextFromToInBrFormat(spanList[ind+3],getLastElementFromTag(spanList[ind+3]).next)
                        parts = textToSplit.split("<br>")
                        if len(parts) > 2:
                            address = parts[0].strip()
                            city = parts[1].strip()
                            phone = parts[2].strip()
                            returned.append([name + " (%s)"%smallName, address, city, phone])
                        elif len(parts) == 2:
                            address = smallName
                            city = parts[0].strip()
                            phone = parts[1].strip()
                            returned.append([name, address, city, phone])
                        ind += 4
        if len(returned>0):
            return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))

    return (UNKNOWN_FORMAT, None)

def sortByCityFunc(el1, el2):
    # el1 and el2 are tuples with first element being city name, 
    # second its calling code
    return cmp(el1[0], el2[0])

# Return data in format:
# RESULTS_DATA (in UDF)
#   country code(s)
#   city, codes
def internationalCodeSearch(htmlTxt):
    result = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    res = testNoResults(soup)
    if RESULTS_DATA != res:
        return (res, None)
    # Country code(s)
    tableList = soup.fetch("table", {"summary":"Codes Results"})
    if len(tableList) != 1:
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    # found country code
    tdListA = tableList[0].fetch("td",{"style":"%padding-left:5px;"})
    tdListB = tableList[0].fetch("td",{"style":"%line-height:14pt;"})
    if len(tdListA) != len(tdListB):
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    cityCodeList = []
    for i in range(len(tdListA)):
        if 0 == i:
            result.append([getAllTextFromTag(tdListB[i])])
        else:
            city = getAllTextFromTag(tdListA[i])
            code = getAllTextFromTag(tdListB[i])
            cityCodeList.append((city,code))
    # sort the (city,code) list by city
    cityCodeList.sort(sortByCityFunc)
    for el in cityCodeList:
        result.append(el)
    return (RESULTS_DATA,universalDataFormatReplaceEntities(result))


# Return data in format:
# RESULTS_DATA
#
def reverseZIPCodeLookup(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    res = testNoResults(soup)
    if RESULTS_DATA != res:
        return (res, None)
    # results (one? we handle more than one)
    tables = soup.fetch("table", {"summary":"Codes Results"})
    if 0 == len(tables):
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    trList = []
    for tab in tables:
        trList += tab.fetch("tr")
    for tr in trList:
        tdList = tr.fetch("td")
        if len(tdList) == 3:
            city     = getAllTextFromTag(tdList[0])
            country  = getAllTextFromTag(tdList[1])
            timezone = getAllTextFromTag(tdList[2])
            if city != "New Search":
                smallList = (city,country,timezone)
                returned.append(smallList)
        elif len(tdList) == 2: #special case (911)
            city     = getAllTextFromTag(tdList[0])
            country  = getAllTextFromTag(tdList[1])
            if city != "New Search":
                smallList = (city,country,"")
                returned.append(smallList)
    if len(returned) == 0:
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))

# Return data in format:
# RESULTS_DATA
#
def reverseAreaCodeLookup(htmlTxt):
    return reverseZIPCodeLookup(htmlTxt)

# Return data in format:
# RESULTS_DATA
# MULTIPLE_SELECT
#
def areaCodeByCity(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    res = testNoResults(soup)
    if RESULTS_DATA != res:
        return (res, None)

    resultsTable = soup.first("table", {"summary":"Results Content"})
    if resultsTable:
        strong = resultsTable.first("strong")
        if strong:
            if getAllTextFromTag(strong).startswith("Multiple cities with"):
                aList = resultsTable.fetch("a")
                for aItem in aList:
                    city = getAllTextFromTag(aItem)
                    returned.append(city)
                if len(returned) == 0:
                    return (UNKNOWN_FORMAT,m411UnknownFormatText)
                return (MULTIPLE_SELECT,string.join(returned,"\n"))
    # results
    return reverseZIPCodeLookup(htmlTxt)

    tables = soup.fetch("table", {"summary":"Search Results"})
    if 0 == len(tables):
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    trList = []
    for tab in tables:
        trList += tab.fetch("tr")
    for tr in trList:
        tdList = tr.fetch("td")
        if len(tdList) == 3:
            code     = getAllTextFromTag(tdList[0]).strip()
            country  = getAllTextFromTag(tdList[1]).strip()
            timezone = getAllTextFromTag(tdList[2]).strip()
            if code != "New Search":
                smallList = (code,country,timezone)
                returned.append(smallList)
    if len(returned) == 0:
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))


def ZIPCodeByCity(htmlTxt):
    return areaCodeByCity(htmlTxt)

# Returns data in format: (this is not from 411, but from www.dexonline.com)
# RESULTS_DATA - in UDF
#
# NO_CITY - if city name not found
#
# MULTIPLE_SELECT - when category search is running (in udf)
#
def businessSearchDex(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # city multiselect (we dont support this on client, so no_city returned)
    span = soup.first("span", {"class":"title"})
    if span:
        if getAllTextFromTag(span).replace("\n"," ").strip().startswith("We found these cities"):
            return (NO_CITY, None)

    # error
    span = soup.first("span", {"class":"error"})
    if span:
        return (NO_RESULTS, None)
    
    # results
    resultsCount = 0
    tdList = soup.fetch("td" ,{"width":"360", "align":"left", "valign":"top"})
    if 0 < len(tdList):
        for td in tdList:
            brList = td.fetch("br")
            bList = td.fetch("b")
            name = ""
            address = ""
            city = ""
            phone = ""
            if len(bList) > 0:
                name = getAllTextFromTag(bList[0]).replace("\n","").strip()
            if len(bList) > 1:
                phone = getAllTextFromTag(bList[1]).replace("\n","").strip()
            if len(brList) == 3:
                address = getAllTextFromTag(brList[0].next).replace("\n","").strip()
                city = getAllTextFromTag(brList[1].next).replace("\n","").strip()
            if len(brList) == 2:
                city = getAllTextFromTag(brList[0].next).replace("\n","").strip()
            smallList = [name, address, city, phone]
            returned.append(smallList)
            resultsCount += 1

    if 0 == resultsCount:
        divTitle = soup.fetch("div",{"id":"alphatitle"})
        divInfo  = soup.fetch("div",{"id":"alphalisting"})
        if len(divInfo) == len(divTitle) and len(divTitle) > 0:
            index = 0
            while index < len(divTitle):
                name = makeTitleCase(getAllTextFromTag(divTitle[index])).strip()
                table = divInfo[index].first("table")
                tableEnd = divInfo[index]
                if table:
                    tableEnd = getLastElementFromTag(table).next
                aItem = divInfo[index].first("a", {"href":"/servlet/ActionServlet?%"})
                if not aItem:
                    aItem = getLastElementFromTag(divInfo[index])
                address = ""
                city = ""
                phone = ""
                text = getAllTextFromToInBrFormat(tableEnd, aItem)
                parts = text.split("<br>")
                # find phone (in <b>)
                for p in parts:
                    if -1 != p.find("<b>"):
                        phone = p.replace("<b>","").replace("</b>","").strip()
                if len(parts) >= 3:
                    address = makeTitleCase(parts[0]).strip()
                    city = parts[1]
                if len(parts) == 2:
                    if phone != "":
                        city = parts[0]
                parts = city.split("&nbsp;")
                parts[0] = makeTitleCase(parts[0])
                city = string.join(parts,"").strip()
                smallList = [name, address, city, phone]
                returned.append(smallList)
                resultsCount += 1
                index += 1

    if 0 == resultsCount:
        spanList = soup.fetch("span", {"class":"h2-3Title"})
        if 0 < len(spanList):
            for span in spanList:
                next = getLastElementFromTag(span)
                dist = 0
                aItem = None
                while dist < 5 and next:
                    next = next.next
                    if isinstance(next, Tag):
                        if next.name == "a":
                            dist = 10
                            aItem = next
                    dist += 1
                if aItem:
                    name = getAllTextFromTag(aItem)
                    href = aItem['href']
                    returned.append((name,href))
                    resultsCount += 1
        if 0 == resultsCount:
            return (UNKNOWN_FORMAT, m411UnknownFormatText)
        else:
            return (MULTIPLE_SELECT,universalDataFormatReplaceEntities(returned))
            
    return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))

# Parse result of switchboard business search query
# Possible results:
#   RESULTS_DATA + list of [name, address, city, phone] in UDF
#   NO_RESULTS if search returns no results
# TODO:
#  NO_CITY - if city name was not found
def parseSwitchboardBusiness(htmlTxt):
    result = []
    #print "parseSwitchboardBusiness\n"

    # the "no results" page has this string in it: "<!--YP_NORESULTS_KERNAL-->"
    if -1 != htmlTxt.find("YP_NORESULTS_KERNAL"):
        return (NO_RESULTS, None)

    soup = BeautifulSoup21.BeautifulSoup(htmlTxt)
    listings = soup.fetch("div", {"class" : "listing"})

    for listing in listings:
        nameDiv = listing.first("div", {"class" : "name"})
        nameTxt = nameDiv.string.strip()
        #print nameTxt

        addrDiv = listing.first("div", {"class" : "address"})
        addrTxt = addrDiv.next.strip()
        # TODO: somehow figureout zip code from url or fetch the page and parse it
        cityTxt = addrDiv.br.next.strip().replace("zip code", "")
        #print addrTxt
        #print cityTxt

        phoneDivs = listing.fetch("div", {"class" : "phone"})
        phoneTxt = ""
        for phoneDiv in phoneDivs:
            spans = phoneDiv.fetch("span")
            if 0 == len(spans):
                continue
            phoneTxtList = [span.string.strip() for span in spans]
            phoneTxt = string.join(phoneTxtList, " ")
            if len(phoneTxt) > 0:
                break
        #print phoneTxt
        #print
        result.append([nameTxt, addrTxt, cityTxt, phoneTxt])

    if 0 == len(result):
        return (NO_RESULTS, None)
    return (RESULTS_DATA, universalDataFormatReplaceEntities(result))
    #return (UNKNOWN_FORMAT,m411UnknownFormatText)

# Returns data in format: (this is not from 411, but from www.switchboard.com)
# RESULTS_DATA - in UDF
#
# NO_CITY - if city name not found
#
# MULTIPLE_SELECT - when category search is running (in udf)
#
# TODO: remove this, parseSwitchboardBusiness is the new godness
def parseSwitchboardBusinessOld(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # city multiselect (we dont support this on client, so no_city returned)
    span = soup.first("span", {"class":"lr"})
    if span:
        if getAllTextFromTag(span).replace("\n"," ").strip().startswith("Sorry -"):
            return (NO_CITY, None)

    # error
    div = soup.first("div", {"class":"s14err"})
    if div:
        return (NO_RESULTS, None)
    
    td = soup.first("td", {"class":"mrb"})
    if td:
        text = getAllTextFromTag(td)
        if text.startswith("Sorry"):
            return (NO_RESULTS, None)
    # results
    resultsCount = 0
    tableList = soup.fetch("table", {"cellspacing":"0", "cellpadding":"0", "border":"0", "width":"444"})
    ignoreNextTable = 0
    index = -1
    for table in tableList:
        index += 1
        divList = table.fetch("div", {"class":"Fm"})
        divList += table.fetch("div", {"class":"Lm"})
        if len(divList) > 0:
            if len(divList) > 1 and ignoreNextTable == 0:
                name = getAllTextFromTag(divList[0]).replace("\n","").replace("\x0d","").strip()
                address = ""
                city = ""
                phone = ""
                if len(divList) > 1:
                    div = divList[1]
                    phoneTable = div.first("table")
                    if phoneTable:
                        if len(phoneTable.fetch("td")) > 1:
                            if getAllTextFromTag(phoneTable.fetch("td")[0]).replace("\n","").replace("\x0d","").strip().startswith("Phone"):
                                phone = getAllTextFromTag(phoneTable.fetch("td")[1]).replace("\n","").replace("\x0d","").strip().split("&nbsp;")[0]
                        script = div.first("script")
                        if not script:
                            script = div.first("SCRIPT")
                            if not script:
                                script = phoneTable
                        textToSplit = getAllTextFromToInBrFormat(div, script).replace("\n","").replace("\x0d","").strip()
                        textSplitted = textToSplit.split("<br>")
                        if len(textSplitted) == 2:
                            address = textSplitted[0].strip()
                            city = textSplitted[1].strip()
                        if len(textSplitted) == 1:
                            city = textSplitted[0].strip()
                smallList = [name, address, city, phone]
                returned.append(smallList)
                resultsCount += 1
            elif ignoreNextTable == 0:
                name = getAllTextFromTag(divList[0]).replace("\n","").replace("\x0d","").strip()
                address = ""
                city = ""
                phone = ""

                if index < len(tableList):
                    divList = tableList[index+1].fetch("div", {"class":"Fm"})
                    divList += tableList[index+1].fetch("div", {"class":"Lm"})
                    if len(divList) > 0:
                        div = divList[0]
                        phoneTable = div.first("table")
                        if not phoneTable:
                            if len(divList) > 1:
                                div = divList[1]
                                phoneTable = div.first("table")
                        if phoneTable:
                            if len(phoneTable.fetch("td")) > 1:
                                if getAllTextFromTag(phoneTable.fetch("td")[0]).replace("\n","").replace("\x0d","").strip().startswith("Phone"):
                                    phone = getAllTextFromTag(phoneTable.fetch("td")[1]).replace("\n","").replace("\x0d","").strip().split("&nbsp;")[0]
                            script = div.first("script")
                            if not script:
                                script = div.first("SCRIPT")
                                if not script:
                                    script = phoneTable
                            textToSplit = getAllTextFromToInBrFormat(div, script).replace("\n","").replace("\x0d","").strip()
                            textSplitted = textToSplit.split("<br>")
                            if len(textSplitted) == 2:
                                address = textSplitted[0].strip()
                                city = textSplitted[1].strip()
                            if len(textSplitted) == 1:
                                city = textSplitted[0].strip()
                smallList = [name, address, city, phone]
                returned.append(smallList)
                resultsCount += 1
                ignoreNextTable = 1
            else:
                ignoreNextTable = 0
        else:
            ignoreNextTable = 0

    if 0 == resultsCount:
        aList = soup.fetch("a", {"class":"ciplink"})
        for aItem in aList:
            name = getAllTextFromTag(aItem)
            href = aItem['href']
            returned.append([name,href])
            resultsCount += 1
        if 0 == resultsCount:
            return (UNKNOWN_FORMAT,m411UnknownFormatText)
        else:
            return (MULTIPLE_SELECT,universalDataFormatReplaceEntities(returned))

    return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))

switchboardServerUrlBusinessSearch            = "http://www.switchboard.com/bin/cgidir.dll?PR=116&mem=1&L=%s&A=&T=%s&S=%s&Z=&ST=1&SD=&LNK=43:24"
switchboardServerUrlBusinessSearchZip         = "http://www.switchboard.com/bin/cgidir.dll?PR=116&mem=1&L=%s&A=&T=&Z=%s&S=%s&ST=1&SD=&LNK=43:24"
switchboardServerUrlBusinessSearchCategory    = "http://www.switchboard.com/bin/cgidir.dll?MEM=1&PR=133&Search=Search&KW=%s&T=%s&Z=&S=%s"
switchboardServerUrlBusinessSearchCategoryZip = "http://www.switchboard.com/bin/cgidir.dll?MEM=1&PR=133&Search=Search&KW=%s&T=&Z=%s&S=%s"

def retrieveSwitchboardBusiness(name,cityOrZip,state,surrounding,categoryOrName):
    url = ""
    zip = False
    if cityOrZip.isdigit() and len(cityOrZip) == 5:
        zip = True
    if categoryOrName == "Name":
        if zip:
            url = switchboardServerUrlBusinessSearchZip % (urllib.quote(name),urllib.quote(cityOrZip),urllib.quote(state))
        else:
            url = switchboardServerUrlBusinessSearch % (urllib.quote(name),urllib.quote(cityOrZip),urllib.quote(state))
    if categoryOrName == "Category":
        if zip:
            url = switchboardServerUrlBusinessSearchCategoryZip % (urllib.quote(name),urllib.quote(cityOrZip),urllib.quote(state))
        else:
            url = switchboardServerUrlBusinessSearchCategory % (urllib.quote(name),urllib.quote(cityOrZip),urllib.quote(state))

    # using cached for testing
    #htmlText = getHttpCached(url)
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = parseSwitchboardBusiness(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Business-Search", name+","+cityOrZip+","+state+","+surrounding+","+categoryOrName, htmlText, url)
    return res, data

# Given a string "firstName        lastName", strip the whitespace
# and return "firstName lastName"
def cleanupName(txt):
    if -1 == txt.find(" "):
        return txt
    names = txt.split(" ", 1)
    nameClean = string.join([name.strip() for name in names], " ")
    return nameClean
    
# Returns data in format: [name, address, city, phone]+ in UDF
def parse411ReversePhoneLookup(htmlTxt):
    result = []
    if -1 != htmlTxt.find("We did not find a listing"):
        print "parse411ReversePhoneLookup: no results"
        return (NO_RESULTS, None)
    soup = BeautifulSoup21.BeautifulSoup(htmlTxt)
    div = soup.first("div", {"id" : "subtext"})
    if not div:
        print "parse411ReversePhoneLookup: no div"
        return (UNKNOWN_FORMAT, None)

    nameTxt = div.span.strong.string
    if not nameTxt:
        print "parse411ReversePhoneLookup: no name"
        return (UNKNOWN_FORMAT, None)
    nameTxt = convertNumberedEntities(nameTxt)
    nameTxt = convertNamedEntities(nameTxt)
    nameTxt = cleanupName(nameTxt)
    #print nameTxt

    addr = div.next.next.next.next.next.next
    addressTxt = addr.string
    #print addressTxt

    city = addr.next.next
    cityTxt = city.string
    #print cityTxt

    phone = city.next.next
    phoneTxt = phone.string
    #print phoneTxt

    result.append([nameTxt, addressTxt, cityTxt, phoneTxt])
    return (RESULTS_DATA, universalDataFormatReplaceEntities(result))

def retrieve411ReversePhone(xxx, yyy, zzzz):
    url = "http://www.411.com/search/Reverse_Phone?phone=%s-%s-%s" % (xxx,yyy,zzzz)
    # using cached for testing
    #htmlText = getHttpCached(url)
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = parse411ReversePhoneLookup(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Reverse-Phone", xxx + "-" + yyy + "-" + zzzz, htmlText, url)
    return res, data    

def main():
    #retrieveSwitchboardBusiness("hill", "", "IL", "No", "Name")
    #retrieve411ReversePhone("777", "682", "9999")
    retrieve411ReversePhone("770", "682", "1533")

if __name__ == "__main__":
    main()

