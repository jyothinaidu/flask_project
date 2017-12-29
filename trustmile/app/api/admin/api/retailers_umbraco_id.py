# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class RetailersUmbracoId(Resource):

    def get(self, umbraco_id):

        return {}, 200, None

    def put(self, umbraco_id):
        print g.json

        return {}, 200, None