# -*- coding: utf-8 -*-
from flask import Blueprint, request
import flask_restful as restful

from .routes import routes
from .validators import security


@security.scopes_loader
def current_scopes():
    return []

def add_access_control_header(response):
    response.headers.add( 'Access-Control-Allow-Origin', '*')
    response.headers.add( 'Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE')
    requestHeaders = request.headers.get( 'Access-Control-Request-Headers')
    if requestHeaders:
        response.headers.add( 'Access-Control-Allow-Headers', requestHeaders)
    return response

bp = Blueprint('consumer_v1', __name__)
bp.after_app_request( add_access_control_header)


api = restful.Api(bp, catch_all_404s=True)

for route in routes:
    api.add_resource(route.pop('resource'), *route.pop('urls'), **route)