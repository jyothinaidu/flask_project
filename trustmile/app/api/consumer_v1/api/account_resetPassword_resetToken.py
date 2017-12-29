# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class AccountResetpasswordResettoken(Resource):

    def get(self, resetToken):

        return {}, 200, None

    def post(self, resetToken):
        print g.json

        return {}, 200, None