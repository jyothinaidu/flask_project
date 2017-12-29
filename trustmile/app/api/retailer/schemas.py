# -*- coding: utf-8 -*-

# TODO: datetime support

###
### DO NOT CHANGE THIS FILE
### 
### The code is auto generated, your change will be overwritten by 
### code generating.
###


DefinitionsRetailercourier = {'type': 'object', 'description': 'Total Number of deliveries from the retailer grouped by Courier for week or month', 'properties': {'logo': {'type': 'string'}, 'not_delivered': {'type': 'string'}, 'courier_company': {'type': 'string'}, 'delivered': {'type': 'string'}}}
DefinitionsDeliverydays = {'type': 'object', 'description': 'Delivery of consignments for week or month days', 'properties': {'deliverydate': {'type': 'string', 'format': 'datetime'}, 'delivered': {'type': 'string'}, 'not_delivered': {'type': 'string'}}}
DefinitionsEmailextractor = {'type': 'object', 'properties': {'start': {'type': 'string'}, 'repeat': {'type': 'boolean'}, 'end': {'type': 'string'}, 'capture': {'type': 'string'}, 'item': {'type': 'string'}}}
DefinitionsPasswordreset = {'required': ['newPassword'], 'type': 'object', 'description': 'Set the users password', 'properties': {'newPassword': {'type': 'string'}}}
DefinitionsAccountforgotpassword = {'type': 'object', 'description': 'Forgotten password reset request', 'properties': {'emailAddress': {'type': 'string', 'description': 'The emailAddress to login with'}, 'resetToken': {'type': 'string', 'description': 'The token provided on reset.'}}}
DefinitionsPasswordupdate = {'required': ['oldPassword', 'newPassword'], 'type': 'object', 'description': 'Change the users password', 'properties': {'newPassword': {'type': 'string'}, 'oldPassword': {'type': 'string'}}}
DefinitionsRetailerattributeupdate = {'additionalProperties': {'type': 'string'}, 'type': 'object', 'description': 'Retailer Attributes (dictonary/map)'}
DefinitionsRetailerlogin = {'type': 'object', 'description': 'Required data for user login', 'properties': {'password': {'type': 'string', 'description': 'The password associated with the username'}, 'emailAddress': {'type': 'string', 'description': 'The emailAddress to login with'}}}
DefinitionsRetailerregister = {'type': 'object', 'properties': {'website_name': {'type': 'string'}, 'contact_phoneNumber': {'type': 'string'}, 'contact_emailAddress': {'type': 'string'}, 'contact_lastname': {'type': 'string'}, 'contact_firstname': {'type': 'string'}, 'contact_password': {'type': 'string'}, 'website_url': {'type': 'string'}}}
DefinitionsRetailerupdate = {'type': 'object', 'description': 'Retailer account fields that can be updated', 'properties': {'website_name': {'type': 'string'}, 'contact_emailaddress': {'type': 'string'}, 'contact_lastname': {'type': 'string'}, 'contact_firstname': {'type': 'string'}, 'contact_phone': {'type': 'string'}, 'website_url': {'type': 'string'}}}
DefinitionsAdddelivery = {'required': ['courierSlug', 'trackingNumber', 'description', 'purchasedFrom', 'emailAddress'], 'type': 'object', 'description': "The tracking number and courier slug for a given parcel required to be added to the user's account. Retailer Name is optional", 'properties': {'trackingNumber': {'type': 'string'}, 'courierSlug': {'type': 'string'}, 'emailAddress': {'type': 'string'}, 'purchasedFrom': {'type': 'string'}, 'description': {'type': 'string'}}}
DefinitionsCouriermapping = {'type': 'object', 'properties': {'sourceText': {'type': 'string'}, 'courierName': {'type': 'string'}}}
Definitions401 = {'required': ['correlationID'], 'type': 'object', 'description': 'Not authorized.  Either the authorization key was missing or not present', 'properties': {'reason': {'type': 'string'}, 'correlationID': {'type': 'string'}}}
DefinitionsRetailersealaudit = {'type': 'object', 'description': 'Gets and sets seal audit information', 'properties': {'answer': {'type': 'boolean'}, 'question_text': {'type': 'string'}, 'question_code': {'type': 'string'}, 'additional_information': {'type': 'string'}}}
DefinitionsRetailerobject = {'type': 'object', 'description': 'describes a retailer', 'properties': {'retailer_attributes': {'additionalProperties': {'type': 'string'}, 'type': 'object'}, 'contact_phoneNumber': {'type': 'string'}, 'contact_firstName': {'type': 'string'}, 'seal_id': {'type': 'string'}, 'website_name': {'type': 'string'}, 'contact_emailAddress': {'type': 'string'}, 'seal_enabled': {'type': 'string'}, 'contact_lastName': {'type': 'string'}, 'id': {'type': 'string'}, 'website_url': {'type': 'string'}}}
DefinitionsEmailparser = {'type': 'object', 'properties': {'extractors': {'items': DefinitionsEmailextractor, 'type': 'array'}, 'repeat': {'type': 'boolean'}, 'position_extractor': DefinitionsEmailextractor}}
DefinitionsRetailersealauditarray = {'items': DefinitionsRetailersealaudit, 'type': 'array', 'description': 'array of RetailerSealAudit'}
DefinitionsCouriermappingarray = {'items': DefinitionsCouriermapping, 'type': 'array'}
DefinitionsEmailintegrationconfiguration = {'type': 'object', 'properties': {'from_email_addresses': {'items': {'type': 'string'}, 'type': 'array'}, 'parsing_set': {'items': DefinitionsEmailparser, 'type': 'array'}}}

validators = {
    ('account_register', 'POST'): {'json': DefinitionsRetailerregister},
    ('account_login', 'POST'): {'json': DefinitionsRetailerlogin},
    ('account_seal_audit', 'POST'): {'json': DefinitionsRetailersealauditarray},
    ('account_password', 'POST'): {'json': DefinitionsPasswordupdate},
    ('account_courier_mapping', 'POST'): {'json': DefinitionsCouriermappingarray},
    ('account_forgotPassword', 'POST'): {'json': DefinitionsAccountforgotpassword},
    ('account', 'POST'): {'json': DefinitionsRetailerupdate},
    ('account_deliveries_retailerintegration', 'POST'): {'json': DefinitionsAdddelivery},
    ('account_resetPassword_resetToken', 'POST'): {'json': DefinitionsPasswordreset},
    ('account_attributes', 'POST'): {'json': DefinitionsRetailerattributeupdate},
}

filters = {
    ('account_deliveries_day_weekorMonth', 'GET'): {200: {'headers': None, 'schema': {'properties': {'deliverydays': {'items': DefinitionsDeliverydays, 'type': 'array'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('account_register', 'POST'): {200: {'headers': None, 'schema': {'properties': {'apiKey': {'type': 'string', 'format': 'uuid'}, 'correlationID': {'type': 'string'}}}}, 409: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 422: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('account_login', 'POST'): {200: {'headers': None, 'schema': {'properties': {'apiKey': {'type': 'string', 'format': 'uuid'}, 'correlationID': {'type': 'string'}}}}, 403: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('account_seal_audit', 'POST'): {200: {'headers': None, 'schema': {'properties': {'emailAddress': {'type': 'string'}, 'correlationID': {'type': 'string'}}}}},
    ('account_seal_audit', 'GET'): {200: {'headers': None, 'schema': {'properties': {'seal_audits': {'items': DefinitionsRetailersealaudit, 'type': 'array'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}},
    ('account_password', 'POST'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}, 403: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 422: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('account_courier_mapping', 'POST'): {200: {'headers': None, 'schema': {'properties': {'emailAddress': {'type': 'string'}, 'correlationID': {'type': 'string'}}}}},
    ('account_courier_mapping', 'GET'): {200: {'headers': None, 'schema': {'properties': {'courier_mappings': DefinitionsCouriermappingarray, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}},
    ('account_forgotPassword', 'POST'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('account', 'POST'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}, 422: {'headers': None, 'schema': {'properties': {'message': {'type': 'string'}, 'correlationID': {'type': 'string'}}}}},
    ('account', 'GET'): {200: {'headers': None, 'schema': {'properties': {'retailer': DefinitionsRetailerobject, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}},
    ('account_deliveries_retailerintegration', 'POST'): {200: {'headers': None, 'schema': {'properties': {'emailAddress': {'type': 'string'}, 'correlationID': {'type': 'string'}}}}},
    ('account_deliveries_courier_weekorMonth', 'GET'): {200: {'headers': None, 'schema': {'properties': {'retailer': {'items': DefinitionsRetailercourier, 'type': 'array'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('account_resetPassword_resetToken', 'POST'): {200: {'headers': None, 'schema': {'properties': {'emailAddress': {'type': 'string'}, 'correlationID': {'type': 'string'}}}}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 422: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('account_resetPassword_resetToken', 'GET'): {200: {'headers': None, 'schema': {'properties': {'emailAddress': {'type': 'string'}, 'correlationID': {'type': 'string'}}}}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('ping', 'GET'): {200: {'headers': None, 'schema': None}, 401: {'headers': None, 'schema': Definitions401}},
    ('account_attributes', 'POST'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}, 403: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 422: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
}

scopes = {
    ('account_deliveries_day_weekorMonth', 'GET'): [],
    ('account_password', 'POST'): [],
    ('account', 'POST'): [],
    ('account', 'GET'): [],
    ('account_deliveries_retailerintegration', 'POST'): [],
    ('account_attributes', 'POST'): [],
}


class Security(object):

    def __init__(self):
        super(Security, self).__init__()
        self._loader = lambda: []

    @property
    def scopes(self):
        return self._loader()

    def scopes_loader(self, func):
        self._loader = func
        return func

security = Security()


def merge_default(schema, value):
    # TODO: more types support
    type_defaults = {
        'integer': 9573,
        'string': 'something',
        'object': {},
        'array': [],
        'boolean': False
    }

    return normalize(schema, value, type_defaults)[0]


def normalize(schema, data, required_defaults=None):

    if required_defaults is None:
        required_defaults = {}
    errors = []

    class DataWrapper(object):

        def __init__(self, data):
            super(DataWrapper, self).__init__()
            self.data = data

        def get(self, key, default=None):
            if isinstance(self.data, dict):
                return self.data.get(key, default)
            if hasattr(self.data, key):
                return getattr(self.data, key)
            else:
                return default

        def has(self, key):
            if isinstance(self.data, dict):
                return key in self.data
            return hasattr(self.data, key)

        def keys(self):
            if isinstance(self.data, dict):
                return self.data.keys()
            return vars(self.data).keys()

    def _normalize_dict(schema, data):
        result = {}
        if not isinstance(data, DataWrapper):
            data = DataWrapper(data)

        for key, _schema in schema.get('properties', {}).iteritems():
            # set default
            type_ = _schema.get('type', 'object')
            if ('default' not in _schema
                    and key in schema.get('required', [])
                    and type_ in required_defaults):
                _schema['default'] = required_defaults[type_]

            # get value
            if data.has(key):
                result[key] = _normalize(_schema, data.get(key))
            elif 'default' in _schema:
                result[key] = _schema['default']
            elif key in schema.get('required', []):
                errors.append(dict(name='property_missing',
                                   message='`%s` is required' % key))

        for _schema in schema.get('allOf', []):
            rs_component = _normalize(_schema, data)
            rs_component.update(result)
            result = rs_component

        additional_properties_schema = schema.get('additionalProperties', False)
        if additional_properties_schema:
            aproperties_set = set(data.keys()) - set(result.keys())
            for pro in aproperties_set:
                result[pro] = _normalize(additional_properties_schema, data.get(pro))

        return result

    def _normalize_list(schema, data):
        result = []
        if hasattr(data, '__iter__') and not isinstance(data, dict):
            for item in data:
                result.append(_normalize(schema.get('items'), item))
        elif 'default' in schema:
            result = schema['default']
        return result

    def _normalize_default(schema, data):
        if data is None:
            return schema.get('default')
        else:
            return data

    def _normalize(schema, data):
        if not schema:
            return None
        funcs = {
            'object': _normalize_dict,
            'array': _normalize_list,
            'default': _normalize_default,
        }
        type_ = schema.get('type', 'object')
        if not type_ in funcs:
            type_ = 'default'

        return funcs[type_](schema, data)

    return _normalize(schema, data), errors

