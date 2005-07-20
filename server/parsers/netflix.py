# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk (Szymon Knitter)
#
# Purpose:
#  netflix.com
#
import sys, StringIO, gzip, string, urllib, urllib2, cookielib
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise

from Retrieve import *

from entities import convertNamedEntities
from entities import convertNumberedEntities
from parserUtils import *
from ResultType import *
from definitionBuilder import *
from popupMenu import *
from arsutils import *

from threading import Lock
from parserErrorLogger import logParsingFailure
from parserErrorLogger import makePathIfNeeded
import sys, os

## prefixes:
netflixPrefix = "http://www.netflix.com/"
addToQueuePrefix = "http://www.netflix.com/AddToQueue?movieid="
movieWithIdPrefix = "http://www.netflix.com/MovieDisplay?movieid="

## CROSS MODULES FUNCTIONS
def titleCrossModuleLinkLogged(gtxt, title, addUrl, titleUrl, modulesInfo, formFlags = ""):
    popupItems = []
    if titleUrl != "":
        popupItems.append(['View details',formFlags+"s+netflixitem:"+titleUrl+";T",False,True,False])
    if addUrl != "":
        popupItems.append(['Add to queue',formFlags+"s+netflixadd:"+addUrl,False,True,False])
    if modulesInfo != None:
        if modulesInfo['Amazon']:
            popupItems.append(['Search Amazon',formFlags+'s+amazonsearch:DVD;;1;'+title,False,False,False])
        if modulesInfo['ListsOfBests']:
            popupItems.append(['Search Lists of Bests',formFlags+'s+listsofbestssearch:'+title+';Movies;Title',False,False,False])
        if modulesInfo['eBay']:
            popupItems.append(['Search eBay',"s+ebay:search;0;?;"+title,False,False,False])

        #TODO: more
    if len(popupItems)>0:
        gtxt.setHyperlink(buildPopupMenu(popupItems))

def titleCrossModuleLink(gtxt, title, modulesInfo):
    if modulesInfo != None:
        popupItems = []
        if modulesInfo['Amazon']:
            popupItems.append(['Search Amazon','s+amazonsearch:DVD;;1;'+title,False,False,False])
        if modulesInfo['ListsOfBests']:
            popupItems.append(['Search Lists of Bests','s+listsofbestssearch:'+title+';Movies;Title',False,False,False])
        if modulesInfo['eBay']:
            popupItems.append(['Search eBay',"s+ebay:search;0;?;"+title,False,False,False])
        #TODO: more

        if len(popupItems) > 0:
            gtxt.setHyperlink(buildPopupMenu(popupItems))

def authorCrossModuleLink(gtxt, author, modulesInfo, netflixLink, formFlags = ""):
    netflixHyperlink = ""
    if netflixLink and netflixLink != "":
        netflixHyperlink = formFlags+"s+netflixbrowse:%s;T" % netflixLink
    if modulesInfo != None:
        popupItems = []
        if netflixHyperlink != "":
            popupItems.append(['Search Netflix',netflixHyperlink,False,True,False])
        if modulesInfo['Amazon']:
            popupItems.append(['Search Amazon',formFlags+'s+amazonsearch:DVD;;1;'+author,False,False,False])
        if modulesInfo['ListsOfBests']:
            popupItems.append(['Search Lists of Bests',formFlags+'s+listsofbestssearch:'+author+';Movies;Creator',False,False,False])
        if modulesInfo['Encyclopedia']:
            popupItems.append(['Search Encyclopedia',formFlags+'s+pediasearch:'+author,False,False,False])
        if modulesInfo['eBay']:
            popupItems.append(['Search eBay',"s+ebay:search;0;?;"+author,False,False,False])
        #TODO: more

        if len(popupItems) > 1 or (len(popupItems) > 0 and netflixHyperlink == ""):
            gtxt.setHyperlink(buildPopupMenu(popupItems))
        elif netflixHyperlink != "":
            gtxt.setHyperlink(netflixHyperlink)
    elif netflixHyperlink != "":
        gtxt.setHyperlink(netflixHyperlink)

## PARSERS

def parseBrowse(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    outerList = []
    divList = soup.fetch("div",{"class":"browse"})
    for div in divList:
        aItem = div.first("a", {"href":"http://www.netflix.com/BrowseSelection?%"})
        if aItem:
            name = getAllTextFromTag(aItem)
            url = aItem['href']
            url = url[url.find('?'):]
            outerList.append([url,name])
    if 0 == len(outerList):
        return (UNKNOWN_FORMAT, None)

    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / Browse")
    df.LineBreakElement(1,2)

    for item in outerList:
        df.BulletElement(False)
        df.TextElement(item[1], link="s+netflixbrowse:"+item[0]+";F")
        df.PopParentElement()
    # buttons
    buttons = [["H","Browse"]]
    return (NETFLIX_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def parseItems(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    outerList = []
    aList = soup.fetch("a",{"href":movieWithIdPrefix+"%"})
    for aItem in aList:
        name = getAllTextFromTag(aItem)
        url = aItem['href']
        url = url[url.find('=')+1:]
        outerList.append([url,name])

    if 0 == len(outerList):
        return (UNKNOWN_FORMAT, None)
    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Browse",link='s+netflixbrowse:;F')
    df.TextElement(" / ")

    div = soup.first("div",{"class":"browseA"})
    genre = getAllTextFromTag(div)
    df.TextElement(genre)

    df.LineBreakElement(1,2)

    for item in outerList:
        df.BulletElement(False)
        df.TextElement(item[1], link="s+netflixitem:"+item[0]+";F")
        df.PopParentElement()
    # buttons
    buttons = [["H",'Browse/'+genre]]
    return (NETFLIX_SEARCH_LIST, universalDataFormatWithDefinition(df, buttons))

def getListFromCommaSeparated(text):
    ret = []
    names = text.split(",")
    for name in names:
        ret.append(name.replace("..."," ").strip())
    return ret

def parseItem(htmlTxt, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    df = Definition()

    outerList = []

    nameDiv = soup.first("div", {"style":"padding-bottom: 10px;"})
    descriptionDiv = soup.first("div", {"class":"description"})
    if not nameDiv or not descriptionDiv:
        return UNKNOWN_FORMAT, None
    # title
    name = []
    spanList = nameDiv.fetch("span")
    if len(spanList) > 0:
        name.append(getAllTextFromTag(spanList[0]).strip())
        if len(spanList) > 1:
            name.append(getAllTextFromTag(spanList[1]).strip())
    else:
        name.append(getAllTextFromTag(nameDiv).strip())
    df.TextElement("Home", link='netflixform:main')
    df.TextElement(" / ")
    gtxt = df.TextElement(string.join(name," "), style='bold')
    titleCrossModuleLink(gtxt, name[0], modulesInfo)
    df.LineBreakElement(1,2)

    # alternate
    div = nameDiv.first("div", {"class":"alternate"})
    if div:
        df.LineBreakElement()
        df.TextElement(getAllTextFromTag(div).strip())
        df.LineBreakElement(1,2)

    # data
    supportDiv = descriptionDiv.first("div", {"class":"support"})
    bList = supportDiv.fetch("b")
    for bItem in bList:
        left = getAllTextFromTag(bItem).strip()
        if left in ["Starring:", "Director:"]:
            right = getListFromCommaSeparated(getAllTextFromTag(getLastElementFromTag(bItem).next).strip())

            df.LineBreakElement()
            if left == "Director:":
                df.TextElement("Director: ", style='bold')
            else:
                df.TextElement("Actor(s): ", style='bold')
            first = True
            for man in right:
                if not first:
                    df.TextElement(", ")
                else:
                    first = False
                gtxt = df.TextElement(man)
                authorCrossModuleLink(gtxt, man, modulesInfo, "")
            df.LineBreakElement(1,2)

    # text
    synopsisDiv = descriptionDiv.fetch("div", {"class":"synopsis"})
    df2 = Definition()
    first = True
    for div in synopsisDiv:
        if not first:
            df2.LineBreakElement(3,2)
        else:
            first = False
        df2.TextElement(getAllTextFromTag(div).strip())
    if not first:
        df.LineBreakElement()
        linkDesc = "simpleform:Description;"+df2.serialize()
        df.TextElement("Description", style='bold', link = linkDesc)
        df.LineBreakElement(1,2)

    # rating
    mpaaDiv = descriptionDiv.first("div", {"class":"mpaa"})
    if mpaaDiv:
        imgItem = mpaaDiv.first("img",{"alt":"%"})
        if imgItem:
            rating = imgItem['alt'].replace("\n","").strip()
            motivation = getAllTextFromTag(mpaaDiv).strip()
            df2 = Definition()
            df2.TextElement(motivation)
            linkDesc = "simpleform:Rating;"+df2.serialize()
            df.LineBreakElement()
            df.TextElement(rating, link = linkDesc)
    # buttons
    buttons = [["H",name[0]]]
    return (NETFLIX_ITEM, universalDataFormatWithDefinition(df, buttons))

def parseSearch(htmlTxt, keyword):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    outerList = []
    aList = soup.fetch("a",{"href":movieWithIdPrefix+"%"})
    for aItem in aList:
        name = getAllTextFromTag(aItem)
        url = aItem['href']
        url = url[url.find('=')+1:]
        if name[0] != "(" and not name.startswith("Read&nbsp;More"):
            outerList.append([url,name])

    if 0 == len(outerList):
        return (NO_RESULTS, None)

    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Search results for: '"+keyword+"'")
    df.LineBreakElement(1,2)

    for item in outerList:
        df.BulletElement(False)
        df.TextElement(item[1], link="s+netflixitem:"+item[0]+";F")
        df.PopParentElement()
    # buttons
    buttons = [["H",'Search for '+keyword]]
    return (NETFLIX_SEARCH_LIST, universalDataFormatWithDefinition(df, buttons))

def parseBrowseLogged(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    outerList = []
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # get data
    div = soup.first("div",{"class":"features"})
    if div:
        aList = div.fetch("a", {"href":netflixPrefix+'%'})
        if len(aList) > 0:
            outerList.append(["","Features:"])
            for aItem in aList:
                name = getAllTextFromTag(aItem)
                url = aItem['href'][len(netflixPrefix):]
                # remove critics picks & award winners:
                if name in ["New Releases", "Netflix Top 100"]:
                    outerList.append([url,name])
    divList = soup.fetch("div",{"class":"all-cat"})
    if len(divList) > 0:
        outerList.append(["","Genres:"])
    for div in divList:
        aList = div.fetch("a", {"href":netflixPrefix+'%'})
        if len(aList) > 0:
            for aItem in aList:
                name = getAllTextFromTag(aItem)
                url = aItem['href'][len(netflixPrefix):]
                if name != "(Add Favorite Genres)":
                    outerList.append([url,name])
    div = soup.first("div",{"class":"categories"})
    if div:
        aList = div.fetch("a", {"href":netflixPrefix+'%'})
        for aItem in aList:
            name = getAllTextFromTag(aItem)
            url = aItem['href'][len(netflixPrefix):]
            outerList.append([url,name])
    if 0 == len(outerList):
        return (UNKNOWN_FORMAT, None)

    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / Browse")
    for item in outerList:
        if item[0] == "":
            df.LineBreakElement(3,2)
            df.TextElement(item[1], style='bold')
        else:
            df.BulletElement(False)
            gtxt = df.TextElement(item[1], link="s+netflixbrowse:"+item[0]+";T")
            if "All Genres" == item[1]:
                gtxt.setStyle('bold')
            df.PopParentElement()
    # buttons
    buttons = [["H","Browse"]]
    return (NETFLIX_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def parseAllGenresLogged(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    outerList = []
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # get data
    tdList = soup.fetch("td", {"class":"catlist"})
    aList = []
    for td in tdList:
        aList += td.fetch("a", {"href":netflixPrefix+'%'})
    for aItem in aList:
        name = getAllTextFromTag(aItem)
        url = aItem['href'][len(netflixPrefix):]
        if url[:8] == "SubGenre" or url[:5] == "Genre":
            outerList.append([url,name])
    if 0 == len(outerList):
        return (UNKNOWN_FORMAT, None)
    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Browse",link='s+netflixbrowse:;T')
    df.TextElement(" / All Genres")
    for item in outerList:
        if item[0].startswith("Genre"):
            df.LineBreakElement(3,2)
            df.TextElement(item[1], style='bold', link="s+netflixbrowse:"+item[0]+";T")
        else:
            df.BulletElement(False)
            df.TextElement(item[1], link="s+netflixbrowse:"+item[0]+";T")
            df.PopParentElement()
    # buttons
    buttons = [["H","Browse/All Genres"]]
    return (NETFLIX_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def getItemsFromListDiv(divList):
    items = []
    for tr in divList.fetch("tr"):
        addUrl = ""
        addA = tr.first("a", {"href":addToQueuePrefix+'%'})
        if addA:
            addUrl = addA['href'][len(addToQueuePrefix):]
        titleDiv = tr.first("div", {"class":"title"})
        if titleDiv:
            titleA = titleDiv.first("a",{"href":movieWithIdPrefix+"%"})
            titleUrl = titleA['href']
            titleUrl = titleUrl[titleUrl.find('=')+1:]
            title = getAllTextFromTag(titleA)
            year = ""
            yearSpan = titleDiv.first("span",{"class":"titleyear"})
            if yearSpan:
                year = getAllTextFromTag(yearSpan)
            mpaa = getAllTextFromTag(tr.first("div", {"class":"mpaa"}))
            ratingScriptText = str(tr.first("div", {"class":"rating"}))
            ratingScriptParts = ratingScriptText.split(",")
            rating = ""
            if len(ratingScriptParts) > 4:
                rating = ratingScriptParts[2]
            items.append([addUrl,titleUrl,title,year,mpaa,rating])
    return items

# call it after movie title ("* Sniper")
# it will add: " (1998) (R) (3.6)" - but with our modifications
# current: (1998) 3.6
# where year is gray, rating is [red < black < green]
def addToDefinitionYearMpaaRating(df, year, mpaa, rating):
    if year != "":
        df.TextElement(" "+year.strip(), style=styleNameGray)
    if rating != "":
        rat = 0
##        gtxt = df.TextElement(" " + rating)
##        rat = 0
##        try:
##            rat = float(rating)
##        except:
##            pass
##        if rat > 3.6:
##            gtxt.setStyle(styleNameGreen)
##        elif rat < 2.0:
##            gtxt.setStyle(styleNameRed)

##        try:
##            rat = float(rating)
##        except:
##            pass
##        text = ""
##        while len(text) < rat:
##            text += "%c" % 144
##        while len(text) < 5:
##            text += "%c" % 143
##        gtxt = df.TextElement(text)
##        if rat > 3.6:
##            gtxt.setStyle(styleNameGreen)
##        elif rat < 2.0:
##            gtxt.setStyle(styleNameRed)
##        gtxt.setJustification(justRightLast)

        try:
            rat = float(rating)
        except:
            pass
        text = ""
        while len(text) < rat:
            text += "\x95"
        gtxt = df.TextElement(text)
        if rat > 3.6:
            gtxt.setStyle(styleNameGreen)
        elif rat < 2.0:
            gtxt.setStyle(styleNameRed)
        #TODO:/TRY: add sth like 1/2 of bullet? 3.5 -> ".ooo" ; 3.0 -> "ooo"
        gtxt.setJustification(justRightLast)

def parseGenreLogged(htmlTxt, modulesInfo, newReleasesMode = False):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    outerList = []
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # get data
    prevUrl = ""
    nextUrl = ""
    pageTitle = getAllTextFromTag(soup.first("title"))
    pageTitle = pageTitle.replace("Netflix:","").strip()
    if newReleasesMode:
        div = soup.first("div", {"class":"page-title-pma"})
        if not div:
            return UNKNOWN_FORMAT, None
        pageTitle = getAllTextFromTag(div)

    # get list contener
    divList = soup.first("div", {"class":"blk-list01"})
    if None == divList:
        divList = soup.first("div", {"class":"list"})
    if None == divList:
        return UNKNOWN_FORMAT, None
    items = getItemsFromListDiv(divList)

    # prev next urls
    moreDiv = divList.first("div", {"class":"morelink"})
    if moreDiv:
        nextUrl = moreDiv.first("a")['href']
        nextUrl = nextUrl[len(netflixPrefix):]
    prevNext = soup.fetch("div", {"align":"right"})
    if 2 == len(prevNext):
        aList = prevNext[1].fetch("a")
        if len(aList) == 2:
            prevUrl = aList[0]['href']
            prevUrl = prevUrl[len(netflixPrefix):]
            nextUrl = aList[1]['href']
            nextUrl = nextUrl[len(netflixPrefix):]
        elif len(aList) == 1:
            imgItem = aList[0].first("img", {"src":"%"})
            if imgItem:
                if -1 != imgItem['src'].find("prev"):
                    prevUrl = aList[0]['href']
                    prevUrl = prevUrl[len(netflixPrefix):]
                elif -1 != imgItem['src'].find("next"):
                    nextUrl = aList[0]['href']
                    nextUrl = nextUrl[len(netflixPrefix):]
                else:
                    return UNKNOWN_FORMAT, None
        else:
            return UNKNOWN_FORMAT, None
    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Browse",link='s+netflixbrowse:;T')
    if newReleasesMode:
        df.TextElement(" / ")
        df.TextElement("New Releases",link='s+netflixbrowse:NewReleases;T')
    df.TextElement(" / "+pageTitle)
    df.LineBreakElement(1,2)

    for item in items:
        # [addUrl,titleUrl,title,year,mpaa,rating]
        df.BulletElement(False)
        gtxt = df.TextElement(item[2])
        titleCrossModuleLinkLogged(gtxt, item[2], item[0], item[1], modulesInfo)
        addToDefinitionYearMpaaRating(df, item[3], item[4], item[5])
        df.PopParentElement()

    df.LineBreakElement(1,2)
    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    gtxt = df.TextElement("prev page")
    if prevUrl != "":
        prevUrl = "s+netflixbrowse:"+prevUrl+";T"
        gtxt.setHyperlink(prevUrl)
    df.TextElement(" \x95 ", style='gray')
    gtxt = df.TextElement("next page")
    if nextUrl != "":
        nextUrl = "s+netflixbrowse:"+nextUrl+";T"
        gtxt.setHyperlink(nextUrl)
    df.PopParentElement()

    # buttons
    buttons = [["H","Browse/"+pageTitle.replace(" / ","/")]]
    buttons.append(["B","P",prevUrl])
    buttons.append(["B","N",nextUrl])
    return (NETFLIX_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def parseItemLogged(htmlTxt, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # start...
    df = Definition()
    # title
    titleDiv = soup.first("div", {"class":"title"})
    if not titleDiv:
        return UNKNOWN_FORMAT, None
    name = []
    # I don't like do it this way, but I can't do it better
    text = str(titleDiv.contents[0])
    text = text.replace("\n"," ").replace("   "," ").replace("  "," ").strip()
    name.append(text)
    span = titleDiv.first("span")
    if span:
        text = getAllTextFromTag(span).strip()
        name.append(text)
    span = titleDiv.first("div")
    if span:
        text = getAllTextFromTag(span).strip()
        name.append(text)
    addUrl = ""
    aItem = soup.first("a",{"href":addToQueuePrefix+'%'})
    if aItem:
        imgItem = aItem.first("img",{"alt":"Add%"})
        if imgItem:
            addUrl = aItem['href'][len(addToQueuePrefix):]
    addToQueueUrl = addUrl
    # df
    df.TextElement("Home", link='netflixform:main')
    df.TextElement(" / ")
    gtxt = df.TextElement(string.join(name," "), style='bold')
    titleCrossModuleLinkLogged(gtxt, name[0], addUrl, "", modulesInfo)
    df.LineBreakElement(1,2)
    # starring & director
    supportDiv = soup.first("div", {"class":"support"})
    if not supportDiv:
        return UNKNOWN_FORMAT, None
    else:
        actors = []
        next = getLastElementFromTag(supportDiv.first("b"))
        end = 2
        while 0 != end:
            if not next:
                end = 0
            else:
                if isinstance(next, Tag):
                    if next.name == "b":
                        actors.append(["",""])
                    elif next.name == "a":
                        if next['href'].startswith(netflixPrefix+"RoleDisplay?"):
                            aTxt = getAllTextFromTag(next)
                            aUrl = next['href'][len(netflixPrefix):]
                            actors.append([aTxt,aUrl])
                    elif next.name == "br":
                        end -= 1
                next = next.next
        if len(actors) > 1:
            insertHeader = 0
            first = True
            for actor in actors:
                if actor[0] != "":
                    if insertHeader == 0:
                        df.LineBreakElement()
                        df.TextElement("With: ", style='bold')
                        insertHeader = 1
                        first = True
                    if insertHeader == 2:
                        df.LineBreakElement(1,2)
                        df.LineBreakElement()
                        df.TextElement("By: ", style='bold')
                        first = True
                        insertHeader = 3
                    if not first:
                        df.TextElement(", ")
                    else:
                        first = False
                    gtxt = df.TextElement(actor[0])
                    authorCrossModuleLink(gtxt,actor[0],modulesInfo,actor[1])
                else:
                    if insertHeader < 2:
                        insertHeader = 2
                    else:
                        insertHeader = 3
            df.LineBreakElement(1,2)
    # description
    synopsisDiv = soup.fetch("div", {"class":"synopsis"})
    if not synopsisDiv:
        return UNKNOWN_FORMAT, None
    df2 = Definition()
    first = True
    index = 0
    titleDiv = soup.fetch("div", {"class":"title"})
    for div in synopsisDiv:
        if not first:
            assert (index > 0)
            df2.LineBreakElement(3,2)
            if len(titleDiv) <= index:
                return UNKNOWN_FORMAT, None
            addUrl = ""
            aItem = titleDiv[index].first("a",{"href":addToQueuePrefix+'%'})
            if aItem:
                imgItem = aItem.first("img",{"alt":"Add%"})
                if imgItem:
                    addUrl = aItem['href'][len(addToQueuePrefix):]
            bItem = titleDiv[index].first("b")
            if not bItem:
                return UNKNOWN_FORMAT, None
            title = getAllTextFromTag(bItem)
            gtxt = df2.TextElement(title, style='bold')
            titleCrossModuleLinkLogged(gtxt, title, addUrl, "", modulesInfo,"c")
            df2.LineBreakElement()
        else:
            first = False
        df2.TextElement(getAllTextFromTag(div).strip())
        index += 1
    if not first:
        df.LineBreakElement()
        linkDesc = "simpleform:Description;"+df2.serialize()
        df.TextElement("Description", style='bold', link = linkDesc)
        df.LineBreakElement(1,2)
    # details
    detailsPars = []
    pars = soup.fetch("p")
    for par in pars:
        aItem = par.next
        if isinstance(aItem,Tag):
            try:
                if aItem['name'] != "":
                    detailsPars.append(par)
            except:
                pass

    lastElement = soup.first("div", {"style":"margin-top:30px;font-size:10px; color:#888888; text-align:center;"})
    detailsPars.append(getLastElementFromTag(lastElement))
    # now in detailsPars we have all params... (but pars are not closed...)
    # we have olso last element, as terminator
    if len(detailsPars) > 1:

        df2 = Definition()
        index = 0
        wasSomething = False
        while index+1 < len(detailsPars):
            if wasSomething:
                df2.LineBreakElement(3,2)
            else:
                wasSomething = True
            par = detailsPars[index]
            ident = par.next['name']
            if "director" == ident or "cast" == ident:
                if "director" == ident:
                    df2.TextElement("By: ", style='bold')
                else:
                    df2.TextElement("Cast: ", style='bold')
                next = par
                aList = []
                while next != detailsPars[index+1] and next:
                    if isinstance(next, Tag):
                        if next.name == "a":
                            try:
                                if next['href'].startswith(netflixPrefix+"RoleDisplay?"):
                                    aList.append(next)
                            except:
                                pass #no href
                    next = next.next
                first = True
                for aItem in aList:
                    if not first:
                        df2.TextElement(", ")
                    else:
                        first = False
                    actor = [getAllTextFromTag(aItem), aItem['href'][len(netflixPrefix):]]
                    gtxt = df2.TextElement(actor[0])
                    authorCrossModuleLink(gtxt,actor[0],modulesInfo,actor[1],"c")
            elif ident in ["specialfeatures", "otherfeatures", "length", "mpaa", "screenformats", "subtitles", "language", "releaseyear"]:
                brItem = par.first("br")
                caption = getAllTextFromTo(par, brItem)
                text = getAllTextFromTo(brItem, detailsPars[index+1])
                df2.TextElement(caption+" ", style=styleNameBold)
                df2.TextElement(text)
            elif "officlalurl" == ident:
                # remove "Official Movie Site" (rating remains)
                rating = getAllTextFromTo(par, detailsPars[index+1]).replace("Official Movie Site", "").strip()
                df2.TextElement(rating)
            elif "awards" == ident:
                brItem = par.first("br")
                caption = getAllTextFromTo(par, brItem)
                textList = getAllTextFromToInBrFormat(brItem, detailsPars[index+1]).split("<br>")
                df2.TextElement(caption+" ", style=styleNameBold)
                for text in textList:
                    df2.LineBreakElement()
                    df2.TextElement(text)
            elif "genres" == ident:
                aListGenre = []
                aListCust = []
                while next != detailsPars[index+1] and next:
                    if isinstance(next, Tag):
                        if next.name == "a":
                            try:
                                if next['href'].startswith(netflixPrefix+"Genre?"):
                                    aListGenre.append(next)
                                if next['href'].startswith(netflixPrefix+"SubGenre?"):
                                    aListGenre.append(next)
                                if next['href'].startswith(netflixPrefix+"Profile?"):
                                    aListCust.append(next)
                            except:
                                pass #no href
                    next = next.next
                if len(aListGenre) > 0:
                    df2.TextElement("Genres: ", style='bold')
                    first = True
                    for aItem in aListGenre:
                        if not first:
                            df2.TextElement(", ")
                        else:
                            first = False
                        df2.TextElement(getAllTextFromTag(aItem), link="cs+netflixbrowse:"+aItem['href'][len(netflixPrefix):]+";T")
                #TODO: customers lists?
##                if len(aListCust) > 0:
##                    df2.TextElement("Customers lists: ", style='bold')
##                    first = True
##                    for aItem in aListCust:
##                        if not first:
##                            df2.TextElement(", ")
##                        else:
##                            first = False
##                        df2.TextElement(getAllTextFromTag(aItem), link="cs+netflixbrowse:"+aItem['href'][len(netflixPrefix):]+";T")
            else:
                df2.TextElement(ident, style=styleNameBoldRed)
            index += 1

        df.LineBreakElement()
        linkDet = "simpleform:Details;"+df2.serialize()
        df.TextElement("Details", style=styleNameBold, link = linkDet)
        df.LineBreakElement(1,2)

    # reviews
    trList = soup.fetch("tr", {"valign":"middle"})
    reviews = []
    for tr in trList:
        script = tr.first("script")
        italics = tr.first("i")
        if script and italics:
            parts = str(script).split(",")
            if len(parts) > 3:
                reviewer = getAllTextFromTag(italics)
                note = parts[2].replace(".0","")
                next = getLastElementFromTag(tr).next
                end = 0
                while 0 == end:
                    if not next:
                        end = 2
                    elif isinstance(next,Tag):
                        if next.name == "i":
                            end = 1
                        else:
                            end = 2
                    else:
                        next = next.next
                if 1 == end:
                    #next = <i>
                    bItems = next.fetch("b")
                    if len(bItems) == 2:
                        helped = getAllTextFromTag(bItems[0])
                        allPeople = getAllTextFromTag(bItems[1])
                        next = getLastElementFromTag(next).next
                else:
                    helped = ""
                    allPeople = ""
                    next = getLastElementFromTag(tr).next
                end = 0
                reviewText = ""
                while 0 == end:
                    if not next:
                        end = 2
                    elif not isinstance(next,Tag):
                        if len(str(next).strip()) > 5:
                            end = 1
                            reviewText = getAllTextFromTag(next)
                        else:
                            next = next.next
                    else:
                        next = next.next
                if end == 1:
                    reviews.append([reviewer, note, helped, allPeople, reviewText])
    if len(reviews) > 0:
        df.LineBreakElement()
        df.TextElement("Reviews by:", style='bold')
        for (reviewer, note, helped, allPeople, reviewText) in reviews:
            df.BulletElement(False)
            df2 = Definition()
            if helped != "":
                df2.TextElement(helped+' out of '+allPeople+' people found this review helpful.')
                df2.LineBreakElement()
            df2.TextElement(reviewText)
            link = "simpleform:Review;"+df2.serialize()
            df.TextElement(note+' - ')
            df.TextElement(reviewer, link=link)
            df.PopParentElement()
        df.LineBreakElement(1,2)

    if addToQueueUrl != "":
        gtxt = df.TextElement("Add to queue", link = "s+netflixadd:"+addToQueueUrl)
        gtxt.setJustification(justCenter)

    # buttons
    buttons = [["H",name[0]]]
    return (NETFLIX_ITEM, universalDataFormatWithDefinition(df, buttons))

def parseRoleLogged(htmlTxt, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # start...
    df = Definition()
    # title
    titleTag = soup.first("title")
    if not titleTag:
        return UNKNOWN_FORMAT, None
    person = getAllTextFromTag(titleTag).replace("Netflix:","").strip()
    # df
    df.TextElement("Home", link='netflixform:main')
    df.TextElement(" / ")
    gtxt = df.TextElement(person, style='bold')
    authorCrossModuleLink(gtxt, person, modulesInfo, "", "")
    df.LineBreakElement(1,2)

    bioDiv = soup.first("div", {"class":"blk-bio01"})
    if bioDiv: ## biography can be empty :(
        biography = getAllTextFromToInBrFormat(bioDiv, getLastElementFromTag(bioDiv).next)
        bioList = biography.split("<br>")
        df2 = Definition()
        for text in bioList:
            if text.strip() != "":
                df2.TextElement(text)
            else:
                df2.LineBreakElement()
                df2.LineBreakElement()
        df.LineBreakElement()
        gtxt = df.TextElement("Biography", style='bold')
        gtxt.setHyperlink("simpleform:Biography;"+df2.serialize())
        df.LineBreakElement(1,2)

    # detect:
    # All %person% Movies
    listDiv = soup.first("div", {"class":"blk-list03"})
    if not listDiv:
        return UNKNOWN_FORMAT, None
    titleDiv = listDiv.first("div", {"class":"blktitle"})
    if not titleDiv:
        return UNKNOWN_FORMAT, None
    cmpText = getAllTextFromTag(titleDiv).strip()
    if not (cmpText == "All "+person+" Movies"):
        return UNKNOWN_FORMAT, None

    items = getItemsFromListDiv(listDiv)
    if len(items) > 0:
        df.LineBreakElement()
        gtxt = df.TextElement(cmpText+":", style='bold')
    for item in items:
        # [addUrl,titleUrl,title,year,mpaa,rating]
        df.BulletElement(False)
        gtxt = df.TextElement(item[2])
        titleCrossModuleLinkLogged(gtxt, item[2], item[0], item[1], modulesInfo)
        addToDefinitionYearMpaaRating(df, item[3], item[4], item[5])
        df.PopParentElement()

    # buttons
    buttons = [["H",person]]
    return (NETFLIX_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def getItemsFromTable(divList):
    items = []
    for tr in divList.fetch("tr"):
        addUrl = ""
        addA = tr.first("a", {"href":addToQueuePrefix+'%'})
        if addA:
            addUrl = addA['href'][len(addToQueuePrefix):]
        titleDiv = tr.first("div", {"style":"margin:7px 0px 5px 0px"})
        if titleDiv:
            titleA = titleDiv.first("a",{"href":movieWithIdPrefix+"%"})
            titleUrl = titleA['href']
            titleUrl = titleUrl[titleUrl.find('=')+1:]
            title = getAllTextFromTag(titleA)
            year = ""
            yearSpan = titleDiv.first("span",{"style":"font-size:10px"})
            if yearSpan:
                year = getAllTextFromTag(yearSpan)
            mpaa = getAllTextFromTag(tr.first("a", {'href':'http://www.netflix.com/Help?id=%'}))
            ratingScriptText = str(tr.first("td", {"width":"110"}))
            if -1 != ratingScriptText.find("StarbarInsert"):
                ratingScriptText = ratingScriptText[ratingScriptText.find("StarbarInsert"):]
            else:
                ratingScriptText = "None"
            ratingScriptParts = ratingScriptText.split(",")
            rating = ""
            if len(ratingScriptParts) > 4:
                rating = ratingScriptParts[2]
            items.append([addUrl,titleUrl,title,year,mpaa,rating])
    return items

def parseSearchLogged(htmlTxt, keyword, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Search results for: '"+keyword+"'")
    df.LineBreakElement(1,2)
    # get data

    resultsDiv = soup.first("div", {"style":"padding-left:15px;"})
    if not resultsDiv:
        #TODO:
        return NO_RESULTS, None

    spanList = resultsDiv.fetch("span", {"style":"font-size:16px;"})

    resultsCount = 0
    index = 0
    while index < len(spanList):
        cmpText = getAllTextFromTag(spanList[index])
        df.LineBreakElement()
        df.TextElement(cmpText.strip()+": ", style='bold')
        firstAAfter = spanList[index].previous
        while not isinstance(firstAAfter, Tag):
            firstAAfter = firstAAfter.previous
        firstAAfter = firstAAfter.first("a", {"href":"/Search?%"})
        if -1 != cmpText.find("People"):
            if firstAAfter:
                df.TextElement("more", link="s+netflixsearch:"+keyword+";People;T")
            peopleDiv = resultsDiv.fetch("div", {"style":"line-height:18px;%"})
            if len(peopleDiv) == 0:
                print "exit - 1"
                return UNKNOWN_FORMAT, None
            aList = peopleDiv[0].fetch("a",{"href":netflixPrefix+"RoleDisplay?%"})
            if len(aList) == 0:
                print "exit - 2"
                return UNKNOWN_FORMAT, None
            for aItem in aList:
                df.BulletElement(False)
                url = aItem['href'][len(netflixPrefix):]
                person = getAllTextFromTag(aItem)
                gtxt = df.TextElement(person)
                authorCrossModuleLink(gtxt, person, modulesInfo, url)
                df.PopParentElement()
                resultsCount += 1
        elif -1 != cmpText.find("Genre"):
            if firstAAfter:
                df.TextElement("more", link="s+netflixsearch:"+keyword+";Genre;T")
            genreDiv = resultsDiv.fetch("div", {"style":"line-height:18px;%"})
            if len(genreDiv) == 0:
                print "exit - 3"
                return UNKNOWN_FORMAT, None
            aList = genreDiv[-1].fetch("a",{"href":"/Genre?%"})
            aList += genreDiv[-1].fetch("a",{"href":"/SubGenre?%"})
            if len(aList) == 0:
                df.BulletElement(False)
                gtxt = df.TextElement("All Genres", link='s+netflixbrowse:AllGenres?lnkctr=LhcAllGenres;T')
                df.PopParentElement()
            else:
                for aItem in aList:
                    df.BulletElement(False)
                    df.TextElement(getAllTextFromTag(aItem), link='s+netflixbrowse:'+aItem['href'][1:]+';T')
                    df.PopParentElement()
                    resultsCount += 1
        elif -1 != cmpText.find("Movie"):
            if firstAAfter:
                df.TextElement("more", link="s+netflixsearch:"+keyword+";Movie;T")
            table = resultsDiv.first("table")
            if not table:
                print "exit - 4"
                return UNKNOWN_FORMAT, None
            items = getItemsFromListDiv(table)
            if 0 == len(items):
                items = getItemsFromTable(table)
            if 0 == len(items):
                print "exit - 5"
                return UNKNOWN_FORMAT, None
            for item in items:
                # [addUrl,titleUrl,title,year,mpaa,rating]
                df.BulletElement(False)
                gtxt = df.TextElement(item[2])
                titleCrossModuleLinkLogged(gtxt, item[2], item[0], item[1], modulesInfo)
                addToDefinitionYearMpaaRating(df, item[3], item[4], item[5])
                df.PopParentElement()
                resultsCount += 1
        else:
            print "exit - 6:" + cmpText

            return UNKNOWN_FORMAT, None
        df.LineBreakElement(1,2)
        index += 1

    if 0 == resultsCount:
        return NO_RESULTS, None
    # buttons
    buttons = [["H",'Search for '+keyword]]
    return (NETFLIX_SEARCH_LIST, universalDataFormatWithDefinition(df, buttons))

def parseAddToQueue(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD
    # test page
    table = soup.first("table", {"width":"297", "style":"position:relative;top:-30px;"})
    if not table:
        return UNKNOWN_FORMAT
    textDiv = table.first("div", {"style":"font-family:verdana;%"})
    if not textDiv:
        return UNKNOWN_FORMAT
    text = getAllTextFromTag(textDiv)
    if -1 != text.find("This movie is already in "):
        return NETFLIX_ADD_ALREADY_IN_QUEUE
    if -1 != text.find(" has been added to "):
        return NETFLIX_ADD_OK
    return UNKNOWN_FORMAT

def clearMovieUrl(href):
    url = href
    if url.startswith("http://www.netflix.com/MovieDisplay?"):
        url = href[len("http://www.netflix.com/MovieDisplay?"):]
    if url.startswith("movieid="):
        url = url[len("movieid="):]
    if url.startswith("trkid="):
        url = url[len("trkid="):]
    if -1 != url.find("&movieid="):
        parts = url.split("&movieid=")
        assert (len(parts) == 2)
        url = parts[1] + "&trkid=" + parts[0]
    return url

def parseQueue(htmlTxt, modulesInfo, informationText="", style=""):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    netflixMoviePrefix = "http://www.netflix.com/MovieDisplay?"
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Queue (")
    df.TextElement("update", link="s+netflixqueue:")
    df.TextElement(")")

    df.LineBreakElement(1,2)

    if informationText != "":
        df.LineBreakElement()
        gtxt = df.TextElement(informationText)
        if style != "":
            gtxt.setStyle(style)
        df.LineBreakElement(1,2)

    # get data
    # out dvd
    outDiv = soup.first("div", {"class":"dvd-out"})
    if outDiv:
        table = outDiv.first("table", {"class":"qotbl"})
        trList = table.fetch("tr",{"class":"or"})
        if len(trList) > 0:
            df.LineBreakElement()
            df.TextElement("At home:", style=styleNameHeader)
            for tr in trList:
                aItem = tr.first("a", {"href":netflixMoviePrefix+'%'})
                link = 's+netflixitem:'+clearMovieUrl(aItem['href'])+';T'
                df.BulletElement(False)
                df.TextElement(getAllTextFromTag(aItem), link=link)
                df.PopParentElement()
            df.LineBreakElement(1,2)

    # queue
    form = soup.first("form", {"method":"POST", "name":"MainQueueForm"})
    if form:
        items = []
        div = soup.first("div", {"class":"dvd-queue"})
        if div:
            tableList = div.fetch("table")
            for table in tableList:
                trList = table.fetch("tr", {"class":"bd"})
                for tr in trList:
                    tdList = tr.fetch("td")
                    shift = 0
                    if len(tdList) == 7:
                        shift = 1
                    elif len(tdList) != 6:
                        return UNKNOWN_FORMAT, None
                    movieTitle = getAllTextFromTag(tdList[1])
                    aItem = tdList[1].first("a", {"href":netflixMoviePrefix+"%"})
                    if not aItem:
                        return UNKNOWN_FORMAT, None
                    movieUrl = 's+netflixitem:'+clearMovieUrl(aItem['href'])+';T'
                    rating = getAllTextFromTag(tdList[2+shift])
                    genre = getAllTextFromTag(tdList[3+shift]).replace("&nbsp;"," ").strip()
                    avail = getAllTextFromTag(tdList[4+shift])
                    # this is some kind of number or sth...
                    iItem = tdList[0].first("input", {"name":"OR%"})
                    if not iItem:
                        return UNKNOWN_FORMAT, None
                    queueId = iItem["name"][2:]
                    items.append([movieTitle, movieUrl, rating, genre, avail, queueId])

        if len(items) > 0:
            index = 1
            df.LineBreakElement()
            gtxt = df.TextElement("Queue:", style=styleNameHeader)
            for item in items:
                #item = [movieTitle, movieUrl, rating, genre, avail, queueId]
                li = df.ListNumberElement(index,False)
                li.setTotalCount(len(items))
                gtxt = df.TextElement(item[0])
                # build popup
                popupItems = []
                popupItems.append(['View details',item[1],False,False,False])
                #if index > 1:
                #    popupItems.append(['Move on top','s+netflixqueue:top;'+item[5] ,False,False,False])
                # this will run popup form on client
                popupItems.append(['Move to ...','netflixform:mov;'+item[5] ,False,False,False])
                popupItems.append(['Remove from the queue','s+netflixqueue:del;'+item[5] ,False,False,False])
                gtxt.setHyperlink(buildPopupMenu(popupItems))
                # add other info
                df.TextElement(" "+item[3])
                if item[4] != "Now":
                    df.TextElement(" ("+item[4]+")")
                df.PopParentElement()
                index += 1
            df.LineBreakElement(1,2)


    # saved movies
    form = soup.first("form", {"method":"POST", "name":"AwaitingReleaseForm"})
    if form:
        items = []
        div = soup.first("div", {"class":"dvd-awaiting"})
        if div:
            tableList = div.fetch("table")
            for table in tableList:
                trList = table.fetch("tr", {"class":"arr"})
                for tr in trList:
                    tdList = tr.fetch("td")
                    shift = 0
                    if len(tdList) == 7:
                        shift = 1
                    elif len(tdList) != 6:
                        return UNKNOWN_FORMAT, None
                    movieTitle = getAllTextFromTag(tdList[1])
                    aItem = tdList[1].first("a", {"href":netflixMoviePrefix+"%"})
                    if not aItem:
                        return UNKNOWN_FORMAT, None
                    movieUrl = 's+netflixitem:'+clearMovieUrl(aItem['href'])+';T'
                    rating = getAllTextFromTag(tdList[2+shift])
                    genre = getAllTextFromTag(tdList[3+shift]).replace("&nbsp;"," ").strip()
                    avail = getAllTextFromTag(tdList[4+shift])
                    # this is some kind of number or sth...
                    iItem = tdList[5+shift].first("input", {"name":"R%"})
                    if not iItem:
                        return UNKNOWN_FORMAT, None
                    queueId = iItem["name"][1:]
                    items.append([movieTitle, movieUrl, rating, genre, avail, queueId])

        if len(items) > 0:
            df.LineBreakElement()
            gtxt = df.TextElement("Saved movies:", style=styleNameHeader)
            for item in items:
                #item = [movieTitle, movieUrl, rating, genre, avail, queueId]
                df.BulletElement(False)
                gtxt = df.TextElement(item[0])
                # build popup
                popupItems = []
                popupItems.append(['View details',item[1],False,False,False])
                popupItems.append(['Remove from the queue','s+netflixqueue:rem;'+item[5] ,False,False,False])
                gtxt.setHyperlink(buildPopupMenu(popupItems))
                # add other info
                df.TextElement(" "+item[3])
                if item[4] != "Unknown":
                    df.TextElement(" ("+item[4]+")")
                df.PopParentElement()

    return (NETFLIX_QUEUE, universalDataFormatWithDefinition(df, []))

def getItemsFromListTop100Div(div):
    items = []
    for tr in div.fetch("tr"):
        addUrl = ""
        addA = tr.first("a", {"href":addToQueuePrefix+'%'})
        if addA:
            addUrl = addA['href'][len(addToQueuePrefix):]
        titleA = tr.first("a",{"href":movieWithIdPrefix+"%"})
        if titleA:
            titleUrl = titleA['href']
            titleUrl = titleUrl[titleUrl.find('=')+1:]
            title = getAllTextFromTag(titleA)
            year = ""
            ratingScriptText = str(tr.first("td", {"width":"111"}))
            ratingScriptParts = ratingScriptText.split(",")
            rating = ""
            if len(ratingScriptParts) > 4:
                rating = ratingScriptParts[2]
            move = ""
            iItem = tr.first("i")
            if iItem:
                move = getAllTextFromTag(iItem).replace("&nbsp;"," ").strip()
            items.append([addUrl,titleUrl,title,year,"",rating, move])
    return items

def parseTop100Logged(htmlTxt, modulesInfo, top100):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # get data
    pageTitle = getAllTextFromTag(soup.first("div", {"class":"page-title-pma"}))
    pageTitle = pageTitle.replace("Netflix","").strip()
    if top100:
        pageTitle = "Top 100"

    # get list contener
    divList = soup.first("div", {"class":"t100"})
    if None == divList:
        return UNKNOWN_FORMAT, None
    items = getItemsFromListTop100Div(divList)
    if len(items) == 0:
        return UNKNOWN_FORMAT, None

    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Browse",link='s+netflixbrowse:;T')
##    if not top100:
##        df.TextElement(" / ")
##        df.TextElement("Top 100",link='s+netflixbrowse:Top100;T')
    df.TextElement(" / "+pageTitle)
    # 25 lists
    if top100:
        aList = soup.fetch("a", {"href":netflixPrefix+"Top25?%"})
        assert len(aList) > 0
        df2 = Definition()
        for aItem in aList:
            name = getAllTextFromTag(aItem)
            url = aItem['href'][len(netflixPrefix):]
            df2.BulletElement(False)
            df2.TextElement(name, link="cs+netflixbrowse:"+url+";T")
            df2.PopParentElement()
        df.LineBreakElement(3,2)
        df.TextElement("Top 25's", style=styleNameBold, link="simpleform:Top 25 in genres;"+df2.serialize())
    df.LineBreakElement(1,2)

    index = 1
    for item in items:
        # [addUrl,titleUrl,title,year,mpaa="",rating, move]
        li = df.ListNumberElement(index, False)
        li.setTotalCount(len(items))
##        if item[6] != "":
##            gtxt = df.TextElement("("+item[6].strip()+") ")
##            if item[6][0] == "+":
##                gtxt.setStyle(styleNameGreen)
##            elif item[6][0] == "-":
##                gtxt.setStyle(styleNameRed)
        gtxt = df.TextElement(item[2])
        titleCrossModuleLinkLogged(gtxt, item[2], item[0], item[1], modulesInfo)
        addToDefinitionYearMpaaRating(df, item[3], item[4], item[5])
        df.PopParentElement()
        index += 1

    # buttons
    buttons = [["H",pageTitle]]
    return (NETFLIX_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

# from any tag get movie title, movie url, add to queue url, stars - rating
def getMovieMinimum(anyTag):
    moviePrefix = "http://www.netflix.com/MovieDisplay?"
    (title, movieUrl, addUrl, rating) = ("","","","")
    # title and movie Url (ignore img, get text link)
    aListMovie = anyTag.fetch("a", {"href":moviePrefix+"%"})
    index = 0
    while index < len(aListMovie):
        aItem = aListMovie[index]
        title = getAllTextFromTag(aItem)
        if len(title) > 0:
            index = len(aListMovie)
            movieUrl = clearMovieUrl(aItem['href'])
        else:
            index += 1
    # add to queue
    aItem = anyTag.first("a", {"href":addToQueuePrefix+"%"})
    if aItem:
        addUrl = aItem['href'][len(addToQueuePrefix):]
    # rating
    scriptList = anyTag.fetch("script")
    index = 0
    while index < len(scriptList):
        script = scriptList[index]
        cut = str(script).find("StarbarInsert(")
        if -1 != cut:
            parts = str(script)[cut:].split(",")
            if len(parts) > 4:
                index = len(scriptList)
                rating = parts[2]
        index += 1
    if "" == title:
        print "No movie title in:\n" + str(anyTag)
    return (title, movieUrl, addUrl, rating)

def parseSectionUsingTags(df, movieTags, titleTag, moreDiv, modulesInfo):
    resultsCount = 0
    if len(movieTags) > 0 and titleTag:
        section = getAllTextFromTag(titleTag)
        df.LineBreakElement()
        df.TextElement(section+": ", style=styleNameHeader)
        if moreDiv:
            moreLink = moreDiv.first("div", {"class":"morelink"})
            if moreLink:
                aItem = moreLink.first("a", {"href":netflixPrefix+"%"})
                if aItem:
                    url = aItem['href'][len(netflixPrefix):]
                    df.TextElement("more", link="s+netflixbrowse:"+url+";T", style=styleNameGray)
        for movie in movieTags:
            item = getMovieMinimum(movie)
            # (title, movieUrl, addUrl, rating)
            if "" == item[0]:
                return UNKNOWN_FORMAT, None
            df.BulletElement(False)
            gtxt = df.TextElement(item[0])
            titleCrossModuleLinkLogged(gtxt, item[0], item[2], item[1], modulesInfo)
            addToDefinitionYearMpaaRating(df, "", "", item[3])
            df.PopParentElement()
            resultsCount += 1
        df.LineBreakElement(1,2)
    return resultsCount

def parseNewReleasesOld(htmlTxt, modulesInfo):
    fo = open("test1.html","wt")
    fo.write(htmlTxt)
    fo.close()

    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # get data
    pageTitle = "New Releases"
    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Browse",link='s+netflixbrowse:;T')
    df.TextElement(" / "+pageTitle)
    df.LineBreakElement(1,2)
    # get sections...
    resultsCount = 0
    div = soup.first("div", {"class":"blk-fetnewrel01"})
    if div:
        movieTags = div.fetch("div", {"class":"movie"})
        titleTag = div.first("div", {"class":"blktitle"})
        moreDiv = div.first("div", {"class":"more"})
        resultsCount += parseSectionUsingTags(df, movieTags, titleTag, moreDiv, modulesInfo)

    div = soup.first("div", {"class":"blk-newthisweek01"})
    if div:
        movieTags = div.fetch("div", {"class":"info"})
        titleTag = div.first("div", {"class":"blktitle"})
        moreDiv = div.first("div", {"class":"more"})
        resultsCount += parseSectionUsingTags(df, movieTags, titleTag, moreDiv, modulesInfo)

    div = soup.first("div", {"class":"blk-nowondvd01"})
    if div:
        movieTags = div.fetch("div", {"class":"movie"})
        titleTag = div.first("div", {"class":"blktitle"})
        moreDiv = div.first("div", {"class":"more"})
        resultsCount += parseSectionUsingTags(df, movieTags, titleTag, moreDiv, modulesInfo)

    div = soup.first("div", {"class":"blk-upcomingrel01"})
    if div:
        movieTags = div.fetch("div", {"class":"movie"})
        titleTag = div.first("div", {"class":"blktitle"})
        moreDiv = div.first("div", {"class":"more"})
        resultsCount += parseSectionUsingTags(df, movieTags, titleTag, moreDiv, modulesInfo)

    if 0 == resultsCount:
        return UNKNOWN_FORMAT, None
    # buttons
    buttons = [["H",pageTitle]]
    return (NETFLIX_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def parseNewReleases(htmlTxt, modulesInfo):
    fo = open("test1.html","wt")
    fo.write(htmlTxt)
    fo.close()

    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # get data
    pageTitle = "New Releases"
    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Browse",link='s+netflixbrowse:;T')
    df.TextElement(" / "+pageTitle)
    df.LineBreakElement(1,2)
    # get sections...
    resultsCount = 0
    divList = soup.fetch("div", {"id":"boxshotimg"})
    divList += soup.fetch("div", {"class":"boxshot"})    
    for div in divList:
        (title, movieUrl, addUrl, rating) = getMovieMinimum(div)
        df.BulletElement(False)
        gtxt = df.TextElement(title)
        titleCrossModuleLinkLogged(gtxt, title, addUrl, movieUrl, modulesInfo)
        addToDefinitionYearMpaaRating(df, "", "", rating)
        df.PopParentElement()
        resultsCount += 1

    categories = soup.first("div", {"class":"categories"})
    if categories:
        aList = categories.fetch("a", {"href":netflixPrefix+'%'})
        if len(aList) > 0:
            for aItem in aList:
                name = getAllTextFromTag(aItem)
                url = aItem['href'][len(netflixPrefix):]
                df.LineBreakElement(3,2)
                df.TextElement(name, style=styleNameBold, link='s+netflixbrowse:'+url+';T')

    if 0 == resultsCount:
        return UNKNOWN_FORMAT, None
    # buttons
    buttons = [["H",pageTitle]]
    return (NETFLIX_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def parseAllNewReleases(htmlTxt, modulesInfo):
    fo = open("test.html","wt")
    fo.write(htmlTxt)
    fo.close()

    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # test cookie...
    if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_REQUEST_PASSWORD, None
    # get data
    pageTitle = "All DVDs Releasing this week"
    # build definition
    df = Definition()
    df.TextElement("Home",link='netflixform:main')
    df.TextElement(" / ")
    df.TextElement("Browse",link='s+netflixbrowse:;T')
    df.TextElement(" / ")
    df.TextElement("New Releases",link='s+netflixbrowse:NewReleases;T')
    df.TextElement(" / "+pageTitle)
    df.LineBreakElement(1,2)
    # get sections...
    resultsCount = 0
    colDivList = soup.fetch("div", {"class":"pcol-wide"})
    colDivList += soup.fetch("div", {"class":"pcol-narrow"})
    for colDiv in colDivList:
        divList = colDiv.fetch("div", {"class":"blk-simplelist01"})
        for div in divList:
            titleTag = div.first("div", {"class":"blktitle"})
            movieTags = div.fetch("div", {"class":"movierow"})
            resultsCount += parseSectionUsingTags(df, movieTags, titleTag, None, modulesInfo)
    if 0 == resultsCount:
        return UNKNOWN_FORMAT, None
    # buttons
    buttons = [["H",pageTitle]]
    return (NETFLIX_BROWSE_LIST, universalDataFormatWithDefinition(df, buttons))

def isUserIsLogged(jar, logged = "?"):
    if logged in ["Y","T"]:
        return True
    if logged in ["N","F"]:
        return False

    htmlTxt = getHttp("http://www.netflix.com", cookieJar=jar)
    if htmlTxt != None:
        soup = BeautifulSoup()
        soup.feed(htmlTxt)
        if not soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
            return False
        else:
            return True
    return False

## RETRIEVERS

def retrieveBrowse(jar, fieldValue, modulesInfo):
    res, body = RETRIEVE_FAILED, None
    url = ""
    htmlTxt = ""
    if 2 != len(fieldValue.split(";",2)):
        return INVALID_REQUEST, None
    (urlIn, logged) = fieldValue.split(";",2)
    if not isUserIsLogged(jar, logged):
        # simple show what netflix is - without login
        url = "http://www.netflix.com/BrowseSelection" + urlIn
        htmlTxt = getHttp(url)
        if urlIn == "":
            res, body = parseBrowse(htmlTxt)
        else:
            res, body = parseItems(htmlTxt)
    else:
        if urlIn == "":
            url = "http://www.netflix.com/Default"
            htmlTxt = getHttp(url, cookieJar=jar)
            res, body = parseBrowseLogged(htmlTxt)
        else:
            url = "http://www.netflix.com/" + urlIn
            htmlTxt = getHttp(url, cookieJar=jar) # why I need to do that? (stupid Netflix)
            htmlTxt = getHttp(url, cookieJar=jar)
            if urlIn.startswith("AllGenres?"):
                res, body = parseAllGenresLogged(htmlTxt)
            elif urlIn.startswith("Genre?") or urlIn.startswith("SubGenre?"):
                res, body = parseGenreLogged(htmlTxt, modulesInfo)
            elif urlIn.startswith("RoleDisplay?") or urlIn.startswith("SubGenre?"):
                res, body = parseRoleLogged(htmlTxt, modulesInfo)
            elif urlIn.startswith("Top100"):
                res, body = parseTop100Logged(htmlTxt, modulesInfo, True)
            elif urlIn.startswith("Top25"):
                res, body = parseTop100Logged(htmlTxt, modulesInfo, False)
            elif urlIn.startswith("NewReleases"):
                res, body = parseNewReleases(htmlTxt, modulesInfo)
            elif urlIn.startswith("MoreNowOnDVD") or urlIn.startswith("MoreNewReleases"):
                res, body = parseGenreLogged(htmlTxt, modulesInfo,newReleasesMode = True)
            elif urlIn.startswith("AllNewReleases"):
                res, body = parseAllNewReleases(htmlTxt, modulesInfo)
            else:
                #TODO:
                print urlIn +" is not supported (for now) :("
                pass

    if res == UNKNOWN_FORMAT:
        logParsingFailure("Get-Netflix-Browse", fieldValue, htmlTxt, url)
    return res, body

def retrieveSearch(jar, fieldValue, modulesInfo):
    if 3 != len(fieldValue.split(";",3)):
        return INVALID_REQUEST, None
    (keyword, matchMode, logged) = fieldValue.split(";",3)
    if not isUserIsLogged(jar, logged):
        # simple show what netflix is - without login
        url = "http://www.netflix.com/Search?v1=%s&hnjr=1" % urllib.quote(keyword)
        htmlTxt = getHttp(url)
        res, body = parseItem(htmlTxt, modulesInfo)
        if res == NETFLIX_ITEM:
            return res, body
        res, body = parseSearch(htmlTxt, keyword)
    else:
        url = ""
        if "People" == matchMode:
            url = "http://www.netflix.com/Search?v1=%s&type=actor&row=actor&dtl=1" % urllib.quote(keyword)
        elif "Movie" == matchMode:
            url = "http://www.netflix.com/Search?v1=%s&type=title&row=title&dtl=1" % urllib.quote(keyword)
        elif "Genre" == matchMode:
            url = "http://www.netflix.com/Search?v1=%s&type=keyword&row=keyword&dtl=1" % urllib.quote(keyword)
        elif "Popular" == matchMode:
            url = "http://www.netflix.com/Search?v1=%s" % urllib.quote(keyword)
        else:
            return INVALID_REQUEST, None
        htmlTxt = getHttp(url, cookieJar=jar)
        res, body = parseItemLogged(htmlTxt, modulesInfo)
        if res == NETFLIX_ITEM:
            return res, body
        res, body = parseRoleLogged(htmlTxt, modulesInfo)
        if res == NETFLIX_BROWSE_LIST:
            return res, body
        res, body = parseSearchLogged(htmlTxt, keyword, modulesInfo)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("Get-Netflix-Search", fieldValue, htmlTxt, url)
    return res, body

def retrieveItem(jar, fieldValue, modulesInfo):
    if 2 != len(fieldValue.split(";",2)):
        return INVALID_REQUEST, None
    (url, logged) = fieldValue.split(";",2)
    if not isUserIsLogged(jar, logged):
        url = movieWithIdPrefix+url
        htmlTxt = getHttp(url)
        res, body = parseItem(htmlTxt, modulesInfo)
    else:
        url = movieWithIdPrefix+url
        htmlTxt = getHttp(url, cookieJar=jar)
        res, body = parseItemLogged(htmlTxt, modulesInfo)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("Get-Netflix-Item", fieldValue, htmlTxt, url)
    return res, body


def retrieveLogin(jar, fieldValue):
    loginAndPwd = fieldValue
    userName = loginAndPwd[:loginAndPwd.find(";")]
    userPwd = loginAndPwd[loginAndPwd.find(";")+1:]

    # recive 2 pages
    loginUrl = "https://www.netflix.com/Login"
    htmlTxt = getHttp(loginUrl, cookieJar=jar)
    if None == htmlTxt:
        print "failed to get login page"
        return MODULE_DOWN
    # if user was logged log out.
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    if soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        # that's it - user was logged... logout?
        htmlTxt = getHttp("http://www.netflix.com/Logout?lnkctr=mL", cookieJar=jar)
        if None == htmlTxt:
            print "failed to log out"
            return MODULE_DOWN
        htmlTxt = getHttp(loginUrl, cookieJar=jar)
        if None == htmlTxt:
            print "failed to get login page"
            return MODULE_DOWN


    postData = {
        "nextpage" : "http://www.netflix.com/Default",
        "email" : userName,
        "movieid" : "",
        "trkid" : "",
        "password1" : userPwd,
        "RememberMe" : "True",
        "SubmitButton" : "Click Here to Continue"
    }
    htmlTxt = getHttp(loginUrl, postData=postData, cookieJar=jar)
    if None == htmlTxt:
        print "failed to get a response for POST to login page"
        return MODULE_DOWN
    # check
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    if soup.first("meta", {"http-equiv":"refresh", "content":"0; URL=http://www.netflix.com/Default"}):
        htmlTxt = getHttp("http://www.netflix.com/Default", cookieJar=jar)
        return NETFLIX_LOGIN_OK
    if soup.first("form", {"method":"POST", "action":"https://www.netflix.com/Login", "name":"login_form"}):
        return NETFLIX_UNKNOWN_LOGIN
    if soup.first("a", {"href":"http://www.netflix.com/YourAccount"}):
        return NETFLIX_LOGIN_OK

    logParsingFailure("Get-Netflix-Login", "field value not available (security)", htmlTxt, "")
    return MODULE_DOWN

def getPostDataQueue(htmlTxt):
    postData = {}
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    maxValue = 0
    div = soup.first("div", {"class":"dvd-queue"})
    if div:
        tableList = div.fetch("table")
        for table in tableList:
            trList = table.fetch("tr", {"class":"bd"})
            for tr in trList:
                inputList = tr.fetch("input", {"name":"%", "value":"%"})
                for inp in inputList:
                    postData[inp['name']] = inp['value']
                    try:
                        val = int(inp['value'])
                        if val > maxValue:
                            maxValue = val
                    except:
                        pass
    postData["updateQueueBtn"]="Update Your Queue"
    return postData, maxValue

def retrieveQueue(jar, fieldValue, modulesInfo):
    url = "http://www.netflix.com/Queue"
    if fieldValue != "":
        valid = False
        sep = fieldValue.find(";")
        assert sep != -1
        req = fieldValue[:sep]
        value = fieldValue[sep+1:]
        postData = {}
        htmlTxt = getHttp(url, cookieJar=jar)
        if req in ["del", "top", "mov"]:
            postData, maxValue = getPostDataQueue(htmlTxt)
        elif req == "rem":
            pass

        text = ""
        style = ""
        if "del" == req:
            if len(postData) > 0:
                valid = True
            postData["R"+value] = 'on'
            text = "Movie removed from queue"
            style = styleNameRed
        elif "top" == req:
            if len(postData) > 0:
                valid = True
            postData["OR"+value] = "1"
            text = "Movie moved on top"
            style = styleNameGreen
        elif "mov" == req:
            if len(postData) > 0:
                valid = True
            parts = value.split(";")
            postData["OR"+parts[0]] = parts[1]
            text = "Movie moved to position %d" % min(int(parts[1]),maxValue)
            style = styleNameGreen
        elif "rem" == req:
            postData = {
                "R"+value:"on",
                "updateAwaitingRls":"Update Your Queue"
                }
            valid = True
            text = "Movie removed from saved queue"
            style = styleNameRed
        if valid:
            htmlTxt = getHttp(url, postData=postData, cookieJar=jar)
            res, body = parseQueue(htmlTxt, modulesInfo, text, style)
        else:
            res, body = UNKNOWN_FORMAT, None
    else:
        # just get queue
        htmlTxt = getHttp(url, cookieJar=jar)
        res, body = parseQueue(htmlTxt, modulesInfo, "", "")

    if res == UNKNOWN_FORMAT:
        logParsingFailure("Get-Netflix-Queue", fieldValue, htmlTxt, url)
    return res, body

def retrieveAdd(jar, fieldValue):
    url = "http://www.netflix.com/AddToQueue?movieid="+fieldValue
    htmlTxt = getHttp(url, cookieJar=jar)
    res = parseAddToQueue(htmlTxt)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("Netflix-Add", fieldValue, htmlTxt, url)
        res = NETFLIX_ADD_FAILED
    return res


referer_hdr = "Referer"
referer_val = "http://www.netflix.com/"

g_cookieJars = {}

def getCookieJar(userId):
    #TODO:
    global g_cookieJars
    if g_cookieJars.has_key(userId):
        return g_cookieJars[userId]

    cookieJarFileName = "cookies_%d.txt" % userId
    cj = cookielib.MozillaCookieJar(cookieJarFileName)
    try:
        cj.load()
    except IOError:
        # it's ok if the file doesn't exist
        pass
    g_cookieJars[userId] = cj
    return g_cookieJars[userId]

def saveCookieJar(userId):
    #TODO:
    global g_cookieJars
    assert g_cookieJars.has_key(userId)
    cj = getCookieJar(userId)
    cj.save()

def getNetflixMainPage(userId, dbgLevel=0):
    #TODO:
    print "\n######## getNetflixMainPage()"

    url = "http://www.netflix.com/Login?hnjr=3";

    req = urllib2.Request(url)
    req.add_header(Retrieve.user_agent_hdr, Retrieve.user_agent_val)
    req.add_header(Retrieve.accept_hdr, Retrieve.accept_val)
    req.add_header(Retrieve.accept_lang_hdr, Retrieve.accept_lang_val)
    req.add_header(Retrieve.accept_charset_hdr, Retrieve.accept_charset_val)
    req.add_header(Retrieve.keep_alive_hdr, Retrieve.keep_alive_val)
    req.add_header(Retrieve.connection_hdr, Retrieve.connection_val)
    req.add_header(Retrieve.referer_hdr, Retrieve.referer_val)
    # print '\n'.join(['%s' %k for k in (req.get_full_url(), req.headers)])

    cj = getCookieJar(userId)
    cookieProcessor = urllib2.HTTPCookieProcessor(cj)
    httpHandler = urllib2.HTTPHandler(debuglevel=dbgLevel)
    httpsHandler = urllib2.HTTPSHandler(debuglevel=dbgLevel)
    opener = urllib2.build_opener(cookieProcessor, httpHandler, httpsHandler)

    response = opener.open(req)

    if not response:
        #print "failed to get a response"
        return None
    #print '\n', response.info()

    encoding = response.headers.get(content_encoding_hdr)

    if "gzip" == encoding:
        htmlCompressed = response.read()
        compressedStream = StringIO.StringIO(htmlCompressed)
        gzipper = gzip.GzipFile(fileobj=compressedStream)
        htmlTxt = gzipper.read()
    else:
        htmlTxt = response.read()

    response.close()
    saveCookieJar(userId)
    return htmlTxt

def netflixDoLogin(userId, userName, userPwd, dbgLevel=0):
    #TODO:

    print "\n######## netflixDoLogin()"

    loginUrl = "https://www.netflix.com/Login"

    req = urllib2.Request(loginUrl)
    req.add_header(Retrieve.user_agent_hdr, Retrieve.user_agent_val)
    req.add_header(Retrieve.accept_hdr, Retrieve.accept_val)
    req.add_header(Retrieve.accept_lang_hdr, Retrieve.accept_lang_val)
    req.add_header(Retrieve.accept_charset_hdr, Retrieve.accept_charset_val)
    req.add_header(Retrieve.keep_alive_hdr, Retrieve.keep_alive_val)
    req.add_header(Retrieve.connection_hdr, Retrieve.connection_val)

    postData = {
        "nextpage" : "http://www.netflix.com/Default",
        "email" : userName,
        "movieid" : "",
        "trkid" : "",
        "password1" : userPwd,
        "RememberMe" : "True",
        "SubmitButton" : "Click Here to Continue"
    }
    encData = urllib.urlencode(postData)
    req.add_data(encData)

    cj = getCookieJar(userId)
    # we only need cookieProcessor since build_opener()
    # adds a lot of default handlers (HTTPHandler, HTTPSHandler) for us
    cookieProcessor = urllib2.HTTPCookieProcessor(cj)
    httpHandler = urllib2.HTTPHandler(debuglevel=dbgLevel)
    httpsHandler = urllib2.HTTPSHandler(debuglevel=dbgLevel)
    opener = urllib2.build_opener(cookieProcessor, httpHandler, httpsHandler)

    response = opener.open(req)

    if not response:
        print "failed to get a response for netflixDoLogin"
        return None
    #print '\n', response.info()

    encoding = response.headers.get(Retrieve.content_encoding_hdr)

    if "gzip" == encoding:
        htmlCompressed = response.read()
        compressedStream = StringIO.StringIO(htmlCompressed)
        gzipper = gzip.GzipFile(fileobj=compressedStream)
        htmlTxt = gzipper.read()
    else:
        htmlTxt = response.read()

    response.close()
    saveCookieJar(userId)

    # TODO: check that a page is just "<meta http-equiv="refresh" content="0; URL=http://www.netflix.com/Default">"
    url = "http://www.netflix.com/Default"
    req = urllib2.Request(loginUrl)
    req.add_header(Retrieve.user_agent_hdr, Retrieve.user_agent_val)
    req.add_header(Retrieve.accept_hdr, Retrieve.accept_val)
    req.add_header(Retrieve.accept_lang_hdr, Retrieve.accept_lang_val)
    req.add_header(Retrieve.accept_charset_hdr, Retrieve.accept_charset_val)
    req.add_header(Retrieve.keep_alive_hdr, Retrieve.keep_alive_val)
    req.add_header(Retrieve.connection_hdr, Retrieve.connection_val)

    cj = getCookieJar(userId)
    # we only need cookieProcessor since build_opener()
    # adds a lot of default handlers (HTTPHandler, HTTPSHandler) for us
    cookieProcessor = urllib2.HTTPCookieProcessor(cj)
    httpHandler = urllib2.HTTPHandler(debuglevel=dbgLevel)
    httpsHandler = urllib2.HTTPSHandler(debuglevel=dbgLevel)
    opener = urllib2.build_opener(cookieProcessor, httpHandler, httpsHandler)

    response = opener.open(req)

    if not response:
        print "failed to get a response for netflixDoLogin"
        return None
    #print '\n', response.info()

    encoding = response.headers.get(Retrieve.content_encoding_hdr)

    if "gzip" == encoding:
        htmlCompressed = response.read()
        compressedStream = StringIO.StringIO(htmlCompressed)
        gzipper = gzip.GzipFile(fileobj=compressedStream)
        htmlTxt = gzipper.read()
    else:
        htmlTxt = response.read()

    response.close()
    saveCookieJar(userId)

    return htmlTxt

def saveToFile(fileName, txt):
    fo = open(fileName, "wb")
    fo.write(txt)
    fo.close()

def main():
    user = "krzysztofk@pobox.com"
    pwd = "bruhaha03"
    userId = 1
    htmlTxt = getNetflixMainPage(userId, dbgLevel=2)
    saveToFile("loginPage.html", htmlTxt)

    # TODO: parse the html to retrieve variables from form named login_form

    htmlTxt = netflixDoLogin(userId, user, pwd, dbgLevel=2)
    saveToFile("afterLoginPage.html", htmlTxt)
    #print htmlTxt

if __name__ == "__main__":
    main()

