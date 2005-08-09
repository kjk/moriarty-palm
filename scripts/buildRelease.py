# Owner: Krzysztof Kowalczyk
# Purpose:
#  Build all files required for a new release of InfoMan:
#  - build shipping version of InfoMan.prc
#  - build shipping version of InfoMan.prc for PalmGear
#  - build InfoMan.zip for our website
#  - build Infoman.zip for PalmGear
#  - print the *.prc version to stdout (for easy double-checking that
#    the version is correct)
#
#  Requirements:
#  - website docs must already exist
import sys, os, os.path, string, subprocess, StringIO, cStringIO, bz2, time, traceback, smtplib

g_mailTxt = []
def logToMail(txt):
    global g_mailTxt
    g_mailTxt.append(txt)

compName = os.environ["COMPUTERNAME"]

g_fBuildDone = False

# list of e-mail addresses to which send the e-mail

MAIL_TO_ALL     = ["krzysztofk@pobox.com", "kkowalczyk@gmail.com", "szknitter@wp.pl", "a.ciarkowski@interia.pl"]
MAIL_TO_JUST_ME = ["krzysztofk@pobox.com", "kkowalczyk@gmail.com"]

# MAIL_HOST must be set as an environment variable e.g. "127.0.0.1"
MAIL_HOST = None
if os.environ.has_key("MAIL_HOST"):
    MAIL_HOST = os.environ["MAIL_HOST"]

# MAIL_USER must be set as an env variable
MAIL_USER = None
if os.environ.has_key("MAIL_USER"):
    MAIL_PWD = os.environ["MAIL_USER"]

MAIL_PWD = None
# MAIL_PWD must be set as an env variable
if os.environ.has_key("MAIL_PWD"):
    MAIL_PWD = os.environ["MAIL_PWD"]

CW_PATH = "C:\\Progra~1\\Metrowerks\\CodeWarrior\\Bin\\IDE.exe"

if compName in ["TLAP", "DVD2"]:
    REPO_ARS_FRAMEWORK = "C:\\kjk\\src\\mine\\ars_framework"
    REPO_INFOMAN = "C:\\kjk\\src\\mine\\moriarty_palm"
    REPO_IPEDIA = "C:\\kjk\\src\\mine\\ipedia"
    # REPO_INOAH = "C:\\kjk\\src\\mine\\inoah"
    # TODO: REPO_SM_INOAH, REPO_SM_IPEDIA, REPO_NOAH_PRO, REPO_NOAH_LITE, REPO_THES
    BUILD_ARCHIVE_PATH = "c:\\kjk\\builds"
    LOG_PATH="c:\\kjk\\builds\\log.txt"
elif "DVD" == compName:
    REPO_ARS_FRAMEWORK = "C:\\kjk\\src\\mine\\ars_framework"
    REPO_INFOMAN = "C:\\kjk\\src\\mine\\moriarty_palm"
    REPO_IPEDIA = "C:\\kjk\\src\\mine\\ipedia"
    # REPO_INOAH = "C:\\kjk\\src\\mine\\inoah"
    BUILD_ARCHIVE_PATH = "e:\\builds"
    LOG_PATH="e:\\builds\\log.txt"
else:
    print "unkown machine"
    sys.exit(0)

INFOMAN_MCP = os.path.join(REPO_INFOMAN, "moriarty.mcp")

SHIPPING_TYPE = "Shipping"
PALMGEAR_TYPE = "Shipping PalmGear"

SUPPORTED_INFOMAN_TYPES = [SHIPPING_TYPE, PALMGEAR_TYPE]

def fDetectRemoveCmdFlag(flag):
    fFlagPresent = False
    try:
        pos = sys.argv.index(flag)
        fFlagPresent = True
        sys.argv[pos:pos+1] = []
    except:
        pass
    return fFlagPresent

def sendEmail(subject, emailContent, mailTo):
    global g_mailTxt, MAIL_HOST, MAIL_PWD
    MAIL_FROM = "buildbot@arslexis.com"
    if None == MAIL_HOST or None == MAIL_USER or None == MAIL_PWD:
        return
    body = string.join((
        "From: %s" % MAIL_FROM,
        "To: %s" % string.join(MAIL_TO,", "),
        "Subject: %s" % subject,
        "",
        emailContent), "\r\n")
    try:
        server = smtplib.SMTP(MAIL_HOST)
        server.login(MAIL_USER, MAIL_PWD)
        server.sendmail(MAIL_FROM, mailTo, body)
        server.quit()
    except Exception, ex:
        print "Failed to send e-mail"
        print str(ex)
    print "sent e-mail"

def emailErrors():
    global g_mailTxt
    if 0 == len(g_mailTxt):
        subject = "Build succesful"
        body = "build succesful on %s" % time.strftime( "%Y-%m-%d_%H-%M", time.localtime() )
        mailTo = MAIL_TO_JUST_ME
    else:
        subject = "Build errors"
        body = "Build tried on %s\n" % time.strftime( "%Y-%m-%d_%H-%M", time.localtime())
        body += string.join( g_mailTxt, "\n")
        mailTo = MAIL_TO_ALL
    sendEmail(subject, body, mailTo)

def printErrors():
    if 0 == len(g_mailTxt):
        return
    txt = string.join(g_mailTxt, "\n")
    print txt

def exceptionAsStr(e):
    exc_info = sys.exc_info()
    s = string.join(apply(traceback.format_exception, exc_info), "\n")
    return s

# do svn update in a given repository path and return true
# if any files were updated
def updateSvn(svnRepoPath):
    try:
        os.chdir(svnRepoPath)
    except:
        txt = "updateSvn(): failed to os.chdir(%s)" % svnRepoPath
        print txt
        logToMail(txt)
        return False
    stdoutTxt = ""
    stderrTxt = ""
    try:
        proc = subprocess.Popen(["svn", "update"], stdout=subprocess.PIPE)
        (stdoutTxt, sterrTxt) = proc.communicate()
    except Exception, ex:
        print exceptionAsStr(ex)
        logToMail("updateSvn(): failed to execute 'svn update' in dir %s" % svnRepoPath)
        return False
    # print "result of svn update,\nstdout='%s'\nstderr='%s'" % (stdoutTxt, stderrTxt)
    # svn update returns (in stdout) "At revision $revNumber." if there was no update
    # or something else if there was an update
    fUpdated = True
    if 0 == string.find(stdoutTxt, "At revision"):
        fUpdated = False
    return fUpdated

def updateArsFramework():
    return updateSvn(REPO_ARS_FRAMEWORK)

def updateInfoMan():
    return updateSvn(REPO_INFOMAN)

# build release project by invoking IDE and return
# (errorCode, stringDsc)
# if errorCode is != 0 then the build failed
def buildFlickr(type):
    if type not in ["Release"]:
        txt = "buildFlickr: %s is not supported build type" % type
        return (1, txt)
    try:
        retcode = subprocess.call([CW_PATH, FLICKR_MCP, "/t", type, "/b", "/r", "/c", "/q", "/s"])
        if retcode < 0:
            return (-retcode, None)
        else:
            return (retcode, None)
    except Exception, ex:
        txt = exceptionAsStr(ex)
        return (1, txt)

# build release project by invoking IDE and return
# (errorCode, stringDsc)
# if errorCode is != 0 then the build failed
def buildInfoMan(type):
    if type not in SUPPORTED_INFOMAN_TYPES:
        txt = "buildInfoMan: %s is not supported build type" % type
        return (1, txt)
    try:
        retcode = subprocess.call([CW_PATH, INFOMAN_MCP, "/t", type, "/b", "/r", "/c", "/q", "/s"])
        if retcode < 0:
            return (-retcode, None)
        else:
            return (retcode, None)
    except Exception, ex:
        txt = exceptionAsStr(ex)
        return (1, txt)

def buildFullInfoMan(type):
    flickrType = "Release"
    #print "building %s flickr and %s infoman" % (flickrType, type)
    (errCode, errTxt) = buildFlickr(flickrType)
    #print "errCode: %d" % errCode
    if 0 != errCode:
        txt = "failed to build InfoMan Flickr %s, errorCode=%s, errorTxt='%s'" % (flickrType, errCode, errTxt)
        logToMail(txt)
        return (errCode, errTxt)

    (errCode, errTxt) = buildInfoMan(type)
    print "errCode: %d" % errCode
    if 0 != errCode:
        txt = "failed to build InfoMan %s, errorCode=%s, errorTxt='%s'" % (flickrType, errCode, errTxt)
        logToMail(txt)
        return (errCode, errTxt)

    return (errCode, errTxt)

def copyFile(srcPath, dstPath, fCompressed=False):
    foSrc = None
    foDest = None
    if fCompressed:
        dstPath = dstPath + ".bz2"
    try:
        foSrc = open(srcPath, "rb")
        if fCompressed:
            foDest = bz2.BZ2File(dstPath, "wb")
        else:
            foDest = open(dstPath, "wb")
        while True:
            buf = foSrc.read(4096)
            if 0 == len(buf):
                break
            foDest.write(buf)
    except Exception, ex:
        print exceptionAsStr(ex)

    if None != foSrc:
        foSrc.close()
    if None != foDest:
        foDest.close()        

DST_DIR = "c:\\kjk\\tmp\\InfoManRelease"

# cleanupDirIfExists will remove everything underneath dir but not
# the dir itself
# based on http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/193736
ERROR_STR= """Error removing %(path)s, %(error)s """
def rmgeneric(path, __func__):
    try:
        __func__(path)
        #print 'Removed ', path
    except OSError, (errno, strerror):
        print ERROR_STR % {'path' : path, 'error': strerror }

def cleanupDirIfExists(path):
    if not os.path.isdir(path):
        return
    files=os.listdir(path)
    for x in files:
        fullpath=os.path.join(path, x)
        if os.path.isfile(fullpath):
            f=os.remove
            rmgeneric(fullpath, f)
        elif os.path.isdir(fullpath):
            cleanupDirIfExists(fullpath)
            f=os.rmdir
            rmgeneric(fullpath, f)

# make sure that directory exists
def ensureDir(dir):
    if not os.path.isdir(dir):
        os.mkdir(dir)

# do all the work:
# - build shipping version for us and PalmGear
# - copy them to apropriate dirs
# - copy docs from www repository
# - build *.zip files
# - print *.prc version number for easy double-checking that version is correct
def buildRelease():

    #(errCode, errTxt) = buildFullInfoMan(SHIPPING_TYPE)
    #if 0 != errCode:
    #    print "failed to build infoman of type %s, errCode=%s, errTxt=%s" % (SHIPPING_TYPE, str(errCode), errTxt)
    #    return

    #(errCode, errTxt) = buildFullInfoMan(PALMGEAR_TYPE)
    #if 0 != errCode:
    #    print "failed to build infoman of type %s, errCode=%s, errTxt=%s" % (PALMGEAR_TYPE, str(errCode), errTxt)
    #    return

    #time.sleep(10)
    #os.remove(FLICKR_MCP)
    #os.remove(INFOMAN_MCP)
    #updateInfoMan()

    cleanupDirIfExists(DST_DIR)
    ensureDir(DST_DIR)
    ensureDir(os.path.join(DST_DIR, "ArsLexis"))
    ensureDir(os.path.join(DST_DIR, "ArsLexis", "InfoMan"))
    ensureDir(os.path.join(DST_DIR, "PalmGear"))
    ensureDir(os.path.join(DST_DIR, "PalmGear", "InfoMan"))

    srcPath = os.path.join(REPO_INFOMAN, SHIPPING_TYPE, "InfoMan.prc")
    dstPath = os.path.join(DST_DIR, "ArsLexis", "InfoMan.prc")
    copyFile(srcPath, dstPath)
    dstPath = os.path.join(DST_DIR, "ArsLexis", "InfoMan", "InfoMan.prc")
    copyFile(srcPath, dstPath)

    srcPath = os.path.join(REPO_INFOMAN, PALMGEAR_TYPE, "InfoMan.prc")
    dstPath = os.path.join(DST_DIR, "PalmGear", "InfoMan.prc")
    copyFile(srcPath, dstPath)
    dstPath = os.path.join(DST_DIR, "PalmGear", "InfoMan", "InfoMan.prc")
    copyFile(srcPath, dstPath)

    # TODO: 
    # - copy the docs to InfoMan dirs
    # - zip the InfoMan directory into InfoMan.zip file
    # - print Infoman.prc version number

def main():
    buildRelease()

if __name__ == "__main__":
    main()
