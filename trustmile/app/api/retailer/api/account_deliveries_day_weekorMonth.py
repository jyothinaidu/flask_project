# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class AccountDeliveriesDayWeekormonth(Resource):

    def get(self, weekorMonth):

        return {}, 200, None