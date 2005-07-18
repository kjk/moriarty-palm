# Copyrigh: Krzysztof Kowalczyk
# Author: Krzysztof Kowalczyk
# Description:
#   Parses ntc dictionary file. Based on dict_tool\dictread.c
import string, os, os.path, struct

# TODO:
#  - there are still some characters that look like garbage
#  - more intelligence so that it can extract meaningful information
#    like figuring out the word, part of speech, pronounciation etc.
#  - collapse word(1), word(2) etc. into one
#  - create multiple entries for dashed words (e.g. "home-made" will create
#    both "home-made" and "homemade" entries, pointing to the same data
#  - build an index (lower-cased words are indexes that map to offset/length
#    of the definition in an definition file
DATA_DIR = "c:\\kjk\\src\\ntc\\ntc data cd"
OUT_DIR = "."

SPANISH_DIR = "anaydata"
ENG_SPANISH_FILE = os.path.join(DATA_DIR, SPANISH_DIR, "sandic01.dat")
ENG_SP_FILE_OUT = "eng-spanish.txt"
SPANISH_ENG_FILE = os.path.join(DATA_DIR, SPANISH_DIR, "sandic02.dat")
SP_ENG_FILE_OUT = "spanish-eng.txt"

GERMAN_DIR = "brandata"
GERMAN_ENGLISH_FILE = os.path.join(DATA_DIR, GERMAN_DIR, "sandic17.dat")
GER_ENG_FILE_OUT = "ger-eng.txt"
ENGLISH_GERMAN_FILE = os.path.join(DATA_DIR, GERMAN_DIR, "sandic23.dat")
ENG_GER_FILE_OUT = "eng-ger.txt"

HARRAP_DIR = "harrdata"
ENGLISH_FRENCH_FILE = os.path.join(DATA_DIR, HARRAP_DIR, "sandic12.dat")
ENG_FRENCH_FILE_OUT = "eng-fr.txt"
FRENCH_ENGLISH_FILE = os.path.join(DATA_DIR, HARRAP_DIR, "sandic13.dat")
FR_ENG_FILE_OUT = "fr-eng.txt"
ENGLISH_GERMAN_HARR_FILE = os.path.join(DATA_DIR, HARRAP_DIR, "sandic14.dat")
GERMAN_ENGLISH_HARR_FILE = os.path.join(DATA_DIR, HARRAP_DIR, "sandic15.dat")

ITALIAN_DIR = "zanidata"
ENG_ITALIAN_FILE = os.path.join(DATA_DIR, ITALIAN_DIR, "sandic03.dat")
ITALIAN_ENG_FILE = os.path.join(DATA_DIR, ITALIAN_DIR, "sandic04.dat")
FIVE_LANGS_FILE = os.path.join(DATA_DIR, ITALIAN_DIR, "sandic05.dat")
FIVE_LANGS_FILE_OUT = "five-langs.txt"

MAX_WORD_LEN = 200
MAX_DEF_LEN = 25000

accentMap = [
    [0x0B,  230],		      # ae 
    [0x0C,  248],                     # \o 
    [0x0D,  229],		      # ao 
    [0x0E,  228],                     # "a 
    [0x0F,  246],                     # "o 

    [0x1B,  198],		      # Ae 
    [0x1C,  216],		      # /O 
    [0x1D,  197],		      # Ao 
    [0x1E,  196],                     # "A 
    [0x1F,  214],                     # "O 

    [0x80,  231],		      # Alternate c-cedille 
    [0x81,  252],
    [0x82,  233],
    [0x83,  226],
    [0x84,  228],
    [0x85,  224],
    [0x87,  231],
    [0x88,  234],
    [0x89,  235],
    [0x8A,  232],
    [0x8B,  239],
    [0x8C,  238],
    [0x8D,  236],
    [0x8E,  198],

    [0x90,  201],
    [0x91,  230],
    [0x92,  198],		      # Ae (Spanish) 
    [0x93,  244],
    [0x94,  246],
    [0x95,  242],
    [0x96,  251],
    [0x97,  249],
    [0x99,  214],
    [0x9A,  220],
    [0x9C,  163],

    [0xA0,  225],
    [0xA1,  237],
    [0xA2,  243],
    [0xA3,  250],
    [0xA4,  241],
    [0xA5,  241],		      # Variant of ~n 

    [0xA8,  191],

    [0xAD,  161],

    [0xC9,  ord('S')],                     # Italian 
    [0xCA,  ord('s')],                     # Italian 
    [0xCB,  ord('Z')],                     # Italian 
    [0xCC,  ord('z')],                     # Italian 

    [0xD0,  223],		      # German double s 

    [0xE1,  223],
    [0xE6,  181],		      # Mu 

    [0xF6,  247],		      # Division sign 
    [0xF7,  176],		      # Degrees in Swedish dict 
    [0xF8,  176],		      # Degrees 
    [0xFA,  215],		      # Times 
]

ipaMap = [
    [0xB0, "\242"],
    [0xB1, "\265"],
    [0xB2, "\360"],
    [0xB3, "\247"],
    [0xB4, "3"],
    [0xB5, "\244"],
    [0xB6, "\376"],
    [0xB7, "z"],                      # Sometimes rendered as s inverted hat #
    [0xB8, "I"],                      # Small-caps I in IPA #
    [0xB9, "\360"],                   # Alternate for "th" thorn #
    [0xBA, "3"],                      # Sometimes rendered as y overbar #
    [0xBB, "\343"],
    [0xBC, "\366"],
    [0xBD, "\365"],
    [0xBE, "\243"],
    [0xBF, "\377"],

    [0xC0, "\256"],
    [0xC2, "l(\265)"],
    [0xC1, "\352"],
    [0xC3, "\265"],                   # Italian #
    [0xC4, "\364"],
    [0xC5, "\361"],
    [0xC6, "Oe"],

    [0xC7, ""],                       # Subscript shift #
    [0xC8, ""],                       # Superscript shift #

    [0xE0, "Alpha"],
    [0xE2, "Gamma"],
    [0xE3, "Pi"],
    [0xE5, "Sigma"],
    [0xE9, "8"],
    [0xEB, "Delta"],
    [0xED, "\370"],
    [0xEE, "\350"],
]

def buildHashFromMap(map):
    hash = {}
    for (key, value) in map:
        hash[key] = value
    return hash

g_accentHash = buildHashFromMap(accentMap)
g_ipaHash = buildHashFromMap(ipaMap)

def replaceAccent(cNum):
    global g_accentHash
    if g_accentHash.has_key(cNum):
        return g_accentHash[cNum]
    return None

def replaceIpa(cNum):
    global g_ipaHash
    if g_ipaHash.has_key(cNum):
        return g_ipaHash[cNum]
    return None

def isAscii(cNum):
    if cNum >= 32 and cNum < 127:
        return True
    return False

def decodeDef(wordDef, wordLen, mysteryLen, defLen):
    on = True
    res = []
    if chr(0xdc) == wordDef[0]:
        word = wordDef[1:wordLen]
    else:
        word = wordDef[0:wordLen]
    for c in wordDef:
        cNum = ord(c)
        if isAscii(cNum):
            res.append(c)
            continue
        if 0xfb == cNum:
            on = False
            continue
        if 0xfc == cNum or 0xfd == cNum:
            on = True
            continue
        if not on:
            continue
        # 0xd9 - I. Main item
        # 0xda - (a) sub-item
        # 0xd8 - (a) sub-item
        # 0xdb 1. sub-item
        if cNum in [0xd9, 0xda, 0xd8, 0xdb]:
            if len(res) > 0:
                res.append('\n')
            continue
        # 0x10 - word break
        # 0xae - italics in norwegian dict
        # 0xaf - normal in norwegian dict
        # 0xdc - start word
        # 0xdd - start of new def
        # 0xde - italic
        # 0xdf - normal
        if cNum in [0x10, 0xae, 0xaf, 0xdc, 0xdd, 0xde, 0xdf]:
            continue
        cAcc = replaceAccent(cNum)
        if None != cAcc:
            res.append(chr(cAcc))
            continue
        ipaStr = replaceIpa(cNum)
        if None != ipaStr:
            res.append(ipaStr)
            continue
        # if couldn't map -> change it to its hex code
        res.append("0x%x" % cNum)
    fullDef = string.join(res, "")
    return (word, fullDef)

# the *.dat file format is as follows:
# uint16   length of an entry word
# uint16   unidentified value (length of sth.)
# uint16   lenght of the definition
# char[word_len]
# char[definition_len]
# but we ignore lengths and just try to parse stuff
def getNextDef(fo):
    header = fo.read(6)
    if None == header:
        return None
    (wordLen, mysteryLen, defLen) = struct.unpack(">hhh", header)
    totalLen = wordLen + mysteryLen + defLen
    if 0 == totalLen:
        return None
    wordDef = fo.read(totalLen)
    #print "%03d, %03d, %03\n" % (wordLen, mysteryLen, defLen)
    assert(wordLen >= 0)
    assert(wordLen < MAX_WORD_LEN)
    assert(defLen >= 0)
    assert(defLen < MAX_DEF_LEN)
    assert(mysteryLen >= 0)
    if 0 == wordLen or 0 == defLen:
        return getNextDef(fo)
    (word, fullDef) = decodeDef(wordDef, wordLen, mysteryLen, defLen)
    print "%s\n%s\n" % (word, fullDef)
    return (word, fullDef)

def convertDict(fileNameIn, fileNameOut):
    fo = open(fileNameIn, "rb")
    wordCount = 0
    while True:
        wordDef = getNextDef(fo)
        if None == wordDef:
            break
        wordCount += 1
    fo.close()
    print "Total words: %d" % wordCount

def main():
    convertDict(ENGLISH_FRENCH_FILE, ENG_FRENCH_FILE_OUT)
    #convertDict(FRENCH_ENGLISH_FILE, FR_ENG_FILE_OUT)
    #convertDict(ENG_SPANISH_FILE, ENG_SP_FILE_OUT)
    #convertDict(SPANISH_ENG_FILE, SP_ENG_FILE_OUT)
    #convertDict(GERMAN_ENGLISH_FILE, GER_ENG_FILE_OUT)
    #convertDict(ENGLISH_GERMAN_FILE, ENG_GER_FILE_OUT)
    #convertDict(FIVE_LANGS_FILE, FIVE_LANGS_FILE_OUT)

if __name__ == "__main__":
    main()
