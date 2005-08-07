# -*- coding: cp1250 -*-
import os, sys, string

from array import array
import binascii
from entities import convertEntities

## defines
typeLineBreakElement               = 'lbrk'
typeHorizontalLineElement          = 'hrzl'
typeTextElement                    = 'gtxt'
typeBulletElement                  = 'bull'
typeListNumberElement              = 'linu'
typeParagraphElement               = 'parg'
typeIndentedParagraphElement       = 'ipar'
## this one is not visible element
typeStylesTableElement             = 'sttb'
typeTitleElement                   = 'titl'
## pop parent element
typePopParentElement               = 'popp'

elementsTypes = [typeLineBreakElement,
                typeHorizontalLineElement,
                typeTextElement,
                typeBulletElement,
                typeListNumberElement,
                typeParagraphElement,
                typeIndentedParagraphElement,
                typeStylesTableElement,
                typeTitleElement,
                typePopParentElement]

## params
paramTextValue                     = 'text'
paramJustification                 = 'just'
paramHyperlink                     = 'hypl'
paramListNumber                    = 'lnum'
paramListTotalCount                = 'ltcn'
paramLineBreakSize                 = 'muld'

paramStyleName                     = 'stnm'
paramStylesCount                   = 'stcn'
paramStyleEntry                    = 'sten'

paramsTypes = [paramTextValue,
                paramJustification,
                paramHyperlink,
                paramListNumber,
                paramListTotalCount,
                paramLineBreakSize,
                paramStyleName,
                paramStylesCount,
                paramStyleEntry]

styleNameDefault        = ".default"
styleNameHyperlink      = ".hyperlink"
styleNameBold           = "bold"
styleNameLarge          = "large"
styleNameBlue           = "blue"
styleNameGray           = "gray"
styleNameRed            = "red"
styleNameGreen          = "green"
styleNameYellow         = "yellow"
styleNameBlack          = "black"
styleNameBoldRed        = "boldred"
styleNameBoldGreen      = "boldgreen"
styleNameBoldBlue       = "boldblue"
styleNameLargeBlue      = "largeblue"
styleNameHeader         = "header"
styleNameSmallHeader    = "smallheader"
styleNamePageTitle      = "pagetitle"
styleNameStockPriceUp   = "stockpriceup"
styleNameStockPriceDown = "stockpricedown"

staticStyles = [
    styleNameDefault,
    styleNameHyperlink,
    styleNameBold,
    styleNameLarge,
    styleNameBlue,
    styleNameGray,
    styleNameRed,
    styleNameGreen,
    styleNameYellow,
    styleNameBlack,
    styleNameBoldRed,
    styleNameBoldGreen,
    styleNameBoldBlue,
    styleNameLargeBlue,
    styleNameHeader,
    styleNameSmallHeader,
    styleNamePageTitle,
    styleNameStockPriceUp,
    styleNameStockPriceDown
    ]

## functions
def longtob(value):
    ar = array('L',[value])
    txt = ar.tostring()
    l = list(txt)
    l.reverse()
    ret = "".join(l)
    return ret

def btolong(value):
    ret = 0
    for i in range(0,4):
        ret *= 256
        ret += long(binascii.hexlify(value[i]),16)
    return ret

class Param:
    def __init__(self, name, value):
        self._name = name
        self._value = value

    def serialize(self, definition):
        name = self._name
        value = self._value
        valueType = "x"
        lengthTxt = ""
        if name == paramTextValue or name == paramHyperlink:
            length = len(value)
            lengthTxt = longtob(length)
            valueType = "L"
        elif name == paramJustification:
            valueType = "1"
        elif name == paramListNumber or name == paramListTotalCount or name == paramStylesCount:
            value = longtob(value)
            valueType = "4"
        elif name == paramLineBreakSize:
            value = longtob(value[0]) + longtob(value[1])
            valueType = "8"
        elif name == paramStyleName:
            # check style name
            if not value in staticStyles:
                if None != definition._styles:
                    if not value in (item[0] for item in definition._styles):
                        print "Unknown style name:%s" % value
                        return ""
                else:
                    print "Unknown style name:%s" % value
                    return ""
            lengthTxt = longtob(len(value))
            valueType = "L"
        elif name == paramStyleEntry:
            lengthTxt = longtob(len(value))
            valueType = "L"
        else:
            print "Unknown param name:%s" % name
            return ""
        if valueType == "x":
            print "Undefined param type for:%s" % name
            return ""
        return name + valueType + lengthTxt + value

(justInherit, justLeft, justRight, justCenter, justRightLast) = range(5)
g_justSymbols = ('i', 'l', 'r', 'c', 'x')

class Element:
    def __init__(self, code):
        self._code = code
        self._params = []

    def addParam(self, param):
        self._params.append(param)

    def serialize(self, definition):
        if self._code == typePopParentElement:
            return self._code
        if not self._code in elementsTypes:
            print "Unknown element type:%s" % self._code
            return ""
        paramsS = ""
        for param in self._params:
            paramsS += param.serialize(definition)

        length = longtob(len(paramsS))
        return self._code + length + paramsS

    ## functions for users
    def setNumber(self, number):
        if isinstance(number,str):
            number = long(number)
        self.addParam(Param(paramListNumber,number))

    def setHyperlink(self, res):
        try:
            self.addParam(Param(paramHyperlink, res.encode("latin-1", "ignore")))
        except:
            self.addParam(Param(paramHyperlink, res))

    def setJustification(self, justification):
        global g_justSymbols
        assert justification < len(g_justSymbols)
        if justification >= len(g_justSymbols):
            print "Unknown justification:%s" % justification
            return
        self.addParam(Param(paramJustification, g_justSymbols[justification]))

    def setText(self, text, removeEntities=True):
        if removeEntities:
            text = convertEntities(text)
        try:
            text = text.encode("latin-1", "ignore")
        except:
            pass
        self.addParam(Param(paramTextValue, text))

    def setStyle(self, styleIn):
        style = styleIn.lower()
        if style in staticStyles:
            self.addParam(Param(paramStyleName, style))
        else:
            print "Unknown static style:%s" % styleIn
            print "Use gtxt.setStyleName() or df.TextElement(text, styleName='%s')" % styleIn
            print "if you want to use your own styles."
            return

    def setTotalCount(self, number):
        if isinstance(number,str):
            number = long(number)
        self.addParam(Param(paramListTotalCount,number))

    def setLineBreakSize(self, mul, div):
        if isinstance(div,str):
            div = long(div)
        if isinstance(mul,str):
            mul = long(mul)
        value = [mul, div]
        self.addParam(Param(paramLineBreakSize,value))

    def setStyleName(self, name):
        self.addParam(Param(paramStyleName, name))

    def setOwnStyle(self, value):
        self.addParam(Param(paramStyleEntry, value))

# used to sort styles
def _cmpStyleByName(a,b):
    return cmp(a[0],b[0])

##
# Stores all DefinitnionElements.
##
class Definition:
    def __init__(self):
        self._elements = []
        self._styles = None
        self._title = None

    def endDefinition(self):
        self._appendCurrentElement()

    def addElem(self, elem):
        if isinstance(elem,list):
            self._elements += elements
        else:
            self._elements.append(element)

    def addElement(self, element):
        self._elements.append(element)

    def addElements(self, elements):
        self._elements += elements

    def empty(self):
        return (len(self._elements) == 0)

    def serialize(self):
        header = ""
        elementsS = ""
        if self._styles != None:
            self._elements = [self._buildStylesTable()] + self._elements
        if self._title != None:
            ttl = Element(typeTitleElement)
            ttl.setText(self._title)
            self._elements = [ttl] + self._elements
        for element in self._elements:
            elementsS += element.serialize(self)
        version = 1
        totalSize = 12+len(elementsS)
        elementsCount = len(self._elements)
        header = longtob(totalSize) + longtob(elementsCount) + longtob(version)
        return header + elementsS

    def addParentPopElement(self):
        pop = Element(typePopParentElement)
        self.addElement(pop)

    def PopParentElement(self):
        self.addParentPopElement()

    def LineBreakElement(self, mult=None, div=None):
        line = Element(typeLineBreakElement)
        if mult!=None and div !=None:
            line.setLineBreakSize(mult,div)
        self.addElement(line)
        self.addParentPopElement()
        return self._elements[-2]

    def HorizontalLineElement(self):
        line = Element(typeHorizontalLineElement)
        self.addElement(line)
        self.addParentPopElement()
        return self._elements[-2]

    def TextElement(self, text, close=True, link=None, style=None, styleName=None):
        gtext = Element(typeTextElement)
        gtext.setText(text)
        if None != link:
            gtext.setHyperlink(link)
        if None != style:
            gtext.setStyle(style)
        if None != styleName:
            gtext.setStyleName(styleName)
        self.addElement(gtext)
        if close:
            self.addParentPopElement()
            return self._elements[-2]
        else:
            return self._elements[-1]

    def BulletElement(self, close=True):
        bull = Element(typeBulletElement)
        self.addElement(bull)
        if close:
            self.addParentPopElement()
            return self._elements[-2]
        else:
            return self._elements[-1]

    def ListNumberElement(self, number, close=True):
        if isinstance(number,str):
            number = long(number)
        num = Element(typeListNumberElement)
        num.setNumber(number)
        self.addElement(num)
        if close:
            self.addParentPopElement()
            return self._elements[-2]
        else:
            return self._elements[-1]

    def ParagraphElement(self, close=True):
        par = Element(typeParagraphElement)
        self.addElement(par)
        if close:
            self.addParentPopElement()
            return self._elements[-2]
        else:
            return self._elements[-1]

    def IndentedParagraphElement(self, close=True):
        par = Element(typeIndentedParagraphElement)
        self.addElement(par)
        if close:
            self.addParentPopElement()
            res = self._elements[-2]
        else:
            res = self._elements[-1]
        return res

    def _buildStylesTable(self):
        element = Element(typeStylesTableElement)
        assert (len(self._styles) > 0)
        element.addParam(Param(paramStylesCount,len(self._styles)))
        # sort styles
        self._styles.sort(_cmpStyleByName)
        # add them
        for style in self._styles:
            value = longtob(len(style[0])) + style[0] + style[1]
            element.addParam(Param(paramStyleEntry, value))
        return element

    def _buildColor(self, color):
        if isinstance(color, list):
            assert len(color) == 3
            return "rgb(%d,%d,%d)" %(color[0], color[1], color[2])
        else:
            return color

    # Analyze this if you want build styles for your own
    # Attribute         : value
    #  font-family      : (on Palm ignored)
    #  font-style       : normal | italic | obligue (Palm: N/A; CE: Yes)
    #  font-variant     : normal | small-caps (Palm: N/A; CE: Yes)
    #  font-weigth      : normal | bold | bolder | lighter | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 (Palm: only normal/bold; CE: all)
    #  font-size        : xx-small | x-small | small | medium | large | x-large | xx-large | <size in points> (Palm: (size <= medium) -> medium; (size >= large) -> large; medium=10pt)
    #  color            : rgb(r, g, b) | #RRGGBB
    #  background-color : rgb(r, g, b) | #RRGGBB
    #  text-decoration  : none | underline | line-through | x-underline-dotted
    #  vertical-align   : baseline | sub | super
    #
    def buildStyleFromParams(self, fontSize=None, color=None, backgroundColor=None, bold=None, italics=None, superscript=None, subscript=None, strike=None, underline=None):
        value = ""
        if fontSize != None:
            value += "font-size:%s;" % fontSize
        if color != None:
            value += "color:%s;" % self._buildColor(color)
        if backgroundColor != None:
            value += "background-color:%s;" % self._buildColor(backgroundColor)
        if bold:
            value += "font-weight:bold;"
        if italics:
            value += "font-style:italic;"
        if superscript or subscript:
            if superscript:
                value += "vertical-align:super;"
            else:
                value += "vertical-align:sub;"
        if strike:
            value += "text-decoration:line-through;"
        if underline != None:
            value += "text-decoration:%s;" % underline
        return value
        
    def AddStyle(self, name, fontSize=None, color=None, backgroundColor=None, bold=None, italics=None, superscript=None, subscript=None, strike=None, underline=None):
        if None == self._styles:
            self._styles = []
        value = self.buildStyleFromParams(fontSize, color, backgroundColor, bold, italics, superscript, subscript, strike, underline)
        # add style to list
        self._styles.append([name, value])
        return name

    def setTitle(self, title):
        self._title = title
        
## Build style values...
styleValueFontSizeLarge    = "large"
styleValueUnderlineDotted  = "x-underline-dotted"
styleValueUnderlineSolid   = "underline"

## This class is used to parse BCF on server (for cacheing or sth)
#  init with ByteCodeFormat data.
class BCF:
    def __init__(self, bcf):
        self.elements = []
        self.elementsCount = 0
        self.version = None
        self.totalLength = 0
        
        start = 0
        end = len(bcf)
        # parse header
        assert end >= 12
        self.totalLength = btolong(bcf[start:start+4])
        start += 4
        self.elementsCount = btolong(bcf[start:start+4])
        start += 4
        self.version = btolong(bcf[start:start+4])
        start += 4
        assert self.totalLength == end
        # parse elements
        while start < end:
            elementCode = bcf[start:start+4]
            el = Element(elementCode)
            self.elements.append(el)
            start += 4
            assert elementCode in elementsTypes
            # parse params
            if elementCode != typePopParentElement:
                paramsEnd = btolong(bcf[start:start+4])
                start += 4
                paramsEnd += start
                while start < paramsEnd:
                    paramCode = bcf[start:start+4]
                    start += 4                    
                    assert paramCode in paramsTypes
                    lenCode = bcf[start]
                    start += 1
                    if lenCode == 'L':
                        paramLen = btolong(bcf[start:start+4])
                        start += 4
                    else:
                        paramLen = int(lenCode,16)
                    value = bcf[start:start+paramLen]
                    start += paramLen
                    el.addParam(Param(paramCode, value))            

        assert self.elementsCount == len(self.elements)

    def Print(self):
        print "---BCF-START---"
        print "---Header:---"
        print "Total length: %d bytes" % self.totalLength
        print "Elements count: %d" % self.elementsCount
        print "Version: %d" % self.version
        print "---Elements:---"
        for el in self.elements:
            print "Element code: "+el._code
            for param in el._params:
                print " (%s,%s)" % (param._name, param._value)
        print "---BCF-END---"

    def getAllHyperlinks(self, startsWith = ""):
        links = []
        for el in self.elements:
            for param in el._params:
                if param._name == paramHyperlink:
                    if param._value.startswith(startsWith):
                        links.append(param._value)
        return links
        
