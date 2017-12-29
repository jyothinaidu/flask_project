import uuid
import string
import random

from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

import config
from app import util
from app.deliveries.model import *
from app.deliveries.model import logger
from app.retailer_integration.model import *
from app.exc import InsecurePasswordException, InvalidEmailException, EmailSendException, DeliveryNotFoundException
from app.location.geocode import Geocoder
from app.messaging.email import EmailHandler
from app.model.meta.base import commit_on_success
from app.model.meta.schema import FeedbackMessage
from app.model.meta.schema import UserPresence, Location
from app.ops.base import BaseOperation, ApiResponse, log_operation, LoginOperation
from app.ops.base import retailer_security
from app.users.model import NeighbourSignup
from app.users.serialize import ApplicationInstallationSchema, UserAddressSchema, ConsumerUserSchema, CourierUserSchema
from app.retailer_integration.RetailerIntegration import RetailerIntegration
from datetime import datetime
#import dateutil.parser

#from tests.test_retailer_integration import send_email

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


#/account get
class GetRetailer(BaseOperation):
    @log_operation
    @retailer_security
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())

        try:
            retailer = kwargs.get('retailer') # type: Retailer
            db.session.expunge(retailer)
            #don't return these fields.  Flask should strip them out but better to be safe
            retailer.secret = None
            retailer.email_integration_configuration = {}
            retailer.courier_mappings = []
            retailer.email_server_configuration = {}
            if not retailer.retailer_attributes:
                retailer.retailer_attributes = {}
            if not retailer.seal_id:
                retailer.seal_id = ''
            if not retailer.seal_enabled:
                retailer.seal_enabled = False


            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'retailer': retailer })
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

#/account/register
class PostRegisterRetailer(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            if not value:
                ApiResponse.create_response(400, 'retailer not supplied', correlation_id)

            if Retailer.get( website_name=value.get('website_name') ):
                ApiResponse.create_response(422, 'website_name '+ value.get('website_name') +' already exists', correlation_id)

            if Retailer.get( contact_emailAddress = value.get( 'contact_emailAddress' ) ):
                ApiResponse.create_response(422, 'contact_emailAddress '+ value.get('contact_emailAddress') +' already exists', correlation_id)

            if Retailer.get( website_url = value.get('website_url')):
                ApiResponse.create_response(422, 'website_url '+ value.get('website_url') +' already exists', correlation_id)

            if not ( value.get( 'website_name')
                    and value.get( 'website_url')
                     ):
                ApiResponse.create_response(422, 'required field missing', correlation_id)


            new_retailer = Retailer( value.get('website_name'))
            new_retailer.website_url = value.get( 'website_url')
            new_retailer.contact_firstName = value.get('contact_firstName')
            new_retailer.contact_lastName = value.get('contact_lastName')
            new_retailer.contact_phoneNumber = value.get('contact_phoneNumber')
            new_retailer.contact_emailAddress = value.get('contact_emailAddress')
            new_retailer.secret = value.get( 'contact_password')

            new_retailer.seal_id = self.generate_seal_id()
            db.session.add(new_retailer)

            ras = RetailerAuthSession.create( new_retailer.contact_emailAddress, new_retailer.secret)

            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'apiKey': ras.token})
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

    def generate_seal_id(self):
        #http://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python/23728630#23728630
        seal_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))
        #the above is cryptographically secure, so it's unlikly there will be a clash of seal id's
        # but lets check anyway
        while Retailer.get( seal_id=seal_id) != None:
            seal_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))

        return seal_id




#/account
class PostRetailer(BaseOperation):

    @log_operation
    @retailer_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:


            retailer = kwargs.get('retailer') # type: Retailer

            db_retailer = Retailer.get(id = retailer.id) # type: Retailer

            existing_retailer = Retailer.get( website_name=value.get( 'website_name'))
            if existing_retailer and existing_retailer.id != retailer.id:
                ApiResponse.create_response(422, 'website_name '+ value.get('website_name') +' already exists', correlation_id)

            existing_retailer = Retailer.get( contact_emailAddress = value.get('contact_emailAddress'))
            if existing_retailer and existing_retailer.id != retailer.id:
                ApiResponse.create_response(422, 'contact_emailAddress '+ value.get('contact_emailAddress') +' already exists', correlation_id)

            existing_retailer = Retailer.get( website_url = value.get('website_url'))
            if existing_retailer and existing_retailer.id != retailer.id:
                ApiResponse.create_response(422, 'contact_emailAddress '+ value.get('contact_emailAddress') +' already exists', correlation_id)


            db_retailer.website_name = value.get('website_name')
            db_retailer.website_url = value.get('website_url')
            db_retailer.contact_firstName = value.get('contact_firstName')
            db_retailer.contact_lastName = value.get('contact_lastName')
            db_retailer.contact_emailAddress = value.get('contact_emailAddress')
            db_retailer.contact_phoneNumber = value.get('contact_phoneNumber')

            db.session.add(db_retailer)

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


#/account/attributes
class PostAccountAttributes(BaseOperation):

    @log_operation
    @retailer_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:


            retailer = kwargs.get('retailer') # type: Retailer

            db_retailer = Retailer.get(id = retailer.id) # type: Retailer

            attributes = {}
            for key in value:
                attributes[key] = value[key]

            db_retailer.retailer_attributes = attributes

            db.session.add(db_retailer)

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

class Ping(BaseOperation):

    #@log_operation - too noisy
    @retailer_security
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        return ApiResponse.create_response(200, 'Success', correlation_id )


class PostLogin(BaseOperation):

    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            email_address = value.get('emailAddress')
            secret = value.get('password')
            if not email_address or not secret:
                ApiResponse.create_response(400, "Email Address or Password not supplied", correlation_id)

            auth_session = RetailerAuthSession.create(email_address, secret)


            if not auth_session or not auth_session.valid:
                ApiResponse.create_response(403, "Invalid login", correlation_id)

            resp = ApiResponse.create_response(200, "Success", correlation_id, json={'apiKey': auth_session.token})
            return resp

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


class PostForgotPassword(BaseOperation):

    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            email_address = value.get('emailAddress')

            if email_address:
                retailer = Retailer.get( contact_emailAddress = email_address)
                if retailer:
                    retailer.reset_password()
                    self.send_retailer_password_reset(retailer)
                else:
                    logger.warn( 'PostForgotPassword - retailer not found {0}'.format(email_address))
            else:
                ApiResponse.create_response(422, 'emailAddress not provided', correlation_id)

        except EmailSendException, ese:
            logger.exception(ese)
            ApiResponse.create_response(500, 'Unexpected email send exception', correlation_id)
        except InvalidEmailException, iee:
            logger.exception(iee)
            ApiResponse.create_response(404, 'Invalid email address', correlation_id)
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)


class PostResetPassword(BaseOperation):

    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            reset_token = kwargs.get('resetToken')
            new_password = value.get('newPassword')

            if reset_token and new_password:
                if not len(new_password.strip()) >= 8:
                    ApiResponse.create_response(422, 'Password must be at least 8 characters', correlation_id)

                retailer = Retailer.find_reset_token(reset_token)
                if not retailer:
                    ApiResponse.create_response(404, 'Reset token not found', correlation_id)

                retailer.secret = new_password.strip()

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)



class GetResetPassword(BaseOperation):

    @log_operation
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            reset_token = kwargs.get('resetToken')

            if reset_token:
                retailer = Retailer.find_reset_token(reset_token)

                if not retailer:
                    ApiResponse.create_response(404, 'Reset token not found', correlation_id)


            return ApiResponse.create_response(200, "Success", correlation_id, json={"emailAddress": mask_email_address(retailer.contact_emailAddress)})

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)



class PostPassword(BaseOperation):

    @log_operation
    @retailer_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            retailer = kwargs.get('retailer') # type: Retailer
            old_password = value.get('oldPassword')
            if retailer.secret != old_password:
                ApiResponse.create_response(403, 'Existing password does not match', correlation_id)
            new_password = value.get('newPassword')
            if not new_password or len( new_password.strip()) < 8:
                ApiResponse.create_response(422, 'Password does not meet complexity requirements', correlation_id)

            retailer.secret = new_password
            db.session.add( retailer)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)


class GetSealAudit(BaseOperation):

    @log_operation
    @retailer_security
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            retailer = kwargs.get('retailer') # type: Retailer
            resp = ApiResponse.create_response(200, "Success", correlation_id, json={'seal_audits': retailer.seal_audits})
            return resp

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


class PostSealAudit(BaseOperation):

    @log_operation
    @retailer_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            retailer = kwargs.get('retailer') # type: Retailer

            if not retailer.seal_audits:
                retailer.seal_audits = []

            #do a merge / update
            for auditAnswer in value:
                question_code = auditAnswer['question_code']
                found = False
                for e_i in range(len(retailer.seal_audits)):
                    e_qc = retailer.seal_audits[e_i].question_code
                    if question_code == e_qc:
                        retailer.seal_audits[e_i].answer = auditAnswer['answer']
                        retailer.seal_audits[e_i].additional_information = auditAnswer['additional_information']
                        found = True
                        break
                if not found:
                    new_answer = RetailerSealAudit()
                    new_answer.question_code = auditAnswer['question_code']
                    new_answer.question_text = auditAnswer['question_text']
                    new_answer.answer = auditAnswer['answer']
                    new_answer.additional_information = auditAnswer['additional_information']
                    retailer.seal_audits.append(new_answer)

            db.session.add(retailer)



            resp = ApiResponse.create_response(200, "Success", correlation_id, json={})
            return resp

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp



class GetCourierMappings(BaseOperation):

    @log_operation
    @retailer_security
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            retailer = kwargs.get('retailer') # type: Retailer

            #sanity check.
            courier_mappings = retailer.courier_mappings

            if not isinstance(courier_mappings,list):
                courier_mappings = []

            resp = ApiResponse.create_response(200, "Success", correlation_id, json={'courier_mappings': courier_mappings})
            return resp

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


class PostCourierMappings(BaseOperation):

    @log_operation
    @retailer_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            retailer = kwargs.get('retailer') # type: Retailer

            if not isinstance(retailer.courier_mappings,list):
                retailer.courier_mappings = []

            #validate input
            if not isinstance(value, list):
                ApiResponse.create_response(400, 'Array of courier mappings Expected', correlation_id)

            #validate and sanatise the input
            courier_mappings = []
            for cm in value:
                if 'sourceText' in cm and 'courierName' in cm:
                    courier_mappings.append( { 'sourceText': cm['sourceText'], 'courierName': cm['courierName']})
                else:
                    ApiResponse.create_response(400, 'invalid array element', correlation_id)


            retailer.courier_mappings = courier_mappings

            db.session.add(retailer)



            resp = ApiResponse.create_response(200, "Success", correlation_id, json={})
            return resp

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

class AddRetailerInegrationDelivery(BaseOperation):

    @log_operation
    @retailer_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            retailer = kwargs.get('retailer') # type: Retailer

            tracking_number = value.get('trackingNumber', None)
            courier = value.get("courierSlug", None)
            order_id = value.get("orderNumber", None)
            email_address = value.get("emailAddress", None)

            #retailer_data = {}
            #retailer_data['retailer_id'] = retailer.id
            #days_diff = self.get_date_difference(retailer_data)

            # Use tracking number as description when absent.
            #description = value.get("description", tracking_number)
            #retailer_pf = value.get("purchasedFrom", None)

            if not (tracking_number or courier or email_address):
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)

            record = db.session.query(ConsumerUser).filter_by(email_address=email_address)

            if record:
                user = record[0]

                consignments_query = Consignment.query.join(
                    UserConsignment).join(User).filter(User.id == user.tmuser_id)

                consignments = consignments_query.all()
                bcheck = False
                for c in consignments:
                    if c.tracking_number == tracking_number:
                        bcheck = True
                if not bcheck:
                    email_dict = {}
                    email_dict["from_address"] = retailer.contact_emailAddress
                    email_dict["to_address"] = email_address
                    email_dict["subject"] = "Delivery Added by the retailer"
                    email_dict["body"] = "For More info refer the delivery with the give tracking number"
                    email_dict["date"] = datetime.now()
                    email_dict["uid"] = "test"

                    parsed_data = {}; tracking_numbers = []; tracking_info = {}

                    tracking_info["tracking_number"] = tracking_number; tracking_info["courier"] = courier;
                    tracking_numbers.append(tracking_info)

                    parsed_data["tracking_numbers"] = tracking_numbers
                    parsed_data["email_address"] = email_address
                    parsed_data["order_id"] = order_id
                    #parsed_data["description"] = description
                    #parsed_data["retailer_name"] =retailer_pf

                    retailerInstance = RetailerIntegration()
                    retailerInstance.add_parsed_email(retailer, email_dict, parsed_data)


        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)

class GetDeliveriesRetailer(BaseOperation):
    @log_operation
    @retailer_security
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())

        try:
            retailer = kwargs.get('retailer') # type: Retailer

            days = kwargs.get('weekorMonth', None)
            weekormonth = 0
            if days=='week':
                weekormonth = 7
            elif days =='month':
                weekormonth = 30

            #this variable is to populate data for time being only
            weekormonth = 180
            if weekormonth != 0:
                delivery_retailer_list = Deliveries.get_deliveries_for_couriers(weekormonth, retailer)
                resp = ApiResponse.create_response(200, 'Success', correlation_id, json=delivery_retailer_list)
            else:
                resp = ApiResponse.create_response(500, 'Invalid input argument', correlation_id)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

class DeliveryDays(BaseOperation):
    @log_operation
    @retailer_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            retailer = kwargs.get('retailer')  # type: Retailer

            days = kwargs.get('weekorMonth', None)
            weekormonth = 0
            if days=='week':
                weekormonth = 7
            elif days =='month':
                weekormonth = 30

            #this variable is to populate data for time being only
            weekormonth = 180
            if weekormonth != 0:
                delivery_days_list = Deliveries.get_deliveries_for_days(weekormonth, retailer)
                resp = ApiResponse.create_response(200, "Success", correlation_id, json=delivery_days_list)
            else:
                resp = ApiResponse.create_response(500, 'Invalid input argument', correlation_id)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp



""" This tmp variable is copied from consumer_v1/api/schemas.py. Copying the generated code pattern """
retailer_ops = {



    ('account_register', 'POST'):{'location': 'json', 'operation': PostRegisterRetailer},
    ('account_login', 'POST'):{'location': 'json', 'operation': PostLogin},
    ('account_forgotPassword', 'POST'):{'location': 'json', 'operation': PostForgotPassword},
    ('account', 'POST'):{'location': 'json', 'operation': PostRetailer},
    ('account', 'GET'):{'location': 'path', 'operation': GetRetailer},
    ('account_resetPassword_resetToken', 'POST'):{'location': 'json', 'operation': PostResetPassword},
    ('account_resetPassword_resetToken', 'GET'):{'location': 'path', 'operation': GetResetPassword},
    ('account_password', 'POST'):{'location': 'json', 'operation': PostPassword},
    ('ping', 'GET'):{'location': 'path', 'operation': Ping},
    ('account_attributes', 'POST'):{'location': 'json', 'operation': PostAccountAttributes},
    ('account_seal_audit', 'GET'):{'location': 'path', 'operation': GetSealAudit},
    ('account_seal_audit', 'POST'):{'location': 'json', 'operation': PostSealAudit},
    ('account_courier_mapping', 'GET'):{'location': 'path', 'operation': GetCourierMappings},
    ('account_courier_mapping', 'POST'):{'location': 'json', 'operation': PostCourierMappings},
    ('account_deliveries_courier_weekorMonth', 'GET'):{'location': 'path', 'operation': GetDeliveriesRetailer},
    ('account_deliveries_day_weekorMonth', 'GET'): {'location': 'path', 'operation': DeliveryDays},
    ('account_deliveries_retailerintegration', 'POST'): {'location': 'json', 'operation': AddRetailerInegrationDelivery}

}



""" Note this factory method requires no conflict of 'path' in the relevant operation dictionaries - consumer_operations
    and courier_operations """
class RetailerOperationsFactory(object):
    def factory(operation_name, method):
        operation = retailer_ops.get((operation_name, method))['operation']
        return operation()

    factory = staticmethod(factory)