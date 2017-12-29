# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class Allneighbourlocations(Resource):

    def get(self):

        return {}, 200, None