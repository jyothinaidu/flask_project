# -*- coding: utf-8 -*-
import flask_restful as restful

from ..validators import request_validate, response_filter
from app.ops import requesthandler

class Resource(restful.Resource):
    method_decorators = [request_validate, requesthandler.admin_request_handler, response_filter]