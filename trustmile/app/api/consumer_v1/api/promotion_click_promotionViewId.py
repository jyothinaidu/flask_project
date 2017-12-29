# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class PromotionClickPromotionviewid(Resource):

    def get(self, promotionViewId):
        print g.json

        
        pass