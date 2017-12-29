from app.ops.consumer_operations import cons_ops, ConsumerOperationsFactory
from app.ops.courier_operations import courier_ops, CourierOperationsFactory
from app.ops.admin_operations import admin_ops, AdminOperationsFactory
from app.ops.retailer_operations import retailer_ops, RetailerOperationsFactory
from app.ops.base import BaseOperation, ApiResponse, admin_security

__author__ = 'james'
from flask import request
from werkzeug.datastructures import MultiDict
import uuid
import logging

logger = logging.getLogger()


def consumer_request_handle(func):
    def wrapper(*args, **kwargs):
        endpoint = request.endpoint.partition('.')[-1]
        # scope
        # if (endpoint, request.method) in scopes and not set(
        #         scopes[(endpoint, request.method)]).issubset(set(security.scopes)):
        #     ApiResponse.create_response(403, 'Method not supported', uuid.uuid4())
        # data
        method = request.method
        opdict = cons_ops.get((endpoint, method), {'location': 'json', 'operation': BaseOperation})

        location = opdict.get('location', None)
        if not location:
            ApiResponse.create_response(500, 'Unknown operation', uuid.uuid4())

        value = getattr(request, location, MultiDict())
        headers = getattr(request, 'headers', MultiDict())
        operation = ConsumerOperationsFactory.factory(endpoint, method)
        query_string = getattr(request, 'values', MultiDict())
        result = operation.perform(value, headers=headers, query_string=query_string, **kwargs)
        return result

    return wrapper

def courier_request_handle(func):
    def wrapper(*args, **kwargs):
        endpoint = request.endpoint.partition('.')[-1]
        # scope
        # if (endpoint, request.method) in scopes and not set(
        #         scopes[(endpoint, request.method)]).issubset(set(security.scopes)):
        #     ApiResponse.create_response(403, 'Method not supported', uuid.uuid4())
        # data
        method = request.method
        opdict = courier_ops.get((endpoint, method), {'location': 'json', 'operation': BaseOperation})

        location = opdict.get('location', None)
        if not location:
            logger.error(u'Unknown operation in courier request handler, params: {0}'.format(locals()))
            ApiResponse.create_response(500, 'Unknown operation', uuid.uuid4())

        value = getattr(request, location, MultiDict())
        headers = getattr(request, 'headers', MultiDict())
        operation = CourierOperationsFactory.factory(endpoint, method)

#        func(*args, **kwargs)
        result = operation.perform(value, headers=headers, **kwargs)
        return result

    return wrapper


def admin_request_handler(func):
    def wrapper(*args, **kwargs):
        endpoint = request.endpoint.partition('.')[-1]
        # scope
        # if (endpoint, request.method) in scopes and not set(
        #         scopes[(endpoint, request.method)]).issubset(set(security.scopes)):
        #     ApiResponse.create_response(403, 'Method not supported', uuid.uuid4())
        # data
        method = request.method
        opdict = admin_ops.get((endpoint, method), {'location': 'json', 'operation': BaseOperation})

        location = opdict.get('location', None)
        if not location:
            ApiResponse.create_response(500, 'Unknown operation', uuid.uuid4())

        value = getattr(request, location, MultiDict())
        headers = getattr(request, 'headers', MultiDict())
        operation = AdminOperationsFactory.factory(endpoint, method)

        ## security
        admin_security( headers, **kwargs)
        result = operation.perform(value, headers=headers, **kwargs)
        return result

    return wrapper

def retailer_request_handler(func):
    def wrapper(*args, **kwargs):
        endpoint = request.endpoint.partition('.')[-1]
        # scope
        # if (endpoint, request.method) in scopes and not set(
        #         scopes[(endpoint, request.method)]).issubset(set(security.scopes)):
        #     ApiResponse.create_response(403, 'Method not supported', uuid.uuid4())
        # data
        method = request.method
        opdict = retailer_ops.get((endpoint, method))
        if not opdict:
            ApiResponse.create_response(500, 'Incorrect endpoint configuration', uuid.uuid4())

        location = opdict.get('location', None)
        if not location:
            ApiResponse.create_response(500, 'Unknown operation', uuid.uuid4())

        value = getattr(request, location, MultiDict())
        headers = getattr(request, 'headers', MultiDict())
        operation = RetailerOperationsFactory.factory(endpoint, method)
        query_string = getattr(request, 'values', MultiDict())

        result = operation.perform(value, headers=headers, query_string=query_string, **kwargs)
        return result

    return wrapper
