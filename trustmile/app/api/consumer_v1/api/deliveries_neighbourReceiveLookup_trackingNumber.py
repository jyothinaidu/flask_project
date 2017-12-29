# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class DeliveriesNeighbourreceivelookupTrackingnumber(Resource):

    def get(self, trackingNumber):

        return {}, 200, None