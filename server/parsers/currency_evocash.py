#### Copyright: Krzysztof Kowalczyk
# Owner: Marek Senderski
#
# Purpose:
#  currency
#  http://www.fms.treas.gov/intn.html
#

import string, re
try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise
from parserUtils import *
from ResultType import *

currencyNoResultsText = None # flag - just for tests

g_CountryToAbbrevDict = {
  "AFGHANISTAN" : "AFA",
  "ALBANIA" : "ALL",
  "ALGERIA" : "DZD",
  "ANGOLA" : "AOA",
  "ANTIGUA" : "XCD",
  "ARGENTINA" : "ARS",
  "ARMENIA" : "AMD",
  "AUSTRALIA" : "AUD",
  "AUSTRIA" : "EUR",
  "AZERBAIJAN" : "AZM",
  "BAHAMAS" : "BSD",
  "BAHRAIN" : "BHD",
  "BANGLADESH" : "BDT",
  "BARBADOS" : "BBD",
  "BELARUS" : "BYR",
  "BELGIUM" : "EUR",
  "BELIZE" : "BZD",
  "BENIN" : "XOF",
  "BERMUDA" : "BMD",
  "BOLIVIA" : "BOB",
  "BOSNIA" : "BAM",
  "BOTSWANA" : "BWP",
  "BRAZIL" : "BRL",
  "BRUNEI" : "BND",
  "BULGARIA" : "BGN",
  "BURKINA FASO" : "XOF",
  "BURMA" : "MMK",
  "BURUNDI" : "BIF",
  "CAMBODIA (KHMER)" : "KHR",
  "CAMEROON" : "XAF",
  "CANADA" : "CAD",
  "CAPE VERDE" : "CVE",
  "CENTRAL AFRICAN REPUBLIC" : "XAF",
  "CHAD" : "XAF",
  "CHILE" : "CLP",
  "CHINA" : "CNY",
  "COLOMBIA" : "COP",
  "COMOROS" : "KMF",
  "CONGO" : "XAF",
  "COSTA RICA" : "CRC",
  "COTE D'IVOIRE" : "NOTFOUND",
  "CROATIA" : "HRK",
  "CYPRUS" : "CYP",
  "CZECH" : "CZK",
  "DEM REP OF CONGO" : "CDF",
  "DENMARK" : "DKK",
  "DJIBOUTI" : "DJF",
  "DOMINICAN REPUBLIC" : "DOP",
  "ECUADOR" : "USD",
  "EGYPT" : "EGP",
  "EL SALVADOR" : "SVC",
  "EQUATORIAL GUINEA" : "XAF",
  "ERITREA" : "ETB",
  "ESTONIA" : "EEK",
  "ETHIOPIA" : "ETB",
  "EURO ZONE" : "EUR",
  "FIJI" : "FJD",
  "FINLAND" : "EUR",
  "FRANCE" : "EUR",
  "GABON" : "XAF",
  "GAMBIA" : "GMD",
  "GEORGIA" : "GEL",
  "GERMANY FRG" : "EUR",
  "GHANA" : "GHC",
  "GREECE" : "EUR",
  "GRENADA" : "XCD",
  "GUATEMALA" : "GTQ",
  "GUINEA" : "NOTFOUND",
  "GUINEA BISSAU" : "NOTFOUND",
  "GUYANA" : "GYD",
  "HAITI" : "HTG",
  "HONDURAS" : "HNL",
  "HONG KONG" : "HKD",
  "HUNGARY" : "HUF",
  "ICELAND" : "ISK",
  "INDIA" : "INR",
  "INDONESIA" : "IDR",
  "IRAN" : "IRR",
  "IRAQ" : "IQD",
  "IRELAND" : "EUR",
  "ISRAEL" : "ILS",
  "ITALY" : "EUR",
  "JAMAICA" : "JMD",
  "JAPAN" : "JPY",
  "JORDAN" : "JOD",
  "KAZAKHSTAN" : "KZT",
  "KENYA" : "KES",
  "KOREA" : "KPW",
  "KUWAIT" : "KWD",
  "KYRGYZSTAN" : "KGS",
  "LAOS" : "LAK",
  "LATVIA" : "LVL",
  "LEBANON" : "LBP",
  "LESOTHO" : "LSL",
  "LIBERIA" : "LRD",
  "LITHUANIA" : "LTL",
  "LUXEMBOURG" : "EUR",
  "MACAO" : "MOP",
  "MACEDONIA FYROM" : "MKD",
  "MADAGASCAR" : "MGA",
  "MALAWI" : "MWK",
  "MALAYSIA" : "MYR",
  "MALI" : "XOF",
  "MALTA" : "MTL",
  "MARSHALLS ISLANDS" : "USD",
  "MARTINIQUE" : "EUR",
  "MAURITANIA" : "MRO",
  "MAURITIUS" : "MUR",
  "MEXICO" : "MXN",
  "MICRONESIA" : "USD",
  "MOLDOVA" : "MDL",
  "MONGOLIA" : "MNT",
  "MOROCCO" : "MAD",
  "MOZAMBIQUE" : "MZM",
  "NAMIBIA" : "NAD",
  "NEPAL" : "NPR",
  "NETHERLANDS" : "EUR",
  "NETHERLANDS ANTILLES" : "ANG",
  "NEW ZEALAND" : "NZD",
  "NICARAGUA" : "NIO",
  "NICARAGUA" : "NIO",
  "NIGER" : "XOF",
  "NIGERIA" : "NGN",
  "NORWAY" : "NOK",
  "OMAN" : "OMR",
  "PAKISTAN" : "PKR",
  "PALAU" : "USD",
  "PANAMA" : "PAB",
  "PAPUA NEW GUINEA" : "PGK",
  "PARAGUAY" : "PYG",
  "PERU" : "PEN",
  "PERU" : "PEN",
  "PHILIPPINES" : "PHP",
  "POLAND" : "PLN",
  "PORTUGAL" : "EUR",
  "QATAR" : "QAR",
  "ROMANIA" : "ROL",
  "RUSSIA" : "RUR",
  "RWANDA" : "RWF",
  "SAO TOME &amp; PRINCIPE" : "STD",
  "SAUDI ARABIA" : "SAR",
  "SENEGAL" : "XOF",
  "SERBIA MONTENEGRO" : "CSD",
  "SEYCHELLES" : "SCR",
  "SIERRA LEONE" : "SLL",
  "SINGAPORE" : "SGD",
  "SLOVAK REPUBLIC" : "SKK",
  "SLOVENIA" : "SIT",
  "SOLOMON ISLANDS" : "SBD",
  "SOUTH AFRICA" : "ZAR",
  "SPAIN" : "EUR",
  "SRI LANKA" : "LKR",
  "ST LUCIA" : "NOTFOUND",
  "SUDAN" : "SDD",
  "SURINAME" : "SRD",
  "SWAZILAND" : "SZL",
  "SWEDEN" : "SEK",
  "SWITZERLAND" : "CHF",
  "SYRIA" : "SYP",
  "TAIWAN" : "TWD",
  "TAJIKISTAN" : "RUR",
  "TANZANIA" : "TZS",
  "THAILAND" : "THB",
  "TOGO" : "XOF",
  "TONGA" : "TOP",
  "TRINIDAD &amp; TOBAGO" : "TTD",
  "TUNISIA" : "TND",
  "TURKEY" : "TRL",
  "TURKMENISTAN" : "TMM",
  "UGANDA" : "UGX",
  "UKRAINE" : "UAH",
  "UNITED ARAB EMIRATES" : "AED",
  "UNITED KINGDOM" : "GBP",
  "URUGUAY" : "UYU",
  "UZBEKISTAN" : "UZS",
  "VANUATU" : "VUV",
  "VENEZUELA" : "VEB",
  "VIETNAM" : "VND",
  "WESTERN SAMOA" : "WST",
  "YEMEN" : "YER",
  "YUGOSLAVIA" : "NOTFOUND",
  "ZAMBIA" : "ZMK",
  "ZIMBABWE" : "ZWD"
}

g_AbbrevToRatesDict = {}

# TODO: documentation i.e. describe the format of returned data
def parseCurrency(htmlTxt):
    soup = BeautifulSoup()
    soup.feed(htmlTxt)
    #TABLE WIDTH="100%" BORDER="0" CELLPADDING="0" CELLSPACING="0" BGCOLOR="#009900"
    #<TABLE WIDTH="100%" BORDER="0" CELLPADDING="1" CELLSPACING="1" BGCOLOR="#000000">
    findTable = soup.fetch("table",{"width" : "100%", "border" : "0", "cellpadding" : "1", "cellspacing" : "1", "bgcolor" : "#000000"})
    #print findTable
    if not findTable:
        return (UNKNOWN_FORMAT, currencyNoResultsText)    
    itemTable = findTable[0]
    findTableTR = itemTable.fetch("tr")
    #Parse page and create dictionary
    for itemTR in findTableTR:
        findTD = itemTR.fetch("td")        
        if 0 == len(findTD):
           continue
        if 4 != len(findTD):
            return (UNKNOWN_FORMAT, currencyNoResultsText)
        #print str(findTD[1].contents[0].contents[0].contents[0])
        #print str(findTD[2].contents[0].contents[0]).replace(",","").strip()
        abbrev = str(findTD[1].contents[0].contents[0].contents[0])
        g_AbbrevToRatesDict[abbrev] = float(str(findTD[2].contents[0].contents[0]).replace(",","").strip())
    g_AbbrevToRatesDict["USD"] = 1.0
    return (RESULTS_DATA, g_AbbrevToRatesDict)
