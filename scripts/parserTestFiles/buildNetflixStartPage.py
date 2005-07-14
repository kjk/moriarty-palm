import os, sys, string

from definitionBuilder import *

def netflixStart():
    print "netflixStart() started"
    df = Definition()

    df.GenericTextElement("Welcome to Netflix module. You're not logged in (")
    df.GenericTextElement("log in", link="netflixform:login")
    df.GenericTextElement(").")

    df.LineBreakElement(1,2)

    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    df.GenericTextElement("My queue", link="netflixform:login")
    df.GenericTextElement(" \x95 ", style='gray')
    df.GenericTextElement("Browse", link="s+netflixbrowse:;F")
    df.GenericTextElement(" \x95 ", style='gray')
    df.GenericTextElement("Search", link="netflixform:search")
    df.PopParentElement()

    df.LineBreakElement(3,2)

    df.GenericTextElement("You can ")
    df.GenericTextElement("browse", link="s+netflixbrowse:;F")
    df.GenericTextElement(" movies, ")
    df.GenericTextElement("search", link="netflixform:search")
    df.GenericTextElement(" for movies and see movie details. ")

    df.LineBreakElement(3,2)

    df.GenericTextElement("Log in", link="netflixform:login")
    df.GenericTextElement(" to manage your Netflix queue.")

    print "netflixStart() finished"
    return df.serialize()

def netflixStartLogged():
    print "netflixStartLogged() started"
    df = Definition()

    df.GenericTextElement("Welcome to Netflix module. You're logged in.")

    df.LineBreakElement(1,2)

    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    df.GenericTextElement("My queue", link="netflixform:queue")
    df.GenericTextElement(" \x95 ", style='gray')
    df.GenericTextElement("Browse", link="s+netflixbrowse:;T")
    df.GenericTextElement(" \x95 ", style='gray')
    df.GenericTextElement("Search", link="netflixform:search")
    df.PopParentElement()

    df.LineBreakElement(3,2)

    df.GenericTextElement("You can ")
    df.GenericTextElement("browse", link="s+netflixbrowse:;T")
    df.GenericTextElement(" movies, ")
    df.GenericTextElement("search", link="netflixform:search")
    df.GenericTextElement(" for movies and manage your ")
    df.GenericTextElement("Netflix queue", link="netflixform:queue")
    df.GenericTextElement(".")

#    df.LineBreakElement(3,2)
#    df.GenericTextElement("You can ")
#    df.GenericTextElement("Log out", link="netflixform:logout")
#    df.GenericTextElement(" any time.")

    print "netflixStartLogged() finished"
    return df.serialize()

allFiles = [
        [netflixStart,      "netflix-start-page.txt"],
        [netflixStartLogged, "netflix-start-page-logged.txt"]
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
