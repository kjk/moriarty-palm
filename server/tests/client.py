# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk
#
# Emulates client (Palm) application by issuing requests to the server.
# For testing the server.
#
import sys, string, re, socket, random, pickle, time
import arsutils, Fields
from InfoManServer import *

# server string must be of form "name:port"
g_serverList = {
    "pc" : "localhost:4000",
    "official" : "infoman.arslexis.com:4000",
    "szymon" : "infoman.arslexis.com:5010",
    "andrzej" : "infoman.arslexis.com:5012",
    "kjk" : "infoman.arslexis.com:5014",
    }

# a list of cookies per server
g_cookies = {}

g_serverToUse = None

# if set to true, we show raw output that server sends
# otherwise, show pretty-printed version more readable for humans
# controlled by -showraw command-line option
g_showRawOutput = None

# make g_DeviceInfoForTests unique (so that we don't pollute users table)
# set PL (platform) to "test client"
g_DeviceInfoForTests    = "PN4e6f742061206e756d626572:PL7465737420636c69656e74"
g_uniqueDeviceInfo      = "PN70686f6e79206e756d626572:PL50616C6D"
g_nonUniqueDeviceInfo   = "OC70616C6D:OD00000000:PL50616C6D"

def strToHex(txt):
    res = ""
    for c in txt:
        hx = hex(ord(c))
        res += hx[2:]
    return res

# current version of the article body format returned by the client
CUR_FORMAT_VER = "1"

# convert data returned by server to a format that is more readable for humans
def listPrettyPrint(txt):
    headers = ""
    restTxt = txt
    while True:
        # a bit of a hack: filter out headers i.e. lines that contain ":"
        (line,restTxt) = restTxt.split("\n",1)
        if -1 == line.find(":"):
            break
        headers = "%s\n%s" % (headers,line)
    # the first line that is not a header should be
    listsNo = int(line)
    result = "Number of lists: %d\n" % listsNo

    listItemsLen = []
    for l in range(listsNo):
        (line,restTxt) = restTxt.split("\n",1)
        itemsLenTxt = line.split(" ")
        itemsLen = [int(itemLenTxt) for itemLenTxt in itemsLenTxt]
        listItemsLen.append(itemsLen)

    listNo = 0
    txtStart = 0
    for itemsLen in listItemsLen:
        result += "** list %d\n" % listNo
        for itemLen in itemsLen:
            txt = restTxt[txtStart:txtStart+itemLen]
            result += "  %s\n" % txt
            txtStart = txtStart + itemLen + 1
        listNo += 1
    #result += restTxt
    return result

g_pickleFileName = "client_pickled_data.dat"
def pickleState():
    global g_pickleFileName,g_cookies
    # save all the variables that we want to persist across session on disk
    fo = open(g_pickleFileName, "wb")
    pickle.dump(g_cookies,fo)
    fo.close()

def unpickleState():
    global g_cookies, g_pickleFileName
    # restores all the variables that we want to persist across session from
    # the disk
    try:
        fo = open(g_pickleFileName, "rb")
    except IOError:
        # it's ok to not have the file
        return
    g_cookies = pickle.load(fo)
    fo.close()

def getGlobalCookie():
    global g_cookies
    if g_cookies.has_key(g_serverToUse):
        #print "found cookie: %s" % g_cookies[g_serverToUse]
        return g_cookies[g_serverToUse]
    return None

def printUsedServer():
    srv = g_serverList[g_serverToUse]
    print "using server %s i.e. %s" % (g_serverToUse,srv)

def getServerNamePort():
    srv = g_serverList[g_serverToUse]
    (name,port) = srv.split(":")
    port = int(port)
    return (name,port)

def socket_readAll(sock):
    result = ""
    while True:
        data = sock.recv(10)
        if 0 == len(data):
            break
        result += data
    return result

class Request:
    def __init__(self, protocolVer="1", clientVer="Python testing client 1.0"):
        self.fields = []
        self.lines = []

        self.addField(Fields.protocolVersion, protocolVer)
        self.addField(Fields.clientInfo,      clientVer)
        self.addTransactionId()

    def addTransactionId(self):
        self.transactionId = "%x" % random.randint(0, 2**16-1)
        self.addField(Fields.transactionId,   self.transactionId)

    # we expose addLine() so that clients can also create malformed requests
    def addLine(self,line):
        self.lines.append(line)

    # we expose clearFields() so that clients can create malformed requests
    # (missing protocol version or transaction id or client info)
    def clearFields(self):
        self.fields = []
        self.lines = []

    def addField(self,fieldName,value):
        assert ':' != fieldName[-1]
        self.fields.append( (fieldName, value) )
        if None==value:
            self.addLine( "%s:\n" % fieldName)
        else:
            self.addLine( "%s: %s\n" % (fieldName,value))

    def getString(self):
        txt = string.join(self.lines , "" )
        txt += "\n"
        return txt

    def getText(self):
        txt = string.join(self.lines , "" )
        return txt

    def addCookie(self):
        global g_DeviceInfoForTests
        if getGlobalCookie():
            self.addField(Fields.cookie, getGlobalCookie())
        else:
            self.addField(Fields.getCookie, g_DeviceInfoForTests)

def getRequestHandleCookie(field=None,value=None):
    r = Request()
    r.addCookie()
    if field!=None:
        r.addField(field,value)
    return r

def getResponseFromServer(req):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    (serverName, serverPort) = getServerNamePort()
    sock.connect((serverName,serverPort))
    #print "Connected to server"
    #print "Sending:", req
    sock.sendall(req)
    sock.shutdown(1)
    #print "Sent all"
    response = socket_readAll(sock)
    #print "Received:", response
    sock.close()
    return response

def parseServerResponse(response):
    result = {}
    rest = response
    while True:
        # print "rest: '%s'" % rest
        if 0==len(rest):
            return result
        parts = rest.split("\n",1)
        fld = parts[0]
        rest = None
        if len(parts)>1:
            rest = parts[1]
        if 0==len(fld):
            return result
        (field,value) = parseRequestLine(fld)
        if None == field:
            print "'%s' is not a valid request line" % fld
            return None
        if Fields.fPayloadField(field):
            payloadLen = int(value)
            payload = rest[:payloadLen]
            result[field] = [value, payload]
            # print "! found field '%s'" % field
            rest = rest[payloadLen:]
            assert '\n'==rest[0]
            rest = rest[1:]
            if 0==len(rest):
                return result
        else:
            result[field] = value
            # print "! found field '%s'" % field

        if None == rest:
            return result

class Response:
    def __init__(self,request):
        # request can be either a string or class Request
        assert request
        if isinstance(request, Request):
            self.txt = request.getString()
        else:
            self.txt = request
        self.responseTxt = getResponseFromServer(self.txt)
        self.responseDict = parseServerResponse(self.responseTxt)
        if None == self.responseDict:
            # TODO: throw an exception
            print "FAILURE in parseServerResponse"
            sys.exit(0)

    def getFields(self):
        return self.responseDict.keys()

    def hasField(self,field):
        assert ':' != field[-1]
        return self.responseDict.has_key(field)

    def hasFields(self,fields):
        for f in fields:
            if not self.hasField(f):
                return False
        return True

    def getField(self,field):
        assert ':' != field[-1]
        fieldValue = self.responseDict[field]
        if isinstance(fieldValue, list):
            return fieldValue[1]
        else:
            return fieldValue

    def getFieldShort(self,field):
        assert ':' != field[-1]
        fieldValue = self.responseDict[field]
        if isinstance(fieldValue, list):
            return fieldValue[0]
        else:
            return fieldValue

    def getText(self):
        return self.responseTxt

    # like getText() except doesn't return the whole value of payload field,
    # just the first line
    def getShortText(self):
        res = []
        for (fieldName,fieldValue) in self.responseDict.items():
            if None != fieldValue:
                if isinstance(fieldValue, list):
                    fieldValue = fieldValue[0]
                res.append( "%s: %s" % (fieldName, fieldValue))
            else:
                res.append( fieldName )
        return string.join(res, "\n")

    def errorResponse(self):
        if self.hasField(Fields.error):
            return True
        return False

def handleCookie(rsp):
    global g_cookies
    if not getGlobalCookie() and rsp.hasField(Fields.cookie):
        #print "Found cookie: %s" % rsp.getField(Fields.cookie)
        g_cookies[g_serverToUse] = rsp.getField(Fields.cookie)
        pickleState()

class Client:
    def __init__(self):
        pass

    def newRequest(self):
        self.req = Request()

    def newRequestWithCookie(self):
        self.req = getRequestHandleCookie()

    def rspHasTransactionId(self):
        if self.rsp.hasField(Fields.transactionId):
            return True
        return False

    def rspCorrectTransactionId(self):
        if not self.rspHasTransactionId():
            return False
        if self.rsp.getField(Fields.transactionId) == self.req.transactionId:
            return True
        return False

    def getResponse(self):
        self.reqTxt = self.req.getString()
        self.rsp = Response(self.req)
        self.rspTxt = self.rsp.getText()

    def getReqString(self):
        return self.reqTxt

    def getRspString(self):
        global g_showRawOutput

        if g_showRawOutput or self.rsp.errorResponse():
            txt = self.rspTxt
        else:
            txt = listPrettyPrint(self.rspTxt)
        return txt

    def getRspRawString(self):
        return self.rspTxt

    def getRspField(self):
        return self.rsp

    def addField(self, fieldName, fieldValue):
        self.req.addField(fieldName, fieldValue)

    def malformed(self):
        self.newRequestWithCookie()
        # malformed, because there is no ":"
        self.req.addLine("malfromed\n")
        self.getResponse()

    def ping(self):
        self.newRequestWithCookie()
        self.getResponse()

    def invalidCookie(self):
        self.newRequest()
        self.addField(Fields.cookie, "blah")
        self.getResponse()

    def getJokeInvalid(self):
        self.newRequestWithCookie()
        self.addField(Fields.getJoke, "not needed arg")
        self.getResponse()

    def getMovies(self,location):
        self.newRequestWithCookie()
        self.addField(Fields.getMovies, location)
        self.getResponse()

    def getRecipeList(self,query):
        self.newRequestWithCookie()
        self.addField(Fields.getRecipesList, query)
        self.getResponse()

    def getRecipe(self,recipe):
        self.newRequestWithCookie()
        self.addField(Fields.getRecipe, recipe)
        self.getResponse()

    def getWeather(self,location):
        self.newRequestWithCookie()
        self.addField(Fields.getWeather, location)
        self.getResponse()

    def get411Person(self,txt):
        self.newRequestWithCookie()
        self.addField(Fields.get411PersonSearch, txt)
        self.getResponse()

    def get411RevPhone(self,txt):
        self.newRequestWithCookie()
        self.addField(Fields.get411ReversePhone, txt)
        self.getResponse()

    def getRandomJoke(self):
        self.newRequestWithCookie()
        self.addField(Fields.getJoke, "random")
        self.getResponse()

    def getCurrency(self,curr):
        self.newRequestWithCookie()
        self.addField(Fields.getCurrencyConversion, curr)
        self.getResponse()

    def getAmazonItem(self, asin):
        self.newRequestWithCookie()
        self.addField(Fields.getAmazonItem, asin)
        self.getResponse()

    def getLyricsSearch(self, query):
        self.newRequestWithCookie()
        self.addField(Fields.getLyricsSearch, query)
        self.getResponse()

    def getDict(self, query):
        self.newRequestWithCookie()
        self.addField(Fields.getUrlDict, query)
        self.getResponse()

    def getAmazonBrowse(self,search_index,node):
        self.newRequestWithCookie()
        self.addField(Fields.getAmazonBrowse, search_index + ";" + node + ";1")
        self.getResponse()

    def getClientVersion(self, clientName):
        self.newRequestWithCookie()
        self.addField(Fields.getLatestClientVersion, clientName)
        self.getResponse()

def doMalformed():
    c = Client()
    c.malformed()
    print c.getReqString()
    print c.getRspString()

def doPing():
    c = Client()
    c.ping()
    assert c.rspCorrectTransactionId()
    print c.getReqString()
    print c.getRspString()

def doJokeInvalid():
    c = Client()
    c.getJokeInvalid()
    print c.getReqString()
    print c.getRspString()

def doInvalidCookie():
    c = Client(False)
    c.invalidCookie()
    print c.getReqString()
    print c.getRspString()
    assert c.rspCorrectTransactionId()

def doMovies(location):
    c = Client()
    c.getMovies(location)
    print c.getReqString()
    print c.getRspString()

def doRecipeList(query):
    c = Client()
    c.getRecipeList(query)
    print c.getReqString()
    print c.getRspString()

def doRecipe(recipe):
    c = Client()
    recipeTxt = "/recipes/recipe_views/views/%s" % recipe
    c.getRecipe(recipeTxt)
    print c.getReqString()
    print c.getRspString()

def doWeather(location):
    c = Client()
    c.getWeather(location)
    print c.getReqString()
    print c.getRspString()

def do411Person(txt):
    c = Client()
    c.get411Person(txt)
    print c.getReqString()
    print c.getRspString()

def do411ReversePhone(txt):
    c = Client()
    c.get411RevPhone(txt)
    print c.getReqString()
    print c.getRspString()

def doRandomJoke():
    c = Client()
    c.getRandomJoke()
    print c.getReqString()
    print c.getRspString()

def doCurrency(curr):
    c = Client()
    c.getCurrency(curr)
    print c.getReqString()
    print c.getRspString()

def doAmazonItem(asin):
    c = Client()
    c.getAmazonItem(asin)
    print c.getReqString()
    print c.getRspString()

def doLyricsSearch(query):
    c = Client()
    c.getLyricsSearch(query)
    print c.getReqString()
    print c.getRspString()

def doDict(query):
    c = Client()
    c.getDict(query)
    print c.getReqString()
    print c.getRspString()


ALL_CLIENTS = ["Palm"]
def doClientVersion():
    for clientName in ALL_CLIENTS:
        c = Client()
        c.getClientVersion(clientName)
        print c.getReqString()
        print c.getRspString()

argsInfo = {
    "ping" : (0, doPing),
    "malformed" : (0, doMalformed),
    "movies" : (1, doMovies),
    "jokeinvalid" : (0, doJokeInvalid),
    "recipelist" : (1, doRecipeList),
    "recipe" : (1, doRecipe),
    "weather" : (1, doWeather),
    "411person" : (1, do411Person),
    "411revphone" : (1, do411ReversePhone),
    "jokerandom" : (0, doRandomJoke),
    "curr" : (1, doCurrency),
    "currency" : (1, doCurrency),
    "amazonItem" : (1, doAmazonItem),
    "lyricsSearch" : (1, doLyricsSearch),
    "clientVersion" : (0, doClientVersion),
    "dict" : (1, doDict),
}

def buildUsage():
    global argsInfo
    allArgs = argsInfo.keys()
    allArgs.sort()
    txt = ""
    for arg in allArgs:
        numArgs = argsInfo[arg][0]
        if numArgs > 0:
            txt = "%s [%s $%d]" % (txt, arg, numArgs)
        else:
            txt = "%s [%s]" % (txt, arg)
    return txt

def usageAndExit():
    print "client.py $server %s" % buildUsage()

def getIndexSafe(arr, obj):
    pos = None
    try:
        pos = arr.index(obj)
    except:
        pass
    return pos

# based on the computer used, set g_defaultServer to use for client.py and
# server unit testing
def detectAndSetServerToUse():
    global g_serverToUse
    if sys.platform != "win32":
        print "client.py/detectServerToUse(): I only know how to detect on Windows!"
        sys.exit(0)
    computerName = os.environ["COMPUTERNAME"]
    if "DVD" == computerName:
        g_serverToUse = "kjk"
    elif "DVD2" == computerName:
        g_serverToUse = "kjk"
    elif "KJKLAP1" == computerName:
        g_serverToUse = "kjk"
    elif "TLAP" == computerName:
        g_serverToUse = "kjk"
    elif "RABBAN" == computerName:
        g_serverToUse = "andrzej"
    elif "GIZMO" == computerName:
        g_serverToUse = "pc"
    else:
        print "Don't know the server for computer %s" % computerName
        sys.exit(0)

if __name__=="__main__":
    serverToUse = None
    serverToUse = arsutils.getRemoveCmdArg("-server")
    if None == serverToUse:
        detectAndSetServerToUse()
    else:
        if not g_serverList.has_key(serverToUse):
            print "server %s is not known. Known servers:" % serverToUse
            for serverName in g_serverList.keys():
                print "   %s" % serverName
            sys.exit(0)
        else:
            g_serverToUse = serverToUse

    if arsutils.fDetectRemoveCmdFlag("-raw"):
        g_showRawOutput = True

    printUsedServer()
    unpickleState()
    pos = None
    for argName in argsInfo.keys():
        pos = getIndexSafe(sys.argv, argName)
        if None != pos:
            break

    if None == pos:
        usageAndExit()
        sys.exit(0)

    numArgs = argsInfo[argName][0]
    func = argsInfo[argName][1]
    if 0 == numArgs:
        func()
    elif 1 == numArgs:
        argOne = sys.argv[pos+1]
        func(argOne)
    elif 2 == numArgs:
        argOne = sys.argv[pos+1]
        argTwo = sys.argv[pos+2]
        func(argOne, argTwo)
    else:
        # not handled yet
        assert(False)
