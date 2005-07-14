# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  parses html data from lyrictracker.com
#
import sys, string, arsutils
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
from definitionBuilder import Definition
from definitionBuilder import justLeft, justRight, justInherit, justCenter, justRightLast
from Retrieve import *
from popupMenu import *

ARTIST_IDX = 0
TITLE_IDX = 1
LYRIC_ID_IDX = 2

def setArtistLink(gtxt, artist, modulesInfo):
    lyricsHyperlink = "s+lyricssearch:"+ artist + ";;;;"
    if None != modulesInfo:
        popupItems = []
        popupItems.append(["Search Lyrics",lyricsHyperlink,False,True,False])
        if modulesInfo["Amazon"]:
            popupItems.append(["Search Amazon","s+amazonsearch:Music;;1;"+artist,False,False,False])
        if modulesInfo["ListsOfBests"]:
            popupItems.append(["Search Lists of Bests","s+listsofbestssearch:"+artist+";Music;Creator",False,False,False])
        if modulesInfo["Encyclopedia"]:
            popupItems.append(["Search Encyclopedia","s+pediasearch:"+artist,False,False,False])
        if modulesInfo['eBay']:
            popupItems.append(['Search eBay',"s+ebay:search;0;?;"+artist,False,False,False])

        if len(popupItems) > 1:
            gtxt.setHyperlink(buildPopupMenu(popupItems))
        else:
            gtxt.setHyperlink(lyricsHyperlink)
    else:
        gtxt.setHyperlink(lyricsHyperlink)

def searchResultsToDefinition(searchResults, modulesInfo):
    assert len(searchResults) > 0

    df = Definition()
    for result in searchResults:
        title = result[TITLE_IDX]
        artist = result[ARTIST_IDX]
        lyricsId = result[LYRIC_ID_IDX]

        df.TextElement(title, link = "s+lyricsitem:"+lyricsId, style="bold")
        #df.LineBreakElement()
        df.TextElement(" by ")
        gtxt = df.TextElement(artist)
        setArtistLink(gtxt, artist, modulesInfo)
        df.LineBreakElement()

    assert not df.empty()

    df.LineBreakElement()
    gtxt = df.TextElement("New Search")
    gtxt.setHyperlink("lyricsform:search")
    gtxt.setJustification(justCenter)
    return df

def searchResultsToDefinitionTwo(searchResults, modulesInfo):
    assert len(searchResults) > 0

    df = Definition()
    df.TextElement("Search results:")
    for result in searchResults:
        title = result[TITLE_IDX]
        artist = result[ARTIST_IDX]
        lyricsId = result[LYRIC_ID_IDX]

        df.BulletElement(False)
        df.TextElement(title, link = "s+lyricsitem:"+lyricsId, style='bold')

        df.TextElement(" by ")
        gtxt = df.TextElement(artist)
        setArtistLink(gtxt, artist, modulesInfo)
        df.PopParentElement()

    df.LineBreakElement()
    gtxt = df.TextElement("New Search")
    gtxt.setHyperlink("lyricsform:search")
    gtxt.setJustification(justCenter)
    return df

def searchResultsToDefinitionThree(searchResults, modulesInfo):
    assert len(searchResults) > 0
    uniqueArtists = {}
    for result in searchResults:
        artist = string.lower(result[ARTIST_IDX])
        if uniqueArtists.has_key(artist):
            uniqueArtists[artist].append(result)
        else:
            uniqueArtists[artist] = [result]

    df = Definition()

    for (artist, songs) in uniqueArtists.items():
        artist = songs[0][ARTIST_IDX]
        df.TextElement("Songs by ")
        gtxt = df.TextElement(artist)
        setArtistLink(gtxt, artist, modulesInfo)
        df.TextElement(":")
        for song in songs:
            title = song[TITLE_IDX]
            artist = song[ARTIST_IDX]
            lyricsId = song[LYRIC_ID_IDX]

            df.BulletElement(False)
            gtxt = df.TextElement(title)
            gtxt.setHyperlink("s+lyricsitem:"+lyricsId)
            gtxt.setStyle('bold')
            df.PopParentElement()
        df.LineBreakElement()

    gtxt = df.TextElement("New Search")
    gtxt.setHyperlink("lyricsform:search")
    gtxt.setJustification(justCenter)
    return df

## version with definitionBuilder
# try parsing search results (LYRICS_SEARCH or NO_RESULTS)
# if unable return UNKNOWN_FORMAT
def tryParseSearchDefinition(htmlTxt, fArtistSearch, modulesInfo, keywords):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    # no results
    input = soup.first("input", {"name":"albumName"})
    if input:
        return NO_RESULTS, None

    # get td's
    headerList = soup.fetch("td", {"class":"tb_header"})
    tdList = soup.fetch("td", {"class":"tb_row_r2"})
    if len(headerList) == 0 or len(tdList) == 0:
        return UNKNOWN_FORMAT, None
    # test modulo offset
    headersCount = len(headerList)
    if (len(tdList) % headersCount) != 0:
        return UNKNOWN_FORMAT, None

    searchResults = []    
    # get results
    for index in range(len(tdList)-1):
        artist = getAllTextFromTag(tdList[index]).strip()
        title = getAllTextFromTag(tdList[index+1]).strip()
        urlStart = "show.php?id="
        aItem = tdList[index+1].first("a", {"href":urlStart+"%"})
        if aItem:
            lyricsId = aItem['href'][len(urlStart):]
            searchResults.append([artist, title, lyricsId])

    if 0 == len(searchResults):
        return (UNKNOWN_FORMAT, None)

    if fArtistSearch:
        df = searchResultsToDefinitionThree(searchResults, modulesInfo)
    else:
        #df = searchResultsToDefinition(searchResults, modulesInfo)
        df = searchResultsToDefinitionTwo(searchResults, modulesInfo)

    return LYRICS_SEARCH, universalDataFormatWithDefinition(df, 
        [["H", "Search: "+keywords]])

# try parsing item
# if unable return UNKNOWN_FORMAT
def tryParseItemDefinition(htmlTxt, modulesInfo):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    pageHeader1 = soup.first("span", {"class":"pageheader1"})
    pageHeader2 = soup.first("span", {"class":"pageheader2"})
    contentTd = soup.first("td", {"class":"content1"})
    if not contentTd or not pageHeader1:
        return UNKNOWN_FORMAT, None

    df = Definition()
    title = getAllTextFromTag(pageHeader1).strip()
    note = ""
    if pageHeader2:
        note = getAllTextFromToInBrFormat(pageHeader2, getLastElementFromTag(pageHeader2).next).strip()
    text = getAllTextFromToInBrFormat(contentTd, getLastElementFromTag(contentTd).next).strip()

    gtxt = df.TextElement(title)
    gtxt.setStyle('bold')
    #df.LineBreakElement()
    albumText = "from the album "
    performedText = "performed by "
    for noteLine in note.split("<br>"):
        noteLine = noteLine.strip()
        if noteLine.startswith(albumText):
            df.TextElement(" from ")
            album = noteLine[len(albumText):]
            gtxt = df.TextElement(album)
            lyricsHyperlink = "s+lyricssearch:;;" + album + ";;"
            if None != modulesInfo:
                popupItems = []
                popupItems.append(["Search Lyrics",lyricsHyperlink,False,True,False])
                if modulesInfo["Amazon"]:
                    popupItems.append(["Search Amazon","s+amazonsearch:Music;;1;"+album,False,False,False])
                if modulesInfo["ListsOfBests"]:
                    popupItems.append(["Search Lists of Bests","s+listsofbestssearch:"+album+";Music;Title",False,False,False])
                #TODO: more?
                if len(popupItems) > 1:
                    gtxt.setHyperlink(buildPopupMenu(popupItems))
                else:
                    gtxt.setHyperlink(lyricsHyperlink)
            else:
                gtxt.setHyperlink(lyricsHyperlink)
        elif noteLine.startswith(performedText):
            df.TextElement(" by ")
            artist = noteLine[len(performedText):]
            ## remove " in yyyy"
            if len(artist) > 8:
                if artist[-8:-4] == " in " and artist[-4:].isdigit():
                    year = artist[-8:]
                    artist = artist[:-8]
                    gtxt = df.TextElement(artist)
                    df.TextElement(year)
                else:
                    gtxt = df.TextElement(artist)
            else:
                gtxt = df.TextElement(artist)
            setArtistLink(gtxt, artist, modulesInfo)
        else:
            df.TextElement(noteLine)

    df.LineBreakElement(1,2)

    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
#    df.TextElement("New Search", link="lyricsform:search")
#    df.LineBreakElement(3,2)

    # this remove double linebreaks...
    text2 = text.replace("<br> <br>","###2br###") # we hope there is no "###2br###" in text
    if -1 == text2.find("<br>"):
        text = text2.replace("###2br###","<br>")
    
    wasBreak = False
    for textLine in text.split("<br>"):
        if len(textLine.strip()) > 0:
            df.TextElement(textLine.strip())
            wasBreak = False
        if wasBreak:
            df.LineBreakElement(1,2)
        else:
            df.LineBreakElement()
            wasBreak = True
    df.PopParentElement()

    return LYRICS_ITEM, universalDataFormatWithDefinition(df, [["H", title]])

def parseLyricsDefinition(htmlTxt, fArtistSearch, modulesInfo, keywords):
    type, body = tryParseSearchDefinition(htmlTxt, fArtistSearch, modulesInfo, keywords)
    if UNKNOWN_FORMAT != type:
        return (type, body)

    type, body = tryParseItemDefinition(htmlTxt, modulesInfo)
    if UNKNOWN_FORMAT != type:
        return (type, body)

    return type, body

def getLyricsItem(itemId, modulesInfo, dbgLevel = 0):
    url = "http://lyrictracker.com/show.php?id=%s" % itemId
    refererUrl = "http://lyrictracker.com"
    htmlTxt = getHttp(url, referer = refererUrl, dbgLevel=dbgLevel)
    if None == htmlTxt:
        return (MODULE_DOWN, None)
    resultType, resultBody = parseLyricsDefinition(htmlTxt, False, modulesInfo, "")
    if UNKNOWN_FORMAT == resultType:
        resultBody = (url, htmlTxt)
    return (resultType, resultBody)

def getLyricsSearch(artist, title, album, composer, fullText, modulesInfo, dbgLevel=0):
    postData = {
        "type"         : "advanced",
        "artistName"   : artist,
        "titleName"    : title,
        "albumName"    : album,
        "composerName" : composer,
        "fullText"     : fullText
    }
    keywords = ""
    kList = [artist, title, album, composer, fullText]
    for item in kList:
        if len(keywords) > 0 and len(item.strip()) > 0:
            keywords += ", "
        keywords += item.strip()
    url = "http://lyrictracker.com/search.php"
    refererUrl = "http://lyrictracker.com"

    fArtistSearch = False
    if 0 != len(artist):
        fArtistSearch = True

    htmlTxt = getHttp(url, postData = postData, referer = refererUrl, dbgLevel=dbgLevel)
    if None == htmlTxt:
        return (MODULE_DOWN, None)
    resultType, resultBody = parseLyricsDefinition(htmlTxt, fArtistSearch, modulesInfo, keywords)
    return (resultType, resultBody)

def usage():
    print "usage: lyrics.py [-item $lyricsId] | [artist];[title];[album];[composer];[fulltext]"

def main():
    itemId = arsutils.getRemoveCmdArg("-item")
    if None == itemId:
        itemId = arsutils.getRemoveCmdArg("--item")
    if itemId:
        (resultType, resultBody) = getLyricsItem(itemId, None, dbgLevel=1)
    else:
        if 2 != len(sys.argv):
            usage()
            sys.exit(0)

        arg = sys.argv[1]
        print "arg=%s" % arg
        argParts = arg.split(";")
        if 5 != len(argParts):
            print "len(argParts) = %d, not 5" % len(argParts)
            usage()
            sys.exit(0)

        artist,title,album,composer,fullText = argParts

        (resultType, resultBody) = getLyricsSearch(artist, title, album, composer, fullText, None, dbgLevel=1)

    if MODULE_DOWN == resultType:
        print "module down"
    if UNKNOWN_FORMAT == resultType:
        print "unknown format"
    if NO_RESULTS == resultType:
        print "no results"
    if LYRICS_ITEM == resultType:
        print "got LYRICS_ITEM"
        #print udfPrettyPrint(resultBody)
    if LYRICS_SEARCH == resultType:
        print "got LYRICS_SEARCH"
        print udfPrettyPrint(resultBody)
        #print resultBody

if __name__ == "__main__":
    main()

