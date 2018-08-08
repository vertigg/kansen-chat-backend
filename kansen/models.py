from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Message(Base):

    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    body = Column(String(255))

    def __repr__(self):
        return self.body

    def __str__(self):
        return self.body