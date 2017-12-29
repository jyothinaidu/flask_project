import uuid

from flask.ext.restful import abort
from googlemaps.exceptions import HTTPError

from werkzeug.exceptions import HTTPException


from app.deliveries.model import *
from app.exc import InsecurePasswordException
from app.location.distances import NearestNeighbours
from app.model.meta.schema import Location
from app.ops.base import BaseOperation, ApiResponse, log_operation, LoginOperation, api_security, DeliveryState
from app.users.model import AuthSession, ConsumerUser, User, CourierUser
from app.users.serialize import UserAddressSchema, ConsumerUserSchema, CourierUserSchema
from app.model.meta.base import commit_on_success
from app.util import wkt_geog_element

__author__ = 'james'

logger = logging.getLogger()


class CourierLoginOperation(LoginOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        # logger.debug(u'Courier op call: {0}, params: {1}'.format(
        #     type(self).__name__, locals()))
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            username = value.get('username', "")    # need to return somethin otherwise auth code chokes
            secret = value.get('password', "")
            auth_session = AuthSession.create_for_courier(username, secret)
            resp = self.authenticate_credentials(auth_session, correlation_id)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

class CourierLogout(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        # logger.debug(u'Courier op call: {0}, params: {1}'.format(
        #     type(self).__name__, locals()))
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        api_key = kwargs.get('api_key')
        try:
            AuthSession.invalidate_token(api_key)
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200, 'courier logged out', correlation_id)         



class CourierPwChange(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, api_key, **kwargs):
        # logger.debug(u'Courier op call: {0}, params: {1}'.format(
        #     type(self).__name__, locals()))

        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            old_password = value.get('oldPassword', '')
            cu = user.get_user_details()
            if cu.secret != old_password:
                ApiResponse.create_response(403, 'Existing password does not match', 
                    correlation_id)
            new_password = value.get('newPassword', '')
            cu.secret = new_password

        except InsecurePasswordException, e:
            logger.exception(e)
            ApiResponse.create_response(403, 'Insecure password not accepted', correlation_id)
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)

class BaseRetrieveDeliveries(BaseOperation):
    def _perform(self, kwargs):
        logger.debug(u'Courier op call: {0}, params: {1}'.format(
            type(self).__name__, locals()))
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        user = kwargs['user'].courier_user  # will throw if no user which is ok I guess
        m_query = TrustmileDelivery.query.filter(TrustmileDelivery.courier == user)
        if len(kwargs.get('exclude_states')) > 0:
            m_query = m_query.filter(~TrustmileDelivery.state.in_(kwargs.get('exclude_states')))
        if len(kwargs.get('include_states')) > 0:
            m_query = m_query.filter(TrustmileDelivery.state.in_(kwargs.get('include_states')))

        deliveries = [d.to_json() for d in m_query.all()]
        return ApiResponse.create_response(200, 'success', correlation_id,
                                           json={"deliveries": deliveries})


class RetrieveDeliveries(BaseRetrieveDeliveries):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, api_key, **kwargs):
        kwargs['include_states'] = []
        kwargs['exclude_states'] = [DeliveryState.CANCELLED.value, DeliveryState.TIME_ARCHIVED.value]
        return self._perform(kwargs)


class RetrieveDeliveriesForState(BaseRetrieveDeliveries):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, api_key, **kwargs):
        desired_state = kwargs.get('deliveryState', None)
        if desired_state:
            kwargs['include_states'] = [desired_state,]
            kwargs['exclude_states'] = []
            return self._perform(kwargs)




class CreateDelivery(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        logger.debug(u'New delivery post value: {0}, {1}'.format(value, kwargs))
        try:
            tracking_numbers = [a['trackingNumber'] for a in value.get('articles')]
            courier_user = user.courier_user

            articles = Article.new_articles(courier_user, tracking_numbers)

            tm_delivery = TrustmileDelivery.create(courier_user, articles)
            if not tm_delivery:
                ApiResponse.create_response(400, 'bad delivery posted', correlation_id)

            tm_delivery.state = value.get('state', DeliveryState.TRANSIT_TO_NEIGHBOUR.value)

            neighbour = ConsumerUser.query.get(value.get('neighbourId'))
            tm_delivery.neighbour = neighbour
            tm_delivery.recipient_info = value.get('recipientInfo', {})
            location = value.get('location')
            if location:
                latitude = location.get('latitude')
                longitude = location.get('longitude')
                tm_delivery.location = wkt_geog_element( longitude, latitude,)
            logger.debug(u"recipient info: #{0}".format(tm_delivery.recipient_info))
            db.session.add(tm_delivery)
            notify_couriers(tracking_numbers, 'Accepted by TrustMile', config.COURIERS_PLEASE_CONTRACTOR_NUM)

            db.session.commit()
            logger.info(u'Delivery created: {0}'.format(tm_delivery.to_json()))
            tasks.send_push.delay(neighbour.email_address, message=u'Courier {0} is on route with a parcel'.format(
                courier_user.fullName))

        except Exception, e:
            logger.exception(e.message)
            ApiResponse.create_response(500, e.message, correlation_id)

        return ApiResponse.create_response(200, 'Success', correlation_id, json={'deliveryID': str(tm_delivery.id),
                                                                                 'correlationID': correlation_id})

class DeliveryGet(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, deliveryId, **kwargs):

        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
 
        logger.debug(u"Retrieving delivery {0}".format(deliveryId))

        try:
            delivery = TrustmileDelivery.query.filter(TrustmileDelivery.id == deliveryId).filter(TrustmileDelivery.state != DeliveryState.CANCELLED.value ).one()
        except:
            logger.error(u"{0},{1} TMdelivery not found ".format(correlation_id, value))
            ApiResponse.create_response(404, 'Delivery not found', correlation_id)

        logger.debug(u"Retrieved delivery {0}".format(delivery.id))

        if not delivery:
            logger.error(u"{0},{1} TMdelivery not found ".format(correlation_id, value))
            ApiResponse.create_response(404, 'Delivery not found', correlation_id)
        return ApiResponse.create_response(200, 'success', correlation_id, 
            json={"delivery": delivery.to_json()})


class DeliveryDelete(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):

        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        delivery_id = kwargs.get('deliveryId', None)

        invalid_delete_states = [DeliveryState.RECIPIENT_RECEIVED.value, DeliveryState.NEIGHBOUR_RECEIVED]
        try:
            delivery = TrustmileDelivery.query.get(delivery_id)
            if delivery.state in invalid_delete_states:
                ApiResponse.create_response(400, 'Cannot delete delivery in states {0}'.format(invalid_delete_states),
                                            correlation_id)

            delivery.state = DeliveryState.CANCELLED.value

            return ApiResponse.create_response(200, 'success', correlation_id,
                                               json={"delivery": delivery.to_json()})

        except HTTPException, hte:
            logger.exception(hte)
            raise hte
        except exc.NoResultFound, nrfe:
            ApiResponse.create_response(404, 'Delivery not found ', correlation_id)
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)



class DeliveryUpdate(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, deliveryId, **kwargs):
        new_state = value.get('DeliveryState')
        neighbour_id = value.get('neighbourId')
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())

        courier_user = kwargs['user'].courier_user   #will throw if no user which is ok I guess
        delivery = TrustmileDelivery.query.filter(
            CourierUser.id == courier_user.id).filter_by(id=deliveryId).one()

        if not delivery:
            logger.error(u"{0},{1} TMdelivery not found ".format(correlation_id, value))
            return ApiResponse.create_response(404, 'Delivery not found', correlation_id)
    
        if new_state:
            logger.debug('updating state for deliveryId {0}, state: {1}'.format(deliveryId, new_state))
            if new_state not in [d.value for d in DeliveryState]:
                logger.error(u"{0} bad status specified for TMdelivery update".format(correlation_id))
                return ApiResponse.create_response(400, 'Required parameter bad or missing', correlation_id)
            elif new_state in [DeliveryState.NEIGHBOUR_RECEIVED.value, DeliveryState.RECIPIENT_RECEIVED.value]:
                logger.error(u"Courier cannot update state once in state {0}".format("OR ".join(
                    [DeliveryState.NEIGHBOUR_RECEIVED.value, DeliveryState.RECIPIENT_RECEIVED.value])))
                return ApiResponse.create_response(400, 'Invalid state transition', correlation_id)
            else:
                logger.debug('State set successfully for deliveryId {0}, state: {1}'.format(deliveryId, new_state))
                delivery.state = new_state

        if neighbour_id:
            neighbour = ConsumerUser.query.get(neighbour_id)
            if neighbour:
                delivery.neighbour = neighbour
            else:                
                logger.error(u"{0} bad neighbour specified for TMdelivery update".format(correlation_id))
                return ApiResponse.create_response(400, 'Required parameter bad or missing', correlation_id)

        return ApiResponse.create_response(200, 'Ok', correlation_id)


class DeliveryArticles(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, deliveryId, **kwargs):
        # logger.debug(u'Courier op call: {0}, params: {1}'.format(
        #     type(self).__name__, locals()))
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())

 
        user = kwargs['user'].courier_user   #will throw if no user which is ok I guess
        delivery = TrustmileDelivery.query.filter(
            CourierUser.id == user.id ).filter_by(id = deliveryId).one()


        articles = delivery.to_json()['articles']
        return ApiResponse.create_response(200, 'success', correlation_id, 
            json = {"parcels": articles})

class DeliveryArticlesAdd(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, deliveryId, **kwargs):
        # logger.debug(u'Courier op call: {0}, params: {1}'.format(
        #     type(self).__name__, locals()))
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
 
        courier_user = kwargs['user'].courier_user   #will throw if no user which is ok I guess
        delivery = TrustmileDelivery.query.filter(
            CourierUser.id == courier_user.id ).filter_by(id = deliveryId).one()

        t_number = value.get('article', {}).get('trackingNumber')

        if not t_number:
            logger.error(u"{0} bad or no article specified for TMdelivery ArticleAdd".format(correlation_id))
            return ApiResponse.create_response(400, 
                'Required parameter bad or missing', correlation_id)

        article = Article.find_by_tracking_id(t_number)
        if not article:
            article = Article(t_number, courier=courier_user.courier, user_entered=True)

        article.delivery = delivery
        db.session.commit()
        articles = delivery.to_json()['articles']
        return ApiResponse.create_response(200, 'success', correlation_id, json={"parcels": articles})


class ArticlesTrackingNumberGet(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        # logger.debug(u'Courier op call: {0}, params: {1}'.format(
        #     type(self).__name__, locals()))
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        tn = kwargs.get('trackingNumber', '')
        article = Article.find_by_tracking_id(tn)
        if not article:
            ApiResponse.create_response(404, 'article not found', correlation_id)
        
        return ApiResponse.create_response(200, 'success', correlation_id, 
            json = {'article': article.to_json()})


class ArticlesTrackingNumberDelete(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        # logger.debug(u'Courier op call: {0}, params: {1}'.format(
        #     type(self).__name__, locals()))
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        tn = kwargs.get('trackingNumber', '')
        article = Article.find_by_tracking_id(tn)
        if not article:
            ApiResponse.create_response(404, 'article not found', correlation_id)
        article.delivery = None
 # todo       ??? articles = delivery. 
 # we're supposed to return a list of articles, but which articles?
        return ApiResponse.create_response(200, 'success', 
            correlation_id, json = {'articles': ''})


class NeighbourLatLong(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, latitude, longitude, **kwargs):
        logger.debug(u'Courier op call: {0}, params: {1}'.format(
            type(self).__name__, locals()))
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        nearest_users = None
        try:
            radius = config.DEFAULT_RADIUS

            nn = NearestNeighbours(Location(latitude, longitude))

            nearest_users = nn.by_travel_time().get_user_distances()
        except HTTPError, hte:
            logger.exception(hte.message)
            ApiResponse.create_response(hte.status_code, u'Google API error: {0}'.format(hte.message), correlation_id)
        except Exception, e:
            logger.exception(e.message)
            ApiResponse.create_response(500, u'Unknown error {0}'.format(e.message), correlation_id)

        if nearest_users:
            alt_recips = [u.to_json() for u in nearest_users]
            logger.debug(u"Found alt recipients: {0}".format(alt_recips))
            return ApiResponse.create_response(200, 'success', correlation_id,
                                               json={"alternateRecipients": alt_recips})
        else:
            ApiResponse.create_response(404, 'No nearby neighbours found', correlation_id)


class AccountRetrieve(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        # logger.debug(u'Courier op call: {0}, params: {1}'.format(
        #     type(self).__name__, locals()))
        try:
            apikey = value.get('X-consumer-apiKey')
            if not apikey:
                ApiResponse.create_response(401, "apiKey not provided in request", correlation_id)
                abort(401, message="apiKey not provided in request", correlationID=correlation_id)
            auth_sess = AuthSession.validate_token(apikey)
            if not auth_sess or not auth_sess.valid:
                ApiResponse.create_response(401, "authentication with API key failed", correlation_id)
            user = auth_sess.user
            user_details = user.get_user_details()
            user_addresses = user.user_address
            user_addr = None

            ud_schema = None
            if isinstance(user_details, ConsumerUser):
                ud_schema = ConsumerUserSchema()
            else:
                ud_schema = CourierUserSchema()

            user_details_data = ud_schema.dump(user_details).data
            if len(user_addresses) > 0:
                user_addr = user_addresses[0]
                user_addr_data = UserAddressSchema().dump(user_addr).data
                user_details_data['accountAddress'] = user_addr_data
            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'account': user_details_data, 'apiKey': apikey})
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


class AccountDelete(BaseOperation):

    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            # Here the value is header
            api_key = value.get('X-consumer-apiKey')
            auth_session = AuthSession.validate_token(api_key)
            if not auth_session or not auth_session.valid:
                ApiResponse.create_response(401, 'Authentication failed', correlation_id)

            user = auth_session.user
            cu = user.get_user_details()
            if not cu.email_verified:
                User.delete(user)
            else:
                return ApiResponse.create_response(409, "Email address already verified", correlation_id)
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)


courier_ops = {
    ('deliveries', 'GET'): {'location': 'body', 'operation': RetrieveDeliveries},
    ('deliveries', 'POST'): {'location': 'json','operation': CreateDelivery},
    ('deliveries_deliveryId', 'PUT'): {'location': 'json', "operation": DeliveryUpdate},
    ('deliveries_deliveryId', 'GET'): {'location': 'path', "operation": DeliveryGet},
    ('deliveries_state_deliveryState', 'GET'): {'location': 'path', "operation": RetrieveDeliveriesForState},
    ('deliveries_deliveryId', 'DELETE'): {'location': 'path', "operation": DeliveryDelete},
    ('deliveries_deliveryId_articles', 'POST'): {'location': 'json', "operation": DeliveryArticlesAdd},
    ('deliveries_deliveryId_articles', 'GET'): {'location': 'path', "operation": DeliveryArticles},
    ('nearestNeighbours_latitude_longitude', 'GET'): {'location': 'path', 'operation': NeighbourLatLong},
    ('articles_trackingNumber', 'GET'): {'location':'path', 'operation': ArticlesTrackingNumberGet},
    ('articles_trackingNumber', 'DELETE'): {'location':'path', 'operation': ArticlesTrackingNumberDelete},
    ('account', 'GET'): {'location': 'headers', 'operation': AccountRetrieve},
    ('login', 'POST'):{'location': 'json', 'operation': CourierLoginOperation},
    ('logout', 'POST'): {'location':'json','operation': CourierLogout},
    ('login_password', 'POST'): {'location':'json', 'operation': CourierPwChange},
}


""" Note this factory method requires no conflict of 'path' in the relevant operation dictionaries - consumer_operations
    and courier_operations """
class CourierOperationsFactory(object):
    def factory(operation_name, method):
        operation = courier_ops.get((operation_name, method))['operation']
        return operation()

    factory = staticmethod(factory)

