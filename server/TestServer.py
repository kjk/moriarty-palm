
from twisted.internet import protocol, reactor
from twisted.protocols import basic

from FieldPayloadProtocol import FieldPayloadProtocol

class TestServerFactory(protocol.ServerFactory):
    servicePort=9000
    protocol = FieldPayloadProtocol

def main():
    reactor.listenTCP(TestServerFactory.servicePort, TestServerFactory())
    reactor.run()

if __name__ == "__main__":
    main()
