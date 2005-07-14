import os, sys, string

from definitionBuilder import Definition, longtob

def main():
    print "start"
    fo = open("recipes-start-page.txt","wb")

    df = Definition()

    df.GenericTextElement("Welcome to recipes module.")
    df.LineBreakElement()
    df.GenericTextElement("To find a recipe, enter an ingredient (e.g. \"bread\") and press \"Search\"")

    fo.write(df.serialize())
    fo.close()
    print "end"

if __name__=="__main__":
    main()
