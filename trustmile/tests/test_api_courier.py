from abc import abstractmethod

__author__ = 'james'
from tests import AppTest
from nose.tools import *
from werkzeug.datastructures import Headers
from app import app
from app.deliveries.model import *
from app.users.model import *
import os
from app.users.serialize import *
import json

account_register = {
    "fullName": "James Bruceton",
    "password": "boundary1234",
    "emailAddress": "this_is_it2@cloudadvantage.com.au",
    "installationInformation": {
        "OSType": "iOS",
        "OSMinorVersion": "1",
        "DeviceIdentifier": "123123123123123123",
        "ApplicationVersion": "0.1",
        "OSMajorVersion": "8"
    }
}

account_login_deep = {
	"installationInformation":{"ApplicationVersion":"1.0",
	"OSMinorVersion":"2",
	"OSType":"iPhone OS",
	"DeviceIdentifier":"C83C5562-D7B6-4F17-8C62-E9373E0D2D72",
	"OSMajorVersion":"9"
}
	,"username":"deep2",
	"password":"2222deep"

}

account_login = {
    "password": "boundary1234",
    "emailAddress": "this_is_it2@cloudadvantage.com.au",
}


account_update = {
    "accountAddress": {
        "countryCode": "AU",
        "suburb": "Elizabeth Bay",
        "state": "NSW",
        "postcode": "2011",
        "addressLine1": "801/12 Ithaca Rd",
        "addressLine2": ""
    },
    "fullName": "James Arthurs",
    "trustmileNeighbour": "true",
    "installationInformation": {
        "OSType": "iOS",
        "OSMinorVersion": "1",
        "DeviceIdentifier": "123123123123123123",
        "ApplicationVersion": "0.1",
        "OSMajorVersion": "8"
    }
}

location_update = {
    "status": True,
    "location": {
        "latitude": -33.871755,
        "longitude": 151.228769

    }
}



# narendra = {u'accountAddress': {u'countryCode': u'Australia', u'suburb': u'Sydney', u'state': u'New South Wales',
#                                 u'addressLine2': u'', u'postcode': u'2010',
#                                 u'addressLine1': u'2 Holt Street Surry Hills NSW 2010 Australia'},
#             u'fullName': u'Narendra Kathayat',
#             u'installationInformation': {u'OSType': u'iPhone OS', u'OSMinorVersion': u'0',
#                                          u'DeviceIdentifier': u'FD7C5E09-19F2-432B-AA30-8C9420E163ED',
#                                          u'ApplicationVersion': u'1.0', u'OSMajorVersion': u'9'}}

pasword_update = {
    "newPassword": "boundary12345",
    "oldPassword": "boundary1234"
}

courier_user = {
    "username": "courier_0101",
    "password": "password5",
    "fullName": "Rapid Gonzales, Esq.",
    "emailAddress": "RapidGonzales@hisowncouriercompany.com"
}
    
courier_account_login = {
    "username": "courier_0101",
    "password": "password5" 
}

courier_pw_update_bad = {
    "username": "courier_0101",
    "oldPassword": "password5", 
    "newPassword": "123" 
}

courier_pw_update_ok = {
    "username": "courier_0101",
    "oldPassword": "password5", 
    "newPassword": "password123" 
}



path = os.getcwd()



class ApiTest(AppTest):

    @classmethod
    def load_couriers(cls):
        from app import db
        path = os.path.dirname(os.path.realpath(__file__))
        d = json.load(open(os.path.join(path + "/../tests/" + config.AFTERSHIP_COURIER_FILE)))
        couriers = d

        for c in couriers:
            courier = Courier(c['name'], c['slug'], c['phone'], c['web_url'], trustmile_courier=True)
            db.session.add(courier)

        db.session.flush()

    # @classmethod
    # def setUpClass(cls):
    #     super(ApiTest, cls).setUpClass()

    #     cls.app, cls.db = app, db
    #     cls.client = cls.app.test_client()
    #     cls.db.drop_all()
    #     cls.db.create_all()
    #     cls.load_couriers()
    #     #
    #     # EmailHandler.setup(config.EMAIL_API_KEY_DEV)
    #     # from app.api.consumer_v1 import bp as blueprint
    #     # cls.app.register_blueprint(blueprint, url_prefix = '/consumer/v1')

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

    def _post(self, path, data):
        return self.client.post(self.base_url + path, 
                    data=json.dumps(data), headers=self.headers)

    def _get(self, path, data={}):
        return self.client.get(self.base_url + path, data = json.dumps(data),
                    headers=self.headers)

    def _put(self, path, data):
        return self.client.put(self.base_url + path, 
                    data=json.dumps(data), headers=self.headers)

    def _delete(self, path, data = {}):
        return self.client.delete(self.base_url + path, 
                    headers=self.headers, data = json.dumps(data))



class CourierApiTestMixin:

    def test_account_login(self):
#        bad login
        rv = self.client.post(self.base_url + '/login', 
                    data=json.dumps(courier_pw_update_bad), headers=self.headers)
        eq_(rv.status_code, 403)

        rv = self.client.post(self.base_url + '/login', 
                data=json.dumps(courier_account_login), headers=self.headers)
        r = self.basic_checks(rv)
        assert r['userId']
        # self.api_key = r['apiKey']

    def test_pw_change(self):
        # try garbage first
        rv = self.client.post(self.base_url + '/login/password', 
                    data=json.dumps(account_login), headers=self.headers)
        eq_(rv.status_code, 403)
        # now pw is too short
        rv = self.client.post(self.base_url + '/login/password', 
                    data=json.dumps(courier_pw_update_bad), headers=self.headers)
        eq_(rv.status_code, 403)

        rv = self.client.post(self.base_url + '/login/password', 
                    data=json.dumps(courier_pw_update_ok), headers=self.headers)
        eq_(rv.status_code, 200)

    def test_account_get(self):
        rv = self._get('/account')
        r = self.basic_checks(rv)
        account = r.get('account')
        eq_(account.get('fullName'), courier_user.get('fullName'))
        assert r.get('correlationID') is not None

    def test_deliveries_get(self):
        tm_delivery =  {
                "articles": [{'trackingNumber': str(a.tracking_number)} for a in self.new_articles],
                "neighbourId":str(self.consumer.id),
                }
        rv = self._post('/deliveries', tm_delivery)
        rv = self.basic_checks(rv)
        db.session.add(self.consumer) 
        tm_delivery = {
                "articles": [{'trackingNumber': a} for a in ['3123', '24425446', '54t5ffgdfvd', '443r3w77yh']],
                "neighbourId":str(self.consumer.id),
                }
        rv = self._post('/deliveries', tm_delivery)
        rv = self.basic_checks(rv)

        rv = self._get('/deliveries', {})
        rv = self.basic_checks(rv)

        ttn = 'TRANSIT_TO_NEIGHBOUR'
        tm_delivery['deliveryState'] = ttn
        rv = self._put('/deliveries', tm_delivery)

        rv = self._get('/deliveries/state/' + ttn,  {})
        rv = self.basic_checks(rv)
        print rv


    def test_delivery_create(self):
        tm_delivery =  {
                "articles": [{'trackingNumber': str(a.tracking_number)} for a in self.new_articles],
                "neighbourId": str(self.consumer.id)
        }
        rv = self._post('/deliveries', tm_delivery)
        rv = self.basic_checks(rv)
        assert rv['deliveryID']

    def test_single_delivery_get(self):
        rv = self._get('/deliveries/' + str(self.tm_delivery.id), {})

        rv = self.basic_checks(rv)
        print '   --------->      RESULTS:', rv
        #eq_(rv['delivery']['neighbour']['id'], self.consumer_id)

    def test_single_delivery_update(self):
        # db.session.add(self.tm_delivery)    #wtf sqlalchemy ?

        rv = self._put('/deliveries/' + str(self.tm_delivery.id), 
            {"DeliveryState":"COURIER_ABORTED"})
        rv = self.basic_checks(rv)

    def test_delivery_delete(self):
        self.tm_delivery.state = DeliveryState.TRANSIT_TO_NEIGHBOUR.value
        db.session.add(self.tm_delivery)
        rv = self._delete('/deliveries/' + str(self.tm_delivery.id), {})
        rv = self.basic_checks(rv)
        print rv

        db.session.add(self.tm_delivery)
        rv = self._get('/deliveries/' + str(self.tm_delivery.id), {})
        eq_(rv.status_code, 404)


    def test_single_delivery_articles_get(self):
        rv = self._get('/deliveries/' + str(self.tm_delivery.id) + '/articles/', {})
        rv = self.basic_checks(rv)
        eq_(len(rv['parcels']), 4)

    def test_single_delivery_articles_post(self):
        rv = self._post('/deliveries/' + str(self.tm_delivery.id) + '/articles/', 
            {})   #bad request
        eq_(rv.status_code, 400)

        db.session.add(self.tm_delivery)    #wtf sqlalchemy ?

        rv = self._post('/deliveries/' + str(self.tm_delivery.id) + '/articles/',      
            {"article": {"trackingNumber": "a11"}})    # existing tracking
        eq_(rv.status_code, 200)
        rv = self._get("/articles/a11")

        db.session.add(self.tm_delivery)    #wtf sqlalchemy ?

        tracking_number = 'LV9006545301000600205'   #new tracking
        rv = self._post('/deliveries/' + str(self.tm_delivery.id) + '/articles/', 
            {"article": {"trackingNumber": tracking_number}})
        rv = self.basic_checks(rv)
        eq_(len(rv['parcels']), 6)


    def test_change_neighbour(self):

        rv = self._put('/deliveries/' + str(self.tm_delivery.id), 
            {"neighbourId": str(self.neighbour1.id)})

        eq_(rv.status_code, 200)
        
        db.session.add(self.tm_delivery)    #wtf sqlalchemy ?
        rv = self._get('/deliveries/' + str(self.tm_delivery.id))
        rv = self.basic_checks(rv)

    # def test_delivery_delete_recipient(self):
    #     rv = self._delete('/deliveries/' + str(self.tm_delivery.id) + 
    #             '/alternateRecipient')
    #     self.basic_checks(rv)

    def test_account_get(self):
        rv = self._get('/account', {})
        eq_(rv.status_code, 200)

    # def test_neighbours_get(self):
    #
    #     rv = self._get('/nearestNeighbours/1/0.1')
    #     rv = self.basic_checks(rv)
    #     eq_(len(rv['alternateRecipients']), 3)

    def test_articles_get(self):

        rv = self._get('/articles/a01')
        rv = self.basic_checks(rv)
        #todo

    def test_articles_delete(self):
        dv_id = str(self.tm_delivery.id)

        rv = self._get('/deliveries/' + dv_id + '/articles/', {})
        rv = self.basic_checks(rv)
        eq_(len(rv['parcels']), 4)

        rv = self._delete('/articles/a01')
        rv = self.basic_checks(rv)

        rv = self._get('/deliveries/' + dv_id + '/articles/', {})
        rv = self.basic_checks(rv)
        eq_(len(rv['parcels']), 3)

    def test_integration(self):
        # courier arrives, recipient not there
        # first, get nearest neighbours
        # rv = self._get('/nearestNeighbours/1bours/27.685994/85.317815', {})
        # rv = self.basic_checks(rv)
        # print "*****************************************************"
        # print rv

        # alt_r = rv['alternateRecipients'][0]
        # eq_(len(rv), 2)

        tm_delivery =  {
                "articles": [
                    {'trackingNumber': 'a12334'},
                    {'trackingNumber': 'b23445'},
                    {'trackingNumber': 'c65678'},
                    {'trackingNumber': 'd54509'},
                    ],
                "neighbourId": self.consumer_id
            }
        rv = self._post('/deliveries', tm_delivery)
        rv = self.basic_checks(rv)
        print "********************************************************"
        print rv
        tmd_id = rv['deliveryID']
        assert tmd_id

        rv = self._get('/deliveries/' + tmd_id, {})
        rv = self.basic_checks(rv)
        print rv
        # good, we've found and selected an alt recipient 
        # and created a new TMD en route to him

        rv = self._get('/deliveries/' + tmd_id, {})
        rv = self.basic_checks(rv)
        print "****>>>>>>>>>> TMD:", rv


    def test_logout(self):
        self.logout()
        # TODO: check access on/off once api has more calls implemented
 
    # login/logout useful for other tests
    def login(self):
        rv = self._post("/login", courier_account_login)
        r = self.basic_checks(rv)
        self.api_key = r['apiKey']

    def logout(self):
        rv = self.client.post(self.base_url + '/logout', data="{}", headers=self.headers)
        r = self.basic_checks(rv)




class CourierApiTest(ApiTest, CourierApiTestMixin):

    @classmethod
    def setUpClass(cls):
        super(CourierApiTest, cls).setUpClass()
        cls.app, cls.db = app, db
        cls.client = cls.app.test_client()
        cls.db.drop_all()
        cls.db.create_all()
        cls.load_couriers()
        #
        # EmailHandler.setup(config.EMAIL_API_KEY_DEV)
        # from app.api.consumer_v1 import bp as blueprint
        # cls.app.register_blueprint(blueprint, url_prefix = '/consumer/v1')

    def tearDown(self):
        # headers = self.headers
        db.session.query(Article).delete()
        db.session.query(Location).delete()
        db.session.query(TrustmileDelivery).delete()
        db.session.query(CourierUser).delete()
        db.session.query(ConsumerUser).delete()
        db.session.query(CouriersPleaseNotifications).delete()
        db.session.commit()

        # db.session.flush()

        self.__class__.db.session.close()

    def setUp(self):
        super(CourierApiTest, self).setUp()
        self.api_key = None
        self.base_url = '/courier/v1'
        self.content_type = 'application/json'
        self.environ_overrides = {}
        self.db.session.query(CourierUser).delete()
        self.db.session.commit()

        self.cuser = CourierUser.create(courier_user['username'],
            courier_user['password'], courier_user['fullName'], Courier.retrieve_courier('couriers-please'))

        self.db.session.commit()
        self.login()
        db.session.add(self.cuser)   # wtf but otherwise cuser has no id and everything fails

        self.addArticles()
        self.addTMDeliveries()
        self.makeNeighbours()

        db.session.commit()  #to survive the exceptions

    def addArticles(self):
        self.consumer = ConsumerUser.create('joe@consumer.com', 'joshua555')
        self.courier = CourierUser.create('joesmith', 'boundary', 'Joe Smith', Courier.retrieve_courier('couriers-please'))
        address_info = {
            "countryCode": "AU",
            "suburb": "Elizabeth Bay",
            "state": "NSW",
            "postcode": "2011",
            "addressLine1": "801/12 Ithaca Rd",
            "addressLine2": ""
        }
        address_obj = UserAddressSchema().load(address_info, partial=True).data
        self.consumer.address = address_obj
        db.session.flush() #otherwise no id on fresh objects
        self.consumer_id = str(self.consumer.id)
        # TODO: dmitry, these articles are
        self.new_articles = Article.new_articles(self.courier,
                                                 ["a01", "a02", "a03", "a04"])
        print self.new_articles[0]
        self.more_articles = Article.new_articles(self.courier,
                                                  ["a11", "a12", "a13", "a14"])
        db.session.flush() #otherwise no id on fresh objects

    def addTMDeliveries(self):
        self.tm_delivery = TrustmileDelivery.create(self.cuser, 
            self.new_articles)
        self.tm_delivery.neighbour = self.consumer

#        self.tm_delivery.location = Location(27.685994, 85.317815)

        db.session.flush() #otherwise no id on fresh objects
        print self.tm_delivery.to_json()
#        self.another_delivery = TrustmileDelivery.create(self.cuser, self.more_articles)
#        self.another_delivery.neighbour = self.consumer
        db.session.flush() #otherwise no id on fresh objects

    def makeNeighbours(self):
        self.neighbour1 = ConsumerUser.create('n1@consumer.com', 'joshua555')
        self.neighbour2 = ConsumerUser.create('n2@consumer.com', 'joshua555')

        self.neighbour1.trustmile_user = True
        self.neighbour2.trustmile_user = True

        address_info =  {
            "countryCode": "AU",
            "suburb": "Elizabeth Bay",
            "state": "NSW",
            "postcode": "2011",
            "addressLine1": "801/12 Ithaca Rd",
            "addressLine2": ""
        }
        address_obj = UserAddressSchema().load(address_info, partial=True).data
        logger.debug(u"User address object {0} of type {1}".format(address_obj, type(address_obj)))
        address_obj.location = Location(27.69, 85.32)
        self.neighbour1.user.user_address.append(address_obj)

        address_info =  {
            "countryCode": "AU",
            "suburb": "St Ives",
            "state": "NSW",
            "postcode": "2075",
            "addressLine1": "11 Athena Rd",
            "addressLine2": ""
        }

        address_obj = UserAddressSchema().load(address_info, partial=True).data
        address_obj.location = Location(27.67, 85.30)
        logger.debug(u"User address object {0} of type {1}".format(address_obj, type(address_obj)))
        self.neighbour2.user.user_address.append(address_obj)
        db.session.flush()



    # TODO: james  - Get better "prod" testing and this is part of it.
class RemoteCourierApiTest(ApiTest, CourierApiTestMixin):
    @classmethod
    def setUpClass(cls):
        import requests
        #super(RemoteConsumerApiTest, cls).setUpClass()
        cls.kwargs = config.FLASK_CLIENT_CONFIG
        cls.kwargs.get('content_type')
        cls.client = requests
        cls.base_url = "http://devapi.trustmile.com/courier/v1"
        cls.content_type = 'application/json'

    @classmethod
    def tearDownClass(cls):
        pass
        #super(RemoteConsumerApiTest, cls).tearDownClass()

    @property
    def     base_url(self):
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
        self.register_deets = account_login_deep
        print self.register_deets
        r = self.client.post('{0}/login'.format(self.base_url), data=json.dumps(account_login_deep), headers = self.headers)
        j = r.json()
        self.api_key = j['apiKey']

    def test_login(self):
        rv = self.client.post(self.base_url + '/login',
                             data=json.dumps(account_login_deep), headers=self.headers)


    def tearDown(self):
        rv = self.client.delete('{0}/account'.format(self.base_url), headers=self.headers)
        # self.__class__.db.session.close()
        # super(RemoteConsumerApiTest, self).tearDown()

    def test_pass(self):
        assert True

