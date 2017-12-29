__author__ = 'james'
from werkzeug.test import Client, EnvironBuilder
from werkzeug.testapp import test_app
from werkzeug.wrappers import BaseResponse
import config
from werkzeug.wrappers import BaseRequest

env = EnvironBuilder(**config.FLASK_CLIENT_ENVIRON)

req = BaseRequest(env)


c = Client(test_app, BaseResponse)
resp = c.get('/')
resp.status_code