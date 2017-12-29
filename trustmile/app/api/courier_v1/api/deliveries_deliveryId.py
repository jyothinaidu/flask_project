# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class DeliveriesDeliveryid(Resource):

    def get(self, deliveryId):

        return {}, 200, None

    def put(self, deliveryId):
        print g.json

        return {}, 200, None

    def delete(self, deliveryId):

        return {}, 200, None