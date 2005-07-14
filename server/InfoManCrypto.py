
try:
    import rsa
except:
    print "requires pyRSA module from http://www.awarenetwork.org/"
    raise


_g_key_length = 512
_g_public_key = "\xdb\xa6\x0a\x13\x10\x98\xb7\xfc\x9d\x78\x47\x9f\x40\xf0\x10\xdd\xe6\x52\xad\xe7\x21\xc6\x12\xdb\x22\x4a\xb2\x90\x58\x3c\x5f\x98\xae\xf1\xd2\x6b\x66\xca\x33\xf9\x16\xa6\xa2\xdb\xdc\x8a\x42\x34\x96\x80\x42\x81\x7e\xc9\xab\x0c\x76\x79\x4d\x46\x08\xa4\x7a\xd3"
_g_private_key = "\xa1\x10\x93\x64\x4b\x0a\x5f\xfe\xe8\x8c\x4a\xa2\xc0\xa1\x98\xd0\xf9\x19\xab\x3a\x80\xa3\x49\xfd\xf5\x3d\x6a\x97\xeb\x8d\x7c\xc7\x0c\xb3\xaf\xe0\x36\x3c\x7f\x1e\xda\x61\xad\x7e\xd3\x68\xfe\x21\xf6\xec\x16\x65\x0c\x62\x22\x02\x84\xf0\x1e\xa4\x5f\xa9\xe1\x9f"
_g_exponent = 65537

def decrypt_binary(s):
    n = rsa.hexpack(_g_public_key)
    d = rsa.hexpack(_g_private_key)
    priv = rsa.rsakey((d, n))
    return priv.decrypt(s)

def decrypt_hexbin(s):
    import binascii
    s = binascii.unhexlify(s)
    return decrypt_binary(s)

def _test_keys():
    e = _g_exponent
    n = rsa.hexpack(_g_public_key)
    d = rsa.hexpack(_g_private_key)
    pub = rsa.rsakey((_g_exponent, n))
    priv = rsa.rsakey((d, n))

    text = "jackdaw loves my big sphinx of quartz"
    print "plain text: ", len(text), text

    ctext = pub.encrypt(text)
    out = priv.decrypt(ctext)

    print "decrypted: ", len (out), out

    assert out == text



def main():
    _test_keys()

if __name__ == "__main__":
    main()
