import string, re
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise
from parserUtils import *
from ResultType import *

_g_metaRe = re.compile(r"\<\!meta.*?\>", re.I + re.S)


def parseCurrencyData(htmlText):
    global _g_metaRe
    htmlText = _g_metaRe.sub("", htmlText)
    soup = BeautifulSoup()
    soup.feed(htmlText)
    tables = soup("table", {"cellpadding": "2", "cellspacing": "0", "border": "0", "width": "468"})
    assert 1 == len(tables)
    rows = tables[0].fetch("tr", {"bgcolor": "#FFFFFF"})
    currencies = dict()
    for row in rows:
        fonts = row.fetch("font")
        currencies[str(fonts[2].contents[0])] = float(str(fonts[3].contents[0]))
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
