import random, re, urllib, time, calendar, copy, thread, threading, cookielib

from Retrieve import retrieveHttpResponseWithRedirectionHandleException

from parserUtils import universalDataFormat
from ResultType import *
from arsutils import log, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC, exceptionAsStr
from parserErrorLogger import logParsingFailure

import BeautifulSoup, entities, Fields

from MySQLdb import IntegrityError
from MySQLdb.cursors import SSDictCursor

from ResultType import TVLISTINGS_PROVIDERS, TVLISTINGS_PARTIAL, TVLISTINGS_FULL, UNKNOWN_FORMAT

def convertEntities(text):
    text = text.replace("&nbsp;", " ")
    text = entities.convertEntities(text)
    return text

PROGRAM_TYPE_SPORTS, PROGRAM_TYPE_MOVIE, PROGRAM_TYPE_SERIES, PROGRAM_TYPE_NEWS, PROGRAM_TYPE_SPECIAL, PROGRAM_TYPE_CHILDREN, PROGRAM_TYPE_OTHER = range(7)

# mimics zap2it's JavaScript
def _randomseven():
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    res = ""
    for i in range(7):
        res += random.choice(letters)
    return res

def _utc_time():
    d = time.gmtime()
    s = "%d%d%d0" % (d.tm_hour, d.tm_min, d.tm_sec)
    return s

_g_zap2it_cookie_domain = ".zap2it.com"

def _zap2it_cookie(name, value, expires = None):
    global _g_zap2it_cookie_domain
    c = cookielib.Cookie(None, name, value, None, False,
        _g_zap2it_cookie_domain, True, True, "/", True, None,
        expires, expires is None, None, None, None)
    return c

def _zap2it_get_cookie(jar, name):
    for cookie in jar:
        if name == cookie.name:
            return cookie
    return None

def _zap2it_get_crumb(cookie, crumb):
    crumbName = crumb + "="
    start = cookie.value.find(crumbName)
    if -1 != start:
        start += len(crumbName)
        end = cookie.value.find("|", start)
        if -1 == end:
            end = len(cookie.value)
        return cookie.value[start:end]
    return None

def _zap2it_set_crumb(cookie, crumb, value):
    crumbName = crumb + "="
    start = cookie.value.find(crumbName)
    end = len(cookie.value)
    if -1 !=    start:
        end = cookie.value.find(";", start)
        if -1 == end:
            end = len(cookie.value)
    else:
        start = len(cookie.value)
    cookie.value = cookie.value[:start] + crumbName + value + "|" + cookie.value[end:]

def _zap2it_tracker(jar):
    cookie = _zap2it_get_cookie(jar, "zap_sugar")
    expSession = time.time() + 60 * 15
    if cookie is None:
        cookie = _zap2it_cookie("zap_sugar", "", expSession)
        _zap2it_set_crumb(cookie, "id", _utc_time() + _randomseven())
        _zap2it_set_crumb(cookie, "count", "1")
        jar.set_cookie(cookie)
    else:
        count = int(_zap2it_get_crumb(cookie, "count"))
        count += 1
        _zap2it_set_crumb(cookie, "count", str(count))

    expPersist = time.time() + 60 * 60 * 24 * 365
    cookie = _zap2it_get_cookie(jar, "zap_oatmeal")
    if cookie is None:
        cookie = _zap2it_cookie("zap_oatmeal", "", expPersist)
        _zap2it_set_crumb(cookie, "id", _utc_time() + _randomseven())
        jar.set_cookie(cookie)

def _zap2it_set_postalcode(jar, zipCode):
    expPersist = time.time() + 60 * 60 * 24 * 365
    cookie = _zap2it_get_cookie(jar, "zap_oatmeal")
    assert cookie is not None
    cookie.expires = expPersist
    _zap2it_set_crumb(cookie, "postalcode", zipCode)

    cookie = _zap2it_cookie("postalcode", zipCode, expPersist)
    jar.set_cookie(cookie)

def _zap2it_set_tvpartner(jar, partner):
    expPersist = time.time() + 60 * 60 * 24 * 365
    cookie = _zap2it_get_cookie(jar, "zap_oatmeal")
    assert cookie is not None
    cookie.expires = expPersist
    _zap2it_set_crumb(cookie, "tvpartner", partner)

def _zap2it_set_tvheadend(jar, providerName):
    expPersist = time.time() + 60 * 60 * 24 * 365
    cookie = _zap2it_get_cookie(jar, "zap_oatmeal")
    assert cookie is not None
    cookie.expires = expPersist
    _zap2it_set_crumb(cookie, "tvheadend", providerName)

_g_zap2it_start_url = "http://tvlistings.zap2it.com/"
_g_zap2it_zipEntry_url = "http://tvlistings.zap2it.com/zipcode.asp?partner_id=national"

def _zap2it_parse_providers(htmlText):
    soup = BeautifulSoup.BeautifulSoup()
    soup.feed(htmlText)
    providers = {}
    options = soup("option")
    for option in options:
        provId = int(convertEntities(str(option["value"])).strip())
        provider = convertEntities(str(option.contents[0])).strip()
        providers[provId] = provider
    return providers

def _zap2it_opener(jar):
    hh = urllib2.HTTPHandler()
#    hh.set_http_debuglevel(1)
    opener = urllib2.build_opener(hh, urllib2.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-Agent", "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322)")]
    return opener

# returns tuple (response, opener)
def _zap2it_get_providers_stage(jar, zipCode):
    try:
        jar.clear(_g_zap2it_cookie_domain)
    except:
        pass
    opener = _zap2it_opener(jar)
    request = urllib2.Request(_g_zap2it_start_url)
    response = opener.open(request)
    response.close()

    _zap2it_tracker(jar)

    formData = {
        "partner_id": "national",
        "zipcode": zipCode,
        "FormName": "zipcode.asp",
        "submit1": "Continue"
    }
    encData = urllib.urlencode(formData)
    _zap2it_set_postalcode(jar, zipCode)
    _zap2it_set_tvpartner(jar, "national")

    request = urllib2.Request(_g_zap2it_zipEntry_url, encData)
    request.add_header("Referer", _g_zap2it_zipEntry_url)
    response = opener.open(request)
    _zap2it_tracker(jar)
    return (response, opener)

_g_zap2it_provider_url = "http://tvlistings.zap2it.com/system.asp?partner_id=national&zipcode=%s"
_g_zap2it_grid_url = "http://tvlistings.zap2it.com/grid.asp?partner_id=national"
_g_zap2it_listings_url = "http://tvlistings.zap2it.com/listings_redirect.asp?partner_id=national"

# listings_redirect.asp?station_num=11211&partner_id=national
_g_zap2it_station_id_re = re.compile(r"listings_redirect\.asp\?station_num=(\d+)\&partner_id=national", re.I + re.S)

# program.asp?dbKey=SH6839800000&prog_id=2668290&partner_id=national
_g_zap2it_program_id_re = re.compile(r"program\.asp\?dbKey=(\w+)\&prog_id=(\d+)&partner_id=national", re.I + re.S)

# program.asp?dbKey=EP0000510143&prog_id=1635951&series_id=356624&partner_id=national
_g_zap2it_series_id_re = re.compile(r"program\.asp\?dbKey=(\w+)&prog_id=(\d+)&(amp;)?series_id=(\d+)&partner_id=national", re.I + re.S)
# 4:00 AM
_g_zap2it_hour_re = re.compile(r"(\d+)\:(\d+) ((AM)|(PM))", re.I + re.S)

def _zap2it_listing_broadcast_time(cell, date):
    hour = convertEntities(str(cell.first("font").contents[0])).strip()
    match = _g_zap2it_hour_re.match(hour)
    h = int(match.group(1))
    m = int(match.group(2))
    pm = False
    if 'PM' == match.group(3):
        pm = True
    if 12 == h:
        h = 0
    if pm:
        h += 12
    # hack: I have to use such a strange conversion as time.struct_time is immutable :-(
    broadcastTime = time.localtime(time.mktime((date.tm_year, date.tm_mon, date.tm_mday, h , m, 0, -1, -1, -1)))
    return broadcastTime

def _zap2it_parse_listings(conn, htmlText, date, provider, stations, programs):
    soup = BeautifulSoup.BeautifulSoup()
    soup.feed(htmlText)
    # cellSpacing=0 cellPadding=0 width=100% bgColor=white border="1"
    outerTable = soup.first("table", {"border": "1", "width": "100%", "cellpadding": "0", "cellspacing": "0", "bgcolor": "white"})
    # WIDTH="100%" CELLSPACING="0" BORDER="0" CELLPADDING="0"
    innerTable = outerTable.first("table", {"border": "0", "width": "100%", "cellpadding": "0", "cellspacing": "0"})
    rows = innerTable.fetch("tr")
    broadcastTime = None
    cursor = None
    useDb = False
    out = []
    if conn is not None:
        useDb = True
        cursor = conn.cursor()
    try:
        for row in rows:
            cells = row.fetch("td")
            cell = cells[0]
            width = cell["width"]
            if "100%" == width:
                broadcastTime = _zap2it_listing_broadcast_time(cell, date)
            else:
                if row.first("div", {"style": "display: none"}) is not None:
                    continue
                assert broadcastTime is not None
                # <td width="10%" valign="top"><font face="arial, helvetica" size="2"><a href="listings_redirect.asp?station_num=16976&partner_id=national">NWCN</a></font></td>
                cell = cells[1]
                link = cell.first("a")
                stationId = int(_g_zap2it_station_id_re.match(str(link["href"])).group(1))
                stationName = convertEntities(str(link.contents[0])).strip()

                # <td width="5%" valign="top" align="right"><font face="arial, helvetica" size="2"><a href="listings_redirect.asp?station_num=16976&partner_id=national">2</a></font></td>
                cell = cells[2]
                link = cell.first("a")

                stationIndex = convertEntities(str(link.contents[0])).strip()

                if not stations.has_key(stationId):
                    if useDb:
                        try:
                            cursor.execute("INSERT INTO zap2it_stations (id, name) VALUES (%d, '%s')" % (stationId, conn.escape_string(stationName)))
                        except IntegrityError:
                            pass
                        try:
                            cursor.execute("INSERT INTO zap2it_providers_listings (provider_id, station_id, index_in_listing) VALUES (%d, %d, %s)" % (provider, stationId, stationIndex))
                        except IntegrityError:
                            pass
                    stations[stationId] = True

                cell = cells[4]
                link = cell.first("a")
                href = _g_zap2it_program_id_re.match(str(link["href"]))
                programDbKey = href.group(1)
                programId = href.group(2)
                programId = programDbKey + "|" + programId
                programTitle = convertEntities(str(link.contents[0])).strip()

                seriesId = None
                seriesVolumeTitle = None
                subtitle = cell.first("i")
                if subtitle is not None:
                    link = subtitle.first("a")
                    seriesVolumeTitle = convertEntities(str(link.contents[0])).strip()
                    href = _g_zap2it_series_id_re.match(str(link["href"]))
                    if href is not None:
                        seriesId = int(href.group(4))

                yearRating = None
                category = None
                description = None
                stars = None
                format = None

                if 4 == len(cell.contents):
                    others = cell.contents[3]

                    category = convertEntities(str(others.contents[0])).strip()

                    if 0 != len(others.contents[1].contents):
                        yearRating = convertEntities(str(others.contents[1].contents[0])).strip()

                    if 0 != len(others.contents[3].contents):
                        description = convertEntities(str(others.contents[3].contents[0])).strip()

                    stars = convertEntities(str(others.contents[4])).strip()

                    if 0 != len(others.contents[5].contents):
                        programFormat = convertEntities(str(others.contents[5].contents[0])).strip()
                else:
                    assert 9 == len(cell.contents)

                    if 0 != len(cell.contents[3].contents):
                        yearRating = convertEntities(str(cell.contents[3].contents[0])).strip()

                    if 0 != len(cell.contents[5].contents):
                        description = convertEntities(str(cell.contents[5].contents[0])).strip()

                    stars = convertEntities(str(cell.contents[6])).strip()

                    if 0 != len(cell.contents[7].contents):
                        format = convertEntities(str(cell.contents[7].contents[0])).strip()

                additionalInfo = ""
                if stars is not None:
                    additionalInfo += (" " + stars)
                if yearRating is not None:
                    additionalInfo += (" " + yearRating)
                if format is not None:
                    additionalInfo += (" " + stars)
                additionalInfo = additionalInfo.strip()
                if 0 == len(additionalInfo):
                    additionalInfo = None

                if not useDb:
                    record = [stationId, stationName, stationIndex, broadcastTime, programId, programTitle, seriesId, seriesVolumeTitle, category, additionalInfo, description]
                    record = _escape_record(record)
                    out.append(record)
                else:
                    stationIndex = conn.string_literal(stationIndex)

                    if additionalInfo is None:
                        additionalInfo = 'NULL'
                    else:
                        additionalInfo = conn.string_literal(additionalInfo)

                    programDbId = None
                    programKey = (programId, seriesId)

                    programId = conn.string_literal(programId)
                    programTitle = conn.string_literal(programTitle)

                    if seriesId is not None:
                        seriesId = str(seriesId)
                    else:
                        seriesId = 'NULL'

                    if seriesVolumeTitle is None:
                        seriesVolumeTitle = 'NULL'
                    else:
                        seriesVolumeTitle = conn.string_literal(seriesVolumeTitle)

                    if category is None:
                        category = 'NULL'
                    else:
                        category = conn.string_literal(category)

                    if description is None:
                        description = 'NULL'
                    else:
                        description = conn.string_literal(description)

                    if programKey not in programs:
                        try:
                            cursor.execute("""
                                INSERT INTO zap2it_programs (zap2it_id, title, series_id, series_volume_title, category, additional_info, description)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)""" %
                                (programId, programTitle, seriesId, seriesVolumeTitle, category, additionalInfo, description)
                            )
                            programDbId = cursor.lastrowid
                        except IntegrityError:
                            cursor.execute("SELECT id FROM zap2it_programs WHERE zap2it_id = %s AND series_id = %s" % (programId, seriesId))
                            programDbId = cursor.fetchone()[0]
                        programs[programKey] = programDbId
                    else:
                        programDbId = programs[programKey]
                    try:
                        cursor.execute("INSERT INTO zap2it_stations_schedule (program_id, station_id, time) VALUES (%d, %d, '%s')" % (programDbId, stationId, time.strftime("%Y-%m-%d %H:%M:%S", broadcastTime)))
                    except IntegrityError:
                        pass
        if useDb:
            cursor.execute("INSERT INTO zap2it_cached_data (provider_id, date) VALUES (%d, '%s')" % (provider, time.strftime("%Y-%m-%d %H:%M:%S", date)))
        return out
    finally:
        if useDb:
            cursor.close()

def _zap2it_start_over(jar, zipCode, provider):
    cookie = _zap2it_get_cookie(jar, "zap_oatmeal")
    if cookie is None:
        return True
    code = _zap2it_get_crumb(cookie, "postalcode")
    if (code is None) or (code != zipCode):
        return True
    cookie = _zap2it_get_cookie(jar, "tvqpremium")
    if (cookie is None) or (-1 == cookie.value.find(str(provider))):
        return True
    return False

def _zap2it_retrieve_grid(jar, zipCode, provider):
    response, opener = None, None
    if  _zap2it_start_over(jar, zipCode, provider):
        response, opener = _zap2it_get_providers_stage(jar, zipCode)
        try:
            formData = {
                "provider": str(provider),
                "saveProvider": "See Listings",
                "zipcode": zipCode,
                "FormName": "system.asp",
                "page_from": ""
            }
            encData = urllib.urlencode(formData)
            providers = _zap2it_parse_providers(response.read())
        finally:
            response.close()

        providerName = providers[provider]
        _zap2it_set_tvheadend(jar, providerName)
        url = _g_zap2it_provider_url % urllib.quote(zipCode)
        request = urllib2.Request(url, encData)
        request.add_header("Referer", url)
        response = opener.open(request)
    else:
        opener = _zap2it_opener(jar)
        request = urllib2.Request(_g_zap2it_grid_url)
        response = opener.open(request)

    _zap2it_tracker(jar)
    return response, opener

def _zap2it_parse_stations(htmlText):
    soup = BeautifulSoup.BeautifulSoup()
    soup.feed(htmlText)
    select = soup.first("select", {"name": "station"})
    options = select.fetch("option")
    out = {}
    for option in options:
        stationId = int(str(option["value"]).strip())
        if 0 == stationId:
            continue
        stationName = convertEntities(str(option.contents[0])).strip()
        out[stationId] = stationName
    return out

def _zap2it_retrieve_stations(jar, zipCode, provider):
    response, opener = _zap2it_retrieve_grid(jar, zipCode, provider)
    htmlText = ""
    try:
        htmlText = response.read()
    finally:
        response.close()
    return _zap2it_parse_stations(htmlText)

_g_zap2it_one_station_listing_url = "http://tvlistings.zap2it.com/text_one.asp?station_num=%d&partner_id=national"

def _zap2it_retrieve_providers(jar, zipCode):
    response, opener = _zap2it_get_providers_stage(jar, zipCode)
    providers = None
    try:
        htmlText = response.read()
        try:
            providers = _zap2it_parse_providers(htmlText)
        except Exception, ex:
            logParsingFailure(Fields.getTvListingsProviders, zipCode, 'zap2it_providers', htmlText)
            return None
    finally:
        response.close()
    return providers


_g_zap2it_cache_manager = None

def _zap2it_retriever_key(provider, date):
    return str(provider) + "|" + time.strftime("%Y-%m-%d", date) + "|" + str(date.tm_hour)

HOURS_RETRIEVED_IN_ONE_STEP = 3

def _escape_record(rec):
    out = []
    import time
    for item in rec:
        if item is None:
            out.append('')
        elif isinstance(item, time.struct_time):
            out.append(time.strftime('%Y%m%dT%H%M%s', item))
        else:
            out.append(str(item))
    return out

class _Zap2ItRetriever:

    # note: date should contain local time, not UTC!
    def __init__(self, conn, jar, zipCode):
        self._conn = conn
        self._jar = jar
        self._zipCode = zipCode
        self._provider = None
        self._date = None
        self._events = {}
        self._has_grid = False

    def setProvider(self, provider):
        self._provider = provider

    def setDate(self, date):
        self._date = date

    def retrieveProviders(self):
        providers = _zap2it_retrieve_providers(self._jar, self._zipCode)
        if providers is None:
            return UNKNOWN_FORMAT, None
        out = []
        cursor = self._conn.cursor()
        try:
            for provider in providers.iteritems():
                id, name = provider
                out.append([str(id), name])
                name = self._conn.string_literal(name)
                try:
                    cursor.execute("INSERT INTO zap2it_providers (id, name) VALUES (%d, %s)" %
                                   (id, name))
                except IntegrityError:
                    pass
        finally:
            cursor.close()
        return TVLISTINGS_PROVIDERS, universalDataFormat(out)

    def retrieveStations(self):
        _zap2it_retrieve_stations(self._jar, self._zipCode, self._provider)

    def _retrieveHours(self, hours, fast):
        cursor = self._conn.cursor()
        try:
            start = time.mktime((self._date.tm_year, self._date.tm_mon, self._date.tm_mday, 0 , 0, 0, -1, -1, -1))
            end = start + 3600 * 24
            cursor.execute("SELECT date FROM zap2it_cached_data WHERE provider_id = %d AND date >= '%s' AND date < '%s'" %
                           (self._provider, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start)), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end))))
            for row in cursor:
                h = row[0].timetuple()[3]
                hours.remove(h)
        finally:
            cursor.close()

        # if all data is cached, return None and use _retrieveFromDatabase() instead
        if 0 == len(hours):
            return None;

        opener = None
        if not self._has_grid:
            response, opener = _zap2it_retrieve_grid(self._jar, self._zipCode, self._provider)
            self._has_grid = True
            response.close()
        else:
            opener = opener = _zap2it_opener(self._jar)

        if not fast:
            for h in hours:
                self._events[h] = threading.Event()
                date = time.localtime(time.mktime((self._date.tm_year, self._date.tm_mon, self._date.tm_mday, h , 0, 0, -1, -1, -1)))
                _g_zap2it_cache_manager._addActiveRetriever(_zap2it_retriever_key(self._provider, date), self)

        rows = 0
        duration = 1
        if fast:
            rows = 20
            duration = 3
            hours = [hours[0]]

        out = []

        formData = {
            "displayType": "Text",
            "duration": str(duration),
            "startDay": time.strftime("%m/%d/%Y", self._date),
            "category": "0",
            "station": "0",
            "rowdisplay": str(rows),
            "goButton": "GO"
        }

        stations = {}
        programs = {}
        for h in hours:
            formData["startTime"] = str(h)
            date = time.localtime(time.mktime((self._date.tm_year, self._date.tm_mon, self._date.tm_mday, h , 0, 0, -1, -1, -1)))
            encData = urllib.urlencode(formData)
            request = urllib2.Request(_g_zap2it_listings_url, encData)
            request.add_header("Referer", _g_zap2it_grid_url)
            response = opener.open(request)
            htmlText = None
            try:
                _zap2it_tracker(self._jar)
                contentLength = long(response.info()["Content-Length"])
                htmlText = response.read(contentLength)
                if fast:
                    out.extend(_zap2it_parse_listings(None, htmlText, date, self._provider, stations, programs))
                else:
                    _zap2it_parse_listings(self._conn,  htmlText, date, self._provider, stations, programs)
            except Exception, ex:
                # todo: log exception
                print exceptionAsStr(ex)
                f = file(time.strftime('tvlistings-%Y%m%dT%H%M%S.html'), 'wb')
                f.write(htmlText)
                f.close()
                pass
            response.close()
            if not fast:
                self._events[h].set()
                _g_zap2it_cache_manager._removeActiveRetriever(_zap2it_retriever_key(self._provider, date))
        return out

    def _retrieveFromDatabase(self):
        h = self._date.tm_hour
        max_h = 24 - HOURS_RETRIEVED_IN_ONE_STEP
        if h > max_h:
            h = max_h
        start = time.mktime((self._date.tm_year, self._date.tm_mon, self._date.tm_mday, self._date.tm_hour , 0, 0, -1, -1, -1))
        end = start + 3600 * HOURS_RETRIEVED_IN_ONE_STEP
        # TODO: is there some way to make this db-agnostic?
        out = []
        cursor = self._conn.cursor(SSDictCursor)
        try:
            cursor.execute("""
                SELECT p.zap2it_id, p.title, p.series_id, p.series_volume_title, p.category, p.additional_info, p.description,
                    ss.station_id, ss.time, s.name AS station_name, pl.provider_id, pl.index_in_listing, pr.name AS provider_name
                FROM zap2it_programs AS p, zap2it_stations_schedule AS ss, zap2it_stations AS s, zap2it_providers_listings AS pl,
                    zap2it_providers AS pr
                WHERE p.id = ss.program_id AND ss.station_id = s.id AND s.id = pl.station_id AND pl.provider_id = pr.id AND
                    pr.id = %d AND ss.time >= '%s' AND ss.time < '%s'
                ORDER BY pl.index_in_listing, ss.time
            """ % (self._provider, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start)), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end))))
            while True:
                rows = cursor.fetchmany(100)
                if 0 == len(rows):
                    break
                for row in rows:
                    programId = row['zap2it_id']
                    programTitle = row['title']
                    seriesId = row['series_id']
                    seriesVolumeTitle = row['series_volume_title']
                    category = row['category']
                    additionalInfo = row['additional_info']
                    description = row['description']
                    stationId = row['station_id']
                    broadcastTime = row['time'].timetuple()
                    stationName = row['station_name']
                    stationIndex = row['index_in_listing']
                    record = [stationId, stationName, stationIndex, broadcastTime, programId, programTitle, seriesId, seriesVolumeTitle, category, additionalInfo, description]
                    record = _escape_record(record)
                    out.append(record)
        finally:
            cursor.close()
        return out

    def retrieveListings(self):
        h = self._date.tm_hour
        max_h = 24 - HOURS_RETRIEVED_IN_ONE_STEP
        if h > max_h:
            h = max_h
        for i in range(HOURS_RETRIEVED_IN_ONE_STEP):
            date = time.localtime(time.mktime((self._date.tm_year, self._date.tm_mon, self._date.tm_mday, h , 0, 0, -1, -1, -1)))
            _g_zap2it_cache_manager.finishCaching(self._provider, date)

        hours = range(h, h + HOURS_RETRIEVED_IN_ONE_STEP)
        res = TVLISTINGS_PARTIAL
        out = self._retrieveHours(hours, True)
        if out is None:
            out = self._retrieveFromDatabase()
            res = TVLISTINGS_FULL
        return res, universalDataFormat(out)

    # this is to be called _after_ InfoManServer sends answer to the client - in the callbacks stage
    def retrieveRest(self):
        hours = range(24)
        h = self._date.tm_hour
        if h != 0:
            h1 = hours[:h]
            h0 = hours[h:]
            hours = h0 + h1

        self._retrieveHours(hours, False)

    def _waitUntilFinished(self, hour):
        self._events[hour].wait()

class _Zap2ItCacheManager:

    def __init__(self):
        self._lock = thread.allocate_lock();
        self._retrievers = {}

    def _addActiveRetriever(self, key, retriever):
        self._lock.acquire()
        try:
            self._retrievers[key] = retriever
        finally:
            self._lock.release()

    def _removeActiveRetriever(self, key):
        self._lock.acquire()
        try:
            del self._retrievers[key]
        finally:
            self._lock.release()

    def _retrieverFor(self, provider, date):
        key = _zap2it_retriever_key(provider, date)
        self._lock.acquire()
        try:
            return self._retrievers.get(key, None)
        finally:
            self._lock.release()

    def finishCaching(self, provider, date):
        retriever = self._retrieverFor(provider, date)
        if retriever is not None:
            retriever._waitUntilFinished(date.tm_hour)

    def allocateRetriever(self, conn, jar, zipCode):
        return _Zap2ItRetriever(conn, jar, zipCode)

def getCacheManager():
    global _g_zap2it_cache_manager
    if _g_zap2it_cache_manager is None:
        _g_zap2it_cache_manager = _Zap2ItCacheManager()
    return _g_zap2it_cache_manager


def main():
#    _zap2it_test_listings_parser()
#    return
    import InfoManServer
    conn = InfoManServer.createDatabaseConnection()
    jar = cookielib.CookieJar()
    cacheMgr = getCacheManager()
    retriever = cacheMgr.allocateRetriever(conn, jar, '98101')
    providers = retriever.retrieveProviders()
    for provider in providers.iterkeys():
        print 'Retrieving provider: ', provider,'; time: ', time.strftime('%X')
        retriever.setProvider(provider)
        retriever.setDate(time.gmtime())
        out = retriever.retrieveListings()
        print 'Retrieved; time: ', time.strftime('%X'), '; programs: ', len(out)

if __name__ == "__main__":
    main()
