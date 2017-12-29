# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class AnonymousTrackingCourierslugTrackingnumber(Resource):

    def get(self, courierSlug, trackingNumber):

        return {}, 200, None