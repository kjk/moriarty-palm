# Copyright: Krzysztof Kowalczyk
# Owner: Krzysztof Kowalczyk

# Purpose:
#  Unit testing for server
#  see http://diveintopython.org/unit_testing/index.html for more info on unittest

# TODO: there are 2 important things we want to add to this framework
# 1. Saving the results to a file and ability to re-run the tests that failed
#    in the last run (or any given run). Usually if there's a failure, we're
#    just interested in re-running the test that caused the failure. Currently
#    it's not easy
# 2. Ability to e-mail results of the tests to a list of given e-mail address
#    The idea is that we could run those unit tests e.g. few times a day so that
#    we know if our server fails for any reason.

import string, unittest, sys, Queue, random, time
import client
from client import getRequestHandleCookie, Response, Request, g_uniqueDeviceInfo, g_nonUniqueDeviceInfo
import Fields, ServerErrors
from InfoManServer import *

invalidRegCodeNumber = "0000"

def searchResultsCount(resultTxt):
    parts = resultTxt.split("\n")
    return len(parts)

class ServerTests(unittest.TestCase):
    def assertFieldExists(self,response,field):
        # list of fields in fields is threated as alternative (one or more from list)
        if isinstance(field, list):
            wasField = 0
            for smallField in field:
                if response.hasField(smallField):
                    wasField = 1
                    self.assertEqual(response.hasField(smallField),True)
            if 0 == wasField:
                print "\nnone of: '%s' does exist in response" % string.join(field,"', '")
                print "all fields: %s" % string.join(response.getFields(),",")
                if response.hasField(Fields.error):
                    print "Error: %s" % response.getField(Fields.error)
        else:
            if not response.hasField(field):
                print "\nfield '%s' doesn't exist in response" % field
                print "all fields: %s" % string.join(response.getFields(),",")
                if response.hasField(Fields.error):
                    print "Error: %s" % response.getField(Fields.error)
            self.assertEqual(response.hasField(field),True)

    def assertFieldDoesntExist(self,response,field):
        if response.hasField(field):
            print "\nfield '%s' exist in response" % field
            print "all fields: %s" % string.join(response.getFields(),",")
        self.assertEqual(response.hasField(field),False)

    def assertFieldsDontExist(self,response,fields):
        for field in fields:
            self.assertFieldDoesntExist(response,field)

    def assertFieldsExist(self,response,fields):
        for field in fields:
            self.assertFieldExists(response,field)

    def assertFieldEqual(self,response,field,value):
        # all values returned by server are strings. If value to compare with
        # is int, change it to string. This makes it easier to e.g. compare
        # server errors
        if isinstance(value,int):
            value = "%d" % value
        self.assertEqual(response.getField(field),value)

    def addField(self,fieldName, fieldValue):
        self.req.addField(fieldName, fieldValue)

    def getResponse(self,requiredFields=[]):
        self.rsp = Response(self.req)
        self.assertFieldsExist(self.rsp,requiredFields)
        if self.rsp.hasField(Fields.transactionId):
            self.assertEqual(self.rsp.getField(Fields.transactionId), self.req.transactionId)

    def assertError(self,expectedError):
        self.assertFieldEqual(self.rsp, Fields.error, expectedError)

    def test_Ping(self):
        # this is the simplest valid requests - only sends transaction id
        # in response server sends the same transaction id
        self.req = getRequestHandleCookie()
        self.getResponse([Fields.cookie,Fields.transactionId])

    def test_MalformedRequest(self):
        self.req = getRequestHandleCookie()
        # malformed, because there is no ":"
        self.req.addLine("malformed\n")
        self.getResponse([Fields.error,Fields.transactionId])
        self.assertError(ServerErrors.malformedRequest)

    def verifyArgument(self, field, fRequiresArguments):
        self.req = getRequestHandleCookie()
        # do the exact opposite of what's expected
        if fRequiresArguments:
            self.req.addField(field, None)
        else:
            self.req.addField(field, "not needed argument")
        self.getResponse([Fields.error,Fields.transactionId])
        if fRequiresArguments:
            self.assertError(ServerErrors.requestArgumentMissing)
        else:
            self.assertError(ServerErrors.unexpectedRequestArgument)

    # check if server correctly detects missing extra arguments
    def test_ArgumentsWithoutValue(self):
        fieldsWithoutValue = [Fields.getRegCodeDaysToExpire, Fields.getCurrentBoxOffice]
        for field in fieldsWithoutValue:
            self.verifyArgument(field,False)

    # check if server correctly detects missing arguments
    def test_ArgumentsWithValue(self):
        fieldsWithValue = [Fields.protocolVersion, Fields.clientInfo, Fields.transactionId, Fields.cookie, Fields.getCookie, Fields.getMovies, Fields.regCode, Fields.verifyRegCode]
        for field in fieldsWithValue:
            self.verifyArgument(field,True)

    def prepareRecipeList(self,query):
        self.req = getRequestHandleCookie(Fields.getRecipesList,query)

    def doRecipeGetListOk(self, query):
        self.prepareRecipeList(query)
        self.getResponse([Fields.recipiesList, Fields.transactionId])

    def test_RecipeBread(self):
        self.doRecipeGetListOk("bread")

    def test_RecipeApricot(self):
        self.doRecipeGetListOk("apricot")

    def doRecipeEmptyList(self,query):
        self.prepareRecipeList(query)
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def test_RecipeEmptyList(self):
        self.doRecipeEmptyList("asdfaawer")

    def prepareRecipe(self,query):
        self.req = getRequestHandleCookie(Fields.getRecipe,query)

    def test_RecipeValid(self):
        self.prepareRecipe("/recipes/recipe_views/views/104527")
        self.getResponse([Fields.recipe, Fields.transactionId])

    def test_RecipeInvalid(self):
        self.prepareRecipe("/recipes/recipe_views/views/asdgasdf")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def test_RecipeInvalid2(self):
        self.prepareRecipe("/asdfadgasdf")
        self.getResponse([Fields.transactionId])
        self.assertError(ServerErrors.moduleTemporarilyDown)

    def test_OnlyOneRequest(self):
        self.prepareRecipe("bread")
        self.addField(Fields.getMovies, "98101")
        self.getResponse([Fields.transactionId])
        self.assertError(ServerErrors.serverFailure)

    def prepareWeather(self,location):
        self.req = getRequestHandleCookie(Fields.getWeather, location)

    def test_WeatherLocationUnknown(self):
        self.prepareWeather("66666")
        self.getResponse([Fields.locationUnknown, Fields.transactionId])

    def test_WeatherLocationAmbig(self):
        self.prepareWeather("warsaw")
        self.getResponse([Fields.weatherMultiselect, Fields.transactionId])

    def test_WeatherValidLocation(self):
        self.prepareWeather("PLXX0005")
        self.getResponse([Fields.weather, Fields.transactionId])

    def test_WeatherValidZipLocation(self):
        self.prepareWeather("98101")
        self.getResponse([Fields.weather, Fields.transactionId])

    def prepareDream(self, dream):
        self.req = getRequestHandleCookie(Fields.getDream, dream)

    def test_DreamNoResults(self):
        self.prepareDream("abrakadabrabumcykcyk")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def test_DreamOkTooth(self):
        self.prepareDream("tooth")
        self.getResponse([Fields.outDream, Fields.transactionId])

    def test_DreamOkSex(self):
        self.prepareDream("sex")
        self.getResponse([Fields.outDream, Fields.transactionId])

    def prepareJokesList(self, query):
        self.req = getRequestHandleCookie(Fields.getJokesList, query)

    def test_JokesListNoResults(self):
        self.prepareJokesList("0;rating;;;;blahhphdsA")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def test_JokesListOk1(self):
        self.prepareJokesList("0;rating;;;;test")
        self.getResponse([Fields.outJokesList, Fields.transactionId])

    def test_JokesListOk2(self):
        self.prepareJokesList("0;rating;Racy;QandA;Blonde;test")
        self.getResponse([Fields.outJokesList, Fields.transactionId])

    def test_JokesListOk3(self):
        self.prepareJokesList("4;rating;;;;")
        self.getResponse([Fields.outJokesList, Fields.transactionId])

    def prepareJoke(self, url):
        self.req = getRequestHandleCookie(Fields.getJoke, url)

    def test_JokeOk(self):
        self.prepareJoke("/results/detail.asp?sql=8&id=6358")
        self.getResponse([Fields.outJoke, Fields.transactionId])

    def test_JokeOkRandom(self):
        self.prepareJoke("random")
        self.getResponse([Fields.outJoke, Fields.transactionId])

    def test_JokeOkRandom2(self):  ## to test cache
        self.prepareJoke("random")
        self.getResponse([Fields.outJoke, Fields.transactionId])

    def test_JokeOkRandom3(self):  ## to test cache
        self.prepareJoke("random")
        self.getResponse([Fields.outJoke, Fields.transactionId])

    def prepare411PersonSearch(self, query):
        self.req = getRequestHandleCookie(Fields.get411PersonSearch, query)

    def test_411PersonSearchOk(self):
        self.prepare411PersonSearch(",Kowalczyk,98101,WA")
        self.getResponse([Fields.out411PersonSearchResult, Fields.transactionId])

    def test_411PersonSearchNoCity(self):
        self.prepare411PersonSearch(",Kowalczyk,blahblah,WA")
        self.getResponse([[Fields.outNoResults, Fields.out411NoCity], Fields.transactionId])

    def test_411PersonSearchTooManyResults(self):
        self.prepare411PersonSearch(",K,,WA")
        self.getResponse([Fields.out411TooManyResults, Fields.transactionId])

    def test_411PersonSearchNoResults(self):
        self.prepare411PersonSearch("Hulianno,Kowalczykos,Seattle,WA")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def test_411PersonSearchCityMultiselect(self):
        self.prepare411PersonSearch(",Kowal,Sea,WA")
        self.getResponse([[Fields.out411PersonSearchCityMultiselect, Fields.outNoResults], Fields.transactionId])

    def prepare411BusinessSearch(self, query):
        self.req = getRequestHandleCookie(Fields.get411BusinessSearch, query)

    def test_411BusinessSearchOk(self):
        self.prepare411BusinessSearch("hair,seattle,WA,No,Name")
        self.getResponse([Fields.out411BusinessSearchResult, Fields.transactionId])

    def test_411BusinessSearchOk2(self):
        self.prepare411BusinessSearch("hair,seattle,WA,Yes,Name")
        self.getResponse([Fields.out411BusinessSearchResult, Fields.transactionId])

    def test_411BusinessSearchOk3(self):
        self.prepare411BusinessSearch("hair,seattle,WA,No,Category")
        self.getResponse([Fields.out411BusinessSearchMultiselect, Fields.transactionId])

    def test_411BusinessSearchOk4(self):
        self.prepare411BusinessSearch("hair,seattle,WA,Yes,Category")
        self.getResponse([Fields.out411BusinessSearchMultiselect, Fields.transactionId])

    def test_411BusinessSearchNoCity(self):
        self.prepare411BusinessSearch("hair,blahblah,WA,No,Category")
        self.getResponse([Fields.out411NoCity, Fields.transactionId])

    def test_411BusinessSearchNoCity2(self):
        self.prepare411BusinessSearch("hair,blahblah,WA,No,Name")
        self.getResponse([Fields.out411NoCity, Fields.transactionId])

    def test_411BusinessSearchNoResults(self):
        self.prepare411BusinessSearch("hairscalpindians,,WA,No,Name")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def test_411BusinessSearchNoResults2(self):
        self.prepare411BusinessSearch("hairscalpindians,,WA,No,Category")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def prepare411International(self, query):
        self.req = getRequestHandleCookie(Fields.get411InternationalCodeSearch, query)

    def test_411International(self):
        self.prepare411International("PL")
        self.getResponse([Fields.out411InternationalCodeSearchResult, Fields.transactionId])

    def test_411International2(self):
        self.prepare411International("DZ")
        self.getResponse([Fields.out411InternationalCodeSearchResult, Fields.transactionId])

    def test_411International3(self):
        self.prepare411International("GO")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def prepare411ReversePhone(self, query):
        self.req = getRequestHandleCookie(Fields.get411ReversePhone, query)

    def test_411ReversePhoneOk(self):
        self.prepare411ReversePhone("425-882-0110")
        self.getResponse([Fields.out411ReversePhoneResult, Fields.transactionId])

    def test_411ReversePhoneNoResults(self):
        self.prepare411ReversePhone("555-555-5555")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def test_411ReversePhoneMalformed(self):
        self.prepare411ReversePhone("20820110")
        self.getResponse([Fields.transactionId])
        self.assertError(ServerErrors.malformedRequest)

    def prepare411AreaByCity(self, query):
        self.req = getRequestHandleCookie(Fields.get411AreaByCity, query)

    def test_411AreaByCityOk(self):
        self.prepare411AreaByCity("seattle,WA")
        self.getResponse([Fields.out411AreaByCityResult, Fields.transactionId])

    def test_411AreaByCityMultiselect(self):
        self.prepare411AreaByCity("sea,WA")
        self.getResponse([Fields.out411AreaByCityMultiselect, Fields.transactionId])

    def test_411AreaByCityNoResults(self):
        self.prepare411AreaByCity("blahblah,WA")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def prepare411ReverseArea(self, query):
        self.req = getRequestHandleCookie(Fields.get411ReverseArea, query)

    def test_411ReverseAreaOk(self):
        self.prepare411ReverseArea("206")
        self.getResponse([Fields.out411ReverseAreaResult, Fields.transactionId])

    def test_411ReverseArea911(self):
        self.prepare411ReverseArea("911")
        self.getResponse([Fields.out411ReverseAreaResult, Fields.transactionId])

    def test_411ReverseAreaNoResults(self):
        self.prepare411ReverseArea("555")
        self.getResponse([Fields.outNoResults, Fields.transactionId])
    def prepare411ZipByCity(self, query):
        self.req = getRequestHandleCookie(Fields.get411ZipByCity, query)

    def test_411ZipByCityOk(self):
        self.prepare411ZipByCity("seattle,WA")
        self.getResponse([Fields.out411ZipByCityResult, Fields.transactionId])

    def test_411ZipByCityMultiselect(self):
        self.prepare411ZipByCity("sea,WA")
        self.getResponse([Fields.out411ZipByCityMultiselect, Fields.transactionId])

    def test_411ZipByCityNoResults(self):
        self.prepare411ZipByCity("blahblah,WA")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def prepare411ReverseZip(self, query):
        self.req = getRequestHandleCookie(Fields.get411ReverseZip, query)

    def test_411ReverseZipOk(self):
        self.prepare411ReverseZip("98101")
        self.getResponse([Fields.out411ReverseZipResult, Fields.transactionId])

    def test_411ReverseZipNoResults(self):
        self.prepare411ReverseZip("66666")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def prepareCurrencies(self):
        self.req = getRequestHandleCookie(Fields.getCurrencyConversion)

    def test_CurrenciesOK(self):
        self.prepareCurrencies()
        self.getResponse([Fields.outCurrencyConversion, Fields.transactionId])

    def prepareStocksList(self, query):
        self.req = getRequestHandleCookie(Fields.getStocksList, query)

    def test_StocksListOK(self):
        self.prepareStocksList("^DJI;^IXIC;^GSPC")
        self.getResponse([Fields.outStocksList, Fields.transactionId])

    def test_StocksListOK2(self):
        self.prepareStocksList("MSFT")
        self.getResponse([Fields.outStocksList, Fields.transactionId])

    def test_StocksListOK3(self):
        self.prepareStocksList("microsoft;prokom")
        self.getResponse([Fields.outStocksList, Fields.transactionId])

    def prepareStocksListValidateLast(self, query):
        self.req = getRequestHandleCookie(Fields.getStocksListValidateLast, query)

    def test_StocksListValidateLastValid(self):
        self.prepareStocksListValidateLast("YHOO;MSFT")
        self.getResponse([Fields.outStocksList, Fields.transactionId])

    def test_StocksListValidateLastByName(self):
        self.prepareStocksListValidateLast("YHOO;microsoft")
        self.getResponse([Fields.outStocksListByName, Fields.transactionId])

    def test_StocksListValidateLastNoResults(self):
        self.prepareStocksListValidateLast("YHOO;notValidSymbolOrName")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def prepareStockByName(self, url):
        self.req = getRequestHandleCookie(Fields.getStockByName, url)

    def test_StockByNameOk(self):
        self.prepareStockByName("/l?s=WHAT")
        self.getResponse([Fields.outStocksListByName, Fields.transactionId])

    def test_StockByNameNoResults(self):
        self.prepareStockByName("/l?s=nothingFindForThis")
        self.getResponse([Fields.outNoResults, Fields.transactionId])

    def prepareStock(self, url):
        self.req = getRequestHandleCookie(Fields.getStock, url)

    def test_StockOk(self):
        self.prepareStock("/q?s=^GSPC")
        self.getResponse([Fields.outStock, Fields.transactionId])

    def test_StockOk2(self):
        self.prepareStock("/q?s=MSFT")
        self.getResponse([Fields.outStock, Fields.transactionId])

    def prepareAmazonBrowse(self, url):
        self.req = getRequestHandleCookie(Fields.getAmazonBrowse, url)

    # TODO: rewrite those tests to use Get-Url
    #def test_AmazonBrowseOk(self):
    #    self.prepareAmazonBrowse("Blended;Books;1")
    #    self.getResponse([Fields.outAmazonBrowse, Fields.transactionId])

    #def test_AmazonBrowseOk1(self):
    #    self.prepareAmazonBrowse("Blended;DVD;1")
    #    self.getResponse([Fields.outAmazonBrowse, Fields.transactionId])

    #def test_AmazonBrowseOk2(self):
    #    self.prepareAmazonBrowse("Books;26;1")
    #    self.getResponse([Fields.outAmazonBrowse, Fields.transactionId])

    #def prepareAmazonSearch(self, url):
    #    self.req = getRequestHandleCookie(Fields.getAmazonSearch, url)

    #def test_AmazonSearchOk(self):
    #    self.prepareAmazonSearch("Books;;1;bb")
    #    self.getResponse([Fields.outAmazonSearch, Fields.transactionId])

    #def test_AmazonSearchNoResults(self):
    #    self.prepareAmazonSearch("Books;;1;ahfafhssafa")
    #    self.getResponse([Fields.outNoResults, Fields.transactionId])

    #def prepareAmazonItem(self, url):
    #    self.req = getRequestHandleCookie(Fields.getAmazonItem, url)

    #def test_AmazonItemOk(self):
    #    self.prepareAmazonItem("073984072X")
    #    self.getResponse([Fields.outAmazonItem, Fields.transactionId])

    #def prepareAmazonList(self, url):
    #    self.req = getRequestHandleCookie(Fields.getAmazonList, url)

    #def test_AmazonListOk(self):
    #    self.prepareAmazonList("L1WOW1VSS7JWSN;1")
    #    self.getResponse([Fields.outAmazonSearch, Fields.transactionId])

    #def prepareAmazonWishlistSearch(self, wstr):
    #    self.req = getRequestHandleCookie(Fields.getAmazonWishlist, wstr)

    #def test_AmazonWishlistSearchOk(self):
    #    self.prepareAmazonWishlistSearch("Kowalczyk;;;;1")
    #    self.getResponse([Fields.outAmazonWishlist, Fields.transactionId])

    def prepareHoroscope(self, query):
        self.req = getRequestHandleCookie(Fields.getHoroscope, query)

    def test_HoroscopesOk(self):
        self.prepareHoroscope("Aries")
        self.getResponse([Fields.outHoroscope, Fields.transactionId])

    def test_HoroscopesOk2(self):
        self.prepareHoroscope("yh;/astrology/careerfinance/monthly/aries")
        self.getResponse([Fields.outHoroscope, Fields.transactionId])

    def test_HoroscopesOk3(self):
        self.prepareHoroscope("yh;/astrology/general/dailyteen/aries")
        self.getResponse([Fields.outHoroscope, Fields.transactionId])

    def test_HoroscopesOk4(self):
        self.prepareHoroscope("yh;/astrology/love/weekly/aries")
        self.getResponse([Fields.outHoroscope, Fields.transactionId])

    def prepareTvListingsProviders(self, zipCode):
        self.req = getRequestHandleCookie(Fields.getTvListingsProviders, zipCode)

    def test_TvLisitingsProviders(self):
        self.prepareTvListingsProviders('98101')
        self.getResponse([Fields.outTvListingsProviders, Fields.transactionId])

    def test_RegisterAndAskVersion(self):
        # TODO write this test
        pass

    # TODO: write test to check if unregistered version expires

# This is a description of tests
# Each item in the array is one test.
# First item in a test is a test number - this should be unique
# Second item is a list of fieldName/fieldValue pairs
# Third item is a list of expected fields in the result. Each item can be
# either a field name or a list [fieldName, expectedFieldValue]
g_allTests = [
  [1,  [Fields.getUrl, "pediasearch:test"], [Fields.outPediaSearchResults]],
  [2,  [Fields.getUrl, "pediasearch:de:test"], [Fields.outPediaSearchResults]],
  [3,  [Fields.getUrl, "pediasearch:xw:test"], [[Fields.error, str(ServerErrors.invalidRequest)]]],
  [4,  [Fields.getUrl, "pediarandom:en"], [Fields.outPediaArticle, Fields.outPediaArticleTitle]],
  [5,  [Fields.getUrl, "pediarandom:xw"], [[Fields.error, str(ServerErrors.invalidRequest)]]],
  [6,  [Fields.getUrl, "pedialangs:"], [Fields.outPediaLangs]],
  [7,  [Fields.getUrl, "pediaterm:en:test"], [Fields.outPediaArticleTitle, Fields.outPediaArticle]],
  [8,  [Fields.getUrl, "pediaterm:test"], [Fields.outPediaArticleTitle, Fields.outPediaArticle]],
  [9,  [Fields.getUrl, "pediaterm:xw:test"], [[Fields.error, str(ServerErrors.invalidRequest)]]],
  [10, [Fields.getUrl, "pediaterm:en:zxcwfwefewcerfvergfwed4e321e2d"], [Fields.outNoResults]],

  [20, [Fields.getCurrentBoxOffice, None], [Fields.outCurrentBoxOffice]],
  # repeat get box office to test caching
  [21, [Fields.getCurrentBoxOffice, None], [Fields.outCurrentBoxOffice]],
  [22, [Fields.getCurrentBoxOffice, "not needed"], [[Fields.error, str(ServerErrors.unexpectedRequestArgument)]]],
  # Get-Cookie requires an argument but we're not sending it
  [23, [Fields.getCookie, None], [[Fields.error, str(ServerErrors.requestArgumentMissing)]]],
  # unrecognized field
  [24, ["Foo", "Blast"], [[Fields.error, str(ServerErrors.invalidRequest)]]],
  # a ping request
  [25, [], []],

  [30, [Fields.getMovies, "aasdfadfa"], [Fields.locationUnknown]],
  [31, [Fields.getMovies, "warsaw"], [Fields.locationAmbiguous]],
  [32, [Fields.getMovies, "seattle, wa"], [Fields.moviesData]],
  [33, [Fields.getMovies, "98101"], [Fields.moviesData]],
  [34, [Fields.getMovies, "95110"], [Fields.moviesData]],
  [35, [Fields.getMovies, None], [[Fields.error, str(ServerErrors.requestArgumentMissing)]]],

  [40, [Fields.getWeather, None], [[Fields.error, str(ServerErrors.requestArgumentMissing)]]],
  [41, [Fields.getWeather, "6666"], [Fields.locationUnknown]],
  [42, [Fields.getWeather, "warsaw"], [Fields.weatherMultiselect]],
  [43, [Fields.getWeather, "PLXX0005"], [Fields.weather]],
  [44, [Fields.getWeather, "98101"], [Fields.weather]],

  [50, [Fields.getGasPrices, None], [[Fields.error, str(ServerErrors.requestArgumentMissing)]]],
  [51, [Fields.getGasPrices, "98101"], [Fields.outGasPrices]],
  [52, [Fields.getGasPrices, "10007"], [Fields.outGasPrices]],
  [53, [Fields.getGasPrices, "66666"], [Fields.locationUnknown]],
  [54, [Fields.getGasPrices, "95110"], [Fields.outGasPrices]],
  [55, [Fields.getGasPrices, "77057"], [Fields.outGasPrices]],
  [56, [Fields.getGasPrices, "48227"], [Fields.outGasPrices]],
  [57, [Fields.getGasPrices, "29420"], [Fields.outGasPrices]],
  [58, [Fields.getGasPrices, "75034"], [Fields.outGasPrices]],
  [59, [Fields.getGasPrices, "asdfasd"], [Fields.locationUnknown]],
  [60, [Fields.getGasPrices, ""], [Fields.locationUnknown]],

  [70, [Fields.getUrl, "eBook-search: earth; doc pdf"], [Fields.outEBookSearchResults]],
  [71, [Fields.getUrl, "eBook-search: conrad; *"], [Fields.outEBookSearchResults]],
 ]

def checkTestNumbersUnique():
    global g_allTests
    checkedTestNumbers = {}
    fValid = True
    for test in g_allTests:
        testNumber = test[0]
        if checkedTestNumber.has_key(testNumber):
            print "duplicate test number %d in g_allTests" % testNumber
            fValid = False
        else:
            checkedTestNumbers[testNumber] = 1 # can be anything
    if not fValid:
        print "aborting. Found duplicate test numbers - fix it first"
        sys.exit(1)

# maps errors to test id
g_errors = {}
g_testNumbers = {} # for detecting duplicate test numbers
g_failedTests = []

# given a list of request fields in test[0] and a list of expected
# fields in test[1], execute a given request and
def fValidTestOk(test):
    global g_errors, g_testNumbers

    testNo = test[0]
    if g_testNumbers.has_key(testNo):
        print "Duplicate test number: %d" % testNo
        sys.exit(0)
    else:
        g_testNumbers[testNo] = 1 # can be anything, we only use it to test if the entry exists

    fieldsToSend = test[1]
    assert isinstance(fieldsToSend, list)
    expectedResultFields = test[2]
    assert 0 == len(fieldsToSend) % 2
    req = getRequestHandleCookie()
    fieldsCount = len(fieldsToSend)/2
    for fieldNo in range(fieldsCount):
        fieldName = fieldsToSend[fieldNo*2]
        fieldValue = fieldsToSend[fieldNo*2+1]
        req.addField(fieldName, fieldValue)
    rsp = Response(req)
    client.handleCookie(rsp)
    errorsTxt = []

    if not rsp.hasField(Fields.transactionId):
        errorsTxt.append("Field %s missing" % Fields.transactionId)
    else:
        tridGot = rsp.getFieldShort(Fields.transactionId)
        tridSent = req.transactionId
        if tridGot != tridSent:
            errorsTxt.append("Sent transactionId %s but got %s" % (tridSent, tridGot))
    for fieldName in expectedResultFields:
        if isinstance(fieldName, list):
            assert 2 == len(fieldName)
            fieldValue = fieldName[1]
            fieldName = fieldName[0]
            if not rsp.hasField(fieldName):
                errorsTxt.append("Field %s missing" % fieldName)
            else:
                if fieldValue != rsp.getFieldShort(fieldName):
                    errorsTxt.append("Field %s value is different, expected: %s, got: %s" % (fieldName, fieldValue, rsp.getFieldShort(fieldName)))
        else:
            if not rsp.hasField(fieldName):
                errorsTxt.append("Field %s missing" % fieldName)
    if len(errorsTxt) > 0:
        errorsTxt.append("Full request:\n'%s'" % req.getText())
        errorsTxt.append("Full response:\n'%s'" % rsp.getShortText())
        g_errors[testNo] = errorsTxt
        return False
    else:
        return True

def runTestThread():
    global requestsQueue, g_failedTests
    while True:
        testNo = requestsQueue.get()
        #print "running test %d" % testNo
        test = g_allTests[testNo]
        testNumber = test[0]
        if fValidTestOk(test):
            sys.stdout.write(".")
        else:
            sys.stdout.write("F")
            g_failedTests.append(testNumber) # TODO: is this save, multi-threaded

# run tests in multiple threads
def runServerTestsThreaded(threadsCount=5):
    global g_allTests, requestsQueue, g_failedTests, g_errors

    testCount = len(g_allTests)
    requestsQueue = Queue.Queue(testCount)

    for i in range(threadsCount):
        start_new_thread(runTestThread, tuple([]))

    testsExecuted = []
    g_failedTests = []
    while True:
        if len(testsExecuted) >= testCount:
            break
        testNo = random.randint(0, testCount-1)
        if testNo in testsExecuted:
            #print "test %d chosen twice" % testNo
            continue
        #print "added test %d to queue" % testNo
        requestsQueue.put(testNo)
        testsExecuted.append(testNo)

    while not requestsQueue.empty():
        time.sleep(1)

    failingTestsCount = len(g_failedTests)
    if failingTestsCount > 0:
        txt = [str(ft) for ft in g_failedTests]
        print "\n"
        for failingTestNo in g_failedTests:
            print "Test %d failed because:\n  %s\n" % (failingTestNo, string.join(g_errors[failingTestNo], "\n  "))
        print "%d out of %d tests failed" % (failingTestsCount, testCount)
        print "Failing tests: %s" % string.join(txt, " ")
    else:
        print "\nAll %d tests passed" % testCount


# run the tests, collect reasons why they failed, display the info at the end
# if testNumbers is not None, it's an array of tests to execute and we only
# execute tests from that array
# TODO: add logging of how long did it take to execute each test.
def runServerTests(testNumbers=None):
    global g_allTests, g_errors
    failingTests = []
    totalTestsCount = 0
    for test in g_allTests:
        testNumber = test[0]
        if testNumbers != None and testNumber not in testNumbers:
            continue
        if fValidTestOk(test):
            sys.stdout.write(".")
        else:
            sys.stdout.write("F")
            failingTests.append(testNumber)
        totalTestsCount += 1

    failingTestsCount = len(failingTests)
    if failingTestsCount > 0:
        txt = [str(ft) for ft in failingTests]
        print "\n"
        for failingTestNo in failingTests:
            print "Test %d failed because:\n  %s\n" % (failingTestNo, string.join(g_errors[failingTestNo], "\n  "))
        print "%d out of %d tests failed" % (failingTestsCount, totalTestsCount)
        print "Failing tests: %s" % string.join(txt, " ")
    else:
        print "\nAll %d tests passed" % totalTestsCount

if __name__ == "__main__":
    serverToUse = None
    fThreaded = arsutils.fDetectRemoveCmdFlag("-threaded")

    if not fThreaded:
        fThreaded = arsutils.fDetectRemoveCmdFlag("-thread")

    serverToUse = arsutils.getRemoveCmdArg( "-server" )
    if None == serverToUse:
        client.detectAndSetServerToUse()
    else:
        if not client.g_serverList.has_key(serverToUse):
            print "server %s is not known. Known servers:" % serverToUse
            for serverName in client.g_serverList.keys():
                print "   %s" % serverName
            sys.exit(0)
        else:
            client.g_serverToUse = serverToUse

    client.printUsedServer()

    testNumbers = []
    if len(sys.argv) > 1:
        for testNo in sys.argv[1:]:
            testNumbers.append(int(testNo))
    if fThreaded:
        runServerTestsThreaded()
        sys.exit(0)

    if len(testNumbers)>0:
        print "Running tests %s" % string.join([str(testNo) for testNo in testNumbers], " ")
        runServerTests(testNumbers)
    else:
        print "running all tests"
        runServerTests()
    #unittest.main()
