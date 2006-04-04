import gzip, urllib, urllib2, random, time, socket, cookielib, StringIO, os, os.path, sys, cPickle
from httplib import HTTPConnection, HTTPException
from ResultType import *
from arsutils import log, exceptionAsStr, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC, Timer

# Functions related to retrieving data from other servers

#code from http://diveintopython.org/http_web_services/redirects.html
''' This is simle version of redirection handling
    but I dont know how to return status and reason
'''
class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.reason = msg
        result.status = code
        return result
    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        result.reason = msg
        return result

def getHttpUsingUrllib2(url, headers=None):
    host = getHostFromUrl(url)
    status, reason, responseText=200, None, None
    if None != host:
        request = urllib2.Request(url)
    else:
        # TODO: implement using host
        request = urllib2.Request(url)
    if headers != None:
        # headers is dictionary
        for name in headers:
            request.add_header(name, headers[name])
    opener = urllib2.build_opener(SmartRedirectHandler())
    result = opener.open(request)
    return status, reason, result.read()

def retrieveHttpResponseWithRedirection(url, headers=None):
    return getHttpUsingUrllib2(url, headers)

# this function extracts host from a url e.g.
# http://foo.com/blah.html gives foo.com
# assumes that url must start with "http://" but url can be malformed (no / in url)
# in which case it returns None instead of extracting host
def getHostFromUrl(url):
    assert 0 == url.find("http://")
    hostAndRest = url[7:]
    hostAndRestParts = hostAndRest.split("/")
    if len(hostAndRestParts)<1:
        return None
    host = hostAndRestParts[0]
    return host

# @note assumption that url is not encoded is unrealistic; url must be encoded
# @exception httplib.HTTPException is thrown in case of connection errors
# @return tuple (status, reason, responseText)
def retrieveHttpResponse(url):
    host = getHostFromUrl(url)
    status, reason, responseText=None, None, None
    if None != host:
        conn = HTTPConnection(host)
    else:
        conn = HTTPConnection()
    conn.connect()
    try:
        conn.putrequest("GET", url)
        conn.putheader("Accept", "image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, */*")
        conn.putheader("Host", host)
        conn.putheader("User-Agent", "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322)")
        conn.putheader("Connection", "Keep-Alive")
        conn.endheaders()
        resp = conn.getresponse()
        status, reason, responseText=resp.status, resp.reason, resp.read()
    finally:
        conn.close()
    return status, reason, responseText

# get HTTP data from a given url. Return either HTTP data or None if there
# was an error during processing
def retrieveHttpResponseHandleException(url):
    #log(SEV_LOW, "retrieveHttpResponseHandleException: %s\n" % url)
    try:
        status, reason, responseText = retrieveHttpResponse(url)
    except Exception, ex:
        txt = exceptionAsStr(ex)
        log(SEV_EXC, "failed to retrieve data for '%s'\nreason:%s\n" % (url, txt))
        return None
    if 200 != status:
        log(SEV_EXC, "failed to retrieve data for '%s'\nreason: got %d\n" % (url, status))
        return None

    return responseText

# get HTTP data from a given url. Return either HTTP data or None if there
# was an error during processing
# If there was a socket error (usually 'connection refused' or 'connection reset by peer'
# or 'connection timedout'), retry the request retryCount times
def retrieveHttpResponseHandleExceptionRetry(url,retryCount=3):
    while True:
        try:
            #log(SEV_LOW, "retrieveHttpResponseHandleExceptionRetry: %s\n" % url)
            status, reason, responseText = retrieveHttpResponse(url)
        except socket.error, (err,txt):
            retryCount -= 1
            #txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to retrieve data for '%s'\nsocket error:%d, %s\n" % (url, err, txt))
            if retryCount < 0:
                log(SEV_EXC, "failed to retrieve data for '%s'\ntoo many socket errors\n" % (url))
                return None
            continue
        # TODO: add handling of urllib2.URLError?
        #   File "C:\Python22\lib\urllib2.py", line 809, in do_open
        # raise URLError(err)
        # URLError: <urlopen error (10060, 'Operation timed out')>
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to retrieve data for '%s'\nreason:%s\n" % (url, txt))
            return None
        if 200 != status:
            log(SEV_HI, "failed to retrieve data for '%s'\nreason: got %d\n" % (url, status))
            return None
        break
    return responseText

# get HTTP data from a given url. Return either HTTP data or None if there
# was an error during processing
def retrieveHttpResponseHandleException(url):
    #log(SEV_LOW, "retrieveHttpResponseHandleException: %s\n" % url)
    try:
        status, reason, responseText = retrieveHttpResponse(url)
    except Exception, ex:
        txt = exceptionAsStr(ex)
        log(SEV_EXC, "failed to retrieve data for '%s'\nreason:%s\n" % (url, txt))
        return None
    if 200 != status:
        log(SEV_HI, "failed to retrieve data for '%s'\nreason: got %d\n" % (url, status))
        return None
    return responseText


def retrieveHttpResponseWithRedirectionHandleException(url, headers=None):
    #log(SEV_LOW, "retrieveHttpResponseWithRedirectionHandleException: %s\n" % url)
    try:
        status, reason, responseText = retrieveHttpResponseWithRedirection(url, headers)
    except Exception, ex:
        txt = exceptionAsStr(ex)
        log(SEV_EXC, "failed to retrieve data for '%s'\nreason:%s\n" % (url, txt))
        return None
    # TODO: is it really possible to get 301/302 from there?
    if not status in (200,301,302):
        log(SEV_HI, "failed to retrieve data for '%s'\nreason: got %d\n" % (url, status))
        return None
    return responseText

# get HTTP data from a given url, handling redirection. Return either HTTP data or None if there
# was an error during processing
# If there was a socket error (usually 'connection refused' or 'connection reset by peer'
# or 'connection timedout'), retry the request retryCount times
def retrieveHttpResponseWithRedirectHandleExceptionRetry(url,retryCount=3):
    while True:
        try:
            #log(SEV_LOW, "retrieveHttpResponseWithRedirectHandleExceptionRetry: %s\n" % url)
            status, reason, responseText = retrieveHttpResponseWithRedirection(url)
        except socket.error, (err,txt):
            retryCount -= 1
            #txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to retrieve data for '%s'\nsocket error:%d, %s\n" % (url, err, txt))
            if retryCount < 0:
                log(SEV_EXC, "failed to retrieve data for '%s'\ntoo many socket errors\n" % (url))
                return None
            continue
        # TODO: add handling of urllib2.URLError?
        #   File "C:\Python22\lib\urllib2.py", line 809, in do_open
        # raise URLError(err)
        # URLError: <urlopen error (10060, 'Operation timed out')>
        except Exception, ex:
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to retrieve data for '%s'\nreason:%s\n" % (url, txt))
            return None
        if 200 != status:
            log(SEV_HI, "failed to retrieve data for '%s'\nreason: got %d\n" % (url, status))
            return None
        break
    return responseText

# those headers are supposed to mimic FireFox
user_agent_hdr = "User-Agent"
user_agent_val = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041107 Firefox/1.0"

accept_hdr = "Accept"
accept_val = "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5"

accept_lang_hdr = "Accept-Language"
accept_lang_val = "en-us,en;q=0.5"

# don't give that, not sure if python handles it
# Accept-Encoding: gzip,deflate

accept_encoding_hdr = "Accept-encoding"
accept_encoding_val = "gzip"

content_encoding_hdr = "Content-Encoding"

accept_charset_hdr = "Accept-Charset"
accept_charset_val = "ISO-8859-1,utf-8;q=0.7,*;q=0.7"

keep_alive_hdr = "Keep-Alive"
keep_alive_val = "300"

connection_hdr = "Connection"
connection_val = "keep-alive"

referer_hdr = "Referer"

location_hdr = "Location"

# a class to trick urllib2 to not handle redirects
class HTTPRedirectHandlerNoRedirect(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        #print "******** HTTPRedirectHandlerNoRedirect() called"
        pass

def _getHttpHelper(url, postData, handleRedirect, dbgLevel, referer, cookieJar):
    # print "_getHttpHelper(%s)" % url
    timer = Timer(fStart=True)
    req = urllib2.Request(url)
    req.add_header(user_agent_hdr, user_agent_val)
    req.add_header(accept_hdr, accept_val)
    req.add_header(accept_lang_hdr, accept_lang_val)
    req.add_header(accept_charset_hdr, accept_charset_val)
    req.add_header(keep_alive_hdr, keep_alive_val)
    req.add_header(connection_hdr, connection_val)
    if None != referer:
        req.add_header(referer_hdr, referer)

    if None != postData:
        req.add_data(urllib.urlencode(postData))

    httpHandler = urllib2.HTTPHandler(debuglevel=dbgLevel)
    httpsHandler = urllib2.HTTPSHandler(debuglevel=dbgLevel)
    if cookieJar is None:
        cookieJar = cookielib.CookieJar()

    cookieHandler = urllib2.HTTPCookieProcessor(cookieJar)

    if handleRedirect:
        opener = urllib2.build_opener(cookieHandler, httpHandler, httpsHandler)
    else:
        noRedirectHandler = HTTPRedirectHandlerNoRedirect()
        opener = urllib2.build_opener(cookieHandler, httpHandler, httpsHandler, noRedirectHandler)

    url_handle = opener.open(req)
    if not url_handle:
        # print "_getHttpHelper() - no url_handle"
        return None

    headers = url_handle.info()

    # TODO: is it always present? What happens if it's not?
    encoding = url_handle.headers.get(content_encoding_hdr)

    if "gzip" == encoding:
        htmlCompressed = url_handle.read()
        compressedStream = StringIO.StringIO(htmlCompressed)
        gzipper = gzip.GzipFile(fileobj=compressedStream)
        htmlTxt = gzipper.read()
    else:
        htmlTxt = url_handle.read()

    url_handle.close()
    timer.stop()
    duration = timer.getDuration()
    # TODO: log somewhere how long retrieving this url took
    # print "_getHttpHelper() htmlTxt size=%d" % len(htmlTxt)
    return htmlTxt

def _getHttpHandleExceptionRetry(url, postData, handleRedirect, dbgLevel, referer, retryCount, cookieJar):
    assert retryCount > 0
    while retryCount > 0:
        try:
            htmlTxt = _getHttpHelper(url, postData, handleRedirect, dbgLevel, referer, cookieJar)
            return htmlTxt
        except socket.error, (err,txt):
            txt = exceptionAsStr(ex)
            log(SEV_EXC, "failed to retrieve data for '%s'\nsocket error:%d, %s\n" % (url, err, txt))
            retryCount -= 1
    return None

# do an http request to retrieve html data for url. By default we use GET request
# if postData (a dictionary) is given we do POST request
# set handleRedirect to False to disable automatic handling of HTTP redirect (302 etc.)
# set dbgLevel to 1 to have HTTP request and response headers dumped to stdio
# to set HTTP header referer, use referer
# TODO: add support for cookies
def getHttp(url, postData = None, handleRedirect=True, dbgLevel=0, referer=None, retryCount=1, handleException=True, cookieJar = None):
    htmlTxt = None
    if handleException:
        assert retryCount > 0
        htmlTxt = _getHttpHandleExceptionRetry(url, postData, handleRedirect, dbgLevel, referer, retryCount, cookieJar)
    else:
        htmlTxt = _getHttpHelper(url, postData, handleRedirect, dbgLevel, referer, cookieJar)
    return htmlTxt

# recursive function that makes given path (if exists exit)
def makePathIfNeeded(path):
    assert path != None
    if 0 == os.access(path, os.F_OK):
        (head,tail) = os.path.split(path)
        makePathIfNeeded(head)
        os.mkdir(path)

# like getHttp but caches urls on disk. Mostly for testing
g_cacheDir = "c:\\kjk\\infoman\\cache"
# maps between url and file name with downloaded html
g_cacheDict = {}

DATA_FILE_NAME = os.path.join(g_cacheDir, "url_cache_data.dat")

g_urlCacheLoaded = False
def loadUrlCache():
    global g_urlCacheLoaded, DATA_FILE_NAME, g_cacheDict, g_cacheDir
    if g_urlCacheLoaded:
        return
    makePathIfNeeded(g_cacheDir)
    # create directory if doesn't exist
    try:
        fo = open(DATA_FILE_NAME, "rb")
    except IOError:
        # it's ok to not have the file
        print "didn't find file %s with data" % DATA_FILE_NAME
        g_urlCacheLoaded = True
        return
    try:
        g_cacheDict = cPickle.load(fo)
    except:
        fo.close()
        removeRetryCount = 0
        while removeRetryCount < 3:
            try:
                os.remove(filePath)
                break
            except:
                time.sleep(1) # try to sleep to make the time for the file not be used anymore
                print "exception: n  %s, n  %s, n  %s n  when trying to remove file %s" % (sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2], filePath)
            removeRetryCount += 1
        return
    fo.close()
    g_urlCacheLoaded = True

def saveUrlCache():
    global DATA_FILE_NAME, g_cacheDict
    fo = open(DATA_FILE_NAME, "wb")
    cPickle.dump(g_cacheDict, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    fo.close()    

def getHttpCached(url, postData = None, handleRedirect=True, dbgLevel=0, referer=None, retryCount=1, handleException=True, cookieJar = None):
    global g_cacheDict, g_cacheDir
    loadUrlCache()
    if g_cacheDict.has_key(url):
        print "found url %s in cache" % url
        fileName = g_cacheDict[url]
        fo = open(fileName, "rb")
        htmlTxt = fo.read()
        fo.close()
        return htmlTxt
    htmlTxt = getHttp(url, postData, handleRedirect, dbgLevel, referer, retryCount, handleException, cookieJar)
    if None == htmlTxt:
        return None
    fileName = os.path.join(g_cacheDir, "%03d.html" % len(g_cacheDict))
    fo = open(fileName, "wb")
    fo.write(htmlTxt)
    fo.close()
    g_cacheDict[url] = fileName
    print "added url %s to cache as file %s" % (url, fileName)
    saveUrlCache()
    return htmlTxt
