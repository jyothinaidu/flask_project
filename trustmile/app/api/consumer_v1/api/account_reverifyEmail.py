# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class AccountReverifyemail(Resource):

    def put(self):

        return {}, 200, None