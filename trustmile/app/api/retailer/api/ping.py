# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class Ping(Resource):

    def get(self):

        return None, 200, None