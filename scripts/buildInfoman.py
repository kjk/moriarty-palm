# Owner: Krzysztof Kowalczyk
# Purpose:
#  Automatic build of all ArsLexis programs.
#
#  If invoked with -archive, it does the following:
#  - update svn repositories of all projects
#  - build all projects whose code has changed
#  - copy built files to builds archive directory, including map files
#  - if build failed, sen e-mail notifying about that
#  Builds are stamped with timestamp e.g. YY-MM-DD_HH-MM-InfoMan-Release.prc
#
#  Otherwise just builds all the targets.
#
# TODO: sometimes Codewarrior might popup a dialog and wait for an answer
# from the user. Since -daily and -archive are automatic, we have to
# have a way of killing such process e.g. by launching a separate thread
# to do the job and killing it if it doesn't finish in some reasonable
# time (e.g. 10 min)
# TODO: maybe also time how long does it take to build each type?
# TODO: add building of iPedia, iNoah, NoahPro, NoahLite, Thesaurus,
# sm_inoah, sm_ipedia, ppc_inoah, ppc_ipedia
import sys, os, os.path, string, subprocess, StringIO, cStringIO, bz2, time, traceback, smtplib

g_mailTxt = []
def logToMail(txt):
    global g_mailTxt
    g_mailTxt.append(txt)

compName = os.environ["COMPUTERNAME"]

g_fBuildDone = False

# list of e-mail addresses to which send the e-mail

MAIL_TO_JUST_ME = ["krzysztofk@pobox.com", "kkowalczyk@gmail.com"]
MAIL_TO_ALL     = MAIL_TO_JUST_ME

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

FLICKR_MCP = os.path.join(REPO_INFOMAN, "FlickrUploader", "FlickrUploader.mcp")
INFOMAN_MCP = os.path.join(REPO_INFOMAN, "moriarty.mcp")
IPEDIA_MCP = os.path.join(REPO_IPEDIA, "ipedia.mcp")

RELEASE_TYPE = "Release"
DEBUG_TYPE = "Debug"
SHIPPING_TYPE = "Shipping"
PALMGEAR_TYPE = "Shipping PalmGear"

SUPPORTED_FLICKR_TYPES  = [RELEASE_TYPE, DEBUG_TYPE]
SUPPORTED_INFOMAN_TYPES = [RELEASE_TYPE, DEBUG_TYPE, SHIPPING_TYPE, PALMGEAR_TYPE]
SUPPORTED_IPEDIA_TYPES  = [RELEASE_TYPE, DEBUG_TYPE]

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

def updateIpedia():
    return updateSvn(REPO_IPEDIA)

def updateInoah():
    return updateSvn(REPO_INOAH)
    
# build release project by invoking IDE and return
# (errorCode, stringDsc)
# if errorCode is != 0 then the build failed
def buildFlickr(type):
    if type not in SUPPORTED_FLICKR_TYPES:
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

def buildIpedia(type):
    if type not in SUPPORTED_IPEDIA_TYPES:
        txt = "buildIpedia: %s is not supported build type" % type
        return (1, txt)
    try:
        retcode = subprocess.call([CW_PATH, IPEDIA_MCP, "/t", type, "/b", "/r", "/c", "/q", "/s"])
        if retcode < 0:
            return (-retcode, None)
        else:
            return (retcode, None)
    except Exception, ex:
        txt = exceptionAsStr(ex)
        return (1, txt)

def buildFullInfoMan(type):
    flickrType = "Release"
    if DEBUG_TYPE == type:
        flickrType = DEBUG_TYPE
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

def copyFileCompressed(srcPath, dstPath):
    copyFile(srcPath, dstPath, True)

# just builds infoman
def buildNormal():
    (errCode, errTxt) = buildFullInfoMan(RELEASE_TYPE)
    if 0 != errCode:
        print "failed to build infoman of type %s, errCode=%s, errTxt=%s" % (RELEASE_TYPE, str(errCode), errTxt)

    (errCode, errTxt) = buildFullInfoMan(DEBUG_TYPE)
    if 0 != errCode:
        print "failed to build infoman of type %s, errCode=%s, errTxt=%s" % (DEBUG_TYPE, str(errCode), errTxt)

    (errCode, errTxt) = buildFullInfoMan(SHIPPING_TYPE)
    if 0 != errCode:
        print "failed to build infoman of type %s, errCode=%s, errTxt=%s" % (SHIPPING_TYPE, str(errCode), errTxt)

    (errCode, errTxt) = buildFullInfoMan(PALMGEAR_TYPE)
    if 0 != errCode:
        print "failed to build infoman of type %s, errCode=%s, errTxt=%s" % (PALMGEAR_TYPE, str(errCode), errTxt)

    time.sleep(10)
    os.remove(FLICKR_MCP)
    os.remove(INFOMAN_MCP)
    updateInfoMan()

# Builds all versions of infoman, if the repository has changed.
# Copies the *.prc an *.MAP files to dstDir
# deletes and updates *.mcp files after the build since they get 
# modified during build process  
def buildAndArchive(dstDir):
    global g_fBuildDone
    try:
        # get a stable time we use for naming resulting files
        curDate = time.strftime( "%Y-%m-%d_%H-%M", time.localtime() )
        fFrameworkUpdated = updateArsFramework()
        fInfoManUpdated = fFrameworkUpdated or updateInfoMan()
        fIpediaUpdated = fFrameworkUpdated or updateIpedia()
        if fInfoManUpdated:
            #print "building InfoMan"
            g_fBuildDone = True
            # errors are logged to mail in buildFullInfoMan,
            # we ignore errors and build as much as possible
            (errCode, errTxt) = buildFullInfoMan(RELEASE_TYPE)
            (errCode, errTxt) = buildFullInfoMan(DEBUG_TYPE)
            (errCode, errTxt) = buildFullInfoMan(SHIPPING_TYPE)
    
            for type in [RELEASE_TYPE, DEBUG_TYPE, SHIPPING_TYPE, PALMGEAR_TYPE]:
                srcPath = os.path.join(REPO_INFOMAN, type, "InfoMan.prc")
                dstPath = os.path.join(dstDir, "%s-InfoMan-%s.prc" % (curDate,type))
                #print "copy %s to %s" % (srcPath, dstPath)
                copyFile(srcPath, dstPath)
                srcPath = os.path.join(REPO_INFOMAN, type, "InfoMan.prc.MAP")
                dstPath = os.path.join(dstDir, "%s-InfoMan-%s.prc.MAP" % (curDate,type))
                #print "copy %s to %s" % (srcPath, dstPath)
                copyFileCompressed(srcPath, dstPath)

            time.sleep(10)
            os.remove(FLICKR_MCP)
            os.remove(INFOMAN_MCP)
            updateInfoMan()

        if fIpediaUpdated:
            #print "building iPedia"
            g_fBuildDone = True
            # errors are logged to mail in buildIpedia,
            # we ignore errors and build as much as possible
            (errCode, errTxt) = buildIpedia(RELEASE_TYPE)
            (errCode, errTxt) = buildIpedia(DEBUG_TYPE)
    
            for type in [RELEASE_TYPE, DEBUG_TYPE]:
                srcPath = os.path.join(REPO_IPEDIA, type, "iPedia.prc")
                dstPath = os.path.join(dstDir, "%s-iPedia-%s.prc" % (curDate,type))
                #print "copy %s to %s" % (srcPath, dstPath)
                copyFile(srcPath, dstPath)
                srcPath = os.path.join(REPO_IPEDIA, type, "iPedia.prc.MAP")
                dstPath = os.path.join(dstDir, "%s-iPedia-%s.prc.MAP" % (curDate,type))
                #print "copy %s to %s" % (srcPath, dstPath)
                copyFileCompressed(srcPath, dstPath)

            time.sleep(10)
            os.remove(IPEDIA_MCP)
            updateIpedia()

    finally:
        emailErrors()
        #printErrors()

def main():
    if fDetectRemoveCmdFlag("-archive"):
        buildAndArchive(BUILD_ARCHIVE_PATH)
    else:
        buildNormal()

if __name__ == "__main__":
    main()
