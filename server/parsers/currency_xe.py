import string, re
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise
from parserUtils import *
from ResultType import *

_g_xercRe = re.compile(r"\<\!XERC.*?\>", re.I + re.S)

def parseCurrencyData(htmlText):
    global _g_xercRe
    htmlText = _g_xercRe.sub("", htmlText)
    htmlText = htmlText.replace("!BORDERCOLOR", "BORDERCOLOR")
    soup = BeautifulSoup()
    soup.feed(htmlText)
    tables = soup("table", {"class": "ictab"})
    assert 1 == len(tables)
    rows = tables[0].fetch("tr", {"valign": "top"})
    currencies = dict()
    for row in rows:
        cells = row.fetch("td")
        if 4 != len(cells):
            continue
        currencies[str(cells[0].contents[0]).strip()] = float(str(cells[3].contents[0]).strip().replace(",", ""))
    return (RESULTS_DATA, currencies)

def main():
    import sys
    fileName = "currency_xe.html"
    try:
        fileName = sys.argv[1]
    except:
        pass
    f = open(fileName, "r")
    try:
        htmlText = f.read()
        print parseCurrencyData(htmlText)
    finally:
        f.close()

if __name__ == "__main__":
    main()

