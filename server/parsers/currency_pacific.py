import string, re
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise
from parserUtils import *
from ResultType import *

_g_turkishLirasAbbrev = "TRL"

def parseCurrencyData(htmlText):
    global _g_turkishLirasAbbrev
    soup = BeautifulSoup()
    soup.feed(htmlText)
    tables = soup("table", {"border": "0", "width": "640", "cellpadding": "0", "cellspacing": "0"})
    assert 5 == len(tables)
    rows = tables[2].fetch("tr")
    currencies = dict()
    isFirstRow = True
    for row in rows:
        if isFirstRow:
            isFirstRow = False
            continue
        fonts = row.fetch("font")
        if 8 != len(fonts):
            continue
        for i in range(2):
            abbrev = str(fonts[i*4].fetch("tt")[0].contents[0]).strip()
            rate = float(str(fonts[i*4 + 3].contents[0]).replace("&nbsp;", " ").strip())
            if _g_turkishLirasAbbrev == abbrev:
                rate *= 1000000
            currencies[abbrev] = rate
    return (RESULTS_DATA, currencies)

def main():
    import sys
    fileName = sys.argv[1]
    f = open(fileName, "r")
    try:
        htmlText = f.read()
        print parseCurrencyData(htmlText)
    finally:
        f.close()

if __name__ == "__main__":
    main()

