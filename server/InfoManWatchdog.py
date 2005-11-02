import os, sys, string, re, socket, random, time, smtplib
import arsutils, multiUserSupport
import Fields
from InfoManServer import *

SERVER_PORT = multiUserSupport.getServerPort()
SERVER_USER = multiUserSupport.getServerUser()

PYTHON_EXEC = "python2.4"

# possible server states
# we can find the server process and it responds to our ping request
STATE_ALIVE = 0
# we can find the server process but it doesn't respond to our poing request
# (too busy?)
STATE_NOT_RESPONDING = 1
# we can't find the server process
STATE_DEAD = 2

def stateName(state):
    if STATE_ALIVE == state:
        return "STATE_ALIVE"

    if STATE_NOT_RESPONDING == state:
        return "STATE_NOT_RESPONDING"

    if STATE_DEAD == state:
        return "STATE_DEAD"

    return "UNKNOWN"

# this is bunch of code copied from client.py
g_serverState = None
g_cookie = None

def getGlobalCookie():
    global g_cookie
    return g_cookie

g_DeviceInfoForTests    = "PN4e6f742061206e756d626572:PL7465737420636c69656e74"

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

def getServerNamePort():
    global SERVER_PORT
    name = "infoman.arslexis.com"
    port = SERVER_PORT
    port = int(port)
    return (name,port)

def getResponseFromServer(req):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    (serverName, serverPort) = getServerNamePort()
    sock.connect((serverName,serverPort))
    sock.sendall(req)
    sock.shutdown(1)
    response = socket_readAll(sock)
    sock.close()
    return response

def parseServerResponse(response):
    result = {}
    rest = response
    while True:
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
            result[field] = payload
            rest = rest[payloadLen:]
            assert '\n'==rest[0]
            rest = rest[1:]
            if 0==len(rest):
                return result
        else:
            result[field] = value

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
        return self.responseDict[field]

    def getText(self):
        return self.responseTxt

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
        return self.rspTxt

    def getRspField(self):
        return self.rsp

    def addField(self, fieldName, fieldValue):
        self.req.addField(fieldName, fieldValue)

    def ping(self):
        self.newRequestWithCookie()
        self.getResponse()

def fServerRespondsToPing():
    c = Client()
    c.ping()
    if c.rspCorrectTransactionId():
        return True
    return False

def fServerProcesRunning():
    pidOwnerList = arsutils.pids(PYTHON_EXEC, "InfoManServer.py")
    user = os.environ["USER"] # who am i
    userId = os.getuid()
    fRunning = False
    for [pid,owner] in pidOwnerList:
        if owner == user or owner == userId:
            fRunning = True
            break
    return fRunning

def currentServerState():
    if not fServerProcesRunning():
        return STATE_DEAD
    if not fServerRespondsToPing():
        return STATE_NOT_RESPONDING
    return STATE_ALIVE

# How often do we check that the server is alive
SERVER_STATE_CHECK_FREQUENCY = 30 # 30 seconds

# How often do we send e-mails about server being down?
# We don't want to flood ourselves with e-mail
SERVER_DOWN_UPDATE_MAIL_FREQENCY = 60*60 # not more often than every hour

# FOR TESTING ONLY: 1 min
#SERVER_DOWN_UPDATE_MAIL_FREQENCY = 60

# list of e-mail addresses to which send the e-mail
#EMAILS_TO_NOTIFY_ABOUT_SERVER_STATE = ["krzysztofk@pobox.com", "kjk@arslexis.com", "kkowalczyk@gmail.com", "szknitter@wp.pl", "smiech@op.pl", "szknitter@mail.ru", "a.ciarkowski@interia.pl"]
EMAILS_TO_NOTIFY_ABOUT_SERVER_STATE = ["krzysztofk@pobox.com", "kjk@arslexis.com", "kkowalczyk@gmail.com"]
# this is our rackshack server
#MAILHOST = "ipedia.arslexis.com"
MAILHOST = "127.0.0.1"
FROM = "infoman@infoman.arslexis.com"

userName = multiUserSupport.getServerUser()
# one of us?
if "infoman-kjk"== userName:
    EMAILS_TO_NOTIFY_ABOUT_SERVER_STATE = ["krzysztofk@pobox.com"]
if "infoman-szymon"== userName:
    EMAILS_TO_NOTIFY_ABOUT_SERVER_STATE = ["arslexis@wp.pl, arslexis@op.pl, arslexis@mail.ru"]
if "infoman-andrzej"== userName:
    EMAILS_TO_NOTIFY_ABOUT_SERVER_STATE = ["a.ciarkowski@interia.pl"]

def sendEmail(subject, emailContent):
    global MAILHOST, FROM, EMAILS_TO_NOTIFY_ABOUT_SERVER_STATE
    if None == MAILHOST:
        return
    body = string.join((
        "From: %s" % FROM,
        "To: %s" % string.join(EMAILS_TO_NOTIFY_ABOUT_SERVER_STATE,", "),
        "Subject: %s" % subject,
        "",
        emailContent), "\r\n")
    server = smtplib.SMTP(MAILHOST)
    try:
        server.sendmail(FROM, EMAILS_TO_NOTIFY_ABOUT_SERVER_STATE, body)
    except:
        pass
    server.quit()

# send an e-mail about server state at watchdog's startup
def emailImmediateStartupState(state):
    global SERVER_DOWN_UPDATE_MAIL_FREQENCY
    curTime = time.strftime( "%Y-%m-%d %H:%M:%S", time.localtime() )
    subject = "InfoMan watchdog for %s:%d, startup notice on %s" % (SERVER_USER, SERVER_PORT, curTime)
    body = "Time: %s\n" % curTime
    body += "Starting InfoMan watchdog. Server state at startup is %s\n" % stateName(state)
    body += "\n"
    body += "Update frequency: %d seconds" % SERVER_DOWN_UPDATE_MAIL_FREQENCY
    sendEmail(subject, body)

def fShouldEmailServerDownUpdate():
    global g_prevEmailUpdateTime, SERVER_DOWN_UPDATE_MAIL_FREQENCY
    if None == g_prevEmailUpdateTime:
        return True
    secondsSinceLastEmail = time.time() - g_prevEmailUpdateTime
    if secondsSinceLastEmail > SERVER_DOWN_UPDATE_MAIL_FREQENCY:
        return True
    return False

# when did we send previous server update e-mail?
g_prevEmailUpdateTime = None
def emailServerDownUpdate(state):
    global g_prevEmailUpdateTime, SERVER_DOWN_UPDATE_MAIL_FREQENCY
    assert state != STATE_ALIVE

    if not fShouldEmailServerDownUpdate():
        return

    curTime = time.strftime( "%Y-%m-%d %H:%M:%S", time.localtime() )
    subject = "InfoMan watchdog for %s:%d, server down notice on %s" % (SERVER_USER, SERVER_PORT, curTime)
    body = "Time: %s\n" % curTime
    body += "Server is down (state is %s)\n" % stateName(state)
    body += "\n"
    body += "Update frequency: %d seconds" % SERVER_DOWN_UPDATE_MAIL_FREQENCY
    sendEmail(subject, body)
    curTime = time.time()
    g_prevEmailUpdateTime = curTime

def emailImmediateServerStateChange(prevState, currState):
    assert prevState != currState
    curTime = time.strftime( "%Y-%m-%d %H:%M:%S", time.localtime() )
    subject = "InfoMan watchdog for %s:%d, server change state notice on %s" % (SERVER_USER, SERVER_PORT, curTime)
    body = "Time: %s\n" % curTime
    body += "Server changed the state from %s to %s" % (stateName(prevState), stateName(currState))
    sendEmail(subject, body)

if __name__ == '__main__':
    state = currentServerState()
    print stateName(state)

    # -nodeamon option is for testing, so that we see problem in the script code
    fNoDemon = arsutils.fDetectRemoveCmdFlag("-nodemon")
    if not fNoDemon:
        fNoDemon = arsutils.fDetectRemoveCmdFlag("-nodaemon")

    if not fNoDemon:
        arsutils.daemonize('/dev/null', '/dev/null')

    g_serverState = currentServerState()
    emailImmediateStartupState(g_serverState)

    while True:  # the only way to stop me is to kill me
        time.sleep(SERVER_STATE_CHECK_FREQUENCY)
        state = currentServerState()
        if state != g_serverState:
            emailImmediateServerStateChange(g_serverState, state)
            g_serverState = state
        elif state != STATE_ALIVE:
            emailServerDownUpdate(state)
