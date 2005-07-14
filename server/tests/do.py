# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk
#
import sys, string, re, socket, random, pickle, time
import arsutils
import netflix

def doNetflixSearch(searchTerm):
    res = netflix.search(searchTerm)
    print res

argsInfo = {
    "netflix-search" : (1, doNetflixSearch),
}

def buildUsage():
    global argsInfo
    allArgs = argsInfo.keys()
    allArgs.sort()
    txt = ""
    for arg in allArgs:
        numArgs = argsInfo[arg][0]
        if numArgs > 0:
            txt = "%s [%s $%d]" % (txt, arg, numArgs)
        else:
            txt = "%s [%s]" % (txt, arg)
    return txt

def usageAndExit():
    print "client.py%s" % buildUsage()

def getIndexSafe(arr, obj):
    pos = None
    try:
        pos = arr.index(obj)
    except:
        pass
    return pos

if __name__=="__main__":
    pos = None
    for argName in argsInfo.keys():
        pos = getIndexSafe(sys.argv, argName)
        if None != pos:
            break

    if None == pos:
        usageAndExit()
        sys.exit(0)

    numArgs = argsInfo[argName][0]
    func = argsInfo[argName][1]
    if 0 == numArgs:
        func()
    elif 1 == numArgs:
        argOne = sys.argv[pos+1]
        func(argOne)
    elif 2 == numArgs:
        argOne = sys.argv[pos+1]
        argTwo = sys.argv[pos+2]
        func(argOne, argTwo)
    else:
        # not handled yet
        assert(False)
        