# -*- coding: utf-8 -*-
from flask import request, g

from . import Resource
from .. import schemas


class SealSealIdSealAudit(Resource):

    def get(self, seal_id):

        return {}, 200, None