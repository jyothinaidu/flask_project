
import uuid
import logging

from flask.ext.restful import abort

from app.async import tasks
from app.messaging.email import EmailHandler
from app.users.model import AuthSession, ConsumerUser, CourierUser
from app.retailer_integration.model import RetailerAuthSession
from enum import Enum
from config import ADMIN_API_KEY

logger = logging.getLogger()

__author__ = 'james'

CONSUMER_API_KEY_STR = 'X-consumer-apiKey'
ADMIN_API_KEY_STR = 'X-admin-apiKey'
COURIER_API_KEY_STR = 'X-courier-apiKey'
RETAILER_API_KEY_STR = 'X-retailer-apiKey'


class DeliveryState(Enum):

    CREATE = "NEWLY_CREATED"
    TRANSIT_TO_NEIGHBOUR = "TRANSIT_TO_NEIGHBOUR"
    NEIGHBOUR_RECEIVED = "NEIGHBOUR_RECEIVED"
    RECIPIENT_RECEIVED = "RECIPIENT_RECEIVED"
    ABORTING = "ABORTING" # The neighbour delivery wasn't possible for whatever reason.
    NEIGHBOUR_ABORTED = "NEIGHBOUR_ABORTED"
    COURIER_ABORTED = "COURIER_ABORTED"
    CANCELLED = "CANCELLED"
    RECIPIENT_ARCHIVED = "RECIPIENT_ARCHIVED"
    TIME_ARCHIVED = "TIME_ARCHIVED"


def api_security(func):
    def api_security_wrapper(*args, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        headers = kwargs.get('headers', None)
        if not headers or not headers.get(CONSUMER_API_KEY_STR):
            ApiResponse.create_response(401, 'Api key missing', correlation_id)

        api_key = headers.get(CONSUMER_API_KEY_STR)

        auth_session = AuthSession.validate_token(api_key)
        if not auth_session or not auth_session.valid:
            ApiResponse.create_response(401, 'Authorization failed', correlation_id)
        user = auth_session.user
        if not user:
            ApiResponse.create_response(401, 'User not found', correlation_id)

        kwargs["user"] = user
        kwargs["api_key"] = api_key

        return func(*args, **kwargs)

    return api_security_wrapper


def log_operation(func):
    def log_wrapper(*args, **kwargs):
        m_uuid = uuid.uuid4()
        logger.debug(u"{0} : {1}, args: {2}, kwargs {3}".format(func.__name__, m_uuid, args, kwargs))
        kwargs['correlation_id'] = m_uuid
        result = func(*args, **kwargs)
        return result

    return log_wrapper


def admin_security(headers, *args, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        if not headers or not headers.get(ADMIN_API_KEY_STR):
            ApiResponse.create_response(401, 'Api key missing', correlation_id)

        api_key = headers.get(ADMIN_API_KEY_STR)
        if api_key != ADMIN_API_KEY:
            ApiResponse.create_response(401, 'Authorization failed', correlation_id)


def retailer_security(func):
    def retailer_security_wrapper(*args, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        headers = kwargs.get('headers', None)
        if not headers or not headers.get(RETAILER_API_KEY_STR):
            ApiResponse.create_response(401, 'Api key missing', correlation_id)

        api_key = headers.get(RETAILER_API_KEY_STR)

        auth_session = RetailerAuthSession.validate_token(api_key)
        if not auth_session or not auth_session.valid:
            ApiResponse.create_response(401, 'Authorization failed', correlation_id)
        retailer = auth_session.retailer
        if not retailer:
            ApiResponse.create_response(401, 'User not found', correlation_id)

        kwargs["retailer"] = retailer
        kwargs["api_key"] = api_key

        return func(*args, **kwargs)

    return retailer_security_wrapper


class BaseOperation(object):
    def __init__(self):
        pass

    @log_operation
    def perform(self, value, **kwargs):
        pass

    @staticmethod
    def send_verification_email(email_address, full_name, token):
        logger.info(u"Sending email to email address: {0}, name: {1}, verify token: {2}".format(email_address, full_name, token))
        #task_result = tasks.send_email_verification.delay(email_address, full_name, token)
        #m_result = EmailHandler.send_verification(cu.email_address, cu.fullName, email_verify_token)
        m_result = EmailHandler.send_verification(email_address, full_name, token)
        #logger.debug(u"Sent email to {0} with status {1}".format(email_address, task_result.status))

    @staticmethod
    def send_password_reset(cu, full_name):

        m_result = EmailHandler.send_password_reset(cu.email_address, full_name, str(cu.password_reset_token))
        logger.debug(u"Sent email with result {0}".format(m_result))
        return cu

    @staticmethod
    def send_retailer_password_reset(retailer):

        m_result = EmailHandler.send_retailer_password_reset(retailer.contact_emailAddress, retailer.contact_firstName, str(retailer.password_reset_token))
        logger.debug(u"Sent email with result {0}".format(m_result))
        return retailer


class ApiResponse(object):
    def __init__(self, code, message, correlation_id, **kwargs):
        self.code = code
        self.message = message
        self.correlation_id = correlation_id
        self.api_key = kwargs.get('apiKey', None)
        self.headers = kwargs.get('headers', None)
        self.json = kwargs.get('json', {})

    def get_resource_response(self):
        self.json['correlationID'] = str(self.correlation_id)
        if self.code >= 400:
            logger.exception(u"Error occured on server, http status {0} message: {1}".format(self.code, self.message))
            abort(self.code, message=self.message, json=self.json)
        r = self.json, self.code, self.headers
        return r

    @classmethod
    def create_response(cls, code, message, correlation_id, **kwargs):
        return ApiResponse(code, message, correlation_id, **kwargs).get_resource_response()


class LoginOperation(BaseOperation):

    def authenticate_credentials(self, auth_session, correlation_id):
        if not auth_session or not auth_session.valid:
            ApiResponse.create_response(403, "Invalid login", correlation_id)
        user = auth_session.user
        user_details = user.get_user_details()
        if isinstance(user_details, ConsumerUser):
            j = {'emailVerified': user_details.email_verified or False, 
                'apiKey': auth_session.token,
                'userId': user.consumer_user.id,
                'correlationID': correlation_id}
        elif isinstance(user_details, CourierUser):
           j = {'apiKey': auth_session.token,
                'userId': user.courier_user.id,
                 'correlationID': correlation_id}
        resp = ApiResponse.create_response(200, "Success", correlation_id, json=j)
        return resp



