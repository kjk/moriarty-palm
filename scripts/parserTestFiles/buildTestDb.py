# based on *.txt file, create a *pdb to be used by parser test module.
# first record has names of text files.
# then each record after that is one text file with a marked up text
# that parser needs to understand.

# This is mostly intended so that we can create test cases for the parser
# by hand and test different layouts for modules.

import os, sys, string
import palmdb

DB_CREATOR = "wIKi"
DB_TYPE = "TesT"

def buildDbFromFiles(fileNames):
    # TODO: assert that "##" doesn't exist in file name (otherwise things will break)
    firstRecData = string.join(fileNames, "##")
    firstRecData += chr(0)

    recsData = []
    for fileName in fileNames:
        fo = open(fileName, "rb")
        fileContent = fo.read()
        fo.close()
        fileContent += "\0"
        recsData.append(fileContent)
        fileContent += chr(0) # null-terminate it for C strings

    pdbRec = palmdb.PDBRecordFromData(firstRecData)
    allRecords = [pdbRec]
    for recData in recsData:
        pdbRec = palmdb.PDBRecordFromData(recData)
        allRecords.append(pdbRec)

    newPdb = palmdb.PDB()
    newPdb.name = "parser test files"
    newPdb.creator = DB_CREATOR
    newPdb.dbType = DB_TYPE
    newPdb.records = allRecords
    newPdb.saveAs("parserTests.pdb", fOverwrite=True)

def main():
    # read all the *.txt files in this directory
    fileNames = []

    for name in os.listdir(os.getcwd()):
        if len(name) > 4:
            if name[-4:] == ".txt":
                fileNames.append(name)

    #print fileNames
    if 0 == len(fileNames):
        print "Didn't find any *.txt files to process. Aborting."
        sys.exit(0)
    buildDbFromFiles(fileNames)

if __name__ == "__main__":
    main()
