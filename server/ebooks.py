# -*- coding: latin-1 -*-

try:
    from lupy.indexer import Index as LupyIndex
    from lupy.search.indexsearcher import IndexSearcher
    from lupy.index.term import Term
    from lupy.search.term import TermQuery
    from lupy.search.phrase import PhraseQuery
    from lupy.search.boolean import BooleanQuery
except:
    print "requires Lupy module from http://www.divmod.org/Home/Projects/Lupy/"
    raise

import thread, os, os.path, cPickle, re, sys, math, base64, string
from binascii import hexlify, unhexlify

import popupMenu, encyclopedia, definitionBuilder, multiUserSupport
from arsutils import exceptionAsStr, log, SEV_LOW, SEV_MED, SEV_HI, SEV_EXC, fDetectRemoveCmdFlag, getRemoveCmdArg, fDirExists, numPretty


FORMAT_DOC = "Doc"
# FORMAT_PDF = "PDF"
FORMAT_EREADER = "eReader"
FORMAT_PLUCKER = "Plucker"
FORMAT_ZTXT = "zTXT"
FORMAT_ISILO = "iSilo"
FORMAT_ISILOX = "iSiloX"

FORMATS = [
    FORMAT_DOC,
#    FORMAT_PDF,
    FORMAT_EREADER,
    FORMAT_PLUCKER,
    FORMAT_ZTXT,
    FORMAT_ISILO,
    FORMAT_ISILOX
]

FORMATS_ALL = "*"

SEARCH_ANY = "any"
SEARCH_AUTHOR = "author"
SEARCH_TITLE = "title"

SEARCH_TYPES = [
    SEARCH_ANY,
    SEARCH_AUTHOR,
    SEARCH_TITLE
]

BROWSE_AUTHOR = SEARCH_AUTHOR
BROWSE_TITLE = SEARCH_TITLE
BROWSE_TYPES = [
    BROWSE_AUTHOR,
    BROWSE_TITLE
]

g_author_exceptions = [
    "various authors",
]

g_title_prefixes = [
    "the",
    "a",
    "an",
]

g_storage = os.path.join(multiUserSupport.getServerStorageDir(), "ebooks")
_g_index_path = os.path.join(g_storage, "index")
_g_new_index_path = os.path.join(g_storage, "index-new")

_g_database = os.path.join(g_storage, "database")
_g_new_database = os.path.join(g_storage, "database-new")

_g_version_path = os.path.join(g_storage, "version.txt")

_g_id_mappings_file_name = "id-mappings.dat"

_g_spiders = [
    "spider_manybooks",
]

_g_spider_modules = None

# make sure that directory for ebooks data exists
def ensureEbooksDir():
    global g_storage
    if not os.path.exists(g_storage):
        os.makedirs(g_storage)
        print "created dir %s" % g_storage

def _spider_modules():
    global _g_spider_modules
    if _g_spider_modules == None:
        _g_spider_modules = dict()
        for spider in _g_spiders:
            module = __import__(spider)
            provider_id = module.PROVIDER_ID
            _g_spider_modules[provider_id] = module
    return _g_spider_modules

def _downloader_for(provider_id):
    mods = _spider_modules()
    mod = mods[provider_id]
    return mod.download

def spider_all(recreate = False):
    ensureEbooksDir()
    mods = _spider_modules()
    count = 0
    for id, mod in mods.iteritems():
        print "Running spider for provider \"%s\"." % id
        count += mod.spider(force = recreate)
    return count

def _next_backup_index(path, pattern):
    index = -1
    for name in os.listdir(path):
        if not os.path.isdir(os.path.join(path, name)):
            continue
        m = pattern.match(name)
        if m is None:
            continue
        num = long(m.group(1), 10)
        if num > index:
            index = num
    return index + 1

_g_index_re = re.compile("index-old-(\\d\\d\\d)")
def _backup_index():
    if not os.path.exists(_g_index_path):
        return
    index = _next_backup_index(g_storage, _g_index_re)
    new_dir = "index-old-%03d" % index
    os.rename(_g_index_path, os.path.join(g_storage, new_dir))

def reindex_all(update_old = False, only_database = False):
    mods = _spider_modules()
    index = Index(update_old, only_database)
    for id, mod in mods.iteritems():
        print "Indexing data from provider \"%s\"." % id
        mod.reindex(index)
    print "Indexing finished, optimizing index."
    index.finish_indexing()

def _index_last_modified():
    return max([os.path.getmtime(os.path.join(_g_index_path, n)) for n in os.listdir(_g_index_path)])

def _spiders_data_last_modified():
    return max([m.spider_last_modified() for m in _spider_modules().itervalues()])
    
def update_all(force = False, force_index_update = False, update_old_index = False):
    ensureEbooksDir()
    count = spider_all(force)
    if force_index_update or (0 != count) or (not os.path.exists(_g_index_path)) or  (_spiders_data_last_modified() > _index_last_modified()):
        reindex_all(update_old_index)
    return count

_g_digit = "#"
_g_letters = _g_digit + "abcdefghijklmnopqrstuvwxyz"
_g_level_count = 4
_g_top_level_partition_count = 5
_g_books_per_leaf = 20
_g_max_label_length = 80
# _g_nodes_per_page = 10


def _alnum_key(s):
    return ("".join([c for c in s.lower() if c.isalnum() or c == ' '])).strip()
    

def _preprocess_label(s, si):
    ss = [x.strip(",.():;").title() for x in s[: si + 1].split()]
    l = 0
    for i in range(0, len(ss)):
        l += len(ss[i])
        if l > 3:
            break
    
    s = " ".join(ss[: i + 1])
    return s

def _diffs(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()
    s1i = 0
    s2i = 0
    while s1i < len(s1) and s2i < len(s2):
        c1 = s1[s1i]
        c2 = s2[s2i]
        if (c1.isalnum() or c1 == ' ') and (c2.isalnum() or c2 == ' '):
            if c1 != c2: break
            else:
               s1i += 1
               s2i += 1
        else:
            if not (c1.isalnum() or c1 == ' '):
               s1i += 1
            if not (c2.isalnum() or c2 == ' '):
               s2i += 1

    return _preprocess_label(s1, s1i), _preprocess_label(s2, s2i)
    
def _letter_for(s):
    s = _alnum_key(s)
    if 0 == len(s):
        return _g_digit

    c = s[0]
    if c.isdigit():
        return _g_digit
    return c

def _dump_leaf(field_name, data, leaf_index):
    f = file(os.path.join(_g_new_database, "%s-%04d.dat" % (field_name, leaf_index)), "wb")
    try:
        cPickle.dump(data, f, protocol = cPickle.HIGHEST_PROTOCOL)
    finally:
        f.close()

def _partition_by_field(data, field_index, field_name):
    field_key = lambda x: _alnum_key(x[field_index])
    data.sort(key = field_key)
    letter_counts = {}
    leaf = []
    leaf_index = 0
    for book in data:
        value = book[field_index]
        l = _letter_for(value)
        letter_counts[l] = letter_counts.get(l, 0) + 1
        leaf.append(book)
        if _g_books_per_leaf == len(leaf):
            _dump_leaf(field_name, leaf, leaf_index)
            leaf = []
            leaf_index += 1
    if 0 != len(leaf):
        _dump_leaf(field_name, leaf, leaf_index)
    print "Created %d \"%s\" leafs." % (leaf_index, field_name)
    
    node_powers = [_g_books_per_leaf]
    power = _g_books_per_leaf
    for i in range(0, _g_level_count - 2):
        x = int(math.ceil(math.pow(float(len(data)) / (power * _g_top_level_partition_count), 1.0 / (_g_level_count - 2 - i))))
        node_powers.append(x)
        power *= x
    node_powers.append(_g_top_level_partition_count)
        
    partition_len = float(len(data)) / _g_top_level_partition_count
    partitions = []
    partition_size = 0
    last_partition_boundary = 0
    for i in range(0, len(_g_letters)):
        l = _g_letters[i]
        new_partition_size = partition_size + letter_counts.get(l, 0)
        if last_partition_boundary + new_partition_size >= (len(partitions) + 1) * partition_len:
            boundary = (len(partitions) + 1) * partition_len
            if 0 != partition_size and abs(partition_size - boundary + last_partition_boundary) < abs(new_partition_size - boundary + last_partition_boundary):
                partitions.append((i - 1, partition_size))
                last_partition_boundary += partition_size
                partition_size = new_partition_size - partition_size
            else:
                partitions.append((i, new_partition_size))
                last_partition_boundary += new_partition_size
                partition_size = 0
            continue
        partition_size = new_partition_size
    if 0 != partition_size:
        partitions.append((len(_g_letters) - 1, len(data) - last_partition_boundary))
    partition_levels = []
    power = 1
    for i in range(0, _g_level_count - 2):
        start_label = None
        power *= node_powers[i]
        level = []
        partition_levels.append(level)
        for x in range(0, int(math.ceil(float(len(data)) / power))):
            start_index = x * power
            end_index = min((x + 1) * power, len(data))
            first_book = data[start_index]
            last_book = data[end_index - 1]
            if start_label is None:
                start_label = "#" # _alnum_key(first_book[field_index])[0].title()
            if end_index == len(data):
                next_label = _alnum_key(last_book[field_index])[0].title()
            else:
                next_label, end_label = _diffs(last_book[field_index], data[end_index][field_index])
            print "Creating level %d partition: \"%s\" - \"%s\"." % (i, start_label.encode("latin-1", "ignore"), next_label.encode("latin-1", "ignore"))
            book = (start_label, next_label, start_index, end_index)
            level.append(book)
            start_label = end_label
    start_index = 0
    level = []
    partition_levels.append(level)
    start_label = _g_letters[0].upper()
    for partition in partitions:
        end_label = _g_letters[partition[0]].upper()
        print "Creating level %d partition: \"%s\" - \"%s\"." % (_g_level_count - 2, start_label.encode("latin-1", "ignore"), end_label.encode("latin-1", "ignore"))
        level.append((start_label, end_label, start_index, start_index + partition[1]))
        if len(_g_letters) != partition[0] + 1:
            start_label = _g_letters[partition[0] + 1].upper()
        start_index += partition[1]
    partition_levels.reverse()
    f = file(os.path.join(_g_new_database, "%s-levels.dat" % field_name), "wb")
    try:
        cPickle.dump(partition_levels, f, protocol = cPickle.HIGHEST_PROTOCOL)
    finally:
        f.close()

def _store_provider_id_mappings(data):
    l = len(data)
    i = 0
    d = {}
    while i < l:
        provider, id = data[i][3], data[i][4]
        key = "; ".join((provider, id))
        d[key] = i        
        i += 1
    f = file(os.path.join(_g_new_database, _g_id_mappings_file_name), "wb")
    try:
        cPickle.dump(d, f, protocol = cPickle.HIGHEST_PROTOCOL)
    finally:
        f.close()

def _partition_data(data):
    print "Partitioning book database (%d books)." % len(data)
    _partition_by_field(data, 0, "title")
    _partition_by_field(data, 2, "author")
    _store_provider_id_mappings(data)

_g_database_re = re.compile("database-old-(\\d\\d\\d)")
def _backup_database():
    if not os.path.exists(_g_database):
        return
    new_dir = "database-old-%03d" % _next_backup_index(g_storage, _g_database_re)
    os.rename(_g_database, os.path.join(g_storage, new_dir))

def _prepare_database(data):
    if os.path.exists(_g_new_database):
        map(os.remove, [os.path.join(_g_new_database, f) for f in os.listdir(_g_new_database)])
    else:
        os.makedirs(_g_new_database)

    _partition_data(data)
    _backup_database()
    os.rename(_g_new_database, _g_database)

def _bump_version():
    version = database_version() + 1
    f = file(_g_version_path, "w")
    try:
        f.write(str(version))
        f.truncate()
    finally:
        f.close()

def database_version():
    if not os.path.exists(_g_version_path):
        return 0

    f = file(_g_version_path, "r")
    try:
        s = f.read()
        if 0 == len(s):
            version = 0
        else:
            version = long(s, 10)
        return version
    finally:
        f.close()

class Index:

    def __init__(self, update_old = False, only_database = False):
        self._lock = thread.allocate_lock()
        self._index = None
        self._update_old = update_old
        self._only_database = only_database
        self._data = []

    def _get_index(self):
        if self._index is None:
            if self._update_old:
                self._index = LupyIndex(_g_index_path, False)
            else:
                self._index = LupyIndex(_g_new_index_path, True)
        return self._index

    # adds book to index.
    # @param format_ids is a list of pairs (format_id (one of FORMAT_XXXX values), version_id)
    # version id should contain information for spider module how to retrieve this version. 
    def index_ebook(self, title, subtitle, author, book_id, format_ids, provider, language):
        if language is None:
            language = ""

        if -1 != title.find(" "):
            tt = title.split(None, 1)
            if 1 != len(tt) and tt[0].lower() in g_title_prefixes:
                title = ", ".join((tt[1], tt[0]))
    
        format_ids.sort()
        formats = "; ".join(["%s: %s" % (format, base64.urlsafe_b64encode(version_id)) for format, version_id in format_ids])
        self._lock.acquire()
        try:
            if not self._only_database:
                self._get_index().index(__title = title, __subtitle = subtitle, __author = author, _provider = provider,  _book_id = book_id, __formats = formats, _language = language)
            self._data.append((title, subtitle, author, provider, book_id, formats, language))
        finally:
            self._lock.release()

    
    def finish_indexing(self):
        self._lock.acquire()
        try:
            if not self._only_database:
                index = self._get_index()
                index.flush()
                index.optimize()
                index.close()
                del self._index
                if not self._update_old:
                    _backup_index()
                    os.rename(_g_new_index_path, _g_index_path)
            _prepare_database(self._data)
            del self._data
            _bump_version()
        finally:
            self._lock.release()

try:
    import psyco
    psyco.bind(Index.finish_indexing)
    psyco.bind(Index.index_ebook)
except Exception, ex:
    print exceptionAsStr(ex)
except ImportError:
    print "psyco not available. You should consider using it (http://psyco.sourceforge.net/)"

_g_cache_file_name= os.path.join(g_storage, "pdb-cache.dat")
_g_cache_path = os.path.join(g_storage, "pdb-cache")

class _DownloadCache:

    def __init__(self):
        self._lock = thread.allocate_lock()
        try:
            f = file(_g_cache_file_name, "rb")
            try:
                self._cache = cPickle.load(f)
            finally:
                f.close()
        except:
            self._cache = {}

    def _pickle_out(self):
        dir = os.path.dirname(_g_cache_file_name)
        if not os.path.exists(dir):
            os.makedirs(dir)
        f = file(_g_cache_file_name, "wb")
        try:
            cPickle.dump(self._cache, f, protocol = cPickle.HIGHEST_PROTOCOL)
        finally:
            f.close()

    def add(self, book_id, file_name):
        self._lock.acquire()
        try:
            cached_name = self._cache.get(book_id, None)
            if cached_name is not None:
                if cached_name == file_name:
                    return
                else:
                    self._cache[book_id] = file_name
                    self._pickle_out()
                    try:
                        os.remove(cached_name)
                    except Exception, ex:
                        log(SEV_EXC, exceptionAsStr(ex))
            else:
                self._cache[book_id] = file_name
                self._pickle_out()
        finally:
            self._lock.release()

    def find(self, book_id):
        self._lock.acquire()
        file_name = None
        try:
            file_name = self._cache.get(book_id, None)
            if file_name is None:
                self._lock.release()
                return None;
            f = file(file_name, "rb")
            self._lock.release()
            return f
        except Exception, ex:
            log(SEV_EXC, exceptionAsStr(ex))
            if file_name is not None:
                try:
                    os.remove(file_name)
                except Exception, ex1:
                    log(SEV_EXC, exceptionAsStr(ex1))
                    pass
            del self._cache[book_id]
            self._lock.release()
            return None

_g_cache = _DownloadCache()

_g_valid_chars = {
    "$": True, "%": True, "‘": True, "-": True, "_": True, "@": True, "~": True, "‘": True, "!": True, "(": True, ")": True, "^": True, "#": True, "&": True
}

def _extract_db_name(f, format):
    data = f.read()
    f.close()

    ll = len(data)
    name = data[:32]
    pos = name.find('\0')
    if -1 != pos:
        name = name[:pos]

    n = []
    for letter in name:
        if letter.isalnum() or ' ' == letter or _g_valid_chars.get(letter, False):
            n.append(letter)
     
    name = "".join(n).strip()
    l = len(format) + 1
    if len(name) + l > 31:
        name = name[:31 - l]
    name += "-" + format

    n = name
    while len(n) < 32:
        n += '\0'
    
    data = n + data[32:]
    assert len(data) == ll
    return name, data

# @return tuple (db_name, file, author, title); file is open file objec
def download(book_id):

    if not os.path.exists(_g_cache_path):
        os.makedirs(_g_cache_path)

    provider, id, version_mapping = [s.strip() for s in unhexlify(book_id).split(";", 2)]
    format, version_id = [s.strip() for s in version_mapping.split(":", 1)]

    doc = _find_book_by_id(provider, id)
    title, author = _reverse_title(doc[0]).encode("latin-1", "ignore"), _reverse_author(doc[2]).encode("latin-1", "ignore")
        
    f = _g_cache.find(book_id)
    if f is not None:
        print unhexlify(book_id), "read from cache"
        name, data = _extract_db_name(f, format)
        return name, data, author, title

    downloader = _downloader_for(provider)
    file_name, f = downloader(_g_cache_path, id, format, base64.urlsafe_b64decode(version_id))

    _g_cache.add(book_id, file_name)
    name, data = _extract_db_name(f, format)
    return name, data, author, title

# def _phrase_query(field, phrase):
#     q = PhraseQuery()
#     p = phrase.split()
#     for pp in p:
#         t = Term(field, pp.lower())
#         q.add(t)
#     return q
    
def _phrase_query(field, phrase):
    q = BooleanQuery()
    for p in phrase.split():
        t = Term(field, p.lower())
        q.add(TermQuery(t), required = True, prohibited = False)
    return q

def _base_query(phrase):
    q = BooleanQuery()
    p1 = _phrase_query("author", phrase)
    p2 = _phrase_query("title", phrase)
    #p2.setBoost(2)
    q.add(p2, required = False, prohibited = False)
    q.add(p1, required = False, prohibited = False)
    return q

def _formats_query(main_query, formats):
    if formats is None:
        return main_query

    q = BooleanQuery()
    fq = BooleanQuery()
    for f in formats:
        t = Term("formats", f.lower())
        tq = TermQuery(t)
        fq.add(tq, required = False, prohibited = False)

    q.add(fq, required = True, prohibited = False)
    q.add(main_query, required = True, prohibited = False)
    return q

def _search(query):
    searcher = IndexSearcher(_g_index_path)
    docs = searcher.search(query)
    return docs

def _find_by_author(author, formats):
    return _search(_formats_query(_phrase_query("author", author), formats))

def _find_by_title(title, formats):
    return _search(_formats_query(_phrase_query("title", title), formats))

def _find(phrase, formats):
    return _search(_formats_query(_base_query(phrase), formats))

def _parse_formats(formats):
    f = []
    for version_mapping in formats.split(";"):
        format, version_id = [s.strip() for s in version_mapping.split(":", 1)]
        f.append((format, version_id))
    f.sort()
    return f

def _doc_to_tuple(doc):
    author = doc.get("author").encode("latin-1", "ignore")
    title = doc.get("title").encode("latin-1", "ignore")
    subtitle = doc.get("subtitle").encode("latin-1", "ignore")
    provider = doc.get("provider").encode("latin-1")
    book_id = doc.get("book_id").encode("latin-1")
    formats = doc.get("formats").encode("latin-1")
    f = _parse_formats(formats)
    lang =  doc.get("language").encode("latin-1")
    return (title, subtitle, author, provider, book_id, f, lang)

def _docs_to_tuples(docs):
    return [_doc_to_tuple(doc) for doc in docs]

def _find_book_by_id(provider, book_id):
    f = file(os.path.join(_g_database, _g_id_mappings_file_name), "rb")
    try:  
        d = cPickle.load(f)
    finally:
        f.close()
    key = "; ".join((provider, book_id))
    index = d[key]
    db = index / _g_books_per_leaf
    f = file(os.path.join(_g_database, "author-%04d.dat" % db), "rb")
    try:
        d = cPickle.load(f)
    finally:
        f.close()
    index -= db * _g_books_per_leaf
    doc = d[index]
    return doc

def _download_link(provider, id, format, version_id):
    return "eBook: download: %s" % hexlify("%s;%s;%s:%s" % (provider, id, format, version_id))

def _append_format_links(df, provider, book_id, formats, requested_formats):
    first = True
    for format, version_id in formats:
        if format not in requested_formats:
            continue
        
        if not first:
            df.TextElement(" ")
        else:
            first = False
        df.TextElement(format, link = _download_link(provider, book_id, format, version_id))

def create_search_author_link(author):
    return "eBook: search: %s: %s" % (SEARCH_AUTHOR, author)

def create_search_title_link(title):
    return "eBook: search: %s: %s" % (SEARCH_TITLE, title)

def _author_link(author, modulesInfo):
    items = [
        ("eBooks by %s" % author, create_search_author_link(author), False, True, False)
    ]
    if modulesInfo["Encyclopedia"]:
        items.append(("Search in Encyclopedia", encyclopedia.create_search_link(author), False, False, False))
    if modulesInfo["Amazon"]:
        items.append(("Search in Amazon", "s+amazonsearch:Books;;1;%s" % author, False, False, False))
    return popupMenu.buildPopupMenu(items)

def _title_link(title, modulesInfo):
    items = []
    if modulesInfo["Encyclopedia"]:
        items.append(("Search in Encyclopedia", encyclopedia.create_search_link(title), False, False, False))
    if modulesInfo["Amazon"]:
        items.append(("Search in Amazon", "s+amazonsearch:Books;;1;%s" % title, False, False, False))

    if 0 != len(items):
        return popupMenu.buildPopupMenu(items)
    return None

def _reverse_title(title):
    t = title.split()
    if 1 == len(t):
        return title
    
    if t[-1].lower() in g_title_prefixes:
        prev = t[-2]
        if ',' == prev[-1]:
            t[-2] = prev[:-1]
            return " ".join((t[-1], " ".join(t[:-1])))
  
    return title

def _reverse_author(author):
    a = author.split()

    if len(a) == 1:
        return author
    
    f = a[0]
    if ',' == f[-1]:
        return " ".join((" ".join(a[1:]), f[:-1]))
    return author

def _download_popup(provider, book_id, formats, requested_formats):
    items = [("Download in:", "", True, False, False)]
    for format, version_id in formats:
        if format not in requested_formats: continue
        link = _download_link(provider, book_id, format, version_id)
        items.append(("  %s format" % format, link, False, False, False))
    if len(items) == 1:
        return None
    return popupMenu.buildPopupMenu(items)

def _append_doc_to_def(df, doc, requested_formats, modulesInfo, type):
    first, sec = None, None
    title, subtitle, author, provider, book_id, formats, lang = doc

    title = _reverse_title(title)
    author = _reverse_author(author)

    df.BulletElement(False)
    auth_link = _author_link(author, modulesInfo)
    title_link = _title_link(title, modulesInfo)
    
    df.TextElement(title, link = title_link).setStyle("bold")
    df.TextElement(" by ")
    df.TextElement(author, link = auth_link)

    if 0 != len(requested_formats):
        lnk = _download_popup(provider, book_id, formats, requested_formats)
        if lnk is not None:
            df.TextElement(" (")
            df.TextElement("download", link = lnk)
            df.TextElement(")")

    df.PopParentElement()

def _results_definition(phrase, docs, requested_formats, modulesInfo, type):
    if 0 == len(docs):
        return None

    df = definitionBuilder.Definition()
    _home_link(df)
    _sl(df)

    txt = None
    if SEARCH_AUTHOR == type:
        txt = "Search results for books of authors containing '%s'" % phrase
    elif SEARCH_TITLE == type:
        txt = "Search results for books with titles containing '%s'" % phrase
    else:
        txt = "Search results for '%s'" % phrase
        
    df.TextElement(txt)
    df.setTitle(txt)

    df.LineBreakElement()

    docs = _docs_to_tuples(docs)
    docs.sort()

    for doc in docs:
        _append_doc_to_def(df, doc, requested_formats, modulesInfo, type)

    return df.serialize()

# def find_by_author(author, formats, modulesInfo):
#     f = None
#     if "*" != formats:
#         f = formats
#     docs = _find_by_author(author, f)
#     return _results_definition(author, docs, True, formats, modulesInfo)

# def find_by_title(title, formats, modulesInfo):
#     f = None
#     if "*" != formats:
#         f = formats
#     docs = _find_by_title(title, f)
#     return _results_definition(title, docs, False, formats, modulesInfo)

def _preprocess_phrase(phrase):
    p = [x.strip(".,;()") for x in phrase.split()]
    p = [x for x in p if len(x) > 1]
    return " ".join(p)

def _find_proxy(phrase, formats, type):
    f = FORMATS
    if FORMATS_ALL != formats:
        f = [s.strip() for s in formats.split()]

    if type == SEARCH_AUTHOR:
        docs = _find_by_author(phrase, f)
    elif type == SEARCH_TITLE:
        docs = _find_by_title(phrase, f)
    else:
        docs = _find(phrase, f)
    return docs

def find(phrase, formats, modulesInfo, type = SEARCH_ANY):
    p = _preprocess_phrase(phrase)
    docs = _find_proxy(p, formats, type)
    return _results_definition(phrase, docs, formats, modulesInfo, type)

def data_ready():
    if not os.path.exists(_g_index_path): return False
    if not os.path.exists(_g_database): return False
    return True

def _levels_for(type):
    f = file(os.path.join(_g_database, "%s-levels.dat" % type), "rb")
    try:
        return cPickle.load(f)
    finally:
        f.close()

def _leaf_for(type, index):
    f = file(os.path.join(_g_database, "%s-%04d.dat" % (type, index)), "rb")
    try:
        return cPickle.load(f)
    finally:
        f.close()

def _level_link(type, levels, level, index):
    link = "eBook: browse: %s; %d; %d" % (type, level, index)
    l = levels[level][index]
    start_label, end_label = l[0], l[1]
    label = "%s - %s" % (start_label.encode("latin-1", "ignore"), end_label.encode("latin-1", "ignore"))
    return link, label

def _dot(df):
    return df.TextElement(" \x95 ")

def _sl(df):
    return df.TextElement(" / ")
        
def _start_page():
    title_levels = _levels_for(BROWSE_TITLE)
    author_levels = _levels_for(BROWSE_AUTHOR)
    total_books = title_levels[0][len(title_levels[0]) - 1][3]

    df = definitionBuilder.Definition()
    df.setTitle("eBooks - Home")
    df.TextElement("%s eBooks available. " % numPretty(total_books))
    df.TextElement("Search", link = "eBook:search")
    df.TextElement(" or browse ")
    df.TextElement("by author", link = "eBook: browse: %s" % (BROWSE_AUTHOR))
    df.TextElement(" or ")
    df.TextElement("by title", link = "eBook: browse: %s" % (BROWSE_TITLE))
    df.TextElement(".")
    df.LineBreakElement()
    df.LineBreakElement(1, 5).setJustification(definitionBuilder.justCenter)
    
    df.TextElement("Browse by author").setJustification(definitionBuilder.justCenter)
    df.LineBreakElement().setJustification(definitionBuilder.justCenter)
    for i in range(0, len(author_levels[0])):
        lnk, label = _level_link(BROWSE_AUTHOR, author_levels, 0, i)
        df.TextElement(label, link = lnk).setJustification(definitionBuilder.justCenter)
        if i != len(author_levels[0]) - 1:
            _dot(df).setJustification(definitionBuilder.justCenter)

    df.LineBreakElement().setJustification(definitionBuilder.justCenter)
    df.LineBreakElement(1, 5).setJustification(definitionBuilder.justCenter)

    df.TextElement("Browse by title").setJustification(definitionBuilder.justCenter)
    df.LineBreakElement().setJustification(definitionBuilder.justCenter)
    for i in range(0, len(title_levels[0])):
        lnk, label = _level_link(BROWSE_TITLE, title_levels, 0, i)
        df.TextElement(label, link = lnk).setJustification(definitionBuilder.justCenter)
        if i != len(title_levels[0]) - 1:
            _dot(df).setJustification(definitionBuilder.justCenter)
    
    df.LineBreakElement().setJustification(definitionBuilder.justCenter)
    df.LineBreakElement(1, 5)
    
    df.TextElement("Manage ")
    df.TextElement("downloaded books", link = "eBook: manage")
    df.TextElement(".")
    return df.serialize()

def _home_link(df):
    return df.TextElement("Home", link = "s+eBook-home:")


def _leaf(df, leaf, type, moduleInfo, requested_formats):
    for doc in leaf:
        (title, subtitle, author, provider, book_id, formats, language) = doc
        f = _parse_formats(formats)
        _append_doc_to_def(df, (title.encode("latin-1", "ignore"), subtitle.encode("latin-1", "ignore"), author.encode("latin-1", "ignore"), provider.encode("latin-1", "ignore"), book_id.encode("latin-1", "ignore"), f, language.encode("latin-1", "ignore")), requested_formats, moduleInfo, type)



def _navigation_path(df, type, levels, level, index):
    _home_link(df)

    if level is None:
        txt = "Browse by %s (%s books)" % (type, numPretty(levels[0][-1][3]))
        lnk = None
    else:
        txt = "Browse by %s" % type
        lnk = "eBook: browse: %s" % type
        
    _sl(df)
    df.TextElement(txt, link = lnk)
    if level is None: 
        return

    if level > 0:
        sl = levels[level][index][0][0].upper()
        # el = levels[level][index][1][0].upper()
        zi = 0
        for l in levels[0]:
            if sl >= l[0] and sl <= l[1]:
                zi = levels[0].index(l)
    else:
        zi = index
    
    i = level
    indexes = []
    while i >= 0:
        if i == level:
            indexes.append(index)
        elif i > 0:
            ind = (indexes[-1] * levels[i + 1][0][3]) / levels[i][0][3]
            indexes.append(ind)
        elif 0 == i:
            indexes.append(zi)
        i -= 1
    
    indexes.reverse()
    for i in range(0, len(indexes)):
        lnk, lbl = _level_link(type, levels, i, indexes[i])
        if i == level:
            lnk = None
        _sl(df)
        df.TextElement(lbl, link = lnk)
                

def _browse_leaf(type, levels, level, index, moduleInfo, requested_formats):
    leaf = _leaf_for(type, index)
    l = levels[len(levels) - 1][index]
    start_label, end_label = l[0], l[1]
    
    df = definitionBuilder.Definition()
    
    _navigation_path(df, type, levels, level, index)
    
    # _sl(df)
    # df.TextElement("%s - %s" % (start_label.encode("latin-1", "ignore"), end_label.encode("latin-1", "ignore")))

    df.setTitle("eBooks by %s (%s - %s)" % (type, start_label.encode("latin-1", "ignore"), end_label.encode("latin-1", "ignore")))
        
    df.LineBreakElement()

    leaf = _leaf_for(type, index)
    _leaf(df, leaf, type, moduleInfo, requested_formats)

    df.LineBreakElement()
    df.LineBreakElement(1, 5)

    prev = False
    if index != 0:
        lnk, lbl = _level_link(type, levels, _g_level_count - 2, index - 1)
        df.TextElement("Previous", link = lnk).setJustification(definitionBuilder.justCenter)
        prev = True
    
    if index != len(l) - 1:
        if prev:
            df.TextElement(" ").setJustification(definitionBuilder.justCenter)
        lnk, lbl = _level_link(type, levels, _g_level_count - 2, index + 1)
        df.TextElement("Next", link = lnk).setJustification(definitionBuilder.justCenter)
    
    return df.serialize()

def _browse_level(type, levels, level, index):
    df = definitionBuilder.Definition()

    _navigation_path(df, type, levels, level, index)
    

    if level is not None:
        # _sl(df)
        lnk, label = _level_link(type, levels, level, index)
        # df.TextElement(label)
        df.setTitle("eBooks by %s (%s)" % (type, label))
    else:
        df.setTitle("eBooks by %s" % type)
        
    df.LineBreakElement()

    if level is None:
        sublevel = 0
        start_index = 0
        end_index = len(levels[0])
    else:
        sublevel = level + 1
        sub_power = levels[sublevel][0][3]
        start_index = int(math.floor(float(levels[level][index][2]) / sub_power))
        end_index = start_index + int(math.floor(float(levels[level][index][3] - sub_power * start_index - 1)/sub_power)) + 1

    subs = levels[sublevel]
    for i in range(start_index, end_index):
        lnk, label = _level_link(type, levels, sublevel, i)
        df.BulletElement(False)
        df.TextElement(label, link = lnk)
        if level is None:
           cnt = subs[i][3] - subs[i][2]
           df.TextElement(" (%s books)" % numPretty(cnt))
        df.PopParentElement()

    df.LineBreakElement()
    df.LineBreakElement(1, 5)
    
    if level is not None:
        prev = False
        if index != 0:
            lnk, lbl = _level_link(type, levels, level, index - 1)
            df.TextElement("Previous", link = lnk).setJustification(definitionBuilder.justCenter)
            prev = True
        
        if index != len(levels[level]) - 1:
            if prev:
                df.TextElement(" ").setJustification(definitionBuilder.justCenter)
            lnk, lbl = _level_link(type, levels, level, index + 1)
            df.TextElement("Next", link = lnk).setJustification(definitionBuilder.justCenter)
    
    return df.serialize()
        
def browse(type, level, index, moduleInfo, requested_formats):
    if type is None:
        return _start_page()

    if requested_formats == FORMATS_ALL:
        requested_formats = FORMATS
    else:
        requested_formats = map(string.strip, requested_formats.split())

    levels = _levels_for(type)
    if level == _g_level_count - 2:
        return _browse_leaf(type, levels, level, index, moduleInfo, requested_formats)
    else:
        return _browse_level(type, levels, level, index)

def _database_type_creator():
    for name in os.listdir(_g_cache_path):
        path = os.path.join(_g_cache_path, name)
        print name
        try:
            db = palmdb("load", path)
            n = db.main_header.get_data_string(32, 0)
            print n
            print db.main_header.get_creator()
            print db.main_header.get_type()
        except:
            pass

def _test():
    # reindex_all(only_database = True)
    browse(BROWSE_TITLE, 2, 0, None, "Doc")
#    print start_page()

    reindex_all(only_database = True)
#    reindex_all()
    sys.exit()
    
def main():
    # _test()
    # return
    spider = fDetectRemoveCmdFlag("-spider")
    reindex = fDetectRemoveCmdFlag("-reindex")
    update = fDetectRemoveCmdFlag("-update")
    force = fDetectRemoveCmdFlag("-force")
    test_query = getRemoveCmdArg("-test")
    # undocumented flags just for testing ;)
    backup = fDetectRemoveCmdFlag("--backup-index")
    use_old_index = fDetectRemoveCmdFlag("--update-old-index")
    update_index = fDetectRemoveCmdFlag("--force-index-update")
    bump_version = fDetectRemoveCmdFlag("--bump_version")
    if test_query:
        formats = FORMATS_ALL
        if -1 != test_query.find(";"):
            test_query, formats = [s.strip() for s in test_query.split(";", 1)]
        type = SEARCH_ANY
        if -1 != test_query.find(":"):
            t, q = [s.strip() for s in test_query.split(":", 1)]
            if t in SEARCH_TYPES:
                type, test_query = t, q
        for doc in _find_proxy(test_query, formats, type):
            d = _doc_to_tuple(doc)
            if 0 != len(d[1]):
                print "%s, \"%s (%s)\"" % (d[2], d[0], d[1])
            else:
                print "%s, \"%s\"" % (d[2], d[0])
        return
    if spider and reindex:
        update = True
    if update:
        update_all(force, force_index_update = update_index, update_old_index = use_old_index )
        return
    if spider:
        spider_all(force)
        return
    if reindex:
        reindex_all(use_old_index )
        return
    if backup:
        _backup_index()
        return
    if bump_version:
        _bump_version()
        return

    print """
usage: ebooks.py (-spider | -reindex | -update | -test "phrase") [-force]
Options:
    -spider  - performs only incremental spidering of all data
    -reindex - only reindexes existing spidered data.
    -update  - performs spidering and reindexing (only if fresh data was
               spidered).
    -force   - (only with -spider or -update) discards previously spidered data
               prior to spidering.
    -test    - tests searching in the index.
"""
    return 1

if __name__ == "__main__":
    main()

