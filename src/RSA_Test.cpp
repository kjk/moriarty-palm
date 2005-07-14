
#include "RSA_Test.hpp"

#ifndef _MSC_VER
#include "moriarty.h"

#include <rsa/rsa.h>
#else

enum {
    rsaKeyLengthBits = 512,
    rsaKeyLengthBytes = rsaKeyLengthBits / 8
};    


#include "../../ars_framework/src/rsa/rsa.h"
#include "../../ars_framework/src/rsa/rand.h"

#include <memory>
#include <cassert>

#endif

#include <cstring>

using namespace std;

#ifndef NDEBUG

const char* rsaPrivateKey = "\xa1\x10\x93\x64\x4b\x0a\x5f\xfe\xe8\x8c\x4a\xa2\xc0\xa1\x98\xd0\xf9\x19\xab\x3a\x80\xa3\x49\xfd\xf5\x3d\x6a\x97\xeb\x8d\x7c\xc7\x0c\xb3\xaf\xe0\x36\x3c\x7f\x1e\xda\x61\xad\x7e\xd3\x68\xfe\x21\xf6\xec\x16\x65\x0c\x62\x22\x02\x84\xf0\x1e\xa4\x5f\xa9\xe1\x9f";

static void print_key(uint8* key)
{
#ifdef _MSC_VER
	printf("\n\"");
	for (uint32 i = 0; i < rsaKeyLengthBytes; ++i)
	{
		unsigned ch = key[i];
		printf("\\x%02x", ch);
	}
	printf("\"\n");
#endif	
}

void test_RSA()
{

#ifdef _MSC_VER

    static uint8 entropy_pool[rsaKeyLengthBytes];

    rand_init();
    rand_selfseed();
    rand_getbytes(entropy_pool, rsaKeyLengthBytes);
    rand_done();

#endif
	
    uint8 *priv = NULL, *pub = NULL, *temp = NULL, *ctext = NULL, *out = NULL;
   
    const char* inStr = "jackdaw loves my big sphinx of quartz";
    uint32 len = strlen(inStr) + 1;
    uint32 outLen;

    uint8* in = (uint8*)inStr;
    int res;
    
    temp = (uint8*)malloc(8 * rsaKeyLengthBits);
    if (NULL == temp)
        goto cleanup;
        
    priv = (uint8*)malloc(rsaKeyLengthBytes);
    if (NULL == priv)
        goto cleanup;
    
    pub = (uint8*)malloc(rsaKeyLengthBytes);
    if (NULL == pub)
        goto cleanup;
    
    out = (uint8*)malloc(rsaKeyLengthBytes);
    if (NULL == out)
        goto cleanup;
    
    ctext = (uint8*)malloc(rsaKeyLengthBytes);
    if (NULL == ctext)
        goto cleanup;
        
    memset(temp, 0, rsaKeyLengthBits * 8);

#ifdef _MSC_VER    
    
    rsa_keygen(entropy_pool, pub, priv, rsaKeyLengthBits, temp);
    print_key(pub);
    print_key(priv);
    memset(temp, 0, rsaKeyLengthBits * 8);
    
#else
    
    memcpy(pub, rsaPublicKey, rsaKeyLengthBytes);
    memcpy(priv, rsaPrivateKey, rsaKeyLengthBytes);
    
#endif        

    res = rsa_encrypt(in, len, ctext, pub, rsaKeyLengthBits, temp);
    assert(0 == res);
    
    memset(temp, 0, rsaKeyLengthBits * 8);

    res = rsa_decrypt(ctext, out, pub, priv, rsaKeyLengthBits, temp);
    assert(0 == res);
    
    outLen = strlen((char*)out) + 1;
    assert(len == outLen);
    assert(0 == memcmp(in, out, len));
    
cleanup:

    if (NULL != out)
        free(out);
    if (NULL != temp)
        free(temp);
    if (NULL != pub)
        free(pub);
    if (NULL != priv)
        free(priv);
    if (NULL != ctext)
        free(ctext);

}

#endif