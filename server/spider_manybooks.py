PROVIDER_ID = "manybooks"

import os.path, urllib, urllib2, ebooks, cPickle, thread, shutil, re, threading
from Retrieve import getHttp

_g_storage = os.path.join(ebooks.g_storage, "manybooks")
_g_spider_data_path = os.path.join(ebooks.g_storage, "manybooks-spider.dat")

# In manybooks-spider.dat file we store data structured like that: {letter: letter_data}
# letter is a single alphabet letter string. letter_data has the following structure:
# (book_count, books_data). books_count is number of books whose title starts with given
# letter. books_data is an array of book_data elements. book_data element is:
# (url, title, subtitle, author, id, language_code, format_descriptions). format_descriptions is an
# array whose elements are pairs (format, identifier). textual "identifiers" of book allowing to download
# it from manybooks site.

try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import Tag
except Exception:
    print "requires BeautifulSoup module from http://www.crummy.com/software/BeautifulSoup/"
    raise

from parserUtils import retrieveContents
from arsutils import exceptionAsStr, log, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC

_g_manybooks_url = "http://www.manybooks.net"
_g_manybooks_titles_url = _g_manybooks_url + "/titles.php?alpha=%s&s=%d"
_g_books_per_page = 20


def _create_spider_data():
    return {}

def _load_spider_data():
    try:
        f = open(_g_spider_data_path, "rb")
        try:
            data = cPickle.load(f)
            return data
        finally:
            f.close()
    except:
        return _create_spider_data()

def _save_spider_data(data):
    dir = os.path.dirname(_g_spider_data_path)
    if not os.path.exists(dir):
        os.makedirs(dir)

    tmp_path = _g_spider_data_path + ".new"
    f = open(tmp_path, "wb")
    try:
        cPickle.dump(data, f, protocol = cPickle.HIGHEST_PROTOCOL)
    finally:
        f.close()
    done = False
    ex = None
    while not done:
        try:
            shutil.copyfile(tmp_path, _g_spider_data_path)
            done = True
        except KeyboardInterrupt, e:
            print "KeyboardInterrupt while copying data, retrying..."
            ex = e
    if ex is not None:
        raise ex

def _transform_author(a):
    if a.lower() in ebooks.g_author_exceptions:
        return a

    aa = a.rsplit(None, 1)
    if len(aa) < 2:
        return a
    return ", ".join((aa[1], aa[0]))

def _spider_book_info(url, letter):
    try:
        html = getHttp(url, handleException = False)
        soup = BeautifulSoup()
        soup.feed(html)
        h1 = soup.first("h1")
        if h1 is None:
            return None

        assert h1 is not None
        title = retrieveContents(h1).decode("iso-8859-1")

        subtitle = None
        author = None
        code = None

        labels = [retrieveContents(x) for x in soup.fetch("span", {"class": "title-label"})]
        data = soup.fetch("span", {"class": "title-data"})
        try:
            index = labels.index("Subtitle")
            subtitle = retrieveContents(data[index]).decode("iso-8859-1")
        except ValueError:
            pass

        try:
            index = labels.index("Author")
            author = retrieveContents(data[index].first("a")).decode("iso-8859-1")
        except ValueError:
            pass

        try:
            index = labels.index("Language")
            href = str(data[index].first("a", {"href": "/language.php?code=%"})["href"])
            code = href[19:href.find("&", 19)].decode("iso-8859-1")
        except ValueError:
            pass

        tid = soup.first("input", {"type": "hidden", "name": "tid"})
        assert tid is not None
        book_id = tid["value"].decode("iso-8859-1")

        print (u"%s: \"%s\"" % (author, title)).encode("iso-8859-1", "ignore")

        sel = soup.first("select", {"name": "book"})
        assert sel is not None
        opts = sel.fetch("option")
        formats = []
        for opt in opts:
            try:
                format = retrieveContents(opt).split()[0]
                if format not in ebooks.FORMATS:
                    continue

                val = opt["value"]
                formats.append((format, val))

            except Exception, ex:
                log(SEV_EXC, exceptionAsStr(ex))
        formats.sort()
        return (url, title, subtitle, author, book_id, code, formats)
    except:
        print "Caught exception at letter %s; url: %s" % (letter, url.encode("iso-8859-1", "ignore"))
        raise

class _StopSpidering(Exception):
    pass

class _SpiderThread(threading.Thread):

    def __init__(self, spider, letters):
        self._spider = spider
        self._letters = letters
        self.count = 0
        self.exception = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.count = self._spider._spider_letter_range(self._letters)
        except _StopSpidering:
            return
        except Exception, ex:
            print exceptionAsStr(ex)
            self._spider._finish.set()

def _find_book_index(books, url, start_index):
    l = len(books)
    while start_index < l:
        book = books[start_index]
        if book[0] == url:
            return start_index
        start_index += 1
    return -1


class _Spider:

    flush_after = 50
    temp_file_pattern = re.compile("manybooks-spider-\d\d\d.tmp")
    letters = "1abcdefghijklmnopqrstuvwxyz"

    def _delete_temps(cls):
        if not os.path.exists(ebooks.g_storage):
            return
        map(os.remove, [os.path.join(ebooks.g_storage, name) for name in os.listdir(ebooks.g_storage) if cls.temp_file_pattern.match(name)])

    def __init__(self, force = False):
        self._lock = thread.allocate_lock()
        self._file_count = 0
        self._offsets = {}
        self._finish = threading.Event()
        for letter in _Spider.letters: self._offsets[letter] = 0
        self._fresh_books = []
        if force:
            self._data = _create_spider_data()
        else:
            self._data = _load_spider_data()
        self._merge_temps()

    def _flush_books(self):
        f = file(os.path.join(ebooks.g_storage, "manybooks-spider-%03d.tmp" % self._file_count), "wb")
        try:
            cPickle.dump(self._fresh_books, f, protocol = cPickle.HIGHEST_PROTOCOL)
            f.close()
            f = None
            self._fresh_books = []
            self._file_count += 1
        finally:
            if f is not None: f.close()

    def _check_finish(self):
        if self._finish.isSet():
            raise _StopSpidering()

    def _parse_letter_page(self, letter, html, index):
        self._check_finish()
        soup = BeautifulSoup()
        soup.feed(html)
        div = soup.first("div", {"class": "sidebar-module"})
        assert div is not None
        count = int(retrieveContents(div.contents[2]).split()[2])
        offset = 0
        self._lock.acquire()
        try:
            if count <= self._data[letter][0]:
                print 'Letter "%s" is up to date (%d records).' % (letter, self._data[letter][0])
                return True, count, 0
            offset = self._offsets[letter]
        finally:
            self._lock.release()

        spidered = 0
        div = soup.first("div", {"class": "titleList"})
        assert div is not None
        as = div.fetch("a")
        urls = []
        for a in as:
            url = _g_manybooks_url + urllib.quote(a["href"])
            urls.append(url)

        for url in urls:
            self._check_finish()
            i = -1
            self._lock.acquire()
            try:
                books = self._data[letter][1]
                i = _find_book_index(books, url, index)
            finally:
                self._lock.release()

            if -1 != i:
                index = i + 1
            else:
                book = _spider_book_info(url, letter)
                if book is not None:
                    spidered += 1
                    self._lock.acquire()
                    try:
                        self._fresh_books.append((letter, index + offset, book))
                        if len(self._fresh_books) == self.flush_after:
                            self._flush_books()
                        offset += 1
                        self._offsets[letter] = offset
                        if self._data[letter][0] + offset  == count:
                            return True, count, spidered
                    finally:
                        self._lock.release()
        return (index + offset == count), index, spidered

    def _spider_letter_page(self, letter, page, index):
        url = _g_manybooks_titles_url % (letter, page)
        html = getHttp(url.encode("iso-8859-1"), handleException = False)
        return self._parse_letter_page(letter, html, index)

    def _spider_letter(self, letter):
        self._lock.acquire()
        try:
            letter_data = self._data.get(letter, None)
            if letter_data is None:
                self._data[letter] = [0, []]
        finally:
            self._lock.release()

        page = 1
        index = 0
        count = 0
        while True:
            self._check_finish()
            done, index, cnt = self._spider_letter_page(letter, page, index)
            count += cnt
            page += 1
            if done:
                break
        if 0 != count:
            print "Spidered %d records for letter '%s'." % (count, letter)
        return count

    def _spider_letter_range(self, letters):
        count = 0
        for letter in letters:
            self._check_finish()
            count += self._spider_letter(letter)
        return count

    def _merge_temps(self):
        if not os.path.exists(ebooks.g_storage):
            return
        temps = [os.path.join(ebooks.g_storage, name) for name in os.listdir(ebooks.g_storage) if self.temp_file_pattern.match(name)]
        if 0 == len(temps):
            return

        print "Merging temporary segments."
        temps.sort()
        try:
            for temp in temps:
                f = file(temp, "rb")
                try:
                    data = cPickle.load(f)
                finally:
                    f.close()
                    os.remove(temp)

                for letter, index, book in data:
                    letter_data = self._data.get(letter, None)
                    if letter_data is None:
                        letter_data = [0, []]
                        self._data[letter] = letter_data

                    assert index <= letter_data[0]
                    letter_data[1].insert(index, book)
                    letter_data[0] += 1
        except Exception, ex:
            print exceptionAsStr(ex)
        _save_spider_data(self._data)

    def spider(self):
        count = 0

        threads = []
        exception = None

        try:
            if True:
                step = 2
                steps = [self.letters[i:i + step] for i in range(0, len(self.letters), step)]
                threads = [_SpiderThread(self, s) for s in steps]
                map(threading.Thread.start, threads)
                for t in threads:
                    t.join()
                    count += t.count
            else:
                count = self._spider_letter_range(self.letters)
        except Exception, ex:
            exception = ex
            self._finish.set()

        if len(self._fresh_books) != 0:
            self._flush_books()

        self._merge_temps()

        for t in threads:
            if t.exception is not None:
                exception = t.exception
                break

        if exception is not None:
            raise exception

        print "Spider finished, %d new records added." % count
        return count

def spider(force = False):
    s = _Spider(force)
    return s.spider()

_g_download_url = "http://manybooks.net/scripts/send.php"


def _download_hook(count, block_size, total):
    if (0 == count):
        print "download started"
        return

    print "%d%%" % ((count * block_size * 100.0)/total);

def download(cache_path, book_id, format, version_id):
    url = _g_manybooks_url + "/titles/" + urllib.quote(book_id.encode("iso-8859-1")) + ".html"

    query = {
        "tid": book_id,
        "book": version_id
    }

    file_name = os.path.join(cache_path, book_id + "-" + format + ".pdb")
    fn, headers = urllib.urlretrieve(_g_download_url, file_name, None, urllib.urlencode(query))

    f = open(fn, "rb")
    return file_name, f

def _decode(str):
    if str is not None:
        if type(str) is unicode:
            return str
        else:
            return str.decode("iso-8859-1")
    else:
        return u""

def spider_last_modified():
    return os.path.getmtime(_g_spider_data_path)

def reindex(index, data = None):
    data = _load_spider_data()

    for letter, letter_data in data.iteritems():
        print "Indexing %d books for letter '%s'." % (letter_data[0], letter)
        for book in letter_data[1]:
            url, title, subtitle, author, book_id, code, formats = book
            title = _decode(title)
            subtitle = _decode(subtitle)
            author = _transform_author(_decode(author))
            book_id = _decode(book_id)
            code = _decode(code)
            formats.sort()
            index.index_ebook(title, subtitle, author, book_id, formats, PROVIDER_ID, code)

try:
    import psyco
    psyco.bind(_Spider._merge_temps)
    psyco.bind(_Spider._spider_letter_range)
except Exception, ex:
    print exceptionAsStr(ex)
except ImportError:
    print "psyco not available. You should consider using it (http://psyco.sourceforge.net/)"

if __name__ == "__main__":
    spider()
