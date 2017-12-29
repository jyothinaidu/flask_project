from geoalchemy2 import Geography
from geoalchemy2 import functions as geo_funcs
from marshmallow import fields
from marshmallow_sqlalchemy import ModelSchema, convert, ModelConverter
from sqlalchemy.dialects import postgresql

from app import db
from app.deliveries.model import Courier, Consignment, ConsignmentAddress
from app.model.meta.schema import Address, Location
from app.users.model import AuthSession, UserAddress, CourierUser, ConsumerUser, ApplicationInstallation, User
from app.util import wkt_geog_element

__author__ = 'james'

convert.ModelConverter.SQLA_TYPE_MAPPING.update({postgresql.JSON: fields.Raw})
# convert.ModelConverter.SQLA_TYPE_MAPPING.update({Geography: fields.Dict})
class GeoConverter(ModelConverter):
    SQLA_TYPE_MAPPING = ModelConverter.SQLA_TYPE_MAPPING.copy()
    SQLA_TYPE_MAPPING.update({
        Geography: fields.Str
    })


def get_location(value):
    return {'latitude': db.session.scalar(geo_funcs.ST_Y(value)),
            'longitude':  db.session.scalar(geo_funcs.ST_X(value))}

class GeographySerializationField(fields.String):
    def _serialize(self, value, attr, obj):
        if value is None:
            return value
        else:
            if attr == 'loc':
                return get_location(value)
            else:
                return None

    def _deserialize(self, value, attr, data):
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :param value: The value to be deserialized.
        :param str attr: The attribute/key in `data` to be deserialized.
        :param dict data: The raw input data passed to the `Schema.load`.
        :raise ValidationError: In case of formatting or validation failure.
        :return: The deserialized value.

        .. versionchanged:: 2.0.0
            Added ``attr`` and ``data`` parameters.
        """
        if value is None:
            return value
        else:
            if attr == 'loc':
                return wkt_geog_element(value.get('longitude'), value.get('latitude'))
            else:
                return None


class LocationSerializationField(fields.Field):

    def _serialize(self, value, attr, obj):
        if value is None:
            return value
        else:
            if attr == 'location':

                return get_location(value.loc)
            else:
                return None


class UserSchema(ModelSchema):
    class Meta:
        model = User
        sqla_session = db.session

class AuthSessionSchema(ModelSchema):
    class Meta:
        model = AuthSession
        sqla_session = db.session


class ConsignmentSchema(ModelSchema):
    class Meta:
        meta =  Consignment
        sqla_session = db.session


class AddressSchema(ModelSchema):

    class Meta:
        fields = ('addressLine1', 'addressLine2', 'countryCode', 'suburb', 'postcode', 'state', 'phoneNumber', 'location')
        model = Address
        sqla_session = db.session


class LocationSchema(ModelSchema):
    loc = GeographySerializationField(attribute='loc')
    id = fields.UUID(Location, attribute='id')

    class Meta:
        model = Location
        sqla_session = db.session
        model_converter = GeoConverter


class ConsignmentAddressSchema(AddressSchema):

    class Meta:
        model = ConsignmentAddress
        sqla_session = db.session

class UserAddressSchema(AddressSchema):
    consignment = fields.Nested(ConsignmentAddressSchema, default=None)
    location = LocationSerializationField()

    class Meta:
        fields =('addressLine1', 'addressLine2', 'countryCode', 'suburb', 'postcode', 'state', 'phoneNumber', 'location')
        model = UserAddress
        sqla_session = db.session


class CourierUserSchema(ModelSchema):
    emailAddress = fields.String(CourierUser, attribute='email_address')
    emailVerified = fields.Boolean(CourierUser, attribute='email_verified')

    class Meta:
        model = CourierUser
        sqla_session = db.session


class ConsumerUserSchema(ModelSchema):
    emailAddress = fields.String(ConsumerUser, attribute='email_address')
    emailVerified = fields.Boolean(ConsumerUser, attribute='email_verified')
    id = fields.UUID(ConsumerUser, attribute='id')
    #accountAddress = fields.Nested(UserAddressSchema, default=None)

    class Meta:
        fields = ('id', 'emailAddress', 'emailVerified', 'fullName')
        model = ConsumerUser
        sqla_session = db.session


class ApplicationInstallationSchema(ModelSchema):
    user = fields.Nested(UserSchema, default = None)
    updated_at = fields.DateTime()
    created_at = fields.DateTime()
    class Meta:
        model = ApplicationInstallation
        sqla_session = db.session


class UserSchema(ModelSchema):
    class Meta:
        model = User
        sqla_session = db.session


class CourierSchema(ModelSchema):
    class Meta:
        model = Courier
        sqla_session = db.session

