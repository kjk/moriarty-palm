import string, re
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise
from parserUtils import *
from ResultType import *

_g_regionsToISO = {
    "Australia": "AUD",
    "Brazil": "BRL",
    "Canada": "CAD",
    "China, P.R.": "CNY",
    "Denmark": "DKK",
    "European Monetary Union": "EUR",
    "Hong Kong": "HKD",
    "India": "INR",
    "Japan": "JPY",
    "Malaysia": "MYR",
    "Mexico": "MXN",
    "New Zealand": "NZD",
    "Norway": "NOK",
    "Singapore": "SGD",
    "South Africa": "ZAR",
    "South Korea": "KPW",
    "Sri Lanka": "LKR",
    "Sweden": "SEK",
    "Switzerland": "CHF",
    "Taiwan": "TWD",
    "Thailand": "THB",
    "United Kingdom": "GBP",
    "Venezuela": "VEB",
    "Israel": "ILS"
}

def parseCurrencyData(htmlText):
    global _g_regionsToISO
    soup = BeautifulSoup()
    soup.feed(htmlText)
    tables = soup("table", {"border": "0", "width": "368", "cellpadding": "0", "cellspacing": "0"})
    rows = tables[0].fetch("tr")
    currencies = dict()
    isFirstRow = True
    for row in rows:
        cells = row.fetch("td")
        if 4 != len(cells):
            continue
        if isFirstRow:
            isFirstRow = False
            continue
        region = retrieveContents(cells[1].fetch("div")[0].contents[0])
        try:
            rate = float(retrieveContents(cells[3].fetch("div")[0].contents[0]))
            if "*" == retrieveContents(cells[0].contents[0]):
                rate = 1/rate
            abbrev = _g_regionsToISO[region]
            currencies[abbrev] = rate
        except ValueError:
            pass
    return (RESULTS_DATA, currencies)

def main():
#     import sys
#     fileName = sys.argv[1]
#     f = open(fileName, "r")
#     try:
#         htmlText = f.read()
#         print parseCurrencyData(htmlText)
#     finally:
#         f.close()
    import currency_retrieve
    print currency_retrieve._retrieve_ny_frb()


if __name__ == "__main__":
    main()
