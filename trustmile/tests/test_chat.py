from app.messaging.model import Message, Conversation, db
from app.users.model import ConsumerUser
from nose.tools import eq_

__author__ = 'james'
from . import TransactionalTest


class TestChat(TransactionalTest):

    @classmethod
    def setUpClass(cls):
        conv = Conversation(users = [])
        m = Message(conv)
        super(TestChat, cls).setUpClass()



    def test_create_message_and_conversation(self):

        cu1 = ConsumerUser.create('jb1@cloudadvantage.com.au', '123123123')
        cu2 = ConsumerUser.create('jb2@cloudadvantage.com.au', '123123123')
        users = [c.user for c in (cu1, cu2)]
        conv = Conversation(users)
        m = Message(conv)
        self.session.add(conv)
        self.session.add(m)
        rs = self.session.query(Message).all()
        eq_(1, len(rs))
        msg = rs[0]
        r_conv = msg.conversation
        eq_(r_conv.id, conv.id)
        participants = conv.users
        eq_(len(participants), 2)
