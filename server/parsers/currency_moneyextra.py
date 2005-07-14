import string, re
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise
from parserUtils import *
from ResultType import *

_g_imgRe = re.compile(r"/images/flags/(\w\w\w)_26x17.gif", re.I + re.S)



def parseCurrencyData(htmlText):
    global _g_imgRe
    soup = BeautifulSoup()
    soup.feed(htmlText)
    # <table width="60%" border="0" cellpadding="3" summary="Displays latest tourist currency rates">
    table = soup.first("table", {"border": "0", "width": "60%", "cellpadding": "3", "summary": "Displays latest tourist currency rates"})
    assert table is not None
    tbody = table.first("tbody")
    assert tbody is not None
    rows = tbody.fetch("tr")
    currencies = dict()
    for row in rows:
        cells = row.fetch("td")
        img = cells[0].fetch("img")[0]
        match = _g_imgRe.match(img["src"])
        if match is None:
            continue
        abbrev = match.group(1)
        rate = float(str(cells[2].contents[0]).strip().split()[0])
        currencies[abbrev] = rate
    usdRate = currencies["USD"]
    for key in currencies.iterkeys():
        currencies[key] = currencies[key] / usdRate
    assert 1 == currencies["USD"]
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
