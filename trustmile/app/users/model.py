from sqlalchemy.exc import StatementError
from sqlalchemy.sql.elements import and_

import config
from app.util import validate_email
import uuid
import os
import logging
from sqlalchemy import event, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import exc, validates
from app.model.meta.orm import one_to_many, UniqueMixin, one_to_one, many_to_one
from app.model.meta.types import GUID, String, BcryptType
from app import db
from app.model.meta.schema import Column, UserTypeBase, utcnow, Boolean,\
    TableColumnsBase, Address, EmailVerification
from app.exc import *
from app import util

__author__ = 'james'


logger = logging.getLogger()


class User(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'tmuser'
    # user_type = Column(Enum)

    # user_address = one_to_many('Address',  uselist= True, backref='user', lazy='immediate', cascade="all, delete-o)
    user_address = one_to_many('Address',  uselist= True, backref='user', lazy='immediate', order_by=lambda: Address.created_at.desc())
    at_home = db.Column(db.Boolean, default=False)

    consumer_user = one_to_one("ConsumerUser", backref="user", lazy='immediate', cascade="all, delete-orphan")
    courier_user = one_to_one("CourierUser", backref="user", lazy='immediate', cascade="all, delete-orphan")
    anonymous_user = one_to_one('AnonymousUser', backref='user', lazy='select', cascade='all, delete-orphan')

    installation_information = one_to_many('ApplicationInstallation', backref='user', lazy='immediate',
                                           cascade="all, delete-orphan")

    auth_sessions = one_to_many('AuthSession', backref='user', lazy='select', cascade='all, delete-orphan')

    user_consignments = one_to_many('UserConsignment', backref='user', lazy='select', cascade='all, delete-orphan' )

    preferences = db.Column(JSON, default=[])

    @property
    def is_trusted_neighbour(self):
        if self.trustmile_user:
            return True

    def update_preferences(self, preferences):
        combined = {}

        def safe_boolean(bool_val):
            result = bool_val
            if isinstance(bool_val, str) or isinstance(bool_val, unicode):
                if bool_val in (True, '1', 'true', 'True'):
                    result =  True
                elif bool_val in (False, '0', 'false', 'False'):
                    result = False
            return result
        new_preferences = {'values': []}
        if self.preferences:
            for p in self.preferences.get('values', []):
                combined[p['key']] = safe_boolean(p['value'])
        for p1 in preferences.get('values', []):
            combined[p1['key']] = safe_boolean(p1['value'])
        for k, v in combined.iteritems():

            new_preferences.get('values').append({'key': k, 'value': v})
        self.preferences = new_preferences

    def user_details_data(self):
        from app.users.serialize import UserAddressSchema, ConsumerUserSchema, CourierUserSchema
        """return user info as in GET /consumer/account call"""
        user_details = self.get_user_details()
        user_addresses = self.user_address
        preferences = self.preferences
        user_addr = None
        if len(user_addresses) > 0:
            s_user_addresses = sorted(user_addresses, cmp=util.create_dates_asc_cmp, reverse=True)
            user_addr = s_user_addresses[0]
        ud_schema = None
        if isinstance(user_details, ConsumerUser):
            ud_schema = ConsumerUserSchema()
        else:
            ud_schema = CourierUserSchema()

        user_details_data = ud_schema.dump(user_details).data
        user_details_data['preferences'] = preferences
        if user_addr:
            user_addr_data = UserAddressSchema().dump(user_addr).data
            user_details_data['accountAddress'] = user_addr_data

        return user_details_data

    def get_user_details(self):
        if self.consumer_user:
            return self.consumer_user
        elif self.courier_user:
            return self.courier_user
        else:
            raise Exception(u'No consumer details found')

    @property
    def current_address(self):

        current_address = None
        if len(self.user_address) > 0:
            current_address = self.user_address[0]
        return current_address

    def get_consignments(self):
        #returns the consignments this user has,
        #and adds in the user_description to the consignment
        ret = []
        for uc in self.user_consignments:
            cons = uc.consignment
            cons.user_description = uc.user_description
            cons.retailer_name = uc.retailer_name
            ret.append(cons)
        ret.sort(key=lambda c: c.updated_at, reverse=True)
        return ret

    def add_consignment(self, consignment, user_description=None, retailer_name=None):
        #adds a consignment to a user, if it does not exist

        exists = False
        for uc in self.user_consignments:
            if uc.consignment == consignment:
                exists = True
                if user_description:
                    uc.user_description = user_description
                if retailer_name:
                    uc.retailer_name = retailer_name
                break
        if not exists:
            self.user_consignments.append(UserConsignment(consignment, user_description, retailer_name))

    def delete_consignment(self, consignment_id):
        self.user_consignments = [ uc for uc in self.user_consignments if str(uc.consignment.id) != consignment_id]

    @classmethod
    def delete(cls, user):
        db.session.delete(user)

    # @classmethod
    # def new_consumer_user(cls, consumer_user, name=''):
    #     user = User()
    #     user.consumer_user = consumer_user
    #     consumer_user.fullName = name
    #     return user

    @classmethod
    def new_courier_user(cls, courier_user):
        user = User()
        user.courier_user = courier_user
        return user

    @classmethod
    def get_for_email_verification(cls, verification_code):
        try:
            if not len(verification_code) > 10:
                evs = EmailVerification.query.filter(EmailVerification.token == verification_code).all()

            if len(evs) == 0 and len(verification_code) > 10:
                q = ConsumerUser.query.filter(ConsumerUser.email_verification_token == verification_code)
            else:
                q = ConsumerUser.query.filter(ConsumerUser.email_address.in_(e.email for e in evs))

            users = q.all()

            if len(users) > 1:
                logger.warn(u"Should not be more than one user for email verification code: {0}, user uuids {1}".format(
                    verification_code, ", ".join(users)))
            if len(users) > 0:
                user = users[0]
            else:
                raise Exception("No user found for token <{0}>".format(verification_code))

            user_uuid = user.id

            logger.debug(u"User {0} found for email verification code {1} entities found {0}".format(user_uuid, verification_code))
        except exc.NoResultFound:
            logger.error(u"No item found for identifier {0}".format(verification_code))
            return None

        return user_uuid





class UserAddress(Address, UniqueMixin, TableColumnsBase):
    __tablename__ = 'user_address'
    __mapper_args__ = {'polymorphic_identity': 'useraddress'}
    id = Column(GUID(), ForeignKey('address.id'), primary_key=True)

    # def __init__(self, address_line_1, address_line_2, country_code, suburb, postcode, state):
    #     Address.__init__(self, address_line_1, address_line_2, country_code, suburb, postcode, state)

# parsed the tracking_info that we receive from aftership
@event.listens_for(UserAddress.user_presence, 'append')
def set_user_presence(target, value, initiator):
    if value == None:
        return

    if target.user:
        target.user.at_home = value.status


@event.listens_for(User.user_address, 'append')
def handle_address_preferences(target, value, initiator):
    if value == None:
        return
    if target:
        if value.postcode:
            if value.postcode in config.ENABLED_POSTCODES:
                logger.debug('Setting regionNeighbourEnabled = True for user id {0}'.format(target.id))
                target.update_preferences({'values': [{'key': 'regionNeighbourEnabled', 'value': True}]})
            else:
                logger.debug('Setting regionNeighbourEnabled = False for user id {0}'.format(target.id))
                target.update_preferences({'values': [{'key': 'regionNeighbourEnabled', 'value': False}]})


class UserConsignment(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'user_consignment'
    consignment = many_to_one('Consignment', backref="user_consignments", lazy="joined")
    user_description = db.Column(db.String(255))
    #Whats this consignment assigned to this user by the user, or via the retailer integration
    #has values of either 'user' or 'retailer'
    created_by = db.Column( db.String(15))

    user_role = db.Enum("OWNER","COLLECTOR", "NONE", )

    retailer_name = db.Column(db.String(255))

    #TODO: find out how to make consumer_user and consignment the primary key
    def __init__(self, consignment, user_description, retailer_name = None ):
        #NB we don't need to take in a user, as
        #sqlalchemy will set it for us when the UserConsignment is added to a User
        self.consignment = consignment
        self.user_description = user_description
        self.retailer_name = retailer_name


class ApplicationInstallation(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'installation_information'

    OSType = Column(String(128), nullable=False)
    OSMinorVersion = Column(String(128))
    DeviceIdentifier = Column(String(255))
    ApplicationVersion = Column(String(128))
    OSMajorVersion = Column(String(128))
    pushNotificationToken = Column(String(500))
    pushNotificationEnabled = Column(Boolean)


class AnonymousUser(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'anonymous_user'
    device_id = db.Column(db.String(512), nullable=False, default='')

    def __init__(self, device_id):
        self.device_id = device_id

    @classmethod
    def create(cls, installation_information):
        if isinstance(installation_information, ApplicationInstallation):
            device_id = installation_information.DeviceIdentifier
            auser = AnonymousUser(device_id)
            user = User()
            user.anonymous_user = auser
            db.session.add(user)
            db.session.add(auser)
            return auser
        else:
            raise InvalidParameterException('ApplicationInstallationInformation parameter type required')


class ConsumerUser(db.Model, UniqueMixin, TableColumnsBase, UserTypeBase):
    __tablename__ = 'consumer_user'

    email_address = db.Column(db.String(50), unique=True, info="This is the users email address")
    secret = db.Column(BcryptType, nullable=False)
    fullName = db.Column(db.String(255), nullable=True, info='Users full name such as James ORourke')
    trusted_neighbour = db.Column(db.Boolean, default=False, info='This indicates if the user has opted in to receive for neighbours')

    @validates('secret')
    def validate_password(self, key, secret):
        if len(secret) < 8:
            raise InsecurePasswordException(u"Passwords must be of length 8 or more")
        return secret

    def reset_password(self):
        self.secret = "".join("%.2x" % ord(x) for x in os.urandom(32))
        self.password_reset_token = uuid.uuid4()
        return self.password_reset_token

    @validates('email_address')
    def validate_email(self, key, email_address):
        return validate_email(email_address)

    def __init__(self, email_address, secret, name):
        self.email_address = email_address
        self.secret = secret
        self.fullName = name or None

    @classmethod
    def unique_hash(cls, email_address):
        return email_address

    @classmethod
    def unique_filter(cls, query, email_address):
        return query.filter(cls.email_address == email_address)

    @classmethod
    def find_reset_token(cls, reset_token):
        # should return 0 or 1.  exception otherwise.
        if reset_token == None or len( reset_token.strip()) == 0:
            return None

        try:
            return db.session.query( ConsumerUser ).filter(ConsumerUser.password_reset_token == reset_token).first()
        except StatementError, e:
            return None

    @classmethod
    def create(cls, email_address, secret, device_identifier = None, name = None, **kwargs):
        cuser = ConsumerUser(email_address, secret, name)

        anoncheck = False
        if device_identifier is not None:
            anonlist = AnonymousUser.query.filter(AnonymousUser.device_id == device_identifier).all()
            if anonlist:
                user = anonlist[0].user
                anoncheck = True

        if anoncheck:
            user.consumer_user = cuser
        else:
            user = User()
            user.consumer_user = cuser
            db.session.add(user)

        db.session.add(cuser)
        return cuser

    def as_consumer(self):
        ar = {
            "fullName": self.fullName,
            "email": self.email_address,
            "consumerId": str(self.id),
            "phoneNumber": self.user.current_address.phoneNumber if
                self.user.current_address else '',
            "physicalAddress": (self.user.current_address.as_physical()
                    if self.user.current_address else {})
        }
        return ar
    @classmethod
    def get(cls, email_address):
        return db.session.query( ConsumerUser).filter( ConsumerUser.email_address == email_address).first()

class NeighbourSignup(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'neighbour_signup'

    name = db.Column(db.String(50), unique=False, info="This is the users email address")
    email_address = db.Column(db.String(50), unique=False, info="This is the users email address")
    addressLine1 = db.Column(String(255), default="", nullable=False, info="Street address, company name, c/o")
    addressLine2 = db.Column(String(255), default="", nullable=True, info="Apartment, suite, unit, building floor, etc")
    suburb = db.Column(String(255), nullable=True, info="Users suburb such as Elizabeth Bay")
    postcode = db.Column(String(32), nullable=True, info="Users postcode such as 2011 for Elizabeth Bay")
    state = db.Column(String(64), info="State for user such as NSW")
    phoneNumber = db.Column(String(255), default="", info="Phone number such as 0410 931 980")
    over18 = db.Column( Boolean(), nullable=False )
    hasIPhone = db.Column( Boolean(), nullable=False )
    workStatus = db.Column(String(255), default="", info="Phone number such as 0410 931 980")

    @classmethod
    def get_all(cls):
        return db.session.query(NeighbourSignup).filter().all()


@event.listens_for(User.preferences, 'set')
def update_preferences_setter(target, value, oldvalue, initiator):
    if isinstance(value, dict):
        preferences = value['values']
        for d in preferences:
            if d['key'] == 'neighbourEnabled':
                cu = target.get_user_details()
                if isinstance(cu, ConsumerUser) and d['value']:
                    cu.trusted_neighbour = True


#ensures that any password reset tokens are cleared after a new password has been set
@event.listens_for(ConsumerUser.secret, 'set')
def set_password_reset_date(target, value, oldvalue, initiator):
    target.password_reset_dt = None
    target.password_reset_token = None


@event.listens_for(ConsumerUser.password_reset_token, 'set')
def set_password_reset_date(target, value, oldvalue, initiator):
    if value == None or len(str(value).strip()) == 0:
        target.password_reset_dt = None
    else:
        target.password_reset_dt = utcnow()


@event.listens_for(ConsumerUser.email_verification_token, 'set')
def clear_email_verification_date(target, value, oldvalue, initiator):
    target.email_verification_dt = None
    target.email_verified = False


class CourierUser(db.Model, UniqueMixin, TableColumnsBase, UserTypeBase):
    __tablename__ = 'courier_user'

    username = Column(String(50), unique=True, nullable=False, info="This is courier users username")
    secret = Column(BcryptType, nullable=False)
    fullName = Column(String(255), nullable=True, info='Users full name such as James ORourke')
    email_address = Column(String(128),  info="This is courier users email address")
    deliveries = one_to_many('TrustmileDelivery', lazy='select', cascade="all, delete-orphan", backref='courier')

    @validates('secret')
    def validate_password(self, key, secret):
        if len(secret) < 8:
            raise InsecurePasswordException(u"Passwords must be of length 8 or more")
        return secret

    def reset_password(self):
        self.secret = "".join("%.2x" % ord(x) for x in os.urandom(32))
        self.password_reset_token = uuid.uuid4()
        return self.password_reset_token

    @validates('email_address')
    def validate_email(self, key, email_address):
        return validate_email(email_address)

    def __init__(self, username, secret, fullname):
        self.username = username
        self.secret = secret
        self.fullName = fullname

    @classmethod
    def unique_hash(cls, username):
        return username

    @classmethod
    def unique_filter(cls, query, username):
        return query.filter(cls.username == username)

    @classmethod
    def create(cls, username, secret, fullname, courier):
        cuser = CourierUser(username, secret, fullname)
        user = User.new_courier_user(cuser)
        cuser.courier = courier
        db.session.add(user)
        db.session.add(cuser)
        return cuser


@event.listens_for(ConsumerUser.email_verified, 'set')
def set_email_verified_date(target, value, oldvalue, initiator):
    target.email_verification_dt = utcnow()

@event.listens_for(CourierUser.password_reset_token, 'set')
def set_password_reset_date(target, value, oldvalue, initiator):
    target.password_reset_dt = utcnow()


@event.listens_for(CourierUser.email_verification_token, 'set')
def clear_courier_email_verification_date(target, value, oldvalue, initiator):
    target.email_verification_dt = None
    target.email_verified = False


# TODO verify it's a valid email address before doing anything!
def get_user_by_email(email_address):
    cu = None
    try:
        consumer_user = db.session.query(ConsumerUser).filter_by(email_address=email_address).one()
        cu = consumer_user

    except exc.NoResultFound:
        logger.debug(u"No consumer found with email {0}".format(email_address))

    if not cu:
        try:
            courier_user = db.session.query(CourierUser).filter_by(email_address=email_address).one()
            cu = courier_user
        except exc.NoResultFound:
            logger.debug(u"No consumer found with email {0}".format(email_address))

    return cu


class AuthSession(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'auth_session'

    token = Column(String(64), index=True, nullable=False)
    valid = Column(Boolean, nullable=False, default=True)
    # user = many_to_one("User", backref="auth_session",
    #                    lazy='immediate')

    def __init__(self, user, valid=True):
        self.user = user
        self.token = self._gen_token()
        self.valid = valid

    def get_user(self):
        try:
            return User.query.filter_by(id=self.user.id).one()
        except exc.NoResultFound:
            return None

    @classmethod
    def _gen_token(cls):
        return "".join("%.2x" % ord(x) for x in os.urandom(32))

    @classmethod
    def validate_token(cls, auth_token):
        try:
          return AuthSession.query.\
                filter_by(token=auth_token).one()
        except exc.NoResultFound:
            return None

    @classmethod
    def invalidate_token(cls, auth_token):
        try:
            auth_sess = AuthSession.query.filter(AuthSession.token == auth_token).one()
            db.session.delete(auth_sess)
        except exc.NoResultFound:
            s = u"No session found for API key {0}".format(auth_token)
            logger.error(s)
            raise EntityNotFoundException(s)



    # TODO: What if courier user has same email - very unlikely so don't worry for now
    @classmethod
    def create(cls, username, secret):
        cu  = None
        logger.debug(u"creating authsession for {0}".format(username))
        try:
            cu = ConsumerUser.query.filter_by(email_address=username).one()
        except exc.NoResultFound:
            logger.debug(u"Consumer user not found for username {0}".format(username))
            try:
                cu = CourierUser.query.filter_by(username=username).one()
            except exc.NoResultFound:
                logger.debug(u"Courier user not found for username {0}".format(username))
                cu = None
        auth_session = cls.check_secret(cu, secret)

        return auth_session

    @classmethod
    def create_anonymous_auth_session(cls, anon_user):
        logger.debug(u'creating anonymous authsession for device {0}'.format(anon_user.device_id))
        auth_session = AuthSession(anon_user.user, valid=True)
        db.session.add(auth_session)
        return auth_session


    @classmethod
    def create_for_courier(cls, username, secret):
        logger.debug(u"creating authsession for {0}".format(username))
        try:
            cu = CourierUser.query.filter_by(username=username).one()
        except exc.NoResultFound:
            logger.debug(u"Courier user not found for username {0}".format(username))
            cu = None
        auth_session = cls.check_secret(cu, secret)

        return auth_session

    @classmethod
    def check_secret(cls, cu, secret):
        auth_session = None
        if cu and cu.secret == secret:
            logger.debug(u"Retrieved user {0}".format(str(cu.id)))
            logger.debug(u"Password match")
            auth_session = AuthSession(cu.user)
            db.session.add(auth_session)
        return auth_session




