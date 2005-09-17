# Copyrigh: Krzysztof Kowalczyk
# Author: Szymon Knitter
# Description:
#   Parses roget.txt dictionary file.
import string, os, os.path, struct, cPickle, sys
from BeautifulSoup import BeautifulSoup, Tag
from parserUtils import *
from entities import convertEntities

DATA_FILE_NAMES = [
##    "test.txt",
    
    "pgw050ab.txt",
    "pgw050c.txt",
    "pgw050de.txt",
    "pgw050fh.txt",
    "pgw050il.txt",
    "pgw050mo.txt",
    "pgw050pq.txt",
    "pgw050r.txt",
    "pgw050s.txt",
    "pgw050tw.txt",
    "pgw050xz.txt",
    ]

OUT_DIR = "."

OUT_DICT_FILE_TXT = os.path.join(OUT_DIR, "wb-dict.txt")
OUT_DICT_FILE_PIC = os.path.join(OUT_DIR, "wb-words-index.pic")
OUT_DICT_FILE_WORDS = os.path.join(OUT_DIR, "wb-words.pic")

OUT_IGNORED_FILE_TXT = os.path.join(OUT_DIR, "wb-ignored-paragraphs.txt")

g_wordsDict = {}
g_dataTxt = ""
g_words = []

g_seeWordDict = {}

g_allIgnoredP = ""

# n, v, r, s, a - only this is accepted
g_pos = {"n." : "n",
         "a." : "a",
         "a" : "a",
         "v." : "v",
         "adv." : "r",
         "adj." : "a",
         "v. t." : "v",
         "v. i." : "v",
         "v. i. & t." : "v",
         "v. t. & i." : "v", 
         "v. t. &" : "v", ## this will be ignored
         "n ." : "n", ## this will be ignored
         
         "prep." : "ignore", ## this will be ignored
         "p. p." : "ignore", ## this will be ignored
         "v. & n." : "ignore", ## this will be ignored
         "p.a." : "ignore", ## this will be ignored
         "a. & n." : "ignore", ## this will be ignored
         "n. pl." : "ignore", ## this will be ignored
         "p. p. & a." : "ignore", ## this will be ignored
         "n. & adv." : "ignore", ## this will be ignored
         "p. a." : "ignore", ## this will be ignored
         "n. & a." : "ignore", ## this will be ignored
         "imp." : "ignore", ## this will be ignored
         "3d pers. sing. pr." : "ignore", ## this will be ignored
         "imp. & p. p." : "ignore", ## this will be ignored
         "a. & adv." : "ignore", ## this will be ignored
         "sing. or pl." : "ignore", ## this will be ignored
         "n. & v. t." : "ignore", ## this will be ignored
         "n.masc." : "ignore", ## this will be ignored
         "n. fem." : "ignore", ## this will be ignored
         "3d sing.pr." : "ignore", ## this will be ignored
         "ads." : "ignore", ## this will be ignored
         "interj." : "ignore", ## this will be ignored
         "n.pl." : "ignore", ## this will be ignored
         "p. p & a." : "ignore", ## this will be ignored
         "a. or pron." : "ignore", ## this will be ignored
         "conj." : "ignore", ## this will be ignored
         "p. pr." : "ignore", ## this will be ignored
         "n. sing. & pl." : "ignore", ## this will be ignored
         "pl." : "ignore", ## this will be ignored
         "adv. & a." : "ignore", ## this will be ignored
         "n. &and; v. t. & i." : "ignore", ## this will be ignored
         "prep. & adv." : "ignore", ## this will be ignored
         "a. & p. p." : "ignore", ## this will be ignored
         "pl. indic. pr." : "ignore", ## this will be ignored
         "compar." : "ignore", ## this will be ignored
         "prep. & adv." : "ignore", ## this will be ignored
         "adv. or prep." : "ignore", ## this will be ignored
         "adv. & prep." : "ignore", ## this will be ignored
         "3d sing. pr." : "ignore", ## this will be ignored
         "n. & v." : "ignore", ## this will be ignored
         "pref." : "ignore", ## this will be ignored
         "n., a., & v." : "ignore", ## this will be ignored
         "sing." : "ignore", ## this will be ignored
         "adv. & conj." : "ignore", ## this will be ignored
         "a. & pron." : "ignore", ## this will be ignored
         "n. pl" : "ignore", ## this will be ignored
         "a. &?; n." : "ignore", ## this will be ignored
         "prefix." : "ignore", ## this will be ignored
         "pron. & a." : "ignore", ## this will be ignored
         "." : "ignore", ## this will be ignored
         "v. t. &?; i." : "ignore", ## this will be ignored
         "A prefix." : "ignore", ## this will be ignored
         "a. superl." : "ignore", ## this will be ignored
         "3d sing. pres." : "ignore", ## this will be ignored
         "interj., adv., & n." : "ignore", ## this will be ignored
         "prep. phr." : "ignore", ## this will be ignored
         "v. t. or i." : "ignore", ## this will be ignored
         "v. inf." : "ignore", ## this will be ignored
         "interj. & adv." : "ignore", ## this will be ignored
         "pret." : "ignore", ## this will be ignored

         "" : "ignore", ## this will be ignored

         }

def getPos(text):
    pos = ""
    try:
        pos = g_pos[text.strip()]
    except:
        print " Unknown pos: %s" % text
        pos = "ignore"
    return pos

def removeAccents(text):
    text = text.replace("*","")
    text = text.replace('"',"")
    text = text.replace("||","")
    text = text.replace("`","")
    return text

def handleSeeWords():
    global g_seeWordDict, g_dataTxt
    global g_wordsDict
    return
    for name in g_seeWordDict:
        try:
            if g_wordsDict[g_seeWordDict[name]] != None:

                textToSave = "^" + g_seeWordDict[name] + "\n"
                length = len(textToSave)
                offset = len(g_dataTxt)
                pair = [offset, length]
                g_dataTxt += textToSave
                try:
                    g_wordsDict[name].append(pair)
                except:
                    g_wordsDict[name] = [pair]
        except:
            print " No definition for: %s" % g_seeWordDict[name]
    

def handleSeeWord(word, pos, defs, quotes):
    global g_seeWordDict
    word = convertEntities(word)
    defs = convertEntities(defs)

    add = True
    if -1 != defs.find("&"):
        add = False
        if -1 == defs.find("&?;"):
            print "------------"
            print pos + "   " + word
            print defs
            for q in quotes:
                print convertEntities(q)
        else:
            print "  *"
    if not add:
        return

    if defs.startswith("See "):
        defs = defs[4:].strip()
    else:
        print " Bad See <word> interpretation: %s" % defs

    # get word to see from def
    defs = defs.strip().strip(".").strip()
    # get only first
    seeWord = defs.split(",")[0].strip()
    g_seeWordDict[word] = seeWord


def addWord(word, pos, defs, quotes):
    global g_wordsDict, g_dataTxt
    word = convertEntities(word)
    defs = convertEntities(defs)

    ind = defs.find(". See ")
    if ind != -1:
        defs = defs[:ind+1]

    add = True
    if -1 != defs.find("&"):
        add = False
        if -1 == defs.find("&?;"):
            print "------------"
            print pos + "   " + word
            print defs
            for q in quotes:
                print convertEntities(q)
        else:
            print "  *"

    if not add:
        return
    
    # save word def
    textToSave = ""
    textToSave += "$" + pos + "\n"
    textToSave += "@" + defs + "\n"
    for q in quotes:
        q = convertEntities(q)
        textToSave += "#" + q + "\n"

    length = len(textToSave)
    offset = len(g_dataTxt)
    pair = [offset, length]

    g_dataTxt += textToSave
    try:
        g_wordsDict[word].append(pair)
    except:
        g_wordsDict[word] = [pair]



    

def getQuote(quoteTag):
    # we add quote as text\n^author pair, or text when author is unknown or missing

    allText = getAllTextFromTag(quoteTag)
    iList = quoteTag.fetch("i")
    author = ""
    if len(iList) > 0:
        author = getAllTextFromTag(iList[-1])
        
    if allText[allText.find(author):] == author:
        allText = allText[:allText.find(author)].strip()
        allText += "\n^" + author
       
    return '%s' % allText
    
def convert(text):
    global g_allIgnoredP
    # make some magic with text - to simplyfy parsing
    # remove <p><! p. xxx !></p>
    text = text[text.find("!>")+2:]
    # remove page info
    i = text.find("<!")
    while -1 != i:
        i2 = text[i+1:].find("!>")
        assert -1 != i2
        i2 += i+1
        text = text[:i]+text[i2+2:]
        i = text.find("<!")
    text = text.replace("\n\n<p></p>","")
    # move blockquotes to one p with def
    text = text.replace("</p>\n\n<p><blockquote>","\n\n<blockquote>")
    # move col to one p with def
    text = text.replace("</p>\n\n<p><col>","\n\n<col>")
    # move Syn. to one p with def
    text = text.replace("</p>\n\n<p><b>Syn.","\n\n<b>Syn.")

    print "  start parsing (feed soup - it may take a while)"
    # start parsing
    soup = BeautifulSoup()
    soup.feed(text)
    print "  soup feeded"

    pList = soup.fetch("p")
    currentPos = "ignore"
    currentWord = ""
    currentDef = ""
    currentQuotes = []

    # add word
    # addWord(currentWord, currentPos, currentDef, currentQuotes)
    counter = 0
    for p in pList:
        counter += 1
        if counter % 2000 == 0:
            print "   counter: %d\t Last word: %s" % (counter, currentWord)
        pos = p.first("pos")
        if pos:
            currentPos = getPos(getAllTextFromTag(pos))
        if currentPos != "ignore":
            hw = p.first("hw")
            if hw:
                txt = getAllTextFromTag(hw)
                currentWord = removeAccents(txt)
            defs = p.first("def")
            currentDef = ""
            if defs:
                currentDef = getAllTextFromTag(defs)

            currentQuotes = []
            for q in p.fetch("blockquote"):
                currentQuotes.append(getQuote(q))

            if currentDef != "":
                if currentDef.startswith("See "):
                    handleSeeWord(currentWord, currentPos, currentDef, currentQuotes)
                else:
                    addWord(currentWord, currentPos, currentDef, currentQuotes)
                
            else:
                g_allIgnoredP += str(p) + "\n\n"

def sortIgnoreCase(el1, el2):
    return cmp(el1.lower(), el2.lower())

def main():
    global g_wordsDict, g_dataTxt, g_words
    print "start"
    if len(sys.argv) != 2:
        scriptName = os.path.basename(sys.argv[0])
        print "usage: %s 5" % scriptName
        print "but it needs folowing files:"
        for fileName in DATA_FILE_NAMES:
            print "  " + fileName
        print "you can download them from:"
        print "http://www.gutenberg.org/browse/authors/w"
        print "this 5 is needed to ensure, that you read this:"
        print " from file pgw050ab.txt and pgw050xz.txt remove section with hexcodes"
        print " or this will fail - they use 0xff code there"
        sys.exit(0)

    for fileName in DATA_FILE_NAMES:
        print "start converting file: %s" % fileName
        fo = open(fileName, "rt")
        text = fo.read()
        fo.close()
        convert(text)       
        print "finished converting file: %s\n" % fileName

    print "handle see <word> definitions"
    handleSeeWords()
    print "create words list"
    for name in g_wordsDict:
        g_words.append(name)
    print " sorting words list"
    g_words.sort(sortIgnoreCase)

    print "save files..."
    fo = open(OUT_DICT_FILE_PIC, "wb")
    cPickle.dump(g_wordsDict, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    fo.close()
    fo = open(OUT_DICT_FILE_WORDS, "wb")
    cPickle.dump(g_words, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    fo.close()
    fo = open(OUT_DICT_FILE_TXT, "wb")
    fo.write(g_dataTxt)
    fo.close()

    fo = open(OUT_IGNORED_FILE_TXT, "wb")
    fo.write(g_allIgnoredP)
    fo.close()


    print "please copy output files:\n %s\n %s\n %s\nto infoman data store dir (.../dict/)" % (OUT_DICT_FILE_PIC, OUT_DICT_FILE_TXT, OUT_DICT_FILE_WORDS)
    print "end"
    

if __name__ == "__main__":
    main()
