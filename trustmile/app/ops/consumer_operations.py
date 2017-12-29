import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.functions import user
from werkzeug.exceptions import HTTPException
from sqlalchemy import update

from app import util
from app.deliveries.model import *
from app.deliveries.model import logger
from app.exc import InsecurePasswordException, InvalidEmailException, EmailSendException, DeliveryNotFoundException
from app.location.geocode import Geocoder
from app.model.meta.base import commit_on_success
from app.model.meta.schema import FeedbackMessage, EmailVerification
from app.model.meta.schema import Location
from app.ops.base import BaseOperation, ApiResponse, log_operation, LoginOperation, DeliveryState
from app.ops.base import api_security
from app.users.model import AuthSession, ConsumerUser, User, get_user_by_email, AnonymousUser
from app.retailer_integration.model import Retailer
from app.users.serialize import ApplicationInstallationSchema, UserAddressSchema, ConsumerUserSchema, CourierUserSchema
from app.retailer_integration.RetailerIntegration import RetailerIntegration
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


def mask_email_address(email):
    left = email[:email.find("@")]
    right = email[email.find("@") + 1:]
    if len(left) > 3:
        left_masked = left[:3] + "*" * len(left[3:])
    else:
        left_masked = left

    if len(right) > 8:
        right_masked = "*" * len(right[:len(right) - 8]) + right[-8:]
    else:
        right_masked = right

    return left_masked + "@" + right_masked


def update_installation_information(user, value):
    replaced = False
    if value.get('installationInformation'):
        inst_info = value.get('installationInformation')
        inst_info_obj = ApplicationInstallationSchema().load(inst_info, partial=True).data
        for i, inst_info in enumerate(user.installation_information):
            if inst_info_obj.DeviceIdentifier == inst_info.DeviceIdentifier:
                user.installation_information[i] = inst_info_obj
                replaced = True
                break
        if not replaced:
            user.installation_information.append(inst_info_obj)


class AccountLoginOperation(LoginOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            email_address = value.get('emailAddress')
            secret = value.get('password')

            installation_information = value.get('installationInformation')

            auth_session = AuthSession.create(email_address, secret)

            if installation_information:

                inst_info_obj = ApplicationInstallationSchema().load(installation_information, partial=True).data
                anonlist = AnonymousUser.query.filter(
                    AnonymousUser.device_id == inst_info_obj.DeviceIdentifier).order_by(
                    desc(AnonymousUser.created_at)).all()
                if anonlist:
                    Deliveries.add_anon_deliveries(auth_session.user, anonlist)

            resp = self.authenticate_credentials(auth_session, correlation_id)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


class DeliveryFeedbackOperation(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    # TODO: Verify that is in delivery status
    def perform(self, value, user, api_key, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            delivery_id = kwargs.get('deliveryId')
            if not delivery_id:
                ApiResponse.create_response(404, "Delivery not provided", correlation_id)
            did = Deliveries.get_for_id(delivery_id)
            rating = value.get('rating', None)
            comment = value.get('comment', None)
            complaints = value.get('complaint', [])
            net_promoter_score = value.get('netPromoterScore', None)
            net_promoter_score_comment = value.get('netPromoterScoreComment', None)

            complaint_objs = []
            for c in complaints:
                complaint_objs.append(DeliveryComplaint(c))

            cu = user.get_user_details()

            nps = None
            if net_promoter_score:
                nps = NetPromoterScore(int(net_promoter_score), cu, did, comment=net_promoter_score_comment)
                db.session.add(nps)
                logger.info(
                    u"Created net promoter score {0}, rating {1}, user {2}".format(
                        delivery_id, net_promoter_score, cu.email_address))

            if rating:
                delivery_feedback = DeliveryFeedback(did, rating, comment, cu, complaints=complaint_objs)

                db.session.add(delivery_feedback)

                logger.info(
                    u"Created delivery feedback item {0}, rating {1}, comment {2}, complaints {3}, user {4}".format(
                        delivery_id, rating, comment, complaints, cu.email_address))

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(u"Unexpected error")
            raise e
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)


class AccountRegister(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        # assume the value has at least username and password
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            email = value.get('emailAddress')
            password = value.get('password')

            installation_information = value.get('installationInformation')
            if not installation_information:
                logger.error(u"{0}, missing parameters".format(correlation_id))
                ApiResponse.create_response(400, 'Missing parameters', correlation_id)

            inst_info_obj = ApplicationInstallationSchema().load(installation_information, partial=True).data

            if not (email and password):
                logger.error(u"{0}, missing parameters".format(correlation_id))
                ApiResponse.create_response(422, 'Missing parameters', correlation_id)

            if value.get('fullName'):
                name = value.get('fullName')

            device_identifier = inst_info_obj.DeviceIdentifier
            cu = ConsumerUser.create(email, password, device_identifier, name=name or None)


            #add any consignments from retailer integration to the users account
            RetailerIntegration().associate_consignments_for_user( email)

            auth_session = AuthSession.create(email, password)
            user = cu.user

            inst_info_obj = None
            address_obj = None
            update_installation_information(user, value)
            if 'accountAddress' in value:
                address_info = value.get('accountAddress')
                address_obj = UserAddressSchema().load(address_info, partial=True).data
                user.user_address.append(address_obj)

            token = util.gen_random_str(10)
            ev = EmailVerification(email, token)
            db.session.add(ev)
            db.session.commit()

            self.send_verification_email(cu.email_address, cu.fullName, token)

            if not auth_session:
                resp = ApiResponse.create_response(401, 'Unauthorised session', correlation_id)
            else:
                resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                                   json={'apiKey': auth_session.token, 'correlationID': correlation_id})

        except HTTPException, he:
            db.session.rollback()
            logger.exception(he)
            raise he
        except IntegrityError, ierror:
            db.session.rollback()
            logger.exception(ierror)
            ApiResponse.create_response(409, 'Email already exists', correlation_id)
        except (InsecurePasswordException, InvalidEmailException), ipe:
            db.session.rollback()
            logger.exception(ipe)
            ApiResponse.create_response(422, 'Invalid email or insecure password', correlation_id)
        except EmailSendException, ese:
            db.session.rollback()
            logger.exception(ese)
            ApiResponse.create_response(500, 'Unexpected email send exception', correlation_id)
        except Exception, e:
            db.session.rollback()
            logger.exception(e)
            raise e
        else:
            return resp


class AnonymousRegistration(BaseOperation):

    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            installation_information = value.get('installationInformation')
            if not installation_information:
                logger.error(u"{0}, missing parameters".format(correlation_id))
                ApiResponse.create_response(400, 'Missing parameters', correlation_id)

            inst_info_obj = ApplicationInstallationSchema().load(installation_information, partial=True).data

            anon_user = AnonymousUser.create(inst_info_obj)

            auth_session = AuthSession.create_anonymous_auth_session(anon_user)

            user = anon_user.user

            update_installation_information(user, value)

            if not auth_session:
                resp = ApiResponse.create_response(401, 'Unauthorised session', correlation_id)
            else:
                resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                                   json={'apiKey': auth_session.token, 'correlationID': correlation_id})

        except HTTPException, he:
            db.session.rollback()
            logger.exception(he)
            raise he
        except IntegrityError, integrity_error:
            db.session.rollback()
            logger.exception(integrity_error)
            ApiResponse.create_response(409, 'Device id already exists', correlation_id)
        except Exception, e:
            db.session.rollback()
            logger.exception(e)
            raise e
        else:
            return resp


class AccountRetrieve(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, api_key, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            user_details = user.get_user_details()
            user_addresses = user.user_address
            preferences = user.preferences
            installation_information = user.installation_information
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
            if user_addr:
                user_addr_data = UserAddressSchema().dump(user_addr).data
                user_details_data['accountAddress'] = user_addr_data
            if installation_information:
                # user_details_data['installationInformation'] = []
                # for inst in installation_information:
                installation_information_data = ApplicationInstallationSchema().dump(installation_information[0]).data
                user_details_data['installationInformation'] = installation_information_data
            if preferences:
                user_details_data['userPreferences'] = preferences
            resp = ApiResponse.create_response(200, 'Success', correlation_id,
                                               json={'account': user_details_data, 'apiKey': api_key})
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp

class AddDelivery(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, *args, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            tracking_number = value.get('trackingNumber', None)
            courier = value.get("courierSlug", None)
            # Use tracking number as description when absent.
            description = value.get("description", tracking_number)
            retailer_pf = value.get("purchasedFrom", None)

            if not (tracking_number and courier):
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)

            # TODO: check that if this article is in the system, it belongs to this user
            # or create an article for it!.
            # For now we just add the one delivery. But the model API will take a list so
            # make it one
            user = kwargs.get('user')

            consignment = Deliveries.user_adds_delivery(user, courier, tracking_number, description, retailer_pf)

            if not consignment:
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)
            db.session.add(consignment)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except DeliveryNotFoundException, dnfe:
            logger.exception(dnfe)
            ApiResponse.create_response(404, 'Delivery not found', correlation_id)
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200, 'Success, consignment with id {0} added'.format(str(consignment.id)),
                                           correlation_id, json={'deliveryId': str(consignment.id)})


class UpdateDelivery(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, *args, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            delivery_id = kwargs.get("deliveryId")
            if not (delivery_id):
                ApiResponse.create_response(404, 'No delivery id provided', correlation_id)

            description = value.get("description")
            retailername = value.get("purchasedFrom")

            tracking_number = value.get('trackingNumber', None)
            courier = value.get("courierSlug", None)

            if not description:
                ApiResponse.create_response(400, 'Description required', correlation_id)

            user = kwargs.get('user')

            consignment = Deliveries.get_consignment_for_user(user, delivery_id)

            if not consignment:
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)

            if tracking_number and courier:

                #Consignment.delete_by_id(delivery_id)
                #db.session.query().filter(Consignment.id == delivery_id, User.id == user.id).update().values(Consignment.tracking_number = tracking_number)
                consignment = Deliveries.user_adds_delivery(user, courier, tracking_number, description, retailername)

            else:
                uc = UserConsignment.query.join(User).join(Consignment).filter(
                    Consignment.id == delivery_id, User.id == user.id).first()
                if not uc:
                    ApiResponse.create_response(404, 'No user description found', correlation_id)
                else:
                    uc.user_description = description
                    uc.retailer_name = retailername


        except HTTPException, he:
            logger.exception(he)
            raise he
        except DeliveryNotFoundException, dnfe:
            logger.exception(dnfe)
            ApiResponse.create_response(404, 'Delivery not found', correlation_id)
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200,
                                           'Success, consignment with id {0} added'.format(str(consignment.id)),
                                           correlation_id, json={'deliveryId': str(consignment.id)})


# NOTE:  You can not add things to a session in this event listener
# 1 - while this is fired via celery this is the desired behaviour
#   - We want the data persistsed to the DB before celery runs
# 2 - If this runs IN THE SAME PROCESS  (remove the .delay() )
#   - It gets all messed up because
#        - this even is executed via a db.session.commit()
#        - so doing another db.session.commit() will bork
#        - doing a db.session.add() isn't supported and may or may not work
# SO  If you are testing, change the event to something else.
# @event.listens_for(Consignment, 'after_insert')
# def fire_aftership_event(mapper, connection, target):
#     tasks.async_update_shipping_info.delay(target.id)


class SetUserPresence(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, api_key, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            if 'status' in value and 'location' in value:
                location = value.get('location')
                status = value.get('status')
                user_id = user.id
                tasks.post_user_presence.delay(
                    user_id, status, location.get("latitude", 0.000), location.get("longitude", 0.0000))

            else:
                ApiResponse.create_response(400, "Location field incorrect", correlation_id)

            resp = ApiResponse.create_response(200, 'Success', correlation_id)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


def update_address_location(addr_obj):
    try:
        str_address = "{0} {1}, {2}, {3}, {4}, {5}".format(addr_obj.addressLine1, addr_obj.addressLine2,
                                                           addr_obj.suburb,
                                                           addr_obj.postcode, addr_obj.state, addr_obj.countryCode)
        geocoder = Geocoder(config.GOOGLE_LOCATION_KEY)
        loc = geocoder.geocode(str_address)
        logger.debug(u"Location is {0}".format(loc))

        addr_obj.location = Location(loc.latitude, loc.longitude)
        db.session.commit()

    except Exception, e:
        logger.exception(e)
        raise e


class AccountUpdate(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, api_key, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            cu = user.get_user_details()
            if value.get('fullName'):
                name = value.get('fullName')
                cu.fullName = name
            is_trustmile_neighbour = to_boolean(value.get('trustmileNeighbour', False))

            cu.trusted_neighbour = is_trustmile_neighbour
            if value.get('installationInformation'):
                update_installation_information(user, value)
            if 'accountAddress' in value:
                address_info = value.get('accountAddress')
                address_obj = UserAddressSchema().load(address_info, partial=True).data
                logger.debug(u"User address object {0} of type {1}".format(address_obj, type(address_obj)))
                user.user_address.append(address_obj)
                db.session.flush()
                tasks.update_address_location.apply_async((address_obj.id,), {})
            if 'userPreferences' in value:
                preferences = value.get('userPreferences', False)
                logger.debug(u'Got preferences {0}, type {1}'.format(preferences, type(preferences)))
                if isinstance(preferences, str) or isinstance(preferences, unicode):
                    user.update_preferences({'values': []})
                elif isinstance(preferences, dict):
                    user.update_preferences(preferences)

            db.session.commit()
            #logger.info('Sending account updated push: {0}'.format(cu.email_address))
            #tasks.send_push.delay(cu.email_address, data={'account_changed': True})

            resp = ApiResponse.create_response(200, 'Success', correlation_id)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return resp


class PasswordUpdate(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, api_key, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            old_password = value.get('oldPassword')
            cu = user.get_user_details()
            if cu.secret != old_password:
                ApiResponse.create_response(403, 'Existing password does not match', correlation_id)
            new_password = value.get('newPassword')
            cu.secret = new_password

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)


class AccountDelete(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, api_key, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            logger.debug(u'api_key for delete {0}'.format(api_key))

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


class VerifyEmail(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            # Here the value is header
            verification_code = kwargs.get('verificationCode')
            verification_code = verification_code.strip()
            if not verification_code:
                ApiResponse.create_response(401, "Verification not provided", correlation_id)

            user_uuid = User.get_for_email_verification(verification_code)

            if not user_uuid:
                ApiResponse.create_response(404, "User not found for email verification code", correlation_id)

            cu = ConsumerUser.query.get(user_uuid)
            cu.email_verified = True
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)


class AccountResendVerificationEmail(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, api_key, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            cu = user.get_user_details()
            ev = EmailVerification.query.filter(EmailVerification.email == cu.email_address).first()
            if ev:
                self.send_verification_email(cu.email_address, cu.fullName, ev.token)
            else:
                ApiResponse.create_response(404, "Original verification not found", correlation_id)
        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)


class GetDeliveries(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, api_key, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            delivery_info_list = Deliveries.get_deliveries_info_for_user(user)

            if not delivery_info_list:
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except DeliveryNotFoundException, dnfe:
            logger.exception(dnfe)
            ApiResponse.create_response(404, 'Delivery not found', correlation_id)
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200, "Success", correlation_id, json=delivery_info_list)

class TrustMileDeliveryInfo(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            delivery_id = kwargs.get('deliveryId', None)
            if not delivery_id:
                ApiResponse.create_response(404, 'deliveryId not supplied', correlation_id)
            user = kwargs.get("user")
            tmd = TrustmileDelivery.query.get(delivery_id)

            if tmd:
                recipient_name = "Unknown recipient"
                recipient_info = tmd.recipient_info
                if recipient_info:
                    recipient_name = recipient_info.get('recipientName')
                result = {
                    'delivery': {
                        'articles': [{'articleId': str(a.id), 'trackingNumber': str(a.tracking_number)}
                                     for a in tmd.articles],
                        'feedbackLeft': tmd.feedback_left(user.id),
                        'isDelivered': tmd.is_delivered(),
                        'recipientName': recipient_name,
                        'secretWord': tmd.secret_word
                    }
                }

            else:
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)

        except HTTPException, hte:
            logger.exception(hte)
            raise hte
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200, "Success", correlation_id,
                                           json=result)

class DelegateDelivery(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            delivery_id = value.get('deliveryId', None)
            email = value.get('email', None)
            if not delivery_id or not email:
                ApiResponse.create_response(400, 'Invalid request', correlation_id)
            user = kwargs.get("user")
            if user.get_user_details().email_address != email:
                logger.warn('User email {0} doesn\'t match the email delegated to: {1}'.format(
                    user.get_user_details().email_address, email))

                ApiResponse.create_response(400, 'Invalid request', correlation_id)

            dd = DeliveryDelegate.query.filter(DeliveryDelegate.delivery_id == delivery_id).all()

            if dd:
                for d in dd:
                    d.completed = True
                consignment_id = Deliveries.get_for_id(delivery_id)
                consignment = Consignment.query.get(consignment_id)

                user.add_consignment(consignment, "Delegated")

            else:
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)

        except HTTPException, hte:
            logger.exception(hte)
            raise hte
        except exc.NoResultFound, nrfe:
            ApiResponse.create_response(404, 'Consignment no found ', correlation_id)
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200, "Success", correlation_id)


class OrderInfo(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        result = None
        try:

            order_id = kwargs.get('orderId', None)
            if not order_id:
                ApiResponse.create_response(404, 'orderId not supplied', correlation_id)
            user = kwargs.get("user")
            order = RetailerIntegrationConsignment.query.join(Consignment).join(UserConsignment).join(User).filter(
                RetailerIntegrationConsignment.order_id == order_id, User.id == user.id).one()

            if order:
                retailer = order.retailer
                result = {
                    'order': {
                        'description': 'Order from {0}'.format(retailer.website_name),
                        'orderId': order.order_id,
                        'retailerName': retailer.website_name,
                        'retailerPhone': retailer.contact_phoneNumber,
                        'retailerImageUrl': config.RETAILER_IMAGE_URL_BASE + retailer.slug + '.png',
                        'retailerHelpUrl': 'https://{0}'.format(retailer.help_url),
                        'orderEmailUrl': user.get_user_details().email_address,
                        'dispatchEmailUrl': retailer.contact_emailAddress
                    }
                }

            else:
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)

        except HTTPException, hte:
            logger.exception(hte)
            raise hte
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200, "Success", correlation_id,
                                           json=result)


class DelegateLink(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        result = None
        try:

            delivery_id = kwargs.get('deliveryId', None)
            if not delivery_id:
                ApiResponse.create_response(404, 'deliveryId not supplied', correlation_id)
            user = kwargs.get("user")
            consignment = Consignment.query.get(delivery_id)

            if consignment:
                email_address = user.get_user_details().email_address
                bdata = {'delivery_id': delivery_id, 'email': email_address}
                branch_link = util.get_branch_link(bdata)

                result = {'correlationID': correlation_id, 'delegateLink': branch_link}
                dd = DeliveryDelegate(delivery_id, branch_link, email_address)
                db.session.add(dd)

            else:
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)

        except HTTPException, hte:
            logger.exception(hte)
            raise hte
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200, "Success", correlation_id,
                                           json=result)


class DeliveryInfo(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            delivery_id = kwargs.get('deliveryId', None)
            if not delivery_id:
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)

            user = kwargs.get("user")

            uc = db.session.query(UserConsignment).join(User).join(Consignment).filter(User.id == user.id).filter(
                Consignment.id == delivery_id).all()

            if len(uc) > 0:
                # should only be one.
                uc = uc[0]
                cons = uc.consignment
                ud = uc.user_description
                retailer_name = uc.retailer_name

            else:
                # To support clicking on a web-link in an email, then deep-linking to that Consignment
                # we need to add this consignments to the users account, assuming that the Consignment exists

                cons = db.session.query(Consignment).filter(Consignment.id == delivery_id).first()
                if cons:
                    user.add_consignment(cons)
                    ud = ''  # empty user description
                    retailer_name = ''
                else:
                    ApiResponse.create_response(404, 'Delivery not found', correlation_id)

            result = None
            courier = cons.courier
            if courier.tracking_info_supported:

                tracking_info_list = Deliveries.trackings_for_consignment(delivery_id)

                # tracking_info_list is an empty list if there are no trackings
                # it is None when the consignment was not found
                if tracking_info_list is None:
                    ApiResponse.create_response(404, 'Delivery info not found', correlation_id)

                result = {'delivery': Deliveries.get_delivery_info_dict(
                    cons, user, ud, retailer_name, tracking_info_list=tracking_info_list)}

            else:
                result = {'delivery': Deliveries.get_delivery_info_dict(cons, user, ud or cons.tracking_number,
                                                                        retailer_name, tracking_info_list=[])}

        except DeliveryNotFoundException, dnfe:
            logger.exception(dnfe)
            ApiResponse.create_response(404, 'Delivery not found', correlation_id)

        except HTTPException, hte:
            logger.exception(hte)
            raise hte
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200, "Success", correlation_id,
                                           json=result)

class DeliveryInfoAnonymous(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:

            courier_slug = kwargs.get('courierSlug', None)
            tracking_number = kwargs.get('trackingNumber', None)
            if not courier_slug or not tracking_number:
                ApiResponse.create_response(404, 'Delivery not found', correlation_id)
            #find courier
            try:
                courier = Courier.retrieve_courier(courier_slug)
            except Exception, e:
                mapped_name = Retailer.find_courier_mapping( courier_slug)
                courier = Courier.retrieve_courier(mapped_name)

            if not courier:
                ApiResponse.create_response(404, 'Courier not found', correlation_id)


            retailer = None
            qs = kwargs.get('query_string')
            if qs:
                r = qs.get('retailer')
                if r:
                    retailer = Retailer.get(website_name=r)

            cons_all = Consignment.get_consignments(courier.courier_slug, tracking_number)
            if not len(cons_all):
                cons = Consignment(courier, tracking_number)
                db.session.add(cons)
                db.session.commit()
                if courier.tracking_info_supported:
                    logger.debug(
                        u"Updating shipping info on consignment {0} for tracking {1}".format(cons.id, tracking_number))
                    #r_result = tasks.update_shipping_info_for_consignment.apply_async(args=(cons.id,), countdown=3)
                    r_result = tasks.update_shipping_info_for_consignment(cons.id)
            else:
                cons = cons_all[0]

            if retailer:
                cons.set_retailer( retailer, 'URL')

            if courier.tracking_info_supported:

                tracking_info_list = Deliveries.trackings_for_consignment(cons.id)

                # tracking_info_list is an empty list if there are no trackings
                # it is None when the consignment was not found
                if tracking_info_list is None:
                    ApiResponse.create_response(404, 'Delivery info not found', correlation_id)

                result = {'delivery': Deliveries.get_base_info_dict(cons, tracking_info_list=tracking_info_list)}
            else:
                result = {'delivery':  Deliveries.get_base_info_dict(cons, tracking_info_list=[])}

        except DeliveryNotFoundException, dnfe:
            logger.exception(dnfe)
            ApiResponse.create_response(404, 'Delivery not found', correlation_id)

        except HTTPException, hte:
            logger.exception(hte)
            raise hte
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)

        return ApiResponse.create_response(200, "Success", correlation_id,
                                           json=result)


class CardLookup(BaseOperation):
    @log_operation
    @commit_on_success
    @api_security
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            card_number = kwargs.get('cardId', None)
            if not card_number:
                ApiResponse.create_response(400, 'Bad request, cardId missing', correlation_id)
            card = DeliveryCard.query.filter(DeliveryCard.card_number == card_number).first()
            if not card:
                ApiResponse.create_response(404, 'Card not found in system', correlation_id)

            delivery = TrustmileDelivery.query.get(card.delivery_id)

            neighbour_name = delivery.neighbour.fullName
            neighbour_address = UserAddressSchema().dump(delivery.neighbour.user.current_address).data
            neighbour_phone = delivery.neighbour.user.current_address.phoneNumber
            response_json = {
                'neighbourName': neighbour_name,
                'neighbourAddress': neighbour_address,
                'neighbourPhone': neighbour_phone,
                'secretWord': delivery.secret_word,
                'articleCount': len(delivery.articles),
                'recipientInfo': delivery.recipient_info,
                'courierName': delivery.articles[0].courier.courier_name,
                'correlationID': correlation_id}

            result = ApiResponse.create_response(200, 'Success', correlation_id=correlation_id, json=response_json)
            return result
        except HTTPException as hte:
            logger.exception(hte)
            raise
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)


class PromotionClickRequest(BaseOperation):
    @log_operation
    @api_security
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            promotion_view_id = kwargs.get('promotionViewId', None)
            if not promotion_view_id:
                ApiResponse.create_response(400, 'Bad request, cardId missing', correlation_id)

            tasks.create_promotion_click(promotion_view_id)
            result = ApiResponse.create_response(200, 'Success', correlation_id=correlation_id)
            return result
        except HTTPException as hte:
            logger.exception(hte)
            raise
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)


class AccountForgotPassword(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            email_address = value.get('emailAddress')
            if email_address:
                cu = get_user_by_email(email_address)
                if cu:
                    full_name = cu.fullName or "YOU"
                    cu.reset_password()
                    self.send_password_reset(cu, full_name)
                else:
                    ApiResponse.create_response(404, 'Email address not found', correlation_id)
            else:
                ApiResponse.create_response(404, 'Email address not found', correlation_id)

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


class AccountResetPasswordGet(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        reset_token = kwargs.get('resetToken')
        if reset_token:
            cu = ConsumerUser.find_reset_token(reset_token)

            if cu:
                return ApiResponse.create_response(200, "Success", correlation_id,
                                                   json={'emailAddress': mask_email_address(cu.email_address)})

        ApiResponse.create_response(404, 'Reset token not found', correlation_id)


class AccountResetPasswordPost(BaseOperation):
    @log_operation
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        reset_token = kwargs.get('resetToken')
        new_password = value.get('newPassword')

        if reset_token:
            cu = ConsumerUser.find_reset_token(reset_token)

            if cu:
                cu.secret = new_password
            return ApiResponse.create_response(200, "Success", correlation_id)

        ApiResponse.create_response(404, 'Reset token not found', correlation_id)


class RecipientHandoverOperation(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        neighbour = kwargs['user']
        article_ids = value['articleIds']

        recipient_name = value.get('recipientName', None)

        if article_ids and len(article_ids) > 0:
            # find the trustmile delivery for these article ids
            # Assert recipient is intended recipient if possible, through existing db records
            articles = Article.query.filter(Article.id.in_(article_ids)).all()

            if not articles or len(article_ids) < 1:
                ApiResponse.create_response(403, 'articles ids not found for neighbour', correlation_id)

            neighbour_user = neighbour.get_user_details()
            tm_delivery = TrustmileDelivery.retrieve_for_recipient_handover(neighbour_user, articles)

            tm_delivery.state = DeliveryState.RECIPIENT_RECEIVED.value
            tm_delivery.update_info(recipient_name=recipient_name)
            notify_couriers([a.tracking_number for a in articles], "Received", config.COURIERS_PLEASE_CONTRACTOR_NUM)
            logger.debug(u"Updated TMD: %s" % tm_delivery.to_json())
            return ApiResponse.create_response(200, "success", correlation_id)

        else:
            ApiResponse.create_response(403, 'articles ids not found for neighbour', correlation_id)


class GetTrustmileDeliveryForArticle(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        tracking_number = kwargs.get('trackingNumber', None)
        user = kwargs.get('user', None)
        if not tracking_number:
            ApiResponse.create_response(401, 'No tracking number', correlation_id)

        if not user:
            ApiResponse.create_response(404, 'Not authorized', correlation_id)

        # Must be neighbour to call the lookup.
        cons_user = user.consumer_user

        tmd = TrustmileDelivery.get_by_tracking_for_neighbour(cons_user, tracking_number,
                                                              state=DeliveryState.TRANSIT_TO_NEIGHBOUR.value)

        if not tmd:
            logger.debug(u"no tm_delivery found: {0}".format(tracking_number))
            return ApiResponse.create_response(404, 'Not found', correlation_id)

        logger.debug(u"tm_delivery found: {0}".format(tmd.to_json()))
        return ApiResponse.create_response(200, "success", correlation_id,
                                           json=tmd.to_json())


class NeighbourReceive(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        tmdId = kwargs.get('deliveryId', None)
        c_user = kwargs.get('user', None)
        if not tmdId:
            ApiResponse.create_response(401, 'No TMD Id', correlation_id)

        if not c_user:
            ApiResponse.create_response(404, 'Not authorized', correlation_id)
        tmd = TrustmileDelivery.query.filter(
            and_(TrustmileDelivery.id == tmdId,
                 TrustmileDelivery.state == DeliveryState.TRANSIT_TO_NEIGHBOUR.value)).one()

        if not tmd:
            logger.debug(u"no tm_delivery found: {0}".format(tmdId))
            ApiResponse.create_response(404, 'Not found', correlation_id)

        logger.debug(u"tm_delivery found: {0}".format(tmd.to_json()))
        tmd.state = DeliveryState.NEIGHBOUR_RECEIVED.value
        tmd.neighbour = c_user.consumer_user
        notify_couriers([a.tracking_number for a in tmd.articles], "Neighbour Received", config.COURIERS_PLEASE_CONTRACTOR_NUM)
        return ApiResponse.create_response(200, "success", correlation_id,
                                           json=tmd.to_json())


class DeleteDelivery(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, user, api_key, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            logger.debug(u'api_key for delete {0}'.format(api_key))
            delivery_id = value.get('deliveryID', None)
            if not delivery_id:
                ApiResponse.create_response(400, "Missing delivery id from delete", correlation_id)

            user.delete_consignment(delivery_id)

            # we can't delete the consignment unless no users have it associated
            # however sqlalchemy can handle that
            # but we should not delete any way as we may have courier billing information attached
            # Consignment.delete_by_id(delivery_id)

        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)


class FeedbackPost(BaseOperation):
    @log_operation
    @api_security
    @commit_on_success
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            user_email_address = value.get('consumerEmail')
            if not user_email_address:
                ApiResponse.create_response(400, "user_email_address missing or blank", correlation_id)
            if len(user_email_address) > 255:
                ApiResponse.create_response(400, "user_email_address exceeds 255 characters", correlation_id)
            user_full_name = value.get('consumerName')
            if not user_full_name:
                ApiResponse.create_response(400, "user_full_name missing or blank", correlation_id)
            if len(user_full_name) > 255:
                ApiResponse.create_response(400, "user_full_name exceeds 255 characters", correlation_id)
            feedback_message = value.get('feedbackMessage')
            if not feedback_message:
                ApiResponse.create_response(400, "feedback_message missing or blank", correlation_id)
            if len(feedback_message) > 4000:
                ApiResponse.create_response(400, "feedback_message exceeds 4000 characters", correlation_id)

            user = kwargs.get('user')

            fm = FeedbackMessage(user_email_address, user_full_name, feedback_message, user)
            db.session.add(fm)

            tasks.send_feedback.delay(user_full_name, user_email_address, feedback_message, str(user.id))


        except HTTPException, he:
            logger.exception(he)
            raise he
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)
        else:
            return ApiResponse.create_response(200, "Success", correlation_id)


class Testpromotion(BaseOperation):
    @log_operation
    @api_security
    def perform(self, value, **kwargs):
        correlation_id = kwargs.get('correlation_id', uuid.uuid4())
        try:
            #promotion_view_id = kwargs.get('promotionViewId', None)
            #if not promotion_view_id:
            #   ApiResponse.create_response(400, 'Bad request, cardId missing', correlation_id)

            #tasks.create_promotion_click(promotion_view_id)
            result = ApiResponse.create_response(200, 'Success', correlation_id=correlation_id)
            return result
        except HTTPException as hte:
            logger.exception(hte)
            raise
        except Exception, e:
            logger.exception(e)
            ApiResponse.create_response(500, 'Unknown error', correlation_id)


cons_ops = {
    ('deliveries', 'GET'): {'location': 'headers', 'operation': GetDeliveries},
    ('deliveries', 'POST'): {'location': 'json', 'operation': AddDelivery},
    ('deliveries', 'DELETE'): {'location': 'json', 'operation': DeleteDelivery},

    ('deliveries_deliveryId', 'GET'): {'location': 'path', 'operation': DeliveryInfo},
    ('deliveries_deliveryId', 'PUT'): {'location': 'json', 'operation': UpdateDelivery},
    ('order_orderId', 'GET'): {'location': 'path', 'operation': OrderInfo},
    ('deliveries_delegateLink_deliveryId', 'GET'): {'location': 'path', 'operation': DelegateLink},
    ('deliveries_delegate', 'POST'): {'location': 'json', 'operation': DelegateDelivery},
    ('deliveries_tracking_deliveryId', 'GET'): {'location': 'path', 'operation': DeliveryInfo},
    ('deliveries_trustmile_deliveryId', 'GET'): {'location': 'path', 'operation': TrustMileDeliveryInfo},
    ('deliveries_neighbourReceiveLookup_trackingNumber', 'GET'): {'location': 'path', 'operation':
        GetTrustmileDeliveryForArticle},
    ('deliveries_cardLookup_cardId', 'GET'): {'location': 'path', 'operation': CardLookup},
    ('deliveries_neighbourReceive_deliveryId', 'POST'): {'location': 'json', 'operation': NeighbourReceive},
    ('deliveries_feedback_deliveryId', 'POST'): {'location': 'json', 'operation': DeliveryFeedbackOperation},
    ('deliveries_recipientHandover_deliveryId', 'POST'): {'location': 'json', 'operation': RecipientHandoverOperation},
    ('account_verifyEmail_verificationCode', 'GET'): {'location': 'kwargs', 'operation': VerifyEmail},
    ('account', 'PUT'): {'location': 'json', 'operation': AccountUpdate},
    ('account_reverifyEmail', 'PUT'): {'location': 'headers', 'operation': AccountResendVerificationEmail},
    ('account_login', 'POST'): {'location': 'json', 'operation': AccountLoginOperation},
    ('account', 'GET'): {'location': 'headers', 'operation': AccountRetrieve},
    ('account_register', 'POST'): {'location': 'json', 'operation': AccountRegister},
    ('account', 'DELETE'): {'location': 'headers', 'operation': AccountDelete},
    ('account_password', 'POST'): {'location': 'json', 'operation': PasswordUpdate},
    ('account_forgotPassword', 'POST'): {'location': 'json', 'operation': AccountForgotPassword},
    ('account_resetPassword_resetToken', 'GET'): {'location': 'headers', 'operation': AccountResetPasswordGet},
    ('account_resetPassword_resetToken', 'POST'): {'location': 'json', 'operation': AccountResetPasswordPost},

    ('user_presence', 'POST'): {'location': 'json', 'operation': SetUserPresence},
    ('feedback', 'POST'): {'location': 'json', 'operation': FeedbackPost},
    ('anonymous_tracking_courierSlug_trackingNumber', 'GET'): {'location': 'path', 'operation': DeliveryInfoAnonymous},
    ('promotion_click_promotionViewId', 'GET'): {'location': 'path', 'operation': PromotionClickRequest},
    ('account_anonymous_register', 'POST'): {'location': 'json', 'operation': AnonymousRegistration},
    ('promotion_viewlist', 'GET'): {'location': 'json', 'operation': Testpromotion}

}


""" Note this factory method requires no conflict of 'path' in the relevant operation dictionaries - consumer_operations
    and courier_operations """
class ConsumerOperationsFactory(object):
    def factory(operation_name, method):
        operation = cons_ops.get((operation_name, method))['operation']
        return operation()

    factory = staticmethod(factory)
