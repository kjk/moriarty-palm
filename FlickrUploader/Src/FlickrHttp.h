#ifndef FLICKR_HTTP_H__
#define FLICKR_HTTP_H__

enum HttpRequestFlags {
    httpRequestFlagPublic = 1,
    httpRequestFlagFriend = 2,
    httpRequestFlagFamily = 4
};    

struct FlickrSocketContext;

Err HttpPrepareRequest(FlickrSocketContext& context);

Err FlickrAddressResolve(FlickrSocketContext& context);

Err FlickrPerformConnection(FlickrSocketContext& context);

#endif // FLICKR_HTTP_H__