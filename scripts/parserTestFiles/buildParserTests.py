import os, sys, string, buildTestDb

from definitionBuilder import *

def simpleExampleElementsHelp(link):
    df = Definition()

    df.LineBreakElement()

    text = "Text test"
    gtxt = df.TextElement(text)

    df.HorizontalLineElement()

    text = "Text test with "
    gtxt = df.TextElement(text)
    
    text = "link"
    gtxt = df.TextElement(text)
    text = "hyperlink resource... wharever inside"
    gtxt.setHyperlink(link)

    df.HorizontalLineElement()

    df.BulletElement(False)

    text = "in bull text"
    gtxt = df.TextElement(text)

    df.BulletElement(False)

    text = "in bull text (bold test)"
    gtxt = df.TextElement(text)
    gtxt.setStyle("bold")
    
    df.PopParentElement()
    df.BulletElement(False)

    text = "in bull small text"
    gtxt = df.TextElement(text)

    df.PopParentElement()
    df.PopParentElement()

    df.HorizontalLineElement()

    text = "Test justify"
    gtxt = df.TextElement(text)
    gtxt.setStyle("bold")

    text = "right"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justRight)
    
    text = "center"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justCenter)

    text = "left"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justLeft)

    df.LineBreakElement()

    text = "inherit"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justInherit)

    text = "right(last)"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justRightLast)

    df.HorizontalLineElement()

    return df.serialize()

def buildSimpleExample():
    elements = simpleExampleElementsHelp("test")
    link = "menu:" + elements
    elements = simpleExampleElementsHelp(link)
    return elements

def buildSimpleBytecodeTwoHelp(link):
    df = Definition()

    gtxt = df.TextElement("test1")
    gtxt.setHyperlink(link)

    df.LineBreakElement()

    gtxt = df.TextElement("test2")
    gtxt.setStyle("bold")

    df.LineBreakElement()
    df.LineBreakElement()

    gtxt = df.TextElement("test3")
    gtxt.setJustification(justRight)

    df.LineBreakElement()
    df.HorizontalLineElement()

    gtxt = df.TextElement("test4")

    li = df.ListNumberElement(1)
    li.setTotalCount(3)
    df.TextElement("text long enought to be more than one line")

    li = df.ListNumberElement(2, False)
    li.setTotalCount(3)
    df.TextElement("text long enought to be more than one line")
    df.PopParentElement()

    li = df.ListNumberElement(3, False)
    li.setTotalCount(3)
    df.TextElement("text")
    df.PopParentElement()

    df.HorizontalLineElement()
    df.HorizontalLineElement()

    df.BulletElement(False)
    df.TextElement("text long enought to be more than one line")
    df.PopParentElement()

    df.HorizontalLineElement()
    df.HorizontalLineElement()
    return df.serialize()

def buildSimpleBytecodeTwo():
    import popupMenu
    elements = buildSimpleBytecodeTwoHelp(popupMenu.buildSampleMenu())
    return elements

def buildListBytecode():
    df = Definition()

    gtxt = df.TextElement("List item 1")
    gtxt.setHyperlink("link res")
    gtxt.setStyle("bold")
    df.LineBreakElement()
    df.TextElement("description")

    df.HorizontalLineElement()

    gtxt = df.TextElement("List item 2")
    gtxt.setHyperlink("link res")
    gtxt.setStyle("bold")
    df.LineBreakElement()
    df.TextElement("description")

    df.HorizontalLineElement()

    gtxt = df.TextElement("List item 3")
    gtxt.setHyperlink("link res")
    gtxt.setStyle("bold")
    df.LineBreakElement()
    df.TextElement("description")

    df.HorizontalLineElement()

    gtxt = df.TextElement("List item 4")
    gtxt.setHyperlink("link res")
    gtxt.setStyle("bold")
    df.LineBreakElement()
    df.TextElement("description")

    gtxt = df.TextElement("$22.00")
    gtxt.setJustification(justRightLast)
    gtxt.setStyle("bold")

    df.HorizontalLineElement()
    return df.serialize()

def buildBullsChildren():
    df = Definition()

    gtxt = df.TextElement("Test bullet elements children")
    gtxt.setStyle("bold")
    df.HorizontalLineElement()

    df.BulletElement(False)
    df.TextElement("Father")

    df.BulletElement(False)
    df.TextElement("Son 1")

    df.BulletElement(False)
    df.TextElement("Son's 1 children 1")
    df.PopParentElement()

    df.BulletElement(False)
    df.TextElement("Son's 1 children 2")
    df.PopParentElement()
    
    df.PopParentElement()

    df.BulletElement(False)
    df.TextElement("Son 2")
    df.PopParentElement()

    df.PopParentElement()

    df.HorizontalLineElement()
    return df.serialize()

def buildAllInOneBytecode():
    df = Definition()

    df.LineBreakElement()

    text = "Test"
    gtxt = df.TextElement(text)

    df.HorizontalLineElement()

    text = "Text test with "
    gtxt = df.TextElement(text)
    
    text = "link to dreams"
    gtxt = df.TextElement(text)
    text = "s+dreams:dream"
    gtxt.setHyperlink(text)

    df.HorizontalLineElement()

    df.BulletElement(False)

    text = "in bull text"
    gtxt = df.TextElement(text)

    df.BulletElement(False)

    text = "in bull text (bold test)"
    gtxt = df.TextElement(text)
    gtxt.setStyle("bold")
    
    df.PopParentElement()
    df.BulletElement(False)

    text = "in bull small text"
    gtxt = df.TextElement(text)

    df.PopParentElement()
    df.PopParentElement()

    df.HorizontalLineElement()

    text = "Test justify"
    gtxt = df.TextElement(text)
    gtxt.setStyle("bold")

    text = "right"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justRight)
    
    text = "center"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justCenter)

    text = "left"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justLeft)

    df.LineBreakElement()

    text = "inherit"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justInherit)

    text = "right(last)"
    gtxt = df.TextElement(text)
    gtxt.setJustification(justRightLast)

    df.HorizontalLineElement()
    df.HorizontalLineElement()

    df.IndentedParagraphElement(False)
    gtxt = df.TextElement("Text in indented paragraph element. is it realy indented?")
    df.PopParentElement()

    df.ParagraphElement(False)
    gtxt = df.TextElement("Text in normal paragraph element. It should looks normal")
    df.PopParentElement()

    df.HorizontalLineElement()

    df.TextElement("Now test setSize() of LineBreakElement")
    lb = df.LineBreakElement()
    lb.setLineBreakSize(3,2)
    df.TextElement("mul = 3, div = 2")
    lb = df.LineBreakElement()
    lb.setLineBreakSize(5,3)
    df.TextElement("mul = 5, div = 3")
    lb = df.LineBreakElement()
    lb.setLineBreakSize(1,2)
    df.TextElement("mul = 1, div = 2")

    df.HorizontalLineElement()

    df.TextElement("Now test setTotalCount of ListNumberElement")
    ln = df.ListNumberElement(1,False)
    ln.setTotalCount(5)
    df.TextElement("element 1")
    df.PopParentElement()
    ln = df.ListNumberElement(2,False)
    ln.setTotalCount(5)
    df.TextElement("element 2")
    df.PopParentElement()
    ln = df.ListNumberElement(3,False)
    ln.setTotalCount(5)
    df.TextElement("element 3")
    df.PopParentElement()

    df.HorizontalLineElement()

    df.TextElement("How to test fontEffects?")    
    
    df.HorizontalLineElement()
    return df.serialize()

def buildStylesTable():
    df = Definition()

    df.TextElement("Build in styles:", style='bold')
    df.HorizontalLineElement()
    for styleName in staticStyles:
        df.TextElement(styleName+" - ABC abc \x95\x95\x95", style=styleName)
        df.LineBreakElement(3,2)
    df.HorizontalLineElement()
    df.TextElement("Server styles:", style='bold')
    df.HorizontalLineElement()

#    df.TextElement("TODO", style = styleNameRed)
#    df.LineBreakElement()

    st1 = df.AddStyle("test style",bold=True)
    st2 = df.AddStyle("test style2",strike=True)
    df.AddStyle("ts3",italics=True, bold=True)

    df.TextElement("Test Styles...")
    df.LineBreakElement()
    gtxt = df.TextElement("bold")
    gtxt.setStyleName(st1)
    df.LineBreakElement()
    gtxt = df.TextElement("strike")
    gtxt.setStyleName("test style2")
    df.LineBreakElement()
    df.TextElement("italics & bold", styleName = "ts3")

    all = df.AddStyle("all",fontSize=styleValueFontSizeLarge, color=[255,0,0], backgroundColor="#007f7f", bold=True, underline=styleValueUnderlineDotted)
    all2 = df.AddStyle("all 2",fontSize=styleValueFontSizeLarge, color="rgb(255,0,0)", underline=styleValueUnderlineSolid)

    df.LineBreakElement()
    df.TextElement("All in one", styleName = all)
    df.LineBreakElement()
    df.TextElement("All in one2", styleName = all2)

    df.HorizontalLineElement()
    df.TextElement("Element styles (owned by element):", style='bold')
    df.HorizontalLineElement()
    
    gtxt = df.TextElement("Test")
    ownStyle = df.buildStyleFromParams(bold=True, superscript=True)
    gtxt.setOwnStyle(ownStyle)
    df.LineBreakElement(3,2)
    gtxt = df.TextElement("Test")
    gtxt.setOwnStyle("color:#00ff00;bakcground-color:#0000ff;font-size:20pt;font-weight:bold")
    df.LineBreakElement()
    df.TextElement("Own style send looks like:")
    df.LineBreakElement()
    df.TextElement(ownStyle, style=styleNameRed)
    df.LineBreakElement()
    df.TextElement("Own style is build like:")
    df.LineBreakElement()
    df.TextElement("ownStyle = df.buildStyleFromParams(bold=True)", style=styleNameRed)

    df.HorizontalLineElement()
    df.TextElement("Note:", style='bold')
    df.HorizontalLineElement()
    df.TextElement("Links are combined with element style.")
    df.LineBreakElement()

    df2 = Definition()
    df2.TextElement("Links are build as:")
    df2.LineBreakElement()
    df2.TextElement("df.TextElement(", style = styleNameBlue)
    df2.TextElement("text", style = styleNameGreen)
    df2.TextElement(", ", style = styleNameBlue)
    df2.TextElement("link=linkData", style = styleNameGreen)
    df2.TextElement(", ", style = styleNameBlue)
    df2.TextElement("style=styleName...", style = styleNameRed)
    df2.TextElement(")", style = styleNameBlue)
    df2.LineBreakElement(3,2)
    df2.TextElement("You can use ")
    df2.TextElement("styleName=ownStyle", style = styleNameRed)
    df2.TextElement(" in ")
    df2.TextElement("TextElement()", style = styleNameBlue)
    df2.TextElement(" for your own styles form:")
    df2.LineBreakElement()
    df2.TextElement("ownStyle = df.AddStyle(bold=True,...)", style = styleNameGreen)

    linkData = "simpleform:Example;"+df2.serialize()     
    
    df.TextElement("link red", link=linkData, style = styleNameRed)
    df.LineBreakElement()
    df.TextElement("link green", link=linkData, style = styleNameGreen)
    df.LineBreakElement()
    df.TextElement("link yellow", link=linkData, style = styleNameYellow)
    
    return df.serialize()

def buildLinesBrakes():
    df = Definition()

    text = "This is veeeery long text to test this line breaks. " 
    text += "I saw problem with line break 3,2 or greater."

    df.TextElement("Test LineBreak(m,d)")
    df.LineBreakElement(1,2)
    df.LineBreakElement()
    df.TextElement(text)

    for i in [1,2,3]:
        df.BulletElement(False)
        df.TextElement(text)
        df.PopParentElement()

    df.LineBreakElement(5,2)
    df.TextElement("can't see it?")
    
    return df.serialize()

def buildTestTitle():
    df = Definition()

    text = "This is page title test. " 

    df.TextElement(text)
    df.setTitle("title test 1")
    return df.serialize()

def buildTestChars():
    df = Definition()

    df.TextElement("Test Chars:")
    df.LineBreakElement(3,2)

    for base in range(0,255,16):
        df.TextElement(str(base)+"  ", style=styleNameBold)
        text = ""
        for i in range(0,16):
            if i+base != 0:
                text += "%c" % (i+base)
        df.TextElement(text)
        df.LineBreakElement()

    return df.serialize()

def buildTestNewStartPageVer(ver):
                # module name          |time?| free
    modules = [["Weather",              True,  False],
               ["Phone book",           False, False],
               ["Movie times",          True,  False],
               ["Box office",           True,  True ],
               ["Currency conversion",  True,  False],
               ["Stocks",               True,  False],
               ["Jokes",                False, True ],
               ["Gas prices",           True,  False],
               ["Horoscopes",           True,  True ],
               ["Dream dictionary",     True,  True ],
               ["Amazon",               False, False],
               ["Netflix",              False, False],
               ["Encyclopedia",         False, False],
               ["Dictionary",           False, False],
               ["Lyrics",               False, False],
               ["Recipes",              False, False],
               ["Lists of bests",       False, False],
               ["TV Listings",          True,  False],
               ["About",                False, False],
              ]

    df = Definition()
    if ver == 1:
        styleTimeInfo = df.AddStyle("xxx",color=[127,127,127])
        for module in modules:
            df.BulletElement(False)
            df.TextElement(module[0], link="")
            if (module[1]):
                gtxt = df.TextElement(" 9 minutes ago", styleName=styleTimeInfo)
                gtxt.setJustification(justRightLast)
                
            df.PopParentElement()
    elif ver == 2:
        index = 0
        par = df.ParagraphElement(False)
        par.setJustification(justCenter)
        for module in modules:
            index += 1
            df.TextElement(module[0], link="")
            if index in [3,5,8,10,13,16,18,19]:
                df.LineBreakElement()
            else:
                df.TextElement(" \x95 ", style=styleNameGray)
        df.PopParentElement()
    elif ver == 3:
        pass
    
    return df.serialize()

def buildTestNewStartPage():
    return buildTestNewStartPageVer(2)


allExamples = [
        [buildSimpleExample,        "simple-bytecode"],
        [buildListBytecode,         "list-bytecode"],
        [buildBullsChildren,        "bulls-children"],
        [buildAllInOneBytecode,     "all-in-1-bytecode"],
        [buildSimpleBytecodeTwo,    "simple-bytecode2"],
        [buildStylesTable,          "styles-table"],
        [buildLinesBrakes,          "line-breaks"],
        [buildTestChars,            "chars"],
        [buildTestNewStartPage,     "infoman-start-page-test"],
        [buildTestTitle,            "title-element"],
    ]

def saveDefToFile(fileName, definition):
    fo = open(fileName,"wb")
    #fo.write("?")
    #fo.write(longtob(len(definition)))
    fo.write(definition)
    fo.close()

def main():
    fileNames = []
    for example in allExamples:
        func = example[0]
        fileName = example[1]
        fileNames.append(fileName)

        definition = func()
        saveDefToFile(fileName, definition)

    buildTestDb.buildDbFromFiles(fileNames)
    for fileName in fileNames:
        try:
            os.remove(fileName)
        except Exception, e:
            pass

if __name__ == "__main__":
    main()
