#ifndef INFOMAN_HISTORY_HPP__
#define INFOMAN_HISTORY_HPP__

#include <Debug.hpp>
#include <Reader.hpp>

class HistoryCache;

bool ReadUrlFromCache(HistoryCache& cache, const char_t* url);

// Opens HistoryCache for this url, reads its contents and moves it in cache as the last entry.
bool ReadUrlFromCache(const char_t* url);


class DefinitionModel;

status_t ReadByteFormatFromReader(Reader& reader, DefinitionModel*& model);

#endif // INFOMAN_HISTORY_HPP__