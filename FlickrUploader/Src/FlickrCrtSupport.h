#ifndef FLICKR_CRT_SUPPORT_H__
#define FLICKR_CRT_SUPPORT_H__

inline void* ::operator new(unsigned long size)
{
    return MemPtrNew(0 == size ? 1 : size);
}

inline void* ::operator new[] (unsigned long size)
{
    return ::operator new(size);
}

inline void ::operator delete(void* p)
{
    if (NULL != p) MemPtrFree(p);
}

inline void ::operator delete[] (void* p)
{
    ::operator delete(p);
}

#endif // FLICKR_CRT_SUPPORT_H__