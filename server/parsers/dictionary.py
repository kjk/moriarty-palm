# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk / Szymon Knitter
#
# Purpose:
#  dictionary module
#
import sys, os, os.path, string, bisect, cPickle, random
from threading import Lock
import multiUserSupport, parserUtils, arsutils
from ResultType import *
from parserUtils import universalDataFormatWithDefinition, universalDataFormat
from definitionBuilder import *

# Format of dictionary data:
# * we have a file wn-dict.txt which contains definitions for all words. Each
#   definition is described by an (offset,length) within wn-dict.txt file.
# * in memory we have a hash (dictionary) g_wnWordIndex mapping a word to
#   a (offset, length) tuple. This is pickled to wn-word-index.pickle file.
# * we also have g_wnWords array which has all the words sorted alphabetically
#   this is pickled to wn-words.pickle file. Allows calculating nearby words.
#   We could generate g_wnWords from g_wnWordIndex but I hope that unpickling is
#   more efficient (both in time as well as wrt. memory used)

# wn-dict.txt, wn-word-index.pickle, wn-words.pickle are created by wn2infoman.py
# script and live in $storage-dir/dict directory

# What we return as a result for a search term:
# * if we have an exact match in g_wnWordIndex, we add ('D', Definition) in
#   the UDF
# * if we don't have an exact match in g_wnWordIndex, but a given word is simply
#   a known conjugation of some other word which we have in g_wnWordIndex, we
#   return ('D', Definition) for that other word, possibly with some explanation
#   at the beginning (e.g. "'granted' is a past tense for the verb 'grant')
# * if we don't have an exact match but ispell returns a list of alternatives
#   we return ('D', Definition) saying something along the lines: "Didn't find
#   definition of '$word'. Did you mean $word1, $word2, $word3... ?" where $word1,
#   $word2 etc. are ispell suggestions (but only if we have their definition in
#   g_wnWordIndex
# * definition also contains a list of N nearby words at the bottom, which we
#   calculate from g_wnWords
# * if we have link(s) to *.wav files with sound recording of this word, then
#   we add them to UDF as ('S', links). This allows us to play the audio of the
#   word. We get those audio files by spidering other dictionaries like encarta
#   or m-w.com. Currently we don't implement this but client shouldn't break
#   if this data is sent.

DICT_DIR      = "dict"
WN_DICT_FILE  = "wn-dict.txt"
WN_INDEX_FILE = "wn-words-index.pic"
WN_WORDS_FILE = "wn-words.pic"

g_wnDictPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, WN_DICT_FILE)
g_wnIndexPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, WN_INDEX_FILE)
g_wnWordsPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, WN_WORDS_FILE)

# how many nearby words we show
NEARBY_WORDS_TO_SHOW = 8

# it's ok to throw an exception, we don't want to proceed if the file is missing
# TODO: somehow make it that this file is closed when we kill InfoMan
g_wnFo = None

g_wnWordIndex = {}
g_wnWords = []

# random.Random() object used to generate random definitions. Must be initialized
# in initDictionary
g_random = None

# protect WN_DICT_FILE file access from multi-thread issues
g_defReadLock = None

# a flag used to make sure initDictionary() is called only once
g_fInitialized = False

# g_fDisabled is set in initDictionar() it's True if there are no dictionary files
g_fDisabled = None

# load WordNet dictionary files. Return False if one of the files doesn't exist
def loadPickledFiles():
    global g_wnWords, g_wnWordIndex, g_wnDictPath, g_wnIndexPath, g_wnWordsPath
    print "loading wn dictionary data files"

    if not arsutils.fFileExists(g_wnDictPath):
        print "WordNet dictionary file '%s' doesn't exist" % g_wnDictPath
        return False

    if not arsutils.fFileExists(g_wnIndexPath):
        print "WordNet dictionary file '%s' doesn't exist" % g_wnIndexPath
        return False

    if not arsutils.fFileExists(g_wnWordsPath):
        print "WordNet dictionary file '%s' doesn't exist" % g_wnWordsPath
        return False

    try:
        fo = open(g_wnIndexPath, "rb")
        g_wnWordIndex = cPickle.load(fo)
        fo.close()

        fo = open(g_wnWordsPath, "rb")
        g_wnWords = cPickle.load(fo)
        fo.close()
    except Exception, ex:
        print arsutils.exceptionAsStr(ex)
        return False
    print "Finished loading WordNet files"
    return True

def initDictionary():
    global g_wnFo, g_wnDictPath, g_defReadLock, g_random, g_fInitialized, g_fDisabled
    if g_fInitialized:
        return
    g_fInitialized = True
    g_fDisabled = True
    if not loadPickledFiles():
        return
    try:
        assert None == g_wnFo
        g_wnFo = open(g_wnDictPath, "rb")
        assert None == g_defReadLock
        g_defReadLock = Lock()
        assert None == g_random
        g_random = random.Random()
        g_random.seed()
    except Exception, ex:
        print arsutils.exceptionAsStr(ex)
        return
    g_fDisabled = False

def deinitDictionary():
    global g_wnFo, g_fInitialized
    if not g_fInitialized:
        return
    print "deinitDictionary()"
    if None != g_wnFo:
        g_wnFo.close()

# given an array of sorted words (sortedWords) and a count of nearby words
# (nearbyWordsCount), returns an array of words that are alphabetically close
# to word
def _getNearbyWords(sortedWords, word, nearbyWordsCount):
    totalWordsCount = len(sortedWords)
    firstWordPos = bisect.bisect(sortedWords, word)
    halfCount = nearbyWordsCount / 2

    # make sure that we don't go below or over sortedWords array
    firstWordPos -= halfCount

    # if an odd number and an exact match, shift to the left by one
    if 1 == nearbyWordsCount % 2:
        if sortedWords[firstWordPos] == word:
            firstWordPos -= 1

    if firstWordPos > 0:
        if firstWordPos + nearbyWordsCount >= totalWordsCount:
            firstWordPos = totalWordsCount - nearbyWordsCount
            if firstWordPos < 0:
                firstWordPos = 0
    else:
        firstWordPos = 0

    lastWordPos = firstWordPos + nearbyWordsCount
    if lastWordPos > totalWordsCount:
        lastWordPos = None

    return sortedWords[firstWordPos:lastWordPos]

# return a definition for a given word or None if doesn't exist
def _getDef(word):
    global g_wnFo, g_defReadLock, g_wnWordIndex

    if not g_wnWordIndex.has_key(word):
        return None

    wordDef = None
    (defOffset, defLen) = g_wnWordIndex[word]
    g_defReadLock.acquire()
    try:
        g_wnFo.seek(defOffset, 0)   # 0 - absolute positioning
        wordDef = g_wnFo.read(defLen)
    finally:
        g_defReadLock.release()
    return wordDef

def test_getNearbyWords():
    words = ["this", "is",  "a word", "blush", "bust", "zippy", "maniac", "cedric"]
    words.sort()

    assert ['a word', 'blush', 'bust'] == _getNearbyWords(words, "!", 3)
    assert ['a word', 'blush', 'bust'] == _getNearbyWords(words, "a", 3)
    assert ['a word', 'blush', 'bust'] == _getNearbyWords(words, "a word", 3)
    assert ['cedric', 'is', 'maniac'] == _getNearbyWords(words, "d", 3)
    assert ['maniac', 'this', 'zippy'] == _getNearbyWords(words, "w", 3)
    assert ['maniac', 'this', 'zippy'] == _getNearbyWords(words, "zzzezo", 3)
    # print "test_getNearbyWords() is ok!\n"

def _buildNearbyWords(df, nearbyWords, dictCode):
    if len(nearbyWords) > 0:
        df.TextElement("Nearby words: ", style=styleNameBold)
        first = True
        for word in nearbyWords:
            if first:
                first = False
            else:
                df.TextElement(", ")
            link = "s+dictterm:%s %s" % (dictCode.strip(), word)
            df.TextElement(word, link=link)
        df.LineBreakElement()

def buildDefinitionNotFound(word, nearbyWords, dictCode):
    df = Definition()
    df.TextElement("Definition for word '%s' was not found." % word)
    df.LineBreakElement(3,2)
    _buildNearbyWords(df, nearbyWords, dictCode)

    return df

# a synset is:
#  list of words
#  part of speech
#  definition
#  list of examples
class Synset:
    def __init__(self):
        self.words = []
        self.pos = None
        self.defTxt = None
        self.examples = []

# parse definition and return an array of synsets
def _parseDef(wordDef):
    synsets = []

    curSynset = Synset()
    fInDef = False
    fCanFinish = False
    for line in string.split(wordDef.strip(), "\n"):
        # print line.strip()
        if 0 == len(line):
            assert fCanFinish
            # we assume this is an empty line dividing synsets
            synsets.append(curSynset)
            curSynset = Synset()
            fInDef = False
            fCanFinish = False
        elif '!' == line[0]:
            if fInDef:
                synsets.append(curSynset)
                curSynset = Synset()
                fInDef = False
            # this is a one of the words
            word = line[1:].strip()
            curSynset.words.append(word)
            fCanFinish = False
        elif '$' == line[0]:
            pos = line[1:].strip()
            curSynset.pos = pos
        elif '@' == line[0]:
            curSynset.defTxt = line[1:].strip()
            fInDef = True
            fCanFinish = True
        elif '#' == line[0]:
            example = line[1:].strip()
            curSynset.examples.append(example)
            fCanFinish = True
        else:
            assert fInDef
            curSynset.defTxt = "%s\n%s" % (curSynset.defTxt, line.strip())
            fCanFinish = True
    synsets.append(curSynset)
    return synsets

def _posToText(pos):
    if pos == "n":
        return "(Noun)"
    if pos == "v":
        return "(Verb)"
    if pos == "r":
        return "(Adv.)"
    if pos in ["s", "a"]:
        return "(Adj.)"
    print "Unknown pos:%s" % pos
    return "(%s)" % pos

def test_parseDefAll():
    global g_wnWords
    print "parsing all definitions"
    n = 1
    for word in g_wnWords:
        if 0 == n % 20000:
            print "processed %d" % n
        wordDef = _getDef(word)
        try:
            synsets = _parseDef(wordDef)
        except Exception, ex:
            print "word: %s" % word
            print "def: '%s'" % wordDef
            raise
        n = n + 1
    print "finished parsing all definitions"

# build a Definition object for a found definition
def buildDefinitionFound(word, wordDef, nearbyWords, dictCode):
    df = Definition()
    synsets = _parseDef(wordDef)
    print synsets

    styleNameExample = df.AddStyle("ex", color=[127,63,0])
    df.TextElement(word, style=styleNamePageTitle)
    #df.LineBreakElement(1,2)

    for synset in synsets:
        df.BulletElement(False)
        df.TextElement(_posToText(synset.pos)+" ", style=styleNameGreen)
        df.TextElement(synset.defTxt)
        for ex in synset.examples:
            df.LineBreakElement()
            gtxt = df.TextElement("\""+ex+"\"")
            gtxt.setStyleName(styleNameExample)
        if len(synset.words) > 1:
            df.LineBreakElement()
            df.TextElement("Synonyms: ", style=styleNameBold)
            first = False
            for syn in synset.words:
                if syn != word:
                    if first:
                        df.TextElement(", ")
                    else:
                        first = True
                    df.TextElement(syn, link="s+dictterm:%s %s" % (dictCode.strip(), syn))
        df.PopParentElement()

    df.LineBreakElement()
    df.LineBreakElement()
    _buildNearbyWords(df, nearbyWords, dictCode)
    return df

def getDictionaryRandom(dictCode, fDebug=False):
    global g_wnWords, g_fDisabled
    initDictionary()
    if g_fDisabled:
        return (MODULE_DOWN, None)

    udf = None
    word = ""
    dictCode = dictCode.split()[0]
    # dict code have code + random number.
    if dictCode.startswith("wn"):
        totalWords = len(g_wnWords)
        randomWordNo = g_random.randint(0, totalWords-1)
        word = g_wnWords[randomWordNo]
        nearbyWords = _getNearbyWords(g_wnWords, word, NEARBY_WORDS_TO_SHOW)
        wordDef = _getDef(word)
        assert None != wordDef
        df = buildDefinitionFound(word, wordDef, nearbyWords, dictCode)
        udf = universalDataFormatWithDefinition(df, [["H", word]])
    else:
        return (INVALID_REQUEST, None)


    if fDebug:
        print "random word is %s" % word
    return (DICT_DEF, udf)

# given search term in the form:
#   dictName SPACE searchTerm
# return a tuple (resultType, resultData). If resultType is DICT_DEF, resultData
# is a serialized definition containing dictionary definition to be displayed
# to the user. Other resultType indicates an error.
def getDictionaryDef(searchTerm, fDebug=False):
    global g_wnWords, g_fDisabled
    initDictionary()
    if g_fDisabled:
        return (MODULE_DOWN, None)

    parts = searchTerm.split(" ", 1)
    if 1 == len(parts):
        return (INVALID_REQUEST, None)
    assert 2 == len(parts)
    (dictName, word) = parts
    word = word.strip()

    if dictName != "wn":
        return (INVALID_REQUEST, None)

    nearbyWords = _getNearbyWords(g_wnWords, word, NEARBY_WORDS_TO_SHOW)

    wordDef = _getDef(word)

    if fDebug:
        if None == wordDef:
            print "definition of '%s' not found" % word
            print nearbyWords
        else:
            print wordDef

    # TODO: ispell and lupy
    if None == wordDef:
        df = buildDefinitionNotFound(word, nearbyWords, dictName)
    else:
        df = buildDefinitionFound(word, wordDef, nearbyWords, dictName)

    udf = universalDataFormatWithDefinition(df, [["H", word]])

    return (DICT_DEF, udf)

# request is dict type ("wn " for now)
def getDictionaryStats(request):
    global g_wnWords, g_fDisabled
    initDictionary()
    if g_fDisabled:
        return (MODULE_DOWN, None)
    
    request = request.strip()
    if 0 == len(request) or "private" == request:
        # TODO: null request can return page, to select dictionary...
        private = False
        if "private" == request:
            private = True



            
        pass

    res = []        
    if "wn" == request:
        res.append(["N","Word net"])
        res.append(["S","wn "])
        res.append(["C",str(len(g_wnWords))])
    else:
        return INVALID_REQUEST, None
    return RESULTS_DATA, universalDataFormat(res)

def usage():
    print "dictionary.py searchTerm"

def main():
    # Import Psyco if available
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    if "-test" in sys.argv:
        initDictionary()
        test_parseDefAll()
        test_getNearbyWords()
        pos = sys.argv.index("-test")
        del sys.argv[pos]

    if 2 != len(sys.argv):
        usage()
        sys.exit(0)

    if "random" == sys.argv[1]:
        (resultType, resultBody) = getDictionaryRandom("wn ", fDebug=True)
    else:
        searchTerm = "wn %s" % sys.argv[1]
        (resultType, resultBody) = getDictionaryDef(searchTerm, fDebug=True)
    if INVALID_REQUEST == resultType:
        print "invalid request"
    if DICT_DEF == resultType:
        print resultBody
    deinitDictionary()

if __name__ == "__main__":
    main()

