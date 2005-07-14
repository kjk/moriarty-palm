
from definitionBuilder import longtob

def stringToBytes(str):
    count = len(str)
    res = longtob(count)
    res += str
    res += '\0'
    return res

def buildPopupMenu(items):
    'Serializes out popup menu items in binary format. items is a list of tuples, '
    'each tuple looking like that: (caption, hyperlink, inactive, bold, separator). '
    'caption, hyperlink - string; inactive, bold, separator - bolean.'
    assert items is not None
    count = len(items)
    res = "menu:" + longtob(count)
    for caption, hyperlink, inactive, bold, separator in items:
        res += stringToBytes(caption)
        res += stringToBytes(hyperlink)
        flags = 0
        if inactive:
            flags += 1
        if bold:
            flags += 2
        if separator:
            flags += 4
        res += longtob(flags)
    return res

def buildSampleMenu():
    items = [
        ("ArsLexis", "http://www.arslexis.com", False, True, False),
        ("Google", "http://www.google.com/palm", False, False, False),
        ("", "", True, False, True),
        ("/.", "http://www.slashdot.org", False, False, False),
        ("Encyclopedia: 'shit happens jokes'", 's+pediaterm:List of "Shit happens" jokes', False, False, False)
    ]
    menu = buildPopupMenu(items)
    return menu
