from Retrieve import retrieveHttpResponseWithRedirectionHandleException
from Retrieve import retrieveHttpResponseHandleExceptionRetry

from parserUtils import *
from ResultType import *
from arsutils import log, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC
from parserErrorLogger import logParsingFailure
import urllib
import dreams

## retrieve

def _retrieve_dreammoods(keyword):
    url = "http://dreammoods.com/cgibin/searchcsv.pl?search=%s&method=exact&header=symbol"
    url = url % urllib.quote(keyword)
    htmlText = retrieveHttpResponseWithRedirectionHandleException(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = dreams.parseDream(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("Get-Dream", keyword, htmlText, url)
    return res, data    

def _retrieve_wordiq(keyword):
    url = "http://www.wordiq.com/dream/%s"
    url = url % urllib.quote(keyword)
    htmlText = retrieveHttpResponseWithRedirectionHandleException(url)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    res, data = dreams.parseDream2(htmlText)
    if res == UNKNOWN_FORMAT:
        logParsingFailure("Get-Dream", keyword, htmlText, url)
    return res, data    

_g_retrieve_dream = [
    _retrieve_wordiq,
    _retrieve_dreammoods
]

def retrieveDream(keyword):
    global _g_retrieve_dream
    for func in _g_retrieve_dream:
        try:
            res, data = func(keyword)
            if res not in [RETRIEVE_FAILED, UNKNOWN_FORMAT]:
                return res, data
        except Exception, ex:
            pass
    return (RETRIEVE_FAILED, None)

