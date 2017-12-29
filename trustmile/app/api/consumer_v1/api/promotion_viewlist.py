# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class PromotionViewlist(Resource):

    def get(self):
        print g.json

        
        pass