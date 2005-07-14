#ifndef INFOMAN_PEDIA_CACHE_DATA_READ_HPP__
#define INFOMAN_PEDIA_CACHE_DATA_READ_HPP__

#include <Reader.hpp>

// I put this function into separate file as it could potentially grow very big and I want to have 
// possibility to put it into separate segment.
status_t PediaCacheDataRead(const char_t* title, Reader& reader);

status_t PediaSearchDataRead(const char_t* title, Reader& reader);

#endif // INFOMAN_PEDIA_CACHE_DATA_READ_HPP__