# Copyright: Krzysztof Kowalczyk
# Owner: Szymon Knitter
#
# Purpose:
#  Epicorious serch  - parseSearch(html)
#  Epicurious recipe - parse(html)
#
import string
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise

from entities import convertNamedEntities
from entities import convertNumberedEntities
from parserUtils import *
from ResultType import *
from definitionBuilder import *

epEmptyListText = None
epUnknownFormatText = None
# to tests only
#epEmptyListText = "empty list"
#epUnknownFormatText = "unknown format"

# htmlTxt is a html page returned by epicurious - search. Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   LIST_OF_RECIPES : resultBody is a list of search results for given query.
#   EMPTY_LIST : when nothing was found. change query to get results. resultBody is None
#   UNKNOWN_FORMAT : this doesn't even look like a page generated by epicurious
#      (or they've changed the format). resultBody is None
def parseSearch(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    outerList = []
    innerList = []    

    tdPD2List = soup.fetch("td",{"class":"pd2"})
    # empty list or unknown format
    if 0 == len(tdPD2List):
        noResults = soup.fetch("div",{"id":"noresults"})
        if 0 < len(noResults):
            return (EMPTY_LIST,epEmptyListText)
        return (UNKNOWN_FORMAT,epUnknownFormatText)

    # results
    for tdItem in tdPD2List:
        aItem = tdItem.first("a")
        if aItem:
            name = getAllTextFromTag(aItem).replace("\n","").strip()
            name = uncapitalizeText(name)
            url = str(aItem['href']).replace("\n","")

            # this is stupid, but there is <br/>> in epicurious code. so when they change that we will change this
            spanText = getAllTextFromTo(getLastElementFromTag(aItem).next, getLastElementFromTag(tdItem)).strip()
            if ">" == spanText[0]:
                spanText = spanText[1:]
            if "<" == spanText[-1]:
                spanText = spanText[:-2]
            smallSoup = BeautifulSoup()
            smallSoup.feed(spanText)
            spanItem = smallSoup.first("span",{"class":"pubdate"})
            splittedSpan = getAllTextFromTag(spanItem).split(",")
            if 1 < len(splittedSpan):
                sourceDate = splittedSpan[-1].replace("\n","").strip()
                source = string.join(splittedSpan[:-1],",").replace("\n","").strip()
                innerList = (url, name, source, sourceDate)
                outerList.append(innerList)

    if 0 == len(outerList):
        # or empty list?
        return (UNKNOWN_FORMAT,epUnknownFormatText)

##    # get totals (not used on client)
##    tdTotals = soup.first("td",{"align":"right","width":"120","class":"recipebotcopy"})
##    if tdTotals:
##        totalsText = getAllTextFromTo(tdTotals, tdTotals.first("br"))
##        totalsText = totalsText.replace("\n","")
##        totalsText = totalsText.replace("&nbsp;","")
##        totalsText = totalsText.replace("<!-- pager -->","")
##        ItemList = totalsText.strip().split()
##        ItemStart = ItemList[0]
##        ItemEnd = ItemList[2]
##        ItemTotal = ItemList[4]
##        innerList = [ItemStart, ItemEnd, ItemTotal]
##        #outerList.append(innerList)
##    else:
##        return (UNKNOWN_FORMAT, epUnknownFormatText)
    # build definition
    df = Definition()
    for item in outerList:
        # url, name, source, sourceDate
        df.BulletElement(False)
        df.TextElement(item[1], link = "s+recipe:"+item[0])
        df.PopParentElement()

    return LIST_OF_RECIPES, universalDataFormatWithDefinition(df, [])


# htmlTxt is a html page returned by epicurious - recipe. Parse it and returned a tuple
# (typeOfResult,resultBody)
# typeOfResult can be:
#   RECIPE_DATA : resultBody is a recipe + rewievs
#   UNKNOWN_FORMAT : this doesn't even look like a page generated by epicurious
#      (or they've changed the format). resultBody is None
def parseRecipe(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)

    # we need this tags to navigate
    divHead = soup.first("div",{"class":"intro"})
    ingredientsImageTag = soup.first("img",{"src":"/images/recipes/recipe_results/ingredients_hed.gif"})
    preperationImageTag = soup.first("img",{"src":"/images/recipes/recipe_results/preperation_hed.gif"})
    reviewsImageTag = soup.first("img",{"src":"/images/recipes/recipe_results/reviews.gif"})

    # no tags - unknown_format
    if not divHead or not ingredientsImageTag or not preperationImageTag or not reviewsImageTag:
        title = soup.first("title")
        if title:
            if getAllTextFromTag(title) == "{recipe title} Recipe at Epicurious.com ":
                return (NO_RESULTS, None)
        return (UNKNOWN_FORMAT,epUnknownFormatText)
    name = uncapitalizeText(getAllTextFromTag(divHead))
    name = name.replace("\n", "")
    name = name.strip()

    # now we need get text between <!-- copy --> (recipe describe)
    copy = getAllTextFromToInBrFormat(getLastElementFromTag(divHead).next,ingredientsImageTag)
    copySplitted = copy.split("<!-- copy -->")
    if 1 < len(copySplitted):
        copy = copySplitted[1]
    else:
        copy = ""

    # ingredients
    ingredients = getAllTextFromToInBrFormat(ingredientsImageTag,preperationImageTag)
    ingredientsSplitted = ingredients.split("<!-- ingredients -->")
    if 1 < len(ingredientsSplitted):
        ingredients = ingredientsSplitted[1]
    else:
        ingredients = ""

    # preperation
    preperation = getAllTextFromToInBrFormat(preperationImageTag, reviewsImageTag)
    preperationSplitted = preperation.split("<!-- preperation -->")
    if 1 < len(preperationSplitted):
        preperation = preperationSplitted[1]
    else:
        preperation = ""

    ind = preperation.find("This is your personal place to write notes")
    if ind != -1:
        preperation = preperation[:ind]
        while preperation[-5:] == "<br> ":
            preperation = preperation[:-5]
    
    # global note
    globalNote = "No review"
    globalNoteDiv = soup.first("img", {"src":"/images/recipes/recipe_search/%","class":"ratimg","align":"left"})
    if globalNoteDiv:
        globalNoteDiv = globalNoteDiv.next.next
        if isinstance(globalNoteDiv,Tag):
            globalNote = getAllTextFromToInBrFormat(globalNoteDiv,getLastElementFromTag(globalNoteDiv).next).replace("<br>"," ")

    ### for now we need to join copy, ingredients and preperation
    ##joined = string.join((copy,ingredients,preperation),"<br><br>")
    ##outerList = [(name,joined,globalNote)]
    outerList = [(name,copy,ingredients,preperation,globalNote)]
    
    # reviews
    cooksList = soup.fetch("div",{"class":"cook"})
    for cookItem in cooksList:
        # get cook name and date
        cookText = getAllTextFromTag(cookItem)
        cookText = cookText.split("<!--")[0].replace("\n","").strip()
        cookText = cookText.split(" on ")
        cook = string.join(cookText[:-1]," on ")
        date = cookText[-1]
        # get note
        note = "0"
        forkImage = cookItem.first("img",{"src":"/images/recipes/recipe_detail/%"})
        if forkImage:
            src = str(forkImage['src'])
            index = int(len("/images/recipes/recipe_detail/"))
            note = str(src[index])
            # just to be sure
            if note < "1" or note > "4":
                note = "0"
        # get review text
        afterCook = getLastElementFromTag(cookItem).next
        review = getAllTextFromTag(afterCook)
        review = review.replace("\n","").strip()
        # add it to outerList
        outerList.append((cook,date,note,review))

    return (RECIPE_DATA, universalDataFormatReplaceEntities(outerList))


def main():
##    fo = open("0019.html", "rt")
##    htmlTxt = fo.read()
##    fo.close()
##    (resultType, resultBody) = parseRecipe(htmlTxt)
##    print resultType
##    print resultBody
    pass

if __name__ == "__main__":
    main()
