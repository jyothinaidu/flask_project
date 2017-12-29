import unittest
from app import db


class AppTest(unittest.TestCase):
    pass


class TransactionalTest(AppTest):
    """Run tests against a relational database within a transactional boundary.
    """

    @classmethod
    def setUpClass(cls):
        super(TransactionalTest, cls).setUpClass()
        cls.db = db
        db.drop_all()
        cls.db.create_all()

    @classmethod
    def tearDownClass(cls):
        super(TransactionalTest, cls).tearDownClass()
        db.session.remove()
        db.drop_all()
        # db.get_engine(cls.app).dispose()

    def setUp(self):
        super(TransactionalTest, self).setUp()

    def tearDown(self):
        super(TransactionalTest, self).tearDown()
        db.session.rollback()
        db.session.close()

    @property
    def session(self):
        return self.__class__.db.session
