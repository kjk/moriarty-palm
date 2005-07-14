import os, sys, string

from definitionBuilder import Definition, longtob

def main():
    print "start"
    fo = open("flights-start-page.txt","wb")

    df = Definition()

    df.TextElement("Welcome to flight schedule module.")
    df.LineBreakElement()
    df.TextElement("To find a flight, press Search and enter an flight number and airlines, or cities and date")

    fo.write(df.serialize())
    fo.close()
    print "end"

if __name__=="__main__":
    main()
