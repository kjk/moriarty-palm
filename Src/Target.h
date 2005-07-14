#ifndef _MORIARTY_TARGET_H_
#define _MORIARTY_TARGET_H_

#if __ide_target("Release")
 #include <PalmOS_Headers>

 #ifndef NDEBUG
  #define NDEBUG
 #endif // __ide_target("Release")

 #define ARSLEXIS_VERSION 1
#endif

#if __ide_target("Shipping")
 #include <PalmOS_Headers>

 #ifndef NDEBUG
  #define NDEBUG
 #endif //  __ide_target("Shipping")

 #define SHIPPING 1

 #define ARSLEXIS_VERSION 1

#endif

#if __ide_target("Shipping PalmGear")
 #include <PalmOS_Headers>

 #ifndef NDEBUG
  #define NDEBUG
 #endif

 #define SHIPPING 1
 #define PALMGEAR 1
#endif  // __ide_target("Shipping PalmGear")

#if __ide_target("Debug")
 #include <PalmOS_Headers_Debug>

 #define ARSLEXIS_VERSION 1
#endif // __ide_target("Debug")

// TODO: make separate HANDANGO versions by
//#define HANDANGO

#define ARSLEXIS_USE_NEW_FRAMEWORK 1
#define _PALM_OS  1

#define ARSLEXIS_USE_MEM_GLUE 1

#define ARSLEXIS_USE_SELECT_EVENTS 1

//devnote: only works in debug build
#define ARSLEXIS_DEBUG_MEMORY_ALLOCATION 1

#define ALLOCATION_LOG_PATH "c:\\moriarty_allocs.txt"

#ifdef __MWERKS__
// Decreases stack usage
#pragma stack_cleanup on

#pragma warn_impl_s2u_conv on
#endif

#define INFOMAN 1

#ifndef NDEBUG
//! Some functions depend on this non-standard symbol instead of standard-compliant @c NDEBUG.
 #define DEBUG
 #define _DEBUG 
#endif

#else

 #error "You must not include file Target.h directly. You should use it as your prefix file."

#endif // _MORIARTY_TARGET_H_
