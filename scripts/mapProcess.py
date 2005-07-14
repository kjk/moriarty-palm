import sys, os, os.path, string, bz2

DEFAULT_FILE = os.path.join("..", "Release", "InfoMan.prc.MAP")

def splitBySpaces(txt):
    elements = []
    curPos = 0
    txtLen = len(txt)
    while True:
        # find the first non-space element
        while curPos < txtLen:
            c = txt[curPos]
            if c is not ' ':
                break
            curPos += 1
        if curPos == txtLen:
            break

        txtStart = curPos
        # find the first space element
        while curPos < txtLen:
            c = txt[curPos]
            if c is ' ':
                break
            curPos += 1
        elements.append(txt[txtStart:curPos])
        if curPos == txtLen:
            break
        curPos += 1
    return elements

def test_splitBySpaces():
    assert (3 == len(splitBySpaces("bar    or d")))
    assert (1 == len(splitBySpaces("bar  ")))
    assert (2 == len(splitBySpaces("     bar  kl")))

def isCodeLine(line):
    if 0 == line.find("Code:"):
        return True
    return False

(TYPE_CODE, TYPE_DATA) = range(2)
def lineToCodeData(line):
    parts = splitBySpaces(line)
    #print parts
    type = parts[0]
    offset = parts[1]
    size = parts[2]
    bytesTxt = parts[3]
    assert parts[3] == "bytes"
    name = parts[4].strip()
    return (name,int(size))

def sortBySize(el1, el2):
    return cmp(el2[1], el1[1])

def sortByName(el1, el2):
    return cmp(el1[0], el2[0])

def isBzipFile(fileName):
    postfix = ".bz2"
    postfixLen = len(postfix)
    if len(fileName)<postfixLen:
        return False
    if postfix == fileName[-postfixLen:]:
        return True
    return False

def test_isBzipFile():
    assert isBzipFile("foo.bz2")
    assert not isBzipFile("foo.bz")
    assert not isBzipFile("")

def processFile(fileName):
    print "reading file: %s" % fileName
    # we're a bit lame in how we deal with duplicate names:
    # we just remove them. More correct handling would be to make them unique
    # by appending file name to them
    dups = []
    entries = {}
    if isBzipFile(fileName):
        fo = bz2.BZ2File(fileName, "r")
    else:
        fo = open(fileName, "rb")
    for line in fo:
        if isCodeLine(line):
            (name,size) = lineToCodeData(line)
            if entries.has_key(name):
                if name not in dups:
                    # print "dup: %s" % name
                    dups.append(name)
            entries[name] = size
    fo.close()
    for dup in dups:
        assert entries.has_key(dup)
        del entries[dup]
    return entries

def doDiff(fileNameOne, fileNameTwo):
    entriesOne = processFile(fileNameOne)
    entriesTwo = processFile(fileNameTwo)

    diff = {}

    for (name, size) in entriesOne.items():
        diff[name] = [size, 0]

    for (name, size) in entriesTwo.items():
        if diff.has_key(name):
            origSize = diff[name][0]
            if size == origSize:
                del diff[name]
            else:
                diff[name] = [origSize,size]
        else:
            diff[name] = [0, size]

    print "diff between %s and %s" % (fileNameOne, fileNameTwo)
    sizeEntries = []
    totalDiff = 0
    for (functionName,sizes) in diff.items():
        beforeSize = sizes[0]
        afterSize = sizes[1]
        sizeDiff = afterSize - beforeSize
        totalDiff += sizeDiff
        sizeEntry = [functionName, sizeDiff, beforeSize, afterSize]
        sizeEntries.append(sizeEntry)

    print "\n* Removed stuff:"
    for sizeEntry in sizeEntries:
        afterSize = sizeEntry[3]
        if 0 == afterSize:
            print "%6d (%4d/%4d) %s" % (sizeEntry[1], sizeEntry[2], sizeEntry[3], sizeEntry[0])

    print "\n* Changed stuff:"
    for sizeEntry in sizeEntries:
        afterSize = sizeEntry[3]
        beforeSize = sizeEntry[2]
        sizeDiff = sizeEntry[1]
        assert 0 != sizeDiff
        if 0!=afterSize and 0!=beforeSize:
            print "%6d (%4d/%4d) %s" % (sizeEntry[1], sizeEntry[2], sizeEntry[3], sizeEntry[0])

    print "\n* Added stuff:"
    for sizeEntry in sizeEntries:
        beforeSize = sizeEntry[2]
        if 0 == beforeSize:
            print "%6d (%4d/%4d) %s" % (sizeEntry[1], sizeEntry[2], sizeEntry[3], sizeEntry[0])

    print "\n* Total change: %d" % totalDiff

def fDetectRemoveCmdFlag(flag):
    fFlagPresent = False
    try:
        pos = sys.argv.index(flag)
        fFlagPresent = True
        sys.argv[pos:pos+1] = []
    except:
        pass
    return fFlagPresent

def usage():
    print "usage: mapProcess.py fileName | [-diff fileOne fileTwo]"

def main():
    global DEFAULT_FILE

    fDiff = fDetectRemoveCmdFlag("-diff")
    if fDiff:
        if 3 != len(sys.argv):
            usage()
            sys.exit(0)
        doDiff(sys.argv[1], sys.argv[2])
        return

    if 1 == len(sys.argv):
        fileName = DEFAULT_FILE
    elif 2 == len(sys.argv):
        fileName = sys.argv[1]
    else:
        usage()
        sys.exit(0)

    entries = processFile(fileName)

    # show entries sorted by name
    #entries.sort(sortByName)
    #for n in range(10):
    #    print "%5d %s" % (entries[n][1], entries[n][0])

    print

    toShow = 30
    entries.sort(sortBySize)
    totalSize = 0
    for n in range(toShow):
        print "%5d %s" % (entries[n][1], entries[n][0])    
        totalSize += entries[n][1]

    print

    print "totalSize for largest %d functions: %d" % (toShow,totalSize)

if __name__ == "__main__":
    #test_isBzipFile()
    main()
