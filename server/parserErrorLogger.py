import string, time, sys, os, smtplib
import multiUserSupport
import ServerErrors

# this is our rackshack server
#MAILHOST = "ipedia.arslexis.com"
MAILHOST = "127.0.0.1"
FROM = "infoman@infoman.arslexis.com"

# this is the dir where we store parsing failures
def getParsingFailuresDir():
    result = os.path.join(multiUserSupport.getServerStorageDir(), "parsing-failures")
    return result

# list of e-mail addresses to which send the e-mail
def getEmailsToNotifyAboutParsingFailures():
    userName = multiUserSupport.getServerUser()
    addr = ["krzysztofk@pobox.com", "kkowalczyk@gmail.com"]
    #  addr = ["krzysztofk@pobox.com", "kkowalczyk@gmail.com", "szknitter@wp.pl", "smiech@op.pl", "szknitter@mail.ru", "a.ciarkowski@interia.pl"]
    # one of us?
    if "infoman-kjk"== userName:
        addr = ["krzysztofk@pobox.com"]
#    if "infoman-szymon"== userName:
#        addr = ["arslexis@wp.pl, arslexis@op.pl, arslexis@mail.ru"]
#    if "infoman-andrzej"== userName:
#        addr = ["a.ciarkowski@interia.pl"]
    return addr

lastFileNumber = -1

def mail(subject, emailContent):
    global MAILHOST, FROM
    if None == MAILHOST:
        return
    body = string.join((
        "From: %s" % FROM,
        "To: %s" % string.join(getEmailsToNotifyAboutParsingFailures(),", "),
        "Subject: %s" % subject,
        "",
        emailContent), "\r\n")
    if "win32" == sys.platform:
        # when running on a pc there's no point of sending e-mails since
        # we should just watch errors on the console
        print body
        return
    server = smtplib.SMTP(MAILHOST)
    try:
        server.sendmail(FROM, getEmailsToNotifyAboutParsingFailures(), body)
    except:
        pass
    server.quit()

def mailParsingFailure(fieldName, fieldValue, url, fileName=None):
    global MAILHOST
    if None == fieldValue:
        fieldValue = ""
    curDate = time.strftime( "%Y-%m-%d", time.localtime() )
    userName = multiUserSupport.getServerUser()
    subject = "InfoMan parsing failure notification %s for %s" % (curDate, userName)
    emailContent = "Server: %s on port %d\n" % (multiUserSupport.getServerUser(), multiUserSupport.getServerPort())
    txt = "InfoMan failed to parse results for query:\n%s: %s\n" % (fieldName, fieldValue)
    if None != url:
        txt = "%surl=%s\n" % (txt, url)
    if None != fileName:
        txt = "%sMore info is in file %s\n" % (txt, fileName)
    mail(subject, txt)

def mailRetrieveFailure(fieldName, fieldValue, url):
    global MAILHOST
    if None == fieldValue:
        fieldValue = ""
    curDate = time.strftime( "%Y-%m-%d", time.localtime() )
    userName = multiUserSupport.getServerUser()
    subject = "InfoMan retrieve failure notification %s for %s" % (curDate, userName)
    emailContent = "Server: %s on port %d\n" % (multiUserSupport.getServerUser(), multiUserSupport.getServerPort())
    txt = "InfoMan failed to retrieve results for query:\n%s: %s\n" % (fieldName, fieldValue)
    if None != url:
        txt = "%surl=%s\n" % (txt, url)
    mail(subject, txt)

# recursive function that makes given path (if exists exit)
def makePathIfNeeded(path):
    assert path != None
    if 0 == os.access(path, os.F_OK):
        (head,tail) = os.path.split(path)
        makePathIfNeeded(head)
        os.mkdir(path)

# returns file name
def getParsingFailureFileName():
    global lastFileNumber
    fileName = "0000.log"
    makePathIfNeeded(getParsingFailuresDir())
    if -1 == lastFileNumber:
        namesList = os.listdir(getParsingFailuresDir())
        if 0 != len(namesList):
            lastFile = namesList[-1]
            number = int(lastFile[:4])
            if number > 9999:
                number = -1
            lastFileNumber = number
            fileName = str(number+1).zfill(4) + ".log"
        lastFileNumber += 1
    else:
        # remember: you can't delete path!!! (errors)
        # you can delete files. but next file name will not be '0000.log'!
        lastFileNumber += 1
        if lastFileNumber > 9999:
            lastFileNumber = 0
        fileName = str(lastFileNumber).zfill(4) + ".log"

    return str(os.path.join(getParsingFailuresDir(), fileName))

# returns file name
def writeParsingFailure(fieldName, fieldValue, url, htmlText):
    fileName = getParsingFailureFileName()
    fo = open(fileName,"wt")
    textList = [fieldName, fieldValue, url, htmlText]
    for i in range(len(textList)):
        if None==textList[i]:
            textList[i] = ""
    fo.write(string.join(textList,"\n"))
    fo.close()
    return fileName

# logs the fact that parsing of a given html failed. field/fieldValue identifies
# the request (and gives enough information for us to re-get the html), htmlText
# is the html that we failed to parse and url is (optional) url that was the
# source of the htmlText
# For each parsing failure create a new file named 0000.log, 0001.log, 0002.log
# etc. i.e. each new file gets incrementally bigger number. The format of the
# file is:
# fieldName
# fieldValue
# url, "None" if not given
# the rest is htmlText
# Notes:
# - at startup we need to figure out what's the biggest log file number currently
#   and keep it in a global variable
# - we probably need locking to serialize writes and prevent problems due to
#   multi-threading e.g. multiple threads trying to write to the same file
# also send an e-mail informing about each parsing failure. For example of
# how to send e-mails from Python see ipedia\tools\dl_wikipedia.py
def logParsingFailure(fieldName, fieldValue, htmlText="", url=None):
    fileName = writeParsingFailure(fieldName, fieldValue, url, htmlText)
    mailParsingFailure(fieldName, fieldValue, url, fileName)

# TODO: those two names are too similar
def logParsingFailed(fieldName, fieldValue, resultBody):
    url = resultBody[0]
    htmlText = resultBody[1]
    fileName = writeParsingFailure(fieldName, fieldValue, url, htmlText)
    mailParsingFailure(fieldName, fieldValue, url, fileName)

def handleParsingFailed(fieldName, fieldValue, resultBody):
    logParsingFailed(fieldName, fieldValue, resultBody)
    return ServerErrors.moduleTemporarilyDown

def logRetrieveFailed(fieldName, fieldValue, resultBody):
    url = resultBody
    mailRetrieveFailure(fieldName, fieldValue, url)

def handleRetrieveFailed(fieldName, fieldValue, resultBody):
    logRetrieveFailed(fieldName, fieldValue, resultBody)
    return ServerErrors.moduleTemporarilyDown
