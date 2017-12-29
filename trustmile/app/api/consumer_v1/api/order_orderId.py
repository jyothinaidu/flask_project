# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class OrderOrderid(Resource):

    def get(self, orderId):

        return {}, 200, None