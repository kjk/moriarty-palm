import sys, m411_by411

def usageAndExit():
    print "Usage: parseFromErrorFile.py $fileName"
    sys.exit(0)

def main():
    if len(sys.argv) != 2:
        usageAndExit();
    fileName = sys.argv[1]
    fo = open(fileName, "rb")
    query = fo.readline().strip()
    queryArg = fo.readline().strip()
    queryUrl = fo.readline().strip()
    queryHtml = fo.read()
    fo.close()
    print "query: " + query
    print "arg: " + queryArg
    print "url:" + queryUrl

    if query == "411-Reverse-Phone":
        res = m411_by411.reversePhoneLookup(queryHtml)
        print res
if __name__ == "__main__":
    main()

    