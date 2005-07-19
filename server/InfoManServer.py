# -*- coding: iso-8859-1 -*-

import sys, os, thread, string, re, random, time, pickle, cPickle
import MySQLdb, _mysql_exceptions
import urllib, urllib2, cookielib
from threading import Lock

import arsutils, multiUserSupport, ServerErrors, Fields

import db, movies, epicurious, weather, m411, boxoffice, dreams, jokes
import ourAmazon, stocks, gasprices, horoscopes, listsofbests, lyrics
import dreams_retrieve, netflix, currency_retrieve, yp_retrieve, dictionary
import encyclopedia, quotes, flights, ebooks, tvlistings_retrieve
import eBay

import InfoManCrypto

from parserErrorLogger import *

from arsutils import exceptionAsStr, fDetectRemoveCmdFlag, log, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC
from ResultType import *
from Retrieve import *
from parserUtils import *

from ThreadedServer import *

try:
    import iPediaServer
except:
    print "Unable to import iPediaServer.py"


g_fDisableRegistrationCheck     = False # for testing only

# 150 might seem like a large value, but I believe we need the user to really
# get addicted to the program. Standard trial period for software is 30 days
# which is only 5 requests per day. If a user doesn't use that many, he probably
# doesn't need InfoMan. If he does use InfoMan often, he'll quickly hit the
# limit anyway (some modules e.g. amazon consume requests quite quickly)
g_unregisteredLookupsLimit      = 150
g_unregisteredLookupsDailyLimit = 2

g_fDumpPayload = False

PROTOCOL_VERSION = "1"

# testing only
g_fForceUpgrade = False

def createDatabaseConnection():
    #log(SEV_LOW,"creating management connection\n")
    return MySQLdb.Connect(host=db.DB_HOST, user=db.getDbUser(), passwd=db.DB_PWD, db=db.getDbName())

lineSeparator =     "\n"

def buildField(name,value=None):
    if value:
        field = "%s: %s%s" % (name, value, lineSeparator)
    else:
        field = "%s:%s" % (name, lineSeparator)
    return field

# A format of a request accepted by a server is very strict:
# validClientRequest = validClientField ":" fieldValue? "\n"
# fieldValue = " " string
# validClientField = "Get-Cookie" | "Protocol-Version" etc.
# In other words:
#  - if request has no parameters, then it must be a requestField immediately
#    followed by a colon (":") and a newline ("\n")
#  - if request has parameters, then it must be a requestField immediately
#    followed by a colon (":"), space (" "), arbitrary string which is an argument and newline ("\n")
#
# This function parses the request line from the server and returns a tuple
# (field,value). If request has no parameters, value is None
# If there was an error parsing the line (it doesn't correspond to our strict
# format), field is None
def parseRequestLine(line):
    parts = line.split(":", 1)
    if 1==len(parts):
        # there was no ":" so this is invalid request
        return (None,None)
    field = parts[0]
    value = parts[1]
    if 0==len(value):
        # the second part is an empty line which means that this is a request
        # without an argument
        return (field, None)
    # this is a request with an argument, so it should begin with a space
    if ' '!=value[0]:
        # it doesn't begin with a space, so invalid
        return (None,None)
    value = value[1:]
    return (field,value)

# given a device info as a string in our encoded form, return a dictionary
# whose keys are tags (e.g. "PL", "SN", "PN") and value is a tuple:
# (value as decoded hex string, value as original hex-encoded string)
# Return None if device info is not in a (syntactically) correct format.
# Here we don't check if tags are valid (known), just the syntax
def decodeDeviceInfo(deviceInfo):
    result = {}
    parts = deviceInfo.split(":")
    for part in parts:
        # each part has to be in the format: 2-letter tag followed by
        # hex-encoded value of that tag
        if len(part)<4:
            # 4 characters are: 2 for the tag, 2 for at least one byte of value
            return None
        tag = part[0:2]
        tagValueHex = part[2:]
        if len(tagValueHex) % 2 != 0:
            return None
        rest = tagValueHex
        tagValueDecoded = ""
        while len(rest)>0:
            curByteHex = rest[0:2]
            rest = rest[2:]
            try:
                curByte = int(curByteHex,16)
                tagValueDecoded += chr(curByte)
            except:
                return False
        result[tag] = (tagValueDecoded,tagValueHex)
    return result

# TODO: add Smartphone/Pocket PC tags
validTags = ["PL", "PN", "SN", "HN", "OC", "OD", "HS", "IM"]
def fValidDeviceInfo(deviceInfo):
    deviceInfoDecoded = decodeDeviceInfo(deviceInfo)
    if None == deviceInfoDecoded:
        log(SEV_HI,"couldn't decode device info '%s'\n" % deviceInfo)
        return False
    tagsPresent = deviceInfoDecoded.keys()
    for tag in tagsPresent:
        if tag not in validTags:
            log(SEV_HI,"tag '%s' is not valid\n" % tag)
            return False
    # "PL" (Platform) is a required tag - must be sent by all clients
    if "PL" not in tagsPresent:
        return False
    return True

# If we know for sure that device id was unique, we issue previously assigned
# cookie. This prevents using program indefinitely by just reinstalling it
# after a limit for unregistered version has been reached.
# Unique tags are:
#   PN (phone number)
#   SN (serial number)
#   HN (handspring serial number)
#   IM (Treo IMEI number)
def fDeviceInfoUnique(deviceInfo):
    deviceInfoDecoded = decodeDeviceInfo(deviceInfo)
    if None == deviceInfoDecoded:
        return False
    tags = deviceInfoDecoded.keys()
    if ("PN" in tags) or ("SN" in tags) or ("HN" in tags) or ("IM" in tags):
        return True
    return False

def genNewCookie():
    randMax=2**16-1
    cookie = ""
    for i in range(8):
        val = random.randint(0, randMax)
        hexVal = hex(val)[2:].zfill(4)
        cookie += hexVal
    assert 32 == len(cookie)
    return cookie

def getUniqueCookie(cursor):
    while True:
        cookie = genNewCookie()
        cursor.execute("""SELECT user_id FROM users WHERE cookie='%s'""" % cookie)
        row = cursor.fetchone()
        if not row:
            break
    return cookie

# amazon browse cache (thread safe)
class AmazonBrowseCache:
    AMAZON_CACHE_DIR = os.path.join(multiUserSupport.getServerStorageDir(), "amazon-cache")
    NO_DATA = 0
    DATA = 1

    def __init__(self):
        self._lock = Lock()

    def buildFileName(self, searchIndex, node):
        file = searchIndex + "_" + node
        fileName = os.path.join(self.AMAZON_CACHE_DIR,file)
        return fileName

    # return (status, resultType, resultBody)
    def getBrowse(self, searchIndex, node):
        status = self.NO_DATA
        resultType = NO_RESULTS
        resultBody = None
        fileName = self.buildFileName(searchIndex, node)
        if os.path.exists(fileName):
            self._lock.acquire()
            fileText = None
            try:
                fo = open(fileName, "rb")
                fileText = fo.read()
                fo.close()
            finally:
                self._lock.release()
            if None != fileText:
                if fileText == "NO_RESULTS" or fileText == "ONLY_SEARCH":
                    status = self.DATA
                else:
                    status = self.DATA
                    resultBody = fileText
                    resultType = AMAZON_BROWSE_LIST
        return status, resultType, resultBody

    def setBrowse(self, searchIndex, node, resultType, resultBody):
        makePathIfNeeded(self.AMAZON_CACHE_DIR)
        fileName = self.buildFileName(searchIndex, node)
        fileText = resultBody
        if resultType != AMAZON_BROWSE_LIST:
            if resultType != AMAZON_SEARCH_LIST:
                fileText = "NO_RESULTS"
            else:
                fileText = "ONLY_SEARCH"
        self._lock.acquire()
        try:
            fo = open(fileName, "wb")
            fo.write(fileText)
            fo.close()
        finally:
            self._lock.release()

g_amazonBrowseCache = AmazonBrowseCache()

# listsOfBests cache (thread safe)
class ListsOfBestsCache:
    LISTS_FILE = "lobLists.pic"
    LIST_FILE = "lobList.pic"

    def __init__(self, cacheToLevel):
        # on cache start load cache to memory...
        ##self._lock = Lock()
        self._listsListData = None
        self._itemsListData = None
        # 1st listsLists
        if cacheToLevel > 0:
            try:
                f = open(self.LISTS_FILE,"rb")
                self._listsListData = pickle.load(f)
                f.close()
            except:
                print "Lists of bests can't cache lists of lists"
        # 2nd itemsLists
        if cacheToLevel > 1:
            try:
                f = open(self.LIST_FILE,"rb")
                self._itemsListData = pickle.load(f)
                f.close()
            except:
                print "Lists of bests can't cache lists"

    def getListsList(self, fieldValue):
        if None == self._listsListData or not self._listsListData.has_key(fieldValue):
            if None == self._itemsListData or not self._itemsListData.has_key(fieldValue):
                return None
            else:
                return self._itemsListData[fieldValue]
        else:
            return self._listsListData[fieldValue]

g_listsOfBestsCache = None

# URLs for all modules
# Weather module
#weatherServerUrl           = "http://www.weather.com/outlook/travel/local/%s"
#weatherServerUrl            = "http://www.w3.weather.com/outlook/travel/local/%s"
weatherServerUrlFirstDay    = "http://weather.yahoo.com/forecast/%s.html"
weatherServerUrl            = "http://www.weather.com/weather/mpdwcr/tenday?locid=%s"
weatherMultiselectServerUrl = "http://www.weather.com/search/enhanced?where=%s"

currencyServerUrl = "http://www.evocash.com/index.cfm?fuseaction=dsp_exchangerates_all"

### Movies module
yahooMoviesUrl = "http://movies.yahoo.com/showtimes/showtimes.html?z=%s&r=sim&nt=30"

### Recipes module
epicuriousRServerUrl = "http://www.epicurious.com%s"
epicuriousSServerUrl = "http://www.epicurious.com/recipes/find/results?search=%s"

## stocks module
stocksListUrl = "http://finance.yahoo.com/q/cq?d=v1&s=%s"
stockUrl      = "http://finance.yahoo.com%s"

g_hourInSeconds = float(60*60)

# a switch mostly for testing e.g. when we want to compare speed of cached
# vs. non-cached version
# usually should be set to True
g_fCacheBoxOffice = True

g_boxOfficeDataCached = None
g_boxOfficeDataWhenCached = None

# refresh box office cache every hour. it's still a bit of overkill (it only
# changes every week) but for now it's good enough.
g_boxOfficeCacheExpiration = g_hourInSeconds

# amazon module is disabled (when key is invalid)
g_fDisableAmazonModule = False

# when switched to True (by server -testCross flag) ignore client version
g_fTestCrossModules = False

# return True if cache for box office data has expired
def boxOfficeCacheExpired():
    global g_fCacheBoxOffice, g_boxOfficeDataWhenCached, g_boxOfficeCacheExpiration
    if not g_fCacheBoxOffice:
        return True
    curTime = time.time()
    secondsSinceCached = curTime - g_boxOfficeDataWhenCached
    if secondsSinceCached > g_boxOfficeCacheExpiration:
        return True
    return False

def assertParseFailed(resultType,resultBody,functionName=None):
    assert (UNKNOWN_FORMAT == resultType) or (RETRIEVE_FAILED == resultType)
    assert None==resultBody
    if None != functionName:
        log(SEV_LOW, "failed to parse html data in '%s'\n" % functionName)

# given a string containing $fieldCount comma-separated values in $txt, return
# an array of those values (after stripping them).
# $txt must have exactly $fieldCount values
def extractCommaSeparatedFields(txt,fieldCount):
    fields = txt.split(",")
    assert fieldCount == len(fields)
    result = [f.strip() for f in fields]
    return result

# those are the client types that we have clients for. Latest client version
# is stored in client-versions.txt
CLIENT_NAMES = ["Palm"] # "PocketPC", "Smartphone" <- those could be in the future
LATEST_CLIENT_VERSIONS_FILE = "client-versions.txt"

g_latestClientVersion = {}
def addClientVersion(clientName, clientVersion):
    global g_latestClientVersion
    g_latestClientVersion[clientName] = clientVersion

def getClientVersion(clientName):
    global g_latestClientVersion
    if not g_latestClientVersion.has_key(clientName):
        return None
    return g_latestClientVersion[clientName]

def readLatestClientVersions():
    print "readLatestClientVersions()"
    fo = open(LATEST_CLIENT_VERSIONS_FILE, "r")
    for line in fo.readlines():
        if len(line) < 1:
            continue
        if '#' == line[0]:
            continue
        (clientName, clientVersion) = line.split(":")
        clientName = clientName.strip()
        clientVersion = clientVersion.strip()
        addClientVersion(clientName, clientVersion)
    fo.close()

class InfoManProtocol(LineReceiver):

    testCookie     = "DEADBEEFDEADBEEFDEADBEEFDEADBEEF"

    testRegCode    = "BEEFDEADBEEFDEADBEEFDEADBEEFDEAD"
    testDeviceInfo = "HS50616C6D204F5320456D756C61746F72:OC70616C6D:OD00000000:PL50616C6D"

    def __init__(self):
        self.delimiter = '\n'

        self.db = None

        # dictionary to keep values of client request fields parsed so far
        self.fields = {}

        self.userId = None
        self.fRegisteredUser = False
        self.response = ""
        self.disabledModules = []
        # those are request fields to be logged for this request. Most
        # of the time it's just one field
        self.requestsToLog = []
        self.afterFinishCallbacks = []
        self.cookieJar = None
        self.tvRetriever = None
        self.clientInfo = None

    # return true if current request has a given field
    def fHasField(self,fieldName):
        assert Fields.fClientField(fieldName)
        if self.fields.has_key(fieldName):
            return True
        return False

    # return value of a given field or None if:
    #  - field was no present
    #  - field had no value (no argument) (so use fHasField() to tell those cases apart)
    def getFieldValue(self,fieldName):
        assert Fields.fClientField(fieldName)
        if self.fHasField(fieldName):
            return self.fields[fieldName]
        return None

    def setFieldValue(self,fieldName,value):
        try:
            assert Fields.fClientField(fieldName)
        except:
            print fieldName
            raise

        # shouldn't be called more than once per value
        assert not self.fHasField(fieldName)
        self.fields[fieldName] = value

    def getManagementDatabase(self):
        if not self.db:
            self.db = createDatabaseConnection()
        return self.db

    def outputField(self, name, value=None):
        field = buildField(name,value)
        # self.transport.write(field)
        self.response += field
        log(SEV_MED,field)

    def outputPayloadField(self, name, payload):
        global g_fDumpPayload
        self.outputField(name, str(len(payload)))
        self.response += payload
        self.response += lineSeparator
#        self.transport.write(payload)
#        self.transport.write(lineSeparator)
        if g_fDumpPayload:
            log(SEV_MED, payload)

    def appendField(self, name, value=None):
        self.outputField(name,value)

    def appendPayloadField(self, name, payload):
         self.outputPayloadField(name,payload)

    # return client's (peer connection's) ip address as a string
    def getClientIp(self):
        try:
            peerInfo = self.transport.getPeer()
            clientIp = peerInfo.host
            return clientIp
        except:
            return ""

    # the last stage of processing a request: if there was an error, append
    # Fields.error to the response, send the response to the client and
    # log the request
    def finish(self, error):
        if None != error:
            self.outputField(Fields.error, str(error))
        self.transport.write(self.response)
        self.transport.loseConnection()

        for callback in self.afterFinishCallbacks:
            callback(self)

        if self.cookieJar is not None:
            self.cookieJar.clear_session_cookies()

        self.storeCookieJar()

        self.logRequests(error)
        if self.db:
            self.db.close()
            self.db = None

        log(SEV_MED, "--------------------------------------------------------------------------------\n")

    # return True if regCode exists in a list of valid registration codes
    def fRegCodeExists(self,regCode):
        cursor = None
        try:
            db = self.getManagementDatabase()
            cursor = db.cursor()
            regCodeEscaped = db.escape_string(regCode)
            cursor.execute("""SELECT reg_code, disabled_p FROM reg_codes WHERE reg_code='%s'""" % regCodeEscaped)
            row = cursor.fetchone()
            cursor.close()
            if row and 'f'==row[1]:
                return True
        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            raise
        return False

    # Log all Get-Cookie requests
    def logGetCookie(self,userId,deviceInfo,cookie):
        cursor=None
        try:
            db = self.getManagementDatabase()
            cursor = db.cursor()
            clientIpEscaped = db.escape_string(self.getClientIp())
            deviceInfoEscaped = db.escape_string(deviceInfo)
            cookieEscaped = db.escape_string(cookie)
            cursor.execute("""INSERT INTO get_cookie_log (user_id, client_ip, log_date, device_info, cookie) VALUES (%d, '%s', now(), '%s', '%s');""" % (userId, clientIpEscaped, deviceInfoEscaped, cookieEscaped))
            cursor.close()
        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            log(SEV_EXC, exceptionAsStr(ex))

    # Log all attempts to verify registration code. We ignore all errors from here
    def logRegCodeToVerify(self,userId,regCode,fRegCodeValid):
        reg_code_valid_p = 'f'
        if fRegCodeValid:
            reg_code_valid_p = 't'

        cursor=None
        try:
            db = self.getManagementDatabase()
            cursor = db.cursor()
            clientIpEscaped = db.escape_string(self.getClientIp())
            regCodeEscaped = db.escape_string(regCode)
            cursor.execute("""INSERT INTO verify_reg_code_log (user_id, client_ip, log_date, reg_code, reg_code_valid_p) VALUES (%d, '%s', now(), '%s', '%s');""" % (userId, clientIpEscaped,regCodeEscaped, reg_code_valid_p))
            cursor.close()
        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            log(SEV_EXC, exceptionAsStr(ex))

    def logRequests(self,error):
        # sometimes we have errors before we can establish userId
        if None == self.userId:
            return

        for request in self.requestsToLog:
            self.logOneRequest(request, self.userId, error)

    # TODO: implement caching of logging requests and make sure that it improves
    # performance
    def logOneRequest(self,request,userId,error):

        cursor = None
        try:
            db = self.getManagementDatabase()
            clientIp = self.getClientIp()
            clientIpEscaped = db.escape_string(clientIp)

            freeRequestEscaped = "f";
            if fFreeRequest(request):
                freeRequestEscaped = "t"

            # TODO: maybe I should log then as separate column requestName and
            # requestValue? Not sure if there's benefit, though

            requestValue = self.getFieldValue(request)
            if None == requestValue:
                request = "%s:" % request
            else:
                request = "%s: %s" % (request, requestValue)
            requestEscaped = db.escape_string(request)

            # TODO: figure out what we need to do for this. Maybe just remove it
            # from logging ?
            resultEscaped = "NULL"

            if None == error:
                errorTxt = "NULL"
            else:
                errorTxt = "'%d'" % error

            sql = "INSERT INTO request_log (user_id,client_ip,log_date,free_p,request,result,error) VALUES (%d,'%s',now(),'%s','%s', %s, %s);" % (userId, clientIpEscaped, freeRequestEscaped, requestEscaped, resultEscaped, errorTxt)
            cursor = db.cursor()
            cursor.execute(sql)
            cursor.close()
        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            log(SEV_HI, arsutils.exceptionAsStr(ex))

    def getCookieJar(self):
        assert self.userId is not None
        db = self.getManagementDatabase()
        cursor = db.cursor()
        self.cookieJar = cookielib.CookieJar()
        try:
            cursor.execute("""SELECT pickled_cookie_jar FROM cookie_jars WHERE user_id = %d""" % self.userId)
            row = cursor.fetchone()
            if row is not None:
                cookies = cPickle.loads(row[0])
                for cookie in cookies:
                    self.cookieJar.set_cookie(cookie)
        finally:
            cursor.close()
        return self.cookieJar

    def storeCookieJar(self):
        if self.cookieJar is None:
            return
        assert self.userId is not None
        cursor = None
        try:
            db = self.getManagementDatabase()
            cursor = db.cursor()
            cookies = list(self.cookieJar)
            data = db.escape_string(cPickle.dumps(cookies))
            onceMore = False
            try:
                cursor.execute("""INSERT INTO cookie_jars (user_id, pickled_cookie_jar) VALUES (%d, '%s')""" % (self.userId, data))
            except:
                onceMore = True
            if onceMore:
                cursor.execute("""UPDATE cookie_jars SET pickled_cookie_jar = '%s' WHERE user_id = %d""" % (data, self.userId))
        except Exception, ex:
            log(SEV_HI, arsutils.exceptionAsStr(ex))
        if cursor is not None:
            cursor.close()

    # Return True if a user identified by userId is over unregistered lookup
    # limits. False if not. Assumes that we don't call this if a user is registered
    def fOverUnregisteredLookupsLimit(self,userId):
        global g_unregisteredLookupsDailyLimit, g_unregisteredLookupsLimit, g_fDisableRegistrationCheck
        assert not self.fRegisteredUser
        cursor = None
        fOverLimit = False
        try:
            db = self.getManagementDatabase()
            cursor = db.cursor()
            query = "SELECT COUNT(*) FROM request_log WHERE user_id=%d AND free_p='f'" % userId
            cursor.execute(query)
            row = cursor.fetchone()
            assert None!=row
            totalLookups = row[0]
            if totalLookups >= g_unregisteredLookupsLimit:
                # TODO: should I setup index on log_date?
                query = "SELECT COUNT(*) FROM request_log WHERE user_id=%d AND free_p='f' AND log_date>DATE_SUB(CURDATE(), INTERVAL 1 DAY)" % self.userId
                cursor.execute(query)
                row = cursor.fetchone()
                assert None != row
                todayLookups = row[0]
                if todayLookups >= g_unregisteredLookupsDailyLimit:
                    fOverLimit = True
            cursor.close()
        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            raise
        if g_fDisableRegistrationCheck:
            fOverLimit = False
        return fOverLimit

    # return how many days a given registered user has before his reg code
    # expires. Return None if there was a fatal error getting this information
    def getDaysToExpire(self):
        assert self.userId
        daysRegistered = None
        cursor = None
        try:
            sql = "SELECT TO_DAYS(now())-TO_DAYS(registration_date) FROM users WHERE user_id=%d" % self.userId
            db = self.getManagementDatabase()
            cursor = db.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            cursor.close()
            if not row:
                return None
            daysRegistered = int(row[0])
            # TODO: I no longer understand why I regCodeValid is sent
            # Remove after making sure it doesn't break
            #self.outputField(Fields.regCodeValid, "1")
        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            raise
        assert None != daysRegistered
        DAYS_TO_REG_CODE_EXPIRATION = 365
        daysToExpire = DAYS_TO_REG_CODE_EXPIRATION - daysRegistered
        if daysToExpire < 0:
            daysToExpire = 0
        return daysToExpire

    def handleRegCodeDaysToExpireRequest(self,fieldName,fieldValue):
        assert self.userId
        assert self.fHasField(Fields.getRegCodeDaysToExpire)
        assert None == fieldValue
        if not self.fHasField(Fields.regCode):
            return ServerErrors.malformedRequest
        daysToExpire = self.getDaysToExpire()
        if None == daysToExpire:
            return ServerErrors.serverFailure

        self.outputField(Fields.regCodeDaysToExpire,daysToExpire)
        return None

    def handleGetLatestClientVersion(self, fieldName, fieldValue):
        assert self.userId
        assert self.fHasField(Fields.getLatestClientVersion)
        assert None != fieldValue
        latestVersion = getClientVersion(fieldValue)
        if None == latestVersion:
            return ServerErrors.malformedRequest
        self.outputField(Fields.latestClientVersion, latestVersion)
        return None

    # handle Fields.verifyRegCode. If reg code is invalid append regCodeValidField
    # with value "0". If reg code is invalid, append regCodeValidField with value
    # "1" and update users table to mark this as a registration
    # Return error if there was an error that requires aborting connection
    # Return None if all was ok
    def handleVerifyRegistrationCodeRequest(self,fieldName,fieldValue):
        # by now we have to have it (from handling Fields.getCookie, Fields.cookie or Fields.regCode)
        assert self.userId
        assert self.fHasField(Fields.verifyRegCode)
        # those are the only fields that can come with Fields.verifyRegCode
        allowedFields = [Fields.transactionId, Fields.clientInfo, Fields.protocolVersion, Fields.cookie, Fields.getCookie, Fields.verifyRegCode, Fields.getLatestClientVersion]
        for field in self.fields.keys():
            if field not in allowedFields:
                return ServerErrors.malformedRequest

        regCode = fieldValue

        fRegCodeExists = self.fRegCodeExists(regCode)

        self.logRegCodeToVerify(self.userId,regCode,fRegCodeExists)

        if not fRegCodeExists:
            self.outputField(Fields.regCodeValid, "0")
            return None

        # update users table to reflect the fact, that this user has registered
        cursor=None
        try:
            db = self.getManagementDatabase()
            cursor = db.cursor()
            regCodeEscaped = db.escape_string(regCode)

            # TODO: should we check if a given user is already registered? It's
            # possible scenario, but not making much sense
            cursor.execute("""UPDATE users SET reg_code='%s', registration_date=now() WHERE user_id=%d""" % (regCodeEscaped, self.userId))
            cursor.close()

            self.outputField(Fields.regCodeValid, "1")
        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            raise
        return None

    # Set self.userId based on reg code given by client
    # Return error if there was a problem that requires aborting the connection
    # Return None if all was ok
    def handleRegistrationCodeRequest(self):
        global g_fDisableRegistrationCheck
        assert self.fHasField(Fields.regCode)

        if self.fHasField(Fields.getCookie) or self.fHasField(Fields.cookie):
            # those shouldn't be in the same request
            return ServerErrors.malformedRequest

        if g_fDisableRegistrationCheck:
            return

        regCode = self.getFieldValue(Fields.regCode)
        cursor = None
        try:
            db = self.getManagementDatabase()
            cursor = db.cursor()
            regCodeEscaped = db.escape_string(regCode)

            cursor.execute("SELECT user_id,disabled_p FROM users WHERE reg_code='%s';" % regCodeEscaped)
            row = cursor.fetchone()
            cursor.close()
            if not row:
                return ServerErrors.invalidRegCode

            if 't'==row[1]:
                return ServerErrors.userDisabled

            self.userId = int(row[0])
            self.fRegisteredUser = True
        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            raise
        return None

    # Set self.userId based on cookie given by client
    # Return error if there was a problem that requires aborting the connection
    # Return None if all was ok
    def handleCookieRequest(self):
        assert self.fHasField(Fields.cookie)

        if self.fHasField(Fields.getCookie) or self.fHasField(Fields.regCode):
            # those shouldn't be in the same request
            return ServerErrors.malformedRequest

        cookie = self.getFieldValue(Fields.cookie)
        if cookie == self.testCookie:
            self.userId = 1
            return None

        cursor = None
        try:
            db = self.getManagementDatabase()
            cursor = db.cursor()
            cookieEscaped = db.escape_string(cookie)

            cursor.execute("SELECT user_id,disabled_p FROM users WHERE cookie='%s';" % cookieEscaped)
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return ServerErrors.invalidCookie

            if 't'==row[1]:
                return ServerErrors.userDisabled

            self.userId = int(row[0])
        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            raise
        return None

    # Assign a cookie to the user. Try to re-use cookie based on deviceInfo
    # or create a new entry in users table. Set self.userId
    # Return error if there was a problem that requires aborting the connection
    # Return None if all was ok
    def handleGetCookieRequest(self):
        assert self.fHasField(Fields.getCookie)

        if self.fHasField(Fields.regCode) or self.fHasField(Fields.cookie):
            # those shouldn't be in the same request
            return ServerErrors.malformedRequest

        deviceInfo = self.getFieldValue(Fields.getCookie)
        if not fValidDeviceInfo(deviceInfo):
            return ServerErrors.unsupportedDevice

        cursor=None
        try:
            db = self.getManagementDatabase()
            cursor = db.cursor()
            deviceInfoEscaped = db.escape_string(deviceInfo)

            fNeedsCookie = True
            if fDeviceInfoUnique(deviceInfo):
                cursor.execute("SELECT user_id,cookie,reg_code FROM users WHERE device_info='%s';" % deviceInfoEscaped)
                row = cursor.fetchone()
                if row:
                    self.userId = int(row[0])
                    cookie = row[1]
                    fNeedsCookie = False
                    # TODO: what to do if reg_code exists for this row?
                    # This can happen in the scenario:
                    #  - Get-Cookie
                    #  - register
                    #  - delete the app, re-install
                    #  - Get-Cookie - we reget the cookie

            if fNeedsCookie:
                # generate new entry in users table
                cookie = getUniqueCookie(cursor)
                # it's probably still possible (but very unlikely) to have a duplicate
                # cookie, in which case we'll just abort
                query = """INSERT INTO users (cookie, device_info, cookie_issue_date, reg_code, registration_date, disabled_p) VALUES ('%s', '%s', now(), NULL, NULL, 'f');""" % (cookie, deviceInfoEscaped)
                cursor.execute(query)
                self.userId=cursor.lastrowid

            self.outputField(Fields.cookie, cookie)
            cursor.close()

        except _mysql_exceptions.Error, ex:
            if cursor:
                cursor.close()
            raise

        self.logGetCookie(self.userId,deviceInfo,cookie)
        return None

    # figure out user id and set self.userId
    # Possible cases:
    # a) we get registration code
    #     - user_id is "select user_id from users where reg_code = $reg_code"
    #     - cookie should not be present
    # b) we get cookie
    #     - user_id is "select user_id from users where cookie = $cookie", reg_code column should be empty
    #     - reg code should not be present
    # c) we have Get-Cookie request
    #     - we try to re-issue cookie based on device_info i.e. if deviceInfoUnique($deviceInfo)
    #       select cookie from users where device_info = $deviceInfo. if present go to b)
    #       if not present, we create a new entry in users table, and use the new user_id
    # return error if for any reson we failed and need to terminate, None if all is ok
    def computeUserId(self):

        # case a)
        if self.fHasField(Fields.regCode):
            return self.handleRegistrationCodeRequest()

        # case b)
        if self.fHasField(Fields.cookie):
            return self.handleCookieRequest()

        # case c)
        if self.fHasField(Fields.getCookie):
            return self.handleGetCookieRequest()

    # called after we parse the whole client request (or if there's an error
    # during request parsing) so that we can process the request and return
    # apropriate response to the client.
    # If error is != None, this is the server errro code to return to the client
    def processRequest(self, error):
        global g_fForceUpgrade, g_fDisableRegistrationCheck

        try:
            log(SEV_MED, "--------------------------------------------------------------------------------\n")

            # try to return Fields.transactionId at all costs
            if self.fHasField(Fields.transactionId):
                self.outputField(Fields.transactionId, self.getFieldValue(Fields.transactionId))

            # exit if there was an error during request parsing
            if None != error:
                return error

            if g_fForceUpgrade:
                return ServerErrors.forceUpgrade

            if not self.fHasField(Fields.transactionId):
                return ServerErrors.malformedRequest

            # protocolVersion and clientInfo must exist
            if not self.fHasField(Fields.protocolVersion):
                return ServerErrors.malformedRequest

            if not self.fHasField(Fields.clientInfo):
                return ServerErrors.malformedRequest

            if PROTOCOL_VERSION != self.getFieldValue(Fields.protocolVersion):
                return ServerErrors.invalidProtocolVersion

            if 0 != len(self.disabledModules):
                self.outputPayloadField(Fields.disabledModules, '\n'.join(self.disabledModules))

            error = self.computeUserId()
            if None != error:
                return error

            # TODO: hack, need to find better solution
            if None==self.userId and g_fDisableRegistrationCheck:
                self.userId = 1

            assert self.userId

            # dispatch a function handling a given request field
            # we're kind of blind here i.e. theoretically we can get
            # multiple, unrelated requests here but we don't do that from the client
            # so in practice we only get one request to handle per client request
            for fieldName in self.fields.keys():

                fieldHandleProc = getFieldHandler(fieldName)
                fieldAfterFinishCallback = getFieldAfterFinishCallback(fieldName)

                if None != fieldHandleProc:
                    # don't log insignificant requests
                    if fieldName not in [Fields.getRegCodeDaysToExpire, Fields.getLatestClientVersion]:
                        self.requestsToLog.append(fieldName)

                    # avoid checking lookup limit for free requests - speeds
                    # up the operations
                    if fFreeRequest(fieldName):
                        fNeedLookupLimitCheck = False
                    else:
                        fNeedLookupLimitCheck = not self.fRegisteredUser

                    if fNeedLookupLimitCheck:
                        if self.fOverUnregisteredLookupsLimit(self.userId):
                            return ServerErrors.lookupLimitReached

                    fieldValue = self.getFieldValue(fieldName)
                    error = fieldHandleProc(self, fieldName, fieldValue)
                    if None != error:
                        return error

                    if fieldAfterFinishCallback is not None:
                        self.afterFinishCallbacks.append(fieldAfterFinishCallback)

        except Exception, ex:
            log(SEV_EXC, exceptionAsStr(ex))
            return ServerErrors.serverFailure
        except:
            # TODO: I don't understand why the above doesn't catch raise "string"
            # exception
            return ServerErrors.serverFailure

        return None # there were no problems

    def answer(self, error):
        error = self.processRequest(error)
        self.finish(error)

    def lineReceived(self, request):
        try:
            # empty line marks end of request
            if request == "":
                return self.answer(None)

            log(SEV_MED, "%s\n" % request)

            (fieldName,fieldValue) = parseRequestLine(request)
            if None == fieldName:
                return self.answer(ServerErrors.malformedRequest)

            if not Fields.fClientField(fieldName):
                return self.answer(ServerErrors.invalidRequest)

            #print "checking for args for %s, value is %s" % (fieldName,value)
            if Fields.fFieldHasArguments(fieldName):
                #print "%s needs arg" % fieldName
                if None == fieldValue:
                    # expected arguments for this request, but didn't get it
                    return self.answer(ServerErrors.requestArgumentMissing)
            else:
                #print "%s doesn't need arg" % fieldName
                if None != fieldValue:
                    #print "but did get an arg"
                    # got arguments even though the function doesn't expect it
                    return self.answer(ServerErrors.unexpectedRequestArgument)

            if self.fHasField(fieldName):
                # duplicate field
                return self.answer(ServerErrors.malformedRequest)

            # turn "Get-Url" requests into "Get-Url-SCHEMA" requests
            if fieldName == Fields.getUrl:
                if fieldValue is None or 0 == len(fieldValue):
                    return self.answer(ServerErrors.malformedRequest)
                pos = fieldValue.find(':')
                if -1 == pos:
                    # this request doesn't have any arguments
                    schema = fieldValue
                    fieldValue = None
                else:
                    schema = fieldValue[:pos]
                    fieldValue = fieldValue[pos + 1:]
                # ignore the part from the beginning until first '+' (if exists)
                pos = schema.find('+')
                if -1 != pos:
                    schema = schema[pos + 1:]
                fieldName = "%s-%s" % (Fields.getUrl, schema)

            self.setFieldValue(fieldName,fieldValue)

        except Exception, ex:
            log(SEV_EXC, exceptionAsStr(ex))
            return self.answer(ServerErrors.serverFailure)

    def handleGet411PersonSearch(self, fieldName, fieldValue):
        value = self.getFieldValue(Fields.get411PersonSearch)
        (firstName,lastName,cityOrZip,state) = extractCommaSeparatedFields(value,4)
        if 0 == len(lastName):
            return ServerErrors.malformedRequest

        resultType, resultBody = yp_retrieve.retrievePerson(firstName,lastName,cityOrZip,state)

        if RESULTS_DATA==resultType:
            self.appendPayloadField(Fields.out411PersonSearchResult, resultBody)
            return None

        if MULTIPLE_SELECT==resultType:
            self.appendPayloadField(Fields.out411PersonSearchCityMultiselect, resultBody)
            return None

        if NO_RESULTS==resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if TOO_MANY_RESULTS==resultType:
            assert(None==resultBody)
            self.appendField(Fields.out411TooManyResults)
            return None

        if NO_CITY==resultType:
            assert(None==resultBody)
            self.appendField(Fields.out411NoCity)
            return None

        assertParseFailed(resultType,resultBody,"handleGet411PersonSearch")
        ## logParsingFailure(fieldName, fieldValue, "", "")
        return ServerErrors.moduleTemporarilyDown

    def handleGet411BusinessSearch(self, fieldName, fieldValue):
        (name,cityOrZip,state,surrounding,categoryOrName) = extractCommaSeparatedFields(fieldValue,5)

        if 0 == len(name) or 0 == len(state):
            return ServerErrors.malformedRequest

        if surrounding != "Yes" and surrounding != "No":
            return ServerErrors.malformedRequest

        if categoryOrName != "Name" and "Category" != categoryOrName:
            return ServerErrors.malformedRequest

        assert surrounding == "Yes" or surrounding == "No"
        assert categoryOrName == "Name" or categoryOrName == "Category"

        resultType, resultBody = yp_retrieve.retrieveBusiness(name,cityOrZip,state,surrounding,categoryOrName)

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.out411BusinessSearchResult, resultBody)
            return None

        if MULTIPLE_SELECT == resultType:
            self.appendPayloadField(Fields.out411BusinessSearchMultiselect, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if NO_CITY == resultType:
            assert(None==resultBody)
            self.appendField(Fields.out411NoCity)
            return None

        assertParseFailed(resultType,resultBody,"handleGet411BusinessSearch")
        return ServerErrors.moduleTemporarilyDown

    def handleGet411BusinessSearchByUrl(self, fieldName, fieldValue):
        url = fieldValue
        resultType, resultBody = yp_retrieve.retrieveBusinessSearchByUrl(url)

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.out411BusinessSearchResult, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if NO_CITY==resultType:
            assert(None==resultBody)
            self.appendField(Fields.out411BusinessSearchNoCity)
            return None

        assertParseFailed(resultType,resultBody,"handleGet411BusinessSearchByUrl")
        return ServerErrors.moduleTemporarilyDown

    def handleGet411ReversePhone(self, fieldName, fieldValue):
        fieldValue = fieldValue.strip()
        valueFields = fieldValue.split("-")
        if len(valueFields)!= 3 or len(fieldValue) != 12:  ##12 = 10 + 2*'-'
            return ServerErrors.malformedRequest
        (xxx,yyy,zzzz) = valueFields
        resultType, resultBody = yp_retrieve.retrieveReversePhone(xxx,yyy,zzzz)

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.out411ReversePhoneResult, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGet411ReversePhone")
        return ServerErrors.moduleTemporarilyDown

    def handleGet411AreaByCity(self, fieldName, fieldValue):
        (city,state) = extractCommaSeparatedFields(fieldValue,2)
        resultType, resultBody = yp_retrieve.retrieveAreaCodeByCity(city,state)

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.out411AreaByCityResult, resultBody)
            return None

        if MULTIPLE_SELECT == resultType:
            self.appendPayloadField(Fields.out411AreaByCityMultiselect, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGet411AreaByCity")
        return ServerErrors.moduleTemporarilyDown

    def handleGet411InternationalCodeSearch(self, fieldName, fieldValue):
        code = fieldValue.strip()
        resultType, resultBody = yp_retrieve.retrieveInternational(code)

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.out411InternationalCodeSearchResult, resultBody)
            return None

        if NO_RESULTS==resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGet411InternationalCodeSearch")
        return ServerErrors.moduleTemporarilyDown

    def handleGet411ZipByCity(self, fieldName, fieldValue):
        (city,state) = extractCommaSeparatedFields(fieldValue,2)
        resultType, resultBody = yp_retrieve.retrieveZipCodeByCity(city,state)

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.out411ZipByCityResult, resultBody)
            return None

        if MULTIPLE_SELECT == resultType:
            self.appendPayloadField(Fields.out411ZipByCityMultiselect, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGet411ZipByCity")
        return ServerErrors.moduleTemporarilyDown

    def handleGet411ReverseZip(self, fieldName, fieldValue):
        code = fieldValue.strip()
        resultType, resultBody = yp_retrieve.retrieveReverseZipCode(code)

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.out411ReverseZipResult, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGet411ReverseZip")
        return ServerErrors.moduleTemporarilyDown

    def handleGet411ReverseArea(self, fieldName, fieldValue):
        code = fieldValue.strip()
        resultType, resultBody = yp_retrieve.retrieveReverseAreaCode(code)

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.out411ReverseAreaResult, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGet411ReverseArea")
        return ServerErrors.moduleTemporarilyDown

    def handleGetMovies(self, fieldName, fieldValue):
        location = fieldValue
        assert 0!=len(location)
        url = yahooMoviesUrl % urllib.quote(location)
        htmlTxt = getHttp(url, retryCount=3)
        if None == htmlTxt:
            return ServerErrors.moduleTemporarilyDown
        resultType, resultBody = movies.parseMovies(htmlTxt)

        if MOVIES_DATA == resultType:
            self.appendPayloadField(Fields.moviesData, resultBody)
            return None

        if LOCATION_UNKNOWN == resultType:
            assert(None==resultBody)
            self.appendField(Fields.locationUnknown)
            return None

        if WEB_PAGE_UNDER_MAINTENANCE == resultType:
            assert(None==resultBody)
            return ServerErrors.moduleTemporarilyDown

        if LIST_OF_LOCATION == resultType:
            self.appendPayloadField(Fields.locationAmbiguous, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetMovies")
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
        return ServerErrors.moduleTemporarilyDown

    def handleGetRecipesList(self, fieldName, fieldValue):
        query = fieldValue
        assert 0!=len(query)
        url = epicuriousSServerUrl % urllib.quote(query)
        htmlTxt = retrieveHttpResponseWithRedirectionHandleException(url)
        if None == htmlTxt:
            return ServerErrors.moduleTemporarilyDown
        resultType, resultBody = epicurious.parseSearch(htmlTxt)
        if LIST_OF_RECIPES == resultType:
            self.appendPayloadField(Fields.recipiesList, resultBody)
            return None

        if EMPTY_LIST == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetRecipesList")
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
        return ServerErrors.moduleTemporarilyDown

    def handleGetRecipe(self, fieldName, fieldValue):
        url = fieldValue
        assert 0!=len(url)
        url = epicuriousRServerUrl % url
        htmlTxt = retrieveHttpResponseWithRedirectionHandleException(url)
        if None == htmlTxt:
            return ServerErrors.moduleTemporarilyDown
        resultType, resultBody = epicurious.parseRecipe(htmlTxt)
        if RECIPE_DATA == resultType:
            self.appendPayloadField(Fields.recipe, resultBody)
            return None

        # this should never happen...
        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetRecipe")
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
        return ServerErrors.moduleTemporarilyDown

    def handleGetWeather(self, fieldName, fieldValue):
        location = fieldValue
        if 0 == len(location):
            return ServerErrors.invalidRequest

        resultType, resultBody = weather.retrieveWeather(self.getCookieJar(), location)

        if WEATHER_DATA == resultType:
            self.appendPayloadField(Fields.weather, resultBody)
            return None

        if LOCATION_MULTISELECT == resultType:
            self.appendPayloadField(Fields.weatherMultiselect, resultBody)
            return None

        if LOCATION_UNKNOWN == resultType:
            assert(None==resultBody)
            self.appendField(Fields.locationUnknown)
            return None

        assertParseFailed(resultType,resultBody,"handleGetWeather")
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
        return ServerErrors.moduleTemporarilyDown

    def handleGetCurrentBoxOffice(self, fieldName, fieldValue):
        assert None == fieldValue
        global g_boxOfficeDataCached, g_boxOfficeDataWhenCached
        # check if we can just return cached data. We're going to refresh the cache
        # every hour

        if None != g_boxOfficeDataCached:
            if not boxOfficeCacheExpired():
                log(SEV_LOW,"Using cached box office data\n")
                self.appendPayloadField(Fields.outCurrentBoxOffice, g_boxOfficeDataCached)
                return None

        resultType, resultBody = boxoffice.retrieveBoxOffice()

        # usually we just do return retrieveFailed() and returnParsingFailed()
        # but box office caches the info, so we might be able to return it
        # even if there's a failure. But we still want log/be informed about
        # the problem
        if RETRIEVE_FAILED == resultType:
            logRetrieveFailed(fieldName, fieldValue, resultBody)

        if PARSING_FAILED == resultType:
            logParsingFailed(fieldName, fieldValue, resultBody)

        if RESULTS_DATA == resultType:
            # this is our new cached info
            g_boxOfficeDataCached = resultBody
            g_boxOfficeDataWhenCached = time.time()
        elif None != g_boxOfficeDataCached:
            # now a trick: for some reason we couldn't retrieve box office data
            # if we have it cached, use the cached copy
            resultType, resultBody = RESULTS_DATA, g_boxOfficeDataCached

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.outCurrentBoxOffice, resultBody)
            return None

        if RETRIEVE_FAILED == resultType:
            return handleRetrieveFailed(fieldName, fieldValue, resultBody)

        if PARSING_FAILED == resultType:
            return handleParsingFailed(fieldName, fieldValue, resultBody)

        assert 0 # we should never get here
        return ServerErrors.moduleTemporarilyDown

    def handleGetDream(self, fieldName, fieldValue):
        dream = fieldValue.strip().replace(".","").replace(",","")
        if 0==len(dream):
            return ServerErrors.malformedRequest
        resultType, resultBody = dreams_retrieve.retrieveDream(dream)

        if DREAM_DATA == resultType:
            self.appendPayloadField(Fields.outDream, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetDream")
        return ServerErrors.moduleTemporarilyDown

    def handleCurrencyConversion(self, fieldName, fieldValue):

        # check validity of parameters
        # currencyList = fieldValue.split(" ")
        #if len(currencyList) < 1:
        #    return ServerErrors.malformedRequest

        out = []
        currencies = currency_retrieve.getCurrencies()
        if 0 == len(currencies):
            return ServerErrors.moduleTemporarilyDown

        for key, value in currencies.iteritems():
            out.append([key, str(value)])

        c = lambda x, y: cmp(x[0], y[0])
        out.sort(c)
        self.appendPayloadField(Fields.outCurrencyConversion, universalDataFormatReplaceEntities(out))
        return None

    def handleGetJokesList(self, fieldName, fieldValue):
        assert 0!=len(fieldValue)
        resultType, resultBody = jokes.getJokesList(fieldValue)

        if JOKES_LIST == resultType:
            self.appendPayloadField(Fields.outJokesList, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        return ServerErrors.moduleTemporarilyDown

    def handleGetJoke(self, fieldName, fieldValue):
        assert 0!=len(fieldValue)
        if "random" == fieldValue.strip():
            res, body = jokes.getRandomJoke()
            if JOKE_DATA == res:
                self.appendPayloadField(Fields.outJoke, body)
                return None
            return ServerErrors.moduleTemporarilyDown
        else:
            res, body = jokes.getJoke(fieldValue)

        if JOKE_DATA==res:
            self.appendPayloadField(Fields.outJoke, body)
            return None
        return ServerErrors.moduleTemporarilyDown

    def afterGetJoke(self):
        jokes.fillJokesCache()

    def handleGetStocksList(self, fieldName, fieldValue):
        stocksSymbols = fieldValue.replace(" ","").replace(";"," ")
        url = stocksListUrl % urllib.quote(stocksSymbols)
        htmlTxt = retrieveHttpResponseWithRedirectionHandleException(url)
        if None == htmlTxt:
            return ServerErrors.moduleTemporarilyDown

        resultType, resultBody = stocks.parseList(htmlTxt)

        if STOCKS_LIST == resultType:
            self.appendPayloadField(Fields.outStocksList, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetStocksList")
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
        return ServerErrors.moduleTemporarilyDown

    def handleGetStocksListValidateLast(self, fieldName, fieldValue):
        stocksSymbols = fieldValue.replace(" ","").replace(";"," ")
        url = stocksListUrl % urllib.quote(stocksSymbols)
        htmlTxt = retrieveHttpResponseWithRedirectionHandleException(url)
        if None == htmlTxt:
            return ServerErrors.moduleTemporarilyDown

        resultType, resultBody = stocks.parseListValidateLast(htmlTxt)

        if STOCKS_LIST == resultType:
            self.appendPayloadField(Fields.outStocksList, resultBody)
            return None

        ## work?
        if VALIDATE_THIS == resultType:
            return self.handleGetStockByName(fieldName, resultBody)

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetStocksList")
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
        return ServerErrors.moduleTemporarilyDown

    def handleGetStock(self, fieldName, fieldValue):
        url = stockUrl % fieldValue

        htmlTxt = retrieveHttpResponseWithRedirectionHandleException(url)
        if None == htmlTxt:
            return ServerErrors.moduleTemporarilyDown
        resultType, resultBody = stocks.parseStock(htmlTxt)

        if STOCKS_DATA == resultType:
            self.appendPayloadField(Fields.outStock, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetStock")
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
        return ServerErrors.moduleTemporarilyDown

    def handleGetStockByName(self, fieldName, fieldValue):
        url = stockUrl % fieldValue
        htmlTxt = retrieveHttpResponseWithRedirectionHandleException(url)
        if None == htmlTxt:
            return ServerErrors.moduleTemporarilyDown
        resultType, resultBody = stocks.parseName(htmlTxt)

        if STOCKS_LIST == resultType:
            self.appendPayloadField(Fields.outStocksListByName, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetStockByName")
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
        return ServerErrors.moduleTemporarilyDown

    def getAvailableModulesForCurrentClientVersion(self):
        global g_fTestCrossModules
        global g_fDisableAmazonModule
        ret = {}
        # set all to true
        ret['Amazon'] = True
        ret['ListsOfBests'] = True
        ret['Lyrics'] = True
        ret['Encyclopedia'] = True
        ret['Netflix'] = True
        ret['eBooks'] = True
        ret['eBay'] = True
        if g_fTestCrossModules:
            return ret
        # else
        ret['Amazon'] = False
        ret['ListsOfBests'] = False
        ret['Lyrics'] = False
        ret['Encyclopedia'] = False
        ret['Netflix'] = False
        ret['eBooks'] = False
        ret['eBay'] = False

        clientVersion = self.getFieldValue(Fields.clientInfo)

        if "Palm " == clientVersion[:5]:
            version = float(clientVersion[5:])
            if version >= 1.4 and not g_fDisableAmazonModule:
                ret['Amazon'] = True
            if version >= 6.6:
                ret['Netflix'] = True
            if version >= 6.6:
                ret['Encyclopedia'] = True
            if version >= 6.6:
                ret['ListsOfBests'] = True
            if version >= 6.6:
                ret['Lyrics'] = True
            if version >= 6.6:
                ret['eBooks'] = True
            if version >= 6.6:
                ret['eBay'] = True

        #else wince... and others?

        # Other modules: (but they are not crosslinked, so # them)
        #ret['Weather'] = True
        #ret['Jokes'] = True
        #ret['Movies'] = True
        #ret['Box Office'] = True
        #ret['Stocks'] = True
        #ret['411'] = True
        #ret['Gas Prices'] = True
        #ret['Currencies'] = True
        #ret['TV Listings'] = True
        #ret['Horoscopes'] = True
        #ret['Dreams'] = True
        #ret['Dictionary'] = True
        #ret['Recipes'] = True

        return ret

    def handleGetAmazonItem(self, fieldName, fieldValue):
        global g_fDisableAmazonModule
        if g_fDisableAmazonModule:
            return ServerErrors.moduleTemporarilyDown
        asin = fieldValue
        resultType, resultBody = ourAmazon.retriveAmazonItemByAsin(asin, self.getAvailableModulesForCurrentClientVersion())

        if AMAZON_ITEM == resultType:
            self.appendPayloadField(Fields.outAmazon, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetAmazonSearch(self, fieldName, fieldValue):
        global g_fDisableAmazonModule
        if g_fDisableAmazonModule:
            return ServerErrors.moduleTemporarilyDown
        parts = fieldValue.split(";")
        if len(parts) < 4:
            return ServerErrors.malformedRequest
        if len(parts) > 4:
            parts[3] = string.join(parts[3:],";")
        (search_index,browse_node,page,keyword) = parts[:4]

        resultType, resultBody = ourAmazon.retriveAmazonSearchByKeyword(keyword, search_index, browse_node, page, self.getAvailableModulesForCurrentClientVersion())

        if AMAZON_SEARCH_LIST == resultType:
            self.appendPayloadField(Fields.outAmazon, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetAmazonSearch")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetAmazonBrowse(self, fieldName, fieldValue):
        global g_fDisableAmazonModule
        global g_amazonBrowseCache
        if g_fDisableAmazonModule:
            return ServerErrors.moduleTemporarilyDown
        splittedValue = fieldValue.split(";")
        if 3 != len(splittedValue):
            return ServerErrors.malformedRequest
        (search_index,browse_node,page) = splittedValue

        status, resultType, resultBody = g_amazonBrowseCache.getBrowse(search_index, browse_node)
        if g_amazonBrowseCache.NO_DATA == status:
            resultType, resultBody = ourAmazon.retriveAmazonBrowseNode(search_index, browse_node, page, self.getAvailableModulesForCurrentClientVersion())
        elif resultType == NO_RESULTS:
            resultType, resultBody = ourAmazon.retriveAmazonSearchByKeyword("", search_index, browse_node, page, self.getAvailableModulesForCurrentClientVersion())

        if g_amazonBrowseCache.NO_DATA == status:
            g_amazonBrowseCache.setBrowse(search_index, browse_node, resultType, resultBody)

        if AMAZON_SEARCH_LIST == resultType:
            self.appendPayloadField(Fields.outAmazon, resultBody)
            return None

        if AMAZON_BROWSE_LIST == resultType:
            self.appendPayloadField(Fields.outAmazon, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetAmazonBrowse")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetAmazonList(self, fieldName, fieldValue):
        global g_fDisableAmazonModule
        if g_fDisableAmazonModule:
            return ServerErrors.moduleTemporarilyDown
        parts = fieldValue.split(";")
        if 2 != len(parts):
            return ServerErrors.malformedRequest

        resultType, resultBody = ourAmazon.retriveAmazonList(parts[0],parts[1],self.getAvailableModulesForCurrentClientVersion())

        if AMAZON_SEARCH_LIST == resultType:
            self.appendPayloadField(Fields.outAmazon, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetAmazonList")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetAmazonWishlist(self, fieldName, fieldValue):
        global g_fDisableAmazonModule
        if g_fDisableAmazonModule:
            return ServerErrors.moduleTemporarilyDown
        parts = fieldValue.split(";")
        if 5 != len(parts):
            return ServerErrors.malformedRequest

        resultType, resultBody = ourAmazon.retriveAmazonWishlist(parts[0],parts[1],parts[2],parts[3], parts[4])

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.outAmazon, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetAmazonWishlist")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetGasPrices(self, fieldName, fieldValue):
        zipCode = fieldValue

        (resultType, resultBody) = gasprices.getGasPricesForZip(self.getCookieJar(), zipCode)

        if GAS_DATA == resultType:
            self.appendPayloadField(Fields.outGasPrices, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if LOCATION_UNKNOWN == resultType:
            assert(None==resultBody)
            self.appendField(Fields.locationUnknown)
            return None

        if RETRIEVE_FAILED == resultType:
            return handleRetrieveFailed(fieldName, fieldValue, resultBody)

        if PARSING_FAILED == resultType:
            return handleParsingFailed(fieldName, fieldValue, resultBody)

        assert 0 # we should never get here
        return ServerErrors.moduleTemporarilyDown

    def handleGetNetflixLogin(self, fieldName, fieldValue):
        if fieldValue is None or 0 == len(fieldValue):
            return ServerErrors.malformedRequest

        print "encrypted: ", fieldValue
        fieldValue = InfoManCrypto.decrypt_hexbin(fieldValue)
        print "decrypted: ", fieldValue

        resultType = netflix.retrieveLogin(self.getCookieJar(), fieldValue)

        if NETFLIX_UNKNOWN_LOGIN == resultType:
            self.appendField(Fields.outNetflixUnknownLogin)
            return None

        if NETFLIX_LOGIN_OK == resultType:
            self.appendField(Fields.outNetflixLoginOk)
            return None

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        assertParseFailed(resultType,None,"handleGetNetflixLogin")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetNetflixAdd(self, fieldName, fieldValue):
        resultType = netflix.retrieveAdd(self.getCookieJar(), fieldValue)

        if NETFLIX_ADD_OK == resultType:
            self.appendField(Fields.outNetflixAddOk)
            return None

        if NETFLIX_ADD_FAILED == resultType:
            self.appendField(Fields.outNetflixAddFailed)
            return None

        if NETFLIX_ADD_ALREADY_IN_QUEUE == resultType:
            self.appendField(Fields.outNetflixAddAlreadyAdded)
            return None

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        if NETFLIX_REQUEST_PASSWORD == resultType:
            self.appendField(Fields.outNetflixPasswordRequest)
            return None

        assertParseFailed(resultType,None,"handleGetNetflixAdd")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetNetflixItem(self, fieldName, fieldValue):
        resultType, resultBody = netflix.retrieveItem(self.getCookieJar(), fieldValue, self.getAvailableModulesForCurrentClientVersion())

        if NETFLIX_ITEM == resultType:
            self.appendPayloadField(Fields.outNetflix, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if NETFLIX_REQUEST_PASSWORD == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNetflixPasswordRequest)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        assertParseFailed(resultType,resultBody,"handleGetNetflixItem")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetNetflixSearch(self, fieldName, fieldValue):
        resultType, resultBody = netflix.retrieveSearch(self.getCookieJar(), fieldValue, self.getAvailableModulesForCurrentClientVersion())

        if NETFLIX_SEARCH_LIST == resultType:
            self.appendPayloadField(Fields.outNetflix, resultBody)
            return None

        if NETFLIX_BROWSE_LIST == resultType:
            self.appendPayloadField(Fields.outNetflix, resultBody)
            return None

        if NETFLIX_ITEM == resultType:
            self.appendPayloadField(Fields.outNetflix, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if NETFLIX_REQUEST_PASSWORD == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNetflixPasswordRequest)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        assertParseFailed(resultType,resultBody,"handleGetNetflixSearch")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetNetflixQueue(self, fieldName, fieldValue):
        resultType, resultBody = netflix.retrieveQueue(self.getCookieJar(), fieldValue, self.getAvailableModulesForCurrentClientVersion())

        if NETFLIX_QUEUE == resultType:
            self.appendPayloadField(Fields.outNetflixQueue, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if NETFLIX_REQUEST_PASSWORD == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNetflixPasswordRequest)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        assertParseFailed(resultType,resultBody,"handleGetNetflixQueue")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetNetflixBrowse(self, fieldName, fieldValue):
        resultType, resultBody = netflix.retrieveBrowse(self.getCookieJar(), fieldValue, self.getAvailableModulesForCurrentClientVersion())

        if NETFLIX_SEARCH_LIST == resultType:
            self.appendPayloadField(Fields.outNetflix, resultBody)
            return None

        if NETFLIX_BROWSE_LIST == resultType:
            self.appendPayloadField(Fields.outNetflix, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if NETFLIX_REQUEST_PASSWORD == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNetflixPasswordRequest)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        assertParseFailed(resultType,resultBody,"handleGetNetflixBrowse")
        logParsingFailure(fieldName, fieldValue)
        return ServerErrors.moduleTemporarilyDown

    def handleGetHoroscope(self, fieldName, fieldValue):
        listValues = fieldValue.split(";")
        url = ""
        if 1 == len(listValues):
            url = "http://astrology.yahoo.com/astrology/general/dailyoverview/%s" % fieldValue.lower()
        elif 2 == len(listValues):
            # by url
            assert("yh" == listValues[0])
            url = "http://astrology.yahoo.com%s" % listValues[1]
        else:
            return ServerErrors.malformedRequest

        htmlTxt = retrieveHttpResponseWithRedirectionHandleException(url)
        if None == htmlTxt:
            return ServerErrors.moduleTemporarilyDown
        resultType, resultBody = horoscopes.parseHoroscope(htmlTxt)

        if HOROSCOPE_DATA == resultType:
            self.appendPayloadField(Fields.outHoroscope, resultBody)
            return None

        assertParseFailed(resultType,None,"handleGetHoroscope")
        logParsingFailure(fieldName, fieldValue, htmlTxt, url)
        return ServerErrors.moduleTemporarilyDown

    def handleGetListsOfBestsSearch(self, fieldName, fieldValue):
        resultType, resultBody = listsofbests.retrieveListsOfBestsSearch(fieldValue, self.getAvailableModulesForCurrentClientVersion())

        if LISTSOFBESTS_SEARCH == resultType:
            self.appendPayloadField(Fields.outListsOfBests, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        assertParseFailed(resultType,resultBody,"handleGetListsOfBestsSearch")
        return ServerErrors.moduleTemporarilyDown

    def handleGetListsOfBestsItem(self, fieldName, fieldValue):
        resultType, resultBody = listsofbests.retrieveListsOfBestsItem(fieldValue, self.getAvailableModulesForCurrentClientVersion())
        if LISTSOFBESTS_DETAILS == resultType:
            self.appendPayloadField(Fields.outListsOfBests, resultBody)
            return None

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        assertParseFailed(resultType,resultBody,"handleGetListsOfBestsItem")
        return ServerErrors.moduleTemporarilyDown

    def handleGetListsOfBestsBrowse(self, fieldName, fieldValue):
        global g_listsOfBestsCache
        resultType, resultBody = LISTSOFBESTS_LISTS, g_listsOfBestsCache.getListsList(fieldValue)
        if None == resultBody:
            resultType, resultBody = listsofbests.retrieveListsOfBestsBrowse(fieldValue, self.getAvailableModulesForCurrentClientVersion())

        if LISTSOFBESTS_LIST == resultType:
            self.appendPayloadField(Fields.outListsOfBests, resultBody)
            return None

        if LISTSOFBESTS_LISTS == resultType:
            self.appendPayloadField(Fields.outListsOfBests, resultBody)
            return None

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        assertParseFailed(resultType,resultBody,"handleGetListsOfBestsBrowse")
        return ServerErrors.moduleTemporarilyDown

    def handleGetTvListingsProviders(self, fieldName, fieldValue):
        # fieldValue is zip code
        if fieldValue is None or 0 == len(fieldValue):
            return ServerErrors.malformedRequest
        cm = tvlistings_retrieve.getCacheManager()
        db = self.getManagementDatabase()
        jar = self.getCookieJar()
        retriever = cm.allocateRetriever(db, jar, fieldValue)
        res, udf = retriever.retrieveProviders()
        if TVLISTINGS_PROVIDERS == res:
            self.appendPayloadField(Fields.outTvListingsProviders, udf)
            return None
        # logging is done in retriever
        return ServerErrors.moduleTemporarilyDown

    def handleGetTvListings(self, fieldName, fieldValue):
        # fieldValue is zip code
        if fieldValue is None or 0 == len(fieldValue):
            return ServerErrors.malformedRequest
        # fieldValue are zipCode, providerId and date separated by ','
        vals = fieldValue.split(',')
        if 3 != len(vals):
            return ServerErrors.malformedRequest
        cm = tvlistings_retrieve.getCacheManager()
        db = self.getManagementDatabase()
        jar = self.getCookieJar()
        retriever = cm.allocateRetriever(db, jar, vals[0])
        retriever.setProvider(int(vals[1]))
        date = time.strptime(vals[2], "%Y%m%dT%H%M%S")
        retriever.setDate(date)
        res, udf = retriever.retrieveListings()
        if res == TVLISTINGS_PARTIAL:
            self.appendPayloadField(Fields.outTvListingsPartial, udf)
            return None
        if res == TVLISTINGS_FULL:
            self.appendPayloadField(Fields.outTvListingsFull, udf)
            return None
        # logging is done in retriever
        return ServerErrors.moduleTemporarilyDown

    def handleGetLyricsSearchDefinition(self, fieldName, fieldValue):
        fieldValueParts = fieldValue.split(";")
        if 5 != len(fieldValueParts):
            return ServerErrors.malformedRequest

        artist,title,album,composer,fullText = fieldValueParts

        (resultType, resultBody) = lyrics.getLyricsSearch(artist, title, album, composer, fullText, self.getAvailableModulesForCurrentClientVersion())

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        if LYRICS_SEARCH == resultType:
            self.appendPayloadField(Fields.outLyrics, resultBody)
            return None

        if LYRICS_ITEM == resultType:
            self.appendPayloadField(Fields.outLyrics, resultBody)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        assertParseFailed(resultType,resultBody,"handleGetLyricsSearchDefinition")
        logParsingFailure(fieldName, fieldValue, "", "")
        return ServerErrors.moduleTemporarilyDown

    def handleGetLyricsItemDefinition(self, fieldName, fieldValue):
        (resultType, resultBody) = lyrics.getLyricsItem(fieldValue, self.getAvailableModulesForCurrentClientVersion())

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        if LYRICS_ITEM == resultType:
            self.appendPayloadField(Fields.outLyrics, resultBody)
            return None

        assertParseFailed(resultType,resultBody,"handleGetLyricsItemDefinition")
        logParsingFailure(fieldName, fieldValue, resultBody[0], resultBody[1])
        return ServerErrors.moduleTemporarilyDown

    def handleDictionary(self, fieldName, fieldValue):
        (resultType, resultBody) = dictionary.getDictionaryDef(fieldValue)

        if INVALID_REQUEST == resultType:
            return ServerErrors.unexpectedRequestArgument

        if DICT_DEF == resultType:
            self.appendPayloadField(Fields.outDictDef, resultBody)
            return None

        return ServerErrors.moduleTemporarilyDown

    def handleDictionaryStats(self, fieldName, fieldValue):
        (resultType, resultBody) = dictionary.getDictionaryStats(fieldValue)

        if INVALID_REQUEST == resultType:
            return ServerErrors.unexpectedRequestArgument

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.outDictStats, resultBody)
            return None

        if DICT_DEF == resultType:
            self.appendPayloadField(Fields.outDictDef, resultBody)
            return None

        # TODO: handle empty dictstats, to get BCF list of dictionaries (done)
        return ServerErrors.moduleTemporarilyDown

    def handleDictionaryRandom(self, fieldName, fieldValue):
        (resultType, resultBody) = dictionary.getDictionaryRandom(fieldValue)

        if DICT_DEF == resultType:
            self.appendPayloadField(Fields.outDictDef, resultBody)
            return None

        return ServerErrors.moduleTemporarilyDown

    def outputPediaArticle(self, title, body, reverseLinks, langCode):
        self.appendField(Fields.outPediaArticleTitle, title)
        payload = encyclopedia.preparePayload(body, reverseLinks, langCode, title)
        self.appendPayloadField(Fields.outPediaArticle, payload)

    def handlePediaTerm(self, fieldName, fieldValue):
        parts = string.split(fieldValue, ":", 1)
        if 2 != len(parts):
            return ServerErrors.invalidRequest

        (lang, title) = parts
        if None == encyclopedia.languageName(lang):
            return ServerErrors.invalidRequest

        dbInfo = iPediaServer.getCurrDbForLang(lang)
        if None == dbInfo:
            return ServerErrors.invalidRequest

        db = iPediaServer.createArticlesConnection(dbInfo.dbName)
        assert db is not None
        cursor = db.cursor()
        try:
            articleTuple = iPediaServer.findArticle(db, cursor, title)
            if articleTuple:
                (articleId, title, body) = articleTuple
                reverseLinks = iPediaServer.getReverseLinks(db, cursor, title)
                self.outputPediaArticle(title, body, reverseLinks, lang)
            else:
                termList = iPediaServer.findFullTextMatches(db, cursor, title)
                if 0==len(termList):
                    self.appendField(Fields.outNoResults, None)
                else:
                    self.appendField(Fields.outPediaArticleTitle, title)
                    text = encyclopedia.searchResultsByteCode(termList, lang, title, 0)
                    self.outputPayloadField(Fields.outPediaSearchResults, text)
        finally:
            cursor.close()
            db.close()
        return None

    def handlePediaLangs(self, fieldName, fieldValue):
        langs = iPediaServer.getAllLangs()
        langs = encyclopedia.languagesByteCode(langs)
        self.outputPayloadField(Fields.outPediaLangs, langs)
        return None

    def handlePediaRandom(self, fieldName, fieldValue):
        lang = fieldValue
        dbInfo = iPediaServer.getCurrDbForLang(lang)
        if dbInfo is None:
            return ServerErrors.invalidRequest

        db = iPediaServer.createArticlesConnection(dbInfo.dbName)
        cursor = db.cursor()
        try:
            (articleId, title, body) = iPediaServer.getRandomArticle(cursor)
            reverseLinks = iPediaServer.getReverseLinks(db, cursor, title)
            self.outputPediaArticle(title, body, reverseLinks, lang)
            return None
        finally:
            cursor.close()
            db.close()

    def handlePediaStats(self, fieldName, fieldValue):
        lang = fieldValue
        if encyclopedia.languageName(lang) is None:
            return ServerErrors.invalidRequest

        dbInfo = iPediaServer.getCurrDbForLang(lang)
        if dbInfo is None:
            return ServerErrors.invalidRequest

        self.appendField(Fields.outPediaArticleCount, str(dbInfo.articlesCount))
        self.appendField(Fields.outPediaDbDate, str(dbInfo.dbDate))
        return None

    def handlePediaSearch(self, fieldName, fieldValue):
        startOffset = 0
        l = fieldValue.split(";")
        if 1 != len(l):
            fieldValue = l[0]
            startOffset = int(l[1])

        parts = string.split(fieldValue, ":", 1)
        if 2 != len(parts):
            return ServerErrors.invalidRequest

        (lang, searchTerm) = parts
        if None == encyclopedia.languageName(lang):
            return ServerErrors.invalidRequest

        dbInfo = iPediaServer.getCurrDbForLang(lang)
        if dbInfo is None:
            return ServerErrors.invalidRequest

        db = iPediaServer.createArticlesConnection(dbInfo.dbName)
        cursor = db.cursor()
        try:
            termList = iPediaServer.findFullTextMatches(db, cursor, searchTerm, startOffset)
            if 0==len(termList):
                self.appendField(Fields.outNoResults, None)
            else:
                self.appendField(Fields.outPediaArticleTitle, searchTerm)
                text = encyclopedia.searchResultsByteCode(termList, lang, searchTerm, startOffset)
                self.outputPayloadField(Fields.outPediaSearchResults, text)
            return None
        finally:
            cursor.close()
            db.close()

    def handleGetQuotes(self, fieldName, fieldValue):
        (resultType, resultBody) = quotes.retrieveQuotes(fieldValue, self.getAvailableModulesForCurrentClientVersion())

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        if QUOTES_DATA == resultType:
            self.appendPayloadField(Fields.outQuotes, resultBody)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        return ServerErrors.moduleTemporarilyDown

    def handleGetFlights(self, fieldName, fieldValue):
        (resultType, resultBody) = flights.retrieveFlights(fieldValue)

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        if RESULTS_DATA == resultType:
            self.appendPayloadField(Fields.outFlights, resultBody)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if NO_CITY == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoCity)
            return None

        return ServerErrors.moduleTemporarilyDown

    def handleEBookSearch(self, fieldName, fieldValue):
        ss = fieldValue.split(";")
        if 2 != len(ss):
            return ServerErrors.invalidRequest

        if not ebooks.data_ready():
            return ServerErrors.moduleTemporarilyDown
        
        query, formats = map(string.strip, ss)

        type = ebooks.SEARCH_ANY
        tq = map(string.strip, query.split(":", 1))
        if 2 == len(tq):
            t, q = tq
            if t in ebooks.SEARCH_TYPES:
                type = t
                query = q

        docs = ebooks.find(query, formats, self.getAvailableModulesForCurrentClientVersion(), type)

        if docs is None:
            self.appendField(Fields.outNoResults)
            return None

        self.outputPayloadField(Fields.outEBookSearchResults, docs)

    def handleEBookDownload(self, fieldName, fieldValue):
        if not ebooks.data_ready():
            return ServerErrors.moduleTemporarilyDown

        try:
            name, data, author, title = ebooks.download(fieldValue.strip())
        except Exception, ex:
            log(SEV_EXC, exceptionAsStr(ex))
            return handleRetrieveFailed(fieldName, fieldValue, None)

        self.appendField(Fields.outEBookName, "; ".join((name, author, title)))
        self.outputPayloadField(Fields.outEBookDownload, data)

    def handleEBookVersion(self, fieldName, fieldValue):
        version = ebooks.database_version()
        self.appendField(fieldName, str(version))        

    def handleEBookBrowse(self, fieldName, fieldValue):
        if not ebooks.data_ready():
            return ServerErrors.moduleTemporarilyDown

        if fieldValue is None:
            fieldValue = ""

        opts = [x.strip() for x in fieldValue.split(";")]
        if len(opts) not in (1, 2, 4):
            return ServerErrors.malformedRequest

        if len(opts) == 1:
            type, level, index, formats = None, None, None, None
        elif len(opts) == 2:
            type, level, index, formats = opts[0], None, None, opts[1]
        else:
            type, level, index, formats = opts
            level, index = int(level), int(index)
            
        if (type is not None) and (type not in ebooks.BROWSE_TYPES):
            return ServerErrors.malformedRequest

        df = ebooks.browse(type, level, index, self.getAvailableModulesForCurrentClientVersion(), formats)
        self.appendPayloadField(fieldName, df)

    def handleGetEBayLogin(self, fieldName, fieldValue):
        if fieldValue is None or 0 == len(fieldValue):
            return ServerErrors.malformedRequest

        fieldValue = InfoManCrypto.decrypt_hexbin(fieldValue)
        resultType = eBay.retrieveLogin(fieldValue, self.userId)

        if EBAY_UNKNOWN_LOGIN == resultType:
            self.appendField(Fields.outEBayUnknownLogin)
            return None

        if EBAY_LOGIN_OK == resultType:
            self.appendField(Fields.outEBayLoginOk)
            return None

        if MODULE_DOWN == resultType:
            return ServerErrors.moduleTemporarilyDown

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        return ServerErrors.moduleTemporarilyDown

    def handleGetEBay(self, fieldName, fieldValue):
        resultType, resultBody = eBay.retrieveEBay(fieldValue, self.getAvailableModulesForCurrentClientVersion(), self.userId)

        if EBAY_DATA == resultType:
            self.appendPayloadField(Fields.outEBay, resultBody)
            # test if i can do this...
            if eBay.isTokenExpired(self.userId):
                self.appendField(Fields.outEBayPasswordRequest)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if EBAY_REQUEST_PASSWORD == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outEBayPasswordRequest)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        return ServerErrors.moduleTemporarilyDown

    def handleGetEBayNoCache(self, fieldName, fieldValue):
        resultType, resultBody = eBay.retrieveEBayNoCache(fieldValue, self.getAvailableModulesForCurrentClientVersion(), self.userId)

        if EBAY_DATA_NO_CACHE == resultType:
            self.appendPayloadField(Fields.outEBayNoCache, resultBody)
            # test if i can do this...
            if eBay.isTokenExpired(self.userId):
                self.appendField(Fields.outEBayPasswordRequest)
            return None

        if NO_RESULTS == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outNoResults)
            return None

        if EBAY_REQUEST_PASSWORD == resultType:
            assert(None==resultBody)
            self.appendField(Fields.outEBayPasswordRequest)
            return None

        if INVALID_REQUEST == resultType:
            return ServerErrors.malformedRequest

        return ServerErrors.moduleTemporarilyDown

    def handleFlickrPicturesUploaded(self, fieldName, fieldValue):
        return None

# Meta-data about fields. Elements in the tuple describing field are:
#   * handler functions for that request
#   * True if free request, False if not free (free mean: doesn't count towards
#     our lookup limit check in unregistered version)
#   * callback function called after sending data to client (i.e. after finishing
#     handling the request)
g_fieldsInfo = {
    Fields.protocolVersion    : (None, True, None),
    Fields.clientInfo         : (None, True, None),
    Fields.transactionId      : (None, True, None),
    Fields.cookie             : (None, True, None),
    Fields.getCookie          : (None, True, None),
    Fields.regCode            : (None, True, None),
    Fields.getRegCodeDaysToExpire : (InfoManProtocol.handleRegCodeDaysToExpireRequest, True, None),
    Fields.verifyRegCode      : (InfoManProtocol.handleVerifyRegistrationCodeRequest, True, None),
    Fields.getLatestClientVersion : (InfoManProtocol.handleGetLatestClientVersion, True, None),
    Fields.getMovies          : (InfoManProtocol.handleGetMovies, False, None),
    Fields.getRecipesList     : (InfoManProtocol.handleGetRecipesList, False, None),
    Fields.getRecipe          : (InfoManProtocol.handleGetRecipe, False, None),
    Fields.getWeather         : (InfoManProtocol.handleGetWeather, False, None),
    Fields.get411ReverseZip   : (InfoManProtocol.handleGet411ReverseZip, False, None),
    Fields.get411ReverseArea  : (InfoManProtocol.handleGet411ReverseArea, False, None),
    Fields.get411ZipByCity    : (InfoManProtocol.handleGet411ZipByCity, False, None),
    Fields.get411AreaByCity   : (InfoManProtocol.handleGet411AreaByCity, False, None),
    Fields.get411PersonSearch : (InfoManProtocol.handleGet411PersonSearch, False, None),
    Fields.get411ReversePhone : (InfoManProtocol.handleGet411ReversePhone, False, None),
    Fields.get411BusinessSearch : (InfoManProtocol.handleGet411BusinessSearch, False, None),
    Fields.get411BusinessSearchByUrl : (InfoManProtocol.handleGet411BusinessSearchByUrl, False, None),
    Fields.get411InternationalCodeSearch : (InfoManProtocol.handleGet411InternationalCodeSearch, False, None),
    Fields.getCurrentBoxOffice : (InfoManProtocol.handleGetCurrentBoxOffice, True, None),
    Fields.getDream            : (InfoManProtocol.handleGetDream,  True, None),
    Fields.getCurrencyConversion : (InfoManProtocol.handleCurrencyConversion, False, None),
    Fields.getJokesList          : (InfoManProtocol.handleGetJokesList, True, None),
    Fields.getJoke               : (InfoManProtocol.handleGetJoke, True, InfoManProtocol.afterGetJoke),
    Fields.getStocksList         : (InfoManProtocol.handleGetStocksList,  False, None),
    Fields.getStock              : (InfoManProtocol.handleGetStock, False, None),
    Fields.getStockByName        : (InfoManProtocol.handleGetStockByName, False, None),
    Fields.getStocksListValidateLast : (InfoManProtocol.handleGetStocksListValidateLast,  False, None),
    Fields.getGasPrices : (InfoManProtocol.handleGetGasPrices,  False, None),
    Fields.getHoroscope     : (InfoManProtocol.handleGetHoroscope,  True, None),
    Fields.getUrlListsOfBestsItem   : (InfoManProtocol.handleGetListsOfBestsItem,  False, None),
    Fields.getUrlListsOfBestsBrowse : (InfoManProtocol.handleGetListsOfBestsBrowse,  False, None),
    Fields.getUrlListsOfBestsSearch : (InfoManProtocol.handleGetListsOfBestsSearch,  False, None),
    Fields.getTvListingsProviders   : (InfoManProtocol.handleGetTvListingsProviders, True, None),
    Fields.getTvListings           : (InfoManProtocol.handleGetTvListings, False, None),
    Fields.getUrlLyricsItem        : (InfoManProtocol.handleGetLyricsItemDefinition, False, None),
    Fields.getUrlLyricsSearch      : (InfoManProtocol.handleGetLyricsSearchDefinition, False, None),
    Fields.getUrlAmazonBrowse      : (InfoManProtocol.handleGetAmazonBrowse, False, None),
    Fields.getUrlAmazonItem        : (InfoManProtocol.handleGetAmazonItem, False, None),
    Fields.getUrlAmazonSearch      : (InfoManProtocol.handleGetAmazonSearch, False, None),
    Fields.getUrlAmazonList        : (InfoManProtocol.handleGetAmazonList, False, None),
    Fields.getUrlAmazonWishList    : (InfoManProtocol.handleGetAmazonWishlist, False, None),
    Fields.getUrlDict              : (InfoManProtocol.handleDictionary, False, None),
    Fields.getUrlDictRandom        : (InfoManProtocol.handleDictionaryRandom, False, None),
    Fields.getUrlDictStats         : (InfoManProtocol.handleDictionaryStats, True, None),
    Fields.getUrlNetflixItem       : (InfoManProtocol.handleGetNetflixItem,  False, None),
    Fields.getUrlNetflixBrowse     : (InfoManProtocol.handleGetNetflixBrowse,  False, None),
    Fields.getUrlNetflixSearch     : (InfoManProtocol.handleGetNetflixSearch,  False, None),
    Fields.getUrlNetflixLogin      : (InfoManProtocol.handleGetNetflixLogin,  True, None),
    Fields.getUrlNetflixAdd        : (InfoManProtocol.handleGetNetflixAdd,  False, None),
    Fields.getUrlNetflixQueue      : (InfoManProtocol.handleGetNetflixQueue,  False, None),
    Fields.getUrlQuotes            : (InfoManProtocol.handleGetQuotes,  True, None),
    Fields.getUrlFlights           : (InfoManProtocol.handleGetFlights,  False, None),
    Fields.getUrlEBay              : (InfoManProtocol.handleGetEBay,  False, None),
    Fields.getUrlEBayLogin         : (InfoManProtocol.handleGetEBayLogin,  True, None),
    Fields.getUrlEBayNoCache       : (InfoManProtocol.handleGetEBayNoCache,  False, None),

    Fields.getUrlPediaTerm         : (InfoManProtocol.handlePediaTerm, False, None),
    Fields.getUrlPediaSearch       : (InfoManProtocol.handlePediaSearch, True, None),
    Fields.getUrlPediaRandom       : (InfoManProtocol.handlePediaRandom, True, None),
    Fields.getUrlPediaLangs        : (InfoManProtocol.handlePediaLangs, True, None),
    Fields.getUrlPediaStats        : (InfoManProtocol.handlePediaStats, True, None),

    Fields.getUrlEBookSearch       : (InfoManProtocol.handleEBookSearch, True, None),
    Fields.getUrlEBookDownload     : (InfoManProtocol.handleEBookDownload, True, None),
    Fields.getUrlEbookBrowse        : (InfoManProtocol.handleEBookBrowse, True, None),
    Fields.getUrlEbookHome        : (InfoManProtocol.handleEBookBrowse, True, None),
    Fields.ebookVersion               : (InfoManProtocol.handleEBookVersion, True, None),

    # we provide handler for flickrPicturesUploaded so that it could be logged without making special cases in fields handling
    Fields.flickrPicturesUploaded   : (InfoManProtocol.handleFlickrPicturesUploaded, True, None),
}

# return a handler function for a given field. None means there is no handler
# throws exception in case of invalid fieldName
def getFieldHandler(fieldName):
    global g_fieldsInfo
    return g_fieldsInfo[fieldName][0]

# return True if a given request is free (i.e. doesn't count towards our
# lookup limit in unregistered version)
def fFreeRequest(fieldName):
    global g_fieldsInfo
    return g_fieldsInfo[fieldName][1]

def getFieldAfterFinishCallback(fieldName):
    global g_fieldsInfo
    return g_fieldsInfo[fieldName][2]

def testAmazonKey(amazonOptionalFlagPresent):
    global g_fDisableAmazonModule
    resType, resBody = ourAmazon.retriveAmazonItemByAsin("B000062VXE",None)
    if resType == AMAZON_ITEM:
        return
    resType, resBody = ourAmazon.retriveAmazonItemByAsin("0825803853",None)
    if resType == AMAZON_ITEM:
        return
    resType, resBody = ourAmazon.retriveAmazonItemByAsin("B000002P72",None)
    if resType == AMAZON_ITEM:
        return
    # 3 times no data - do sth
    if amazonOptionalFlagPresent:
        print "Amazon module disabled"
        g_fDisableAmazonModule = True
        return
    else:
        print "Amazon key is not accepted by amazon.com"
        print "Set ARSLEXIS_LICENSE_KEY in parsers/ourAmazon.py"
        print "or give amazonkey in amazonkey.txt file in server directory"
        print "Server will be stoped"
        print "if you want start server anyway, please add -amazon-optional as parametr"
        sys.exit(0)

def startListsOfBestsCache(level):
    global g_listsOfBestsCache
    assert g_listsOfBestsCache == None
    g_listsOfBestsCache = ListsOfBestsCache(level)

def _ebooks_update_wrapper():
    try:
        print "started ebooks update"
        ebooks.update_all()
    except Exception, ex:
        log(SEV_EXC, exceptionAsStr(ex))

def _check_ebooks_update():
    thread.start_new_thread(_ebooks_update_wrapper, ()) 

def main():
    global g_acceptedLogSeverity, g_fDisableRegistrationCheck
    global g_fTestCrossModules

    if sys.platform == "win32":
        print "Warning: test me directly on the server!"

    fDemon = fDetectRemoveCmdFlag("-demon")
    if not fDemon:
        fDemon = fDetectRemoveCmdFlag("-daemon")

    if fDetectRemoveCmdFlag( "-verbose" ):
        arsutils.setLogSeverity(SEV_LOW)

    if fDetectRemoveCmdFlag( "-testCross" ):
        g_fTestCrossModules = True

    if fDetectRemoveCmdFlag( "-disableregcheck" ):
        g_fDisableRegistrationCheck = True

    dontUpdateEBooks = fDetectRemoveCmdFlag("-no-ebooks-update")

    fDbExists = False
    try:
        fDbExists = db.FDbExists()
    finally:
        db.deinitDatabase()
    if not fDbExists:
        print "infoman database doesn't exist. Use db.py to create it"
        sys.exit(0)
    readLatestClientVersions()
    testAmazonKey(fDetectRemoveCmdFlag( "-amazon-optional" ))

    dictionary.initDictionary()

    if fDetectRemoveCmdFlag( "-lob0" ):
        startListsOfBestsCache(0)
    elif fDetectRemoveCmdFlag( "-lob1" ):
        startListsOfBestsCache(1)
    else:
        startListsOfBestsCache(2)

    eBay.initEBay()

    try:
        iPediaServer.getAllDbInfos()

        for lang in iPediaServer.g_supportedLangs:
            dbInfo = iPediaServer.getLatestDbForLang(lang)
            if None != dbInfo:
                iPediaServer.setCurrDbForLang(lang, dbInfo)
    except:
        print "iPediaServer - missing, or error in getAllDbInfos()"

    if fDemon:
        arsutils.daemonize('/dev/null', os.path.join(multiUserSupport.getServerStorageDir(), 'infoman.log'), os.path.join(multiUserSupport.getServerStorageDir(), 'infoman.log'))

    port = multiUserSupport.getServerPort()
    log(SEV_MED, "Started InfoMan server on port %d\n" % port)
    thread.start_new_thread(currency_retrieve.startCurrencyCaching, ())

    if not dontUpdateEBooks:
        _check_ebooks_update()

    runServer(port, InfoManProtocol)

if __name__ == "__main__":
    main()

