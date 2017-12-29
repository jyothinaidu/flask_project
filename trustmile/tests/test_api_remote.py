import json


class RemoteConsumerApiTestMixin:
    def test_account_get(self):
        rv = self.client.get(self.base_url + '/account', headers=self.headers)
        r = self.basic_checks(rv)
        account = r.get('account')
        eq_(account.get('fullName'), account_register.get('fullName'))
        assert r.get('correlationID') is not None

    def test_account_update(self):
        rv = self.client.put(self.base_url + '/account', data=json.dumps(account_update), headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('correlationID') is not None
        rv = self.client.get(self.base_url + '/account', headers=self.headers)
        r = self.basic_checks(rv)

    def test_delivery_feedback(self):
        data = {
            "comment": "Good APP",
            "complaint": [
                "Complain1",
                "Complain2"
            ],
            "rating": 1,
            "netPromoterScore": 9
        }

        rv = self.client.post(self.base_url + '/deliveries',
                              data=json.dumps({"trackingNumber": "79S8067982",
                                               "courierSlug": "australia-post",
                                               "description": "Stuff"}),
                              headers=self.headers)
        result_dict = self.basic_checks(rv)

        delivery_id = result_dict.get('deliveryId')

        rv = self.client.post(self.base_url + '/deliveries/feedback/{0}'.format(delivery_id), data=json.dumps(data),
                              headers=self.headers)

        r = self.basic_checks(rv)

    def test_account_login(self):

        rv = self.client.post(self.base_url + '/account/login', data=json.dumps(account_login),
                              headers=self.headers)
        r = self.basic_checks(rv)

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
                              data=json.dumps({"emailAddress": account_register["emailAddress"]}),
                              headers=self.headers)
        self.basic_checks(rv)

    def test_forgot_password_bad_email(self):
        rv = self.client.post(self.base_url + '/account/forgotPassword',
                              data=json.dumps({"emailAddress": account_register["emailAddress"] + 'foobar'}),
                              headers=self.headers)
        eq_(rv.status_code, 404)

    def test_add_delivery(self):
        rv = self.client.post(self.base_url + '/deliveries',
                              data=json.dumps({"trackingNumber": "79S8067982",
                                               "courierSlug": "australia-post",
                                               "description": "Stuff"}),
                              headers=self.headers)
        result_dict = self.basic_checks(rv)

        deliveryId = result_dict.get('deliveryId')

        time.sleep(2)
        rv = self.client.get(self.base_url + '/deliveries', headers=self.headers)
        r = self.basic_checks(rv)
        assert len(r['deliveries']) > 0
        ds = r.get('deliveries', [])
        posted_tracking_found = False
        for d in ds:
            assert d.get('trackingNumber', None)
            if d.get('trackingNumber') == "79S8067982":
                posted_tracking_found = True
                assert d.get('description') == "Stuff"

        assert posted_tracking_found

        time.sleep(5)
        rv = self.client.get(self.base_url + '/deliveries/tracking/' + deliveryId, headers=self.headers)
        r = self.basic_checks(rv)
        assert r.get('delivery')
        # try adding the same delivery, should be no error
        rv = self.client.post(self.base_url + '/deliveries',
                              data=json.dumps({"trackingNumber": "79S8067982",
                                               "courierSlug": "australia-post",
                                               "description": "Stuff"}),
                              headers=self.headers)
        result_dict = self.basic_checks(rv)

        rv = self.client.delete(self.base_url + '/deliveries', data=json.dumps({"deliveryID": deliveryId}),
                                headers=self.headers)
        self.basic_checks(rv)

        # ensure the consignment has been deleted
        rv = self.client.get(self.base_url + '/deliveries', headers=self.headers)
        r = self.basic_checks(rv)
        ds = r.get('deliveries', [])
        posted_tracking_found = False
        for d in ds:
            assert d.get('trackingNumber', None)
            if d.get('trackingNumber') == "79S8067982":
                posted_tracking_found = True

        assert not posted_tracking_found

        # Test update delivery.

        rv = self.client.put

    # def test_recipient_handover(self):
    #     # create some articles tied to a
    #     tracking_number = 'LV9006545301000600205'
    #     tm_delivery = self.setup_articles(tracking_number)
    #     articles = tm_delivery.articles
    #     cons_user = ConsumerUser.query.filter(ConsumerUser.email_address == account_register['emailAddress']).one()
    #     tm_delivery.neighbour = cons_user
    #     db.session.commit()
    #     url = self.base_url + '/deliveries/recipientHandover/' +  str(tm_delivery.id)
    #     rv = self.client.post(url, headers = self.headers, data = json.dumps({'articleIds': [str(a.id) for a in articles ]}))
    #     self.basic_checks(rv)
    #
    #     self.clear()
    #
    # def test_update_location(self):
    #     rv = self.client.put(self.base_url + '/account', data=json.dumps(account_update), headers=self.headers)
    #     rv = self.client.post(self.base_url + '/user/presence', data=json.dumps(location_update),
    #                           headers=self.headers)
    #
    #     up = db.session.query(UserPresence).one()
    #     assert up
    #     assert up.status
    #     self.basic_checks(rv)

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


        # def test_neighbour_scan_first_item(self):
        #
        #     tracking_number = 'LV9006545301000600205'
        #     self.setup_articles(tracking_number)
        #     rv = self.client.get(self.base_url + '/deliveries/neighbourReceive/' + tracking_number, headers=self.headers)
        #     self.basic_checks(rv)
        #     self.clear()
        #
        # def setup_articles(self, tracking_number):
        #     # Setup, TODO: eventually this should be replaced by api calls rather than db calls.
        #     courier_user = CourierUser.create('brucearthurs', 'boundary', 'James O''Rourke')
        #     cons_user = ConsumerUser.create('bruce@trustmile.com', 'boundary', name='James O''Rourke')
        #     articles = Article.create_new_articles_for_user(cons_user, [tracking_number, 'VY30029390'])
        #     tm_delivery = TrustmileDelivery.create(courier_user, articles)
        #     db.session.commit()
        #     return tm_delivery
        #
        #
        # def clear(self):
        #     db.session.query(Article).delete()
        #     db.session.query(TrustmileDelivery).delete()
        #     db.session.query(ConsumerUser).delete()
        #     db.session.query(CourierUser).delete()
        #     db.session.commit()

        # def test_reset_password(self):
        #
        #     # 1) request password reset
        #     # 2) read reset token from cu
        #     # 3) check ResetPassword GET
        #     # 4) set new password
        #     # 5) check login works with the new password
        #
        #     new_password = "qwerty123456"
        #
        #     # 1) request password reset
        #     self.test_forgot_password()
        #
        #     cu = db.session.query(ConsumerUser).filter_by(email_address=account_login["emailAddress"]).one()
        #     # as cu will be modified, SQLAlchemy invalidates the object (something about not being bound to a session )
        #     # and borks
        #     # so we need to make a copy of variables here
        #     password_reset_token = str(cu.password_reset_token)
        #     print(password_reset_token)
        #     # 2 & 3
        #     rv = self.client.get(self.base_url + '/account/resetPassword/' + password_reset_token,
        #                          headers=self.headers)
        #
        #     result_dict = self.basic_checks(rv)
        #
        #     emailAddress = result_dict.get('emailAddress')
        #     assert emailAddress == mask_email_address(account_login["emailAddress"])
        #
        #     rv = self.client.post(self.base_url + '/account/resetPassword/' + password_reset_token,
        #                           data=json.dumps({"newPassword": new_password}),
        #                           headers=self.headers)
        #     self.basic_checks(rv)
        #
        #     # 5)
        #     rv = self.client.post(self.base_url + '/account/login', data=json.dumps(
        #         {"emailAddress": account_login["emailAddress"], "password": new_password}), headers=self.headers)
        #     self.basic_checks(rv)
        #
        #     # TODO Failure cases for resetPassword API

# TODO: james  - Get better "prod" testing and this is part of it.
class RemoteConsumerApiTest(RemoteConsumerApiTestMixin):
    @classmethod
    def setUpClass(cls):
        # super(RemoteConsumerApiTest, cls).setUpClass()
        cls.kwargs = config.FLASK_CLIENT_CONFIG
        cls.kwargs.get('content_type')
        cls.client = requests
        cls.base_url = "http://devapi.trustmile.com/consumer/v1"
        cls.content_type = 'application/json'

    @classmethod
    def tearDownClass(cls):
        pass
        # super(RemoteConsumerApiTest, cls).tearDownClass()

    @property
    def base_url(self):
        return self.__class__.base_url

    @property
    def content_type(self):
        return self.__class__.content_type

    def get_json(self, r):
        return r.json()

    @property
    def headers(self):
        headers = {'content-type': self.content_type}
        if self.api_key:
            headers.update({'X-consumer-apiKey': self.api_key})
        return headers

    def basic_checks(self, rv):
        eq_(rv.status_code, 200)
        r = rv.json()
        assert rv is not None
        assert r is not None
        assert r.get('correlationID') is not None
        return r

    def setUp(self):
        # super(RemoteConsumerApiTest, self).setUp()
        self.api_key = None
        self.register_deets = account_register
        print self.register_deets
        r = self.client.post('{0}/account/register'.format(self.base_url), data=json.dumps(self.register_deets),
                             headers=self.headers)
        j = r.json()
        self.api_key = j['apiKey']

    def tearDown(self):
        rv = self.client.delete('{0}/account'.format(self.base_url), headers=self.headers)
        # self.__class__.db.session.close()
        # super(RemoteConsumerApiTest, self).tearDown()

    def test_pass(self):
        assert True

#
# class RemoteSSLApiTest(RemoteConsumerApiTest):
#     @classmethod
#     def setUpClass(cls):
#         super(RemoteSSLApiTest, cls).setUpClass()
#         cls.base_url = cls.kwargs.get('base_url').replace('http', 'https')
