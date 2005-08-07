# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk / Szymon Knitter
#
# Purpose:
#  dictionary module
#
import sys, os, os.path, string, bisect, cPickle, random, popen2
from threading import Lock
import multiUserSupport, parserUtils, arsutils
from ResultType import *
from parserUtils import universalDataFormatWithDefinition, universalDataFormat
from definitionBuilder import *
from arsutils import log, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC, exceptionAsStr
import threading

try:
    from lupy.indexer import Index as LupyIndex
    import lupy
except:
    print "requires Lupy module from http://www.divmod.org/Home/Projects/Lupy/"
    raise

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

g_wnDictPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, "wn-dict.txt")
g_wnIndexPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, "wn-words-index.pic")
g_wnWordsPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, "wn-words.pic")
g_wnLupyIndexPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, "wn-index-lupy")
g_wnLupyIndexedCount = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, "wn-index-lupy-count.txt")

g_fWnLupyIndexExamples = False

TH_DICT_FILE  = "th-dict.txt"
TH_INDEX_FILE = "th-words-index.pic"
TH_WORDS_FILE = "th-words.pic"

g_thDictPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, TH_DICT_FILE)
g_thIndexPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, TH_INDEX_FILE)
g_thWordsPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, TH_WORDS_FILE)

# how many nearby words we show
NEARBY_WORDS_TO_SHOW = 8

# it's ok to throw an exception, we don't want to proceed if the file is missing
# TODO: somehow make it that this file is closed when we kill InfoMan
g_wnFo = None
g_wnWordIndex = {}
g_wnWords = []

g_thFo = None
g_thWordIndex = {}
g_thWords = []

# random.Random() object used to generate random definitions. Must be initialized
# in initDictionary
g_random = None

# protect WN_DICT_FILE file access from multi-thread issues
g_wnDefReadLock = None
g_thDefReadLock = None

# a flag used to make sure initDictionary() is called only once
g_fInitialized = False

# g_fDisabled is set in initDictionar() it's True if there are no dictionary files
g_fDisabled = None

# dicts code
WORDNET_CODE = 'wn'
THESAURUS_CODE = 'th'

# flags
FLAG_EXAMPLES_OFF = 'e'
FLAG_SYNONYMS_OFF = 's'
FLAG_NEARBY_WORDS_OFF = 'n'
FLAG_COMPACT = 'o'

g_availableDicts = {
    "wn:" : ["wn:", "an English dictionary", "WordNet", WORDNET_CODE],
    #"wn:e" : ["wn:e", "an English dictionary (without examples)", "WordNet without examples", WORDNET_CODE],
    #"wn:s" : ["wn:s", "an English dictionary (without synonyms)", "WordNet without synonyms", WORDNET_CODE],
    #"wn:n" : ["wn:n", "an English dictionary (without nearby words)", "WordNet without nearby words", WORDNET_CODE],
    #"wn:esn" : ["wn:esn", "an English dictionary (mini)", "WordNet mini", WORDNET_CODE],
    "wn:o" : ["wn:o", "an English dictionary (compact)", "WordNet compact", WORDNET_CODE],
    
    "th:" : ["th:", "an English Thesaurus", "Thesaurus full", THESAURUS_CODE],
    #"th:n" : ["th:n", "an English Thesaurus (without nearby words)", "Theasaurus without nearby words", THESAURUS_CODE],
    "th:on" : ["th:on", "an English Thesaurus (compact)", "Thesaurus compact", THESAURUS_CODE],
}

# this is a list of dictionaries, sorted by name. It's build from g_availableDicts
# each element is the key to g_availableDicts
g_dictsSortedByName = None

def buildDictsSortedByName():
    global g_availableDicts, g_dictsSortedByName
    assert None == g_dictsSortedByName
    names = []
    for val in g_availableDicts.values():
        name = val[2]
        names.append(name)
    names.sort()
    g_dictsSortedByName = []
    for name in names:
        # not very efficient, but what the hell
        for (key, val) in g_availableDicts.items():
            if val[2] == name:
                g_dictsSortedByName.append(key)
    print g_dictsSortedByName

buildDictsSortedByName()

def flagsHaveFlag(flags, flag):
    return -1 != flags.find(flag)

def getWordsCount(dictCode):
    initDictionary()
    dictCode = dictCode.split(":")[0]
    if dictCode == WORDNET_CODE:
        return len(g_wnWords)
    if dictCode == THESAURUS_CODE:
        return len(g_thWords)
    return 0

# Lupy index.
# main method is g_lupyIndex.getWords(word, dictCode)
# init must call g_lupyIndex.initialize()
class DictLupyIndex:
    def __init__(self):
        self._lock = Lock()
        self._initializated = False
        self._index = {}
        self._failedToInit = False

#	index.close() ??

    def fInitialized(self):
        return self._initializated and not self._failedToInit

    def fNeedInitialization(self):
        if self._initializated:
            return False
        if self._failedToInit:
            return False
        return True

    def initialize(self):
        print "init lupy index from dict module"
        self._failedToInit = True
        # wordNet
        try:
            self._index[WORDNET_CODE] = lupy.indexer.Index(g_wnLupyIndexPath)
        except:
            try:
                self._index[WORDNET_CODE] = lupy.indexer.Index(g_wnLupyIndexPath, True)
            except:
                print " failed to init - lupy missing?"
                self._failedToInit = True
                return
        i = 0
        try:
            fo = open(g_wnLupyIndexedCount, "rt")
            i = int(fo.read())
            fo.close()
        except:
            pass

        end = len(g_wnWords)
        if i < end:
            while i < end:
                word = g_wnWords[i]
                if i % 1000 == 0:
                    print " wn - %d words indexed" % i
                synsets = _wnParseDef(_wnGetDef(word))
                text = ""
                for syn in synsets:
                    text += syn.defTxt
                    if g_fWnLupyIndexExamples:
                        text += " ; " + string.join(syn.examples, " ")
                    text += " ; "
                self._index[WORDNET_CODE].index(text=text, __title=word)
                if i % 100 == 0:
                    self._index[WORDNET_CODE].flush()
                    fo = open(g_wnLupyIndexedCount, "wt")
                    fo.write(str(i))
                    fo.close()
                i += 1
            print " optimize"
            self._index[WORDNET_CODE].flush()
            fo = open(g_wnLupyIndexedCount, "wt")
            fo.write(str(end))
            fo.close()

            self._index[WORDNET_CODE].optimize()
        print " lupy index for dict module initialized"
        self._initializated = True
        self._failedToInit = False

    def getWords(self, word, dictCode):
        if self.fNeedInitialization():
            initLupyIndex(inThread = True)
            return []
        if not self.fInitialized():
            print "Index not ready."
            return []
        results = []        
        hits = []
        try:
            if self._index[dictCode]:
                pass
        except:
            print "Index for dict code:%s is not available!" % dictCode
            return []
        
        self._lock.acquire()
        try:
            hits = self._index[dictCode].find(word)
        finally:
            self._lock.release()

        for h in hits:
            results.append(h.get('title'))

        return results

g_lupyIndex = DictLupyIndex()

class RunLupyThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global g_lupyIndex
        print "Thread start (dict lupy index)"
        try:
            g_lupyIndex.initialize()
        except Exception, ex:
            txt = arsutils.exceptionAsStr(ex)
            log(SEV_EXC, "exception in lupy index dictionary\n%s\n" % (txt))
        print "Thread stop (dict lupy index)"

def initLupyIndex(inThread = True):
    global g_lupyIndex
    if inThread:
        th = RunLupyThread()
        th.start() 
    else:
        g_lupyIndex.initialize()

# based on http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/117221
# probably won't work on windows
class aspell:
    def __init__(self):
        self._f = popen2.Popen3("aspell -a")
        self._f.fromchild.readline() #skip the credit line
    def __call__(self, word):
        self._f.tochild.write(word+'\n')
        self._f.tochild.flush()
        s = self._f.fromchild.readline()
        self._f.fromchild.readline() #skip the blank line
        if s[:8]=="word: ok":
            return None
        else:
            return (s[17:-1]).split(', ')

# an active session to aspell process
g_aspell = None

# True if we failed to create an active session to aspell process
# (this might happen if e.g. there is no aspell executable like, for example,
# on windows
g_fAspellFailed = False

g_aspellLock = Lock()

# given a word, return a list of spell-checking suggestions. Returns None if
# there are not suggestions or if we cannot talk to aspell process
def getSpellcheckSuggestions(word):
    global g_aspell, g_fAspellFailed, g_aspellLock
    # TODO: probably needs to be wrapped in a Lock for multi-threaded safety
    # since it uses just one aspell process to do its job
    # also, not sure what will happen if the aspell process dies (if it can happen)
    # maybe it also needs a try/catch block and re-create aspell object (to open
    # connection to a new aspell process)
    if g_fAspellFailed:
        return None

    suggestions = []
    g_aspellLock.acquire()
    try:
        if None == g_aspell:
            try:
                g_aspell = aspell()
                print "opened connection to aspell"
            except Exception, ex:
                # assume we failed to open connection to aspell process
                print "failed to open connection to aspell"
                g_fAspellFailed = True
        if not g_fAspellFailed:
            suggestions = g_aspell(word)
    finally:
        g_aspellLock.release()

    if 0 == len(suggestions):
        return None
    # if list of suggestions consists of only one empty string, it means no
    # suggestions
    if 1 == len(suggestions) and 0 == len(suggestions[0]):
        return None
    return suggestions

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

    global g_thWords, g_thWordIndex, g_thDictPath, g_thIndexPath, g_thWordsPath
    print "loading th dictionary data files"

    if not arsutils.fFileExists(g_thDictPath):
        print "Thesaurus dictionary file '%s' doesn't exist" % g_thDictPath
        return False

    if not arsutils.fFileExists(g_thIndexPath):
        print "Thesaurus dictionary file '%s' doesn't exist" % g_thIndexPath
        return False

    if not arsutils.fFileExists(g_thWordsPath):
        print "Thesaurus dictionary file '%s' doesn't exist" % g_thWordsPath
        return False

    try:
        fo = open(g_thIndexPath, "rb")
        g_thWordIndex = cPickle.load(fo)
        fo.close()

        fo = open(g_thWordsPath, "rb")
        g_thWords = cPickle.load(fo)
        fo.close()
    except Exception, ex:
        print arsutils.exceptionAsStr(ex)
        return False
    print "Finished loading Thesaurus files"
    return True


def initDictionary():
    global g_wnFo, g_wnDictPath, g_wnDefReadLock, g_random, g_fInitialized, g_fDisabled
    global g_thFo, g_thDictPath, g_thDefReadLock
    if g_fInitialized:
        return
    g_fInitialized = True
    g_fDisabled = True
    if not loadPickledFiles():
        return
    try:
        assert None == g_wnFo
        g_wnFo = open(g_wnDictPath, "rb")
        assert None == g_wnDefReadLock
        g_wnDefReadLock = Lock()
        assert None == g_thFo
        g_thFo = open(g_thDictPath, "rb")
        assert None == g_thDefReadLock
        g_thDefReadLock = Lock()
        assert None == g_random
        g_random = random.Random()
        g_random.seed()
    except Exception, ex:
        print arsutils.exceptionAsStr(ex)
        return
    g_fDisabled = False

def deinitDictionary():
    global g_wnFo, g_fInitialized
    global g_thFo
    if not g_fInitialized:
        return
    print "deinitDictionary()"
    if None != g_wnFo:
        g_wnFo.close()
    if None != g_thFo:
        g_thFo.close()

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
def _wnGetDef(word):
    global g_wnFo, g_wnDefReadLock, g_wnWordIndex

    if not g_wnWordIndex.has_key(word):
        return None

    wordDef = None
    (defOffset, defLen) = g_wnWordIndex[word]
    g_wnDefReadLock.acquire()
    try:
        g_wnFo.seek(defOffset, 0)   # 0 - absolute positioning
        wordDef = g_wnFo.read(defLen)
    finally:
        g_wnDefReadLock.release()
    return wordDef

def _thGetDef(word):
    global g_thFo, g_thDefReadLock, g_thWordIndex

    if not g_thWordIndex.has_key(word):
        return None

    wordDef = None
    pairs = g_thWordIndex[word]
    try:
        g_thDefReadLock.acquire()
        wd2 = []
        for (defOffset, defLen) in pairs:
            g_thFo.seek(defOffset, 0)   # 0 - absolute positioning
            wd2.append(g_thFo.read(defLen))
        wordDef = wd2
    finally:
        g_thDefReadLock.release()
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

def _buildSuggestions(df, origWord, suggestions, dictCode, flags):
    if len(suggestions) > 0:
        df.LineBreakElement()
        df.LineBreakElement()
        df.TextElement("Did you mean: ", style=styleNameBold)
        first = True
        for word in suggestions:
            if first:
                first = False
            else:
                df.TextElement(", ")
            link = "s+dictterm:%s:%s:%s" % (dictCode, flags, word)
            df.TextElement(word, link=link)

def _buildLupyResults(df, origWord, suggestions, dictCode, flags):
    if len(suggestions) > 0:
        df.LineBreakElement()
        df.LineBreakElement()
        df.TextElement("Definitions that contains: %s" % origWord, style=styleNameBold)
        df.LineBreakElement()
        first = True
        if len(suggestions) > 20:
            print "Found: %d words with this" % len(suggestions)
            suggestions = suggestions[:20]

        for word in suggestions:
            if first:
                first = False
            else:
                df.TextElement(", ")
            link = "s+dictterm:%s:%s:%s" % (dictCode, flags, word)
            df.TextElement(word, link=link)

def _buildNearbyWords(df, origWord, nearbyWords, dictCode, flags):
    if len(nearbyWords) > 0:
        df.LineBreakElement()
        df.LineBreakElement()
        df.TextElement("Nearby words: ", style=styleNameBold)
        first = True
        for word in nearbyWords:
            if first:
                first = False
            else:
                df.TextElement(", ")
            if origWord != word:
                link = "s+dictterm:%s:%s:%s" % (dictCode, flags, word)
                df.TextElement(word, link=link)
            else:
                df.TextElement(word)

def buildDefinitionNotFound(word, nearbyWords, dictCode, flags, suggestions, lupyResults):
    df = Definition()
    df.TextElement("Home", link="dictform:main") 
    df.TextElement(" / Definition for word '%s' was not found." % word)
    _buildSuggestions(df, word, suggestions, dictCode, flags)
    _buildNearbyWords(df, word, nearbyWords, dictCode, flags)
    _buildLupyResults(df, word, lupyResults, dictCode, flags)

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

def sortByPos(el1, el2):
    return cmp(el1.pos, el2.pos)

# parse definition and return an array of synsets
def _wnParseDef(wordDef):
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
    # sort synsets by pos.
    synsets.sort(sortByPos)    
    return synsets

def _thParseDef(wordDef):
    synsets = []

    for el in wordDef:
        curSynset = Synset()
        curSynset.words = el[1:].split(", ")
        curSynset.defTxt = ""
        curSynset.exaples = []
        curSynset.pos = el[0]
        synsets.append(curSynset)
    # sort synsets by pos.
    synsets.sort(sortByPos)    
    return synsets

def _posToText(pos):
    if pos == "n":
        return "Noun"
    if pos == "v":
        return "Verb"
    if pos == "r":
        return "Adv."
    if pos in ["s", "a"]:
        return "Adj."
    print "Unknown pos:%s" % pos
    return "(%s)" % pos

def test_wnParseDefAll():
    global g_wnWords
    print "parsing all definitions"
    n = 1
    for word in g_wnWords:
        if 0 == n % 20000:
            print "processed %d" % n
        wordDef = _wnGetDef(word)
        try:
            synsets = _wnParseDef(wordDef)
        except Exception, ex:
            print "word: %s" % word
            print "def: '%s'" % wordDef
            raise
        n = n + 1
    print "finished parsing all definitions"

def moreThanOnePosInSynsets(synsets):
    if len(synsets) > 0:
        pos = synsets[0].pos
        for synset in synsets:
            if synset.pos != pos:
                return True
    return False

# build a Definition object for a found definition
def buildDefinitionFound(word, wordDef, nearbyWords, dictCode, flags):
    df = Definition()
    if dictCode == WORDNET_CODE:
        synsets = _wnParseDef(wordDef)
    elif dictCode == THESAURUS_CODE:
        synsets = _thParseDef(wordDef)
    else:
        assert 0
    styleNameExample = df.AddStyle("ex", color=[127,63,0])
    df.TextElement("Home", link="dictform:main")
    df.TextElement(" / ")
    df.TextElement(word, style=styleNameBoldBlue)

    moreThanOnePos = moreThanOnePosInSynsets(synsets)
    roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    i = 0
    posNumber = 0
    listNumber = 1
    currPos = ""
    while i < len(synsets):
        synset = synsets[i]
        if flagsHaveFlag(flags, FLAG_COMPACT):
            df.LineBreakElement()
            df.TextElement("\x95 ")
            df.TextElement(_posToText(synset.pos)+" ", style=styleNameGreen)
        else:
            if currPos != synset.pos:
                listNumber = 1
                currPos = synset.pos
                if moreThanOnePos:
                    df.LineBreakElement()
                    df.TextElement(roman[posNumber] + " " + _posToText(synset.pos), style=styleNameBoldGreen)
                    posNumber += 1
                else:
                    df.LineBreakElement()
                    df.TextElement(_posToText(synset.pos), style=styleNameBoldGreen)

            df.LineBreakElement()
            if listNumber == 1:
                if i == len(synsets)-1:
                    pass
                elif currPos != synsets[i+1].pos:
                    pass
                else:
                    df.TextElement("%d) " % listNumber)
            else:
                df.TextElement("%d) " % listNumber)
            listNumber += 1

        df.TextElement(synset.defTxt)
        if not flagsHaveFlag(flags, FLAG_EXAMPLES_OFF):
            for ex in synset.examples:
                df.LineBreakElement()
                gtxt = df.TextElement("\""+ex+"\"")
                gtxt.setStyleName(styleNameExample)
        if len(synset.words) > 1 and not flagsHaveFlag(flags, FLAG_SYNONYMS_OFF):
            if "" != synset.defTxt or len(synset.examples)>0:
                df.LineBreakElement()
                df.TextElement("Synonyms: ", style=styleNameBold)
                first = False
                for syn in synset.words:
                    if syn != word:
                        if first:
                            df.TextElement(", ")
                        else:
                            first = True
                        df.TextElement(syn, link="s+dictterm:%s:%s:%s" % (dictCode, flags, syn))
            else:
                df.TextElement(string.join(synset.words, ", "))

        i += 1

    if not flagsHaveFlag(flags, FLAG_NEARBY_WORDS_OFF):
        _buildNearbyWords(df, word, nearbyWords, dictCode, flags)
    return df

# get definition of random word for a given dictionary. randomUrl is in the format:
# 'dictCode:$num' (e.g. 'wn:5') where dictCode identifies dictionary to use
# and $num is for implementing history on the client side
def getDictionaryRandom(randomUrl, fDebug=False):
    global g_wnWords, g_fDisabled
    initDictionary()
    if g_fDisabled:
        return (MODULE_DOWN, None)

    parts = randomUrl.split(":")
    dictCode = parts[0]
    flags = parts[1]
    
    if WORDNET_CODE == dictCode:
        totalWords = len(g_wnWords)
        randomWordNo = g_random.randint(0, totalWords-1)
        word = g_wnWords[randomWordNo]
        nearbyWords = _getNearbyWords(g_wnWords, word, NEARBY_WORDS_TO_SHOW)
        wordDef = _wnGetDef(word)
    elif THESAURUS_CODE == dictCode:
        totalWords = len(g_thWords)
        randomWordNo = g_random.randint(0, totalWords-1)
        word = g_thWords[randomWordNo]
        nearbyWords = _getNearbyWords(g_thWords, word, NEARBY_WORDS_TO_SHOW)
        wordDef = _thGetDef(word)
    else:
        return (INVALID_REQUEST, None)

    assert None != wordDef
    df = buildDefinitionFound(word, wordDef, nearbyWords, dictCode, flags)
    udf = universalDataFormatWithDefinition(df, [["H", word]])

    if fDebug:
        print "random word is %s" % word
    return (DICT_DEF, udf)

# given search term in the form:
#   dictCode SPACE searchTerm
# return a tuple (resultType, resultData). If resultType is DICT_DEF, resultData
# is a serialized definition containing dictionary definition to be displayed
# to the user. Other resultType indicates an error.
def getDictionaryDef(searchTerm, fDebug=False):
    global g_wnWords, g_fDisabled
    initDictionary()
    if g_fDisabled:
        return (MODULE_DOWN, None)

    parts = searchTerm.split(":", 2)
    if 3 != len(parts):
        return (INVALID_REQUEST, None)
    assert 3 == len(parts)
    (dictCode, flags, word) = parts
    word = word.strip()

    if WORDNET_CODE == dictCode:
        words = g_wnWords
        wordDef = _wnGetDef(word)
    elif THESAURUS_CODE == dictCode:
        words = g_thWords
        wordDef = _thGetDef(word)
    else:
        return (INVALID_REQUEST, None)

    nearbyWords = _getNearbyWords(words, word, NEARBY_WORDS_TO_SHOW)

    if fDebug:
        if None == wordDef:
            print "definition of '%s' not found" % word
            print nearbyWords
        else:
            print wordDef

    if None == wordDef:
        # lupy
        if WORDNET_CODE == dictCode:
            lupyResults = g_lupyIndex.getWords(word, dictCode)
        else:
            lupyResults = []
        # ispell
        suggestionsUnfiltred = getSpellcheckSuggestions(word)
        suggestions = []
        if suggestionsUnfiltred != None:
            for sug in suggestionsUnfiltred:
                if sug in words:
                    suggestions.append(sug)

        df = buildDefinitionNotFound(word, nearbyWords, dictCode, flags, suggestions, lupyResults)
    else:
        df = buildDefinitionFound(word, wordDef, nearbyWords, dictCode, flags)

    udf = universalDataFormatWithDefinition(df, [["H", word]])

    return (DICT_DEF, udf)

def _getAvailableDicts(private):
    global g_availableDicts, g_dictsSortedByName
    assert None != g_dictsSortedByName
    initDictionary()
    if g_fDisabled:
        return (MODULE_DOWN, None)

    df = Definition()
    df.TextElement("Home", link="dictform:main")
    df.TextElement(" / Select dictionary")
    df.LineBreakElement(1,2)

    for name in g_dictsSortedByName:
        df.BulletElement(False)
        df.TextElement(g_availableDicts[name][2], link="s+dictstats:%s" % g_availableDicts[name][0])
        df.PopParentElement()

    # TODO: if private then add some private dicts
        
    udf = universalDataFormatWithDefinition(df, [["H", "Change dictionary"]])
    return (DICT_DEF, udf)

# request is dict type ("wn" for now)
def getDictionaryStats(request):
    global g_wnWords, g_fDisabled
    global g_availableDicts
    initDictionary()
    if g_fDisabled:
        return (MODULE_DOWN, None)
    
    request = request.strip()
    if 0 == len(request) or "private" == request:
        # TODO: null request can return page, to select dictionary...
        private = False
        if "private" == request:
            private = True

        return _getAvailableDicts(private)

    res = []

    if request in g_availableDicts:
        res.append(["N",g_availableDicts[request][1]])
        res.append(["S", g_availableDicts[request][0]])
        res.append(["C",str(getWordsCount(request))])
    else:
        return INVALID_REQUEST, None
    return RESULTS_DATA, universalDataFormat(res)

def testThes():
    pass

def usage():
    print "dictionary.py searchTerm"

def main():
    global g_lupyIndex
    # Import Psyco if available
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    if "-test" in sys.argv:
        initDictionary()
        test_wnParseDefAll()
        test_getNearbyWords()
        pos = sys.argv.index("-test")
        del sys.argv[pos]

    if "-lupy" in sys.argv:
        initDictionary()
        initLupyIndex(inThread = False)

        pos = sys.argv.index("-lupy")
        del sys.argv[pos]

    if "-thes" in sys.argv:
        initDictionary()

        testThes()
        
        pos = sys.argv.index("-thes")
        del sys.argv[pos]

    if 2 != len(sys.argv):
        usage()
        sys.exit(0)

    if "random" == sys.argv[1]:
        (resultType, resultBody) = getDictionaryRandom(WORDNET_CODE, fDebug=True)
    else:
        searchTerm = "%s:%s" % (WORDNET_CODE, sys.argv[1])
        (resultType, resultBody) = getDictionaryDef(searchTerm, fDebug=True)
    if INVALID_REQUEST == resultType:
        print "invalid request"
    if DICT_DEF == resultType:
        print resultBody
    deinitDictionary()

if __name__ == "__main__":
    main()

