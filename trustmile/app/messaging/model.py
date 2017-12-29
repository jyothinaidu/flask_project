from flask import json
from sqlalchemy import Column, Text, Table, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.model.meta.orm import UniqueMixin, one_to_many
from app.model.meta.schema import TableColumnsBase
from app.model.meta.types import GUID

__author__ = 'james'

from app import db

conversation_participants = Table('conversation_participants', db.metadata,
                                  Column('users', GUID(), ForeignKey('tmuser.id')),
                                  Column('conversations', GUID(), ForeignKey('conversation.id'))
                                  )


class Conversation(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'conversation'

    messages = one_to_many('Message', backref='conversation', lazy='immediate', cascade='all, delete-orphan')
    users = relationship('User', secondary=conversation_participants, backref='conversations')
    conversation_name = db.Column(String(128, convert_unicode=True), nullable=True)

    def __init__(self, users=[]):
        self.users = users


class Message(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'message'
    sender_id = Column(GUID())
    content = Column(Text, nullable=False)

    ''' Message should be a dict at this point'''

    def __init__(self, conversation, sequence_number=0, content={}):
        c = json.dumps(content)
        self.content = c
        self.conversation = conversation

    @classmethod
    def delete(cls, message):
        db.session.delete(message)
