import hashlib, base64, hmac, json
from app.retailer_integration.model import Retailer, RetailerShopifyTracking, RetailerGlobalSettings
from app.retailer_integration.RetailerIntegration import RetailerIntegration
from app import db
from app.model.meta.base import commit_on_success
from app.deliveries.model import Courier
import logging

def process_shopify_webhook(store, topic, json, hmac):
    retailer = Retailer.get_shopify_retailer( store )

    if not retailer:
        raise Exception( 'shopify web hook - retailer not found {0}'.format(store))
        return

    if topic == 'fulfillments/create' or topic == 'fulfillments/update':
        shopify_fulfillment( retailer, topic, json)



def shopify_fulfillment( retailer, topic, json):
    shopify_tracking = RetailerShopifyTracking()
    shopify_tracking.shopify_topic = topic
    shopify_tracking.retailer = retailer
    shopify_tracking.courier_string = json.get( 'tracking_company')
    shopify_tracking.tracking_numbers = json.get( 'tracking_numbers')
    shopify_tracking.order_id = json.get( 'order_id')
    shopify_tracking.to_email_address = json.get( 'email')
    shopify_tracking.destination =     json.get( 'destination')

    db.session.add( shopify_tracking)
    db.session.commit()

    if shopify_tracking.courier_string and shopify_tracking.tracking_numbers:
        ri = RetailerIntegration()
        courier_name = RetailerGlobalSettings.get_shopify_courier_mapping(shopify_tracking.courier_string)
        if not courier_name:
            courier_name = shopify_tracking.courier_string


        if not courier_name:
            logging.warn( 'shopify web hook - no courier name {0}'.format(retailer.website_name))
            return

        courier = Courier.retrieve_courier( courier_name)
        if not courier:
            logging.warn( 'shopify web hook - no courier found {0} - {1}'.format(retailer.website_name, courier_name))
            return

        for tracking_number in shopify_tracking.tracking_numbers:
            ri.add_shopify_tracking(shopify_tracking.retailer, shopify_tracking, shopify_tracking.to_email_address, shopify_tracking.order_id,tracking_number, courier)




# def verify_shopify_hmac(f):
#   """
#   A decorator thats checks and validates a Shopify Webhook request.
#   """
#
#   def _hmac_is_valid(body, secret, hmac_to_verify):
#     hash            = hmac.new(body, secret, hashlib.sha256)
#     hmac_calculated = base64.b64encode(hash.digest())
#     return hmac_calculated == hmac_to_verify
#
#   @wraps(f)
#   def wrapper(request, *args, **kwargs):
#     # Try to get required headers and decode the body of the request.
#     try:
#       webhook_topic = request.META['HTTP_X_SHOPIFY_TOPIC']
#       webhook_hmac  = request.META['HTTP_X_SHOPIFY_HMAC_SHA256']
#       webhook_data  = json.loads(request.body)
#     except:
#       return HttpResponseBadRequest()
#
#     # Verify the HMAC.
#     if not _hmac_is_valid(request.body, settings.SHOPIFY_API_SECRET, webhook_hmac):
#       return HttpResponseForbidden()
#
#     # Otherwise, set properties on the request object and return.
#     request.webhook_topic = webhook_topic
#     request.webhook_data  = webhook_data
#     return f(request, args, kwargs)
#
#   return wrapper