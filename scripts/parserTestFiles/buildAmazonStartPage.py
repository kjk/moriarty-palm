import os, sys, string
from definitionBuilder import *

# possible stores
g_categories = [
    ["Books","s+amazonbrowse:Blended;books;1"],
    ["Music","s+amazonbrowse:Blended;music;1"],
    ["DVD","s+amazonbrowse:Blended;dvd;1"],
    ["Video","s+amazonbrowse:Blended;video;1"],
    ["VHS","s+amazonbrowse:Blended;vhs;1"],
    ["Video Games","s+amazonbrowse:Blended;videogames;1"],
    ["Photo","s+amazonbrowse:Blended;photo;1"],
    ["Electronics","s+amazonbrowse:Blended;electronics;1"],
    ["Toys","s+amazonbrowse:Blended;toys;1"],
    ["Tools","s+amazonbrowse:Blended;tools;1"],
    ["Computers","s+amazonbrowse:Blended;computers;1"],
    ["Sports & Outdoors","s+amazonbrowse:Blended;sportinggoods;1"],
    ["Software","s+amazonbrowse:Blended;software;1"],
    ["Health & Personal Care","s+amazonbrowse:Blended;health;1"],
    ["Wireless","s+amazonbrowse:Blended;wireless;1"],
    ["Office Products","s+amazonbrowse:Blended;office;1"],
    ["Outdoor Living","s+amazonbrowse:Blended;outdoorliving;1"],
    ["Baby","s+amazonbrowse:Blended;baby;1"],
    ["Musical Instruments","s+amazonbrowse:Blended;musicalinstruments;1"],
    ["Kitchen","s+amazonbrowse:Blended;kitchen;1"],
    ["Wireless Accessories","s+amazonbrowse:Blended;wirelessaccessories;1"],
    ["Beauty","s+amazonbrowse:Blended;beauty;1"],
    ["Apparel","s+amazonbrowse:Blended;apparel;1"],
    ["Magazines","s+amazonbrowse:Blended;magazines;1"],
    ["Jewelry","s+amazonbrowse:Blended;jewelry;1"],
    ["Gourmet Food","s+amazonbrowse:Blended;gourmetfood;1"]
    ]

g_categoriesSmall = [
    ["Books","s+amazonbrowse:Blended;books;1"],
    ["Music","s+amazonbrowse:Blended;music;1"],
    ["DVD","s+amazonbrowse:Blended;dvd;1"],
    ["Video","s+amazonbrowse:Blended;video;1"]
    ]

def mainOld():
    global g_categories, g_categoriesSmall
    print "start"
    fo = open("amazon-start-page.txt","wb")
    foSmall = open("amazon-start-page-small.txt","wb")

    df = Definition()
    dfSmall = Definition()

    gtxt = df.TextElement("Search:")
    gtxt.setStyle("bold")
    df.TextElement(" Entire Store")

    gtxt = dfSmall.TextElement("Search:")
    gtxt.setStyle("bold")
    dfSmall.TextElement(" Entire Store")

    #df.TextElement("Search: Entire Store")
    #dfSmall.TextElement("Search: Entire Store")

    # version with bullets
    for elem in g_categories:
        df.BulletElement(False)
        gtxt = df.TextElement(elem[0])
        gtxt.setHyperlink(elem[1])
        df.PopParentElement()

    for elem in g_categoriesSmall:
        dfSmall.BulletElement(False)
        gtxt = dfSmall.TextElement(elem[0])
        gtxt.setHyperlink(elem[1])
        dfSmall.PopParentElement()

    # version with multiple elements in line
##    df.LineBreakElement()
##    index = 0
##    for elem in dict:
##        if index != 0:
##            df.TextElement(" - ")
##        index += 1
##        gtxt = df.TextElement(elem[0])
##        gtxt.setHyperlink(elem[1])
##
##    dfSmall.LineBreakElement()
##    index = 0
##    for elem in dictSmall:
##        if index != 0:
##            dfSmall.TextElement(" - ")
##        index += 1
##        gtxt = dfSmall.TextElement(elem[0])
##        gtxt.setHyperlink(elem[1])

    # add links to switch between small/all
    dfSmall.LineBreakElement()
    gtxt = dfSmall.TextElement("Show all categories")
    gtxt.setHyperlink("amazonpreferences:showall")

    df.LineBreakElement()
    gtxt = df.TextElement("Show only major categories")
    gtxt.setHyperlink("amazonpreferences:showmajor")

    # save it
    serialized = df.serialize()
    serializedSmall = dfSmall.serialize()
    fo.write(serialized)
    fo.close()
    foSmall.write(serializedSmall)
    foSmall.close()
    print "end"
    print "preview start"
    fo2 = open("preview.txt","wb")
    fo2.write("?")
    fo2.write(longtob(len(serialized)))
    fo2.write(serialized)
    fo2.close()
    fo2Small = open("previewSmall.txt","wb")
    fo2Small.write("?")
    fo2Small.write(longtob(len(serializedSmall)))
    fo2Small.write(serializedSmall)
    fo2Small.close()
    print "preview end"

def amazonStart():
    global g_categories

    print "amazonStart() started"

    df = Definition()
    txt = df.TextElement("Only major categories", link="amazonpreferences:showmajor")
    txt.setJustification(justCenter)
    df.LineBreakElement(1,2)

    n = 0
    lastElement = len(g_categories)
    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    for (title, vurl) in g_categories:
        n = n + 1
        txt = df.TextElement(title, link=vurl)
        if n != lastElement:
            if n in [5,8,11,13,15,17,19,21,24]:
                df.LineBreakElement()                
            else:
                txt = df.TextElement(" \x95 ", style='gray')
    df.PopParentElement()
    df.LineBreakElement()
    df.LineBreakElement()

    df.TextElement(" Browse different stores using links. Press 'Search' button to ")
    df.TextElement("search", link="amazonform:search")
    df.TextElement(" for an item.");

    print "amazonStart() finished"

    return df.serialize()

def amazonStartMajor():
    global g_categoriesSmall

    print "amazonStartMajor() started"
    df = Definition()
    txt = df.TextElement("All categories", link="amazonpreferences:showall");
    txt.setJustification(justCenter)
    df.LineBreakElement(1,2)

    n = 0
    lastElement = len(g_categoriesSmall)
    par = df.ParagraphElement(False)
    par.setJustification(justCenter)
    for (title, vurl) in g_categoriesSmall:
        n = n + 1
        txt = df.TextElement(title, link=vurl)
        if n != lastElement:
            txt = df.TextElement(" \x95 ", style='gray')
    df.PopParentElement()

    df.LineBreakElement()
    df.LineBreakElement()

    df.TextElement(" Browse different stores using links. Press 'Search' button to ")
    df.TextElement("search", link="amazonform:search")
    df.TextElement(" for an item.");

    print "amazonStartMajor() finished"
    return df.serialize()

allFiles = [
        [amazonStart,      "amazon-start-page.txt", "preview.txt"],
        [amazonStartMajor, "amazon-start-page-small.txt", "previewSmall.txt"]
    ]

def saveDefToFile(fileName, definition, fPreview=False):
    fo = open(fileName,"wb")
    if fPreview:
        fo.write("?")
        fo.write(longtob(len(definition)))
    fo.write(definition)
    fo.close()

def main():
    fileNames = []
    for fileDsc in allFiles:
        func = fileDsc[0]
        fileName = fileDsc[1]
        fileNamePreview = fileDsc[2]

        definition = func()
        saveDefToFile(fileName, definition, fPreview=False)
        saveDefToFile(fileNamePreview, definition, fPreview=True)

if __name__=="__main__":
    main()
