# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class NearestneighboursLatitudeLongitude(Resource):

    def get(self, latitude, longitude):

        return {}, 200, None