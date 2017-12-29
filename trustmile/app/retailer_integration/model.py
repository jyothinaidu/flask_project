from sqlalchemy import DateTime, Boolean, ForeignKey, event, or_, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import load_only
from sqlalchemy.exc import StatementError
import os
from app.model import GUID, relationship
from app.model.meta.orm import UniqueMixin, many_to_one, one_to_many, one_to_one
from app.model.meta.schema import TableColumnsBase, utcnow
from app.model.meta.types import BcryptType, String
__author__ = 'aaron'

import uuid
from app import db
from sqlalchemy.orm import exc, validates, backref
import logging
from app.exc import *

logger = logging.getLogger()


class RetailerAuthSession(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'retailer_auth_session'

    token = db.Column(String(64), index=True, nullable=False)
    valid = db.Column(Boolean, nullable=False, default=True)
    # user = many_to_one("User", backref="auth_session",
    #                    lazy='immediate')

    def __init__(self, retailer, valid=True):
        self.retailer = retailer
        self.token = self._gen_token()
        self.valid = valid

    def get_retailer(self):
        try:
            return Retailer.query.filter_by(id=self.retailer.id).one()
        except exc.NoResultFound:
            return None

    @classmethod
    def _gen_token(cls):
        return "".join("%.2x" % ord(x) for x in os.urandom(32))

    @classmethod
    def validate_token(cls, auth_token):
        try:
          return RetailerAuthSession.query.\
                filter_by(token=auth_token).one()
        except exc.NoResultFound:
            return None

    @classmethod
    def invalidate_token(cls, auth_token):
        try:
            auth_sess = RetailerAuthSession.query.filter(RetailerAuthSession.token == auth_token).one()
            db.session.delete(auth_sess)
        except exc.NoResultFound:
            s = u"No session found for Retailer API key {0}".format(auth_token)
            logger.error(s)
            raise EntityNotFoundException(s)



    @classmethod
    def create(cls, retailer_emailAddress, secret):
        cu  = None
        logger.debug(u"creating retailer authsession for {0}".format(retailer_emailAddress))
        try:
            retailer = Retailer.query.filter_by(contact_emailAddress=retailer_emailAddress).one()
        except exc.NoResultFound:
            logger.debug(u"Retailer user not found for email address {0}".format(retailer_emailAddress))
            return None

        auth_session = cls.check_secret(retailer, secret)

        return auth_session


    @classmethod
    def check_secret(cls, retailer, secret):
        auth_session = None
        if retailer and retailer.secret == secret:
            logger.debug(u"Retrieved retailer {0}".format(str(retailer.id)))
            logger.debug(u"Password match")
            auth_session = RetailerAuthSession(retailer)
            db.session.add(auth_session)
        return auth_session


class Retailer(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'retailer'

    website_name = db.Column(db.String(255)) #name of the retailer.  DUplicate from the name set in umbraco
    website_url = db.Column( db.String(255))
    umbraco_id = db.Column( db.String(36)) #a link back to the retailer in Umbraco # depricated
    email_integration_configuration = db.Column(JSON, default={})
    email_server_configuration = db.Column(JSON, default={})
    courier_mappings = db.Column(JSON, default=[])
    slug = db.Column(db.String(255))
    help_url = db.Column(db.String(255))
    shopify_hmac_key = db.Column(db.String(255))
    shopify_store_domain = db.Column(db.String(255)) #this is the domain used to match a shopify webhook post to a retailer
                                                    #differs from website_url by the absennce of http(s):// etc.
                                                    # this must match exactly.
    contact_firstName = db.Column(db.String(255))
    contact_lastName = db.Column(db.String(255))
    contact_phoneNumber = db.Column(db.String(255))
    contact_emailAddress = db.Column(db.String(255))
    secret = db.Column(BcryptType, default='', nullable=False)
    retailer_attributes = db.Column(JSON, default=None)

    seal_id = db.Column( db.String(12));
    seal_enabled = db.Column( Boolean, nullable=False, default=True)
    #default_late_delivery_days = db.Column(db.Float(53))

    auth_sessions = one_to_many('RetailerAuthSession', backref='retailer', lazy='select', cascade='all, delete-orphan')

    password_reset_token = db.Column(GUID())
    password_reset_dt = db.Column(DateTime(timezone=True))

    def __init__(self, website_name, umbraco_id=None, config=None):
        self.website_name = website_name
        self.umbraco_id = umbraco_id
        self.email_integration_configuration = config

    @classmethod
    def get_all(cls):
        return db.session.query(Retailer).all()

    @classmethod
    def get_all_ids(cls):
        return db.session.query(Retailer).options( load_only( 'id' ) ).all()

    @classmethod
    def get_shopify_retailer(cls, shopify_domain):
        return db.session.query(Retailer).filter( Retailer.shopify_store_domain == shopify_domain ).first()

    @classmethod
    def find_courier_mapping(cls, source_courier_name):

        cmd = text('select courierName from '\
            '( ' \
              'select json_array_elements(courier_mappings)->> \'sourceText\' AS sourceName ' \
               ', json_array_elements(courier_mappings)->>\'courierName\' AS courierName ' \
              'from retailer) AS aa ' \
            'where sourceName = :sourceName ' )

        result = db.engine.execute(cmd, sourceName = source_courier_name).fetchone()

        if result:
            return result['couriername']

        return None

    @classmethod
    def get(cls, id=None, umbraco_id=None, website_name=None, contact_emailAddress=None, website_url=None, seal_id=None):
        """

        :param id:
        :param umbraco_id:
        :param website_name:
        :param contact_emailAddress:
        :param website_url:
        :return: Retailer
        """
        if id:
            return db.session.query(Retailer).filter( Retailer.id == id).first()

        if umbraco_id:
            return db.session.query(Retailer).filter( Retailer.umbraco_id == umbraco_id).first()

        if website_name:
            return db.session.query(Retailer).filter( Retailer.website_name == website_name).first()

        if contact_emailAddress:
            return db.session.query(Retailer).filter( Retailer.contact_emailAddress == contact_emailAddress).first()

        if website_url:
            return db.session.query(Retailer).filter( Retailer.website_url == website_url).first()

        if seal_id:
            return db.session.query(Retailer).filter( Retailer.seal_id == seal_id).first()


        raise "id is None and umbracoID is None and website_name is None and contact_emailAddress is None and website_url is None"


    @classmethod
    def find_reset_token(cls, reset_token):
        # should return 0 or 1.  exception otherwise.
        if reset_token == None or len( reset_token.strip()) == 0:
            return None

        try:
            return db.session.query( Retailer ).filter(Retailer.password_reset_token == reset_token).first()
        except StatementError, e:
            return None


    def reset_password(self):
        self.password_reset_token = uuid.uuid4()
        return self.password_reset_token


@event.listens_for(Retailer.secret, 'set')
def set_password_reset_date(target, value, oldvalue, initiator):
    target.password_reset_dt = None
    target.password_reset_token = None


@event.listens_for(Retailer.password_reset_token, 'set')
def set_password_reset_date(target, value, oldvalue, initiator):
    if value == None or len(str(value).strip()) == 0:
        target.password_reset_dt = None
    else:
        target.password_reset_dt = utcnow()


class RetailerGlobalSettings(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'retailer_global_settings'

    tracking_number_regex = db.Column(JSON, default=None)
    # [
    #     {
    #         'RegEx': '^IZ[0-9]+$',
    #         'Courier Name': 'Couriers Please'
    #     }
    # ]
    shopify_courier_mapping = db.Column(JSON, default=[])
    # not sure if this is needed, but it's here
    # [
    #     {
    #         'tracking_company': 'UPS',
    #         'courier_name': 'The Trustmile Courier Name'
    #     }
    # ]

    @classmethod
    def get(cls):
        return db.session.query( RetailerGlobalSettings).one()

    @classmethod
    def get_shopify_courier_mapping(cls, shopify_courier_name):
        rgs = cls.get()
        if rgs.shopify_courier_mapping:
            for mapping in rgs.shopify_courier_mapping:
                if mapping.get('tracking_company') and mapping.get('courier_name'):
                    if mapping['tracking_company'] == shopify_courier_name:
                        return mapping['courier_name']

        return None



class RetailerTrackingEmail(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'retailer_tracking_email'

    retailer = many_to_one('Retailer',  backref='tracking_emails', lazy='select')
    email_sent_date = db.Column(DateTime(timezone=True))
    external_email_id = db.Column(db.String(255), nullable=True) #this is the ID of the email in the external email server
    to_email_address =  db.Column(db.String(255), nullable=False)
    from_email_address = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(1000), nullable=True) #There is no limit to the subject length of emails.  The number 998 comes up in RFC's as the maximum line length, but this is not an absolute length
    body = db.Column( db.Text() )


    @classmethod
    def create(cls, retailer, uid, from_address, to_address, subject, date, body ):
        rte = RetailerTrackingEmail()
        rte.retailer = retailer
        rte.email_sent_date = date
        rte.external_email_id = uid
        rte.to_email_address = to_address
        rte.from_email_address = from_address
        rte.subject = subject
        rte.body = body

        db.session.add( rte )
        db.session.commit()

        return rte









class RetailerShopifyTracking(db.Model, UniqueMixin, TableColumnsBase):
    __tablename_ = 'retailer_shopify_tracking'

    retailer = many_to_one('Retailer',  backref='shopify_tracking', lazy='select')
    shopify_topic =  db.Column(db.String(255), nullable=False)
    to_email_address =  db.Column(db.String(255), nullable=False)
    order_id = db.Column(db.String(255))
    destination = db.Column(JSON, default=None)
    courier_string = db.Column(db.String(255))  #raw string from shopify.  This is a logging thing, hence why we are not matching to the courier
    tracking_numbers =db.Column(JSON, default=None)





class RetailerIntegrationConsignment(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'retailer_integration_consignment'

    retailer = many_to_one('Retailer',  backref='integration_consignments', lazy='select')
    retailer_tracking_email = many_to_one('RetailerTrackingEmail', backref='integration_consignments') #this is the email the
    retailer_shopify_tracking = many_to_one('RetailerShopifyTracking', backref='shopify_consignments')
    email_address = db.Column(db.String(255), nullable=False)
    order_id = db.Column(db.String(255))
    tracking_number = db.Column(db.String(255), nullable=False)
    courier_id = db.Column(GUID(), ForeignKey('courier.id'))
    courier = relationship('Courier', backref='integration_consignments', lazy='select')

    consignment = one_to_one('Consignment', backref='integration_consignment', lazy='joined')

    #consignment_id_ri_fkey = db.Column(GUID(), ForeignKey('consignment.id'))

    def __init__(self, retailer=None, retailer_tracking_email=None, email_address=None, order_id=None,
                 tracking_number=None, courier=None):
        self.retailer = retailer
        self.retailer_tracking_email = retailer_tracking_email
        self.email_address = email_address
        self.order_id = order_id
        self.tracking_number = tracking_number
        self.courier = courier

    @classmethod
    def get_by_email_address(cls, email_address):
        return db.session.query(RetailerIntegrationConsignment).filter(
            RetailerIntegrationConsignment.email_address == email_address).all()



class RetailerSealAudit(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'retailer_seal_audit'

    retailer = many_to_one( 'Retailer', backref='seal_audits')
    question_code = db.Column( db.String(10), nullable=False)
    question_text = db.Column( db.String(255), nullable=False)
    answer = db.Column( db.Boolean, nullable=False, default=False)
    additional_information = db.Column( db.String(255), nullable=True)
    additional_information_approved = db.Column( db.Boolean, nullable=True)
