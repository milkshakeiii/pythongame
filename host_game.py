import jsons

from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.protocols.basic import NetstringReceiver

import gameplay
import gameflow
import messages

from dataclasses import dataclass
from typing import List

class ServerState:
    def __init__(self):
        self.players = list()
        self.turns = list()
        self.starting_gamestate = None
serverState = ServerState()
    
class HostProtocol(NetstringReceiver):
    
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
        message_container = jsons.loads(string, cls=messages.MessageContainer)
        message = jsons.loads(message_container.message,
                              cls=message_container.message_type)
        print(type(message))
        response_body = message.handle_on_server(serverState)
        response = messages.MessageContainer(
            message=jsons.dumps(response_body),
            message_type=response_body.message_type())
        self.encodeAndSendString(jsons.dumps(response))

class HostProtocolFactory(Factory):
    def buildProtocol(self, addr):
        return HostProtocol()
    
# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 8007)
endpoint.listen(HostProtocolFactory())
reactor.run()
