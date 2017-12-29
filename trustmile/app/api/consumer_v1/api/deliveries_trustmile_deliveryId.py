# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class DeliveriesTrustmileDeliveryid(Resource):

    def get(self, deliveryId):

        return {}, 200, None