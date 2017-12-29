# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class LoginPassword(Resource):

    def post(self):
        print g.json

        return {}, 200, None