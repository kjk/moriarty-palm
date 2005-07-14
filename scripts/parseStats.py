# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk

# Purpose:
#
# Build and display infoman stats.

import sys, os, string, datetime, arsutils
from downloadStats import *

g_users = None
g_requests = None
g_devices = None

def sortPred(el1, el2):
    return cmp(el1[1], el2[1])

def isUserRegistered(userId):
    global g_users
    regCode = g_users[userId-1][USERS_REG_CODE]
    if None == regCode:
        return False
    return True

# creates statistics about number of requests per user
# prints:
#  - user id
#  - total number of requests
#  - number of non-free requests
#  - number of free requests
def doUserStats():
    global g_users, g_requests
    usersCount = len(g_users)+1
    userReqFree = range(usersCount)
    userReqNonFree = range(usersCount)
    for n in range(usersCount):
        userReqFree[n] = []
        userReqNonFree[n] = []
    print "users: %d" % len(g_users)
    print "requests: %d" % len(g_requests)
    for req in g_requests:
        userId = req[RL_USER_ID]
        reqDate = req[RL_LOG_DATE]
        reqDateTxt = "%04d-%02d-%02d" % (reqDate.year, reqDate.month, reqDate.day)
        freeReq = True
        if 'f' == req[RL_FREE_P]:
            freeReq = False
        #print "userId: %d, reqDate: %s" % (userId, reqDateTxt)
        if freeReq:
            userReqFree[userId].append(reqDateTxt)
        else:
            userReqNonFree[userId].append(reqDateTxt)
    userReqCount = []
    totalUserCount = 0
    totalReqCount = 0
    for userId in range(usersCount):
        reqCountNonFree = len(userReqNonFree[userId])
        reqCountFree = len(userReqFree[userId])
        reqCountTotal = reqCountFree + reqCountNonFree
        if reqCountTotal > 0:
            userReqCount.append([userId, reqCountTotal, reqCountNonFree, reqCountFree])
            totalUserCount += 1
            totalReqCount += reqCountTotal

    userReqCount.sort(sortPred)
    for (userId, reqCountTotal, reqCountNonFree, reqCountFree) in userReqCount:
        if isUserRegistered(userId):
            print "* %4d: %6d %6d %6d" % (userId, reqCountTotal, reqCountNonFree, reqCountFree)
        else:
            print "  %4d: %6d %6d %6d" % (userId, reqCountTotal, reqCountNonFree, reqCountFree)
    print "Total users:    %d" % totalUserCount
    print "Total requests: %d" % totalReqCount
    reqPerUser = float(totalReqCount) / float(totalUserCount)
    print "Requests/user: %.2f" % reqPerUser

class ReqDailyStats:
    def __init__(self):
        self.total = 0
        self.free = 0

def sortDailyStatsPred(el1, el2):
    return cmp(el1[0], el2[0])

# creates stats about requests per day
# prints:
#  - date
#  - number of requests
def doRequestsStats():
    global g_requests
    requestsPerDay = {}
    for req in g_requests:
        reqDate = req[RL_LOG_DATE]
        reqDateTxt = "%04d-%02d-%02d" % (reqDate.year, reqDate.month, reqDate.day)
        freeReq = True
        if 'f' == req[RL_FREE_P]:
            freeReq = False
        if requestsPerDay.has_key(reqDateTxt):
            stats = requestsPerDay[reqDateTxt]
        else:
            stats = ReqDailyStats()
            requestsPerDay[reqDateTxt] = stats
        stats.total = stats.total + 1
        if freeReq:
            stats.free = stats.free + 1

    dailyStats = requestsPerDay.items()
    dailyStats.sort(sortDailyStatsPred)
    for stat in dailyStats:
        print " %s: %6d %6d" % (stat[0], stat[1].total, stat[1].free)


errorUnknown = 0
# those values are copied from \server\ServerErrors.py
serverFailure = 1
unsupportedDevice = 2
malformedRequest = 4
lookupLimitReached = 5
invalidProtocolVersion = 6
requestArgumentMissing = 7
unexpectedRequestArgument = 8
invalidCookie = 9
userDisabled = 10
invalidRegCode = 11
forceUpgrade = 12
invalidRequest = 13
moduleTemporarilyDown = 14
regCodeExpired = 15

g_errorCodeToName = ["errorUnknown", 
    "serverFailure", 
    "unsupportedDevice",
    "no error with error code 3"
    "malformedRequest",
    "lookupLimitReached",
    "invalidProtocolVersion",
    "requestArgumentMissing",
    "unexpectedRequestArgument",
    "invalidCookie",
    "userDisabled",
    "invalidRegCode",
    "forceUpgrade",
    "invalidRequest",
    "moduleTemporarilyDown",
    "regCodeExpired" ]

# True if we should ignore lookupLimitReached errors
g_filterLookupLimitErrors = True

# creates stats about all failed requests
# prints:
#  - date
#  - request
#  - error number
def doFailedRequestsStats():
    global g_requests, g_filterLookupLimitErrors
    failedRequests = {}
    totalErrors = 0 # not including lookupLimitReached
    lookupLimitErrors = 0
    for req in g_requests:
        errorCode = req[RL_ERROR]
        if None == errorCode:
            continue
        if g_filterLookupLimitErrors and lookupLimitReached == errorCode:
            lookupLimitErrors += 1
            continue
        totalErrors += 1
        errorCode = int(str(errorCode))
        reqDate = req[RL_LOG_DATE]
        reqDateTxt = "%04d-%02d-%02d" % (reqDate.year, reqDate.month, reqDate.day)
        reqTxt = req[RL_REQUEST]
        if failedRequests.has_key(reqDateTxt):
            failedRequests[reqDateTxt].append((errorCode, reqTxt))
        else:
            failedRequests[reqDateTxt] = [(errorCode, reqTxt)]

    days = failedRequests.keys()
    days.sort()
    for day in days:
        for stats in failedRequests[day]:
            errorCode = stats[0]
            errorName = g_errorCodeToName[errorCode]
            reqTxt = stats[1]
            #print " %s %2d (%s) %s" % (day, errorCode, errorName, reqTxt)
            print " %s %2d %s" % (day, errorCode, reqTxt)
    print
    print "Total errors: %6d" % totalErrors
    print "Lookup limit: %6d" % lookupLimitErrors

def sortDeviceStatsPred(el1, el2):
    return cmp(el1[1], el2[1])

# creates stats about devices used
# prints:
#  - device name
#  - number of users using this device
def doDeviceStats():
    global g_users
    deviceStats = {}
    for user in g_users:
        deviceInfo = user[USERS_DEVICE_INFO]
        di = arsutils.decodeDi(deviceInfo)
        deviceName = di['device_name']
        if deviceStats.has_key(deviceName):
            deviceStats[deviceName] = deviceStats[deviceName] + 1
        else:
            deviceStats[deviceName] = 1

    deviceStatsArr = [item for item in deviceStats.items() if item[1] > 2]
    deviceStatsArr.sort(sortDeviceStatsPred)
    for (deviceName, n) in deviceStatsArr:
        print " %5d : %s" % (n, deviceName)

def main():
    global g_users, g_requests
    loadData()
    g_users = getTableUsersData()
    g_requests = getTableRequestLogData()
    #doUserStats()
    #doRequestsStats()
    #doDeviceStats()
    doFailedRequestsStats()

if __name__ == "__main__":
    main()
