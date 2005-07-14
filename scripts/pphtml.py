# pretty-print html docs
import sys,os,string,os.path

def readFromFile(fileName):
    print "readFromFile(%s)" % fileName
    data = None
    try:
        fo = open(fileName, "rb")
        data = fo.read()
        fo.close()
    except Exception, ex:
        # just ignore any errors
        print "no file %s" % fileName
        data = None
    return data

(TAG_START, TAG_END, TAG_START_END) = range(3)
# TAG_START     is <foo>
# TAG_END       is </foo>
# TAG_START_END is <foo/>

g_prevTag = ""
def getTagType(txt):
    global g_prevTag
    assert txt[0] is '<'
    assert txt[-1] is '>'

    prevTag = g_prevTag
    g_prevTag = txt[1:-1]
    if txt[1] is '/':
        return TAG_END
    if txt[-2] is '/':
        return TAG_START_END

    if prevTag == g_prevTag:
        # we're assuming that this is a mistake: unclosed tag
        # eg as in: "<b>foo<b>" (as opposed to "<b>foo</b>"
        return TAG_END

    # some html tag are start/end even though they're not
    # start/end xml tags
    if 0 == txt.find("<br"):
        return TAG_START_END
    if 0 == txt.find("<img "):
        return TAG_START_END
    if 0 == txt.find("<!--"):
        return TAG_START_END

    return TAG_START

g_curSpacesStr = "                                            "
def getSpaces(spacesCount):
    global g_curSpacesStr
    while len(g_curSpacesStr) < spacesCount:
        g_curSpacesStr += "                                                                 "
    assert spacesCount <= len(g_curSpacesStr)
    return g_curSpacesStr[:spacesCount]

def prettyPrintXml(xmlData, foOut):
    xmlDataLen = len(xmlData)
    curPos = 0
    identLevel = 0
    while True:
        # find the next tag
        startTagPos = string.find(xmlData, "<", curPos)
        endTagPos = string.find(xmlData, ">", startTagPos)

        if startTagPos is -1 or endTagPos is -1:
            foOut.write(xmlData[curPos:])
            foOut.flush()
            break

        beforeTag = xmlData[curPos:startTagPos]
        tag = xmlData[startTagPos:endTagPos+1]
        curPos = endTagPos+1

        dontNewline = False
        if len(beforeTag) > 0:
            if beforeTag[-1] is '\n':
                beforeTag = beforeTag.strip()
        else:
            dontNewline = True
        tagType = getTagType(tag)
        if tagType is TAG_START:
            foOut.write(beforeTag)
            if not dontNewline:
                foOut.write("\n")
            foOut.write(getSpaces(identLevel))
            foOut.write(tag)
            foOut.write("\n")
            identLevel += 1

        if tagType is TAG_END:
            identLevel -= 1
            if identLevel < 0:
                identLevel = 0
            foOut.write(beforeTag)
            if not dontNewline:
                foOut.write("\n")
            foOut.write(getSpaces(identLevel))
            foOut.write(tag)
            foOut.write("\n")

        if tagType is TAG_START_END:
            foOut.write(beforeTag)
            if not dontNewline:
                foOut.write("\n")
            foOut.write(getSpaces(identLevel))
            foOut.write(tag)
            foOut.write("\n")

def main():
    if len(sys.argv) != 3:
        scriptName = os.path.basename(sys.argv[0])
        print "usage: %s fileIn.html fileOut.html" % scriptName
        sys.exit(0)
    fileNameIn = sys.argv[1]
    fileNameOut = sys.argv[2]
    xmlData = readFromFile(fileNameIn)
    if None == xmlData:
        print "file %s doesn't exists" % fileNameIn
        sys.exit(0)
    foOut = open(fileNameOut, "wb")
    prettyPrintXml(xmlData, foOut)
    foOut.close()

if __name__ == "__main__":
    main()
