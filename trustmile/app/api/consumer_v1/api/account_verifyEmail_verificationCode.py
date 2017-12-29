# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class AccountVerifyemailVerificationcode(Resource):

    def get(self, verificationCode):

        return {}, 200, None