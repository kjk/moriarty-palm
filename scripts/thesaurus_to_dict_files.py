# Copyrigh: Krzysztof Kowalczyk
# Author: Szymon Knitter
# Description:
#   Parses roget.txt dictionary file.
import string, os, os.path, struct, cPickle, sys

DATA_FILE_NAME = "roget.txt"
OUT_DIR = "."

OUT_DICT_FILE_TXT = os.path.join(OUT_DIR, "th-dict.txt")
OUT_DICT_FILE_PIC = os.path.join(OUT_DIR, "th-words-index.pic")
OUT_DICT_FILE_WORDS = os.path.join(OUT_DIR, "th-words.pic")

def cleenupText(text):
    print " clean text:"
    # remove all before...
    text = text[text.find("     #1."):]
    # remove all after...
    text = text[:text.find("***")]
    # remove in % states
    i = text.find("%")
    while -1 != i:
        i2 = text[i+1:].find("%")
        assert -1 != i2
        i2 += i+1
        text = text[:i]+text[i2+1:]
        i = text.find("%")
        if text[i-1:i+2] == '"%"':
            j = text[i+2:].find("%")
            if j == -1:
                i = j
            else:
                i = i + j + 2
    print "  % removed"
    # remove page info
    i = text.find("<--")
    while -1 != i:
        i2 = text[i+1:].find("-->")
        assert -1 != i2
        i2 += i+1
        text = text[:i]+text[i2+3:]
        i = text.find("<--")
    print "  <-- page --> removed"
    # remove {opp. xx}
    i = text.find("{opp.")
    while -1 != i:
        i2 = text[i+1:].find("}")
        assert -1 != i2
        i2 += i+1
        text = text[:i]+text[i2+1:]
        i = text.find("{opp.")
    print "  {opp. xxx} removed"
    return text    

# n, v, r, s, a - only this is accepted
g_pos = {"N" : "n",
         "N." : "n",
         "V" : "v",
         "v" : "v",
         "Adj" : "a",
         "Adv" : "r",
         "adv" : "r",
         "Phr" : "ignore", ## this will be ignored
         "phr" : "ignore", ## this will be ignored
         "Int" : "ignore", ## this will be ignored
         "Pref" : "ignore", ## this will be ignored
         "Pron" : "ignore", ## this will be ignored
         "b" : "v", ## this will be ignored
         }

def convert(text):
    wordsDict = {}
    defText = ""

    text = cleenupText(text)

    #fo = open("test.txt","rt")
    #text = fo.read()
    #fo.close()

    print " start converting"
    parts = text.split("     #")
    progress = len(parts)
    for part in parts[1:]:
        if progress % 30 == 0:
            print "  remain: %d" % progress
        progress -= 1
        
        actPos = ""
        partText = string.join(part.split("--")[1:],"--").strip()        
        for wordsText in partText.split("\n     "):
            testPos = wordsText.split(". ")[0].strip()
            if testPos in g_pos:
                actPos = g_pos[testPos]
                try:
                    wordsText = string.join(wordsText.split(". ")[1:],". ")
                except:
                    wordsText = ""
            else:
                if len(testPos) < 10:
                    if -1 == testPos.find("&c"):
                        if testPos.startswith("Phr["):
                            actPos = "ignore"
                        else:
                            pass
                            #print "!!!Unknown pos: %s" % testPos
            if actPos != "ignore":
                # replace ["text , text"] by [text text]
                i = wordsText.find('"')
                i2 = 0
                while -1 != i and -1 != i2:
                    i2 = wordsText[i+1:].find('"')
                    if -1 != i2:
                        i2 += i+1
                        if i2 == i + 2:
                            i = -1
                        else:
                            wordsText = wordsText[:i]+wordsText[i+1:i2].replace(",","")+wordsText[i2+1:]
                            i = wordsText.find('"')
                
                wordsText = wordsText.replace(";",",").replace("\n"," ").replace("  "," ")
                dirtyWords = wordsText.split(",")
                words = []
                for word in dirtyWords:
                    word = word.strip()
                    word = word.strip(".")
                    word = word.strip()
                    if len(word) > 0:
                        if -1 == word.find("[obs3]"):
                            if -1 != word.find("&c"):
                                word = word.split("&c")[0].strip()
                            if -1 != word.find("("):
                                word = word.split("(")[0].strip()
                            if -1 == word.find("[") and -1 == word.find("]"):
                                if -1 == word.find("\x03"):
                                    if -1 == word.find("<gr"):
                                        word = word.strip("|!")
                                        word = word.strip("|")
                                        word = word.strip("*")
                                        if len(word) > 0:
                                            words.append(word)

                if len(words) > 1:
                    pass
                    #print "------- pos:%s\n%s\n-------" % (actPos, string.join(words, ", "))
                    offset = len(defText)
                    toAdd = actPos + string.join(words, ", ")
                    length = len(toAdd)
                    defText += toAdd
                    for word in words:
                        try:
                            wordsDict[word] += [[offset, length]]
                        except:
                            wordsDict[word] = [[offset, length]]
            
    print " finished converting"
    print " building words list"
    allWords = []
    for word in wordsDict:
        allWords.append(word)
    allWords.sort()    
    print " finished."
    return wordsDict, defText, allWords

def main():
    print "start"
    if len(sys.argv) != 2:
        scriptName = os.path.basename(sys.argv[0])
        print "usage: %s roget15a.txt" % scriptName
        print "get roget from:"
        print "http://www.gutenberg.org/browse/authors/r#a20"
        sys.exit(0)
    DATA_FILE_NAME = sys.argv[1]

    fo = open(DATA_FILE_NAME, "rt")
    text = fo.read()
    fo.close()

    wordsDict, dataTxt, words = convert(text)

    print " save files..."
    fo = open(OUT_DICT_FILE_PIC, "wb")
    cPickle.dump(wordsDict, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    fo.close()
    fo = open(OUT_DICT_FILE_WORDS, "wb")
    cPickle.dump(words, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    fo.close()
    fo = open(OUT_DICT_FILE_TXT, "wb")
    fo.write(dataTxt)
    fo.close()

    print "please copy output files:\n %s\n %s\n %s\nto infoman data store dir (.../dict/)" % (OUT_DICT_FILE_PIC, OUT_DICT_FILE_TXT, OUT_DICT_FILE_WORDS)
    print "end"
    

if __name__ == "__main__":
    main()
