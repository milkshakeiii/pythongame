import jsons
import crochet

from twisted.internet import reactor
from twisted.protocols.basic import NetstringReceiver
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from dataclasses import dataclass

import game_io
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
        response_container = jsons.loads(string, cls=messages.MessageContainer)
        self.response = jsons.loads(
            response_container.message,
            cls=response_container.message_type)
        self.transport.loseConnection()

@crochet.wait_for(5)
def send_message(message):
    message_string = jsons.dumps(message)
    message_container_string = jsons.dumps(
        messages.MessageContainer(message=message_string,
                         message_type=message.message_type()))
    point = TCP4ClientEndpoint(reactor, "localhost", 8007)
    message_protocol = MessageProtocol(message_container_string)
    connectProtocol(point, message_protocol)
    return message_protocol

def wait_for_response(message):
    message_protocol = send_message(message)
    while (message_protocol.response == None):
        pass
    return message_protocol.response
