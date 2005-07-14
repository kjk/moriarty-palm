#include <BaseTypes.hpp>
#include <Debug.hpp>
#include <Text.hpp>
#include <DynStr.hpp>
#include <ByteFormatParser.hpp>
#include <HistoryCache.hpp>
#include <DefinitionStyle.hpp>

#include "UnitTests.hpp"

#include "RSA_Test.hpp"

// Implements running unit tests for our code.
// The idea is simple: RunAllUnitTests() runs in debug
// mode and executes all unit tests. A failure is indicated by an assert().

// a good idea is to first write unit tests and only after that
// write the code to implement the functionality being tested. It's called
// test-driven developement.

static void testVersionNumberCmp()
{
    assert( versionNumberCmp("1.1", "1.1") == 0);
    // 1.1 is greater than 1.0
    assert( versionNumberCmp("1.1", "1.0") > 0);
    assert( versionNumberCmp("2.0", "1.0") > 0);
    assert( versionNumberCmp("22.1", "17.5") > 0);
    // 1.1 is smaller than 1.2
    assert( versionNumberCmp("1.1", "1.2") < 0);
    assert( versionNumberCmp("5.5", "5.6") < 0);
    assert( versionNumberCmp("6.6", "7.5") < 0);
    assert( versionNumberCmp("7.3", "8.4") < 0);
}

/*
static void testReadWriteUnaligned32()
{
    char_t test[8] = {0,1,2,3,4,5,6,7};
    assert(66051 == readUnaligned32(&test[0]));
    assert(16909060 == readUnaligned32(&test[1]));
    assert(33752069 == readUnaligned32(&test[2]));
    assert(50595078 == readUnaligned32(&test[3]));

    writeUnaligned32(&test[0],66051);
    writeUnaligned32(&test[1],16909060);
    writeUnaligned32(&test[2],33752069);
    writeUnaligned32(&test[3],50595078);

    assert(test[0] == 0);
    assert(test[1] == 1);
    assert(test[2] == 2);
    assert(test[3] == 3);
    assert(test[4] == 4);
    assert(test[5] == 5);
    assert(test[6] == 6);
}
*/

void RunAllUnitTests()
{
    // if you want to verify, that the system works, just uncomment
    // the assert below. It should fire at startup in debug build
    // assert(false);

    testVersionNumberCmp();
    test_DynStrAll();

//    testReadWriteUnaligned32();

    test_TextUnitTestAll();

    test_HistoryCache();
    
    test_StaticStyleTable();
    
    test_StyleParse();
  
// RSA decryption lasts very long so it should be run only when really neccessary  
//    test_RSA();
}
