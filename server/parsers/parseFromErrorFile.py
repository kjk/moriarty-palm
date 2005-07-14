# read the content of the parsing failures file and inokes
# apropriate parser on the data in it. This is to make it easier
# inspecting parsing failures
# TODO: needs to be written

import sys, string

def main():
    # file name is the first argument
    fileName = sys.argv[0]
    print fileName
    # read the file, parse the content and invoke proper parser
    # based on it. dump the result to stdout

if __main__ == "__main__":
    main()
    