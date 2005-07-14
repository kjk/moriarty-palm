#### Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  functions that helps parsing with BeautifulSoup
#  and some others usefull stuff
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
from entities import convertEntities23

def retrieveContents(tag):
    if not isinstance(tag, Tag):
        return " ".join(convertEntities23(str(tag)).split())

    out = []
    for cont in tag.contents:
        out.append(retrieveContents(cont))

    return " ".join(out)


def getAllTextFromTag(tag):
    if not isinstance(tag, Tag):
        return string.join(str(tag).split(), " ")
    returned = []
    for cont in tag.contents:
        if not isinstance(cont, Tag):
            returned.append(str(cont).replace("\n"," ").replace("\x0d","").replace("\x0a",""))
        else:
            returned.append(getAllTextFromTag(cont))
    parts = string.join(returned," ").split()
    return string.join(parts," ")

def getLastElementFromTag(tag):
    if not isinstance(tag, Tag):
        return tag
    contentsCount = len(tag.contents)
    if contentsCount > 0:
        return getLastElementFromTag(tag.contents[contentsCount-1])
    return tag

def getAllTextFromTo(tagStart, tagEnd):
    next = tagStart
    returned = []
    while next != tagEnd:
        if not isinstance(next, Tag):
            returned.append(str(next).replace("\n"," ").replace("\x0d","").replace("\x0a",""))
        next = next.next
    return string.join(returned," ").replace("   "," ").replace("  "," ")

def getAllTextFromToInBrFormat(tagStart, tagEnd):
    next = tagStart
    returned = []
    brBuffer = []
    while next != tagEnd:
        if not isinstance(next, Tag):
            text = str(next).replace("\n"," ").replace("\t"," ").replace("\x0d"," ")
            if 0 < len(text.strip()):
                left = ""
                right = ""
                if not text.startswith(text.strip()):
                    left = " "
                if not text.endswith(text.strip()):
                    right = " "
                text = left + text.strip() + right
                text = text.replace("  "," ")
                returned.append(string.join(brBuffer))
                brBuffer = []
                returned.append(text)
        if isinstance(next, Tag):
            if "br" == next.name or "p" == next.name:
                if 0 < len(returned):
                    brBuffer.append("<br>")
                    if "p" == next.name:
                        brBuffer.append("<br>")
            # <b> - any idea how to find </b> - it will be 2 lines instead of this:
            elif "b" == next.name:
                # get text inside <b>
                returned.append(string.join(brBuffer))
                brBuffer = []
                returned.append("<b>")
                bItem = next
                tableInsideB = next.contents
                for contentB in tableInsideB:
                    if isinstance(contentB, Tag):
                        if "br" == contentB.name or "p" == contentB.name:
                            if 0 < len(returned):
                                brBuffer.append("<br>")
                                if "p" == contentB.name:
                                    brBuffer.append("<br>")
                    if not isinstance(contentB, Tag):
                        text = contentB
                        text = str(text).replace("\n"," ").replace("\t"," ")
                        text = str(text).replace("\x0d"," ") #unix enters
                        text = str(text).strip().replace("  "," ")
                        if 0 < len(text):
                            returned.append(string.join(brBuffer))
                            brBuffer = []
                            returned.append(text)
                returned.append(string.join(brBuffer))
                brBuffer = []
                returned.append("</b>")
                next = getLastElementFromTag(bItem)
        next = next.next
    ret = string.join(returned,"").replace("\t"," ")
    # remove whitespaces from text
    length = len(ret)+1
    while len(ret) != length:
        length = len(ret)
        ret = ret.replace("  "," ")
    return ret

# return data in our universalDataFormat
#
# example:
#
# 2                             ## number of items
# 6 5                           ## number of elements in each item
# 7 2 5
# martha smith seattle wa 98101 ## elements (separated by ' ')
#
def universalDataFormat(listOfLists):
    assert isinstance(listOfLists,list)
    header = ["%d" % len(listOfLists)]
    results = []
    for smallList in listOfLists:
        headerItem = []
        for item in smallList:
            results.append(item)
            headerItem.append("%d" % len(item))
        header.append(string.join(headerItem," "))
    return "%s\n%s " % (string.join(header,"\n"), string.join(results," "))

# the same but remove entities form items
def universalDataFormatReplaceEntities(listOfLists):
    assert isinstance(listOfLists,list)
    header = ["%d" % len(listOfLists)]
    results = []
    for smallList in listOfLists:
        headerItem = []
        for item in smallList:
            #remove entities
            item = convertNumberedEntities(0, item)
            item = convertNamedEntities(0, item)
            # add it to lists
            results.append(item)
            headerItem.append("%d" % len(item))
        header.append(string.join(headerItem," "))
    return "%s\n%s " % (string.join(header,"\n"), string.join(results," "))

# first item in udf is definition
def universalDataFormatWithDefinition(definition, listOfLists):
    assert isinstance(listOfLists,list)
    header = ["%d" % (len(listOfLists) + 1)]
    serializedDefinition = definition.serialize()
    header.append("1 " + ("%d" % len(serializedDefinition)))
    results = ["D", serializedDefinition]
    for smallList in listOfLists:
        headerItem = []
        for item in smallList:
            item = convertNumberedEntities(0, item)
            item = convertNamedEntities(0, item)
            results.append(item)
            headerItem.append("%d" % len(item))
        header.append(string.join(headerItem," "))
    return "%s\n%s " % (string.join(header,"\n"), string.join(results," "))

# for geting text form xml texts
# (they can include <i> or other tags, we just want to remove them)
# replace <br> and <p> with "\n"
def getTextFromDirtyText(dirtyText):
    soup = BeautifulSoup()
    soup.feed("<xxx>"+dirtyText+"</xxx><yyy>test</yyy>")
    dirtySoup = soup.first("xxx")
    textWithBr = getAllTextFromToInBrFormat(dirtySoup, getLastElementFromTag(dirtySoup).next)
    text = textWithBr.replace("<br>","\n").replace("<b>","").replace("</b>","")
    return text

# I need to test it!
class UDF:
    def __init__(self, udfText):
        textSplitted = udfText.split("\n")
        self.vectorSize = int(textSplitted[0])
        textSplitted = udfText.split("\n", self.vectorSize+1)
        vector = []
        i = 1
        while i <= self.vectorSize:
            smallVectorText = textSplitted[i].split(" ")
            smallVector = []
            for item in smallVectorText:
                smallVector.append(int(item))
            vector.append(smallVector)
            i += 1
        textData = textSplitted[self.vectorSize+1]
        offsetStart = 1
        offsetEnd = 0
        self.data = []
        for smallV in vector:
            itemData = []
            for number in smallV:
                offsetEnd += number + 1
                itemData.append(textData[offsetStart-1:offsetEnd-1])
                offsetStart = offsetEnd + 1
            self.data.append(itemData)

    def getItemsCount(self):
        return len(self.data)

    def getItemElementsCount(self, itemNo):
        return len(self.data[itemNo])

    def getItemText(self, itemNo, elemNo):
        return self.data[itemNo][elemNo]

# convert UDF text to a more human-readable text
def udfPrettyPrint(txt):
    restTxt = txt
    (line,restTxt) = restTxt.split("\n",1)
    listsNo = int(line)
    result = "Number of lists: %d\n" % listsNo

    listItemsLen = []
    for l in range(listsNo):
        (line,restTxt) = restTxt.split("\n",1)
        itemsLenTxt = line.split(" ")
        itemsLen = [int(itemLenTxt) for itemLenTxt in itemsLenTxt]
        listItemsLen.append(itemsLen)

    listNo = 0
    txtStart = 0
    for itemsLen in listItemsLen:
        result += "** list %d\n" % listNo
        for itemLen in itemsLen:
            txt = restTxt[txtStart:txtStart+itemLen]
            result += "  %s\n" % txt
            txtStart = txtStart + itemLen + 1
        listNo += 1
    #result += restTxt
    return result

##
g_onlySmallCaps=["THE", "IN", "ON", "AT", "WITH", "WITHOUT", "FOR", "FROM", "TO", "OF", "S", "AND", "DE", "LA", "LE", "L", "SANS", "A"]
def uncapitalizeWord(word, ignoreSmallCaps):
    if not ignoreSmallCaps:
        if word.upper() in g_onlySmallCaps:
            return word.lower()
    return word[:1].upper()+word[1:].lower()
##
def uncapitalizeText(text, ignoreSmallCaps=False):
    wordStart=0
    wordEnd=0
    pos=0
    inWord=False
    res=""
    prevC=""
    for c in text:
        if not prevC.isalpha() and c.isalpha():
            wordStart=pos
            inWord=True
        elif prevC.isalpha() and not c.isalpha():
            wordEnd=pos
            inWord=False
            res+=uncapitalizeWord(text[wordStart:wordEnd], ignoreSmallCaps)
        if not c.isalpha():
            res+=c
        pos+=1
        prevC=c
    if inWord:
        res+=uncapitalizeWord(text[wordStart:], ignoreSmallCaps)
    return res

# change:
#  ALAN D FOSTER
#  alan d foster
#  Alan d Foster
# or others variations to:
#  Alan D Foster
#
# if detectSmallCaps == True then words like "the" or "in" will be lowered.
#
def makeTitleCase(text, detectSmallCaps=True):
    return uncapitalizeText(text, detectSmallCaps)
