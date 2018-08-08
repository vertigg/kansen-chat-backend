import sys
from time import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.python import log
from twisted.python.logfile import DailyLogFile

from kansen.chat import ChatProtocol
from kansen.models import Base

PORT = 29500

class ChatFactory(Factory):
    def __init__(self):
        self.users = []
        self.engine = create_engine('sqlite:///data.db', echo=False)
        # Base.metadata.create_all(self.engine) # Update db metadata
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        reactor.addSystemEventTrigger("before", "shutdown", self.pre_shutdown)

    def buildProtocol(self, addr):
        return ChatProtocol(self, reactor=reactor)

    def broadcast(self, data):
        for user in self.users:
            user.send(data)

    def pre_shutdown(self):
        """Commits to db before shutdown and ends session"""
        try:
            self.session.commit()
        except:
            self.session.rollback()
        self.session.close()

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    log.startLogging(DailyLogFile.fromFullPath('kansen/logs/chat.log'))
    reactor.listenTCP(PORT, ChatFactory())
    reactor.run()
