import os, sys, string

from definitionBuilder import *

def main():
    print "start"
    fo = open("quotes-start-page.txt","wb")

    df = Definition()

    dailyLink = "s+quotes:daily"
    randomLink = "s+quotes:random"

    df.TextElement("Welcome to quotes of the day module.")
    df.LineBreakElement(1,2)

    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    df.TextElement("Daily", link=dailyLink)
    df.TextElement(" \x95 ", style='gray')
    df.TextElement("Random", link=randomLink)
    df.LineBreakElement(1,2)
    df.PopParentElement()

    df.TextElement("Press ")
    df.TextElement("Daily", link=dailyLink)
    df.TextElement(" to get daily quotes, or ")
    df.TextElement("Random", link=randomLink)
    df.TextElement(" to get random quotes.")

    fo.write(df.serialize())
    
    fo.close()
    print "end"

if __name__=="__main__":
    main()
