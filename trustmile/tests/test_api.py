import json

import os
from abc import abstractmethod
from nose.tools import *
from werkzeug.datastructures import Headers

import config
from app import db, app
from app.deliveries.model import Courier, Article, TrustmileDelivery
from app.users.model import ConsumerUser
from app.users.model import CourierUser
from . import AppTest
from static_data import *
from api_test_base import ConsumerApiTestMixin, ConsumerApiTestDeliveries

path = os.getcwd()


class ApiTest(AppTest):
    @classmethod
    def load_couriers(cls):
        from app import db
        couriers_file_path = os.path.dirname(os.path.realpath(__file__))
        d = json.load(open(os.path.join(couriers_file_path + "/../tests/" + config.AFTERSHIP_COURIER_FILE)))
        couriers = d

        for c in couriers:
            courier = Courier(c['name'], c['slug'], c['phone'], c['web_url'], trustmile_courier=True)
            db.session.add(courier)
        c = Courier("Allied Express", 'allied-express', '0295555555', 'http://www.alliedexpress.com.au/',
                    trustmile_courier=False, tracking_url='http://www.alliedexpress.com.au/',
                    tracking_info_supported=False)

        db.session.add(c)

        db.session.commit()

    @classmethod
    def setUpClass(cls):
        super(ApiTest, cls).setUpClass()

        cls.app, cls.db = app, db
        cls.client = cls.app.test_client()
        cls.db.drop_all()
        cls.db.create_all()
        cls.load_couriers()
        #
        # EmailHandler.setup(config.EMAIL_API_KEY_DEV)
        # from app.api.consumer_v1 import bp as blueprint
        # cls.app.register_blueprint(blueprint, url_prefix = '/consumer/v1')

    @classmethod
    def tearDownClass(cls):
        super(ApiTest, cls).tearDownClass()
        cls.db.session.remove()
        cls.db.get_engine(cls.app).dispose()

    @abstractmethod
    def setUp(self):
        pass

    @abstractmethod
    def tearDown(self):
        pass

    @property
    def headers(self):
        headers = Headers()
        if self.api_key:
            headers['X-consumer-apiKey'] = self.api_key
        headers['content-type'] = self.content_type
        return headers

    def basic_checks(self, rv):
        eq_(rv.status_code, 200)
        r = json.loads(rv.data)
        assert rv is not None
        assert r is not None
        assert r.get('correlationID') is not None
        return r


class AnonymousUserApiTest(ApiTest, ConsumerApiTestDeliveries):

    def setUp(self):
        self.api_key = None
        self.base_url = '/consumer/v1'
        self.content_type = 'application/json'
        self.environ_overrides = {}
        rv = self.client.post(self.base_url + '/account/anonymous/register', data=json.dumps(anonymous_account_register),
                              headers=self.headers)
        r = json.loads(rv.data)
        self.api_key = r['apiKey']

    def clear(self):
        db.session.query(Article).delete()
        db.session.query(TrustmileDelivery).delete()
        db.session.query(ConsumerUser).delete()
        db.session.query(CourierUser).delete()
        db.session.commit()

    def tearDown(self):
        headers = self.headers
        rv = self.client.delete('{0}/account'.format(self.base_url), headers=headers)
        self.clear()
        self.__class__.db.session.close()


class ConsumerApiTest(ApiTest, ConsumerApiTestMixin, ConsumerApiTestDeliveries):
    # @property
    # def timeout(self):
    #     return self.__class__.timeout

    def setUp(self):
        self.api_key = None
        self.base_url = '/consumer/v1'
        self.content_type = 'application/json'
        self.environ_overrides = {}
        rv = self.client.post(self.base_url + '/account/register', data=json.dumps(account_register),
                              headers=self.headers)
        r = json.loads(rv.data)
        self.api_key = r['apiKey']

    def clear(self):
        db.session.query(Article).delete()
        db.session.query(TrustmileDelivery).delete()
        db.session.query(ConsumerUser).delete()
        db.session.query(CourierUser).delete()
        db.session.commit()

    def tearDown(self):
        headers = self.headers
        rv = self.client.delete('{0}/account'.format(self.base_url), headers=headers)
        self.clear()
        self.__class__.db.session.close()

