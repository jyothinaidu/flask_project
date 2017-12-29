import time
import logging
import mandrill
from app import exc
import config

__author__ = 'james'

logger = logging.getLogger()


class EmailHandler(object):
    client = None

    @classmethod
    def setup(cls, api_key):
        cls.client = mandrill.Mandrill(apikey=api_key)

    @classmethod
    def send_password_reset(cls, email_address, full_name, reset_token):
        if not cls.client:
            cls.setup(config.EMAIL_API_KEY)
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

                'merge_language': 'handlebars',

            }
            send_result = cls.client.messages.send_template(template_name='trustmile-password-reset',
                                                            template_content=None, message=message)

            logger.info(u'Sent password reset email to {0} with send id: {0}, status: {1}'.format(
                email_address, send_result[0]['_id'], send_result[0]['status']))

        except mandrill.Error, e:
            # Mandrill errors are thrown as exceptions
            logger.exception(e)
            raise exc.EmailSendException(e)
        else:
            return send_result

    @classmethod
    def send_retailer_password_reset(cls, email_address, contact_name, reset_token):
        if not cls.client:
            cls.setup(config.EMAIL_API_KEY)
        try:

            message = {
                'to': [{'email': email_address,
                        'name': contact_name,
                        'type': 'to'}],

                'global_merge_vars': [{'content': contact_name, 'name': 'RECIPIENT_NAME'},
                                      {'name': 'ResetUrl',
                                       'content': config.RETAILER_PASSWORD_RESET_URL + u'{0}'.format(
                                           reset_token)},
                                      {'name': 'EMAIL_ADDRESS', 'content': email_address}
                                      ],

                'merge_language': 'handlebars',

            }
            send_result = cls.client.messages.send_template(template_name='reset-password-v2',
                                                            template_content=None, message=message)

            logger.info(u'Sent retailer password reset email to {0} with send id: {0}, status: {1}'.format(
                email_address, send_result[0]['_id'], send_result[0]['status']))

        except mandrill.Error, e:
            # Mandrill errors are thrown as exceptions
            logger.exception(e)
            raise exc.EmailSendException(e)
        else:
            return send_result

    @classmethod
    def send_left_with_neighbour_notification(cls, recipient_email, recipient_name, courier_name, neighbour_info):
        if cls.client is None:
            cls.setup(config.EMAIL_API_KEY)

        try:
            message = {
                'to': [{'email': recipient_email,
                        'name': recipient_name,
                        'type': 'to'}],

                'global_merge_vars': [{'content': recipient_name, 'name': 'RECIPIENT_NAME'},
                                      {'name': 'NEIGHBOUR_NAME',
                                       'content': neighbour_info['name']},
                                      {'name': 'NEIGHBOUR_PHONE', 'content': neighbour_info['phone']},
                                      {'name': 'NEIGHBOUR_ADDRESS_LINE_1', 'content': neighbour_info['address_line_1']},
                                      {'name': 'NEIGHBOUR_ADDRESS_LINE_2', 'content': neighbour_info['address_line_2']},
                                      {'name': 'NEIGHBOUR_SUBURB', 'content': neighbour_info['suburb']},
                                      {'name': 'NEIGHBOUR_POSTCODE', 'content': neighbour_info['postcode']},
                                      {'name': 'COURIER_NAME', 'content': courier_name},
                                      {'name': 'NEIGHBOUR_latitude', 'content': neighbour_info['latitude']},
                                      {'name': 'NEIGHBOUR_longitude', 'content': neighbour_info['longitude']}
                                    ],
                'merge_language': 'handlebars',
            }
            send_result = cls.client.messages.send_template(template_name='couriers-please-neighbour-delivered',
                                                        template_content=None, message=message)

            logger.info(u'Sent email with send id: {0}, status: {1}'.format(
                send_result[0]['_id'], send_result[0]['status']))
        except mandrill.Error, e:
            # Mandrill errors are thrown as exceptions
            logger.exception(e)
            raise exc.EmailSendException(e)
        else:
            return send_result


    @classmethod
    def send_verification(cls, email_address, to_name, verification_code):
        if cls.client is None:
            cls.setup(config.EMAIL_API_KEY)
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
            start_time = time.time()
            send_result = cls.client.messages.send_template(template_name='trustmile-email-verification',
                                                            template_content=None, message=message)
            #send_result = cls.client.messages.send(message=message, async=True, ip_pool='Main Pool',
            #                                       send_at='2016-08-10 12:00:00')
            call_time = time.time()
            logger.info(u'Sent email with send id: {0}, status: {1}'.format(
                send_result[0]['_id'], send_result[0]['status']))
            result_time = time.time()
            logger.info('Email send time {0}, result time {1}'.format(((call_time-start_time)*1000), ((result_time-call_time) * 1000)))
        except mandrill.Error, e:
            # Mandrill errors are thrown as exceptions
            logger.exception(e)
            raise exc.EmailSendException(e)
        else:
            return send_result

    @classmethod
    def send_feedback(cls, user_full_name, user_email_address, feedback_message, user_id):
        if cls.client is None:
            cls.setup(config.EMAIL_API_KEY)
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
            send_result = cls.client.messages.send_template(template_name='trustmile-feedback',
                                                            template_content=None, message=message)
            logger.info(
                u'Sent email with send id: {0}, status: {1}'.format(send_result[0]['_id'], send_result[0]['status']))
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
