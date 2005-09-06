# Copyrigh: Krzysztof Kowalczyk
# Author: Szymon Knitter
# Description:
#   Parses roget.txt dictionary file.
import string, os, os.path, struct, cPickle, sys

def sortIgnoreCase(el1, el2):
    return cmp(el1.lower(), el2.lower())

def main():
    print "start"
    if len(sys.argv) != 2:
        scriptName = os.path.basename(sys.argv[0])
        print "usage: %s wn_words.pic" % scriptName
        sys.exit(0)

    DATA_FILE_NAME = sys.argv[1]

    fo = open(DATA_FILE_NAME, "rb")
    allWords = cPickle.load(fo)
    fo.close()

    allWords.sort(sortIgnoreCase)

    fo = open(DATA_FILE_NAME, "wb")
    cPickle.dump(allWords, fo, protocol = cPickle.HIGHEST_PROTOCOL)
    fo.close()
    print "end"
    

if __name__ == "__main__":
    main()
