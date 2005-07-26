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
WN_DICT_FILE  = "wn-dict.txt"
WN_INDEX_FILE = "wn-words-index.pic"
WN_WORDS_FILE = "wn-words.pic"

g_wnDictPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, WN_DICT_FILE)
g_wnIndexPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, WN_INDEX_FILE)
g_wnWordsPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, WN_WORDS_FILE)
g_wnLupyIndexPath = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, "wn-index-lupy")
g_wnLupyIndexedCount = os.path.join(multiUserSupport.getServerStorageDir(), DICT_DIR, "wn-index-lupy-count.txt")

g_fWnLupyIndexExamples = False

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

WORDNET_CODE = 'wn'
THESAURUS_CODE = 'th'

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
                synsets = _parseDef(_getDef(word))
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
        if self._failedToInit:
            return []        
        if not self._initializated:
            self.initialize()            
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

def initLupyIndex(inThread = True):
    if inThread:
        pass
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

def _buildSuggestions(df, origWord, suggestions, dictCode):
    if len(suggestions) > 0:
        df.LineBreakElement()
        df.LineBreakElement()
        df.TextElement("Suggestions: ", style=styleNameBold)
        first = True
        for word in suggestions:
            if first:
                first = False
            else:
                df.TextElement(", ")
            link = "s+dictterm:%s:%s" % (dictCode.strip(), word)
            df.TextElement(word, link=link)

def _buildLupyResults(df, origWord, suggestions, dictCode):
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
            link = "s+dictterm:%s:%s" % (dictCode.strip(), word)
            df.TextElement(word, link=link)

def _buildNearbyWords(df, origWord, nearbyWords, dictCode):
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
                link = "s+dictterm:%s:%s" % (dictCode.strip(), word)
                df.TextElement(word, link=link)
            else:
                df.TextElement(word)

def buildDefinitionNotFound(word, nearbyWords, dictCode, suggestions, lupyResults):
    df = Definition()
    df.TextElement("Definition for word '%s' was not found." % word)
    _buildNearbyWords(df, word, nearbyWords, dictCode)
    _buildSuggestions(df, word, suggestions, dictCode)
    _buildLupyResults(df, word, lupyResults, dictCode)

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

def moreThanOnePosInSynsets(synsets):
    if len(synsets) > 0:
        pos = synsets[0].pos
        for synset in synsets:
            if synset.pos != pos:
                return True
    return False

# build a Definition object for a found definition
def buildDefinitionFound(word, wordDef, nearbyWords, dictCode):
    df = Definition()
    synsets = _parseDef(wordDef)

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
                    df.TextElement(syn, link="s+dictterm:%s:%s" % (dictCode.strip(), syn))
        i += 1

    _buildNearbyWords(df, word, nearbyWords, dictCode)
    return df

# get definition of random word for a given dictionary. randomUrl is in the format:
# 'dictCode:$num' (e.g. 'wn:5') where dictCode identifies dictionary to use
# and $num is for implementing history on the client side
def getDictionaryRandom(randomUrl, fDebug=False):
    global g_wnWords, g_fDisabled
    initDictionary()
    if g_fDisabled:
        return (MODULE_DOWN, None)

    dictCode = randomUrl.split(":",1)[0]
    if WORDNET_CODE != dictCode:
        return (INVALID_REQUEST, None)

    totalWords = len(g_wnWords)
    randomWordNo = g_random.randint(0, totalWords-1)
    word = g_wnWords[randomWordNo]
    nearbyWords = _getNearbyWords(g_wnWords, word, NEARBY_WORDS_TO_SHOW)
    wordDef = _getDef(word)
    assert None != wordDef
    df = buildDefinitionFound(word, wordDef, nearbyWords, dictCode)
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

    parts = searchTerm.split(":", 1)
    if 1 == len(parts):
        return (INVALID_REQUEST, None)
    assert 2 == len(parts)
    (dictCode, word) = parts
    word = word.strip()

    if dictCode != WORDNET_CODE:
        return (INVALID_REQUEST, None)
    words = g_wnWords

    nearbyWords = _getNearbyWords(words, word, NEARBY_WORDS_TO_SHOW)

    wordDef = _getDef(word)

    if fDebug:
        if None == wordDef:
            print "definition of '%s' not found" % word
            print nearbyWords
        else:
            print wordDef

    if None == wordDef:
        # lupy
        print "lupy start searching"
        lupyResults = g_lupyIndex.getWords(word, dictCode)
        print "lupy end searching"
        # ispell
        suggestionsUnfiltred = getSpellcheckSuggestions(word)
        suggestions = []
        if suggestionsUnfiltred != None:
            for sug in suggestionsUnfiltred:
                if sug in words:
                    suggestions.append(sug)

        df = buildDefinitionNotFound(word, nearbyWords, dictCode, suggestions, lupyResults)
    else:
        df = buildDefinitionFound(word, wordDef, nearbyWords, dictCode)

    udf = universalDataFormatWithDefinition(df, [["H", word]])

    return (DICT_DEF, udf)

def _getAvailableDicts(private):
    initDictionary()
    if g_fDisabled:
        return (MODULE_DOWN, None)

    df = Definition()
    df.TextElement("Home", link="dictform:main")
    df.TextElement(" / Select dictionary")
    df.LineBreakElement(3,2)

    df.TextElement("We're sorry, but for now only ")
    df.TextElement("WordNet", link="s+dictstats:wn")
    df.TextElement(" dictionary is available.")

    df.LineBreakElement(3,2)

    df.TextElement("test other", link="s+dictstats:th")
    df.TextElement(" this is not working dict - only to test dict change page.")

    udf = universalDataFormatWithDefinition(df, [["H", "Change dictionary"]])
    return (DICT_DEF, udf)

# request is dict type ("wn" for now)
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

        return _getAvailableDicts(private)

    res = []        
    if WORDNET_CODE == request:
        res.append(["N","an English"])
        res.append(["S", WORDNET_CODE])
        res.append(["C",str(len(g_wnWords))])
    elif "th" == request:
        res.append(["N","test thesaurus"])
        res.append(["S", "th"])
        res.append(["C","0"])
    else:
        return INVALID_REQUEST, None
    return RESULTS_DATA, universalDataFormat(res)

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
        test_parseDefAll()
        test_getNearbyWords()
        pos = sys.argv.index("-test")
        del sys.argv[pos]

    if "-lupy" in sys.argv:
        initDictionary()
        initLupyIndex(inThread = False)

        pos = sys.argv.index("-lupy")
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

