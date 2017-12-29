# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class ArticlesTrackingnumber(Resource):

    def get(self, trackingNumber):

        return {}, 200, None

    def delete(self, trackingNumber):

        return {}, 200, None