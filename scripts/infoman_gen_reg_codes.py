# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk
#
# Purpose:
#  Generate registration codes for infoman. Our goals:
#  - generate codes incrementally
#  - codes can be for handango, palmgear and esellerate
#  - codes should be unique and random and not easy to find
#  - generate *.sql file that we can import into infoman to install those regcodes
#  - generate *.txt file with codes ready to be uploaded to esellerate/pg/handango
#
# How it works.
#
# Generating codes. We plan to sell about 100.000 copies. If we want to 
# have 1% chance of guessing a regcode, we have to generate 100.000.00
# i.e. 8 digit random number. We make it 12-digit random number just
# for kicks
#
# We store generated numbers in reg_codes.csv file. It's a CSV file
# with the following fields:
# regcode, purpose, when
#   'when' is the time it was generated in the "YYYY-MM-DD hh:mm" format
#   'purpose' describes to whom it was assigned (i.e. 'pg' for PalmGear,
#             'h' for handango, 'es' for eSellerate
# and custom strings for special reg codes)
# Reg codes from this file can be imported via import_reg_codes.py script.
#
# We also generate a *.txt file with serial numbers ready to be uploaded to
# eSellerate/PalmGear/Handango. The format of this file:
#  eSellerate: serial number per line, at least 500 serial numbers
#
#
#  TODO:
#    - don't generate multiple special codes for the same special thing
#    - should be more data driven
#
# Usage:
#  -s who: a special code. the idea is to give out codes to some people
#                (like reviewers) and be able to track what they do with the
#                software
# or:
# $purpose $count
#
#  $count   : number of reg codes to generate
#  $purpose : who the reg codes are for Valid entries:
#     - 'h' for Handango
#     - 'pg' for PalmGear
#     - 'es' for eSellerate
#     - 'sn' for smartphone.net
#     - 'mr' for mobireach.com

#
# History:
#  2004-04-15  created
#  2004-06-20  more work done
#  2004-08-22  support for smartphone.net
#  2006-06-20  added mobireach.net

import sys,os,random,time,string,StringIO

def csvQuote(txt):
    if -1 != txt.find(","):
        txt = '"%s"' % txt
    return txt

# doesn't work!
#def csvUnquote(txt):
#    if len(txt)>2 and txt[0]=='"' and txt[-1]=='"':
#        return txt[1:-1]
#    return txt

# note: those are very primitive and likely to fail on ony non-standard data
def csvRowToTxt(row):
    rowQuoted = [csvQuote(el) for el in row]
    return string.join(rowQuoted,",")

def checkCsvTxt(txt):
    if -1 != txt.find(","):
        print "'%s' contains comma(',') and it's not allowed" % txt
        sys.exit(0)

def csvRowToTxt(row):
    for el in row:
        checkCsvTxt(el)
    return string.join(row,",")

def csvTxtToRow(txt):
    #this doesn't work
    #return [csvUnquote(el) for el in txt.split(",")]
    return txt.split(",")

g_regCodesFileName        = "reg_codes.csv"
REG_CODE_LEN = 12

# minimum number of per-file codes for Esellerate
MIN_ES_CODES = 500

# minimum number of per-file codes for PalmGear
# PalmGear says that they send e-mail if number of regcodes below 50
# no mention of any other limit
MIN_PG_CODES = 500

# TODO: check MIN_H_CODES limit
# minimum number of per-file codes for Handango
MIN_H_CODES = 500

# minimum number of per-file codes for smartphone.net
MIN_SN_CODES = 100

# minimum number of per-file codes for mobireach.net
MIN_MR_CODES = 100

# given argument name in argName, tries to return argument value
# in command line args and removes those entries from sys.argv
# return None if not found
def getRemoveCmdArg(argName):
    argVal = None
    try:
        pos = sys.argv.index(argName)
        argVal = sys.argv[pos+1]
        sys.argv[pos:pos+2] = []
    except:
        pass
    return argVal

def fFileExists(filePath):
    try:
        st = os.stat(filePath)
    except OSError:
        # TODO: should check that Errno is 2
        return False
    return True

# generate a random reg code of a given length (in decimal numbers)
def genRegCode(regCodeLen):
    regCode = ""
    for i in range(regCodeLen):
        num=chr(random.randint(ord('0'), ord('9')))
        assert num>='0' and num<='9'
        regCode += num
    return regCode

def getCurDate():
    return time.localtime()

g_stableDate = None
def getStableDate():
    global g_stableDate
    if None == g_stableDate:
        g_stableDate = getCurDate()
    return g_stableDate

g_stableDateTxt = None
def getStableDateTxt():
    global g_stableDateTxt
    if None == g_stableDateTxt:
        g_stableDateTxt = time.strftime("%Y-%m-%d %H:%M", getStableDate())
    return g_stableDateTxt

# generate a unique file name
def getUniqueDatedFileName(prefix):
    fileName = prefix + time.strftime("%Y-%m-%d_%H_%M.txt", getStableDate())
    count = 1
    while True:
        if not fFileExists(fileName):
            return fileName
        print "getUniqueDatedFileName(): file '%s' exists, generating a new one" % fileName
        fileName = prefix + time.strftime("%Y-%m-%d_%H_%M", getStableDate())
        fileName = "%s-%d.txt" % (fileName,count)
        count += 1
    return fileName

def getEsellerateFileName():
    return getUniqueDatedFileName("es-")
def getHandangoFileName():
    return getUniqueDatedFileName("h-")
def getPalmGearFileName():
    return getUniqueDatedFileName("pg-")
def getSmartphoneFileName():
    return getUniqueDatedFileName("sn-")
def getMobiReachFileName():
    return getUniqueDatedFileName("mr-")

# we need to read previous csv data in order to avoid generating duplicate codes
def readPreviousCodes():
    global g_regCodesFileName
    prevCodes = {}
    fo = None
    try:
        fo = open(g_regCodesFileName,"rb")
    except:
        # file doesn't exist - that's ok
        pass
    if None == fo:
        return prevCodes

    for line in fo.readlines():
        line = line.strip()
        row = csvTxtToRow(line)
        prevCodes[row[0]] = row[1:]
    fo.close()
    return prevCodes

def saveNewCodesToCsv(newCodes):
    global g_regCodesFileName
    csvFile = StringIO.StringIO()
    # csvRow is: [regCode, purpose, when_generated]
    for regCode in newCodes.keys():
        csvRow = [regCode, newCodes[regCode][0], newCodes[regCode][1]]
        txt = csvRowToTxt(csvRow)
        csvFile.write(txt+"\n")
    csvTxt = csvFile.getvalue()
    csvFile.close()
    fo = open(g_regCodesFileName, "ab")
    fo.write(csvTxt)
    fo.close()

def saveNewCodesToSQL(newCodes):
    # TODO: should I check if the file exists? Or maybe just append?
    fo = open(getSQLFileName(), "wb")
    for code in newCodes.keys():
        purpose = newCodes[code][0]
        fo.write("INSERT INTO VALUES('%s','%s')\n" % (code, purpose))
    fo.close()

def genNewCodes(count, purpose, prevCodes):
    newCodes = {}
    dateTime = getStableDateTxt()
    for t in range(count):
         newCode = genRegCode(REG_CODE_LEN)
         while prevCodes.has_key(newCode) or newCodes.has_key(newCode):
            print "found dup: %s" % newCode
            newCode = genRegCode(REG_CODE_LEN)
         newCodes[newCode] = [purpose,dateTime]
    return newCodes

def usageAndExit():
    print "Usage: infoman_gen_reg_codes.py [-special who] [$purpose (es,h,pg) $count]"
    print "e.g. infoman_gen_reg_codes.py es 700"
    sys.exit(0)

#  eSellerate: serial number per line, at least MIN_ES_CODES serial numbers
def createEsellerateFile(codes):
    fileName = getEsellerateFileName()
    assert not fFileExists(fileName)
    assert len(codes)>=MIN_ES_CODES
    fo = open(fileName, "wb")
    fo.write( string.join(codes.keys(), "\r\n") + "\r\n")
    fo.close()

# Handango: comma separated list of registration codes. They don't support
# uploading files, you have to copy&paste reg codes into a text field.
# FireFox 0.9.1 doesn't show such a long text in text field (although it's there).
# IE 6 works better.
def createHandangoFile(codes):
    fileName = getHandangoFileName()
    assert not fFileExists(fileName)
    assert len(codes)>=MIN_H_CODES
    fo = open(fileName, "wb")
    codesTxt = string.join(codes.keys(), ",")
    fo.write(codesTxt + "\n")
    fo.close()

# smartphone.net: comma separated list of registration codes. They don't support
# uploading files, you have to copy&paste reg codes into a text field.
# FireFox 0.9.1 doesn't show such a long text in text field (although it's there).
# IE 6 works better.
def createSmartphoneFile(codes):
    fileName = getSmartphoneFileName()
    assert not fFileExists(fileName)
    assert len(codes)>=MIN_SN_CODES
    fo = open(fileName, "wb")
    codesTxt = string.join(codes.keys(), ",")
    fo.write(codesTxt + "\n")
    fo.close()

# PalmGear. From their site:
# Text only
# One code per line
# File extension .txt
# For ease of entry by customers it is suggested that characters such
# as 0 (zero) or others easily confused not be used. Once the quantity
# remaining reaches 50 or less our system will send an email alerting and
# requesting that more codes be uploaded. Should the quantity drop to zero
# customers will be emailed notifying that the code pool is depleted and that
# the developer will email the code to them. 
def createPalmGearFile(codes):
    fileName = getPalmGearFileName()

    assert not fFileExists(fileName)
    assert len(codes)>=MIN_PG_CODES
    fo = open(fileName, "wb")
    for code in codes.keys():
        fo.write( "%s\r\n" % code )
    fo.close()

# codes separated by commas (',')
def createMobiReachFile(codes):
    fileName = getMobiReachFileName()
    assert not fFileExists(fileName)
    assert len(codes) >= MIN_MR_CODES
    fo = open(fileName, "wb")
    codesTxt = string.join(codes.keys(), ",")
    fo.write(codesTxt + "\r\n")
    fo.close()

# TODO: all this should use the following data
g_ProviderInfo = [
 ["h", "handango.com", "h-", MIN_H_CODES, getHandangoFileName]
 ]

def main():
    specialName = getRemoveCmdArg("-special")
    if None == specialName:
        specialName = getRemoveCmdArg("-s")
    if specialName:
        if len(sys.argv) != 1:
            print "no other arguments allowed when using -special"
            usageAndExit()
        if len(specialName) > 190:
            # db allows 255 but we use 190 just to be safe; it's way too long anyway
            print "-special argument too long (%d chars, only 190 allowed)" % len(specialName)
            usageAndExit()
        specialName = "s:%s" % specialName
    else:
        if len(sys.argv) != 3:
            usageAndExit()
        purpose = sys.argv[1]
        if purpose not in ["pg", "h", "es", "sn", "mr"]:
            print 'purpose cannot be %s. Must be "pg", "h", "es", "mr" or "sn"' % purpose
            usageAndExit()
        regCodesCount = int(sys.argv[2])

    if None == specialName:
        if "es" == purpose:
            if regCodesCount < MIN_ES_CODES:
                print "When generating Esellerate codes, the minium number of codes is %d" % MIN_ES_CODES
                usageAndExit()

        if "h" == purpose:
            if regCodesCount < MIN_H_CODES:
                print "When generating Handango codes, the minium number of codes is %d" % MIN_H_CODES
                usageAndExit()

        if "pg" == purpose:
            if regCodesCount < MIN_PG_CODES:
                print "When generating PalmGear codes, the minium number of codes is %d" % MIN_PG_CODES
                usageAndExit()

        if "sn" == purpose:
            if regCodesCount < MIN_SN_CODES:
                print "When generating Smartphone.net codes, the minium number of codes is %d" % MIN_SN_CODES
                usageAndExit()

        if "mr" == purpose:
            if regCodesCount < MIN_MR_CODES:
                print "When generating MobiReach.net codes, the minium number of codes is %d" % MIN_MR_CODES
                usageAndExit()

    print "reading previous codes"
    prevCodes = readPreviousCodes()
    print "read %d old codes" % len(prevCodes)
    print "start generating new codes"

    if specialName:
        newCodes = genNewCodes(1, specialName, prevCodes)
    else:
        newCodes = genNewCodes(regCodesCount, purpose, prevCodes)
        if "es" == purpose:
            createEsellerateFile(newCodes)
        if "h" == purpose:
            createHandangoFile(newCodes)
        if "pg" == purpose:
            createPalmGearFile(newCodes)
        if "sn" == purpose:
            createSmartphoneFile(newCodes)
        if "mr" == purpose:
            createMobiReachFile(newCodes)
    print "generated %d new codes" % len(newCodes)
    
    saveNewCodesToCsv(newCodes)

if __name__=="__main__":
    main()

