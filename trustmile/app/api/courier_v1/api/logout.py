# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class Logout(Resource):

    def post(self):

        return {}, 200, None