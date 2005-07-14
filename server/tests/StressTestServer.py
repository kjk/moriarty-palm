# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk
#
# The idea is to do stress testing of the server i.e. bombard it with random
# (but valid) requests

import time,threading
import client

g_requestsAtATime = 20
g_totalRequests = 200

def runRandomTest():
    # TODO: obviously, need to make them random
    c = client.Client()
    #c.getMovies("seattle")
    c.ping()

class RandomTestThread(threading.Thread):
    def __init__(self,threadNo):
        self.no = threadNo
        threading.Thread.__init__(self)

    def run(self):
        print "launchign thread no %d" % self.no
        runRandomTest()

def main():
    global g_totalRequests, g_requestsAtATime
    reqsLeft = g_totalRequests
    no = 1
    while reqsLeft > 0:
        th = RandomTestThread(no)
        no += 1
        th.start()
        reqsLeft -= 1
        while threading.activeCount() >= g_requestsAtATime:
            secsToSleep = 0
            if secsToSleep > 0:
                print "sleeping for %d secs" % secsToSleep
                time.sleep(secsToSleep)

if __name__=="__main__":
    main()
