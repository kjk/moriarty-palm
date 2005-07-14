import os, sys

# we run both the shipping version as well as testing versions of InfoMan
# server on the same Unix box. That means that each server needs to run
# on a different port and use different database and files etc.
# This dict maps Unix user name to [port, database, tmpFileDir]
userPortDbMapping = {
    "infoman" : [4000, "infoman", "/infoman/infoman"],
    "infoman-szymon" : [5010, "infomanszymon", "/infoman/szymon"],
    "infoman-andrzej" : [5012, "infomanandrzej", "/infoman/andrzej"],
    "infoman-kjk" : [5014, "infomankjk", "/infoman/kjk"],
    # those are settings for testing locally on a pc
    "kjk-tlap" : [4000, "infoman", "c:\\kjk\infoman"],
    "kjk-dvd"  : [4000, "infoman", "c:\\kjk\\infoman"],
    "kjk-dvd2" : [4000, "infoman", "c:\\kjk\\infoman"],
    "kjk-kjklap1" : [4000, "infoman", "c:\\tmp\\infoman"],
    "szymon" : [4000, "infoman", "c:\\tmp\\infoman"],
    "andrzej" : [4000, "infoman", "c:\\tmp\\infoman"],
}

def getServerUser():
    global userPortDbMapping
    if "win32" == sys.platform:
        compName = os.environ["COMPUTERNAME"]
        if "TLAP" == compName:
            return "kjk-tlap"
        if "DVD" == compName:
            return "kjk-dvd"
        if "DVD2" == compName:
            return "kjk-dvd2"
        if "KJKLAP1" == compName:
            return "kjk-kjklap1"
        if "MAGG" == compName:
            return "szymon"
        if "GIZMO" == compName:
            return "andrzej"
        if "RABBAN" == compName:
            return "andrzej"
        if "D60031LLX51" == compName:
            return "kjk-dvd"
    userName = os.environ["USER"]
    return userName

# this is the user we're using for db access
def getDbUser():
    global userPortDbMapping
    if "win32" == sys.platform:
        return "infoman"
    return getServerUser()

def getServerPort():
    global userPortDbMapping
    return userPortDbMapping[getServerUser()][0]

def getServerDatabaseName():
    global userPortDbMapping
    return userPortDbMapping[getServerUser()][1]

def getServerStorageDir():
    global userPortDbMapping
    return userPortDbMapping[getServerUser()][2]
