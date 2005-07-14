# Owner: Krzysztof Kowalczyk
#
# Purpose:
#  Inspect url cache

import sys,string,arscache

def usageAndExit():
    print "Usage: dumpUrlCache fileName [url]"
    sys.exit(0)

def main():
    if len(sys.argv)<2 or len(sys.argv)>3:
        usageAndExit()
    fileName = sys.argv[1]
    url = None
    if len(sys.argv)==3:
        url = sys.argv[2]
    c = arscache.Cache(fileName)
    if None==url:
        for key in c.iterKeys():
            urlData = c.getItem(key)
            print "url: '%s', size=%d" % (key["url"], len(urlData.data))
    else:
        for key in c.iterKeys():
            if key["url"]==url:
                urlData = c.getItem(key)
                print urlData.data
                break

if __name__=="__main__":
    main()

