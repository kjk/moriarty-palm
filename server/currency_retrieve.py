# -*- coding: latin-1 -*-
import urllib2, urllib
from Retrieve import getHostFromUrl, getHttp

from parserUtils import *
from ResultType import *
from arsutils import log, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC, exceptionAsStr
from parserErrorLogger import logParsingFailure
import arsutils
import currency_exchangerate, currency_xe, currency_pacific, currency_moneyextra
import currency_ny_frb
import thread, threading

_g_exchangerate_urls = [
    "http://www.exchangerate.com/world_rates.html?cont=Africa",
    "http://www.exchangerate.com/world_rates.html?cont=Central%20America/Caribbean",
    "http://www.exchangerate.com/world_rates.html?cont=Asia",
    "http://www.exchangerate.com/world_rates.html?cont=Europe",
    "http://www.exchangerate.com/world_rates.html?cont=North%20America",
    "http://www.exchangerate.com/world_rates.html?cont=Australia/Oceania",
    "http://www.exchangerate.com/world_rates.html?cont=Middle%20East",
    "http://www.exchangerate.com/world_rates.html?cont=South%20America"
]

def _parse_currency(htmlText, function, url):
    try:
        res = function(htmlText)
        return res
    except:
        logParsingFailure("Get-Currency-Conversion", "", htmlText, url)
        raise

def _retrieve_exchangerate():
    global _g_exchangerate_urls
    currencies = dict()
    for url in _g_exchangerate_urls:
        htmlText = getHttp(url, retryCount=3)
        if htmlText is None:
            return (RETRIEVE_FAILED, None)
        res, data =  _parse_currency(htmlText, currency_exchangerate.parseCurrencyData, url)
        if RESULTS_DATA != res:
            return res, data
        currencies.update(data)
    return (RESULTS_DATA, currencies)

_g_xe_url = "http://www.xe.com/ict/"

#?currency=USD&historical=false&month=01&day=01&year=2004&template=ict-en

def _retrieve_xe():
    global _g_xe_url
    formData = {
        "basecur": "USD",
        "historical": "false",
        "month": "1",
        "day": "1",
        "year": "2004",
        "sort_by": "code",
        "template": "ict-en"
    }
    encFormData = urllib.urlencode(formData)
    headers = {
        #"Host": getHostFromUrl(_g_xe_url),
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322)",
        "Referer": _g_xe_url
    }
    request = urllib2.Request(_g_xe_url, encFormData, headers)
    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler())
    htmlText = None
    result = None
    try:
        result = opener.open(request)
        htmlText = result.read()
    except Exception, ex:
        txt = exceptionAsStr(ex)
        log(SEV_EXC, "failed to retrieve data for '%s'\nreason:%s\n" % (_g_xe_url, txt))
    if result is not None:
        result.close()
    else:
        return (RETRIEVE_FAILED, None)
    res, data = _parse_currency(htmlText, currency_xe.parseCurrencyData, _g_xe_url)
    return (res, data)

_g_pacific_url = "http://fx.sauder.ubc.ca/today.html"

def _retrieve_pacific():
    global _g_pacific_url
    htmlText = getHttp(_g_pacific_url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    return _parse_currency(htmlText, currency_pacific.parseCurrencyData, _g_pacific_url)

##_g_moneyextra_url = "http://www.moneyextra.com/rates/currency/tourist.htm"
_g_moneyextra_url = "http://www.moneyextra.com/advice/touristrates/"

def _retrieve_moneyextra():
    global _g_moneyextra_url
    htmlText = getHttp(_g_moneyextra_url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    return _parse_currency(htmlText, currency_moneyextra.parseCurrencyData, _g_moneyextra_url)

_g_ny_frb_url = "http://www.ny.frb.org/markets/fxrates/noon.cfm"

def _retrieve_ny_frb():
    global _g_ny_frb_url
    htmlText = getHttp(_g_ny_frb_url, retryCount=3)
    if htmlText is None:
        return (RETRIEVE_FAILED, None)
    return _parse_currency(htmlText, currency_ny_frb.parseCurrencyData, _g_ny_frb_url)

_g_retrieve_functions = [
    _retrieve_moneyextra,
    _retrieve_exchangerate,
    _retrieve_xe,
    _retrieve_pacific,
    _retrieve_ny_frb
]

_g_tracked_currencies = {
    "AED": ("Dirhams", "United Arab Emirates"),
    "AFA": ("Afghanis", "Afghanistan"),
    "ALL": ("Leke", "Albania"),
    "AMD": ("Drams", "Armenia"),
    "ANG": ("Netherlands Antilles Guilders", "Aruba"),
    "AOA": ("Kwanza", "Angola"),
    "ARS": ("Pesos", "Argentina"),
    "AUD": ("Dollars", "Australia"),
    "AZM": ("Manats", "Azerbaijan"),
    "BAM": ("Convertible Marka", "Bosnia and Herzegovina"),
    "BBD": ("Dollars", "Barbados"),
    "BDT": ("Taka", "Bangladesh"),
    "BGN": ("Leva", "Bulgaria"),
    "BHD": ("Dinars", "Bahrain"),
    "BIF": ("Francs", "Burundi"),
    "BMD": ("Dollars", "Bermuda"),
    "BND": ("Dollars", "Brunei Darussalam"),
    "BOB": ("Bolivianos", "Bolivia"),
    "BRL": ("Real", "Brazil"),
    "BSD": ("Dollars", "Bahamas"),
    "BWP": ("Pulas", "Botswana"),
    "BYR": ("Rubles", "Belarus"),
    "BZD": ("Dollars", "Belize"),
    "CAD": ("Dollars", "Canada"),
    "CHF": ("Switzerland Francs", "Liechtenstein"),
    "CLP": ("Pesos", "Chile"),
    "CNY": ("Yuan Renminbi", "China"),
    "COP": ("Pesos", "Colombia"),
    "CRC": ("Colones", "Costa Rica"),
    "CVE": ("Escudos", "Cape Verde"),
    "CYP": ("Pounds", "Cyprus"),
    "CZK": ("Koruny", "Czech Republic"),
    "DJF": ("Francs", "Djibouti"),
    "DKK": ("Kroner", "Denmark"),
    "DOP": ("Pesos", "Dominican Republic"),
    "DZD": ("Dinars", "Algeria"),
    "EEK": ("Krooni", "Estonia"),
    "EGP": ("Pounds", "Egypt"),
    "ETB": ("Ethiopia Birr", "Eritrea, Eritrea"),
    "EUR": ("Euro", "Austria, Belgium, Finland, France, Greece, Eire (Ireland), Italy, Luxembourg, Martinique, Portugal, Spain"),
    "FJD": ("Dollars", "Fiji"),
    "GBP": ("Pounds", "Britain (United Kingdom)"),
    "GEL": ("Lari", "Georgia"),
    "GHC": ("Cedis", "Ghana"),
    "GMD": ("Dalasi", "Gambia"),
    "GTQ": ("Quetzales", "Guatemala"),
    "GYD": ("Dollars", "Guyana"),
    "HKD": ("Dollars", "Hong Kong"),
    "HNL": ("Lempiras", "Honduras"),
    "HRK": ("Kuna", "Croatia"),
    "HTG": ("Gourdes", "Haiti"),
    "HUF": ("Forint", "Hungary"),
    "IDR": ("Indonesia Rupiahs", "East Timor"),
    "ILS": ("New Shekels", "Israel"),
    "INR": ("India Rupeess", "Bhutan"),
    "IQD": ("Dinars", "Iraq"),
    "IRR": ("Rials", "Iran"),
    "ISK": ("Kronur", "Iceland"),
    "JMD": ("Dollars", "Jamaica"),
    "JOD": ("Dinars", "Jordan"),
    "JPY": ("Yen", "Japan"),
    "KES": ("Shillings", "Kenya"),
    "KGS": ("Soms", "Kyrgyzstan"),
    "KMF": ("Francs", "Comoros"),
    "KPW": ("Won", "Korea (North)"),
    "KRW": ("Won", "Korea (South)"),
    "KWD": ("Dinars", "Kuwait"),
    "LAK": ("Kips", "Laos"),
    "LBP": ("Pounds", "Lebanon"),
    "LKR": ("Rupees", "Sri Lanka"),
    "LRD": ("Dollars", "Liberia"),
    "LSL": ("Maloti", "Lesotho"),
    "LTL": ("Litai", "Lithuania"),
    "LVL": ("Lati", "Latvia"),
    "MAD": ("Dirhams", "Morocco"),
    "MDL": ("Lei", "Moldova"),
    "MGA": ("Ariary", "Madagascar"),
    "MMK": ("Kyats", "Burma (Myanmar)"),
    "MNT": ("Tugriks", "Mongolia"),
    "MRO": ("Ouguiyas", "Mauritania"),
    "MTL": ("Liri", "Malta"),
    "MUR": ("Rupees", "Mauritius"),
    "MWK": ("Kwachas", "Malawi"),
    "MXN": ("Pesos", "Mexico"),
    "MYR": ("Ringgits", "Malaysia"),
    "MZM": ("Meticais", "Mozambique"),
    "NAD": ("Dollars", "Namibia"),
    "NGN": ("Nairas", "Nigeria"),
    "NIO": ("Gold Cordobas", "Nicaragua"),
    "NOK": ("Norway Kroner", "Bouvet Island"),
    "NPR": ("Rupees", "Nepal"),
    "NZD": ("New Zealand Dollars", "Cook Islands"),
    "OMR": ("Rials", "Oman"),
    "PAB": ("Balboa", "Panama"),
    "PEN": ("Nuevos Soles", "Peru"),
    "PGK": ("Kina", "Papua New Guinea"),
    "PHP": ("Pesos", "Philippines"),
    "PKR": ("Rupees", "Pakistan"),
    "PLN": ("Zlotych", "Poland"),
    "PYG": ("Guarani", "Paraguay"),
    "QAR": ("Rials", "Qatar"),
    "ROL": ("Lei", "Romania"),
    "RUR": ("Rubles", "Russia, Tajikistan"),
    "RWF": ("Francs", "Rwanda"),
    "SAR": ("Riyals", "Saudi Arabia"),
    "SBD": ("Dollars", "Solomon Islands"),
    "SCR": ("Rupees", "Seychelles"),
    "SDD": ("Dinars", "Sudan"),
    "SEK": ("Kronor", "Sweden"),
    "SGD": ("Dollars", "Singapore"),
    "SIT": ("Tolars", "Slovenia"),
    "SLL": ("Leones", "Sierra Leone"),
    "SRD": ("Dollars", "Suriname"),
    "SVC": ("Colones", "El Salvador"),
    "SYP": ("Pounds", "Syria"),
    "SZL": ("Emalangeni", "Swaziland"),
    "THB": ("Baht", "Thailand"),
    "TMM": ("Manats", "Turkmenistan"),
    "TND": ("Dinars", "Tunisia"),
    "TOP": ("Pa'anga", "Tonga"),
    "TRL": ("Liras", "Turkey"),
    "TWD": ("New Dollars", "Taiwan"),
    "TZS": ("Shillings", "Tanzania"),
    "UAH": ("Hryvnia", "Ukraine"),
    "UGX": ("Shillings", "Uganda"),
    "USD": ("United States Dollars", "USA, Ecuador, Micronesia (Federated States of), Palau"),
    "UYU": ("Pesos", "Uruguay"),
    "UZS": ("Sums", "Uzbekistan"),
    "VEB": ("Bolivares", "Venezuela"),
    "VUV": ("Vatu", "Vanuatu"),
    "WST": ("Tala", "Western Samoa (Samoa)"),
    "XAF": ("Communauté Financiere Africaine Francs", "Cameroon, Central African Republic, Chad, Congo/Brazzaville, Equatorial Guinea, Gabon"),
    "XCD": ("East Caribbean Dollars", "Antigua and Barbuda, Grenada"),
    "XOF": ("Communauté Financiere Africaine Francs", "Benin, Burkina Faso, Mali, Niger, Senegal, Togo"),
    "YER": ("Rials", "Yemen"),
    "ZAR": ("South Africa Rand", "Lesotho"),
    "ZMK": ("Kwacha", "Zambia"),
    "ZWD": ("Zimbabwe Dollars", "Zimbabwe")
}

_g_currency_cache_lock = thread.allocate_lock()
_g_currency_cache = {}
_g_cache_update_interval = 30 * 60 # In seconds - currently 30 minutes

def getCurrencies():
    out = {}
    _g_currency_cache_lock.acquire()
    try:
        out.update(_g_currency_cache)
    finally:
        _g_currency_cache_lock.release()
    return out


def _update_cache():
    global _g_currency_cache, _g_currency_cache_lock, _g_retrieve_functions, _g_tracked_currencies, _g_cache_update_interval

    t = threading.Timer(_g_cache_update_interval, _update_cache)
    t.start()

    out = {}
    tracked = {}
    tracked.update(_g_tracked_currencies)
    for func in _g_retrieve_functions:
        if 0 == len(tracked):
            break
        try:
            res, data = func()
            if RESULTS_DATA != res:
                log(SEV_MED, "currency parser: %s returned result: %d" % (str(func), res))
                continue
            for item in data.iteritems():
                key, value = item

                #if key in ["KRW"]:
                #    print "Func: %s" % (str(func))
                #    print "Key: %s   Value: %s " % (key, str(value))
                if tracked.has_key(key) and 0 != value:
                    out[key] = value
                    del tracked[key]
        except Exception, ex:
            log(SEV_EXC, exceptionAsStr(ex))

    _g_currency_cache_lock.acquire()
    try:
        _g_currency_cache = out
    finally:
        _g_currency_cache_lock.release()

def startCurrencyCaching():
    _update_cache()

def main():
    startCurrencyCaching()
    
if __name__ == "__main__":
    main()
