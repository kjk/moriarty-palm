# Owner: Krzysztof Kowalczyk
#
# Purpose:
#   unit testing of all the code

import unittest
import arsutils

class TestMisc(unittest.TestCase):

    def testHostFromUrl(self):
        self.assertEqual("foo.com", arsutils.getHostFromUrl("http://foo.com/"))
        self.assertEqual("me.him.com", arsutils.getHostFromUrl("http://me.him.com/blast///as/"))
        self.assertEqual("arslexis.com", arsutils.getHostFromUrl("http://arslexis.com////"))
        self.assertEqual("foo.com", arsutils.getHostFromUrl("http://foo.com/;asdfa;asf;//asdf//asdf"))

if __name__ == "__main__":
    unittest.main()
