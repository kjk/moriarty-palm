# Gets a log file as an argument and parses it using apropriate parser
# function
import sys, string
from ResultType import *
import m411_by411

REVERSE_PHONE = "411-Reverse-Phone"

def doReversePhone(funArg, url, htmlText):
    res, data = m411_by411.reversePhoneLookup(htmlText)
    if res == UNKNOWN_FORMAT:
        print "failed to parse '%s'" % url
    else:
        print res
        print data

def main():
    fileName = sys.argv[1]
    fo = open(fileName, "rb")
    fun = string.strip(fo.readline())
    funArg = string.strip(fo.readline())
    url = string.strip(fo.readline())
    htmlText = fo.read()
    fo.close()
    print "fun:    '%s'" % fun
    print "funArg: '%s'" % funArg
    print "url:    '%s'" % url

    if REVERSE_PHONE == fun:
        doReversePhone(funArg, url, htmlText)

if __name__ == "__main__":
    main()