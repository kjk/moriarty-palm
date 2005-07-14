# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk
#
# this is amazon browse test...
# multithread - each category have its own thread

import time,threading
import client
import Fields
import parserUtils

g_exceptionsCount = 0
g_maxLevel = 10
g_searchIndexList = [
    ["Books", "Books", "Books"],
    ["Music", "Music", "Music"],
    ["DVD", "DVD", "DVD"],
    ["Video", "Video", "Video"],
    ["VHS", "VHS", "VHS"],
    ["Video Games", "VideoGames", "VideoGames"],
    ["Photo", "Photo", "Photo"],
    ["Electronics", "Electronics", "Electronics"],
    ["Toys", "Toys", "Toys"],
    ["Tools", "Tools", "Tools"],
    ["Computers", "PCHardware", "computers"],
    ["Sports & Outdoors", "SportingGoods", "SportingGoods"],
    ["Software", "Software", "Software"],
    ["Health & Personal Care", "HealthPersonalCare", "health"],
    ["Wireless", "Wireless", "Wireless"],
    ["Office Products", "OfficeProducts", "Office"],
    ["Baby", "Baby", "Baby"],
    ["Outdoor Living", "OutdoorLiving", "OutdoorLiving"],
    ["Musical Instruments", "MusicalInstruments", "MusicalInstruments"],
    ["Kitchen", "Kitchen", "Kitchen"],
    ["Wireless Accessories", "WirelessAccessories", "WirelessAccessories"],
    ["Beauty", "Beauty", "Beauty"],
    ["Apparel", "Apparel", "Apparel"],
    ["Magazines", "Magazines", "Magazines"],
    ["Jewelry", "Jewelry", "Jewelry"],
    ["Gourmet Food", "GourmetFood", "GourmetFood"]
    ]

def runBrowseSmallTest(search_index, node, level=1):
    if level >= g_maxLevel:
        return
    c = client.Client()
    c.getAmazonBrowse(search_index,node)
    if c.getRspField().hasField(Fields.outAmazonBrowse):
        print "."
        udfTxt = c.getRspField().getField("Amazon-Browse")
        udf = parserUtils.UDF(udfTxt)
        itemsCount = udf.getItemsCount()
        i = 1        # first comes ..
        while i < itemsCount:
            childNode = udf.getItemText(i,0)
            if childNode != "":
                runBrowseSmallTest(search_index,childNode,level+1)
            i += 1
    elif c.getRspField().hasField(Fields.outAmazonSearch):
        print ","
    else:
        print "No Amazon-Browse and no Amazon-Search in response\nfor: %s %s" % (search_index, node)

def runBrowseTest(index):
    c = client.Client()
    c.getAmazonBrowse("Blended",g_searchIndexList[index][2])
    if not c.getRspField().hasField(Fields.outAmazonBrowse):
        print "No 1st level browse results!!!"
    else:
        print "."
        udfTxt = c.getRspField().getField("Amazon-Browse")
        udf = parserUtils.UDF(udfTxt)
        itemsCount = udf.getItemsCount()
        i = 1        # first comes ..
        while i < itemsCount:
            node = udf.getItemText(i,0)
            if node != "":
                runBrowseSmallTest(g_searchIndexList[index][1],node)
            i += 1

class RandomTestThread(threading.Thread):
    def __init__(self,threadNo):
        self.no = threadNo
        threading.Thread.__init__(self)

    def run(self):
        global g_exceptionsCount
        print "Starting thread browsing %s" % g_searchIndexList[self.no][0]
        try:
            runBrowseTest(self.no)
        except:
            print "EXCEPTION!"
            print "%s thread active" % str(threading.activeCount())
            g_exceptionsCount += 1
            
        print "Stopping thread browsing %s" % g_searchIndexList[self.no][0]

import sys

def usageAndExit():
    print "usage: AmazonFillCacheTests.py maxLevel maxThread"
    print "maxLevel - default = 10 - recurency deep level"
    print "maxThread - default = 50 - how many threads works together"
    sys.exit(0)

g_useThreads = True

def main():
    global g_maxLevel
    args = sys.argv
    if 2 == len(args):
        g_maxLevel = int(args[1])
    maxThread = 50    
    if 3 == len(args):
        g_maxLevel = int(args[1])
        maxThread = int(args[2])
        if maxThread < 1:
            maxThread = 1
    no = 0
    reqsLeft = len(g_searchIndexList)
    startTime = time.time()
    while reqsLeft > 0:
        if g_useThreads:
            th = RandomTestThread(no)
            no += 1
            th.start()
        else:
            runBrowseTest(no)
            no += 1
        reqsLeft -= 1
        while threading.activeCount() > maxThread:
            time.sleep(2)

    # wait for thread close
    while threading.activeCount() > 1:
        secsToSleep = 0
    stopTime = time.time()
    timeTaken = float(stopTime - startTime)
    print "Ran in %.3fs" % (timeTaken)
    print "Exceptions count: %d" % g_exceptionsCount

if __name__=="__main__":
    main()
