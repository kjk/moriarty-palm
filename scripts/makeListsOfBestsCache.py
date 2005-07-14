# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# makes files for listsOfBestsCache

import time
from ResultType import *
import parserUtils
import listsofbests
import urllib2
import pickle
import sys
from definitionBuilder import *

g_maxLevel = 2
g_listsCached = 0
g_listsListsCached = 0

def htmlEqualsNone():
    print "htmlTxt == None"
    print "exiting"
    return None

def notExpectedType(resultType):
    print "resultType not expected"
    print "%s" % str(resultType)
    print "exiting"
    return None
    
def runCacheFill():
    global g_maxLevel
    global g_listsCached
    global g_listsListsCached

    modulesInfo = {}
    modulesInfo['Amazon'] = True
    modulesInfo['ListsOfBests'] = True
    modulesInfo['Lyrics'] = True
    modulesInfo['Encyclopedia'] = True
    modulesInfo['Netflix'] = True
    # else = False

    listsListsCache = {}
    # get data from net (lists of lists)
    translate = {
        "books":"http://listsofbests.com/lists/1/",
        "movies":"http://listsofbests.com/lists/2/",
        "music":"http://listsofbests.com/lists/3/"
        }
    for name in ["Movies", "Books", "Music"]:
        url = translate[name.lower()]
        resp = urllib2.urlopen(url)
        htmlTxt = resp.read()
        if None == htmlTxt:
            return htmlEqualsNone()
        resultType, resultBody = listsofbests.parseListsOfBests(htmlTxt,"",None)
        if LISTSOFBESTS_LISTS == resultType:
            listsListsCache[name] = resultBody
            g_listsListsCached += 1
        else:
            return notExpectedType(resultType)
    # save it
    f = open("lobLists.pic", "wb")
    pickle.dump(listsListsCache,f)
    f.close()
    print "first level cached (lobLists.pic)"    
    # and make level down (lists)
    if g_maxLevel < 2:
        return None
    listsCache = {}
    for name in listsListsCache:
        udf = parserUtils.UDF(listsListsCache[name])
        for i in range(udf.getItemsCount()):
            code = udf.getItemText(i,0)
            if "D" == code:
                # get data from net
                bcf = BCF(udf.getItemText(i,1))
                links = bcf.getAllHyperlinks("s+listsofbestsbrowse:")
                for link in links:
                    fieldValue = link[link.find(':')+1:]
                    (listNo, category) = fieldValue.split(";")
                    category = listsofbests._symbolToCategory(category)
                    url = "http://listsofbests.com/list/%s/" % listNo
                    htmlTxt = None
                    counter = 0
                    while htmlTxt == None and counter < 10:
                        try:
                            resp = urllib2.urlopen(url)
                            htmlTxt = resp.read()
                        except:
                            counter += 1
                            print "\nproblem with retrieve - sleep and wait"
                            time.sleep(10)
                    if counter == 10:
                        return None
                    if None == htmlTxt:
                        return htmlEqualsNone()
                    #TODO: add modulesInfo to cache
                    resultType, resultBody = listsofbests.parseListsOfBests(htmlTxt,category,modulesInfo)
                    if LISTSOFBESTS_LIST == resultType:
                        listsCache[fieldValue] = resultBody
                        g_listsCached += 1
                        sys.stdout.write(".")
                    else:
                        return notExpectedType(resultType)
    # save it
    f = open("lobList.pic", "wb")
    pickle.dump(listsCache,f)
    f.close()
    print "\nsecond level cached  (lobList.pic)"
    print "\nto make items cache run makeListsOfBestsCacheItems.py"
    return None

def usageAndExit():
    print "usage: makeListsOfBestsCache.py maxLevel"
    print "maxLevel - default = 2"
    print "1st - lists of lists, 2nd - lists"
    sys.exit(0)

def main():
    global g_maxLevel
    global g_listsCached
    global g_listsListsCached
    
    args = sys.argv
    if 2 == len(args):
        try:
            g_maxLevel = int(args[1])
        except:
            usageAndExit()
    if g_maxLevel not in [1,2]:
        usageAndExit()

    startTime = time.time()
    runCacheFill()
    stopTime = time.time()
    timeTaken = float(stopTime - startTime)
    print "Ran in %.3fs" % (timeTaken)
    print "Lists of lists cached: %d" % g_listsListsCached
    print "Lists cached: %d" % g_listsCached

if __name__=="__main__":
    main()
