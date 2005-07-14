#ifndef FLICKR_HPP__
#define FLICKR_HPP__

#include <Debug.hpp>

// TODO: correctly set FLICKR_ENABLED when module is finished
#ifndef NDEBUG
#define FLICKR_ENABLED 1
#else
#define FLICKR_ENABLED 0
#endif

status_t FlickrInitialize();

void FlickrSynchronizeRegistrationStatus();

UInt32 FlickrGetResetPictureCount();

#endif