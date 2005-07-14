# -*- coding: iso-8859-1 -*-

import string,socket
from sys import stdout
from MoriartyServer import buildField, parseRequestLine, lineSeparator
from arsutils import exceptionAsStr
import Fields

class TestAssertionFailed(Exception):
    
    def __init__(self, cause):
        self.cause=cause

def retrieveResponse(address, request):
    sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    res=""
    try:
        sock.connect(address)
        sock.sendall(request+lineSeparator)
        sock.shutdown(1)
        while True:
            chunk=sock.recv(256)
            if 0==len(chunk):
                break;
            res+=chunk
    finally:
        sock.shutdown(2)
        sock.close()
    return res

PROTOCOL_VERSION = "1"
CLIENT_INFO = "Python test client 1.0"

class ServerTest:

    def __init__(self):
        self.testCases=dict()
        self.transactionId="DEADBEEF"
        self.payloadFields=[]
        self.address=None
        self.fields=dict()

    def extractFields(self, response):
        while True:
            index=response.find(lineSeparator)
            line=None
            if -1==index:
                line=response
                response=""
            else:
                line=response[:index]
                index+=1
                response=response[index:]
            if 0==len(line):
                break
            (name, value)=parseRequestLine(line)
            assert None != name
            if name in self.payloadFields:
                assert None!=value
                length=int(value)
                value=response[:length]
                response=response[length+1:]
            self.fields[name]=value

    def assertFieldExists(self, name):
        if not self.fields.has_key(name):
            raise TestAssertionFailed("there's no field %s in response" % name)
    
    def assertFieldValueEquals(self, name, value):
        self.assertFieldExists(name)
        if self.fields[name]!=value:
            raise TestAssertionFailed("field %s isn't equal %s (is equal %s)" % (name, str(value), str(self.fields[name])))

    def prepareCommonFields(self):
        fields = [buildField(Fields.protocolVersion, PROTOCOL_VERSION)]
        fields.append(buildField(Fields.clientInfo, CLIENT_INFO))
        fields.append(buildField(Fields.transactionId, self.transactionId))
        return string.join(fields,"")

    def testCommonFields(self):
        self.assertFieldValueEquals(Fields.transactionId, self.transactionId)
    
    def runTestCase(self, prepAndTest):
        testName, prepFun, testFun=prepAndTest
        try:
            request=prepFun()
            response=retrieveResponse(self.address, request)
            self.extractFields(response)
            try:
                testFun()
                stdout.write('.')
            except TestAssertionFailed, ex:
                print "\n--------------------------------------------------------------------------------"
                print "Test case %s FAILED: %s" % (testName, ex.cause)
                print "--------------------------------------------------------------------------------"
        except Exception, ex:
            print "\n--------------------------------------------------------------------------------"
            print "Test case %s caused Exception.\n" % (testName)
            print exceptionAsStr(ex)
            print "--------------------------------------------------------------------------------"
        self.fields=dict()
    
    def runNamedTestCase(self, name):
        assert self.testCases.has_key(name)
        prepFun, testFun=self.testCases[name]
        self.runTestCase((name, prepFun, testFun))

    def runAllTests(self):
        for name in self.testCases.iterkeys():
            self.runNamedTestCase(name)
    
