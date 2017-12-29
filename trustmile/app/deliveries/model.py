import copy

import time
import datetime

from Cython.Plex.Regexps import RE
from geoalchemy2 import Geography
from sqlalchemy import DateTime, Boolean, ForeignKey, event, or_, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import and_
from sqlalchemy.sql.functions import current_time
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import case

import config
from app.exc import DeliveryNotFoundException, CourierNotFoundException
from app.messaging.push import PushNotification
from app.ops.base import DeliveryState
from app.model.meta.orm import UniqueMixin, many_to_one, one_to_many, one_to_one
from app.model.meta.schema import TableColumnsBase, Address
from app.model.meta.types import GUID
from app.async import tasks
from app.promotion.model import Promotion, PromotionView
from app.retailer_integration.model import RetailerIntegrationConsignment, Retailer
from app.users.model import UserConsignment, ConsumerUser, User
from app import db
from sqlalchemy.orm import exc, relationship, joinedload
import logging
import random
from collections import defaultdict

__author__ = 'james'


logger = logging.getLogger()

TRUSTMILE_DELIVERY_STATE_MAP = {
    'NEWLY_CREATED': "Newly created",
    'TRANSIT_TO_NEIGHBOUR': "In Transit To Neighbour",
    'NEIGHBOUR_RECEIVED': "Deliveries In My Care",
    "RECEPIENT_RECEIVED": "Delivered",

}

class DeliveryFeedbackMixin:
    def feedback_left(self, user_id):
        feedback = db.session.query(DeliveryFeedback).join(ConsumerUser).join(User).filter(and_(
            DeliveryFeedback.delivery_id == self.id, User.id == user_id)).first()
        logger.debug(u'Feedback for id {0} is {1}'.format(str(self.id), feedback is not None))
        return feedback is not None


class Consignment(db.Model, UniqueMixin, DeliveryFeedbackMixin, TableColumnsBase):
    __tablename__ = 'consignment'
    tracking_number = db.Column(db.String(255), nullable=False)
    num_items = db.Column(db.SmallInteger, nullable=False)
    """ The reason for using relationship and courier_id here is because adding the unique constraint
        can't find courier_id with the normal many_to_one declaration """
    courier_id = db.Column(GUID(), ForeignKey('courier.id'), index=True)
    courier = relationship('Courier', backref='consignments', lazy = 'joined')

    articles = one_to_many('Article', backref='consignment', lazy='select')
    tracking_info = db.Column(JSON, default=None)
    # an event listener sets this column
    # needed so we can page the aftership results and don't hit the 1,000,000 trackings limit
    tracking_info_created_at = db.Column(DateTime(timezone=True))
    # an event listener sets this column
    # when this is set to true, no further updates will be retrieved from AfterShip
    is_closed = db.Column(Boolean, default=False)
    # an event listener sets this column
    # this it the id of the tracking object we get back from AfterShip
    tracking_external_id = db.Column(db.String)

    retailer = many_to_one('Retailer', backref='consignment', lazy='select')

    latest_status_col = db.Column(db.String(512), default='', nullable=True)
    is_delivered_col = db.Column(db.Boolean, default=False, nullable=True)

    #this is used to enforce which retailer 'owns' the consignment based on the source of the retailer-courier mapping info
    # the heirarchy of trust is
    # 'URL' - was passed in via a URL, we 1/2 trust this.  It probably came from a link provided by a retailer, but we cant gurantee it.
    # 'Integration' - This is a trusted source and overrides other sources.
    retailer_source =  db.Column(db.String(15))
    #Whats this consignment entered into the system by a user, or via the retailer integration
    #has values of either 'user' or 'retailer'
    created_by = db.Column(db.String(15))
    # this gets set by the User class, in the consignments property
    # it's value is taken from the UserConsignment.user_description field
    # user_description = None
    __table_args__ = (UniqueConstraint('courier_id', 'tracking_number', name='courier_tracking_unique_constr'),)

    def __init__(self, courier, tracking_number, articles=[], num_items=1):
        self.courier = courier
        self.tracking_number = tracking_number
        self.num_items = num_items
        self.articles = articles

    def __eq__(self, other):
        if hasattr( other, 'tracking_number') and hasattr( other, 'courier'):
            if self.tracking_number == other.tracking_number and self.courier == other.courier:
                return True

        return False

    def get_order_id(self):
        if self.integration_consignment:
            return self.integration_consignment.order_id
        else:
            return None

    def get_retailer_image_url(self):
        if self.retailer:
            if self.retailer.slug:
                return config.RETAILER_IMAGE_URL_BASE + self.retailer.slug + '.png'

        return None

    def get_retailer_name(self):
        if self.retailer:
            return self.retailer.website_name
        else:
            return None

    def set_retailer(self, retailer, source):
        if source != 'URL' and source != 'Integration':
            raise Exception( 'Supplied source is invalid {0}'.format(source))

        if not retailer:
            raise Exception( 'retailer can not be none')

        if not self.retailer:
            self.retailer = retailer
            self.retailer_source = source
        elif self.retailer_source == 'URL' and source == 'Integration':
            self.retailer = retailer
            self.retailer_source = source
        else:
            # We can't set the retailer
            # fail silently.
            None

    @classmethod
    def create_or_get_consignment(cls, courier_obj, tracking_number):
        logger.debug(u"In create_or_get_consignment. Passed Tracking number - {0}. Passed courier slug - {1}".format(tracking_number, courier_obj.courier_slug))

        if not courier_obj:
            raise CourierNotFoundException(u'No courier for courier slug {0}'.format(courier_obj.courier_slug))

        consignments = cls.get_consignments(courier_obj.courier_slug, tracking_number)
        if len(consignments) > 1:
            logger.warn(u'More than one consignment with same courier: {0} and tracking number {1}'
                        .format(courier_obj.courier_slug, tracking_number))
        cons = None
        if consignments:
            cons = consignments[0]

        logger.debug(u"Consignment Object {0}".format(cons))

        if not cons:
            logging.info(
                u'Adding consignment for courier {0}, tracking number {1}'.format(
                    courier_obj.courier_slug, tracking_number))
            cons = Consignment(tracking_number=tracking_number, courier=courier_obj)
            #cons.articles = [Article(tracking_number, courier_obj, True)]

            db.session.add(cons)
        logger.debug(
            u"Create or get consignment {0} ".format(cons.id))
        return cons

    # This is a really bad way to get user descriptions
    # however needed for api
    def get_description(self, user):
        l1 = user.user_consignments
        l2 = self.user_consignments
        for uc in l1:
            for uc2 in l2:
                if uc.id == uc2.id:
                    return uc.user_description
        return None

    @classmethod
    def get_consignments_for_user(cls, user, courier_slug, tracking_number):
        return db.session.query(Consignment).join(Courier).join(UserConsignment).join(User). \
            filter(and_(Consignment.tracking_number == tracking_number,
                   Courier.courier_slug == courier_slug, User.id == user.id)).all()

    @classmethod
    def get_consignments(cls, courier_slug, tracking_number):

        logging.info(
            u'In getting consignments {0}, tracking number {1}'.format(
                courier_slug, tracking_number))
        consignment_qry = db.session.query(Consignment).join(Courier). \
            filter(Consignment.tracking_number == tracking_number).filter(
            Courier.courier_slug == courier_slug).all()
        logger.debug('Consignment query: {0}'.format(consignment_qry))
        return consignment_qry

    @classmethod
    def retrieve_consignments(cls, tracking_external_id):
        consignments = Consignment.query.filter(Consignment.tracking_external_id == tracking_external_id)
        return consignments

    @classmethod
    def update_trackings(cls, aftership_tracking_info):
        # this method is used to update aftership tracking information
        # however it is suitable for use in other situations
        #
        # it is assumed that the aftership_tracking_info passed in is the complete JSON
        # IF (as I assumed for a short period of time) the checkpoints passed in are only a partial list of checkpoints
        # this method will need to be changed
        #
        # sanarios catered for
        # old == None, new != None   (adding tracking info for the first time)
        # old.updated_at < new.updated_at  (normal case)
        # old.updated_at >= new.updated_at (error case, skip )
        # new == None (error case, skip)
        #
        # 2 consignments may share the same tracking_id
        # - this won't happen in production as consignments are unique, but it occurs in dev
        #

        if aftership_tracking_info == None:
            raise Exception(u'aftership_tracking_info is None')

        consignments = cls.get_consignments(aftership_tracking_info['slug'], aftership_tracking_info['tracking_number'])
        for cons in consignments:
            logger.info('Updating tracking for consignment {0}, tracking_number {1}, {2}'.format(
                str(cons.id), cons.tracking_number, aftership_tracking_info))
            cons.update_tracking(aftership_tracking_info)
            for a in cons.articles:
                a.tracking_info = aftership_tracking_info

        db.session.commit()

    def new_checkpoints(self, checkpoints):

        checkpoints.sort(key=lambda c: c['checkpoint_time'], reverse=True)
        checkpoint_status = checkpoints[0][u'message']

        cons = Consignment.query.filter(Consignment.id == self.id).one()

        for uc in cons.user_consignments:
            if uc.user.consumer_user:
                logger.info(u'Sending new push for item {0} tracking event email {1}, checkpoint status: {2}'.format(
                    uc.user_description, uc.user.consumer_user.email_address, checkpoint_status))
                PushNotification.send_new_tracking_notification(uc.user.consumer_user.email_address, cons.id,
                                                                uc.user_description, checkpoint_status)

    def update_tracking(self, aftership_tracking_info):
        if not aftership_tracking_info:
            raise Exception(u'aftership_tracking_info is None')

        if self.tracking_info is None:
            logger.debug('Setting aftership tracking info first time consignment {0}'.format(str(self.id)))
            self.tracking_info = aftership_tracking_info
            self.set_latest_status(aftership_tracking_info)
            self.set_is_delivered(aftership_tracking_info)
            return

        if self.tracking_info['updated_at'] >= aftership_tracking_info['updated_at']:
            return

        # the aftership_tracking_info is newer then the stored version
        assert len(self.tracking_info['checkpoints']) <= len(aftership_tracking_info['checkpoints'])

        new_checkpoints = []
        if len(self.tracking_info['checkpoints']) < len(aftership_tracking_info['checkpoints']):
            # there are new checkpoints, so we will need to fire an event
            # - but only after we have updated the object ... otherwise weird things could happen
            if len(self.tracking_info['checkpoints']) > 0:
                max_old_checkpoint = \
                    sorted(self.tracking_info['checkpoints'], key=lambda c: c['checkpoint_time'], reverse=True)[0]
                new_checkpoints = [c for c in aftership_tracking_info['checkpoints'] if
                                   c['checkpoint_time'] > max_old_checkpoint['checkpoint_time']]
                new_checkpoints.sort(key=lambda c: c['checkpoint_time'])
            else:
                # edge case when the first new tracking has been added
                new_checkpoints = sorted(aftership_tracking_info['checkpoints'], key=lambda c: c['checkpoint_time'])

        # there may have been checkpoints that are removed from the checkpoints that
        # we ignore this possibility
        logger.info(u'Setting tracking info for consignment {0}, info {1}'.format(str(self.id), aftership_tracking_info))
        self.tracking_info = aftership_tracking_info
        self.set_latest_status(aftership_tracking_info)
        self.set_is_delivered(aftership_tracking_info)


        if new_checkpoints:
            # we do not make a decision about what to do if we have several new checkpoints
            # no do we care what happens with new checkpoints (push notification, email, other)
            # we are only firing an event
            logger.info(u'New checkpoints found, tracking number: {0}, count: {1}'.format(
                aftership_tracking_info[u'tracking_number'], len(new_checkpoints)))
            self.new_checkpoints(new_checkpoints)

    def set_latest_status(self, tracking_info):
        message = 'Currently being retrieved'
        tracking_items = TrackingInfo.items_from_tracking_dict(tracking_info)
        if len(tracking_items) > 0:
            sorted_items = sorted(tracking_items, reverse=True)
            latest = sorted_items[0]
            message = latest.message
            if message is None:
                message = latest.tag
        self.latest_status_col = message

    def set_is_delivered(self, tracking_info):
        is_delivered = False
        tracking_items = TrackingInfo.items_from_tracking_dict(tracking_info)
        for t in tracking_items:
            if t.tag == u'Delivered':
                is_delivered = True
                break

        self.is_delivered_col = is_delivered

    def latest_status(self):
        latest_status = self.latest_status_col
        if not latest_status:
            latest_status = 'Currently being retrieved'
        return latest_status

    def is_delivered(self):

        is_delivered = False
        if self.is_delivered_col:
            is_delivered = self.is_delivered_col
        return is_delivered

    @classmethod
    def delete_by_id(self, consignment_id):
        try:
            if consignment_id:
                cons = Consignment.query.get(consignment_id)
                db.session.delete(cons)
                db.session.commit()

        except Exception, e:
            logger.exception(e.message)
            raise e


class DeliveryCard(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'delivery_card'
    card_number = db.Column(db.String(255), nullable=False, index=True)
    delivery_id = db.Column(GUID(), nullable=False, index=True)

    def __init__(self, card_number, delivery_id):
        self.card_number = card_number
        self.delivery_id = delivery_id


# parsed the tracking_info that we receive from aftership
@event.listens_for(Consignment.tracking_info, 'set', retval=True)
def set_tracking_info_date(target, value, oldvalue, initiator):
    if value == None:
        return value

    tracking = value
    if 'tracking' in value:
        target.tracking_info = value['tracking']
        tracking = value['tracking']

    target.tracking_info_created_at = tracking['created_at']
    target.tracking_external_id = tracking['id']
    for checkpoint in tracking['checkpoints']:
        if checkpoint['tag'] in ['Delivered', 'Expired', 'Exception']:
            target.is_closed = True

    return tracking


class TrackingInfo:
    def __init__(self, slug, courier_name, tracking_number, tag, message, checkpoint_time, location, created_at,
                 is_delivered):
        self.slug = slug
        self.courier_name = courier_name
        self.tracking_number = tracking_number
        self.tag = tag
        self.message = message
        self.location = location
        self.checkpoint_time = checkpoint_time
        self.created_at = created_at
        self.is_delivered = is_delivered

    def __cmp__(self, other):
        if self.tag == u'Delivered' and other.tag != u'Delivered':
            return 1
        elif self.tag != u'Delivered' and other.tag == u'Delivered':
            return -1
        elif self.checkpoint_time < other.checkpoint_time:
            return -1
        elif self.checkpoint_time > other.checkpoint_time:
            return 1
        else:
            return 0

    def to_json(self):
        return {u'slug': self.slug, u'courier_name': self.courier_name, u'tracking_number': self.tracking_number,
                u'tag': self.tag, u'message': self.message, u'checkpoint_time': self.checkpoint_time,
                u'location': self.location, u'created_at': self.created_at,
                u'isDelivered': self.is_delivered}

    @classmethod
    def items_from_tracking_dict(cls, tracking_info):
        if tracking_info == None:
            return []

        checkpoints = tracking_info.get(u'checkpoints')
        tracking_number = tracking_info.get(u'tracking_number')
        trackings = []
        for c in checkpoints:
            trackings.append(
                TrackingInfo(c.get(u'slug'), c.get(u'courier_name'), tracking_number, c.get(u'tag'),
                             c.get(u'message'), c.get(u'checkpoint_time'), c.get(u'location', u''),
                             c.get('created_at'), c.get(u'tag') == 'Delivered'))
        return trackings


def compare_delivery_item(item1, item2):
    if item1['courierName'] == 'TrustMile' and item2['courierName'] == 'TrustMile':
        if item1['updated_at'] > item2['updated_at']:
            return 1
        elif item1['updated_at'] == item2['updated_at']:
            return 0
        else:
            return -1
    elif item1['courierName'] == 'TrustMile' and item2['courierName'] != 'TrustMile':
        return 1
    elif item1['courierName'] != 'TrustMile' and item2['courierName'] == 'TrustMile':
        return -1
    elif item1['courierName'] != 'TrustMile' and item2['courierName'] != 'TrustMile':
        if item1['updated_at'] > item2['updated_at']:
            return 1
        elif item1['updated_at'] == item2['updated_at']:
            return 0
        else:
            return -1


class Deliveries:
    # TODO: If we can't find the delivery, do we create a new one
    # and if so, do we create a new Article, or Consignment
    # This method shall return { tracking_number : tracking_info }
    @classmethod
    def user_adds_delivery(cls, user, courier_slug, tracking_number, description, retailer_pf=None):
        courier_obj = Courier.retrieve_courier(courier_slug)
        consignment = Consignment.create_or_get_consignment(courier_obj, tracking_number)
        user.add_consignment(consignment, description, retailer_pf)

        if courier_obj.tracking_info_supported:
            logger.debug(
                u'Updating shipping info on consignment {0} for tracking {1}'.format(consignment.id, tracking_number))
            r_result = tasks.update_shipping_info_for_consignment.apply_async(args=(consignment.id,), countdown=3)
        return consignment

    @classmethod
    def get_delivery_info_dict(cls, consignment, user, user_description, retailer_name = None, feedback_map=None,
                               retailer_info_map=None, tracking_info_list=None):

        cons = cls.trackings_for_consignment(consignment.id)
        dd = cls.get_base_info_dict(consignment, retailer_name, feedback_map=feedback_map, retailer_info_map=retailer_info_map,
                                    tracking_info_list=cons, user=user)

        if feedback_map is not None:
            dd['feedbackLeft'] = feedback_map.get(consignment.id, False)
        else:
            dd['feedbackLeft'] = consignment.feedback_left(user.id)

        if user_description:
            dd['description'] = user_description

        if not cons:
            dd['deliveryIsValid'] = False
        else:
            dd['deliveryIsValid'] = True

        return dd

    @classmethod
    def get_base_info_dict(cls, consignment, retailerNAME=None,user=None, feedback_map=None,
                           retailer_info_map=None, tracking_info_list=None):

        courier = consignment.courier
        feedback_left = False
        if feedback_map is not None:
            feedback_left = feedback_map.get(consignment.id, False)
        else:
            feedback_left = False

        if retailer_info_map is not None:
            retailer_image_url = retailer_info_map.get(consignment.id, {}).get('retailer_image_url', None) or ''
            retailer_name = retailer_info_map.get(consignment.id, {}).get('retailer_name', None) or ''
            order_id = retailer_info_map.get(consignment.id, {}).get('order_id', None) or ''
        else:
            retailer_image_url = consignment.get_retailer_image_url() or ''
            retailer_name = consignment.get_retailer_name() or ''
            order_id = consignment.get_order_id() or ''
        promotion_source_url = ''
        promotion_dest_url = ''
        promotion_view_id = ''
        promotion_retailer_name = ''

        if retailerNAME is not None:
            retailer_name = retailerNAME

        if tracking_info_list is not None and user:
            promotions = Promotion.query.all()

            if len(promotions) > 0:
                selected_promo = random.choice(promotions)
                # Only make the banners available for those delivaries
                # with the same retailer as in promotion and delivery.
                if selected_promo.retailer is not None:
                    if consignment.retailer is not None:
                        if (selected_promo.retailer.id == consignment.retailer.id):
                            promotion_source_url = selected_promo.promotion_view_url
                            promotion_dest_url = selected_promo.promotion_destination_url
                            promotion_retailer_name = selected_promo.retailer.website_name
                            pv = PromotionView(selected_promo, user, str(consignment.id))
                            db.session.add(pv)
                            db.session.commit()
                            promotion_view_id = str(pv.id)

        latest_status = consignment.latest_status()
        dd = {'courierName': courier.courier_name,
              'courierPhone': courier.phone, 'courierWeb': courier.web_url,
              'imageUrl': config.COURIER_IMAGE_URL_BASE + courier.courier_slug + '.png',
              'courierTrackingUrl': courier.tracking_url,
              'trackingInfoSupported': courier.tracking_info_supported,
              'isNeighbour': False,
              'trackingNumber': consignment.tracking_number,
              'description': consignment.tracking_number,
              'latestStatus': latest_status,
              'displayStatus': latest_status,
              'deliveryId': str(consignment.id),
              'feedbackLeft': feedback_left,
              'isDelivered': consignment.is_delivered(),
              'orderId': order_id,
              'retailerName': retailer_name,
              'retailerImageUrl': retailer_image_url,
              'updated_at': consignment.updated_at,
              'promotionSourceUrl': promotion_source_url,
              'promotionDestUrl': promotion_dest_url,
              'promotionViewId': promotion_view_id,
              'promotionRetailerName': promotion_retailer_name
              }

        if tracking_info_list and len(tracking_info_list) == 0:
            dd['trackingInfoSupported'] = False
            dd['isDelivered'] = False
            dd['feedbackLeft'] = False
            dd['latestStatus'] = dd['displayStatus'] = 'Tracking information available on courier website'

        if tracking_info_list:
            dd['trackingEvents'] = [t.to_json() for t in tracking_info_list]

        return dd

    @classmethod
    def get_trustmile_info_dict(cls, tmd, user, delivery_card_map=None, feedback_map=None):

        if delivery_card_map:
            card_number = delivery_card_map.get(tmd.id, '')
        else:
            card_number = ''

        if feedback_map:
            feedback_left = feedback_map.get(tmd.id, False)
        else:
            feedback_left = False

        dd = {
            'courierName': 'TrustMile',
            'trackingNumber': str(tmd.id),
            'courierPhone': '',
            'courierWeb': 'https://www.trustmile.com',
            'description': 'Packages for a neighbour',
            'displayStatus': tmd.get_display_state(is_neighbour=tmd.neighbour.user.id == user.id),
            'isNeighbour': tmd.neighbour.user.id == user.id,
            'latestStatus': tmd.state,
            'cardNumber': card_number,
            'neighbour': tmd.neighbour.as_consumer() if tmd.neighbour else {},
            'recipient': tmd.recipient_info,
            'articles': [a.to_json() for a in tmd.articles],
            'feedbackLeft': feedback_left,
            'isDelivered': tmd.is_delivered(),
            'orderId': '',
            'retailerImageUrl': '',
            'retailerName': '',
            'deliveryId': str(tmd.id),
            'updated_at': tmd.updated_at
        }
        return dd


    @classmethod
    def get_deliveries_info_for_user(cls, user):
        try:

            consignments_query = Consignment.query.join(
                UserConsignment).join(User).filter(User.id == user.id)

            logger.debug('Consignment query: {0}'.format(consignments_query))
            consignments = consignments_query.all()
            cons_ids = [c.id for c in consignments]
            retailer_info_map = cls.get_retailer_info_map(consignments, user)
            user_consignments_map = cls.get_user_consignments_map(cons_ids, user)
            for c in consignments:
                c.user_description = user_consignments_map.get(c.id).user_description
                c.retailer_name = user_consignments_map.get(c.id).retailer_name

            delivery_feedback_map = cls.get_delivery_feedback_map(consignments, user)

            logger.debug(u'Updating shipping info for consignments {0}'.format(', '.join([str(id) for id in cons_ids])))
            tasks.update_shipping_info_for_consignments.delay(cons_ids)

            # for c in consignments:
            #     logger.debug(u"Updating shipping info for consignment id {0}".format(str(c.id)))
            #     tasks.update_shipping_info_for_consignment.delay(c.id)


            results = {'deliveries': [cls.get_delivery_info_dict(
                c, user, c.user_description, c.retailer_name, feedback_map=delivery_feedback_map, retailer_info_map=retailer_info_map) for c in consignments]}

            logger.debug(u"Return results: {0}".format(results))
            # This is tricky - The question is - how do we manage a package through out system
            # and how do we model the data to track it?
            if(user.anonymous_user):
                tm_deliveries_q = TrustmileDelivery.query.options(joinedload(TrustmileDelivery.articles)).filter(
                    or_(TrustmileDelivery.neighbour == user.anonymous_user,
                        TrustmileDelivery.recipient == user.anonymous_user)).filter(
                    TrustmileDelivery.state.in_([DeliveryState.TRANSIT_TO_NEIGHBOUR.value,
                                                 DeliveryState.NEIGHBOUR_RECEIVED.value,
                                                 DeliveryState.RECIPIENT_RECEIVED.value]))
            else:
                tm_deliveries_q = TrustmileDelivery.query.options(joinedload(TrustmileDelivery.articles)).filter(
                or_(TrustmileDelivery.neighbour == user.consumer_user,
                    TrustmileDelivery.recipient == user.consumer_user)).filter(
                TrustmileDelivery.state.in_([DeliveryState.TRANSIT_TO_NEIGHBOUR.value,
                                             DeliveryState.NEIGHBOUR_RECEIVED.value,
                                             DeliveryState.RECIPIENT_RECEIVED.value]))

            logger.debug('TrustMile deliveries query {0}'.format(tm_deliveries_q))
            tm_deliveries = tm_deliveries_q.all()

            delivery_feedback_map = cls.get_delivery_feedback_map(tm_deliveries, user)
            card_number_map = cls.get_delivery_card_map(tm_deliveries)

            pres_tm_results = [cls.get_trustmile_info_dict(
                tm, user, feedback_map=delivery_feedback_map,
                delivery_card_map=card_number_map) for tm in tm_deliveries]

            logger.debug(u"Found {0} trustmile deliveries".format(len(pres_tm_results)))
            results['deliveries'].extend(pres_tm_results)

            # reverse = True means descending
            results['deliveries'] = sorted(results['deliveries'], compare_delivery_item, reverse=True)

        except Exception, e:
            logger.exception(u"Exception on getting consignments")
        else:
            return results

    @classmethod
    def get_deliveries_for_days(cls, numdays, retailer):
        try:

            current_time = datetime.datetime.utcnow()
            archive_time = current_time - datetime.timedelta(days=numdays)
            consignments_query = Consignment.query.join(RetailerIntegrationConsignment).filter(Consignment.created_at > archive_time).filter(RetailerIntegrationConsignment.retailer_id == retailer.id).order_by(desc(Consignment.created_at))
            consignments_data = consignments_query.all()

            dictelem = {}
            for cday in consignments_data:
                deliverydate = datetime.datetime.strftime(cday.created_at, '%Y/%m/%d')
                dictelem.setdefault(deliverydate, []).append(cday.is_delivered_col)

            dictfinal = {}
            for deldate, dstatus in (sorted(dictelem.iteritems(), key=lambda kv: kv[0], reverse=True)):
                dictcons = {};
                dictcons['delivered'] = 0; dictcons['not_delivered'] = 0
                dictcons['deliverydate'] = deldate

                for stat in dstatus:
                    if stat == True:
                        dictcons['delivered'] = dictcons.get('delivered', 0) + 1
                    else:
                        dictcons['not_delivered'] = dictcons.get('not_delivered', 0) + 1
                dictfinal.setdefault('deliverydays', []).append(dictcons)

            results = dictfinal

        except Exception, e:
                logger.exception(u"Exception on getting consignments")
        else:
            return results

    @classmethod
    def get_deliveries_for_couriers(cls, numdays, retailer):
        try:

            current_time = datetime.datetime.utcnow()
            archive_time = current_time - datetime.timedelta(days=numdays)
            consignments_query = Consignment.query.with_entities(Consignment.courier_id, Courier.courier_name.label('courier_company'),func.sum(case([(Consignment.is_delivered_col == 't', 1),], else_=0)).label('delivered'), func.sum(case([(Consignment.is_delivered_col == 'f', 1),], else_=0)).label('not_delivered'), Courier.courier_slug.label('logo')).join(RetailerIntegrationConsignment).join(Courier).filter(Consignment.created_at > archive_time).filter(RetailerIntegrationConsignment.retailer_id == retailer.id).group_by(Consignment.courier_id, Courier.courier_name, Courier.courier_slug)

            consignments_data = consignments_query.all()

            logo_url = "http://assets.trustmile.com/images/courier/"
            dictfinal = {}
            for cdata in consignments_data:
                dictcons = {};
                dictcons['courier_company'] = cdata.courier_company
                dictcons['delivered'] = cdata.delivered
                dictcons['not_delivered'] = cdata.not_delivered
                dictcons['logo'] = logo_url + cdata.logo + ".png"
                dictfinal.setdefault('retailer', []).append(dictcons)

            results = dictfinal



        except Exception, e:
                logger.exception(u"Exception on getting consignments")
        else:
            return results

    @classmethod
    def add_anon_deliveries(cls, user, anonlist):
        try:

            consignments_query = Consignment.query.join(
                UserConsignment).join(User).filter(User.id == user.id)

            logger.debug('Consignment query: {0}'.format(consignments_query))
            consignments = consignments_query.all()

            cons_ids = [c.id for c in consignments]
            retailer_info_map = cls.get_retailer_info_map(consignments, user)
            user_consignments_map = cls.get_user_consignments_map(cons_ids, user)
            for c in consignments:
                c.user_description = user_consignments_map.get(c.id).user_description
                c.retailer_name = user_consignments_map.get(c.id).retailer_name

            anon_query = Consignment.query.join(
                UserConsignment).join(User).filter(User.id == anonlist[0].user.id)
            anon_consignments = anon_query.all()

            cons_anon_ids = [a.id for a in anon_consignments]
            anon_retailer_info_map = cls.get_retailer_info_map(anon_consignments, anonlist[0].user)
            anon_user_consignments_map = cls.get_user_consignments_map(cons_anon_ids, anonlist[0].user)
            for a in anon_consignments:
                a.user_description = anon_user_consignments_map.get(a.id).user_description
                a.retailer_name = anon_user_consignments_map.get(a.id).retailer_name


            if anon_consignments and consignments:

                for a_cons in anon_consignments:
                    consexist = False

                    for c_cons in consignments:
                        if a_cons.id == c_cons.id:
                            consexist = True

                    if consexist == False:
                        user.add_consignment(a_cons, a.user_description, a.retailer_name)
            elif not consignments:
                if anon_consignments:
                    for a_cons in anon_consignments:
                        user.add_consignment(a_cons, a.user_description, a.retailer_name)

        except Exception, e:
            logger.exception(u"Exception on getting consignments")

    @classmethod
    def get_retailer_info_map(cls, consignments, user):

        ris = RetailerIntegrationConsignment.query.join(Consignment).filter(
            Consignment.id.in_([c.id for c in consignments])).all()

        ris_map = dict([(r.consignment.id, r.order_id) for r in ris])

        return dict([(c.id, {'retailer_image_url': config.RETAILER_IMAGE_URL_BASE + c.retailer.slug + '.png',
                             'retailer_name': c.retailer.website_name,
                             'order_id': ris_map.get(c.id) or ''}) for c in consignments if c.retailer])

    @classmethod
    def get_user_consignments_map(cls, consignment_ids, user):
        ucs = UserConsignment.query.join(Consignment).join(User).filter(
            Consignment.id.in_(consignment_ids), User.id == user.id).all()

        map = dict([(u.consignment.id, u) for u in ucs])
        return map

    @classmethod
    def get_delivery_feedback_map(cls, delivery_items, user):
        delivery_feedback_map = {}
        if delivery_items:

            feedbacks = DeliveryFeedback.query.join(ConsumerUser).join(User).filter(and_(
                DeliveryFeedback.delivery_id.in_([d.id for d in delivery_items]), User.id == user.id)).all()

            delivery_feedback_map = dict([(f.delivery_id, True) for f in feedbacks])

        return delivery_feedback_map

    @classmethod
    def get_delivery_card_map(cls, delivery_items):
        delivery_card_map = {}
        if delivery_items:
            cards = DeliveryCard.query.filter(DeliveryCard.delivery_id.in_([d.id for d in delivery_items])).all()
            delivery_card_map = dict([(c.delivery_id, c.card_number) for c in cards])
        return delivery_card_map


    @classmethod
    def get_for_id(cls, delivery_id):
        try:
            consignment_query = db.session.query(Consignment.id).filter(Consignment.id == delivery_id)
            tmd_query = db.session.query(TrustmileDelivery.id).filter(TrustmileDelivery.id == delivery_id)
            entity_ids = consignment_query.union(tmd_query).all()
            assert len(entity_ids) == 1

        except exc.NoResultFound, nrfe:
            logger.exception(u"No results found " + nrfe.message)
            raise nrfe
        except Exception, e:
            logger.exception(u"Unexpected exception")
            raise e
        else:
            return entity_ids[0][0]

    @classmethod
    def get_consignment_for_user(cls, user, delivery_id):
        try:
            consignment = Consignment.query.join(UserConsignment).join(User).filter(and_(User.id == user.id, Consignment.id == delivery_id)).one()

        except exc.NoResultFound, nrfe:
            logger.exception(u'No results found {0}'.format(nrfe.message))
            raise nrfe
        else:
            return consignment

    @classmethod
    def trackings_for_consignment(cls, consignment_id):
        try:
            consignment = Consignment.query.get(consignment_id)
            app_tracking_info = sorted(TrackingInfo.items_from_tracking_dict(consignment.tracking_info), reverse=True)

            return app_tracking_info

        except exc.NoResultFound, nrf:
            logger.exception(u"No results found " + nrf.message)
            return None

    @classmethod
    def find_deliveries(cls, tracking_numbers):
        try:
            cons_q = db.session.query(Consignment.id).filter(Consignment.tracking_number.in_(tracking_numbers))
            art_q = db.session.query(Article.id).filter(Article.tracking_number.in_(tracking_numbers))

            entity_uuids = cons_q.union(art_q).all()

            # just give me the tuple, not the array with tuple
            if len(entity_uuids) > 0:
                entity_uuids = entity_uuids[0]

            logger.debug(u"Article entities found {0}".format(entity_uuids))
        except exc.NoResultFound:
            logger.error(u"No item found for identifier {0}".format(tracking_numbers))
            raise DeliveryNotFoundException(u'Delivery not found for tracking number {0}'.format(tracking_numbers))
        return entity_uuids

    @classmethod
    def tracking_for_delivery(cls, courier, tracking_number):
        try:
            rs = Article.query.filter(and_(Article.tracking_number == tracking_number, Article.courier == courier)).all()
        except exc.NoResultFound, nrfe:
            logger.exception(u"No results found for tracking id {0}".format(tracking_number))
            raise DeliveryNotFoundException(u'Delivery not found for tracking number {0}'.format(tracking_number))

        return [r.tracking_info for r in rs]


class DeliveryFeedback(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'delivery_feedback'
    delivery_id = db.Column(GUID, nullable=False, index=True)
    stars = db.Column(db.SmallInteger, nullable=False)
    message = db.Column(db.Text)
    complaints = one_to_many('DeliveryComplaint', backref='feedback_parent', lazy='select')
    user = many_to_one('ConsumerUser', backref='delivery_feedback', lazy='select', cascade="all")

    def __init__(self, delivery_id, stars, message, user, complaints=[]):
        self.delivery_id = delivery_id
        self.stars = stars
        self.message = message
        self.complaints = complaints
        self.user = user

    def get_delivery_item(self):
        cons = db.session.query(Consignment).filter(Consignment.id == self.delivery_id).first()
        art = db.session.query(Article).filter(Article.id == self.delivery_id).first()
        tm_delivery = db.session.query(TrustmileDelivery).filter(TrustmileDelivery.id == self.delivery_id).first()

        return cons or art or tm_delivery


class DeliveryComplaint(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'delivery_complaint'
    complaint = db.Column(db.String(255), nullable=False)

    def __init__(self, complaint):
        self.complaint = complaint


class NetPromoterScore(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'net_promoter_score'
    score = db.Column(db.SmallInteger, nullable=False)
    consumer_user = many_to_one('ConsumerUser', backref='net_promoter_scores', lazy='select')
    delivery_id = db.Column(GUID, nullable=False, index=True)
    comment = db.Column(db.Text, nullable=True)


    def __init__(self, score_value, consumer_user, delivery_id, comment = None):
        self.score = score_value
        self.consumer_user = consumer_user
        self.delivery_id = delivery_id
        self.comment = comment


# TODO: Article could get injected into the system when a courier types it into his app
class Article(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'article'
    tracking_number = db.Column(db.String(255), nullable=True)
    """ The reason for using relationship and courier_id here is because adding the unique constraint
        can't find courier_id with the normal many_to_one declaration """
    courier_id = db.Column(GUID(), ForeignKey('courier.id'), nullable=False)
    courier = relationship('Courier', backref='articles', lazy = 'select')

    tracking_info = db.Column(JSON, default=None)
    recipient = many_to_one('ConsumerUser', backref='articles', lazy='select')
    user_entered = db.Column(db.Boolean, default=False)
    users_description = db.Column(db.String(255), nullable=True)
    tracking_info = db.Column(JSON, default=None)
    # __table_args__ = (UniqueConstraint('courier_id', 'tracking_number', name='courier_tracking_art_unique_constr'),)

    def __init__(self, tracking_number, courier, user_entered=False):
        self.tracking_number = tracking_number
        self.user_entered = user_entered
        self.courier = courier

    @classmethod
    def find_by_tracking_id(cls, tid):
        article = None
        try:
            article = cls.query.filter_by(tracking_number=tid).one()
        except exc.NoResultFound, nrfe:
            logger.exception(nrfe)
            logger.debug(u"article not found for id {0}".format(tid))

        return article

    ''' This is when we can't find the article so we just create one '''

    @classmethod
    def new_articles(cls, courier_user, tracking_numbers):
        new_articles = []

        for t in tracking_numbers:
            article = Article(t, courier=courier_user.courier, user_entered= True)
            new_articles.append(article)
        return new_articles

    @classmethod
    def get_for_tracking_numbers(cls, tracking_numbers):
        try:
            art_q = db.session.query(Article).filter(Article.tracking_number.in_(tracking_numbers))

            articles = art_q.all()

            # just give me the tuple, not the array with tuple

            logger.debug(u"Found articles {0}".format([str(a.id) for a in articles]))

        except exc.NoResultFound:
            logger.error(u"No item found for tracking numbers {0}".format(tracking_numbers))
            raise DeliveryNotFoundException(u'Delivery not found for tracking number {0}'.format(tracking_numbers))

        return articles

    def to_json(self):
        return {'articleId': str(self.id), 'trackingNumber': self.tracking_number}


class TrustmileDelivery(db.Model, UniqueMixin, DeliveryFeedbackMixin, TableColumnsBase):
    __tablename__ = 'trustmile_delivery'
    articles = one_to_many('Article', backref='delivery', lazy='select')
    # neighbour = many_to_one('ConsumerUser', backref='trustmile_deliveries_in_care', lazy='select')

    neighbour_id = db.Column(GUID(), ForeignKey('consumer_user.id'))
    neighbour = relationship('ConsumerUser', backref='trustmile_deliveries_in_care', lazy='select', foreign_keys=[neighbour_id])

    recipient_id = db.Column(GUID(), ForeignKey('consumer_user.id'))
    recipient = relationship('ConsumerUser', backref='trustmile_deliveries_in_field', lazy='select', foreign_keys=[recipient_id])

    state = db.Column(db.String(255), default=DeliveryState.CREATE.value)
    location = db.Column(Geography(geometry_type='POINT', srid=4326))
    recipient_info = db.Column(JSON, default={})
    secret_word = db.Column(db.String(32), default=None)

    enum_to_display_map = {
        'NEWLY_CREATED': 'New',
        'TRANSIT_TO_NEIGHBOUR': "In transit to neighbour",
        'ABORTING':  'Aborting',
        'NEIGHBOUR_ABORTED': "Neighbour Aborted",
        'COURIER_ABORTED': "Courier aborted",
        'CANCELLED': 'Cancelled'
    }

    def __init__(self, articles):
        if len(articles):
            self.articles.extend(articles)
        self.secret_word = random.choice(config.SECRET_WORDS)

    def set_neighbour(self, neighbour):
        self.neighbour = neighbour

    def update_info(self, recipient_name=None, recipient_phone=None, email_address=None, source=None):
        if self.recipient_info is None:
            v = {'recipientName': recipient_name, 'phoneNumber': recipient_phone,
                 'recipientEmail': email_address, 'source': source}
            self.recipient_info = v
        else:
            recipient_info = copy.copy(self.recipient_info)
            if recipient_name:
                recipient_info['recipientName'] = recipient_name
            if recipient_phone:
                recipient_info['phoneNumber'] = recipient_phone
            if email_address:
                recipient_info['recipientEmail'] = email_address
            if source:
                recipient_info['source'] = source

            self.recipient_info = recipient_info

    def get_recipient_name(self):
        res = None
        if self.recipient_info:
            res = self.recipient_info.get('recipientName', None)
        return res


    @classmethod
    def create(cls, courier_user, articles):
        tmd = TrustmileDelivery(articles)
        tmd.courier = courier_user
        logger.debug(u'TM DELIVERY created for user:{} '.format(tmd.courier.id))
        return tmd

    @property
    def user_description(self):
        # Unknwon at this stage
        return u"Delivery for {0} at {1}".format('Unknown', self.neighbour.fullName)

    @property
    def latest_status(self):
        return self.state

    @classmethod
    def by_tracking(cls, trk):
        article = Article.find_by_tracking_id(trk)
        tmd = article.delivery if article else None
        return tmd

    @classmethod
    def get_for_tracking_numbers(cls, tracking_numbers):
        articles = Article.get_for_tracking_numbers(tracking_numbers)
        tmds = []
        for a in articles:
            tmds.append(a.delivery)

        return tmds


    @classmethod
    def get_by_tracking_for_neighbour(cls, neighbour_user, tracking_number,
                                      state=DeliveryState.TRANSIT_TO_NEIGHBOUR.value):
        return TrustmileDelivery.query.filter_by(neighbour=neighbour_user).join(
            Article).filter(and_(Article.tracking_number == tracking_number, TrustmileDelivery.state == state)).first()


    @classmethod
    def retrieve_for_recipient_handover(cls, user, articles):
        article_ids = [a.id for a in articles]
        required_state = DeliveryState.NEIGHBOUR_RECEIVED.value
        q = TrustmileDelivery.query.filter_by(neighbour=user).join(Article).filter(
            and_(Article.id.in_(article_ids), TrustmileDelivery.state == required_state))

        tm_deliveries = q.all()
        if len(tm_deliveries) < 1:
            raise Exception(u"No deliveries found for user {0}".format(user.id))
        if len(tm_deliveries) != 1:
            raise Exception(u"Articles should belong to single Trustmile Delivery object {0}, articles {1}".format(
                [t.id for t in tm_deliveries], article_ids))

        return tm_deliveries[0]

    def is_delivered(self):
        return self.state == DeliveryState.RECIPIENT_RECEIVED.value

    def to_json(self):
        return {
            'deliveryId': str(self.id),
            'articles': [{'articleId': str(a.id), 'trackingNumber': str(a.tracking_number)} for a in self.articles],
            'state': self.state,
            'neighbour': self.neighbour.user.user_details_data() if self.neighbour else {},
            'recipient': self.recipient_info or {},
            'lastUpdated': self.updated_at
        }

    def get_card_number(self):
        delivery_id = self.id
        dc = DeliveryCard.query.filter(DeliveryCard.delivery_id == delivery_id).first()
        if dc:
            return dc.card_number
        else:
            return None

    def get_latest_status(self):
        return self.state

    def get_display_state(self, is_neighbour=True):
        display_string = None
        if self.state in self.__class__.enum_to_display_map:
            display_string = self.__class__.enum_to_display_map[self.state]
        elif self.state == DeliveryState.NEIGHBOUR_RECEIVED.value:
            if is_neighbour:
                display_string = u'For {0}'.format(self.recipient_info.get('recipientName') or 'Unknown recipient')
            else:
                display_string = u'Collect from {0}'.format(self.neighbour.user.user_address[0].addressLine1)
        elif self.state == DeliveryState.RECIPIENT_RECEIVED.value:
            if is_neighbour:
                display_string = u'Collected by {0}'.format(self.recipient_info.get('recipientName'))
            else:
                display_string = u'Collected from {0}'.format(self.neighbour.user.user_address[0].addressLine1)
        return display_string

class DeliveryDelegate(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'delivery_delegate'
    link = db.Column(db.String(512), nullable=False)
    delivery_id = db.Column(GUID(), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, delivery_id, link, email):
        self.delivery_id = delivery_id
        self.link = link
        self.email = email

class ConsignmentAddress(Address, UniqueMixin, TableColumnsBase):
    __tablename__ = 'consignment_address'
    __mapper_args__ = {'polymorphic_identity': 'consignmentaddress'}
    id = db.Column(GUID(), ForeignKey('address.id'), primary_key=True)


class Courier(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'courier'
    courier_name = db.Column(db.String(255), nullable=False)
    trustmile_courier = db.Column(db.Boolean)
    courier_slug = db.Column(db.String(64), nullable=False, unique=True)
    phone = db.Column(db.String(64), nullable=True)
    web_url = db.Column(db.String(255), nullable=True)
    tracking_info_supported = db.Column(db.Boolean)
    tracking_url = db.Column(db.String(255), nullable=True)

    courier_users = one_to_many('CourierUser', backref='courier', lazy='select', cascade="all, delete-orphan")

    def __init__(self, courier_name, courier_slug, phone, web_url,
                 trustmile_courier=True, tracking_url = None, tracking_info_supported = True):
        self.courier_name = courier_name
        self.courier_slug = courier_slug
        self.trustmile_courier = trustmile_courier
        self.web_url = web_url
        self.phone = phone
        self.tracking_url = tracking_url
        self.tracking_info_supported = tracking_info_supported

    @classmethod
    def retrieve_courier(cls, courier):
        try:
            q = Courier.query.filter(
                or_(Courier.courier_slug == courier, Courier.courier_name == courier))
            courier_obj = q.one()

        except Exception, e:
            logger.exception(u"Failed to find courier {0}".format(courier))
            raise e
        else:
            return courier_obj


def notify_couriers(tracking_numbers, scan_event, contractor_num):
    for tn in tracking_numbers:
        cpn = CouriersPleaseNotifications(tn, scan_event, contractor_num)
        db.session.add(cpn)


class TrackableEvent:

    def event_datetime(self):
        pass

    def message(self):
        pass

    def location_name(self):
        pass

    def location_coords(self):
        pass

    def tag(self):
        pass


class TrustmileDeliveryEvent(TrackableEvent):

    def __init__(self):
        pass


class ConsignmentTrackingEvent(TrackableEvent):

    def __init__(self):
        pass


class CouriersPleaseNotifications(db.Model):
    __tablename__ = 'couriers_please_notifications'
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(255), nullable=False)
    consignment_number = db.Column(db.String(255))
    scan_event = db.Column(db.String(255), nullable=False)
    contractor_num = db.Column(db.String(255), nullable=False)
    exception_reason = db.Column(db.String(255))


    def __init__(self, tracking_number, scan_event, contractor_num):
        self.tracking_number = tracking_number
        self.scan_event = scan_event
        self.contractor_num = contractor_num


class LatestCouriersPleaseMarker(db.Model):
    __tablename__ = 'latest_couriers_please_marker'
    id = db.Column(db.Integer, primary_key=True)
