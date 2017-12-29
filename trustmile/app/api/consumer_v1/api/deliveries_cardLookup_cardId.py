# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class DeliveriesCardlookupCardid(Resource):

    def get(self, cardId):

        return {'neighbourAddress': {}, 'neighbourName': 'something'}, 200, None