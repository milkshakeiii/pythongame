import jsons

from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.protocols.basic import NetstringReceiver

import gameplay
import gameflow
import messages

class HostProtocol(NetstringReceiver):
    def __init__(self):
        self.players = []
        self.starting_gamestate = None
    
    def connectionMade(self):
        print ("Connection made")

    def encodeAndSendString(self, string):
        self.sendString(bytes(string, "utf-8"))

    def connectionLost(self, reason):
        print("connection lost")

    def stringReceived(self, data):
        print("stringReceived")
        self.stringDecoded(str(data, 'utf-8'))

    def stringDecoded(self, string):
        message = jsons.loads(string)
        print(type(message))
        response = message.handle_on_server(self)
        self.encodeAndSendString(jsons.dumps(response, verbose=True))



class HostProtocolFactory(Factory):
    def buildProtocol(self, addr):
        return HostProtocol()
    
# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 8007)
endpoint.listen(HostProtocolFactory())
reactor.run()
