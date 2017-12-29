# -*- coding: utf-8 -*-

# TODO: datetime support

###
### DO NOT CHANGE THIS FILE
### 
### The code is auto generated, your change will be overwritten by 
### code generating.
###


DefinitionsEmailextractor = {'type': 'object', 'properties': {'start': {'type': 'string'}, 'repeat': {'type': 'boolean'}, 'end': {'type': 'string'}, 'capture': {'type': 'string'}, 'item': {'type': 'string'}}}
DefinitionsPromotionimage = {'type': 'object', 'properties': {'imageFileData': {'type': 'string'}, 'name': {'type': 'string'}}}
DefinitionsNeighbourlocation = {'type': 'object', 'properties': {'lat': {'type': 'string'}, 'lng': {'type': 'string'}, 'name': {'type': 'string'}}}
DefinitionsSealinfo = {'type': 'object', 'properties': {'seal_enabled': {'type': 'boolean'}, 'website_name': {'type': 'string'}, 'website_url': {'type': 'string'}}}
DefinitionsNeighboursignup = {'type': 'object', 'properties': {'emailAddress': {'type': 'string'}, 'hasIPhone': {'type': 'boolean'}, 'name': {'type': 'string'}, 'workStatus': {'type': 'string'}, 'over18': {'type': 'boolean'}, 'suburb': {'type': 'string'}, 'state': {'type': 'string'}, 'phoneNumber': {'type': 'string'}, 'postcode': {'type': 'string'}, 'addressLine1': {'type': 'string'}, 'addressLine2': {'type': 'string'}, 'id': {'type': 'string'}}}
DefinitionsCouriermapping = {'type': 'object', 'properties': {'sourceText': {'type': 'string'}, 'courierName': {'type': 'string'}}}
Definitions401 = {'required': ['correlationID'], 'type': 'object', 'description': 'Not authorized.  Either the authorization key was missing or not present', 'properties': {'reason': {'type': 'string'}, 'correlationID': {'type': 'string'}}}
DefinitionsRetailersealaudit = {'type': 'object', 'description': 'Gets and sets seal audit information', 'properties': {'answer': {'type': 'boolean'}, 'additional_information_approved': {'type': 'boolean'}, 'question_text': {'type': 'string'}, 'question_code': {'type': 'string'}, 'additional_information': {'type': 'string'}}}
DefinitionsNeighbourlocations = {'type': 'object', 'properties': {'userLocations': {'items': DefinitionsNeighbourlocation, 'type': 'array'}}}
DefinitionsCreatepromotion = {'type': 'object', 'properties': {'retailerId': {'type': 'string', 'format': 'uuid'}, 'promotionImages': {'items': DefinitionsPromotionimage, 'type': 'array'}, 'promotionDestinationUrl': {'type': 'string'}}}
DefinitionsEmailparser = {'type': 'object', 'properties': {'start': DefinitionsEmailextractor, 'repeat': {'type': 'boolean'}, 'stop': DefinitionsEmailextractor, 'extractors': {'items': DefinitionsEmailextractor, 'type': 'array'}}}
DefinitionsEmailintegrationconfiguration = {'type': 'object', 'properties': {'from_email_addresses': {'items': {'type': 'string'}, 'type': 'array'}, 'parsing_set': {'items': DefinitionsEmailparser, 'type': 'array'}}}
DefinitionsRetailer = {'type': 'object', 'properties': {'umbraco_id': {'type': 'string'}, 'website_name': {'type': 'string'}, 'courier_mappings': {'items': DefinitionsCouriermapping, 'type': 'array'}, 'email_integration_configuration': DefinitionsEmailintegrationconfiguration, 'id': {'type': 'string'}, 'website_url': {'type': 'string'}}}

validators = {
    ('retailers', 'POST'): {'json': DefinitionsRetailer},
    ('promotion', 'POST'): {'json': DefinitionsCreatepromotion},
    ('neighbourSignup', 'POST'): {'json': DefinitionsNeighboursignup},
    ('retailers_umbraco_id', 'PUT'): {'json': DefinitionsRetailer},
}

filters = {
    ('seal_seal_id_seal_audit', 'GET'): {200: {'headers': None, 'schema': {'properties': {'seal_enabled': {'type': 'boolean'}, 'seal_audits': {'items': DefinitionsRetailersealaudit, 'type': 'array'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('retailers', 'POST'): {200: {'headers': None, 'schema': {'properties': {'retailer': DefinitionsRetailer, 'correlationID': {'type': 'string'}}}}, 422: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('retailers', 'GET'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}, 'retailers': {'items': DefinitionsRetailer, 'type': 'array'}}}}, 401: {'headers': None, 'schema': Definitions401}},
    ('allNeighbourLocations', 'GET'): {200: {'headers': None, 'schema': DefinitionsNeighbourlocations}, 401: {'headers': None, 'schema': Definitions401}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('seal_seal_id', 'GET'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}, 'seal_info': DefinitionsSealinfo}}}, 401: {'headers': None, 'schema': Definitions401}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('promotion', 'POST'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}, 'promotionId': {'type': 'string', 'format': 'uuid'}}}}, 401: {'headers': None, 'schema': Definitions401}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('neighbourSignup', 'POST'): {200: {'headers': None, 'schema': {'properties': {'retailer': DefinitionsNeighboursignup, 'correlationID': {'type': 'string'}}}}},
    ('neighbourSignup', 'GET'): {200: {'headers': None, 'schema': {'properties': {'neighbourSignups': {'items': DefinitionsNeighboursignup, 'type': 'array'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}},
    ('retailers_umbraco_id', 'PUT'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 400: {'headers': None, 'schema': None}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('retailers_umbraco_id', 'GET'): {200: {'headers': None, 'schema': {'properties': {'retailer': DefinitionsRetailer, 'correlationID': {'type': 'string'}}}}, 404: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
}

scopes = {
    ('seal_seal_id_seal_audit', 'GET'): [],
    ('retailers', 'GET'): [],
    ('allNeighbourLocations', 'GET'): [],
    ('seal_seal_id', 'GET'): [],
    ('promotion', 'POST'): [],
    ('neighbourSignup', 'GET'): [],
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

