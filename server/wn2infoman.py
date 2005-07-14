#!/usr/local/bin/python

# Copyright (C) Krzysztof Kowalczyk
# Author: Krzysztof Kowalczyk

# Purpose:
#
# A script to convert WordNet data into something that InfoMan understands
# WordNet data is a set of synsets
# synset is a list of words, part of speech, definition
# and a list of examples

import sys,string, re, cPickle, arsutils, os
from struct import pack

unparsed = []

# wordnet_data_dir = "/home/kjk/src/wn10-10-00/"
# wordnet_data_dir = "c:\\kjk\src\wn10-10-00\\"
#wordnet_data_dir = "C:\\kjk\\src\\mine\\dict_data\\wordnet16\\"
#wordnet_data_dir = "C:\\kjk\\src\\mine\\dicts_data\\wordnet16\\"
wordnet_data_dir = "C:\\kjk\\src\\mine\\dicts_data\\WordNet-20\\dict\\"

# we'll use this file to create a subset of synsets for Noah Lite
#engpolFileName = "c:\\kjk\\src\\mine\\dict_data\\eng_pol.txt"

#dataFiles = [ "data.adv" ]
dataFiles = [ "data.adv", "data.adj", "data.noun", "data.verb" ]

# keeps a mapping offset->Synset so that we can
# keep track of synset relations
synset_off_synset_map = {}

# an array of all synsets defined so far
proSynsets = []
liteSynsets = []

class AllWords:
    def __init__(self):
        self.words = {}
    def add(self,word):
        if not self.words.has_key(word):
            self.words[word] = -1
    def setWordNo(self,word,no):
        self.words[word] = no
    def getWordNo(self,word):
        return self.words[word]
    def getWords(self):
        return self.words
    def getWordsCount(self):
        return len(self.words)
    def wordExistP(self,word):
        return self.words.has_key(word)

proWords = AllWords()
liteWords = AllWords()
epWords = AllWords()

# read the words that match the pattern for a head word
# from eng-pol dictionary file
epWordRe = "^([a-zA-Z\.'-]+)$"
epWordReCompiled = re.compile(epWordRe)
def epIsWord(txt):
    global epWordReCompiled
    if epWordReCompiled.match(txt):
        return 1
    return 0

def readEPWords(fileName):
    epWords = AllWords() 
    wordsHash = {}
    f = open(fileName, "r")
    line = f.readline()
    while line != '':
        if epIsWord(line):
            word = string.strip(line)
            epWords.add(word)
        line = f.readline()
    f.close()
    return epWords

# used to generate sequence of synset IDs
next_synset_id = 0

def sql_qq(txt):
    """Quote a string so that it can be inserted into SQL database"""
    return string.replace(txt,"'", "''")

def map_synset_off_to_synset(synset_off,synset):
    global synset_off_synset_map
    synset_off_synset_map[ synset_off ] = synset

class id_gen:
    def __init__(self, start_id = 1):
        self.next_id = start_id-1
    def get_next(self):
        self.next_id += 1
        return self.next_id

g_noLeft = -1
def write3ByteWordNumber(file, no, fSpecial):
    """Writes a number no to file as a 3-byte such that
    no = 256*256*pos[0]+256*pos[1]+pos[2]. if fSpecial is true
    then additionaly pos[0] should have the first bit set i.e.
    pos[0] |= 0x80 """
    global g_noLeft
    if g_noLeft > 0:
        print "no: %d, fSpecial: %d" % (no, fSpecial)
        g_noLeft -= 1
        
    p0 = no / (256*256)
    assert( (p0 < 0x80) and (p0 >= 0) )
    no = no - (p0*256*256)
    p1 = no / 256
    assert( (p1 <= 0xff) and (p1 >= 0) )
    no = no - p1*256
    p2 = no
    assert( (p2 <= 0xff) and (p2 >= 0) )
    if fSpecial:
        p0 = p0 | 0x80
    assert( (p0 <= 0xff) and (p0 >= 0) )
    file.write( pack("<BBB", p0, p1, p2) )
    
synset_id = id_gen()

class Synset:
    def __init__(self, words=[], part_of_speech='', definition="", examples=[]):
        self.words = words
        self.part_of_speech = part_of_speech
        self.definition = definition
        self.examples = examples
        self.id = synset_id.get_next()
        self.winDef = None

#     def getWords(self):
#         txt = self.words[0]
#         for w in self.words[1:]:
#                 txt = txt + " " + w
#         return txt

    def getWords(self):
        return self.words

    def getPos(self):
        return self.part_of_speech

    def getDefinition(self):
        return self.definition

    def getExamples(self):
        return self.examples

    def getWordsCount(self):
        return len(self.words)

    def getWordsNumbers(self):
        nums = []
        for w in self.words:
            nums.append( proWords.getWordNo(w) )
        return nums

    def getWinDef(self):
        if None != self.winDef:
            return self.winDef
        self.winDef = pack( "c", self.part_of_speech )
        self.winDef += self.definition
        self.winDef += '\0'
        for e in self.examples:
            self.winDef += e
            self.winDef += '\0'
        return self.winDef

    def getWinDefLen(self):
        return len( self.getWinDef() )

    # get XML representation of the synset
    def getXML(self):
        xml_txt = "<SYNSET ID=\"" + repr(self.id) + "\" POS=\"" + self.part_of_speech + "\">\n"
        for w in self.words:
            xml_txt = xml_txt +" <WORD>" + w + "</WORD>\n"
        xml_txt = xml_txt + " <DEF>" + self.definition + "</DEF>\n"
        for e in self.examples:
            xml_txt = xml_txt + " <EXAMPLE>" + e + "</EXAMPLE>\n"
        xml_txt = xml_txt + "</SYNSET>"
        return xml_txt

    def getTxtSimple(self):
        txt = ""
        for w in self.words:
            txt = txt + w + "\n"
        txt = txt + self.part_of_speech + "\n"
        txt = txt + self.definition + "\n"
        for e in self.examples:
            txt = txt + e + "\n"
        return txt

    def getTxtMarked(self):
        txt = ""
        for w in self.words:
            txt = txt + "!" + w + "\n"
        txt = txt + "$" + self.part_of_speech + "\n"
        txt = txt + "@" + self.definition + "\n"
        for e in self.examples:
            txt = txt + "#" + e + "\n"
        return txt

    # convert internal representation to an SQL statements that inserts
    # this synset and word->synset mappings into a database
    def getSqlInXml(self):
        xml_txt = self.getXML()
        sql_txt = "INSERT INTO wn_synset (synset_id, xml_def) VALUES ("
        sql_txt = sql_txt + repr(self.id) + ", '" + sql_qq(xml_txt) + "');\n"
        for w in self.words:
            sql_txt = sql_txt + "INSERT INTO wn_word_synset_map (word, synset_id) VALUES ('" + sql_qq(w) + "', " + repr(self.id) + ");\n"
        return sql_txt

    def getSqlInMarked(self):
        markedTxt = self.getTxtMarked()
        sqlTxt = ""
        for w in self.words:
            sqlTxt = sqlTxt + "INSERT INTO words (word,def,which_db) VALUES ("
            sqlTxt = sqlTxt + "'" + sql_qq(w) + "', '" + sql_qq(markedTxt) + "', 'f' );\n";
        return sqlTxt

# parse a line (string) from the wordnet file and convert the data
# to synset struct
# Input:
#    line - line (string) from the wordnet file
#    nested_level - this function calls itself recursively.
#          We need this to prevent infinite recursion
# format of the line: synset_offset lex_filenum
#   ss_type: n - NOUN, v - VERB, a - ADJ, s - ADJ SATELLITE, r - ADVERB
#   w_cnt - number of words in synset
#   word
#   lex_id (appended into lemma uniquely identifies sense within lex file)
#   p_cnt - number of pointers from this synset to other synsets
#     pointer is:
#        pointer_symbol synset_offset pos source/target
def line_to_synset(line, nested_level=0):
    global synset_off_synset_map
    global proWords
    #print line
    parts = string.split(line, "|")
    gloss_part = string.strip(parts[1])
    info_parts = string.split(parts[0])
    hash_key = info_parts[0] + "_" + info_parts[1]
    part_of_speech = info_parts[2]
    words_count = int(string.strip(info_parts[3]),16)
    words = []
    for i in range(words_count):
        w = info_parts[4+2*i]
        w = w.replace( "_", " ")
        if w not in words:
            words.append(w)
            proWords.add(w)
        #else:
        #    print "duplicate word:", w, "in line:", line

    # now the definition is everything that starts from
    # the beginning of gloss_part until `; "` or `: "`
    # the rest (if at all present) are examples/quotes
    definition_end = string.find(gloss_part, "; \"")
    if definition_end == -1:
        definition_end = string.find(gloss_part, ": \"")

    # it's either not found, in which case the whole part is
    # a definition, or it's found in which case definition
    # is
    examples = []
    if definition_end == -1:
        definition = gloss_part
    else:
        definition = gloss_part[0:definition_end]
        # let's find all examples, example starts with
        # " and ends in either " (the last example) or
        # ";
        # TODO: also need to detect quotes ("--*; or "- *;)
        examples = []
        ex_start = definition_end + 3
        while 1:
            ex_end = string.find(gloss_part, "\";", ex_start)
            if ex_end == -1:
                try:
                    ex_end = string.index(gloss_part, "\"", ex_start)
                except ValueError:
                    if nested_level > 0:
                        unparsed.append(line)
                        return None
                    else:
                        # fix case no. 1: spurious ';' at the end
                        if line[-1] == ';':
                            return line_to_synset(line[:-1], nested_level+1)
                        # fix case no. 2: missing '"' at the end
                        if line[-1] != '"':
                            return line_to_synset( line + "\"", nested_level+1)
                        unparsed.append(line)
                        return None
                if ex_end > ex_start:
                    # TODO: this is a hack to fix parsing of "home"
                    # probably should just start looking from ex_start+1
                    examples.append(gloss_part[ex_start:ex_end])
                break
            else:
                examples.append(gloss_part[ex_start:ex_end])
                ex_start = ex_end + 4

    synset = Synset(words, part_of_speech, definition, examples)
    synset_off_synset_map[ hash_key ] = synset
    return synset
    
    
class SynsetIterator:
    """Iterates over synsets in all files with synset data
    It's a forward-only process"""

    def __init__(self,list_of_files):
        """list_of_files - names of files with synset data"""
        # we need to have at least one file
        if len(list_of_files)==0:
            raise TypeError, 'didnt give any files'
        self.list_of_files = list_of_files
        # which file from self.list_of_files is currently being processed,
        # -1 means none
        self.current_file = -1
        # file object of the currently opened file
        self.f = None

    def skip_initial_lines(self):
        """Wordnet files begin with copyright info that needs
        to be skipped (those are empty or starting with a space)
        returns first non-empty line"""
        while 1:
            line = self.f.readline()
            if len(line)>0 and line[0] != ' ':
                break
        return line

    def get_next_synset(self):
        """return the next synset, None if the end"""
        # if no file open, open the first file
        if self.current_file==-1:
            self.current_file = 0
            self.f = open(self.list_of_files[self.current_file], "r")
            line = self.skip_initial_lines()
        else:
            line = self.f.readline()
        # empty line means the end of the file
        if line == '': return None
        synset = line_to_synset(line)
        if synset==None: return self.get_next_synset()
        else:            return synset

def grok_one_data_file(file_name_in):
    global proSynsets
    file_name = wordnet_data_dir + file_name_in

    syn_iter = SynsetIterator([file_name])
    synLeft = -1
    # synLeft = 4
    while 1:
        synset = syn_iter.get_next_synset()
        if synset==None:
            break
        proSynsets.append(synset)
        synLeft = synLeft - 1
        if 0==synLeft:
            break

def dumpSql(fileName):
    global proSynsets
    # truncate the file to zero lenght
    sql_file = open(fileName, "w+b")
    #sql_file.write("BEGIN TRANSACTION;\n")
    sql_file.close()
    sql_file = open(fileName, "a+b")
    for synset in proSynsets:
        sql_file.write(synset.get_sql())
    #sql_file.write("END TRANSACTION;\n")
    sql_file.close()

def dumpSynsets(fileName):
    global proSynsets
    synLeft = -1
    synFile = open(fileName, "w+b")
    for synset in proSynsets:
        synLeft -= 1
        if 0 == synLeft:
            break
        #txt = synset.getTxtSimple()
        #txt = synset.getTxtMarked()
        txt = synset.getSqlInMarked()
        print txt + "\n"
        synFile.write( txt + "\n" )
        synFile.write( "\n" )
    synFile.close()

class LetterInfo:
    def __init__(self,letter,wordsOffset,wordNo,wordsData):
        self.data = [letter,wordsOffset,wordNo,wordsData]
    def getLetter(self): return self.data[0]
    def getOffset(self): return self.data[1]
    def getWordNo(self): return self.data[2]
    def getWordsData(self): return self.data[3]

# an array that contains all unique letters with which all the
# words begin
allLetters = []

def clearLetters():
    global allLetters
    allLetters = []

def addLetter(letter, wordsOffset, wordNo, wordsData ):
    """Info about letters consists of: a letter, offset of the first
    word starting with that letter in compressed words data block,
    number of the first word starting with this letter"""
    global allLetters
    letterInfo = LetterInfo( letter, wordsOffset, wordNo, wordsData)
    allLetters.append( letterInfo )
    if (len(allLetters)>50):
        raise StandardError
    print "Letter: %s, offset: %d, wordNo: %d" % (letter, wordsOffset, wordNo)

def isLiteSynset(syn):
    global proWords
    for w in syn.getWords():
        if epWords.wordExistP(w):
            return 1
    return 0

def makeLiteSynsets():
    global proSynsets, liteSynsets
    print "making lite synsets out of %d pro synsets" % len(proSynsets)
    for syn in proSynsets:
        if isLiteSynset(syn):
            liteSynsets.append(syn)
def makeLiteWords():
    global liteSynsets, liteWords
    for syn in liteSynsets:
        for w in syn.getWords():
            liteWords.add(w)

def isLiteWord(word):
    global liteWords
    return liteWords.wordExistP(word)

def dumpStats():
    global proWords,proSynsets,liteWords,liteSynsets
    print "proWordsCount: %d" % proWords.getWordsCount()
    print "liteWordsCount: %d" % liteWords.getWordsCount()
    print "proSynsets count: %d" % len(proSynsets)
    print "liteSynsets count: %d" % len(liteSynsets)

def dumpWindowsFormat(fileName,fNoahLite=0):
    """Write WordNet data in the Windows Noah file format. This format
    is described in docs\design.html"""
    global proSynsets, proWords, liteSynsets, liteWords

    clearLetters()
    wordsSorted = proWords.getWords().keys()
    wordsSorted.sort(sortFun)
    wordsCount = len(wordsSorted)
    if fNoahLite:
        liteWordsCount = liteWords.getWordsCount()
    
    # start with letter that cannot happen
    currentLetter = None
    wordsPackedSize = 0
    wordsData = ""
    wordNo = 0
    localWordsCount = 0
    for w in wordsSorted:
        proWords.setWordNo(w,wordNo)
        thisLetter = w[:1].lower()
        if thisLetter != currentLetter:
            if currentLetter != None:
                addLetter( currentLetter, wordsPackedSize, wordNo-localWordsCount, wordsData )
                wordsPackedSize += len(wordsData)
            wordsData = ""
            localWordsCount = 0
            currentLetter = thisLetter
        # format of words is: zero-or-one-terminated word and
        # zero-terminated pronunciation
        # TODO: we don't have pronuncitaions yet, when we have them,
        # we need to change the pack below
        f = "<%dsbb" % len(w)
        # termination is 0 for all words in pro and for
        # available in lite dictionary
        termination = 0
        if fNoahLite and not isLiteWord(w):
            termination = 1
        wordsData += pack( f, w, termination, 0 )
        localWordsCount += 1
        wordNo += 1

    addLetter( currentLetter, wordsPackedSize, wordNo-localWordsCount, wordsData )
    wordsPackedSize += len(wordsData)

    #print "number of letters: %d" % (len(allLetters))
    # print "size of packed words: %d, i.e. %d per word" % (wordsPackedSize, int(wordsPackedSize/wordsCount))
    assert( wordsCount == wordNo )
    synFile = open(fileName, "w+b")
    # 4b write a header
    if fNoahLite:
        synFile.write("NoaL")
    else:
        synFile.write( "NoaH" )

    # 4b write number of words (word-count)
    synFile.write( pack("<l", wordsCount) )

    # 4b for lite: write number of available words (word-available-count)
    wordsAvailableCount = liteWords.getWordsCount()
    if fNoahLite:
        synFile.write( pack("<l", wordsAvailableCount) )

    # 4b write number of letters with which words start (letters-count)
    lettersCount = len(allLetters)
    print "lettersCount=%d" % lettersCount
                       
    synFile.write( pack("<l", lettersCount ) )

    # letters-count*(4*2+1), for each letter:
    #  1b a letter
    #  4b offset of a first word beginning with that letter in the words block
    #  4b number of the first word beginning with that letter
    for letterInfo in allLetters:
        letter = letterInfo.getLetter()
        assert( 1 == len(letter) )
        offset = letterInfo.getOffset()
        wordNo = letterInfo.getWordNo()
        toWrite =  pack( "<cll", letter, offset, wordNo )
        assert( 9 == len(toWrite))
        synFile.write( toWrite )
        
    # 4b write the size of words & pronunciations (words-size)
    synFile.write( pack("<l", wordsPackedSize) )
    print "wordsPackedSize: %d" % wordsPackedSize

    writtenSize = 0
    # write words and pronunciation info
    for letterInfo in allLetters:
        writtenSize += len(letterInfo.getWordsData())
        synFile.write( letterInfo.getWordsData() )
    if writtenSize != wordsPackedSize:
        print "Sizes different, writtenSize=%d, wordsPackedSize=%d" % (writtenSize, wordsPackedSize)

    synsets = proSynsets
    if fNoahLite:
        synsets = liteSynsets

    # 4b write number of synsets (synset-count)
    synFile.write(pack("<l", len(synsets)))

    # 4b write the size of synset information (word-synset-map-size)
    synsetMapSize = 0
    #for s in proSynsets:
    for s in synsets:
        synsetMapSize += 3*s.getWordsCount()
    synFile.write( pack("<l", synsetMapSize ) )
    print "word-synset-map-size: %d" % synsetMapSize
    
    # write out info about synsets i.e. which word belongs to which synset
    #for s in proSynsets:
    for s in synsets:
        wordNumbers = s.getWordsNumbers()
        l = len(wordNumbers)
        for i in range(l):
            num = wordNumbers[i]
            fSpecial = (i == l-1)
            write3ByteWordNumber(synFile, num, fSpecial)

    # write out info about the sizes of synset definitions,
    # 2 bytes per synset
    totalDefLen = 0
    wrote = 0
    #for s in proSynsets:
    for s in synsets:
        defLen = s.getWinDefLen()
        assert( defLen < 10000 )
        totalDefLen += defLen
        toWrite = pack( "<h", defLen )
        wrote += len(toWrite)
        synFile.write( toWrite )
    print "synset-def-sizes-len: %d" % wrote

    #write synset-data-size, total size of all synset definitions
    synFile.write( pack( "<l", totalDefLen ) )
    print "totalDefLen: %d" % totalDefLen

    # write out all definitions
    #for s in proSynsets:
    for s in synsets:
        synsetDef = s.getWinDef()
        synFile.write(synsetDef)
    synFile.close()

def sortFun(x, y):
    """The way we sort words is by converting them to lowercase
    and replacing underscores with spaces"""
    x = x.lower()
    y = y.lower()
    x = x.replace("_", " " )
    y = y.replace("_", " " )
    return cmp(x, y)

def getSqlPrelude():
    fo = open("create_db.sql", "r")
    txt = fo.read()
    fo.close()
    return txt

pron_data_file = "C:\\kjk\\src\\mine\\dicts_data\\cmu_dict\\c06d"
pron_data = {}

def dump_pron_data_info():
    global pron_data
    print "Elements in pron_data: %d" % len(pron_data)
    dumpedCount = 0
    DUMP_LIMIT = 5
    for key in pron_data.keys():
        print "%s->%s" % (key, pron_data[key])
        dumpedCount += 1
        if dumpedCount > DUMP_LIMIT:
            break

def load_pron_data():
    global pron_data,pron_data_file
    assert 0 == len(pron_data)
    fo = open(pron_data_file, "rb")
    # first few lines are header lines starting with "##" but after
    # that we don't expect any lines to start with it
    fFinishedHeader = False
    for l in fo.readlines():
        if string.find(l,"##") == 0:
            # this is a header line, skip it
            assert fFinishedHeader == False
            continue
        else:
            fFinishedHeader = True
            space_pos = string.find(l," ")
            assert space_pos != -1
            word = l[0:space_pos]
            pron = string.strip( l[space_pos+1:] )
            pron_data[ string.lower(word)] = pron
    fo.close()

# return pronunciation for a given word/sentence
# empty string means no pronunciation
def get_pron_for_word(word):
    global pron_data
    word = string.lower(word)
    if pron_data.has_key(string.lower(word)):
        return pron_data[word]
    else:
        return ""

def doSql():
    global proSynsets

    for fileName in dataFiles:
        #print "groking file: %s" % fileName
        grok_one_data_file(fileName)

    if len(unparsed) > 0:
        print "Unparsed:", len(unparsed)
        for i in unparsed:
            print i
    print getSqlPrelude()
    # first gather full definitions for all words
    all_words = {}
    limit = 999999
    for synset in proSynsets:
        limit -= 1
        if limit == 0:
            break
        word_def = synset.getTxtMarked()
        for w in synset.words:
            if all_words.has_key(w):
                all_words[w] = all_words[w] + word_def
            else:
                all_words[w] = word_def
    load_pron_data()
    word_no = 1
    # wordsToPrint = 10
    for w in all_words.iterkeys():
        full_def = all_words[w]
        pron = get_pron_for_word(w)
        sqlTxt = "INSERT INTO words VALUES (%d,'%s',SOUNDEX('%s'), '%s','%s');\n" % (word_no, sql_qq(w), sql_qq(w), sql_qq(pron), sql_qq(full_def) )
        print sqlTxt
        word_no +=1
        #if word_no > wordsToPrint:
        #    break

def doWindows():
    epWords = readEPWords(engpolFileName)
    #print "ep words count: %d" % epWords.getWordsCount()

    for fileName in dataFiles:
        #print "groking file: %s" % fileName
        grok_one_data_file(fileName)
    if len(unparsed) > 0:
        print "Unparsed:", len(unparsed)
        for i in unparsed:
            print i
    makeLiteSynsets()
    makeLiteWords()
    dumpStats()
    #dumpWindowsFormat( winProFileName )
    dumpWindowsFormat( winLiteFileName, 1 )

def usage():
    print "Usage: wn2infoman.py";

line_to_test = """10410205 26 n 01 home 0 001 @ 10040804 n 0000 | an environment offering affection and security; "home is where the heart is"; "he grew up in a good Christian home";  "there's no place like home"  """

def test_line():
    synset = line_to_synset(line_to_test)
    txt = synset.getTxtMarked()
    print "." + txt + "."

# make sure that directory for ebooks data exists
def ensureDir(dir):
    if not arsutils.fDirExists(dir):
        print "created dir %s" % dir
        os.mkdir(dir)

# generate the following files:
# wn-dict.txt
#   contains wordnet synset for each word
# wn-word-index.pic
#   this contains a hash where each word is a key to a tuple (defOffset, defSize)
#   which define offset and size of word definition inside wndict-data.txt
def doInfoMan(outDir):
    global proSynsets

    ensureDir(outDir)

    # synchronize those file names with dictionary.py
    DICT_FILE   = "wn-dict.txt"
    INDEX_FILE  = "wn-words-index.pic"
    WORDS_FILE  = "wn-words.pic"

    dictPath  = os.path.join(outDir, DICT_FILE)
    indexPath = os.path.join(outDir, INDEX_FILE)
    wordsPath = os.path.join(outDir, WORDS_FILE)

    if arsutils.fFileExists(dictPath) and arsutils.fFileExists(indexPath) and arsutils.fFileExists(wordsPath):
        print "All files already exist. Nothing to do"
        return

    for fileName in dataFiles:
        print "groking file: %s" % fileName
        grok_one_data_file(fileName)

    if len(unparsed) > 0:
        print "Unparsed:", len(unparsed)
        for i in unparsed:
            print i

    all_words = {}
    print "generating word defs"
    for synset in proSynsets:
        word_def = synset.getTxtMarked()
        for w in synset.words:
            if all_words.has_key(w):
                # TODO: some better sorting of this data?
                all_words[w] = all_words[w] + word_def
            else:
                all_words[w] = word_def

    print "sorting words"
    sortedWords = all_words.keys()
    sortedWords.sort()

    print "words: %d" % len(sortedWords)
    print "writing %s" % dictPath
    dictDataFo = open(dictPath, "wb")
    wordIndex = {}
    curOffset = 0
    for word in sortedWords:
        wordDef = all_words[word]
        defLen = len(wordDef)
        wordIndex[word] = (curOffset, defLen)
        curOffset += defLen
        dictDataFo.write(wordDef)
    dictDataFo.close()

    print "pickling %s" % indexPath
    dictIndexFo = open(indexPath, "wb")
    cPickle.dump(wordIndex, dictIndexFo, protocol=cPickle.HIGHEST_PROTOCOL)
    dictIndexFo.close()

    print "pickling %s" % wordsPath
    dictWordsFo = open(wordsPath, "wb")
    cPickle.dump(sortedWords, dictWordsFo, protocol=cPickle.HIGHEST_PROTOCOL)
    dictWordsFo.close()

if __name__ == "__main__":
    # Import Psyco if available
    try:
        import psyco
        psyco.full()
        print "using psyco"
    except ImportError:
        pass

    doInfoMan("c:\\kjk\\infoman\\dict")
