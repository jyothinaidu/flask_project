import logging

from pypushwoosh.client import PushwooshClient
from pypushwoosh.command import CreateMessageForApplicationCommand
from pypushwoosh.notification import Notification

import config
from app.util import get_branch_link

logger = logging.getLogger()


class PushNotification:
    @classmethod
    def send_new_tracking_notification(cls, email_address, consignment_id, consignment_description, checkpoint_status):
        # constructs and sends a push notification for a new tracking even

        PushWoosh.send_tracking_notification(email_address, consignment_description, checkpoint_status, consignment_id)

    @classmethod
    def send_new_order_notificication(cls, email_address, order_id, retailer):
        PushWoosh.send_new_order(email_address, order_id, retailer)

    @classmethod
    def notify_neighbour(cls, neighbour, courier_user):
        PushWoosh.notify_neighbour(neighbour, courier_user)

    @classmethod
    def notify_account_updated(cls, email_address):
        message = u'Updated address for {0}'.format(email_address)
        notification = Notification()
        branch_link = get_branch_link({'account_changed': True})
        custom_data = {'branch': branch_link}
        code, status_message = PushWoosh.send_push_message(email_address, message, notification, custom_data=custom_data)
        logger.info(u'Sent push to {0}, branch link: {1}, status {2} for account changed'.format(
            email_address, branch_link, code))

    @classmethod
    def send_push(cls, email, data=None, message=""):
        success = False
        notification = Notification()
        custom_data = None
        branch_link = None
        if data:
            branch_link = get_branch_link(data)
            custom_data = {'branch': branch_link}
        status_code, status_message = PushWoosh.send_push_message(email, message, notification, custom_data=custom_data)
        if status_code == 200:
            logger.info(u'Sent push to {0}, branch link: {1}, status {2}'.format(
                email, branch_link, status_code))
            success = True
        else:
            logger.info(u'Failed push to {0}, branch link: {1}, status_code {2}, status_message {3}'.format(
                email, branch_link, status_code, status_message))
        return success

class PushWoosh:
    @classmethod
    def send_new_order(cls, email_address, order_id, retailer):
        try:
            message = u'New Delivery Added: Order {0} from {1}'.format(order_id, retailer)
            custom_data = {'order_id': str(order_id)}
            notification = Notification()
            response_code, response_message = cls.send_push_message(email_address, message, notification, custom_data=custom_data)
            logger.info(u'Sent push notification to {0} for order {1}. Result code {2}'.format(email_address, order_id,
                                                                                               response_code))
        except Exception as e:
            logger.info(u'Request error: ' + e.message)

    @classmethod
    def send_push_message(cls, email_address, message, notification, custom_data=None):
        if message:
            notification.content = message
        else:
            notification.ios_root_params = {'aps': {'content-available': '1'}}
            notification.ios_sound = 'silent_sound.m4a'
        notification.ignore_user_timezone = True
        notification.send_date = 'now'
        if custom_data:
            notification.data = custom_data
        notification.conditions = [['Email Address', 'EQ', email_address]]
        command = CreateMessageForApplicationCommand(notification, config.PUSHWOOSH_APPLICATION)
        command.auth = config.PUSHWOOSH_AUTH
        command.command_name = 'createMessage'
        client = PushwooshClient()
        response = client.invoke(command)
        response_code = response.get('status_code')
        status_message = response.get('status_message')
        return response_code, status_message

    @classmethod
    def send_tracking_notification(cls, email_address, consignment_description, checkpoint_status, consignment_id):

        try:
            message = u'"{0}" update: {1}'.format(consignment_description, checkpoint_status)
            branch_link = get_branch_link({"delivery_id": str(consignment_id)})
            custom_data = {'delivery_id': str(consignment_id), 'branch': branch_link}
            notification = Notification()

            logger.debug(u"Branch link {1} generated for delivery {0}".format(branch_link, consignment_id))
            response_code, response_message = cls.send_push_message(email_address, message, notification, custom_data=custom_data)

            logger.info(u'Sent push notification to {0} for consignment {1} with status {2}. Result code {3}'.format(
                email_address, consignment_id, checkpoint_status, response_code))
        except Exception as e:
            logger.exception(e)
            logger.info(u'Request error: ' + e.message)

    @classmethod
    def notify_neighbour(cls, neighbour, courier):
        try:
            message = u'Courier {0} is in transit with a parcel'.format(courier.fullName)
            notification = Notification()
            response_code, response_message = cls.send_push_message(neighbour.email_address, message, notification)
            logger.info(u'Send push notification to {0} about courier in transit with response code {1}'.format(
                neighbour.email_address, response_code))
        except Exception as e:
            logger.exception(e)
