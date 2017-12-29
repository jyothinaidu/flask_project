import ascii85
import uuid

import os
from sqlalchemy.orm import aliased
from werkzeug.exceptions import HTTPException

from app.deliveries.model import *
from app.deliveries.model import logger
from app.retailer_integration.model import *

from app.model.meta.base import commit_on_success
from app.model.meta.schema import Location
from app.ops.base import BaseOperation, ApiResponse, log_operation
from app.promotion.model import Promotion
from app.retailer_integration.model import *
from app.users.model import NeighbourSignup
import boto
from boto.s3.connection import OrdinaryCallingFormat

__author__ = 'james'


logger = logging.getLogger()



def to_boolean(value):
    result = None
    if type(value) == bool:
        result = value
    else:
        if type(value) == str or type(value) == unicode:
            if value in [u'true', 'true', u'True', 'True']:
                result = True
            if value in [u'false', 'false', u'False', 'False']:
                result = False
    return result


def mask_email_address( email):
    left = email[:email.find("@")]
    right = email[email.find("@")+1:]
    if len(left) > 3:
        left_masked = left[:3] +"*"*len(left[3:])
    else:
        left_masked = left

    if len(right) > 8:
        right_masked = "*"*len(right[:len(right)-8]) + right[-8:]
    else:
        right_masked = right

    return left_masked + "@" + right_masked


class GetRetailers(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            db_retailers = Retailer.get_all()
            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'retailers': db_retailers })
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

class GetRetailer(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        umbraco_id = kwargs.get( 'umbraco_id')

        try:
            if not umbraco_id:
                ApiResponse.create_response(400, 'umbraco_id not supplied', correlation_id)

            db_retailer = Retailer.get( umbraco_id=umbraco_id)
            if not db_retailer:
                ApiResponse.create_response(404, 'Retailer not found for umbraco_id:' + umbraco_id, correlation_id)


            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'retailer': db_retailer })
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

class PostRetailer(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            if not value:
                ApiResponse.create_response(400, 'retailer not supplied', correlation_id)

            umbraco_id = value.get('umbraco_id')
            existing_retailer = Retailer.get( umbraco_id=umbraco_id)
            if existing_retailer:
                ApiResponse.create_response(422, 'umbraco_id '+ umbraco_id +' already exists', correlation_id)

            if not ( value.get( 'umbraco_id')
                    and value.get( 'website_name')
                    and value.get( 'website_url')
                     ):
                ApiResponse.create_response(422, 'required field missing', correlation_id)

            new_retailer = Retailer( value.get('website_name'), value.get('umbraco_id'), value.get('email_integration_configuration'))
            new_retailer.website_url = value.get( 'website_url')
            if value.get('courier_mappings') and len( value.get('courier_mappings')) > 0: #ensures an empty array is converted into a null
                new_retailer.courier_mappings = value.get('courier_mappings')

            db.session.add(new_retailer)

            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'retailer': new_retailer })
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


class PostPromotion(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            if not value:
                ApiResponse.create_response(400, 'retailer not supplied', correlation_id)

            if not (value.get('promotionDestinationUrl') and value.get('promotionImages')):
                ApiResponse.create_response(400, 'parameters missing', correlation_id)

            destination_url = value.get('promotionDestinationUrl')
            image_base85 = value.get('promotionImages')[0].get('imageFileData')
            retailer_id = value.get('retailerId')

            image_raw_data = ascii85.b85decode(image_base85)
            image_name = value.get('promotionImages')[0].get('name')

            promotion = Promotion(destination_url, retailer_id)


            conn = boto.s3.connect_to_region(config.AWS_REGION,
                                             aws_access_key_id=config.AWS_S3_ACCESSl_KEY,
                                             aws_secret_access_key=config.AWS_S3_SECRET_ACCESS_KEY,
                                             is_secure=True,
                                             calling_format=OrdinaryCallingFormat(),
                                             )


            bucket = conn.get_bucket(config.PROMOTION_BUCKET_NAME)

            key_name = config.PROMOTION_S3_STORE_PREFIX + '/' + image_name

            key = bucket.new_key(key_name)

            #write out the file locally"
            f = open('/tmp/' + image_name, 'w')
            f.write(image_raw_data)
            f.close()

            key.set_contents_from_filename('/tmp/' + image_name, headers={'Content-Type': 'image/png'})

            promotion.promotion_view_url = 'http://' + config.PROMOTION_BUCKET_NAME + config.PROMOTION_S3_STORE_PREFIX + '/' +  image_name

            os.remove('/tmp/' + image_name)

            db.session.add(promotion)

            db.session.commit()

            logger.debug('Created promotion with id {0}'.format(promotion.id))

            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'promotionId': str(promotion.id)})
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

class PutRetailer(BaseOperation):

    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            if not value:
                ApiResponse.create_response(400, 'retailer not supplied', correlation_id)

            umbraco_id = value.get('umbraco_id')
            existing_retailer = Retailer.get( umbraco_id=umbraco_id)
            if not existing_retailer:
                ApiResponse.create_response(404, 'umbraco_id '+ umbraco_id +' does not exist', correlation_id)

            if str(existing_retailer.id) != value.get('id'):
                ApiResponse.create_response(400, 'id supplied does not corospond to the umbraco_id', correlation_id)

            if not ( value.get( 'umbraco_id')
                    and value.get( 'website_name')
                    and value.get( 'website_url')
                     ):
                ApiResponse.create_response(422, 'required field missing', correlation_id)

            existing_retailer.website_name = value.get('website_name')
            existing_retailer.website_url = value.get('website_url')
            existing_retailer.email_integration_configuration = value.get( 'email_integration_configuration')
            existing_retailer.courier_mappings = value.get('courier_mappings')


            db.session.add(existing_retailer)

            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={})
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


class GetNeighbourSignups(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())

        try:

            neighbourSignups = NeighbourSignup.get_all()

            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'neighbourSignups': neighbourSignups })
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

class GetAtHomeUsers(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, ** kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())

        try:

            alias_address = aliased(Address)

            nearby_locations_q = db.session.query(Location).join(alias_address,
                                                               alias_address.id == Location.address_id).join(
                User, User.id == alias_address.tmuser_id).join(ConsumerUser).filter(
                and_(User.at_home == True, ConsumerUser.trusted_neighbour == True))
            logger.debug('Query: {0}'.format(nearby_locations_q))
            nearby_locations = nearby_locations_q.all()
            logger.debug(u'At home users count {0}'.format(len(nearby_locations)))
            result_locations = []
            if nearby_locations:
                users = db.session.query(User).join(Address).filter(
                    Address.id.in_(l.user_address.id for l in nearby_locations)).all()
                logger.debug(u'Found {0} users with addresses'.format(len(users)))
                address_set = set(l.user_address.id for l in nearby_locations)
                for u in users:
                    if u.user_address[0].id in address_set:
                        result_locations.append(u.user_address[0].location)

            results = []
            for u in users:
                if u.current_address:
                    location = u.current_address.location
                    if location:
                        results.append({'lat': u.user_address[0].location.latitude, 'lng': location.longitude, 'name': u.get_user_details().fullName})
            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'userLocations': results})
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp
class PostNeighbourSignup(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            if not value:
                ApiResponse.create_response(400, 'neighbour signup not supplied', correlation_id)


            if not ( value.get( 'name')
                    and value.get( 'emailAddress')
                    and value.get( 'phoneNumber')
                     ):
                ApiResponse.create_response(422, 'required field missing', correlation_id)

            neighbourSignup = NeighbourSignup()
            neighbourSignup.name = value.get( 'name')
            neighbourSignup.email_address = value.get( 'emailAddress')
            neighbourSignup.phoneNumber = value.get( 'phoneNumber')
            neighbourSignup.addressLine1 = value.get( 'addressLine1')
            neighbourSignup.addressLine2 = value.get( 'addressLine2')
            neighbourSignup.suburb = value.get( 'suburb')
            neighbourSignup.state = value.get( 'state')
            neighbourSignup.postcode = value.get( 'postcode')
            neighbourSignup.over18 = value.get( 'over18')
            neighbourSignup.hasIPhone = value.get( 'hasIPhone')
            neighbourSignup.workStatus = value.get( 'workStatus')


            db.session.add(neighbourSignup)

            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'retailer': neighbourSignup })
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp



class GetSealInfo(BaseOperation):
    @log_operation
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())

        try:

            seal_id = kwargs.get('seal_id')
            retailer = Retailer.get( seal_id=seal_id)
            if not retailer:
                ApiResponse.create_response(404, 'Retailer not found', correlation_id,
                                               json={})

            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'seal_info':
                                                         {
                                                              'website_name': retailer.website_name,
                                                              'website_url': retailer.website_url,
                                                              'seal_enabled': retailer.seal_enabled
                                                         }

                                                     })
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

class GetSealAudit(BaseOperation):
    @log_operation
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())

        try:

            seal_id = kwargs.get('seal_id')
            retailer = Retailer.get( seal_id=seal_id)
            if not retailer:
                ApiResponse.create_response(404, 'Retailer not found', correlation_id,
                                               json={})

            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={   'seal_enabled': retailer.seal_enabled,
                                                        'seal_audits': retailer.seal_audits

                                                     })
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


""" This tmp variable is copied from consumer_v1/api/schemas.py. Copying the generated code pattern """
admin_ops = {

    ('retailers_umbraco_id', 'PUT'):{'location': 'json', 'operation': PutRetailer},
    ('retailers_umbraco_id', 'GET'):{'location': 'path', 'operation': GetRetailer},
    ('retailers', 'POST'):  {'location': 'json', 'operation': PostRetailer},
    ('neighbourSignup', 'GET'):  {'location': 'path', 'operation': GetNeighbourSignups},
    ('neighbourSignup', 'POST'):  {'location': 'json', 'operation': PostNeighbourSignup},
    ('promotion', 'POST'): {'location': 'json', 'operation': PostPromotion},
    ('allNeighbourLocations', 'GET'): {'location': 'json', 'operation': GetAtHomeUsers},
    ('seal_seal_id', 'GET'):  {'location': 'path', 'operation': GetSealInfo},
    ('seal_seal_id_seal_audit', 'GET'):  {'location': 'path', 'operation': GetSealAudit}
}


""" Note this factory method requires no conflict of 'path' in the relevant operation dictionaries - consumer_operations
    and courier_operations """
class AdminOperationsFactory(object):
    def factory(operation_name, method):
        operation = admin_ops.get((operation_name, method))['operation']
        return operation()

    factory = staticmethod(factory)