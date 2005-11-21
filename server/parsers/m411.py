#### Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  411
#  http://yp.com
#
import string, arsutils, sys
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise
from ResultType import *
from entities import convertNamedEntities
from entities import convertNumberedEntities
from epicurious import uncapitalizeText
from parserUtils import *

# flags - just for tests
m411NoResultsText = None
m411UnknownFormatText = None
m411TooManyResults = None
m411NoCity = None
#m411NoResultsText = "no results"
#m411UnknownFormatText = "unknown format"
#m411TooManyResults = "too many results"
#m411NoCity = "no city"

# good for all except: businessSearch and reversePhoneLookup
def m411testNoResults(soup):
    noResults = soup.fetch("td",{"align":"left", "valign":"top"})
    for item in noResults:
        if len(item.contents) > 0:
            if str(item.contents[0]).replace("\n","").strip().startswith("Your search returned no results."):
                return NO_RESULTS
            if str(item.contents[0]).replace("\n","").strip().startswith("No results."):
                return NO_RESULTS
    div = soup.first("div",{"id":"error"})
    if div:
        if getAllTextFromTag(div).replace("\n","").strip().startswith("We\'re sorry."):
            return NO_RESULTS
        if getAllTextFromTag(div).replace("\n","").strip().startswith("No selection made."):
            return NO_RESULTS
    return RESULTS_DATA

# test no results in Business Search
def m411testNoResultsBusinessSearch(soup):
    noResults = soup.fetch("td",{"width":"425"})
    for item in noResults:
        for content in item.fetch("span", {"class":"%"}):
            if str(content.contents[0]).startswith("City or Zip"):
                return NO_CITY
        if str(item.contents[0]).replace("\n","").strip().startswith("Your Business Name search yielded 0 results."):
            return NO_RESULTS
        if str(item.contents[0]).replace("\n","").strip().startswith("Your Category search yielded 0 results."):
            return NO_RESULTS
    div = soup.first("div",{"id":"error"})
    if div:
        if getAllTextFromTag(div).replace("\n","").strip().startswith("We're sorry.  Your search returned no results."):
            return NO_RESULTS
    return RESULTS_DATA

# test no results in Reverse Phone Lookup
def m411testNoResultsReversePhoneLookup(soup):
    noResults = soup.fetch("font",{"color":"#FF0000"})
    for item in noResults:
        if str(item.contents[0]).replace("\n","").strip().startswith("Missing or bad input."):
            return NO_RESULTS
        if str(item.contents[0]).replace("\n","").strip().startswith("No results."):
            return NO_RESULTS
    div = soup.first("div",{"id":"error"})
    if div:
        if getAllTextFromTag(div).replace("\n","").strip().startswith("We're sorry.  Your search returned no results."):
            return NO_RESULTS
    return RESULTS_DATA


# Returns data in format:
# RESULTS_DATA
#  Name:<name>
#  Address:<address>
#  City:<city>
#  Phone:<phone>
#  ...
#  Name:<name>
#  Address:<address>
#  City:<city>
#  Phone:<phone>
#
#  line separator "\n". For example:
#
#  Name:21-2 Happy Barbers
#  Address:6412 24th Ave Nw
#  City:Seattle, WA 98107
#  Phone:(206) 782-2173
#
# NO_CITY - if city name or zip code not found
#
def businessSearch(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    noResults = m411testNoResultsBusinessSearch(soup)
    if(noResults == NO_RESULTS):
        return (NO_RESULTS,m411NoResultsText)
    if(noResults == NO_CITY):
        return (NO_CITY,m411NoCity)

    ttl = soup.fetch("td", {"class":"TTLPREF"})
    ttl += soup.fetch("td", {"class":"TTLBASC"})
    smallList = []
    resultsCount = 0
    for item in ttl:
        h2List = item.fetch("h2")
        for h2 in h2List:
            # name
            string = uncapitalizeText(getAllTextFromTag(h2))
            smallList = [string.replace("\n","").strip()]
            # address
            # city
            lastInH2 = getLastElementFromTag(h2)
            lastInItem = getLastElementFromTag(item)
            brList = item.fetch("br")
            if 0 == len(brList):
                smallList.append("")
                smallList.append(getAllTextFromTo(lastInH2.next, lastInItem.next).replace("\n","").strip())
            elif 1 == len(brList):
                smallList.append(getAllTextFromTo(lastInH2.next, brList[0]).replace("\n","").strip())
                smallList.append(getAllTextFromTo(brList[0].next, lastInItem.next).replace("\n","").strip())
            else:
                smallList.append("")
                smallList.append("")
        # phone
        if 0 == len(h2List):
            smallList.append(getAllTextFromTag(item).replace("\n","").strip())
            returned.append(smallList)
            resultsCount += 1
    if 0 == resultsCount:
        trList = soup.fetch("tr")
        for trItem in trList:
            lenTd = len(trItem.fetch("td"))
            tdItem = trItem.fetch("td",{"colspan":"4"})
            if 1 == lenTd and 1 == len(tdItem):
                aList = tdItem[0].fetch("a", {"href":"yplist.php%"})
                brList = tdItem[0].fetch("br")
                if len(aList) == len(brList):
                    for aItem in aList:
                        name = uncapitalizeText(getAllTextFromTag(aItem))
                        name.replace("\n","").strip()
                        # remove information in bracers?   ...  (21)
                        ##name = name.split("(")[0].strip()
                        href = aItem['href']
                        returned.append((name,href))
                        resultsCount += 1
        if 0 == resultsCount:
            return (UNKNOWN_FORMAT,m411UnknownFormatText)
        else:
            return (MULTIPLE_SELECT,universalDataFormatReplaceEntities(returned))
            
    return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))


# Returns data in format:
# TOO_MANY_RESULTS - when there is too many results
#
# NO_CITY - when there is no such city or zip code
#
# MULTIPLE_SELECT - city is ambigous
#  city
#  line separator "\n"
#  "Seattle, WA"
#
# RESULTS_DATA in UDF
#
def personSearch(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    noResults = m411testNoResults(soup)
    if NO_RESULTS == noResults:
        return (noResults,m411NoResultsText)
    ttlPref = soup.first("td",{"class":"TTLPREF"})
    if not ttlPref:
        ttlPref = soup.first("span",{"class":"TTLPREF"})
    if not ttlPref:
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    # too many results:
    font = ttlPref.first("font",{"color":"#FF0000"})
    if font:
        if "No results." == font.contents[0]:
            return (NO_RESULTS,m411NoResultsText)
        if "Results found in multiple cities." == font.contents[0]:
            brList = ttlPref.fetch("br")
            brList = brList[4:] ## skip text about select
            for br in brList:
                text = str(br.next).replace("<br />","").replace("\n","").strip()
                if len(text) > 0:
                    returned.append(text)
            return (MULTIPLE_SELECT, string.join(returned,"\n"))
        return (TOO_MANY_RESULTS,m411TooManyResults)
    # results:
    brList = ttlPref.fetch("br")
    resultsCount = len(brList) - 2
    if 0 == resultsCount:
        # no city?
        if "NO CITY FOUND" == str(brList[1].next).replace("\n","").strip():
            return (NO_CITY,m411NoCity)
    results = resultsCount/5
    if results*5 != resultsCount:    ## test if number of <br> is 5*n+2
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    # get them
    brList = brList[1:]  ## skip first br
    counter = 0
    smallList = []    
    for br in brList:
        text = str(br.next).replace("<br />","").replace("\n","").strip()
        if results > 0:
            if 0 == counter:
                smallList = [text]
            if 1 == counter or 2 == counter:
                smallList.append(text)
            if 3 == counter:
                smallList.append(text)
                returned.append(smallList)                
                results -= 1
        counter += 1
        if 5 == counter:
            counter = 0
    return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))


# Return data in format:
# RESULTS_DATA
# MULTIPLE_SELECT
#
def areaCodeByCity(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    noResults = m411testNoResults(soup)
    if NO_RESULTS == noResults:
        return (noResults,m411NoResultsText)

    # multiple select list (why they call it multiple select in 4.html ?)
    div = soup.first("div", {"style":"padding: 3px 3px 3px 3px;"})
    if div:
        strong = div.first("strong")
        if strong:
            if getAllTextFromTag(strong).startswith("Multiple "):
                aList = div.fetch("a")
                for aItem in aList:
                    city = getAllTextFromTag(aItem)
                    returned.append(city)
                if len(returned) > 0:
                    return (MULTIPLE_SELECT,string.join(returned,"\n"))
                else:                    
                    return (UNKNOWN_FORMAT,m411UnknownFormatText)
    return reverseAreaCodeLookup(htmlTxt)

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
    noResults = m411testNoResults(soup)
    if NO_RESULTS == noResults:
        return (noResults,m411NoResultsText)
    # results
    tableList = soup.fetch("table",{"id":"listings"})
    if len(tableList) != 1:
        return UNKNOWN_FORMAT, None
    trList = tableList[0].fetch("tr")
    cityCodeList = []
    for trItem in trList:
        if 0 == len(trItem.fetch("tr")):
            tdList = trItem.fetch("td", {"id":"subtextid"})
            if 2 == len(tdList):
                if 0 == len(result):
                    result.append([getAllTextFromTag(tdList[1])])
                else:
                    city = getAllTextFromTag(tdList[0])
                    code = getAllTextFromTag(tdList[1])
                    cityCodeList.append((city,code))
    # sort the (city,code) list by city
    cityCodeList.sort(sortByCityFunc)
    for el in cityCodeList:
        result.append(el)
    if 0 == len(result):
        return UNKNOWN_FORMAT, None
    return (RESULTS_DATA,universalDataFormatReplaceEntities(result))
           

# Return data in format:
# RESULTS_DATA
#  page should (but not need to) be in sorted format: (alpha-sorted results)
#   http://yp.whitepages.com/log_feature/sort/search/Reverse_Areacode?npa=507&sort=alpha
#
def reverseAreaCodeLookup(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    noResults = m411testNoResults(soup)
    if NO_RESULTS == noResults:
        return (noResults,m411NoResultsText)
    # results
    tableList = soup.fetch("table", {"id":"listings"})
    if len(tableList) != 1:
        return UNKNOWN_FORMAT, None

    trList = tableList[0].fetch("tr")
    if len(trList) == 0:
        return UNKNOWN_FORMAT, None
    # ignore headers ([1:])
    for trItem in trList[1:]:
        if 0 == len(trItem.fetch("tr")): # they have sth screwed with this <tr><tr> .... </tr></tr>
            tdList = trItem.fetch("td", {"id":"subtextid"})
            if 3 == len(tdList):
                city     = getAllTextFromTag(tdList[0])
                country  = getAllTextFromTag(tdList[1])
                timezone = getAllTextFromTag(tdList[2])
                smallList = (city,country,timezone)
                returned.append(smallList)
            elif 2 == len(tdList):
                city     = getAllTextFromTag(tdList[0])
                country  = ""
                timezone = getAllTextFromTag(tdList[1])
                smallList = (city,country,timezone)
                returned.append(smallList)

    if 0 == len(returned):
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))


# Return data in format:
# RESULTS_DATA in UDF
#  <Person> <Address> <City> <Phone>
#
def reversePhoneLookupWhitepages(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    noResults = m411testNoResultsReversePhoneLookup(soup)
    if NO_RESULTS == noResults:
        return (noResults,m411NoResultsText)
    div = soup.first("div", {"class":"listings"})
    if div:
        for table in div.fetch("table"):
            for tr in table.fetch("tr"):
                text1 = tr.first("div",{"class":"textb"})
                text2 = tr.first("div",{"class":"text"})
                if text1 and text2:
                    name = getAllTextFromTag(text1)
                    cont = getAllTextFromToInBrFormat(text2, getLastElementFromTag(text2).next)
                    parts = cont.split("<br>")
                    (address,city,phone) = ("","","")
                    if len(parts) == 3:
                        (address,city,phone) = parts
                    if len(parts) == 2:
                        (city,phone) = parts
                    if len(parts) == 4:
                        (prefix,address,city,phone) = parts
                    returned.append((name,address.strip(),city.strip(),phone.strip()))
    if len(returned) == 0:
        return UNKNOWN_FORMAT, None
    return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))

# Return data in format:
# RESULTS_DATA in UDF
#  <Person> <Address> <City> <Phone>
#
def reversePhoneLookup(htmlTxt):
    returned = []
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    noResults = m411testNoResultsReversePhoneLookup(soup)
    if NO_RESULTS == noResults:
        return (noResults,m411NoResultsText)
    tdWithResults = soup.first("td",{"class":"TTLPREF"})
    if not tdWithResults:
        tdWithResults = soup.first("span",{"class":"TTLPREF"})
    if not tdWithResults:
        return (UNKNOWN_FORMAT,m411UnknownFormatText)
    # results are inside <td>
    fontColor = tdWithResults.first("font")
    if fontColor:
        # "No details available."
        counter = 0
        for br in tdWithResults.fetch("br"):
            # we belive that after 6th <br> is city
            if counter == 5:
                city =  "%s" % str(br.next).replace("\n","").strip()
                returned.append(["","",city,""])
            counter += 1
    else:
        # all data, or city & phone
        counter = 0
        person = ""
        address = ""
        city = ""
        phone = ""
        for br in tdWithResults.fetch("br"):
            # 7 <br> in <td> 
            if 1 == counter:
                if not isinstance(br.next,Tag):
                    person = "%s" % str(br.next).replace("\n","").strip()
            if 2 == counter:
                if not isinstance(br.next,Tag):
                    address = "%s" % str(br.next).replace("\n","").strip()
            if 3 == counter:
                city = "%s" % str(br.next).replace("\n","").strip()
            if 4 == counter:
                phone = "%s" % str(br.next).replace("\n","").strip()
            counter += 1
        returned.append((person,address,city,phone))    
    return (RESULTS_DATA,universalDataFormatReplaceEntities(returned))


# Return data in format:
# RESULTS_DATA
#
def reverseZIPCodeLookup(htmlTxt):
    return reverseAreaCodeLookup(htmlTxt)

# Return data in format:
# RESULTS_DATA
# MULTIPLE_SELECT
#
def ZIPCodeByCity(htmlTxt):
    return areaCodeByCity(htmlTxt)

def usage():
    print "usage: movies.py [-file $fileToParse]"

def main():
    fileName = arsutils.getRemoveCmdArg("-file")
    if None == fileName:
        usage()
        sys.exit(0)

    if 1 != len(sys.argv):
        usage()
        sys.exit(0)

    fo = open(fileName, "rb")
    htmlTxt = fo.read()
    fo.close()
    (resultType, resultBody) = reversePhoneLookup(htmlTxt, fileName, fDebug=True)

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
