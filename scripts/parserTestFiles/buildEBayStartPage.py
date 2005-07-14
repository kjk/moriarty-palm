import os, sys, string

from definitionBuilder import *

def eBayStart():
    print "eBayStart() started"
    df = Definition()

    df.TextElement("Welcome to eBay module. You're not logged in (")
    df.TextElement("log in", link="ebayform:login")
    df.TextElement(").")

    df.LineBreakElement(1,2)

    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    browseLink = "s+ebay:browse;0;F"
    df.TextElement("Browse", link=browseLink)
    df.TextElement(" \x95 ", style='gray')
    df.TextElement("Search", link="ebayform:search")
    df.PopParentElement()

    df.LineBreakElement(3,2)

    df.TextElement("You can ")
    df.TextElement("browse", link=browseLink)
    df.TextElement(" categories, ")
    df.TextElement("search", link="ebayform:search")
    df.TextElement(" for items. ")

    df.LineBreakElement(3,2)

    df.TextElement("Log in", link="ebayform:login")
    df.TextElement(" to buy, place bids and watch items.")

    print "eBayStart() finished"
    return df.serialize()

def eBayStartLogged():
    print "eBayStartLogged() started"
    df = Definition()

    df.TextElement("Welcome to eBay module. You're logged in.")

    df.LineBreakElement(1,2)

    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    browseLink = "s+ebay:browse;0;T"
    df.TextElement("My eBay", link="hs+ebay:myebay")
    df.TextElement(" \x95 ", style='gray')
    df.TextElement("Browse", link=browseLink)
    df.TextElement(" \x95 ", style='gray')
    df.TextElement("Search", link="ebayform:search")
    df.PopParentElement()

    df.LineBreakElement(3,2)

    df.TextElement("You can ")
    df.TextElement("browse", link=browseLink)
    df.TextElement(" categories, ")
    df.TextElement("search", link="ebayform:search")
    df.TextElement(" for items.")

    df.LineBreakElement()
    df.TextElement("In ")
    df.TextElement("My eBay", link="hs+ebay:myebay")
    df.TextElement(" you can check your bids and watches.")

    print "eBayStartLogged() finished"
    return df.serialize()

allFiles = [
        [eBayStart,      "ebay-start-page.txt"],
        [eBayStartLogged, "ebay-start-page-logged.txt"]
    ]

def saveDefToFile(fileName, definition):
    fo = open(fileName,"wb")
    fo.write(definition)
    fo.close()

def main():
    fileNames = []
    for fileDsc in allFiles:
        func = fileDsc[0]
        fileName = fileDsc[1]
        definition = func()
        saveDefToFile(fileName, definition)

if __name__=="__main__":
    main()
