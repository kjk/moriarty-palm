from parserUtils import *
from ResultType import *
from arsutils import log, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC, exceptionAsStr
from parserErrorLogger import logParsingFailure
import urllib
import urllib2
import m411
import m411_by411
from Retrieve import getHttp

## Person Search

def _retrieve_yp_person(firstName,lastName,cityOrZip,state):
    url = "http://www.yp.com/white-pages-results.php?f=%s&firstname_begins_with=1&l=%s&name_begins_with=1&c=%s&s=%s&client=&ver=1.4&type=r"
    url = url % (urllib.quote(firstName),urllib.quote(lastName),urllib.quote(cityOrZip),urllib.quote(state))
    htmlText = getHttp(url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411.personSearch(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Person-Search", firstName+";"+lastName+";"+cityOrZip+";"+state, htmlText, url)
    return res, data    

def _retrieve_411_person(firstName,lastName,cityOrZip,state):
    url = "http://www.411.com/search/Find_Person?firstname_begins_with=1&firstname=%s&name_begins_with=1&name=%s&city_zip=%s&state_id=%s"
    url = url % (urllib.quote(firstName),urllib.quote(lastName),urllib.quote(cityOrZip),urllib.quote(state))
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411_by411.personSearch(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Person-Search", firstName+";"+lastName+";"+cityOrZip+";"+state, htmlText, url)
    return res, data

_g_retrieve_person = [
    _retrieve_yp_person,
    _retrieve_411_person
]

def retrievePerson(firstName,lastName,cityOrZip,state):
    global _g_retrieve_person
    for func in _g_retrieve_person:
        try:
            res, data = func(firstName,lastName,cityOrZip,state)
            if RETRIEVE_FAILED != res and UNKNOWN_FORMAT != res:
                return res, data
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to parse data\nreason:%s\n" % (txt))
    return (RETRIEVE_FAILED, None)

## international Code

def _retrieve_yp_international(code):
    url = "http://yp.whitepages.com/search/Find_Intl_Code?country_id=%s"
    url = url % code
    htmlText = getHttp(url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411.internationalCodeSearch(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-International-Code", code, htmlText, url)
    return res, data    

def _retrieve_411_international(code):
    url = "http://www.411.com/search/Find_Intl_Code?country_id=%s"
    url = url % code
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411_by411.internationalCodeSearch(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-International-Code", code, htmlText, url)
    return res, data    

_g_retrieve_international = [
    _retrieve_411_international,
    _retrieve_yp_international
]

def retrieveInternational(code):
    global _g_retrieve_international
    for func in _g_retrieve_international:
        try:
            res, data = func(code)
            if RETRIEVE_FAILED != res and UNKNOWN_FORMAT != res:
                return res, data
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to parse data\nreason:%s\n" % (txt))
    return (RETRIEVE_FAILED, None)

## reverse area Code

def _retrieve_yp_reverseAreaCode(code):
    url = "http://yp.whitepages.com/log_feature/sort/search/Reverse_Areacode?npa=%s&sort=alpha"
    url = url % code
    htmlText = getHttp(url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411.reverseAreaCodeLookup(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Reverse-Area-Code", code, htmlText, url)
    return res, data    

def _retrieve_411_reverseAreaCode(code):
    url = "http://www.411.com/log_feature/sort/search/Reverse_Areacode?npa=%s&sort=alpha"
    url = url % code
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411_by411.reverseAreaCodeLookup(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Reverse-Area-Code", code, htmlText, url)
    return res, data    

_g_retrieve_reverseAreaCode = [
    _retrieve_411_reverseAreaCode,
    _retrieve_yp_reverseAreaCode
]

def retrieveReverseAreaCode(code):
    global _g_retrieve_reverseAreaCode
    for func in _g_retrieve_reverseAreaCode:
        try:
            res, data = func(code)
            if RETRIEVE_FAILED != res and UNKNOWN_FORMAT != res:
                return res, data
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to parse data\nreason:%s\n" % (txt))
    return (RETRIEVE_FAILED, None)

## reverse Zip Code

def _retrieve_yp_reverseZipCode(code):
    url = "http://yp.whitepages.com/search/Reverse_Zip?zip=%s"
    url = url % code
    htmlText = getHttp(url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411.reverseZIPCodeLookup(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Reverse-Zip", code, htmlText, url)
    return res, data    

def _retrieve_411_reverseZipCode(code):
    url = "http://www.411.com/search/Reverse_Zip?zip=%s"
    url = url % code
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411_by411.reverseZIPCodeLookup(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Reverse-Zip", code, htmlText, url)
    return res, data    

_g_retrieve_reverseZipCode = [
    _retrieve_411_reverseZipCode,
    _retrieve_yp_reverseZipCode
]

def retrieveReverseZipCode(code):
    global _g_retrieve_reverseZipCode
    for func in _g_retrieve_reverseZipCode:
        try:
            res, data = func(code)
            if RETRIEVE_FAILED != res and UNKNOWN_FORMAT != res:
                return res, data
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to parse data\nreason:%s\n" % (txt))
    return (RETRIEVE_FAILED, None)

## Zip Code by city

def _retrieve_yp_zipCodeByCity(city, state):
    url = "http://yp.whitepages.com/search/Find_Zip?city_zip=%s&state_id=%s"
    url = url % (urllib.quote(city), urllib.quote(state))
    htmlText = getHttp(url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411.ZIPCodeByCity(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Zip-By-City", city+","+state, htmlText, url)
    return res, data    

def _retrieve_411_zipCodeByCity(city, state):
    url = "http://www.411.com/search/Find_Zip?city_zip=%s&state_id=%s"
    url = url % (urllib.quote(city), urllib.quote(state))
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411_by411.ZIPCodeByCity(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Zip-By-City", city+","+state, htmlText, url)
    return res, data    

_g_retrieve_zipCodeByCity = [
    _retrieve_411_zipCodeByCity,
    _retrieve_yp_zipCodeByCity
]

def retrieveZipCodeByCity(city, state):
    global _g_retrieve_zipCodeByCity
    for func in _g_retrieve_zipCodeByCity:
        try:
            res, data = func(city, state)
            if RETRIEVE_FAILED != res and UNKNOWN_FORMAT != res:
                return res, data
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to parse data\nreason:%s\n" % (txt))
    return (RETRIEVE_FAILED, None)

## Area Code by city

def _retrieve_yp_areaCodeByCity(city, state):
    url = "http://yp.whitepages.com/search/Find_Areacode?city_zip=%s&state_id=%s"
    url = url % (urllib.quote(city), urllib.quote(state))
    htmlText = getHttp(url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411.areaCodeByCity(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Area-Code-By-City", city+","+state, htmlText, url)
    return res, data    

def _retrieve_411_areaCodeByCity(city, state):
    url = "http://www.411.com/search/Find_Areacode?city=%s&state_id=%s"
    url = url % (urllib.quote(city), urllib.quote(state))
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411_by411.areaCodeByCity(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Area-Code-By-City", city+","+state, htmlText, url)
    return res, data    

_g_retrieve_areaCodeByCity = [
    _retrieve_411_areaCodeByCity,
    _retrieve_yp_areaCodeByCity
]

def retrieveAreaCodeByCity(city, state):
    global _g_retrieve_areaCodeByCity
    for func in _g_retrieve_areaCodeByCity:
        try:
            res, data = func(city, state)
            if RETRIEVE_FAILED != res and UNKNOWN_FORMAT != res:
                return res, data
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to parse data\nreason:%s\n" % (txt))
    return (RETRIEVE_FAILED, None)

## reverse Phone

def _retrieve_yp_reversePhone(xxx,yyy,zzzz):
    url = "http://yp.com/wp-p-results.php?npa=%s&np3=%s&np4=%s&client=1482&ver=1.2&type=p&phone=%s%s"
    url = url % (xxx,yyy,zzzz,yyy,zzzz)
    htmlText = getHttp(url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411.reversePhoneLookup(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Reverse-Phone", xxx+"-"+yyy+"-"+zzzz, htmlText, url)
    return res, data    

def _retrieve_411_reversePhone(xxx,yyy,zzzz):
    url = "http://www.411.com/search/Reverse_Phone?phone=%s-%s-%s"
    url = url % (xxx,yyy,zzzz)
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411_by411.reversePhoneLookup(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Reverse-Phone", xxx+"-"+yyy+"-"+zzzz, htmlText, url)
    return res, data    

def _retrieve_whitepages_reversePhone(xxx,yyy,zzzz):
    url = "http://yp.whitepages.com/1048/search/Reverse_Phone?phone=%s%s%s"
    url = url % (xxx,yyy,zzzz)
    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411.reversePhoneLookupWhitepages(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Reverse-Phone", xxx+"-"+yyy+"-"+zzzz, htmlText, url)
    return res, data    

_g_retrieve_reversePhone = [
    _retrieve_411_reversePhone,
    _retrieve_yp_reversePhone,
    _retrieve_whitepages_reversePhone  ## this is not fully tested (but can help sometimes)
]

def retrieveReversePhone(xxx,yyy,zzzz):
    global _g_retrieve_reversePhone
    for func in _g_retrieve_reversePhone:
        try:
            res, data = func(xxx,yyy,zzzz)
            if RETRIEVE_FAILED != res and UNKNOWN_FORMAT != res:
                return res, data
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to parse data\nreason:%s\n" % (txt))
    return (RETRIEVE_FAILED, None)

## Business Search

ypServerUrlBusinessSearch             = "http://yp.com//yplist.php?cn=%s&cz=%s&cs2=%s&lc=&styp=1&flvl=1"
ypServerUrlBusinessSearchYPsa         = "http://yp.com//yplist.php?cn=%s&cz=%s&cs2=%s&lc=&YPsa=1&styp=1&flvl=1"
ypServerUrlBusinessSearchCategory     = "http://yp.com/ypcat.php?find=%s&radsearchby=cs&cz=%s&cs2=%s"
ypServerUrlBusinessSearchCategoryYPsa = "http://yp.com/ypcat.php?find=%s&radsearchby=cs&cz=%s&YPsa=1&cs2=%s"

def _retrieve_yp_business(name,cityOrZip,state,surrounding,categoryOrName):
    url = ""
    name = name.replace(" ","+")
    if categoryOrName == "Name":
        if surrounding == "Yes":
            url = ypServerUrlBusinessSearchYPsa % (urllib.quote(name),urllib.quote(cityOrZip),urllib.quote(state))
        else:
            url = ypServerUrlBusinessSearch % (urllib.quote(name),urllib.quote(cityOrZip),urllib.quote(state))
    if categoryOrName == "Category":
        if surrounding == "Yes":
            url = ypServerUrlBusinessSearchCategoryYPsa % (urllib.quote(name),urllib.quote(cityOrZip),urllib.quote(state))
        else:
            url = ypServerUrlBusinessSearchCategory % (urllib.quote(name),urllib.quote(cityOrZip),urllib.quote(state))

    htmlText = getHttp(url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411.businessSearch(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Business-Search", name+","+cityOrZip+","+state+","+surrounding+","+categoryOrName, htmlText, url)
    return res, data    

dexServerUrlBusinessSearch             = "http://www.dexonline.com/servlet/ActionServlet;DexSESSIONID=?pid=bfull&&cityText=%s&state=%s&locationVerified=false&surroundingAreas=%s&from=&resultForm=BASIC&queryText=%s&queryType=NAME"
dexServerUrlBusinessSearchCategory     = "http://www.dexonline.com/servlet/ActionServlet;DexSESSIONID=?pid=blistings&surroundingAreas=%s&from=&queryText=%s&cityText=%s&state=%s"

def _retrieve_dex_business(name,cityOrZip,state,surrounding,categoryOrName):
    ## from www.dexonline.com
    ## no zip accepted:
    if cityOrZip.isdigit() and len(cityOrZip)==5:
        log(SEV_EXC, "_retrieve_dex_business doesn't support cityOrZip='%s'" % cityOrZip)
        return RETRIEVE_FAILED, None    
    url = ""
    sur = "false"
    if surrounding == "Yes":
        sur = "true"
    
    if categoryOrName == "Name":
        url = dexServerUrlBusinessSearch % (urllib.quote(cityOrZip),urllib.quote(state), sur, urllib.quote(name))
    elif categoryOrName == "Category":
        url = dexServerUrlBusinessSearchCategory % (sur, urllib.quote(name), urllib.quote(cityOrZip),urllib.quote(state))

    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411_by411.businessSearchDex(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Business-Search", name+","+cityOrZip+","+state+","+surrounding+","+categoryOrName, htmlText, url)
    return res, data


switchboardServerUrlBusinessSearch            = "http://www.switchboard.com/bin/cgidir.dll?PR=116&mem=1&L=%s&A=&T=%s&S=%s&Z=&ST=1&SD=&LNK=43:24"
switchboardServerUrlBusinessSearchZip         = "http://www.switchboard.com/bin/cgidir.dll?PR=116&mem=1&L=%s&A=&T=&Z=%s&S=%s&ST=1&SD=&LNK=43:24"
switchboardServerUrlBusinessSearchCategory    = "http://www.switchboard.com/bin/cgidir.dll?MEM=1&PR=133&Search=Search&KW=%s&T=%s&Z=&S=%s"
switchboardServerUrlBusinessSearchCategoryZip = "http://www.switchboard.com/bin/cgidir.dll?MEM=1&PR=133&Search=Search&KW=%s&T=&Z=%s&S=%s"

def _retrieve_switchboard_business(name,cityOrZip,state,surrounding,categoryOrName):
    ## from 
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

    htmlText = getHttp(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = m411_by411.businessSearchSwitchboard(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Business-Search", name+","+cityOrZip+","+state+","+surrounding+","+categoryOrName, htmlText, url)
    return res, data

_g_retrieve_business = [
    _retrieve_switchboard_business,
    _retrieve_yp_business,
    _retrieve_dex_business
]

def retrieveBusiness(name,cityOrZip,state,surrounding,categoryOrName):
    global _g_retrieve_business
    for func in _g_retrieve_business:
        try:
            res, data = func(name,cityOrZip,state,surrounding,categoryOrName)
            if res not in [RETRIEVE_FAILED, UNKNOWN_FORMAT]:
                return res, data
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to parse data\nreason:%s\n" % (txt))
    return (RETRIEVE_FAILED, None)

## by url

def retrieveBusinessSearchByUrl(urlIn):
    res = RETRIEVE_FAILED
    data = None
    # witch server?
    type = "?"
    url = ""
    if urlIn.startswith("yplist.php"):
        url = "http://yp.com/%s" % urlIn
        type = "yp"
    elif urlIn.startswith("/servlet"):
        url = "http://www.dexonline.com%s" % urlIn
        type = "dex"
    elif urlIn.startswith("http://www.switchboard.com"):
        url = urlIn
        type = "switch"

    # retrieve
    htmlText = None
    if type == "yp":
        htmlText = getHttp(url, retryCount=3)
    elif type == "dex" or type == "switch":
        htmlText = getHttp(url, retryCount=3)

    # no?
    if htmlText is None:
        return (RETRIEVE_FAILED, None)

    # parse
    if type == "yp":
        res, data = m411.businessSearch(htmlText)
    elif type == "dex":
        res, data = m411_by411.businessSearchDex(htmlText)
    elif type == "switch":
        res, data = m411_by411.businessSearchSwitchboard(htmlText)

    # ending
    if res == UNKNOWN_FORMAT:
        logParsingFailure("411-Business-Search-By-Url", urlIn , htmlText, url)
    return res, data

def main():
    print "--------------"
    typer, body = _retrieve_411_international("PL")

    print str(typer)
    print "--------------"
    print body


if __name__ == "__main__":
    main()
    


