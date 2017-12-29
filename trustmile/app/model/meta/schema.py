import uuid

from geoalchemy2.elements import _SpatialElement
from sqlalchemy import Column, Table, DateTime, Boolean, String
from sqlalchemy import event
from sqlalchemy.orm import validates
from sqlalchemy.sql import functions
from geoalchemy2 import functions as geo_funcs
from sqlalchemy.ext.compiler import compiles
from validate_email import validate_email

from .types import GUID
from app import db
from geoalchemy2 import Geography, WKTElement, Geometry
from geoalchemy2.shape import to_shape
from app.model.meta.orm import one_to_many, one_to_one, many_to_one
from app.util import wkt_geog_element

class utcnow(functions.FunctionElement):
    key = 'utcnow'
    type = DateTime(timezone=True)


@compiles(utcnow)
def _default_utcnow(element, compiler, **kw):
    """default compilation handler.

    Note that there is no SQL "utcnow()" function; this is a
    "fake" string so that we can produce SQL strings that are dialect-agnostic,
    such as within tests.

    """
    return "utcnow()"


@compiles(utcnow, 'postgresql')
def _pg_utcnow(element, compiler, **kw):
    """Postgresql-specific compilation handler."""

    return "(CURRENT_TIMESTAMP AT TIME ZONE 'utc')::TIMESTAMP WITH TIME ZONE"


@event.listens_for(Table, "after_parent_attach")
def timestamp_cols(table, metadata, a=None):

    #The way SQL ALchemy handels inheritance, if a column exists on both the parent and child object
    #things get confused.  While it is valid SQL, in an ORM world there should only be one
    # if the object only has one copy what gets done in the SQL where the 1 property exists in 2 tables?
    #so it should only exist on the parent
    #
    # I tried to do this programmatic - but I could not get a reference to the parent object
    # So i've had to hard-code tables to exclude, to prevent these columns being on both the parent and child

    if table.name in ['user_address','consignment_address']:
        return

    if metadata is db.metadata:
        if not table.columns.get('created_at'):
            table.append_column(
                Column('created_at',
                            DateTime(timezone=True),
                            nullable=False, default=utcnow())
            )
        if not table.columns.get('updated_at'):
            table.append_column(
                Column('updated_at',
                            DateTime(timezone=True),
                            nullable=False,
                            default=utcnow(), onupdate=utcnow())
            )


class TableColumnsBase(object):
    """A mixin that adds a surrogate integer 'primary key' column named
    ``id`` to any declarative-mapped class."""

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

class EmailVerification(db.Model, TableColumnsBase):
    token = db.Column(db.String(10), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)

    def __init__(self, email, token):
        self.token = token
        self.email = email

    @validates('email_address')
    def validate_email(self, key, address):
        assert validate_email(address)
        return address

class UserTypeBase(object):
    password_reset_token = Column(GUID())
    password_reset_dt = Column(DateTime(timezone=True))
    email_verification_token = Column(GUID())
    email_verified = Column(Boolean, default=False)
    email_verification_dt = Column(DateTime(timezone=True))


class   Address(db.Model, TableColumnsBase):
    __tablename__ = 'address'
    addressLine1 = db.Column(String(255), default="", nullable=False, info="Street address, company name, c/o")
    addressLine2 = db.Column(String(255), default="", nullable=True, info="Apartment, suite, unit, building floor, etc")
    countryCode = db.Column(String(255), nullable=True, info="Country code such as AU, US etc")
    suburb = db.Column(String(255), nullable=True, info="Users suburb such as Elizabeth Bay")
    postcode = db.Column(String(32), nullable=True, info="Users postcode such as 2011 for Elizabeth Bay")
    state = db.Column(String(64), info="State for user such as NSW")
    phoneNumber = db.Column(String(255), default="", info="Phone number such as 0410 931 980")
    user_presence = one_to_many('UserPresence', backref='address', lazy='joined', cascade='all, delete-orphan',
                                order_by=lambda: UserPresence.created_at.desc())

    location = one_to_one('Location', backref='user_address', lazy='select', cascade='all, delete-orphan')
    discriminator = Column('type', String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}

    # def __init__(self, address_line_1, address_line_2, country_code, suburb, postcode, state):
    #     self.addressLine1 = address_line_1
    #     self.addressLine2 = address_line_2
    #     self.countryCode = country_code
    #     self.suburb = suburb
    #     self.postcode = postcode
    #     self.state = state

    def as_physical(self):
        pa = {   # TODO - stub, make it proper
            "latitude": self.location.latitude if self.location else '',
            "longitude": self.location.longitude if self.location else '',
            "unitNumber": '1',
            "streetNumber": self.addressLine1,
            "streetName": self.addressLine2,
            "streetType": 'street',
            "suburb": self.suburb,
            "postcode": self.postcode
        }
        return pa


class UserPresence(db.Model, TableColumnsBase):
    __tablename__ = 'user_presence'
    location = db.Column(Geography(geometry_type='POINT', srid=4326))
    status = db.Column(db.Boolean, default = False, info="True is at home, false not at home")


    def __init__(self, status, latitude, longitude):
        self.status = status
        self.location = wkt_geog_element(longitude, latitude)

    @property
    def latitude(self):
        return db.session.scalar(geo_funcs.ST_Y(self.location))

    @property
    def longitude(self):
        return db.session.scalar(geo_funcs.ST_X(self.location))


class Location(db.Model, TableColumnsBase):
    __tablename__ = "location"
    loc = db.Column(Geography(geometry_type='POINT', srid=4326))

    def __init__(self, latitude, longitude):
        self.loc = wkt_geog_element(longitude, latitude)

    @property
    def latitude(self):
        return to_shape(self.loc).y #db.session.scalar(geo_funcs.ST_Y(self.loc))

    @property
    def longitude(self):
        return to_shape(self.loc).x #db.session.scalar(geo_funcs.ST_X(self.loc))

    def to_json(self):
        return {
            'longitude': self.longitude,
            'latitude': self.latitude
        }


class FeedbackMessage(db.Model, TableColumnsBase):
    __tablename__ = 'user_feedback'
    user_email_address = Column(String(255), nullable=True)
    user_full_name = Column(String(255), nullable=True)
    feedback_message = Column(String(4000), nullable=True)
    user = many_to_one( 'User', backref='feedback_messages', cascade='all')

    def __init__(self, user_email_address, user_full_name, feedback_message, user):
        self.user_email_address = user_email_address
        self.user_full_name = user_full_name
        self.feedback_message = feedback_message
        self.user = user
