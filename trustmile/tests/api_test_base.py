import ascii85
import copy
import datetime
import json
import time

import os
from abc import abstractmethod
from nose.tools import *
from werkzeug.datastructures import Headers

import config
from app import db, app
from app.deliveries.model import Courier, Article, TrustmileDelivery, DeliveryDelegate, Consignment
from app.ops.consumer_operations import mask_email_address, DeliveryState
from app.retailer_integration.model import Retailer, RetailerIntegrationConsignment
from app.users.model import ConsumerUser, CourierUser
from . import AppTest
from static_data import *


class ConsumerApiTestDeliveries:


    def test_add_delivery(self):
        rv = self.client.post(self.base_url + '/deliveries',
                              data=json.dumps({"trackingNumber": "MZN0001784",
                                               "courierSlug": "australia-post",
                                               "description": "Stuff"}),
                              headers=self.headers)
        result_dict = self.basic_checks(rv)

        deliveryId = result_dict.get('deliveryId')

        rv = self.client.get(self.base_url + '/deliveries', headers=self.headers)
        r = self.basic_checks(rv)
        assert len(r['deliveries']) > 0
        time.sleep(1)
        rv = self.client.get(self.base_url + '/deliveries', headers=self.headers)
        r = self.basic_checks(rv)
        ds = r.get('deliveries', [])
        posted_tracking_found = False
        for d in ds:
            assert d.get('trackingNumber', None)
            eq_(d.get('isNeighbour'), False)
            if d.get('trackingNumber') == "MZN0001784":
                posted_tracking_found = True
                assert d.get('description') == "Stuff"
                eq_(d.get('imageUrl'), 'http://assets.trustmile.com/images/courier/australia-post.png')
                import requests
                resp = requests.get(d.get('imageUrl'))
                assert resp.content

        assert posted_tracking_found

        time.sleep(1)
        rv = self.client.get(self.base_url + '/deliveries/' + deliveryId, headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('delivery')

        rv = self.client.post(self.base_url + '/deliveries',
                              data=json.dumps({"trackingNumber": "MZN0001784",
                                               "courierSlug": "allied-express", "description": "Stuff"}),
                              headers=self.headers)
        result_dict = self.basic_checks(rv)
        delivery_id = result_dict.get('deliveryId')

        rv = self.client.get(self.base_url + '/deliveries/' + delivery_id, headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('delivery')

        description = "New stuff"
        rv = self.client.put(self.base_url + '/deliveries/' + delivery_id, headers=self.headers,
                             data=json.dumps({"description": description}))

        r = self.basic_checks(rv)
        rv = self.client.get(self.base_url + '/deliveries/' + delivery_id, headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('delivery')
        delivery = r.get('delivery')
        eq_(delivery.get('description'), description)


    def test_order_info(self):
        rv = self.client.post(self.base_url + '/deliveries',
                              data=json.dumps({"trackingNumber": "MZN0001784",
                                               "courierSlug": "australia-post",
                                               "description": "Stuff"}),
                              headers=self.headers)
        result_dict = self.basic_checks(rv)
        retailer_name = 'IndulgeHQ'
        r1 = Retailer(retailer_name, 'UID1', retailer_config)
        r1.slug = 'indulgehq'
        retailer_image_url = 'http://assets.trustmile.com/images/retailer/' + r1.slug + '.png'
        r1.email_server_configuration = email_server1
        r1.secret = 'abc123'
        db.session.add(r1)
        order_id = 'OR12345'
        r1_con = RetailerIntegrationConsignment()
        r1_con.retailer = r1
        r1_con.order_id = order_id
        r1_con.email_address = 'customer1@trustmile.com'
        r1_con.tracking_number = 'MZN0001784'
        r1_con.consignment = Consignment.query.get(result_dict['deliveryId'])
        r1_con.consignment.retailer = r1
        r1_con.courier = Courier.retrieve_courier('australia-post')

        db.session.add(r1_con)

        # check why below orderinfo test is failing
        # # create a consumer user
        # cons_user = ConsumerUser.create('bruce@trustmile.com', 'boundary', name='James O''Rourke')
        # db.session.add(cons_user)
        db.session.commit()
        # rv = self.client.get(self.base_url + '/order/' + r1_con.order_id, headers=self.headers)
        # r = self.basic_checks(rv)
        # eq_(r.get('order').get('orderId'), order_id)

        rv = self.client.get(self.base_url + '/deliveries', headers=self.headers)
        r = self.basic_checks(rv)
        eq_(r.get('deliveries')[0].get('retailerName'), retailer_name)
        eq_(r.get('deliveries')[0].get('retailerImageUrl'), retailer_image_url)
        delivery_id = r.get('deliveries')[0].get('deliveryId')

        rv = self.client.get(self.base_url + '/deliveries/' + delivery_id, headers=self.headers)
        r = self.basic_checks(rv)
        eq_(r.get('delivery').get('retailerName'), retailer_name)
        eq_(r.get('delivery').get('retailerImageUrl'), retailer_image_url)

    def test_get_anonymous(self):
        slug = 'australia-post'
        tracking_number = 'ABC_ANON_123'

        # check consignment does not exist
        cons = Consignment.get_consignments(slug, tracking_number)
        self.assertEquals(len(cons), 0)

        # add consignment
        rv = self.client.get(self.base_url + '/anonymous/tracking/' + slug + '/' + tracking_number,
                             headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('delivery')

        cons = Consignment.get_consignments(slug, tracking_number)
        self.assertEquals(len(cons), 1)
        self.assertEquals(cons[0].retailer, None)

        # add same consignment with a retailer
        retailer_name = 'TestRetailer'
        r1 = Retailer(retailer_name, 'UID1', retailer_config)
        r1.slug = 'indulgehq'
        r1.secret = 'abc123'
        r1.email_server_configuration = email_server1
        db.session.add(r1)
        db.session.commit()

        rv = self.client.get(
            self.base_url + '/anonymous/tracking/' + slug + '/' + tracking_number + '?retailer=' + retailer_name,
            headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('delivery')

        cons = Consignment.get_consignments(slug, tracking_number)
        self.assertEquals(len(cons), 1)
        self.assertEquals(cons[0].retailer.website_name, retailer_name)

    def test_consignment_methods(self):
        # testing retailer related methods

        slug = 'australia-post'
        tracking_number = 'ABC_ANON_123456'
        retailer_name = 'TestRetailer2'
        r1 = Retailer(retailer_name, 'UID12', retailer_config)
        r1.slug = 'test-retailer-slug'
        r1.email_server_configuration = email_server1
        r1.secret = 'abc123'
        db.session.add(r1)
        db.session.commit()

        rv = self.client.get(
            self.base_url + '/anonymous/tracking/' + slug + '/' + tracking_number + '?retailer=' + retailer_name,
            headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('delivery')

        cons = Consignment.get_consignments(slug, tracking_number)
        self.assertEquals(len(cons), 1)
        self.assertNotEquals(cons[0].get_retailer_image_url().lower().find('test-retailer-slug.png'), -1)
        self.assertEquals(cons[0].get_retailer_name(), retailer_name)

        r1 = Retailer('TestRetailer3', 'UID12', retailer_config)
        r1.slug = 'test-retailer-slug'
        r1.secret = 'abc123'
        r1.email_server_configuration = email_server1
        db.session.add(r1)
        db.session.commit()

        cons[0].set_retailer(r1, 'URL')
        # retailer should not have changed
        self.assertEquals(cons[0].retailer.website_name, 'TestRetailer2')

        cons[0].set_retailer(r1, 'Integration')
        # retailer changed
        self.assertEquals(cons[0].retailer.website_name, 'TestRetailer3')


class ConsumerApiTestMixin:
    def test_account_get(self):
        rv = self.client.put(self.base_url + '/account', data=json.dumps(account_update), headers=self.headers)
        rv = self.client.get(self.base_url + '/account', headers=self.headers)
        r = self.basic_checks(rv)
        account = r.get('account')
        eq_(account.get('fullName'), account_update.get('fullName'))
        assert account.get('userPreferences')
        rv = self.client.put(self.base_url + '/account', data=json.dumps(account_update2), headers=self.headers)

        rv = self.client.get(self.base_url + '/account', headers=self.headers)

        r = self.basic_checks(rv)

        account = r.get('account')
        for d in account['userPreferences']['values']:
            k = d.get('key')
            if k == 'courierHonesty':
                assert d.get('value') == False
            if k == 'userLocation':
                assert d.get('value') == '40.7590110,-73.9844720'

        # eq_(account.get('userPreferences').get('courierHonesty'), True)

        assert r.get('correlationID') is not None

    def test_delivery_feedback(self):

        rv = self.client.post(self.base_url + '/deliveries',
                              data=json.dumps({"trackingNumber": "MZN0001784",
                                               "courierSlug": "australia-post",
                                               "description": "Stuff"}),
                              headers=self.headers)
        result_dict = self.basic_checks(rv)

        delivery_id = result_dict.get('deliveryId')

        rv = self.client.post(self.base_url + '/deliveries/feedback/{0}'.format(delivery_id),
                              data=json.dumps(delivery_feedback),
                              headers=self.headers)
        eq_(rv.status_code, 200)

        rv = self.client.get(self.base_url + '/deliveries', headers=self.headers)
        r = self.basic_checks(rv)

        rv = self.client.post(self.base_url + '/deliveries/feedback/{0}'.format(delivery_id),
                              data=json.dumps(delivery_feedback_2),
                              headers=self.headers)

        eq_(rv.status_code, 200)

        rv = self.client.get(self.base_url + '/deliveries', headers=self.headers)
        r = self.basic_checks(rv)


    def test_delegate_delivery(self):
        rv = self.client.post(self.base_url + '/deliveries',
                              data=json.dumps({"trackingNumber": "79S8067982",
                                               "courierSlug": "australia-post",
                                               "description": "Stuff"}),
                              headers=self.headers)

        result_dict = self.basic_checks(rv)

        delivery_id = result_dict.get('deliveryId')

        rv = self.client.get(self.base_url + '/deliveries/delegateLink/{0}'.format(delivery_id),
                             headers=self.headers)

        r = self.basic_checks(rv)

        assert r.get('delegateLink').startswith('http://push.trustmile.com')

        delegate_data = {'email': account_register['emailAddress'], 'deliveryId': delivery_id}
        rv = self.client.post(self.base_url + '/deliveries/delegate', headers=self.headers,
                              data=json.dumps(delegate_data))

        r = self.basic_checks(rv)

        dd = DeliveryDelegate.query.filter(DeliveryDelegate.delivery_id == delivery_id).one()
        eq_(dd.completed, True)



    def test_account_update(self):
        rv = self.client.put(self.base_url + '/account', data=json.dumps(account_update), headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('correlationID') is not None
        rv = self.client.get(self.base_url + '/account', headers=self.headers)
        r = self.basic_checks(rv)

    def test_anonymous_register(self):
        rv = self.client.post(self.base_url + '/account/anonymous/register',
                              data=json.dumps(anonymous_account_register), headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('correlationID') is not None
        assert r.get('apiKey')

    def test_neighbour_enabled_zone_account_update(self):
        rv = self.client.put(self.base_url + '/account', data=json.dumps(neighbour_region_enabled_account_update),
                             headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('correlationID') is not None
        rv = self.client.get(self.base_url + '/account', headers=self.headers)
        r = self.basic_checks(rv)
        print r
        assert 'regionNeighbourEnabled' in [k.get('key') for k in r.get('account').get('userPreferences').get('values')]

    def test_account_login(self):
        rv = self.client.post(self.base_url + '/account/login', data=json.dumps(account_login), headers=self.headers)
        r = self.basic_checks(rv)
        assert r['userId']

    def test_account_preferences(self):
        prefs = {"userPreferences": {"values": [
            {"key": "courierHonesty", "value": "False"},
            {"key": "userLocation", "value": "27.686927,85.315128"},
            {"key": "neighbourEnabled", "value": True}
        ]}}
        rv = self.client.put(self.base_url + '/account',
                             data=json.dumps(prefs), headers=self.headers)
        rv = self.basic_checks(rv)

        rv = self.client.get(self.base_url + '/account', headers=self.headers)
        rv = self.basic_checks(rv)
        eq_(len(rv['account']['userPreferences']['values']), 3)

    def test_password_update(self):
        rv = self.client.post(self.base_url + '/account/password',
                              data=json.dumps(pasword_update), headers=self.headers)

    def test_password_update_failure(self):
        passwordu = {"newPassword": "boundary12345", "oldPassword": "boundary1234XXXX"}
        rv = self.client.post('{0}/account/password'.format(self.base_url),
                              data=json.dumps(passwordu), headers=self.headers)
        eq_(rv.status_code, 403)

    def test_reverify_email(self):
        rv = self.client.put(self.base_url + '/account/reverifyEmail', headers=self.headers)

        self.basic_checks(rv)

    def test_forgot_password(self):
        rv = self.client.post(self.base_url + '/account/forgotPassword',
                              data=json.dumps({"emailAddress": account_register["emailAddress"]}), headers=self.headers)
        self.basic_checks(rv)

    def test_forgot_password_bad_email(self):
        rv = self.client.post(self.base_url + '/account/forgotPassword',
                              data=json.dumps({"emailAddress": account_register["emailAddress"] + 'diddils'}),
                              headers=self.headers)
        eq_(rv.status_code, 404)



    def test_recipient_handover(self):
        # create some articles tied to a
        print "####################### TEST RECIP HANDOVER ************* ###############"
        tracking_number = 'LV9006545301000600205'

        tm_delivery = self.setup_articles(tracking_number)
        tm_delivery.state = DeliveryState.NEIGHBOUR_RECEIVED.value
        articles = tm_delivery.articles
        cons_user = ConsumerUser.query.filter(ConsumerUser.email_address == account_register['emailAddress']).one()
        tm_delivery.neighbour = cons_user
        db.session.commit()
        delivery_id = tm_delivery.id
        url = self.base_url + '/deliveries/recipientHandover/' + str(delivery_id)
        recipient_handover_details = {'articleIds': [str(a.id) for a in articles], 'recipientName': 'Joe Public'}

        rv = self.client.post(url, headers=self.headers, data=json.dumps(recipient_handover_details))
        r = self.basic_checks(rv)
        print r
        rv = self.client.get(self.base_url + '/deliveries/trustmile/' + str(delivery_id), headers=self.headers)
        r = self.basic_checks(rv)
        eq_(r['delivery']['recipientName'], 'Joe Public')

    def test_neighbour_receive(self):
        tracking_number = 'LV9006545301000600205'
        r = self.post_articles_setup(tracking_number)
        self.api_key = r['apiKey']

        url = self.base_url + '/deliveries/neighbourReceiveLookup/' + tracking_number
        rv = self.client.get(url, headers=self.headers, data={})
        rv = self.basic_checks(rv)
        print rv

        dId = rv['deliveryId']
        trackings = [a['trackingNumber'] for a in rv['articles']]
        print u'will accept delivery {0} with {1} now'.format(dId, trackings)

        url = self.base_url + '/deliveries/neighbourReceive/' + dId
        print url
        rv = self.client.post(url, headers=self.headers,
                              data=json.dumps({'articles': trackings}))
        r = self.basic_checks(rv)

    def test_get_delivery_adds_to_user(self):
        courier = Courier.retrieve_courier('australia-post')
        cons = Consignment(courier, 'ADD123456')
        db.session.add(cons)
        db.session.commit()

        # check consignment is not in the users account
        cu = ConsumerUser.get('this_is_it2@cloudadvantage.com.au')
        user = cu.user
        for uc in user.user_consignments:
            if uc.consignment.courier.courier_slug == 'australia-post' and uc.consignment.tracking_number == 'ADD123456':
                raise Exception(
                    'consignment exists in the users account.  THis is a DB/setup problem with the test')

        rv = self.client.get(self.base_url + '/deliveries/tracking/' + str(cons.id), headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('delivery')

        cu = ConsumerUser.get('this_is_it2@cloudadvantage.com.au')
        user = cu.user
        consignment_in_account = False
        for uc in user.user_consignments:
            if uc.consignment.courier.courier_slug == 'australia-post' and uc.consignment.tracking_number == 'ADD123456':
                consignment_in_account = True

        assert consignment_in_account


    def test_card_lookup(self):

        tracking_number = 'LV9006545301000600205'
        card_number = 'NHCLCON0170355'
        r = self.post_articles_setup(tracking_number)
        self.api_key = r['apiKey']
        couriers_please_data = {
            "Courier": "CouriersPlease",
            "storeDlb": "LOC0042184",
            "missedDeliveryCardNumber": card_number,
            "labelNumber": tracking_number,
            "consignmentNumber": "CPAYJRZ1066609",
            "totalNumberOfLogisticUnits": "1",
            "contactName": "James ORourke",
            "mobileNumber": "",
            "emailAddress": "james@trustmile.com"
        }
        user_address_update = {
            "accountAddress": {
                "countryCode": "AU",
                "suburb": "Elizabeth Bay",
                "state": "NSW",
                "postcode": "2011",
                "addressLine1": "801/12 Ithaca Rd",
                "addressLine2": "",
                "phoneNumber": "0410 932 980"
            }
        }
        bogus_couriers_please_data = {
            "Courier": "CouriersPlease",
            "storeDlb": "LOC0042184",
            "missedDeliveryCardNumber": 'NHCLCON0170367',
            "labelNumber": 'LV90065453010006002XX',
            "consignmentNumber": "CPAYJRZ10666XX",
            "totalNumberOfLogisticUnits": "1",
            "contactName": "James ORourke",
            "mobileNumber": "",
            "emailAddress": "james@trustmile.com"
        }

        rv = self.client.put(self.base_url + '/account', data=json.dumps(user_address_update),
                             headers=self.headers)
        r = self.basic_checks(rv)

        headers = Headers()
        headers['X-courier-apiKey'] = 'e686b40e1d72374de9d31bdfb73e6c0367b7d45fb2772f676c6e8b0985366d06'
        headers['content-type'] = 'application/json'

        self.headers['X-courier-apiKey'] = 'e686b40e1d72374de9d31bdfb73e6c0367b7d45fb2772f676c6e8b0985366d06'
        rv = self.client.post('/couriers_please', data=json.dumps(couriers_please_data), headers=headers)

        rv = self.client.get(self.base_url + '/deliveries/cardLookup/' + card_number, headers=self.headers)

        r = self.basic_checks(rv)

        eq_(r.get('neighbourName'), 'James O''Rourke')
        assert (r.get('secretWord'))
        assert (r.get('articleCount'))
        assert (r.get('courierName'))
        assert (r.get('recipientInfo'))

        rv = self.client.get(self.base_url + '/deliveries/cardLookup/' + "BOGUSCARDNUMBER", headers=self.headers)

        eq_(rv.status_code, 404)

        rv = self.client.post('/couriers_please', data=json.dumps(bogus_couriers_please_data), headers=headers)
        eq_(rv.status_code, 404)

    def test_update_location(self):
        rv = self.client.put(self.base_url + '/account', data=json.dumps(account_update), headers=self.headers)
        rv = self.client.post(self.base_url + '/user/presence', data=json.dumps(location_update),
                              headers=self.headers)

        # TODO: Must fix this. issue with celery running on jenkins server
        # time.sleep(1)
        # up = db.session.query(UserPresence).one()
        # assert up
        # assert up.status
        self.basic_checks(rv)

    def test_verify_email(self):

        rv = self.client.get(self.base_url + '/account', headers=self.headers)
        r = self.basic_checks(rv)
        email_verification_code = r.get('')

        rv = self.client.get(self.base_url + '/account/verifyEmail')

    def test_feedback(self):
        rv = self.client.post(self.base_url + '/feedback', headers=self.headers,
                              data=json.dumps({
                                  "consumerName": 'Aaron ''T'' Foote',
                                  "consumerEmail": 'aaron_test@trustmile.com',
                                  "feedbackMessage": 'Test Feedback Message ' + str(datetime.datetime.now())
                              }))
        r = self.basic_checks(rv)

    def test_neighbour_scan_first_item(self):

        tracking_number = 'LV9006545301000600205'
        r = self.post_articles_setup(tracking_number)

        self.api_key = r['apiKey']
        rv = self.client.get(self.base_url + '/deliveries/neighbourReceiveLookup/' + 'bad_article_id',
                             headers=self.headers)
        eq_(rv.status_code, 404)
        rv = self.client.get(self.base_url + '/deliveries/neighbourReceiveLookup/' + tracking_number,
                             headers=self.headers)
        self.basic_checks(rv)

    def post_articles_setup(self, tracking_number):
        cons_user_info = {'emailAddress': 'bruce@trustmile.com', 'password': 'boundary'}
        cons_user = ConsumerUser.create(cons_user_info['emailAddress'], cons_user_info['password'],
                                        name='James O''Rourke')
        courier_login_info = {"username": "courier_0101", "password": "password5",
                              "fullName": "Rapid Gonzales, Esq."}
        courier_user = CourierUser.create(courier_login_info['username'], courier_login_info['password'],
                                          'Rapid Gonzales, Esq.', Courier.retrieve_courier('couriers-please'))
        db.session.commit()
        del courier_login_info['fullName']
        cons_user_id = str(cons_user.id)
        courier_headers = copy.copy(self.headers)
        del courier_headers['X-consumer-apiKey']
        rv = self.client.post('/courier/v1/login', data=json.dumps(courier_login_info), headers=courier_headers)
        r = json.loads(rv.data)
        courier_api_key = r['apiKey']
        courier_headers['X-consumer-apiKey'] = courier_api_key
        rv = self.client.post('/courier/v1/deliveries', data=json.dumps(
            {'articles': [{'trackingNumber': tracking_number, 'articleId': '123123123123'}],
             'neighbourId': cons_user_id}), headers=courier_headers)
        rv = self.client.post(self.base_url + '/account/login', data=json.dumps(
            {"emailAddress": cons_user_info['emailAddress'], "password": cons_user_info['password']}),
                              headers=self.headers)
        r = self.basic_checks(rv)
        return r

    def test_get_trustmile_delivery_info(self):
        tracking_number = 'LV9006545301000600205'
        tm_delivery = self.setup_articles(tracking_number)
        tm_delivery_id = tm_delivery.id
        rv = self.client.get(self.base_url + '/deliveries/trustmile/' + str(tm_delivery_id), headers=self.headers)
        r = self.basic_checks(rv)

        assert r.get('delivery').get('articles')
        assert r.get('delivery').get('recipientName')
        assert r.get('delivery').get('secretWord')



    def setup_articles(self, tracking_number):
        # Setup, TODO: eventually this should be replaced by api calls rather than db calls.
        my_courier_user = CourierUser.create('brucearthurs', 'boundary', 'James O''Rourke',
                                             Courier.retrieve_courier('couriers-please'))
        cons_user = ConsumerUser.create('bruce@trustmile.com', 'boundary', name='James O''Rourke')
        articles = Article.new_articles(my_courier_user, [tracking_number, 'VY30029390'])
        tm_delivery = TrustmileDelivery.create(my_courier_user, articles)
        db.session.commit()
        return tm_delivery



    def test_reset_password(self):

        # 1) request password reset
        # 2) read reset token from cu
        # 3) check ResetPassword GET
        # 4) set new password
        # 5) check login works with the new password

        new_password = "qwerty123456"

        # 1) request password reset
        self.test_forgot_password()

        cu = db.session.query(ConsumerUser).filter_by(email_address=account_login["emailAddress"]).one()
        # as cu will be modified, SQLAlchemy invalidates the object (something about not being bound to a session )
        # and borks
        # so we need to make a copy of variables here
        password_reset_token = str(cu.password_reset_token)
        print(password_reset_token)
        # 2 & 3
        rv = self.client.get(self.base_url + '/account/resetPassword/' + password_reset_token,
                             headers=self.headers)

        result_dict = self.basic_checks(rv)

        emailAddress = result_dict.get('emailAddress')
        assert emailAddress == mask_email_address(account_login["emailAddress"])

        rv = self.client.post(self.base_url + '/account/resetPassword/' + password_reset_token,
                              data=json.dumps({"newPassword": new_password}),
                              headers=self.headers)
        self.basic_checks(rv)

        # 5)
        rv = self.client.post(self.base_url + '/account/login', data=json.dumps(
            {"emailAddress": account_login["emailAddress"], "password": new_password}), headers=self.headers)
        self.basic_checks(rv)


    def test_myapi(self):

        rv = self.client.get(self.base_url + '/account', headers=self.headers)
        r = self.basic_checks(rv)
        myapiCode = r.get('')

        rv = self.client.get(self.base_url + '/account/testmyapi')
        assert r.get('correlationID') is not None

