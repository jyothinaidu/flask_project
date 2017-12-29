import uuid

import bcrypt
from sqlalchemy import Table, select, Column
from sqlalchemy import MetaData

from nose.tools import assert_true, raises
from sqlalchemy import and_

from app.deliveries.model import Courier
from app.model.meta.types import BcryptType, Password, GUID
from app.exc import InvalidEmailException, EntityNotFoundException
from app.exc import InsecurePasswordException
from app.users.model import User, ConsumerUser, CourierUser, AuthSession, UserAddress, db
from app.model.meta.schema import UserPresence, Location, EmailVerification
from . import AppTest
from tests import TransactionalTest
from tests.util import load_couriers

email_address = 'james@cloudadvantage.com.au'
username = 'james'
full_name = "James O'Rourke"
test_password = 'mypassword'


class UserTest(TransactionalTest):
    @classmethod
    def setUpClass(cls):
        super(UserTest, cls).setUpClass()
        load_couriers()
        db.session.commit()

    def setUp(self):
        super(UserTest, self).setUp()

    def test_create_user(self):
        user = User()
        db.session.add(user)

    def test_create_consumer_user(self):
        cu = ConsumerUser.create(email_address, test_password)
        assert cu.email_address == email_address
        assert cu.secret == test_password

    def test_create_courier_user(self):
        courier = Courier.query.filter(Courier.courier_slug == 'couriers-please').one()
        cu = CourierUser.create(username, test_password, full_name, courier)
        assert cu.username == username
        assert cu.secret == test_password


    # def test_old_email_verification(self):
    #     cu = ConsumerUser.create(email_address, test_password)
    #     cu.email_verification_token = uuid.uuid4()
    #     assert cu.email_address == email_address
    #     assert cu.secret == test_password
    #
    #     result = User.get_for_email_verification(cu.email_verification_token)
    #
    #     cu = ConsumerUser.query.get(result)
    #     assert cu.email_verification_token is not None
    #     cu.email_verified = True
    #
    #     assert cu.email_verified

    def test_email_verification(self):
        cu = ConsumerUser.create(email_address, test_password)
        from app import util
        token = util.gen_random_str(10)
        ev = EmailVerification(email_address, token)
        db.session.add(ev)
        assert cu.email_address == email_address
        assert cu.secret == test_password

        result = User.get_for_email_verification(token)
        cu = ConsumerUser.query.get(result)


    def test_auth_session(self):
        cu = ConsumerUser.create(email_address, test_password)
        auth_sess = AuthSession.create(email_address, test_password)
        assert auth_sess is not None
        print auth_sess.valid
        assert_true(auth_sess.valid)
        assert auth_sess.user is not None
        assert auth_sess.token is not None
        AuthSession.invalidate_token(auth_sess.token)

    @raises(EntityNotFoundException)
    def test_invalidate_failure(self):
        cu = ConsumerUser.create(email_address, test_password)
        auth_sess = AuthSession.create(email_address, test_password)
        assert auth_sess is not None
        print auth_sess.valid
        assert_true(auth_sess.valid)
        assert auth_sess.user is not None
        assert auth_sess.token is not None
        AuthSession.invalidate_token(auth_sess.token)
        AuthSession.invalidate_token(auth_sess.token)


    #
    #
    # def test_location(self):
    #     loc = UserPresence(True, -33.8717550, 151.2287690)
    #     db.session.add(loc)
    #
    #     results = db.session.query(UserPresence).filter(and_(UserPresence.latitude < -30.000, UserPresence.longitude > 150.0000)).all()
    #     assert len(results) > 0
    #     results = db.session.query(UserPresence).filter(and_(UserPresence.latitude < -35.000, UserPresence.longitude > 155.0000)).all()
    #     assert len(results) == 0

    def test_user_address(self):
        addr = UserAddress()
        addr.addressLine1 = 'c/o Arthur Skittle'
        addr.addressLine2 = '12 Smith St'
        addr.countryCode = 'US'
        addr.suburb = 'San Francisco'
        addr.location = Location(-33.8717550, 151.2287690)
        addr.postcode = '94110'
        addr.state = 'CA'
        user = User()
        user.user_address.append(addr)
        db.session.add(addr)
        assert addr.user is not None
        assert len(user.user_address) > 0

    @raises(InvalidEmailException)
    def test_validate_email(self):
        ConsumerUser.create('james@foobar..co', test_password)

    @raises(InsecurePasswordException)
    def test_valid_password(self):
        ConsumerUser.create(email_address, 'abcd12')


class GUIDTest(AppTest):
    def setUp(self):
        super(GUIDTest, self).setUp()

        self.guid_table = Table('guid_table', MetaData(),
                                Column('guid_value', GUID())
                                )

        self.guid_table.create(db.session.bind)

    def tearDown(self):
        super(GUIDTest, self).tearDown()
        db.session.rollback()
        self.guid_table.drop(db.session.bind)

    def test_round_trip(self):
        my_guid = uuid.uuid4()
        db.session.execute(self.guid_table.insert(), dict(guid_value=my_guid))

        self.assertEquals(
            db.session.scalar(select([self.guid_table.c.guid_value])),
            my_guid
        )


class BcryptTypeTest(TransactionalTest):
    def setUp(self):
        super(BcryptTypeTest, self).setUp()

        self.bc_table = db.Table('bc_table', MetaData(),
                                 db.Column('bc_value', BcryptType)
                                 )

        self.bc_table.create(db.session.bind)

    def tearDown(self):
        super(BcryptTypeTest, self).tearDown()
        self.bc_table.drop(db.session.bind)

    def test_round_trip(self):
        db.session.execute(self.bc_table.insert(), dict(bc_value="hello"))

        result = db.session.scalar(select([self.bc_table.c.bc_value]))
        self.assertEquals(result, "hello")
        self.assertEquals(result, Password("hello", result))
        self.assertNotEquals(result, "bye")


class PasswordTest(AppTest):
    def test_password_wrapper_string_cmp(self):
        p1 = Password("abcdef")

        self.assertEquals(p1, "abcdef")
        self.assertNotEquals(p1, "qprzt")

    def test_password_wrapper_pw_cmp(self):
        p1 = Password("abcdef")

        # compare to self
        self.assertEquals(p1, p1)

        # compare to a comparable Password
        self.assertEquals(p1, Password("abcdef", p1))
        self.assertNotEquals(p1, Password("qprzt", p1))

    def test_password_wrapper_conversion(self):
        p1 = Password("abcdef")
        raw = str(p1)
        self.assertEquals(raw, bcrypt.hashpw("abcdef", raw))

    def test_password_type(self):
        self.assertEquals(
            BcryptType().process_bind_param("abcdef", None),
            "abcdef"
        )
