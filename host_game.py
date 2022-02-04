import jsons

from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.protocols.basic import NetstringReceiver

import gameplay
import gameflow
import messages

class HostProtocol(NetstringReceiver):
    def connectionMade(self):
        print ("Connection made")

    def encodeAndSendString(self, string):
        self.sendString(bytes(string, "utf-8"))

    def connectionLost(self, reason):
        print("connection lost")

    def stringReceived(self, data):
        self.stringDecoded(str(data, 'utf-8'))

    def stringDecoded(self, string):
        print(string)
        message = jsons.loads(string)
        self.encodeAndSendString(str(type(message)))

class HostProtocolFactory(Factory):
    def buildProtocol(self, addr):
        return HostProtocol()
    
# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 8007)
endpoint.listen(HostProtocolFactory())
reactor.run()
