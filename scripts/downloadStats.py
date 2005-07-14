# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk

# Purpose:
#
# Create usage statistics for infoman.
#
# How it works: to minimize load on the server, every time this script
# is run, it downloads new data from users, request_log, get_cookie_log,
# verify_reg_code_log and reg_codes tables.
# Data from users and reqeust_log can be downloaded incrementally, since
# they have autoincrement user_id and request_id fields.
#
# Downloaded data is stored in a pickled format in a file. We use
# data from this file to generate all kinds of stats.

import sys, os, string, MySQLdb, cPickle

DB_HOST = "infoman.arslexis.com"
DB_PWD = "gaz32orb"
DB_USER = "infoman-logs"
DB_NAME = "infoman"

DATA_FILE_NAME = "infoman-stats.dat"

g_conn = None

# stores data from users table
g_tableUsersData = []
# stores data from request_log table
g_tableRequestLogData = []
# stores data from get_cookie_log
g_tableGetCookieLogData = []
# stores data from verify_reg_code_log
g_tableVerifyRegCodeLogData = []

# users table
USERS_USER_ID = 0
USERS_COOKIE = 1
USERS_DEVICE_INFO = 2
USERS_COOKIE_ISSUE_DATE = 3
USERS_REG_CODE = 4
USERS_REGISTRATION_DATE = 5
USERS_DISABLED_P = 6

# request_log table
RL_REQUEST_ID = 0
RL_USER_ID = 1
RL_CLIENT_IP = 2
RL_LOG_DATE = 3
RL_FREE_P = 4
RL_REQUEST = 5
RL_RESULT = 6
RL_ERROR = 7

# get_cookie_log table
GCL_LOG_ID = 0
GCL_USER_ID = 1
GCL_CLIENT_IP = 2
GCL_LOG_DATE = 3
GCL_DEVICE_INFO = 4
GCL_COOKIE = 5

# verify_reg_code_log
VRCL_LOG_ID = 0
VRCL_USER_ID = 1
VRCL_CLIENT_IP = 2
VRCL_LOG_DATE = 3
VRCL_REG_CODE = 4
VRCL_REC_CODE_VALID_P = 5

def getTableUsersData():
    global g_tableUsersData
    return g_tableUsersData

def getTableRequestLogData():
    global g_tableRequestLogData
    return g_tableRequestLogData

def saveData():
    global g_tableUsersData, g_tableRequestLogData, g_tableGetCookieLogData, g_tableVerifyRegCodeLogData, g_tableRegCodesData
    fo = open(DATA_FILE_NAME, "wb")
    cPickle.dump(g_tableUsersData, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    cPickle.dump(g_tableRequestLogData, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    cPickle.dump(g_tableGetCookieLogData, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    cPickle.dump(g_tableVerifyRegCodeLogData, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    fo.close()

def loadData():
    global g_tableUsersData, g_tableRequestLogData, g_tableGetCookieLogData, g_tableVerifyRegCodeLogData, g_tableRegCodesData
    try:
        fo = open(DATA_FILE_NAME, "rb")
    except IOError:
        # it's ok to not have the file
        print "didn't find file %s with data" % DATA_FILE_NAME
        return
    try:
        g_tableUsersData = cPickle.load(fo)
        g_tableRequestLogData = cPickle.load(fo)
        g_tableGetCookieLogData = cPickle.load(fo)
        g_tableVerifyRegCodeLogData = cPickle.load(fo)
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

def getLastUserId():
    global g_tableUsersData
    lastUserId = -1
    for row in g_tableUsersData:
        userId = int(row[USERS_USER_ID])
        if userId > lastUserId:
            lastUserId = userId
    return lastUserId

def getLastRequestId():
    global g_tableRequestLogData
    lastRequestId = -1
    for row in g_tableRequestLogData:
        requestId = int(row[RL_REQUEST_ID])
        if requestId > lastRequestId:
            lastRequestId = requestId
    return lastRequestId

def getCookieLastLogId():
    global g_tableGetCookieLogData
    lastRequestId = -1
    for row in g_tableGetCookieLogData:
        requestId = int(row[GCL_LOG_ID])
        if requestId > lastRequestId:
            lastRequestId = requestId
    return lastRequestId

def getRegCodeLastLogId():
    global g_tableVerifyRegCodeLogData
    lastRequestId = -1
    for row in g_tableVerifyRegCodeLogData:
        requestId = int(row[VRCL_LOG_ID])
        if requestId > lastRequestId:
            lastRequestId = requestId
    return lastRequestId

def getConnection():
    global g_conn
    if None == g_conn:
        g_conn = MySQLdb.Connect(host=DB_HOST, user=DB_USER, passwd=DB_PWD, db=DB_NAME)
    return g_conn

def deinitDatabase():
    global g_conn
    if g_conn:
        g_conn.close()

def getTableUsers():
    global g_tableUsersData
    print "Getting data from users table"
    lastUserId = getLastUserId()
    sql = "SELECT user_id, cookie, device_info, cookie_issue_date, reg_code, registration_date, disabled_p FROM users WHERE user_id > %s;" % str(lastUserId)
    #print "sql = %s" % sql
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    rowCount = 0
    lastUserId = 0
    while True:
        row = cursor.fetchone()
        if not row:
            break
        g_tableUsersData.append(row)
        rowCount += 1
    cursor.close()
    print "%d new rows in users table" % rowCount

def getTableRequestLog():
    global g_tableRequestLogData
    print "Getting data from request_log table"
    lastRequestId = getLastRequestId()
    sql = "SELECT request_id, user_id, client_ip, log_date, free_p, request, result, error FROM request_log WHERE request_id > %s;" % str(lastRequestId)
    #print "sql = %s" % sql
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    rowCount = 0
    while True:
        row = cursor.fetchone()
        if not row:
            break
        g_tableRequestLogData.append(row)
        rowCount += 1
    cursor.close()
    print "%d new rows in request_log table" % rowCount

def getTableGetCookieLog():
    global g_tableGetCookieLogData
    print "Getting data from get_cookie_log table"
    lastLogId = getCookieLastLogId();
    sql = "SELECT log_id, user_id, client_ip, log_date, device_info, cookie FROM get_cookie_log WHERE log_id > %s;" % str(lastLogId)
    #print "sql = %s" % sql
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    rowCount = 0
    while True:
        row = cursor.fetchone()
        if not row:
            break
        g_tableGetCookieLogData.append(row)
        rowCount += 1
    cursor.close()
    print "%d new rows in get_cookie_log table" % rowCount

def getTableVerifyRegCodeLog():
    global g_tableVerifyRegCodeLogData
    print "Getting data from verify_reg_code_log table"
    lastLogId = getRegCodeLastLogId();
    sql = "SELECT log_id, user_id, client_ip, log_date, reg_code, reg_code_valid_p FROM verify_reg_code_log WHERE log_id > %s;" % str(lastLogId)
    #print "sql = %s" % sql
    conn = getConnection()
    cursor = conn.cursor()
    cursor.execute(sql)
    rowCount = 0
    while True:
        row = cursor.fetchone()
        if not row:
            break
        g_tableVerifyRegCodeLogData.append(row)
        rowCount += 1
    cursor.close()
    print "%d new rows in verify_reg_code_log table" % rowCount

def main():
    try:
        loadData()
        getTableUsers()
        getTableRequestLog()
        getTableGetCookieLog()
        getTableVerifyRegCodeLog()
    finally:
        deinitDatabase()
        saveData()

if __name__ == "__main__":
    main()
