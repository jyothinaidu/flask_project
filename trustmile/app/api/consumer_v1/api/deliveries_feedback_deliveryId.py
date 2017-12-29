# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class DeliveriesFeedbackDeliveryid(Resource):

    def post(self, deliveryId):
        print g.json

        return {}, 200, None