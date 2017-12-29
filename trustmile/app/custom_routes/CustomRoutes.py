from flask import request
from sqlalchemy import and_
from sqlalchemy.orm import exc
from flask import render_template
from app import db
from app.async import tasks
from app.deliveries.model import Consignment, TrustmileDelivery, DeliveryCard
import logging
from flask import Response
import json
import config

from app.location.geocode import Geocoder
from app.messaging.email import EmailHandler
from app.users.model import ConsumerUser, User
from app.retailer_integration import ShopifyHelper
logger = logging.getLogger()


def init_custom_routes(app):
    @app.route('/aftership_webhook', methods=['GET', 'POST'])
    def webhook():
        return process_aftership_webhook_post()

    @app.route('/couriers_please', methods=['POST'])
    def post_missed_delivery():
        return process_couriers_please_missed_delivery()

    @app.route('/shopify/', methods=['POST'])
    @app.route('/shopify', methods=['POST'])
    def shopify_webhook():
        #we are not validating the shopify hmac atm.
        #there is some python for it but too much effort atm.
        return process_shopify()



def process_aftership_webhook_post():
    js = request.json
    # aftership appear to be sending us the full tracking info
    logger.info(u"AfterShip WebHook JSON {0}".format(str(js)))
    if js['msg']['id'] == '000000000000000000000000':
        # this is the JSON that is sent when you configure the webhook in aftership
        return 'hello'

    Consignment.update_trackings(js["msg"])
    return "hello"


def process_couriers_please_missed_delivery():

    headers = request.headers
    delivery_data = request.json
    api_key = headers.get('X-courier-apiKey')
    if api_key != 'e686b40e1d72374de9d31bdfb73e6c0367b7d45fb2772f676c6e8b0985366d06':
        return Response(status=401, response=json.dumps({"status": "Failed",
                                                         "statusDescription": "Unauthorized",
                                                         "durationMs": 10,
                                                         "labelNumber": delivery_data['labelNumber']
                                                         }))

    try:
        label_number = delivery_data['labelNumber']
        tmds = TrustmileDelivery.get_for_tracking_numbers([label_number])
        if len(tmds) < 1:
            return Response(status=404, response=json.dumps({"status": "Failed",
                                                             "statusDescription": "Item not found",
                                                             "durationMs": 10,
                                                             "labelNumber": delivery_data['labelNumber']
                                                             }), mimetype="application/json")

        for tmd in tmds:
            if tmd:
                logger.info(u'Received couriers please notification on TrustmileDelivery id: {0}, labelNumber {1}'.format(
                    tmd.id, label_number))
                email_address = delivery_data['emailAddress']
                recipient_name = delivery_data['contactName']
                tmd.update_info(recipient_name=recipient_name,
                                recipient_phone=delivery_data['mobileNumber'],
                                email_address=email_address, source='couriersPlease')

                dc = DeliveryCard(delivery_data['missedDeliveryCardNumber'], tmd.id)

                recipient = ConsumerUser.query.filter(ConsumerUser.email_address == email_address).first()
                if recipient and not tmd.recipient:
                    logger.info(u'Found recipient {0} in system for couriers please notification card id {1}'.format(
                        recipient.email_address, dc.card_number))
                    tmd.recipient = recipient
                    tasks.send_shipping_notification(
                        recipient.email_address, "Card left for new package", "TrustMile card left", tmd.id)
                if email_address:
                    neighbour = tmd.neighbour
                    # Get the first one as it's sorted by date desc.
                    courier = tmd.courier.courier
                    courier_name = courier.courier_name

                    neighbour_address = neighbour.user.user_address[0]
                    if not neighbour_address.location:
                        # This is mainly a hack for testing.
                        str_address = "{0} {1}, {2}, {3}, {4}, {5}".format(
                            neighbour_address.addressLine1, neighbour_address.addressLine2, neighbour_address.suburb,
                                                                           neighbour_address.postcode,
                                                                           neighbour_address.state, neighbour_address.countryCode)
                        geocoder = Geocoder(config.GOOGLE_LOCATION_KEY)
                        loc = geocoder.geocode(str_address)
                        logger.debug(u"Location is {0}".format(loc))
                        latitude = loc.latitude
                        longitude = loc.longitude
                    else:
                        latitude = neighbour_address.location.latitude
                        longitude = neighbour_address.location.longitude

                    neighbour_info = {'phone': neighbour_address.phoneNumber, 'address_line_1': neighbour_address.addressLine1,
                                      'address_line_2': neighbour_address.addressLine2, 'suburb': neighbour_address.suburb,
                                      'postcode': neighbour_address.postcode, 'name': neighbour.fullName, 'latitude': latitude,
                                      'longitude': longitude}
                    EmailHandler.send_left_with_neighbour_notification(email_address, recipient_name, courier_name, neighbour_info)

                db.session.add(tmd)
                db.session.add(dc)

                db.session.commit()

                return Response(status=200, response=json.dumps({"status": "Accept",
                                                                 "statusDescription": "1 item has been Accepted by TrustMile",
                                                                 "durationMs": 10,
                                                                 "labelNumber": delivery_data['labelNumber']
                                                                 }), mimetype="application/json")
            else:
                try:
                    tasks.associate_delivery_card.delay(delivery_data)
                    return Response(status=404, response=json.dumps({"status": "Failed",
                                                                     "statusDescription": "Item not found",
                                                                     "durationMs": 10,
                                                                     "labelNumber": delivery_data['labelNumber']
                                                                     }), mimetype="application/json")
                except Exception, e:
                    logger.exception(e)

    except exc.NoResultFound, nrfe:
        logger.exception(nrfe)
        return Response(status=404, response=json.dumps({"status": "Failed",
                                                  "statusDescription": "Item not found",
                                                  "durationMs": 10,
                                                  "labelNumber": delivery_data['labelNumber']
                                                  }), mimetype="application/json")

    except Exception, e:
        logger.exception(e)
        return Response(status=500, response=json.dumps({"status": "Failed",
                                                  "statusDescription": "Unknown server error",
                                                  "durationMs": 10,
                                                  "labelNumber": delivery_data['labelNumber']
                                                  }), mimetype="application/json")



def process_shopify():
    shopify_store = request.headers['X_SHOPIFY_SHOP_DOMAIN']
    shopify_topic = request.headers['X_SHOPIFY_TOPIC']
    shopify_json = request.json
    shopify_hmac = request.headers['X_SHOPIFY_HMAC_SHA256']
    try:
        ShopifyHelper.process_shopify_webhook(shopify_store, shopify_topic, shopify_json, shopify_hmac)
        return Response( status=200)
    except Exception, e:
        logger.exception( e)
        return Response( status=500)

