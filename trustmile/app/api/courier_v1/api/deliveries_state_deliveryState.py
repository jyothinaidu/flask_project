# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class DeliveriesStateDeliverystate(Resource):

    def get(self, deliveryState):

        return {}, 200, None