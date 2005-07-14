# --------------------------------------------------
#
#   Copyright (c) 2003-2004 by Jesko Huettenhain,
#   .aware security research
#
#   http://www.awarenetwork.org/
#
#   For more information consult the Readme file.
#
# --------------------------------------------------
#
#   This is pyRSA, an RSA implementation in Python
#
#   pyRSA is free software; you can redistribute it
#   and/or modify it under the terms of the GNU
#   General Public License as published by the Free
#   Software Foundation; either version 2 of the
#   License, or (at your option) any later version.
#
#   pyRSA is distributed in the hope that it will be
#   useful, but WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or
#   FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU
#   General Public License along with Plague; if not,
#   write to the Free Software Foundation, Inc.,
#
#   59 Temple Place,
#   Suite 330, Boston,
#   MA 02111-1307 USA
#
# --------------------------------------------------


from math import *
from types import *
from random import random
from sys import stdout as out
from time import time,gmtime,strftime
from base64 import encodestring as b64, decodestring as unb64


# All the following functions are used to provide a
# visualization of the key generation process when
# using the python interpreter.

_rsa_dsp_sequence = ("|/-\\", '>')
_rsa_dsp_i = 0
_rsa_dsp_t = 0

def rsadsp(d):
    global rsa_dsp
    rsa_dsp = d

def _rsa_dsp_init():
    global _rsa_dsp_t
    _rsa_dsp_t = time()

def _rsa_dsp_end():
    out.write(strftime(" # keys created in %H:%M:%S\n", gmtime(time()-_rsa_dsp_t)))

def _rsa_dsp_iter(b=False):
    if (b):
        out.write(_rsa_dsp_sequence[1])
    else:
        global _rsa_dsp_i
        _rsa_dsp_i += 1
        _rsa_dsp_i %= len(_rsa_dsp_sequence[0])
        out.write(_rsa_dsp_sequence[0][_rsa_dsp_i]+'\b')



# randrange() doesn't work for too big
# ranges, eg. 2048 bit-lengthy ones.
# therefore, I coded this little hack.
# it basically uses randrange() code, but
# in an altered fashion.

def rand(start):
    fl = random()
    ll = long(fl * (10**17)) # thats the maximum precision
    ll *= start
    ll /= (10**17)
    return ll


# returns the number of bytes in memory
# that are required to store the given
# long integer number i.

def bytelen(i):
    blen = 0
    while (i != 0):
        blen += 1 # one more byte
        i >>= 8 # and shift.
    return blen



# hexunpack turns a long integer number i
# into a python string that contains the
# same number in little endian format.

def hexunpack(i,l=0):
    sval = ""
    if not l: l = bytelen(i)
    for j in range (l):
        ival = i & 0xFF
        i = i >> 8
        sval += chr(ival)
    return sval

# hexpack reads a string an interprets it
# as a long integer number stored byte by
# byte in little endian format and returns
# that integer.

def hexpack(s,l=0):
    hret = 0L
    if not l: l = long(len(s))
    for i in range(l):
        val = long(ord(s[i]))
        val = val << long(i*8)
        hret += val
    return long(hret)


# raw encryption algorithm for RSA keys and
# python strings.

def raw_Encrypt(s, key):

    if (type(s) != StringType):
        return None

    # the bytelength of the modulo key part.
    blen = long(bytelen(key[1]))

    # thh first two bytes store the cipher block
    # length as determined by the keylength itself.
    # rev = hexunpack(blen,2)
    rev = ""

    # a simple signature at the end of our string,
    # then it is padded with zeros up to the block
    # length. To be really sure not to miss any data,
    # we will encrypt blocks of (blen-1) bytes.

    while len(s) % (blen-1):
        s += '\x00'

    # perform the actual encryption of every block.

    for i in xrange(0,len(s),blen-1):
        rev += hexunpack(ModExp(hexpack(s[i:i+blen],blen-1), key[0], key[1]),blen)

    return rev


# this is the decryption routine. It works very
# similar to the decryption routine.

def raw_Decrypt(s, key):

    if (type(s) != StringType):
        return None

    rev = ""

    blen = long(bytelen(key[1]))

    # extract the block length from the first
    # two bytes and check whether the remaining
    # string has the correct length.

    # blen, s = hexpack(s[0:2],2), s[2:]
    if len(s) % blen: return None

    # now we just loop through the remaining string
    # and decrypt each blockk Remember we encrypted blocks
    # with an actual block length of (blen-1) bytes.

    for i in xrange(0,len(s),blen):
        rev += hexunpack(ModExp(hexpack(s[i:i+blen],blen), key[0], key[1]),blen-1)


    # find the signature at the end. All zeros that
    # follow this signature are padding and will be
    # truncated. However, if there is no signature,
    # this is not a string encrypted with our
    # encryption routine and therefore our results
    # so fare are bogus.

    sig = rev.find("\x00")

    if -1 == sig:
        sig = len(rev)

    return rev[0:sig]




# This is the main class of the rsa module. rsakey
# objects are returned by the core function keypair()
# which generates two matching keys. An rsakey object
# provides mechanisms to encrypt and decrypt data
# and can be represented as a Base64 encoded string.


class rsakey:


    # Thh constructor takes as the first and only argument
    # an already working key. This key can be passed as a
    # filename, a base64 encoded string or a two-element-sequence
    # holding the cruicial numbers.

    def __init__(self,keys=None):

        self.__key = 0  # first, we initialize the core
        self.__mod = 0  # values to zero.

        # If the keys argument is a string, we will at first
        # interpret this string as a filename and try to
        # load the key from the file. If it is an invalid
        # filename, an exception will be thrown and we can
        # assume that the string is not a filename but the
        # base64 encoded string representation of the key.

        if type(keys) is StringType:
            try: self.load(keys)
            except: self.read(keys)

        # If the argument, however, is not a string but a
        # sequence, we can directly try to initialize our
        # core values.

        elif type(keys) in [ListType,TupleType]:
            if (len(keys)!=2): raise ValueError("a valid key consists of 2 integer numbers")
            else: self.set(keys[0],keys[1])

        # Anything else, except a value of None is not
        # a valid argument.

        elif type(keys) is not NoneType:
            raise ValueError("argument must be a string representation of the keys or a tuple/list")



    # This is the core encryption and decryption
    # routine. It should seldomly be called directly,
    # unless you want to implement your own
    # encryption / decryption mechanisms.

    def crypt(self, x):
        return ModExp(x,self.__key,self.__mod)

    # len(rsakey) will return the length of the key
    # in bits. This also equals the block length that
    # will be used when encrrpting arbitrary data.

    def __len__(self):
        return bytelen(self.__mod)*8

    # The string representation of the key is just a
    # raw dump of the core values, encoded with base64.

    def __repr__(self):
        return str(self)

    def __str__(self):
        b = max(bytelen(self.__key),bytelen(self.__mod))
        v = hexunpack(self.__key,b) + hexunpack(self.__mod)
        return b64(v)

    # rsakey.read() will read a string representation
    # generated by this class (see __str__()) and set
    # the core values appropriately.

    def read(self,s):
        try: s = unb64(s)
        except: raise ValueError("key must be base64 encoded.")
        if len(s)%2: raise ValueError("invalid key")

        k = s[0:len(s)/2]
        m = s[len(s)/2:]

        self.set(hexpack(k),hexpack(m))


    # The set routine can be used to set the core values
    # directly.

    def set(self,k,m):
        self.__key, self.__mod = k, m


    # encryption / decryption routines merely wrap the
    # raw routines which have been discussed at the
    # beginning of this source file.

    def encrypt(self,s):
        return raw_Encrypt(s,[self.__key,self.__mod])

    def decrypt(self,s):
        return raw_Decrypt(s,[self.__key,self.__mod])


    # The dump() function dumps the key to an ASCII
    # file by writing the string representation from
    # self.__str__() to the file.
    #
    # The related load() function will read such a
    # string representation from a file and pass the
    # string over to the read() function to initialize
    # the core values.

    def dump(self,filename):
        t = open(filename,"w")
        t.write(str(self))
        t.truncate()
        t.close()

    def load(self,filename):
        return self.read(open(filename,"r").read())


    # For very large keys, encryption and decryption
    # of data can be very slow. Therefore, small strings
    # like passwords or keys for other encryption
    # mechanisms should be encrypted by using the
    # pencrypt and pdecrypt functions which only
    # call the ModExp() operation once.
    #
    # For this purpose, the data that has to be
    # encrypted is interpreted as one large integer
    # number (byte by byte) and this single number
    # is being encrypted / decrypted.

    def pencrypt(self, s):
        i = self.crypt(hexpack(s))
        return b64(hexunpack(i))

    def pdecrypt(self, s):
        i = self.crypt(hexpack(unb64(s)))
        return hexunpack(i)



# The ModExp function is a faster way to perform
# the following arithmethic task:
#
# (a ** b) % n

def ModExp(a,b,n):
    d = 0L
    t = 0L
    i = 0

    n = long(n)

    if (b == 0):  return (1%n)  # easy.
    elif (b < 0): return (-1)   # error.

    else:

        d = 1L
        i = int(log(b)/log(2))

        while (i >= 0):
            d = (d*d)%n; t = long(2**i)
            if (b&t): d = long(d*a)%n
            i -= 1

        return d


# The Miller-Rabin Algorithm is used to verify that
# a number is a prime number.

def MRabin(number,attempts):

    rndNum = 0L
    retVal = False
    i = 0

    if (number < 10):
        return Fermat(number);

    else:
        retVal = True;

        for i in xrange(attempts):
            rndNum = rand(number-2)
            if (rndNum < 2): rndNum = rndNum + 2

            if (Witness(rndNum, number)):
                retVal = False
                break

        return retVal


# the witness function is used by the miller-rabin
# alorithm to prove that a number is NOT prime

def Witness(witness,number):

    f = 1; x = 0;
    t = 0; i = 0;

    retVal = False;
    i = int(log(number-1)/log(2))

    while (i >= 0):

        x = f
        f = x * x % number
        t = 2 ** i

        if ((f==1) and (x!=1) and (x!=(number-1))):
            retVal = True
            break

        if (((number-1) & t) != 0):
            f = f * witness % number;

        i -= 1

    if (retVal):
        return True
    else:
        if (f != 1): return True
        else: return False


# fermat is a much more simple and less reliable
# function to check whether a number is prime or
# not. It sometimes gives false results but is
# much faster than the miller-rabin algorithm.

def Fermat(number):
    return bool((number==2)or(ModExp(2,(number-1),number)==1))


# This function calculates the greatest common
# divisor of two numbers.

def GCD(a,b):
    if (b!=0):
        if ((a%b)!=0): return GCD(b,(a%b))
        else: return b
    else: return a


# Euclid's extended algorithm. I altered it briefly
# so it does not return the GCD but only the multiplicative
# inverse.

def exeu(a, b):

    q=0L; r=0L;
    x = [0L,0L,0L]
    y = [0L,0L,0L]

    if not b: return [1,0]

    else:

        x[2] = 1; x[1] = 0
        y[2] = 0; y[1] = 1

        while (b>0):

            q=a/b
            r=a-q*b

            x[0]=x[2]-q*x[1];
            y[0]=y[2]-q*y[1]

            a,b=b,r

            x[2]=x[1];x[1]=x[0];
            y[2]=y[1];y[1]=y[0];

        return [x[2],y[2]]


# This function generates a random prime number by using
# the algorithms specified above.

def prime(bytes, init=0L):

    i = init

    # if we already know a large prime number, it
    # is sometimes faster to find the "next" prime
    # number by guessing where to start the search.

    if i: i+= long(log(i)/2)
    else: i = rand(2**bytes)

    if not i%2: i+=1 # chose the first uneven number

    # p is the required precision for the miller-
    # rabin algorithm. For large numbers, we higher
    # values for p to ensure that the miller-rabin
    # algorithm returns reliable results.

    p = int(ceil(sqrt(bytes)))*2
    if (p > 40): p = 40

    f = False # f is true if i is prime

    while not f:
        while not Fermat(i): # find a number that might be prime
            i += 2
            if (rsa_dsp): _rsa_dsp_iter()
        if (rsa_dsp): out.write("!\b");

        f = MRabin(i,p) # verify that it is prime

    if (rsa_dsp): _rsa_dsp_iter(True)

    return i # return the prime number


# the keypair function returns a tuple of 2 rsakey objects
# which can be used for public key encryption via RSA. The
# bitmax paramter specifies the length in bits of the
# generated keys. On a 700 MHz machine, this script has
# already generated 8192 bit keys after a couple of hours
# while 4096 bits are considered secure already.

def keypair(bitmax):

    p = 0L; q = 0L;
    e = 0L; d = 0L;

    n = 0L

    bWorks = False;

    if (bitmax % 2): bitmax += 1
    maxB = 2L ** long(bitmax/2)

    if (rsa_dsp): _rsa_dsp_init()

    # find two large prime numbers

    p = prime(bitmax/2)
    q = prime(bitmax/2, p)

    # calculate n=p*q and p=phi(n)=phi(p*q)=(q-1)*(p-1)
    # moreover, delete the prime numbers from memory
    # as they are not required any longer.

    n,p = (q*p), (q-1)*(p-1)
    del q

    while not bWorks:

        bWorks = True

        # find a random number e with gcd(phi(n),e)!=1
        # it will be the encryption key (the public key)

        e = rand(maxB)*rand(maxB)
        while (p/e > 5): e=rand(maxB)*rand(maxB)
        while (GCD(p,e)!=1): e+=1

        # calcualte the multiplicative inverse of e and
        # phi(n), it will be the decryption key (the
        # private key)

        sum = exeu(p,e)
        if ((e * sum[1] % p) == 1): d = sum[1]
        else: d = sum[2]

        # test these keys to verify that they are
        # valid and working

        if ((d>1) and (e>1) and (n<>0) and (e<>d)):

            for a in range(4):

                ascNum = rand(255)
                if rsa_dsp: _rsa_dsp_iter()
                cipher = ModExp(ascNum,e,n)
                if rsa_dsp: _rsa_dsp_iter()

                if (ModExp(cipher,d,n)!=ascNum):
                    bWorks = False
                    break

        else:

            bWorks = False


    if rsa_dsp:
        _rsa_dsp_iter(True)
        _rsa_dsp_end()

    e = long(e)
    n = long(n)
    d = long(d)
    print "e: ", e
    print "n: ", n
    print "d: ", d

    return rsakey((e,n)),rsakey((d,n))


rsadsp(True)

if __name__ == "__main__":

    e,d = keypair(1024)
    print "\nPublic Key:"
    print e
    print "\nPrivate Key:"
    print d
    raw_input()



