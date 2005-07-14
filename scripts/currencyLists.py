# Copyright: Krzysztof Kowalczyk
# Owner: Marek Senderski
#
# Purpose:
#  Extraction of currency tables needed on server and client side

import sys
import string
import re

try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise

def usageAndExit():
    print ""
    print "Usage: this.py countriesFile currencyAbbrevFile listType"
    print "countriesFile: page from http://www.fms.treas.gov/intn.html"
    print "abbrevFile: page from http://www.xe.com/iso4217.htm (with table tag marked with attrib \"summary\":\"countries\")"
    print "listType: server - server side list, client - client side list"
    sys.exit(0)

def main():
    # now we should only have file name
    if 4 != len(sys.argv) :
        usageAndExit()
    server = True
    if "client" == sys.argv[3]:
        server = False
    elif "server" != sys.argv[3]:
        usageAndExit()

    fileName = sys.argv[1]
    fileName2 = sys.argv[2]
    fo1 = open(fileName,"rb")
    htmlTxt1 = fo1.read()

    soup = BeautifulSoup()
    soup.feed(htmlTxt1)
    findTable = soup.fetch("table",{"border":"1", "cellpadding":"5", "align":"left", "summary":"Table includes foreign currency exchange rate to the US dollar"})
    #dictionary to store touples (name, countries of currency)
    abbrevToNameAndCountry = {}
    
    itemTable = findTable[0]
    findTableTR = itemTable.fetch("tr")
    for itemTR in findTableTR:
        findTD = itemTR.fetch("td")        
        if len(findTD) == 0:
           continue
        currencyAbbrev = ""
        currencyCountry = ""
        currencyName = ""

        countryMatch = str(findTD[1].contents[0])
        r1 = re.compile(r'[^-]*')
        country = r1.search(countryMatch).group(0).strip()
        if "1/" == str(findTD[0].contents[0]) and server:
            print "\"%s\":\"EUR\"," % (country)
        else:
            fo2 = open(fileName2,"rb")
            htmlTxt2 = fo2.read()
            
            soup2 = BeautifulSoup()
            soup2.feed(htmlTxt2)
            
            findTable2 = soup2.fetch("table",{"cellpadding":"1", "cellspacing":"0", "border":"0","summary":"countries"})
            itemTable2 = findTable2[0];
            findTableTR2 = itemTable2.fetch("tr")
            found = False
            for itemTR2 in findTableTR2:
                findTD2 = itemTR2.fetch("td") 
                abbrev = str(findTD2[0].first("tt").contents[0])
                countryCurrency = str(findTD2[1].first("tt").contents[0]).upper()
                #print countryCurrency, " ", abbrev
                if countryCurrency.find(country) != -1:
                    if server:
                        print "\"%s\":\"%s\"," % (country, abbrev)
                        found = True
                        break
                    else:
                        countryCurrency = str(findTD2[1].first("tt").contents[0])
                        r1 = re.compile(r'[^,]*')
                        gr = r1.search(countryCurrency)
                        country = gr.group(0).strip()
                        currency = countryCurrency[len(gr.group(0))+1:].strip()
                        #print "\"%s\":\"%s\"," % (country, currency)
                        found = True
                        if not abbrevToNameAndCountry.has_key(abbrev):
                            abbrevToNameAndCountry[abbrev] = [currency, country]
                        else:
                            countries = abbrevToNameAndCountry[abbrev][1] + ", " + country
                            abbrevToNameAndCountry[abbrev] = (abbrevToNameAndCountry[abbrev][0], countries)
            if not found and server:
                print "\"%s\":\"NOTFOUND\"," % (country)
    if not server:
        coutriesMaxLen = 0
        currencyMaxLen = 0
        keys = abbrevToNameAndCountry.keys();
        keys.sort()
        for item in keys:
            if len(abbrevToNameAndCountry[item][1]) > coutriesMaxLen:
                coutriesMaxLen = len(abbrevToNameAndCountry[item][1])
            if len(abbrevToNameAndCountry[item][0]) > currencyMaxLen:
                currencyMaxLen = len(abbrevToNameAndCountry[item][0])

            print "{_T(\"%s\"), _T(\"%s\"), _T(\"%s\") }," % (item, abbrevToNameAndCountry[item][0], abbrevToNameAndCountry[item][1])
        print currencyMaxLen
        print coutriesMaxLen
if __name__=="__main__":
    main()
