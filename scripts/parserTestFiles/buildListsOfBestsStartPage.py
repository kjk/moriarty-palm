import os, sys, string

from definitionBuilder import *

def main():
    print "start"
    fo = open("lists-of-bests-start-page.txt","wb")

    df = Definition()

    gtxt = df.GenericTextElement("Welcome to Lists of Bests module.")
    df.LineBreakElement(1,2)
    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    df.GenericTextElement("Books", link='s+listsofbestsbrowse:Books')
    df.GenericTextElement(" \x95 ", style='gray')
    df.GenericTextElement("Music", link='s+listsofbestsbrowse:Music')
    df.GenericTextElement(" \x95 ", style='gray')
    df.GenericTextElement("Movies", link='s+listsofbestsbrowse:Movies')
    df.PopParentElement()
    df.LineBreakElement(3,2)
    df.GenericTextElement("You can press ")
    gtxt = df.GenericTextElement("Search", link="listsofbestsform:search")
    gtxt = df.GenericTextElement(" button to find best movies, books or music.")
    fo.write(df.serialize())
    fo.close()
    print "end"

if __name__=="__main__":
    main()
