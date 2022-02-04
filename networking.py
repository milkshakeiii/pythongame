import jsons

from twisted.internet import reactor
from twisted.protocols.basic import NetstringReceiver
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from dataclasses import dataclass

import gameplay
import gameflow
import messages


class MessageProtocol(NetstringReceiver):
    def __init__(self, request):
        self.request = request
        self.response = None
    
    def encodeAndSendString(self, string):
        self.sendString(bytes(string, "utf-8"))

    def stringReceived(self, data):
        self.stringDecoded(str(data, 'utf-8'))

    def connectionMade(self):
        self.encodeAndSendString(self.request)

    def stringDecoded(self, string):
        print(string)
        self.transport.loseConnection()

def send_message(message):
    message_string = jsons.dumps(message, verbose=True)
    point = TCP4ClientEndpoint(reactor, "localhost", 8007)
    connectProtocol(point, MessageProtocol(message_string))
    reactor.run() # TODO why does this block forever
