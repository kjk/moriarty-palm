# Contains a list of all fields in InfoMan protocol

transactionId    =  "Transaction-ID"
getCookie        =  "Get-Cookie"
cookie           =  "Cookie"
formatVersion    =  "Format-Version"
error            =  "Error"
verifyRegCode    =  "Verify-Registration-Code"
regCodeValid     =  "Registration-Code-Valid"
protocolVersion  =  "Protocol-Version"
clientInfo       =  "Client-Info"
regCode          =  "Registration-Code"
disabledModules  =  "Disabled-Modules"
getRegCodeDaysToExpire = "Get-Reg-Code-Days-To-Expire"
regCodeDaysToExpire    = "Reg-Code-Days-To-Expire"

getLatestClientVersion = "Get-Latest-Client-Version"
latestClientVersion    = "Latest-Client-Version"

outNoResults = "No-Results"

getUrl = "Get-Url"

# for yahoo!movies
getMovies         = "Get-Movies"
moviesData        = "Movies-Data"
locationUnknown   = "Location-Unknown"
locationAmbiguous = "Location-Ambiguous"

# for epicurious
getRecipesList    = getUrl + "-recipeslist"
getRecipe         = getUrl + "-recipe"
recipiesList      = "Recipes-List"
recipe            = "Recipe"

# for weather
getWeather         = "Get-Weather"
weather            = "Weather"
weatherMultiselect = "Weather-Multiselect"

# for 411
out411NoCity         = "411-No-City"
out411TooManyResults = "411-Too-Many-Results"

get411ReverseZip        = "411-Reverse-Zip"  ## $zipCode
out411ReverseZipResult  = "411-Reverse-Zip-Result"
get411ReverseArea       = "411-Reverse-Area-Code"  ##  $areaCode
out411ReverseAreaResult = "411-Reverse-Area-Code-Result"
get411AreaByCity            = "411-Area-Code-By-City"  ##  $city,$state
out411AreaByCityResult      = "411-Area-Code-By-City-Result"
out411AreaByCityMultiselect = "411-Area-Code-By-City-Multiselect"
get411ZipByCity            = "411-Zip-By-City"  ##  $city,$state
out411ZipByCityResult      = "411-Zip-By-City-Result"
out411ZipByCityMultiselect = "411-Zip-By-City-Multiselect"
get411PersonSearch                = "411-Person-Search"  ##  $firstName,$lastName,$city(or zip),$state
out411PersonSearchResult          = "411-Person-Search-Result"
out411PersonSearchCityMultiselect = "411-Person-Search-City-Multiselect"
get411ReversePhone       = "411-Reverse-Phone"  ##  $phone in format xxx-yyy-zzzz
out411ReversePhoneResult = "411-Reverse-Phone-Result"
get411InternationalCodeSearch = "411-International-Code"  ##  $code
out411InternationalCodeSearchResult = "411-International-Code-Result"
get411BusinessSearch                = "411-Business-Search"  ##  $businessName,$city(or zip),$state,"Yes"/"No"(Include Surrounding Areas),"Name"/"Category"(for now only name is supported)
out411BusinessSearchResult          = "411-Business-Search-Result"
out411BusinessSearchMultiselect     = "411-Business-Search-Multiselect"
get411BusinessSearchByUrl           = "411-Business-Search-By-Url"  ##  $url

# for box office module
getCurrentBoxOffice = "Get-Current-Box-Office"
outCurrentBoxOffice = "Current-Box-Office"

# for currency module
getCurrencyConversion = "Get-Currency-Conversion"
outCurrencyConversion = "Currency-Conversion"

# for dreams module
getDream = "Get-Dream-Interpretation"
outDream = "Dream-Interpretation"

# for jokes module
getJokesList    = "Get-Jokes-List"
getJoke         = "Get-Joke"
outJokesList       = "Jokes-List"
outJoke            = "Joke"

# for gasprices module
getGasPrices = "Get-Gas-Prices"
outGasPrices = "Gas-Prices"

# for stocks module
getStocksList    = "Get-Stocks-List"  ## list with ';' as separator
getStock         = "Get-Stock"  ## $url
getStockByName   = "Get-Stock-By-Name"  ## $name (when name is no symbol)
outStocksList      = "Stocks-List"
outStock           = "Stock"
outStocksListByName = "Stocks-List-By-Name"
getStocksListValidateLast = "Get-Stocks-List-Validate-Last"  ## list with ';' as separator

# for amazon module
outAmazon   = "Amazon"

# for ListsOfBests module
outListsOfBests   = "Lists-Of-Bests"

# for Horoscopes module
getHoroscope   = "Get-Horoscope"
outHoroscope   = "Horoscope"

# for Lyrics module
outLyrics = "Lyrics"

# for tvlistings module
getTvListingsProviders = "Get-TvListings-Providers"
getTvListings = "Get-TvListings"
outTvListingsProviders = "TvListings-Providers"
outTvListingsPartial = "TvListings-Partial"
outTvListingsFull = "TvListings"

getUrlLyricsItem = getUrl + "-lyricsitem"
getUrlLyricsSearch = getUrl + "-lyricssearch"

getUrlAmazonBrowse = getUrl + "-amazonbrowse"
getUrlAmazonItem = getUrl + "-amazonitem"
getUrlAmazonSearch = getUrl + "-amazonsearch"
getUrlAmazonList = getUrl + "-amazonlist"
getUrlAmazonWishList = getUrl + "-amazonwishlist"


getUrlListsOfBestsItem   = getUrl + "-listsofbestsitem"
getUrlListsOfBestsBrowse = getUrl + "-listsofbestsbrowse"
getUrlListsOfBestsSearch = getUrl + "-listsofbestssearch"

getUrlPediaTerm = getUrl + "-pediaterm"
getUrlPediaSearch = getUrl + "-pediasearch"
getUrlPediaRandom = getUrl + "-pediarandom"
getUrlPediaLangs = getUrl + "-pedialangs"
getUrlPediaStats = getUrl + "-pediastats"

outPediaArticle = "Pedia-Article"
outPediaArticleCount = "Pedia-Article-Count"
outPediaArticleTitle = "Pedia-Article-Title"
outPediaReverseLinks = "Pedia-Reverse-Links"
outPediaLangs = "Pedia-Langs"
outPediaSearchResults = "Pedia-Search-Results"
outPediaDbDate = "Pedia-Db-Date"

# for Netflix module
getUrlNetflixItem   = getUrl + "-netflixitem"
getUrlNetflixBrowse = getUrl + "-netflixbrowse"
getUrlNetflixSearch = getUrl + "-netflixsearch"
getUrlNetflixLogin  = getUrl + "-netflixlogin"
getUrlNetflixAdd    = getUrl + "-netflixadd"
getUrlNetflixQueue  = getUrl + "-netflixqueue"
outNetflix       = "Netflix"

outNetflixPasswordRequest = "Netflix-Password-Request"
outNetflixUnknownLogin    = "Netflix-Unknown-Login"
outNetflixLoginOk         = "Netflix-Login-Ok"
outNetflixAddOk           = "Netflix-Add-Ok"
outNetflixAddFailed       = "Netflix-Add-Failed"
outNetflixAddAlreadyAdded = "Netflix-Add-Already-In-Queue"
outNetflixQueue           = "Netflix-Queue"

getUrlDict = getUrl + "-dictterm"
getUrlDictRandom = getUrl + "-dictrandom"
getUrlDictStats = getUrl + "-dictstats"
outDictStats = "Dict-Stats"
outDictDef = "Dict-Def"


# for quotes module
outQuotes    = "Quotes"
getUrlQuotes = getUrl + "-quotes"

# for flights module
outFlights    = "Flights"
getUrlFlights = getUrl + "-flights"

# eBook
getUrlEBookSearch = getUrl + "-eBook-search"
getUrlEBookDownload = getUrl + "-eBook-download"
outEBookSearchResults = "eBook-Search-Results"
outEBookDownload = "eBook-Download"
outEBookName = "eBook-Name"
ebookVersion = "eBook-Version"

# "Get-Url-eBook-browse:<type>[;<level>;<index>]"
# type is one of values from ebooks.BROWSE_TYPES
# level, index are (optional) ints
getUrlEbookBrowse = getUrl + "-eBook-browse"
getUrlEbookHome = getUrl + "-eBook-home"

# for eBay module
getUrlEBay       = getUrl + "-ebay"
getUrlEBayLogin  = getUrl + "-ebaylogin"
outEBay          = "EBay"
# to ignore history
getUrlEBayNoCache  = getUrl + "-ebayno"
outEBayNoCache     = "EBay-No-Cache"

outEBayPasswordRequest = "EBay-Password-Request"
outEBayUnknownLogin    = "EBay-Unknown-Login"
outEBayLoginOk         = "EBay-Login-Ok"

flickrPicturesUploaded = "Flickr-Pictures-Uploaded"

(fieldTypeClient, fieldTypeServer, fieldTypeBoth) = range(3)
(valueNone, valueInline, valuePayload) = range(3)

# describes all fields used in InfoMan protocol. First value describes who
# sends the field (client, server or both). Second value describes the type
# of the value (no value, value inline or payload value)
fieldsInfo = {
    protocolVersion         : (fieldTypeClient, valueInline),
    clientInfo              : (fieldTypeClient, valueInline),
    transactionId           : (fieldTypeBoth,   valueInline),
    cookie                  : (fieldTypeBoth,   valueInline),
    error                   : (fieldTypeServer, valueInline),
    getCookie               : (fieldTypeClient, valueInline),
    regCode                 : (fieldTypeBoth,   valueInline),
    formatVersion           : (fieldTypeServer, valueInline),
    verifyRegCode           : (fieldTypeClient, valueInline),
    regCodeValid            : (fieldTypeServer, valueInline),
    getRegCodeDaysToExpire  : (fieldTypeClient, valueNone),
    regCodeDaysToExpire     : (fieldTypeServer, valueInline),
    getLatestClientVersion  : (fieldTypeClient, valueInline),
    latestClientVersion     : (fieldTypeServer, valueInline),

    outNoResults            : (fieldTypeServer, valueNone),

    outNetflixPasswordRequest : (fieldTypeServer, valueNone),
    outNetflixUnknownLogin    : (fieldTypeServer, valueNone),
    outNetflixLoginOk         : (fieldTypeServer, valueNone),
    outNetflixAddOk           : (fieldTypeServer, valueNone),
    outNetflixAddFailed       : (fieldTypeServer, valueNone),
    outNetflixAddAlreadyAdded : (fieldTypeServer, valueNone),

    outEBayPasswordRequest    : (fieldTypeServer, valueNone),
    outEBayUnknownLogin       : (fieldTypeServer, valueNone),
    outEBayLoginOk            : (fieldTypeServer, valueNone),

    getMovies               : (fieldTypeClient, valueInline),
    getRecipesList          : (fieldTypeClient, valueInline),
    getRecipe               : (fieldTypeClient, valueInline),
    getWeather              : (fieldTypeClient, valueInline),
    get411ReverseZip        : (fieldTypeClient, valueInline),
    get411ReverseArea       : (fieldTypeClient, valueInline),
    get411AreaByCity        : (fieldTypeClient, valueInline),
    get411ZipByCity         : (fieldTypeClient, valueInline),
    get411PersonSearch      : (fieldTypeClient, valueInline),
    get411ReversePhone      : (fieldTypeClient, valueInline),
    get411BusinessSearch    : (fieldTypeClient, valueInline),
    get411BusinessSearchByUrl : (fieldTypeClient, valueInline),
    get411InternationalCodeSearch : (fieldTypeClient, valueInline),
    getCurrentBoxOffice     : (fieldTypeClient, valueNone),
    getDream                : (fieldTypeClient, valueInline),
    getCurrencyConversion   : (fieldTypeClient, valueNone),
    getJokesList            : (fieldTypeClient, valueInline),
    getJoke                 : (fieldTypeClient, valueInline),
    getStocksList           : (fieldTypeClient, valueInline),
    getStock                : (fieldTypeClient, valueInline),
    getStockByName          : (fieldTypeClient, valueInline),
    getStocksListValidateLast : (fieldTypeClient, valueInline),
    getGasPrices              : (fieldTypeClient, valueInline),
    getHoroscope              : (fieldTypeClient, valueInline),
    getTvListingsProviders  : (fieldTypeClient, valueInline),
    getTvListings               : (fieldTypeClient, valueInline),

    getUrl                          : (fieldTypeClient, valueInline),

    moviesData          : (fieldTypeServer, valuePayload),
    locationAmbiguous   : (fieldTypeServer, valuePayload),
    locationUnknown     : (fieldTypeServer, valueNone),
    recipiesList        : (fieldTypeServer, valuePayload),
    recipe              : (fieldTypeServer, valuePayload),
    weather             : (fieldTypeServer, valuePayload),
    weatherMultiselect  : (fieldTypeServer, valuePayload),

    out411NoCity            : (fieldTypeServer, valueNone),
    out411TooManyResults    : (fieldTypeServer, valueNone),

    out411ReverseZipResult  : (fieldTypeServer, valuePayload),
    out411ReverseAreaResult : (fieldTypeServer, valuePayload),
    out411AreaByCityResult  : (fieldTypeServer, valuePayload),
    out411AreaByCityMultiselect : (fieldTypeServer, valuePayload),
    out411ZipByCityResult       : (fieldTypeServer, valuePayload),
    out411ZipByCityMultiselect  : (fieldTypeServer, valuePayload),
    out411PersonSearchResult    : (fieldTypeServer, valuePayload),
    out411PersonSearchCityMultiselect : (fieldTypeServer, valuePayload),
    out411ReversePhoneResult    : (fieldTypeServer, valuePayload),
    out411InternationalCodeSearchResult : (fieldTypeServer, valuePayload),
    out411BusinessSearchResult          : (fieldTypeServer, valuePayload),
    out411BusinessSearchMultiselect     : (fieldTypeServer, valuePayload),

    outCurrentBoxOffice     : (fieldTypeServer, valuePayload),
    outCurrencyConversion   : (fieldTypeServer, valuePayload),
    outDream                : (fieldTypeServer, valuePayload),
    outJokesList            : (fieldTypeServer, valuePayload),
    outJoke                 : (fieldTypeServer, valuePayload),
    outStocksList           : (fieldTypeServer, valuePayload),
    outStock                : (fieldTypeServer, valuePayload),
    outStocksListByName     : (fieldTypeServer, valuePayload),
    outAmazon               : (fieldTypeServer, valuePayload),
    outGasPrices            : (fieldTypeServer, valuePayload),
    outNetflix              : (fieldTypeServer, valuePayload),
    outNetflixQueue         : (fieldTypeServer, valuePayload),
    outHoroscope            : (fieldTypeServer, valuePayload),
    outListsOfBests         : (fieldTypeServer, valuePayload),
    outLyrics               : (fieldTypeServer, valuePayload),
    outTvListingsProviders  : (fieldTypeServer, valuePayload),
    outTvListingsPartial        : (fieldTypeServer, valuePayload),
    outTvListingsFull           : (fieldTypeServer, valuePayload),
    outQuotes                   : (fieldTypeServer, valuePayload),
    outFlights                  : (fieldTypeServer, valuePayload),
    outEBay                     : (fieldTypeServer, valuePayload),
    outEBayNoCache              : (fieldTypeServer, valuePayload),
    outDictStats                : (fieldTypeServer, valuePayload),

    getUrlLyricsItem        : (fieldTypeClient, valueInline),
    getUrlLyricsSearch      : (fieldTypeClient, valueInline),
    getUrlAmazonBrowse      : (fieldTypeClient, valueInline),
    getUrlAmazonItem        : (fieldTypeClient, valueInline),
    getUrlAmazonSearch      : (fieldTypeClient, valueInline),
    getUrlAmazonList        : (fieldTypeClient, valueInline),
    getUrlAmazonWishList    : (fieldTypeClient, valueInline),
    getUrlDict              : (fieldTypeClient, valueInline),
    getUrlDictRandom        : (fieldTypeClient, valueInline),
    getUrlNetflixItem       : (fieldTypeClient, valueInline),
    getUrlNetflixBrowse     : (fieldTypeClient, valueInline),
    getUrlNetflixSearch     : (fieldTypeClient, valueInline),
    getUrlNetflixLogin      : (fieldTypeClient, valueInline),
    getUrlNetflixAdd        : (fieldTypeClient, valueInline),
    getUrlNetflixQueue      : (fieldTypeClient, valueInline),
    getUrlListsOfBestsItem       : (fieldTypeClient, valueInline),
    getUrlListsOfBestsBrowse     : (fieldTypeClient, valueInline),
    getUrlListsOfBestsSearch     : (fieldTypeClient, valueInline),
    getUrlQuotes                 : (fieldTypeClient, valueInline),
    getUrlFlights                : (fieldTypeClient, valueInline),
    getUrlEBay                   : (fieldTypeClient, valueInline),
    getUrlEBayLogin              : (fieldTypeClient, valueInline),
    getUrlEBayNoCache            : (fieldTypeClient, valueInline),
    getUrlDictStats              : (fieldTypeClient, valueInline),

    outDictDef              : (fieldTypeServer, valuePayload),

    getUrlPediaTerm         : (fieldTypeClient, valueInline),
    getUrlPediaRandom   : (fieldTypeClient, valueInline),
    getUrlPediaSearch     : (fieldTypeClient, valueInline),
    getUrlPediaLangs       : (fieldTypeClient, valueNone),
    getUrlPediaStats        : (fieldTypeClient, valueInline),

    outPediaLangs       : (fieldTypeServer, valuePayload),
    outPediaReverseLinks : (fieldTypeServer, valuePayload),
    outPediaArticleTitle    : (fieldTypeServer, valueInline),
    outPediaArticle         : (fieldTypeServer, valuePayload),
    outPediaSearchResults : (fieldTypeServer, valuePayload),
    outPediaArticleCount     : (fieldTypeServer, valueInline),
    outPediaDbDate              : (fieldTypeServer, valueInline),

    getUrlEBookSearch       : (fieldTypeClient, valueInline),
    getUrlEBookDownload     : (fieldTypeClient, valueInline),
    outEBookSearchResults   : (fieldTypeServer, valuePayload),
    outEBookDownload        : (fieldTypeServer, valuePayload),
    outEBookName            : (fieldTypeServer, valueInline),
    getUrlEbookBrowse       : (fieldTypeClient, valueInline),
    getUrlEbookHome          : (fieldTypeClient, valueNone),
    ebookVersion:                   (fieldTypeClient, valueNone),

    flickrPicturesUploaded      : (fieldTypeClient, valueInline),
}

# return True if this is a valid field
def fValidField(fieldName):
    if fieldsInfo.has_key(fieldName):
        return True
    return False

# return True if a given field is a field sent by a client
def fClientField(fieldName):
    if not fValidField(fieldName):
        return False
    fieldType =  fieldsInfo[fieldName][0]
    if fieldTypeClient==fieldType or fieldTypeBoth==fieldType:
        return True
    return False

# return True if a given field is a field sent by a server
def fServerField(fieldName):
    if not fValidField(fieldName):
        return False
    fieldType = fieldsInfo[fieldName][0]
    if fieldTypeServer==fieldType or fieldTypeBoth==fieldType:
        return True
    return False

# return True if a given field is a payload field (i.e. its value is a payload)
def fPayloadField(fieldName):
    fieldValueType = fieldsInfo[fieldName][1]
    if valuePayload==fieldValueType:
        return True
    return False

def fFieldHasArguments(fieldName):
    fieldValueType = fieldsInfo[fieldName][1]
    if valueNone == fieldValueType:
        return False
    return True

