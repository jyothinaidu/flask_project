import logging
import aftership
import time
import datetime
import mandrill
import pytz
from sqlalchemy.orm import exc
from sqlalchemy.sql.elements import and_

import config
from app.async.celery_app import capp
from app.exc import NoTrackingResultsException, NoCheckpointsException, TrackingResultsRetryException, \
    ShippingInfoUnsupportedException, NoAddressSetException
from app import db
from app.location.geocode import Geocoder
from app.messaging.push import PushNotification
from app.model.meta.schema import Location, UserPresence, Address
from celery.utils.log import get_task_logger
import csv
import os
from ftplib import FTP

from app.promotion.model import PromotionView, PromotionClick
from app.users.model import User


__author__ = 'james'

logger = get_task_logger(__file__)

logger.setLevel(logging.DEBUG)


@capp.task(bind=True)
def update_address_location(self, address_id):
    from app.model.meta.schema import Address
    wait_time = 1
    for i in xrange(3):
        try:
            logger.debug(u"Looking for address with id {0}".format(address_id))
            addr = db.session.query(Address).filter(Address.id == address_id).one()
            str_address = "{0} {1}, {2}, {3}, {4}, {5}".format(addr.addressLine1, addr.addressLine2, addr.suburb,
                                                               addr.postcode, addr.state, addr.countryCode)
            geocoder = Geocoder(config.GOOGLE_LOCATION_KEY)
            loc = geocoder.geocode(str_address)
            logger.debug(u"Location is {0}".format(loc))

            addr.location = Location(loc.latitude, loc.longitude)
            db.session.commit()
            logger.info(
                u"Updated addr {0} with latitude: {1}, longitude: {2}".format(addr.id, loc.latitude, loc.longitude))
            break

        except Exception, e:
            logger.exception(e)
            time.sleep(wait_time)
            db.session.rollback()
            wait_time += 5

    db.session.close()

@capp.task(bind=True)
def post_user_presence(self, user_id, status, latitude, longitude):

    user_presence = UserPresence(status, latitude, longitude)

    db.session.add(user_presence)

    logger.debug(u"User's location being set to latitude {0}, longitude {1}".format(
        latitude, longitude))
    user = User.query.get(user_id)
    c_addr = user.current_address
    if c_addr:
        c_addr.user_presence.append(user_presence)
        db.session.commit()
    else:
        raise NoAddressSetException("No Current address set")


@capp.task(bind=True, default_retry_delay = 120, max_retries = 3)
def associate_delivery_card(self, card_notification):
    from app.deliveries.model import TrustmileDelivery, DeliveryCard
    from app.users.model import ConsumerUser
    try:
        label_number = card_notification['labelNumber']
        tmd = TrustmileDelivery.by_tracking(label_number)
        logger.info('Processing delivery card label: {0}'.format(label_number))
        if tmd:
            logger.info(u'Received couriers please notification on TrustmileDelivery id: {0}, labelNumber {1}'.format(
                tmd.id, label_number))
            email_address = card_notification['emailAddress']
            tmd.update_info(recipient_name=card_notification['contactName'],
                            recipient_phone=card_notification['mobileNumber'],
                            email_address=email_address, source='couriersPlease')

            dc = DeliveryCard(card_notification['missedDeliveryCardNumber'], tmd.id)

            recipient = ConsumerUser.query.filter(ConsumerUser.email_address == email_address).first()
            if recipient and not tmd.recipient:
                logger.info(u'Found recipient {0} in system for couriers please notification card id {1}'.format(
                    recipient.email_address, dc.card_number))
                tmd.recipient = recipient
                send_shipping_notification(
                    recipient.email_address, "Card left for new package", "TrustMile card left", tmd.id)
            db.session.add(tmd)
            db.session.add(dc)

            db.session.commit()

            logger.info('Successfully associated card: {0}, delivery_id {1}'.format(label_number, tmd.id))
        else:
            logger.info('Retrying for delivery card label: {0}'.format(label_number))
        self.retry()
    except Exception, e:
        logger.exception(e)
    finally:
        db.session.close()

@capp.task(bind=True)
def create_promotion_click(self, promotion_view_id):

    logger.info('Creating promotion click for promotion view {0}'.format(promotion_view_id))

    promotion_view = PromotionView.query.filter(PromotionView.id == promotion_view_id).first()
    if not promotion_view:
        logger.error(404, 'No promotion found for promotion view id {0}'.format(promotion_view_id))
    promotion_click = PromotionClick(promotion_view)
    db.session.add(promotion_click)
    db.session.commit()


@capp.task(bind=True)
def send_email_verification(self, email_address, to_name, verification_code):
    client = mandrill.Mandrill(apikey=config.EMAIL_API_KEY)

    try:
        message = {
            'to': [{'email': email_address,
                    'name': to_name,
                    'type': 'to'}],

            'global_merge_vars': [{'content': to_name, 'name': 'RECIPIENT_NAME'},
                                  {'name': 'VERIFY_URL',
                                   'content': config.EMAIL_VERIFY_URL + u'{0}'.format(
                                       verification_code)}],

            'merge_language': 'handlebars',

        }
        send_result = client.messages.send_template(template_name='trustmile-email-verification',
                                                    template_content=None, message=message)
        logger.info(u'Sent email to: {0}, code: {1}, name: {2} - with send id: {3}, status: {4}'.format(
            email_address, verification_code, to_name, send_result[0]['_id'], send_result[0]['status']))
        '''
        [{'_id': 'abc123abc123abc123abc123abc123',
          'email': 'recipient.email@example.com',
          'reject_reason': 'hard-bounce',
          'status': 'sent'}]
        '''

    except mandrill.Error, e:
        # Mandrill errors are thrown as exceptions
        logger.exception(e)
        raise exc.EmailSendException(e)
    else:
        return send_result


@capp.task(bind=True)
def send_password_reset(self, email_address, full_name, reset_token):
    client = mandrill.Mandrill(apikey=config.EMAIL_API_KEY)
    try:

        message = {
            'to': [{'email': email_address,
                    'name': full_name,
                    'type': 'to'}],

            'global_merge_vars': [{'content': full_name, 'name': 'RECIPIENT_NAME'},
                                  {'name': 'RESET_URL',
                                   'content': config.PASSWORD_RESET_URL + u'{0}'.format(
                                       reset_token)},
                                  {'name': 'EMAIL_ADDRESS', 'content': email_address}
                                  ],

            'merge_language': 'handlebars'

        }
        send_result = client.messages.send_template(template_name='trustmile-password-reset',
                                                    template_content=None, message=message)
        logger.info(u'Sent password reset email to {0} with send id: {1}, status: {2}'.format(email_address,
                                                                                             send_result[0]['_id'],
                                                                                             send_result[0]['status']))

        '''
        [{'_id': 'abc123abc123abc123abc123abc123',
          'email': 'recipient.email@example.com',
          'reject_reason': 'hard-bounce',
          'status': 'sent'}]
        '''

    except mandrill.Error, e:
        # Mandrill errors are thrown as exceptions
        logger.exception(e)
        raise exc.EmailSendException(e)
    else:
        return send_result


@capp.task(bind=True)
def send_feedback(self, user_full_name, user_email_address, feedback_message, user_id):
    client = mandrill.Mandrill(apikey=config.EMAIL_API_KEY)
    logger.info('User {0} sending feedback'.format(user_email_address))
    try:
        message = {
            'to': [{'email': config.EMAILADDRESSES_FEEDBACK,
                    'name': 'TrustMile Feedback',
                    'type': 'to'}],
            'headers': {'Reply-To': user_email_address},
            'global_merge_vars': [{'name': 'user_full_name', 'content': user_full_name},
                                  {'name': 'user_email_address', 'content': user_email_address},
                                  {'name': 'feedback_message', 'content': feedback_message},
                                  {'name': 'user_id', 'content': user_id},
                                  ],

            'merge_language': 'handlebars',

        }
        send_result = client.messages.send_template(template_name='trustmile-feedback',
                                                    template_content=None, message=message)
        logger.info(u'Sent email with send id: {0}, status: {1}'.format(send_result[0]['_id'], send_result[0]['status']))
        '''
        [{'_id': 'abc123abc123abc123abc123abc123',
          'email': 'recipient.email@example.com',
          'reject_reason': 'hard-bounce',
          'status': 'sent'}]
        '''

    except mandrill.Error, e:
        # Mandrill errors are thrown as exceptions
        logger.exception(e)
        raise exc.EmailSendException(e)
    else:
        return send_result

@capp.task(bind=True)
def archive_old_trustmile_deliveries(args):
    logger.debug(u'args {0}'.format(args))

    from app.deliveries.model import TrustmileDelivery, DeliveryState
    current_time = datetime.datetime.utcnow()
    archive_time = current_time - datetime.timedelta(days=config.ARCHIVE_DAYS)
    archive_time = archive_time.replace(tzinfo=pytz.utc)

    try:
        tmds = TrustmileDelivery.query.filter(and_(TrustmileDelivery.state == DeliveryState.RECIPIENT_RECEIVED.value,
                                                   TrustmileDelivery.created_at < archive_time)).all()
        if tmds:
            logger.info(u'Archiving {0} trustmile deliveries'.format(len(tmds)))
            for t in tmds:
                t.state = DeliveryState.TIME_ARCHIVED.value
                db.session.add(t)
            db.session.commit()
        else:
            logger.info(u'No deliveries to archive')
    except Exception, e:
        logger.exception(e)
    finally:
        db.session.close()


@capp.task(bind=True)
def check_expired_locations(args):
    logger.debug(u'args {0}'.format(args))
    now = datetime.datetime.utcnow()
    now = now.replace(tzinfo=pytz.utc)
    try:

        users = User.query.join(Address).join(UserPresence).filter(User.at_home == True)
        count = 0
        for u in users:
            if u.user_address:
                up = u.user_address[0].user_presence
                if up:
                    latest_up = up[0]
                    diff = now - latest_up.created_at
                    if diff.seconds > 3600:
                        count += 1
                        logger.info('User {0}, {1} expired, last user_presence updated {2}'.format(
                            u.id, u.consumer_user.email_address, latest_up.created_at))
                        u.at_home = False
                    else:
                        logger.info(
                            'User {0}, {1} still at home, last user_presence updated {2}, {3} seconds ago'.format(
                                u.id, u.consumer_user.email_address, latest_up.created_at, diff.seconds))
        logger.info('Updating {0} users with expired at home presences'.format(count))
        db.session.commit()
    except Exception, e:
        logger.exception(e)
    finally:
        db.session.close()


@capp.task(bind=True)
def send_couriers_please_notifications(args):
    logger.debug(u"args {0}".format(args))
    from app.deliveries.model import CouriersPleaseNotifications, LatestCouriersPleaseMarker
    latest_run = LatestCouriersPleaseMarker.query.order_by(LatestCouriersPleaseMarker.id.desc()).first()
    notifications = []
    if latest_run:
        notifications = CouriersPleaseNotifications.query.filter(
            CouriersPleaseNotifications.created_at > latest_run.created_at).all()
        # Write output file and sftp it

    else:
        notifications = CouriersPleaseNotifications.query.all()
    if len(notifications) > 0:
        logger.info(u"Writing {0} couriers please notifications file".format(len(notifications)))
        write_cp_outfile(notifications)
        db.session.add(LatestCouriersPleaseMarker())
        db.session.commit()
        db.session.close()
    else:
        logger.info(u'No couriers please notifications to write')


def write_cp_outfile(notifications):

    def format_date(dt):
        return dt.strftime('%Y%m%d%H%M')

    cp_filename = "couriers_please_trustmile_{0}.csv".format(format_date(datetime.datetime.now()))
    with open(cp_filename, 'wb') as cp_file:
        cp_writer = csv.writer(cp_file, delimiter='|')
        for n in notifications:
            row = [n.tracking_number, n.consignment_number, format_date(n.created_at), n.scan_event,
                                 n.contractor_num, n.exception_reason]
            logger.debug(u"Writing cp out: {0}".format(row))
            cp_writer.writerow(row)

    logger.info(u'Uploading file: {0} to site {1}'.format(cp_filename, config.COURIERS_PLEASE_FTP_HOST))
    ftp = FTP(config.COURIERS_PLEASE_FTP_HOST, config.COURIERS_PLEASE_FTP_USER, config.COURIERS_PLEASE_FTP_PASS)
    ftp.cwd(config.COURIERS_PLEASE_FTP_DIR)
    ftp.storlines("STOR " + cp_filename, open(cp_filename))
    ftp.quit()
    # TODO: Ultimately push the file up to S3 and then remove it from the server.
    os.remove(cp_filename)


@capp.task(bind=True)
def send_push(self, email_address, data=None, message=""):
    logger.info('Sending push to {0}, data {1}, message {2}'.format(email_address, data, message))

    return PushNotification.send_push(email_address, data=data, message=message)


@capp.task(bind=True)
def send_shipping_notification(email_address, consignment_description, checkpoint_status,
                               consignment_id, badge=None):
    from app.messaging.push import PushNotification
    logger.info(u'Sending shipping notification to {0} for delivery id {1}'.format(email_address, consignment_id))
    PushNotification.send_new_tracking_notification(email_address, consignment_id, consignment_description,
                                                    checkpoint_status)


@capp.task(bind=True)
def update_shipping_info_for_consignments(self, consingment_ids):
    for cid in consingment_ids:
        update_shipping_info_for_consignment(cid)

@capp.task(bind=True)
def update_shipping_info_for_consignment(self, consignment_id):
    from app.deliveries.model import Consignment
    wait_time = 0
    success = False
    for n in xrange(3):
        try:
            logger.info(u"Updating tracking info for consignment {0}".format(consignment_id))
            cons = db.session.query(Consignment).filter(Consignment.id == consignment_id).one()
            tracking_number = cons.tracking_number
            courier_slug = cons.courier.courier_slug
            tracking_info_supported = cons.courier.tracking_info_supported
            if not (tracking_number and courier_slug):
                raise TrackingResultsRetryException(
                    u"No tracking number found for consignment {0}, with tracking_number {1}".format(consignment_id,
                                                                                                     tracking_number))
            if not tracking_info_supported:
                raise ShippingInfoUnsupportedException(u'Shipping information not supported for courier {0}'.format(
                    courier_slug))

            tracking_results = retrieve_tracking_info(courier_slug, tracking_number)
            if not tracking_results:
                create_tracking(courier_slug, tracking_number)
                # TODO: need to then poll for the tracking unless we can get notified somehow.
                tracking_results = retrieve_tracking_info(courier_slug, tracking_number, retry=True)

            if tracking_results:
                if not tracking_results.get(u'checkpoints', None) or len(tracking_results.get(u'checkpoints')) < 1:
                    raise NoCheckpointsException(u"No checkpoints for consignment {0} with tracking number {1}".format(
                        consignment_id, tracking_number))

                # this was changed from
                # cons.tracking_info = tracking_results
                # so it is more resilient.  Additionally the aftership webhook appears to fire
                # when a new tracking is created ...
                logger.info(
                    u"Setting tracking info for consignment {0}, info {1}".format(str(cons.id), tracking_results))
                # TODO: since this is an aysnc call, and update_tracking calls async again, this should be fixed.
                cons.update_tracking(tracking_results)
                for a in cons.articles:
                    a.tracking_info = cons.tracking_info
                db.session.commit()
                #db.session.close()
                success = True
                logger.info(u"Finished updating tracking info for tracking number: {0}".format(tracking_number))
                break
            else:
                raise NoTrackingResultsException(
                    u"Tracking results not found for tracking number {0}".format(tracking_number))

        except exc.NoResultFound, e:
            wait_time = wait_and_log(wait_time, e)
            continue
        except NoCheckpointsException, nce:
            logger.exception(nce)
            break
        except aftership.APIv4RequestException, api_exc:
            logger.exception(api_exc)
            break
        except NoTrackingResultsException, ntre:
            logger.exception(ntre)
            break
        except ShippingInfoUnsupportedException, siue:
            logger.exception(siue)
            break
        except TrackingResultsRetryException, trre:
            wait_time = wait_and_log(wait_time, trre)
            continue
        except Exception, ee:
            logger.exception(ee)
            break

    #db.session.close()
    return success


def wait_and_log(wait_time, excp):
    logger.exception(u"Error {0}".format(excp))
    wait_time += 1
    time.sleep(wait_time)
    return wait_time


def create_tracking(courier_slug, tracking_number):
    datasource = TrackingDataSource(AftershipDelegate())
    datasource.post_new_tracking(courier_slug, tracking_number)


def retrieve_tracking_info(courier_slug, tracking_number, retry=False):
    datasource = TrackingDataSource(AftershipDelegate())
    tracking_results = datasource.retrieve_tracking_for_courier(courier_slug, tracking_number)
    if retry and not tracking_results:
        for n in xrange(3):
            time.sleep(2)
            tracking_results = datasource.retrieve_tracking_for_courier(courier_slug, tracking_number)
            if tracking_results:
                break
    return tracking_results


class TrackingDataSource:
    def __init__(self, source_delegate=None):
        self.source_delegate = source_delegate

    def retrieve_trackings_for_number(self, tracking_number):
        return self.source_delegate.get_trackings(tracking_number)

    def retrieve_tracking_for_courier(self, courier_slug, tracking_number):
        return self.source_delegate.get_trackings(courier_slug, tracking_number)

    def post_new_tracking(self, courier_slug, tracking_number):
        return self.source_delegate.post_new_tracking(courier_slug, tracking_number)

    def retrieve_tracking_with_filter(self, filter):
        return self.source_delegate.get_trackings_with_filter(filter)


class AftershipDelegate:
    def __init__(self):
        self.api = aftership.APIv4(config.AFTERSHIP_API_KEY, datetime_convert=False)

    def get_trackings(self, courier_slug, tracking_number):
        try:
            # TODO: right now going to get everything in our account for trackings
            trackings = self.api.trackings.get(courier_slug, tracking_number)

            if trackings.get('meta', {}).get('message') == u'Tracking does not exist.':
                return None

            return trackings["tracking"]

        except aftership.APIv4RequestException:
            logger.exception(u"Api Exception")
            return None

    def get_trackings_with_filter(self, filter):

        # select specific filters we support, instead of blindly
        # the filter object into the AfterShip API
        filter_args = {"limit": 1000000}
        if filter.get("created_at_min"):
            filter_args["created_at_min"] = filter["created_at_min"]
        if filter.get("created_at_max"):
            filter_args["created_at_max"] = filter["created_at_max"]

        try:
            trackings = self.api.trackings.get(**filter_args)["trackings"]

        except:
            logger.exception(u"Api Exception")
            trackings = {}

        return trackings

    def post_new_tracking(self, courier_slug, tracking_number):
        try:
            new_tracking = {
                "slug": courier_slug,
                "tracking_number": tracking_number,
                "title": "Trustmile Created Tracking",
                "emails": [
                    "trackings@trustmile.com"
                ],
            }
            result = self.api.trackings.post(tracking=new_tracking)
        except aftership.APIv4RequestException, e:
            logger.exception(e.message())
            if e.args[0].get('meta').get('message') == 'Tracking already exists.':
                pass
            else:
                raise e
        except Exception, e:
            logger.exception(u"Unable to post new tracking")
            raise e

        else:
            logger.debug(u"Posted new item to aftership tracking_number {0}, slug {1}, aftership result {2}".format(
                tracking_number, courier_slug, result))
            return result

    @classmethod
    def class_method_x(cls):
        pass
