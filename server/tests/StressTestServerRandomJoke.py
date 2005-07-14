# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk
#
# The idea is to do stress testing of the server i.e. bombard it with random
# (but valid) requests

import time,threading
import client
import Fields

g_requestsAtATime = 200
g_totalRequests = 20

def runRandomTest():
    c = client.Client()
    c.getRandomJoke()
    if not c.getRspField().hasField(Fields.outJoke):
        print "NO JOKE!"
    else:
        print "."

class RandomTestThread(threading.Thread):
    def __init__(self,threadNo):
        self.no = threadNo
        threading.Thread.__init__(self)

    def run(self):
        print "launchign thread no %d" % self.no
        runRandomTest()

import sys

def usageAndExit():
    print "stressTestServerRandomJoke [totalRequest=200] [requestAtTime=20]"
    print "both as integer!"
    print "if only one - it will be threated as totalRequest"
    sys.exit(0)
    
def main():
    global g_totalRequests, g_requestsAtATime
    args = sys.argv
    if 2 == len(args):
        try:
            g_totalRequests = int(args[1])
        except:
            usageAndExit()
    elif 3 == len(args):
        try:
            g_totalRequests = int(args[1])
            g_requestsAtATime = int(args[2])
        except:
            usageAndExit()
    elif 1 != len(args):
        usageAndExit()
    if 1 > g_requestsAtATime:
        g_requestsAtATime = 1
    
    reqsLeft = g_totalRequests
    no = 1
    startTime = time.time()
    while reqsLeft > 0:
        th = RandomTestThread(no)
        no += 1
        th.start()
        reqsLeft -= 1
        while threading.activeCount() > g_requestsAtATime:
            secsToSleep = 0
            if secsToSleep > 0:
                print "sleeping for %d secs" % secsToSleep
                time.sleep(secsToSleep)

    # wait for thread close
    while threading.activeCount() > 1:
        secsToSleep = 0
    stopTime = time.time()
    timeTaken = float(stopTime - startTime)
    print "Ran %d in %.3fs" % (g_totalRequests, timeTaken)

if __name__=="__main__":
    main()
