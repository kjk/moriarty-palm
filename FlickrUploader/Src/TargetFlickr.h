
#include <BuildDefines.h>

#define INFOMAN_FLICKR_EXCHANGE_LIB

#if __ide_target("Release")
 #include <PalmOS_Headers>

 #ifndef NDEBUG
  #define NDEBUG
 #endif 
 #endif // __ide_target("Release")

#if __ide_target("Debug")
 #include <PalmOS_Headers_Debug>
#endif // __ide_target("Debug")


#ifndef NDEBUG
//! Some functions depend on this non-standard symbol instead of standard-compliant @c NDEBUG.
 #define DEBUG
 #define _DEBUG
#endif 

#ifdef EMULATION_LEVEL
#undef EMULATION_LEVEL
#endif

#define EMULATION_LEVEL EMULATION_NONE

