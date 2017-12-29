data1  = {u'msg': {u'tracking_destination_country': None, u'tracking_ship_date': None, u'updated_at': u'2015-12-08T00:33:08+00:00', u'smses': [], u'tag': u'OutForDelivery', u'tracking_key': None, u'id': u'56662540d60059c20c47c306', u'custom_fields': {}, u'customer_name': None, u'tracking_postal_code': None, u'tracked_count': 1, u'title': u'Trustmile Created Tracking', u'origin_country_iso3': u'AUS', u'tracking_account_number': None, u'emails': [u'trackings@trustmile.com'], u'shipment_type': u'Toll IPEC', u'source': u'api', u'order_id_path': None, u'expected_delivery': None, u'destination_country_iso3': u'AUS', u'order_id': None, u'checkpoints': [{u'city': None, u'zip': None, u'checkpoint_time': u'2015-12-07T09:52:00', u'created_at': u'2015-12-08T00:33:08+00:00', u'country_iso3': u'AUS', u'coordinates': [], u'state': None, u'tag': u'InfoReceived', u'country_name': u'IN SYSTEM, Australia', u'message': u'CONNOTE FILE LODGED (E-TRADER)', u'slug': u'toll-ipec'}, {u'city': None, u'zip': None, u'checkpoint_time': u'2015-12-07T16:59:00', u'created_at': u'2015-12-08T00:33:08+00:00', u'country_iso3': u'AUS', u'coordinates': [], u'state': None, u'tag': u'InTransit', u'country_name': u'SYDNEY, Australia', u'message': u'SORTED TO CHUTE', u'slug': u'toll-ipec'}, {u'city': None, u'zip': None, u'checkpoint_time': u'2015-12-08T07:33:00', u'created_at': u'2015-12-08T00:33:08+00:00', u'country_iso3': u'AUS', u'coordinates': [], u'state': None, u'tag': u'InTransit', u'country_name': u'NEWCASTLE, Australia', u'message': u'SCANNED INTO DEPOT', u'slug': u'toll-ipec'}, {u'city': None, u'zip': None, u'checkpoint_time': u'2015-12-08T09:05:00', u'created_at': u'2015-12-08T00:33:08+00:00', u'country_iso3': u'AUS', u'coordinates': [], u'state': None, u'tag': u'OutForDelivery', u'country_name': u'NEWCASTLE, Australia', u'message': u'ON FOR DELIVERY', u'slug': u'toll-ipec'}], u'active': True, u'path': u'-JdGrgX_9e', u'slug': u'toll-ipec' , u'delivery_time': 1, u'shipment_weight_unit': None, u'created_at': u'2015-12-08T00:33:04+00:00', u'tracking_number': u'7179051423051', u'unique_token': u'-JdGrgX_9e', u'signed_by': None, u'shipment_weight': None, u'shipment_package_count': 1}, u'event': u'tracking_update', u'ts': 1449534793}


data2 = {u'msg': {u'tracking_destination_country': None, u'tracking_ship_date': None, u'updated_at': u'2015-12-08T02:33:22+00:00', u'smses': [], u'tag': u'Delivered', u'tracking_key': None, u'id': u'56662540d60059c20c47c306', u'custom_fields': {}, u'customer_name': None, u'tracking_postal_code': None, u'tracked_count': 5, u'title': u'Trustmile Created Tracking', u'origin_country_iso3': u'AUS', u'tracking_account_number': None, u'emails': [u'trackings@trustmile.com'], u'shipment_type': u'Toll IPEC', u'source': u'api', u'order_id_path': None, u'expected_delivery': None, u'destination_country_iso3': u'AUS', u'order_id': None, u'checkpoints': [{u'city': None, u'zip': None, u'checkpoint_time': u'2015-12-07T09:52:00', u'created_at': u'2015-12-08T00:33:08+00:00', u'country_iso3': u'AUS', u'coordinates': [], u'state': None, u'tag': u'InfoReceived', u'country_name': u'IN SYSTEM, Australia', u'message': u'CONNOTE FILE LODGED (E-TRADER)', u'slug': u'toll-ipec'}, {u'city': None, u'zip': None, u'checkpoint_time': u'2015-12-07T16:59:00', u'created_at': u'2015-12-08T00:33:08+00:00', u'country_iso3': u'AUS', u'coordinates': [], u'state': None, u'tag': u'InTransit', u'country_name': u'SYDNEY, Australia', u'message': u'SORTED TO CHUTE', u'slug': u'toll-ipec'}, {u'city': None, u'zip': None, u'checkpoint_time': u'2015-12-08T07:33:00', u'created_at': u'2015-12-08T00:33:08+00:00', u'country_iso3': u'AUS', u'coordinates': [], u'state': None, u'tag': u'InTransit', u'country_name': u'NEWCASTLE, Australia', u'message': u'SCANNED INTO DEPOT', u'slug': u'toll-ipec'}, {u'city': None, u'zip': None, u'checkpoint_time': u'2015-12-08T09:05:00', u'created_at': u'2015-12-08T00:33:08+00:00', u'country_iso3': u'AUS', u'coordinates': [], u'state': None, u'tag': u'OutForDelivery', u'country_name': u'NEWCASTLE, Australia', u'message': u'ON FOR DELIVERY', u'slug': u'toll-ipec'}, {u'city': None, u'zip': None, u'checkpoint_time': u'2015-12-08T13:11:00', u'created_at': u'2015-12-08T02:33:22+00:00', u'country_iso3': u'AUS', u'coordinates': [], u'state': None, u'tag': u'Delivered', u'country_name': u'NEWCASTLE, Australia', u'message': u'FREIGHT DELIVERED', u'slug': u'toll-ipec'}], u'active': False, u'path': u'-JdGrgX_9e', u'slug': u'toll-ipec', u'delivery_time': 2, u'shipment_weight_unit': None, u'created_at': u'2015-12-08T00:33:04+00:00', u'tracking_number': u'7179051423051', u'unique_token': u'-JdGrgX_9e', u'signed_by': None, u'shipment_weight': None, u'shipment_package_count': 1}, u'event': u'tracking_update', u'ts': 1449542007}




import pprint
print len(data1[u'msg'][u'checkpoints'])

pprint.pprint(data1)

print 'xxxxxxxxxxxxxxxxxxxxxxxxx'
print len(data2[u'msg'][u'checkpoints'])
pprint.pprint(data2)

from app.deliveries.model import Consignment, Courier
from app import db
import json, os
import config


db.drop_all()
db.create_all()

def load_couriers():
    path = os.path.dirname(os.path.realpath(__file__))
    d = json.load(open(os.path.join(path + "/tests/" + config.AFTERSHIP_COURIER_FILE)))
    couriers = d

    for c in couriers:
        courier = Courier(c['name'], c['slug'], True)
        db.session.add(courier)

        db.session.commit()

load_couriers()

# c = Consignment.create_or_get_consignment('toll-ipec', '7179051423051', null)

# Consignment.update_trackings(data1[u'msg'])

# Consignment.update_trackings(data2[u'msg'])





