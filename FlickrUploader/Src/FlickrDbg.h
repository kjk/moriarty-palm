#ifndef FLICKR_DBGH__
#define FLICKR_DBG_H__

void DbgNum(long l);

void DbgHex(unsigned long l);

inline void DbgPtr(void* p) {DbgHex((unsigned long)p);}

#ifndef NDEBUG

#define DMSG(a) DbgMessage((a))
#define DNUM(n) DbgNum(n)
#define DHEX(n) DbgHex(n)
#define DPTR(p) DbgPtr(p)

#define assert(condition) ((condition) ? ((void) 0) : ErrDisplayFileLineMsg(__FILE__, (UInt16) __LINE__, #condition))

#else

#define DMSG(a)
#define DNUM(n)
#define DHEX(n)
#define DPTR(p)

#define assert(ignore) ((void) 0)

#endif

#define DENDL   DMSG("\n");

#endif // FLICKR_DEBUG_H__