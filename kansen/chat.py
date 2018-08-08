from socketserver import BaseRequestHandler
from time import time
from twisted.internet.protocol import Protocol
from kansen.models import Message
from twisted.python import log


class ChatProtocol(Protocol):

    def __init__(self, factory, reactor):
        self.factory = factory
        self.reactor = reactor
        self.state = None
        self.last_message_time = 0
        self.message_limit = 0

    def connectionMade(self):
        self.factory.users.append(self)
        self.factory.broadcast(self.users_online())
        self.send(self.welcome_message())
        log.msg('Client connected')

        # send last 5 messages from db
        q = self.factory.session.query(Message).order_by(
            Message.id.desc()).limit(5).all()[::-1]
        for item in q:
            self.send(item.body)

    def connectionLost(self, reason):
        self.factory.users.remove(self)
        self.factory.broadcast(self.users_online())
        log.msg('Client disconnected')

    def send(self, data, reciever=None):
        """Encode message to bytes object before sending"""
        if not isinstance(data, bytes):
            data = data.encode('utf-8')
        if not reciever:
            self.transport.write(data)

    def unmute(self):
        """Resets user message limit and state"""
        self.message_limit = 0
        self.state = None

    def mute(self, timeout:int):
        """Mutes user for :timeout: seconds"""
        return self.reactor.callLater(timeout, self.unmute)

    def dataReceived(self, data):
        self.check_spam()
        if not self.state:
            if data.decode('utf-8').startswith('[2:'):
                timestamp = ':{}]'.format(str(round(time())))
                msg = Message(body=data.decode('utf-8').replace('[2:', '[3:').replace(']', timestamp))
                self.factory.session.add(msg)
                try:
                    self.factory.session.commit()
                except Exception:
                    self.factory.session.rollback()
                self.factory.broadcast(data)
                log.msg("New chat message recieved: {}".format(data))
            else:
                log.err("Wrong data recieved. {0}".format(data))
                self.transport.loseConnection()

    def check_spam(self):
        data_timestamp = time()
        if not self.state:
            if data_timestamp - self.last_message_time < 0.5:
                self.message_limit += 1
            else:
                self.message_limit = 0
            self.last_message_time = data_timestamp
            if self.message_limit >= 5:
                self.state = 'MUTED'
                self.send("[4]")
                log.msg('User muted')
                self.mute(5)

    def users_online(self):
        return '[1:{}]'.format(len(self.factory.users))

    def welcome_message(self):
        return "[0]"
