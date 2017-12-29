#example remote testing of Flask app

class RemoteApiTest(AppTest, ApiTestMixin):
    @classmethod
    def setUpClass(cls):
        super(RemoteApiTest, cls).setUpClass()
        cls.kwargs = config.FLASK_CLIENT_CONFIG
        cls.base_url = cls.kwargs.get('base_url')
        cls.content_type = cls.kwargs.get('content_type')
        cls.client = requests
        cls.db = db
        cls.db.create_all()

    @classmethod
    def tearDownClass(cls):
        super(RemoteApiTest, cls).tearDownClass()
        cls.db.session.remove()
        cls.db.drop_all()
        #cls.db.get_engine(cls.app).dispose()

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
        super(RemoteApiTest, self).setUp()
        self.api_key = None

        r = self.client.post('{0}/account/register'.format(self.base_url), data=json.dumps(account_register),
                             headers=self.headers)
        j = r.json()
        self.api_key = j['apiKey']

    def tearDown(self):
        rv = self.client.delete('{0}/account'.format(self.base_url), headers=self.headers)
        # self.__class__.db.session.close()
        super(RemoteApiTest, self).tearDown()

    def test_pass(self):
        assert True
