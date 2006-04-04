# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk
#
# This tests all html parsers used in InfoMan. The idea is that we
# store original *.html files and corresponding *.extracted files
# that contain extracted data. We run parsing function on each .html
# file and we check if the result looks exactly like *.extracted file

import sys, os, os.path, fnmatch
import boxoffice, currency_evocash, dreams, jokes, stocks, m411, weather
import epicurious, movies, currency_exchangerate, gasprices, listsofbests
import netflix, m411_by411, horoscopes

# structure describing our test data. For each parsing function
# (second argument) it lists a directory that contains data
# (*.html and corresponding *.extracted) for each parsing
# We look through files in this directory, for each *.html file
# call parsing function and compare the result of this function
# with corresponding *.extracted file
g_testDataTst = [
  ["data\\listsofbests", listsofbests.parseListsOfBests],
]
g_testData = [
  ["data\\listsofbests", listsofbests.parseListsOfBests],
  ["data\\listsofbests\\search", listsofbests.parseListsOfBestsSearch],
  ["data\\listsofbests\\items", listsofbests.parseListsOfBests],
  ["data\\boxoffice", boxoffice.parseYahooBoxOffice],
  #["data\\currency_evocash", currency_evocash.parseCurrency],
  ["data\\dreams", dreams.parseDream],
  ["data\\dreams\\2ndSource", dreams.parseDream2],
  ["data\\jokes\\joke", jokes.parseJoke],
  ["data\\jokes\\list", jokes.parseList],
  ["data\\stocks\\name", stocks.parseName],
  ["data\\stocks\\detailed", stocks.parseStock],
  ["data\\stocks\\list", stocks.parseList],
  ["data\\movies", movies.parseMovies],
  ["data\\epicurious\\recipe", epicurious.parseRecipe],
  ["data\\epicurious\\list", epicurious.parseSearch],
  ["data\\weather", weather.parseWeather],
  ["data\\weather\\multiselect", weather.parseMultiselect],
  ["data\\m411\\AreaCodeByCity", m411.areaCodeByCity],
  ["data\\m411\\ZipCodeByCity", m411.ZIPCodeByCity],
  ["data\\m411\\ReverseAreaCodeLookup", m411.reverseAreaCodeLookup],
  ["data\\m411\\ReverseZIPCodeLookupAreaCodeByCity", m411.reverseZIPCodeLookup],
  ["data\\m411\\ReversePhoneLookup", m411.reversePhoneLookup],
  ["data\\m411\\InternationalCodeSearch", m411.internationalCodeSearch],
  ["data\\m411\\PersonSearch", m411.personSearch],
  ["data\\m411\\BusinessSearch", m411.businessSearch],
  ["data\\m411\\BusinessSearch\\switchboard", m411_by411.parseSwitchboardBusiness],
  #["data\\currency_exchangerate", currency_exchangerate.parseCurrencyData],
  ["data\\gasprices", gasprices.parseGas],
  ["data\\netflix\\browse", netflix.parseBrowse],
  ["data\\netflix\\browseItems", netflix.parseItems],
  ["data\\netflix\\item", netflix.parseItem],
  ["data\\netflix\\search", netflix.parseSearch],
  ["data\\horoscopes\\yahoo", horoscopes.parseHoroscope],
  ["data\\m411\\ReversePhoneLookup\\411", m411_by411.reversePhoneLookup],
  ["data\\m411\\PersonSearch\\411", m411_by411.personSearch],
  ["data\\m411\\AreaCodeByCity\\411", m411_by411.areaCodeByCity],
  ["data\\m411\\ReverseAreaCodeLookup\\411", m411_by411.reverseAreaCodeLookup],
]

def listFiles(root, patterns='*', recurse=1, return_folders=0):
    # Expand patterns from semicolon-separated string to list
    pattern_list = patterns.split(';')
    # Collect input and output arguments into one bunch
    class Bunch:
        def __init__(self, **kwds):
            self.__dict__.update(kwds)

    arg = Bunch(recurse=recurse, pattern_list=pattern_list,
        return_folders=return_folders, results=[])

    def visit(arg, dirname, files):
        # Append to arg.results all relevant files (and perhaps folders)
        for name in files:
            fullname = os.path.normpath(os.path.join(dirname, name))
            if arg.return_folders or os.path.isfile(fullname):
                for pattern in arg.pattern_list:
                    if fnmatch.fnmatch(name, pattern):
                        arg.results.append(fullname)
                        break
        # Block recursion if recursion was disallowed
        if not arg.recurse: files[:]=[]

    os.path.walk(root, visit, arg)

    return arg.results

def readFile(fileName):
    fo = open(fileName, "rb")
    data = fo.read()
    fo.close()
    return data

def writeToFile(fileName,data):
    fo = open(fileName, "wb")
    fo.write(data)
    fo.close()

def deleteFilesInADir(dir):
    files = listFiles(dir,recurse=0)
    for f in files:
        #print "deleted %s" % f
        os.remove(f)

g_totalTestsCount = 0
g_failures = []
def appendFailure(origFileName,origContent,newParsed):
    global g_failures
    g_failures.append([origFileName,origContent,newParsed])

def dumpFailures():
    global g_failures, g_totalTestsCount
    failuresCount = len(g_failures)
    print "\ntotal tests: %d" % g_totalTestsCount

    if 0 == failuresCount:
        print "no failures"
        return

    print "failures: %d" % failuresCount
    for f in g_failures:
        print "failed for %s" % f[0]
    # dump the data to tmp\orig and tmp\new directories
    # and execute windiff

    try:
        os.mkdir("tmp")
    except:
        pass

    try:
        os.mkdir("tmp\\orig")
    except:
        pass

    try:
        os.mkdir("tmp\\new")
    except:
        pass

    deleteFilesInADir("tmp\\orig")
    deleteFilesInADir("tmp\\new")

    for f in g_failures:
        fileName = f[0]
        origData = f[1]
        newData = f[2]
        fileName = fileName.replace("\\", "_") # make a flat file name out of a directory
        writeToFile("tmp\\orig\\%s" % fileName, origData)
        writeToFile("tmp\\new\\%s" % fileName, newData)
        #print origData
        #print newData

    print "do: windiff tmp\\orig tmp\\new to see the differences"

def remEmptyLines(arr):
    ret = []
    for txt in arr:
        if len(txt)>0:
            ret.append(txt)
    return ret

def txtEqualIgnoreNewlineDiffs2(txtOne,txtTwo):
    txtOneLines = [l.strip() for l in txtOne.split("\n")]
    txtTwoLines = [l.strip() for l in txtTwo.split("\n")]
    txtOneLines = remEmptyLines(txtOneLines)
    txtTwoLines = remEmptyLines(txtTwoLines)

    if len(txtOneLines) != len(txtTwoLines):
        print "diff num of lines"
        return False
    for (lineOne,lineTwo) in zip(txtOneLines,txtTwoLines):
        if lineOne != lineTwo:
            print "%s != %s" % (lineOne, lineTwo)
            return False
    return True

def txtEqualIgnoreNewlineDiffs(txtOne,txtTwo):
    txtOne = txtOne.strip()
    txtTwo = txtTwo.strip()
    txtOne = txtOne.replace("\r\n", "\n")
    txtTwo = txtTwo.replace("\r\n", "\n")
    if txtOne == txtTwo:
        return True
    return False

def testFilesInDir(dir,parsingFunction):
    global g_totalTestsCount
    # build a list of *.html and corresponding *.extracted files
    # in the directory
    filesHtml = listFiles(dir,'*.html',0,0)
    filesExtracted = listFiles(dir,'*.extracted',0,0)
    for fileHtml in filesHtml:
        fileExtracted = fileHtml[:-4] + "extracted"
        #print fileHtml
        #print fileExtracted
        if not fileExtracted in filesExtracted:
            print "corresponding file %s to %s is missing" % (fileExtracted, fileHtml)
            continue
        #print "processing %s, %s" % (fileHtml,fileExtracted)
        fileContent = readFile(fileHtml)
        status, parsed = parsingFunction(fileContent)
        if None == parsed:
            parsed = ""
        parsed = str(parsed) # needed for currency which returns a dict, not a text
        extractedContent = readFile(fileExtracted)
        if not txtEqualIgnoreNewlineDiffs(parsed,extractedContent):
            appendFailure(fileExtracted, extractedContent, parsed)
            print "\n* failure %s, %s" % (fileHtml, fileExtracted)
        else:
            #print "  ok %s, %s" % (fileHtml, fileExtracted)
            sys.stdout.write(".")
        g_totalTestsCount += 1

def main():
    global g_testData
    for test in g_testData:
        dir = test[0]
        parsingFunction = test[1]
        testFilesInDir(dir,parsingFunction)
    dumpFailures()

if __name__ == "__main__":
    main()
