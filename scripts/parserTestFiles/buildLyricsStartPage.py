import os, sys, string

from definitionBuilder import Definition, longtob

def main():
    print "start"
    fo = open("lyrics-start-page.txt","wb")

    df = Definition()

    gtxt = df.GenericTextElement("Welcome to lyrics module. Press ")
    gtxt = df.GenericTextElement("search")
    gtxt.setHyperlink("lyricsform:search")

    gtxt = df.GenericTextElement(" button to find lyrics for your favourite songs.")
    
    fo.write(df.serialize())
    
    fo.close()
    print "end"

if __name__=="__main__":
    main()
