# -*- coding: utf-8 -*-

# TODO: datetime support

###
### DO NOT CHANGE THIS FILE
### 
### The code is auto generated, your change will be overwritten by 
### code generating.
###


DefinitionsFeedbackmessage = {'description': 'the content of a feedback post', 'properties': {'consumerName': {'type': 'string'}, 'feedbackMessage': {'type': 'string'}, 'consumerEmail': {'type': 'string'}}}
DefinitionsConversation = {'description': 'represents a single conversation.  A conversation may or may not be tied to a delivery.  It is also possible to have a conversation that has not yet started - the messages tab will show a list of conversation AND neighbour pickups that the user can create a conversation againt, in this situation the conversationId will be null', 'properties': {'deliveriestate': {'type': 'string', 'description': "the collection state of the pickup (delivery).  one of 'ready to pickup', 'collected awaiting feedback', 'collected, closed'"}, 'deliveryId': {'type': 'string', 'description': 'If this message relates to a , the ID of the delivery.  Null indicates a  system message', 'format': 'uuid'}, 'unreadMessage': {'type': 'integer', 'description': 'the number of messagesd in the conversation the user has not read'}, 'conversationId': {'type': 'string', 'description': 'The conversationId of the conversation.  This value can be null in cases where the user has the ability to start a conversation but no conversation has been started.  A conversationId can exist with 0 messages in the conversation.', 'format': 'uuid'}, 'neighbourAddress': {'type': 'string', 'description': 'the pickup address of the neighbour'}, 'systemMessageTitle': {'description': 'when this is a system message, this is the title to display on the conversations screen'}, 'neighbourName': {'type': 'string', 'description': 'the name of the neighbour'}, 'totalMessages': {'type': 'integer', 'description': 'the total number of messages in the conversation'}}}
DefinitionsInstallationinformation = {'description': 'A collection of information that describes an instance of the application and what device it is running on.', 'properties': {'OSType': {'type': 'string', 'description': 'Android or Apple or other'}, 'OSMinorVersion': {'type': 'string', 'description': 'the minor version of the mobile OS'}, 'DeviceIdentifier': {'type': 'string', 'description': 'the device ID of the mobile device'}, 'ApplicationVersion': {'type': 'string', 'description': 'the version of the application installed, such as 1  or 1.1 or 1.1.1'}, 'OSMajorVersion': {'type': 'string', 'description': 'The major version of the mobile OS'}}}
DefinitionsPasswordupdate = {'required': ['oldPassword', 'newPassword'], 'type': 'object', 'description': 'Change the users password', 'properties': {'newPassword': {'type': 'string'}, 'oldPassword': {'type': 'string'}}}
DefinitionsPasswordreset = {'required': ['newPassword'], 'type': 'object', 'description': 'Set the users password', 'properties': {'newPassword': {'type': 'string'}}}
DefinitionsOrderinfo = {'type': 'object', 'description': 'Details pertaining to a retailer order', 'properties': {'orderId': {'type': 'string'}, 'retailerName': {'type': 'string'}, 'description': {'type': 'string'}, 'retailerHelpUrl': {'type': 'string'}, 'retailerPhone': {'type': 'string'}, 'orderEmailUrl': {'type': 'string'}, 'retailerImageUrl': {'type': 'string'}, 'dispatchEmailUrl': {'type': 'string'}}}
DefinitionsDeliveryfeedback = {'required': ['rating'], 'type': 'object', 'description': 'Delivery Feedback on delivered item', 'properties': {'comment': {'type': 'string'}, 'rating': {'enum': [1, 2, 3, 4, 5], 'type': 'number', 'format': 'integer'}, 'complaint': {'items': {'type': 'string'}, 'type': 'array'}, 'netPromoterScore': {'enum': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 'type': 'number', 'format': 'integer'}, 'netPromoterScoreComment': {'type': 'string'}}}
DefinitionsPromotionclick = {'properties': {'promotionId': {'type': 'string'}}}
Definitions401 = {'required': ['correlationID'], 'type': 'object', 'description': 'Not authorized.  Either the authorization key was missing or not present', 'properties': {'reason': {'type': 'string'}, 'correlationID': {'type': 'string', 'format': 'uuid'}}}
DefinitionsDelegatedelivery = {'properties': {'email': {'type': 'string'}, 'deliveryId': {'type': 'string', 'format': 'uuid'}}}
DefinitionsRecipientinfo = {'type': 'object', 'properties': {'emailAddress': {'type': 'string', 'format': 'email'}, 'fullName': {'type': 'string'}, 'phoneNumber': {'type': 'string'}}}
DefinitionsAccountforgotpassword = {'description': 'Forgotten password reset request', 'properties': {'emailAddress': {'type': 'string', 'description': 'The emailAddress to login with'}, 'resetToken': {'type': 'string', 'description': 'The token provided on reset.'}}}
DefinitionsAlternaterecipient = {'required': ['consumerId'], 'properties': {'consumerId': {'type': 'string', 'description': 'the Id of the alternate recipient'}, 'fullName': {'type': 'string'}, 'phoneNumber': {'type': 'string'}, 'email': {'type': 'string'}, 'physicalAddress': {'properties': {'streetType': {'type': 'string'}, 'longitude': {'type': 'number', 'description': 'the longitude of the recipient', 'format': 'double'}, 'suburb': {'type': 'string'}, 'unitNumber': {'type': 'string'}, 'postcode': {'pattern': '^[0-9]{4}$', 'type': 'string'}, 'streetNumber': {'type': 'string'}, 'latitude': {'type': 'number', 'description': 'the latitude of the recipient', 'format': 'double'}, 'streetName': {'type': 'string'}}}}}
DefinitionsNeighbourreceive = {'type': 'object', 'description': 'List of articles for the neighbour receive post operation', 'properties': {'articles': {'items': {'type': 'string'}, 'type': 'array'}}}
DefinitionsRetailer = {'properties': {'contactNumber': {'type': 'string'}, 'name': {'type': 'string'}}}
DefinitionsApplicationsettings = {'description': 'a set of properties used to enable & disable features on the client', 'properties': {'promptForNeighbourSignup': {'type': 'boolean', 'description': 'yes/no to show a neighbour signup prompt on My Deliveries'}, 'trustMileFeedback': {'type': 'boolean', 'description': 'show / hide capture of feedback for TrustMile on feedback screen'}, 'offerNeighbourSignupInMenu': {'type': 'boolean', 'description': 'yes/no to offer neighbour signup in the SETTINGS menu'}, 'heartbeat': {'type': 'integer', 'description': '0 (off) or greater, being the number of minutes between sending heartbeats to the server'}, 'isTrustMileNeighbour': {'type': 'boolean', 'description': 'yes/no that this user has given permission to receive deliveries on behalf of others'}, 'showMessages': {'type': 'boolean', 'description': 'show/hide the messages icon (no messages until ready for neighbour collections)'}}}
DefinitionsDeliveryupdate = {'required': ['description'], 'type': 'object', 'description': 'Just can update the description', 'properties': {'description': {'type': 'string'}}}
DefinitionsPromotionview = {'properties': {'promotionUrl': {'type': 'string'}, 'promotionViewId': {'type': 'string'}, 'promotionId': {'type': 'string'}}}
DefinitionsKeyvaluepair = {'properties': {'key': {'type': 'string'}, 'value': {'type': 'string'}}}
DefinitionsAdddelivery = {'required': ['courierSlug', 'trackingNumber', 'description', 'purchasedFrom'], 'type': 'object', 'description': "The tracking number and courier slug for a given parcel required to be added to the user's account. Retailer Name is optional", 'properties': {'trackingNumber': {'type': 'string'}, 'description': {'type': 'string'}, 'courierSlug': {'type': 'string'}}}
DefinitionsRecipienthandover = {'required': ['articleIds'], 'type': 'object', 'properties': {'recipientName': {'type': 'string'}, 'articleIds': {'items': {'type': 'string'}, 'type': 'array'}}}
DefinitionsTrackinginformation = {'description': 'reperesents 1 tracking event for a delivery', 'properties': {'checkpoint_time': {'type': 'string', 'format': 'datetime'}, 'tag': {'type': 'string', 'description': 'a code to describe this event, for courier events the tag will be the AfterShip tag.  For trustmile events the set of tages has not yet been determined'}, 'location': {'type': 'string'}, 'tacking_number': {'type': 'string'}, 'message': {'type': 'string', 'description': 'a free-form text description of the event'}, 'slug': {'type': 'string', 'description': 'tracking slug'}, 'isTrustMileEvent': {'type': 'boolean', 'description': 'true means this is a trustmile event, false means this is a courier event'}}}
DefinitionsCourier = {'description': 'A courier company', 'properties': {'courierId': {'type': 'string', 'format': 'uuid'}, 'name': {'type': 'string'}}}
DefinitionsArticle = {'description': 'A single physical article.  Consists of a tracking number and an item number, for cases where a TrackingNumber consists of several parcels.', 'properties': {'trackingNumber': {'type': 'string'}, 'articleId': {'type': 'string'}}}
DefinitionsMessage = {'description': 'a single message in a conversation', 'properties': {'isFromMe': {'type': 'boolean', 'description': 'was this message sent but the requesting user'}, 'from': {'type': 'string', 'description': 'text description of the person who wrote this message.'}, 'sequenceNumber': {'type': 'integer', 'description': 'the order of this message in this conversation'}, 'messageId': {'type': 'string', 'format': 'uuid'}, 'isUnread': {'type': 'boolean', 'description': 'has the user read this message or not.'}, 'messageContent': {'type': 'string', 'description': 'the content of the message'}}}
DefinitionsGeolocation = {'required': ['latitude', 'longitude'], 'type': 'object', 'description': "Essentially latitude and logitude of user's address", 'properties': {'latitude': {'type': 'number', 'format': 'double'}, 'longitude': {'type': 'number', 'format': 'double'}}}
DefinitionsPromotionviewlist = {'properties': {'promotionUrl': {'type': 'string'}, 'promotionName': {'type': 'string'}}}
DefinitionsAddresslocation = {'type': 'object', 'description': "Essentially latitude and logitude of user's address", 'properties': {'latitude': {'type': 'number', 'format': 'double'}, 'longitude': {'type': 'number', 'format': 'double'}}}
DefinitionsUserpresence = {'description': 'Schema for updating the users status for an address.', 'properties': {'status': {'type': 'boolean'}, 'location': DefinitionsAddresslocation}}
DefinitionsTrustmiledeliveryinfo = {'type': 'object', 'description': 'Detail info about a trustmile delivery', 'properties': {'articles': {'items': DefinitionsArticle, 'type': 'array'}, 'secretWord': {'type': 'string'}, 'recipientName': {'type': 'string'}}}
DefinitionsDictionary = {'properties': {'values': {'items': DefinitionsKeyvaluepair, 'type': 'array'}}}
DefinitionsAccountlogin = {'description': 'Required data for user login', 'properties': {'password': {'type': 'string', 'description': 'The password associated with the username'}, 'emailAddress': {'type': 'string', 'description': 'The emailAddress to login with'}, 'installationInformation': DefinitionsInstallationinformation}}
DefinitionsLogin = {'description': 'Required data for  login', 'properties': {'username': {'type': 'string', 'description': 'The username to login with'}, 'password': {'type': 'string', 'description': 'The password associated with the username'}, 'installationInformation': DefinitionsInstallationinformation}}
DefinitionsDeliveryinfo = {'type': 'object', 'description': 'A single summary of delivery info', 'properties': {'orderId': {'type': 'string'}, 'description': {'type': 'string'}, 'promotionDestUrl': {'type': 'string'}, 'courierPhone': {'type': 'string'}, 'deliveryIsValid': {'type': 'boolean'}, 'courierWeb': {'type': 'string'}, 'displayStatus': {'type': 'string'}, 'tag': {'type': 'string'}, 'retailerName': {'type': 'string'}, 'courierTrackingUrl': {'type': 'string'}, 'promotionSourceUrl': {'type': 'string'}, 'articles': {'items': DefinitionsArticle, 'type': 'array'}, 'latestStatus': {'type': 'string'}, 'feedbackLeft': {'type': 'boolean'}, 'trackingNumber': {'type': 'string'}, 'imageUrl': {'type': 'string'}, 'isDelivered': {'type': 'boolean'}, 'promotionViewId': {'type': 'string'}, 'deliveryId': {'type': 'string', 'format': 'uuid'}, 'promotionRetailerName': {'type': 'string'}, 'courierName': {'type': 'string'}, 'trackingEvents': {'items': DefinitionsTrackinginformation, 'type': 'array'}, 'isNeighbour': {'type': 'boolean'}, 'cardNumber': {'type': 'string'}, 'trackingInfoSupported': {'type': 'boolean'}, 'retailerImageUrl': {'type': 'string'}}}
DefinitionsAccountaddress = {'required': ['addressLine1', 'addressLine2', 'suburb', 'state', 'postcode', 'countryCode'], 'type': 'object', 'description': 'Object with users address information', 'properties': {'countryCode': {'type': 'string'}, 'suburb': {'type': 'string'}, 'state': {'type': 'string'}, 'phoneNumber': {'type': 'string'}, 'postcode': {'type': 'string'}, 'addressLine1': {'type': 'string'}, 'addressLine2': {'type': 'string'}, 'location': DefinitionsAddresslocation}}
DefinitionsCreatedelivery = {'required': ['articles', 'neighbourId'], 'type': 'object', 'properties': {'articles': {'items': DefinitionsArticle, 'type': 'array'}, 'location': DefinitionsGeolocation, 'neighbourId': {'type': 'string'}}}
DefinitionsAnonymousregister = {'required': ['installationInformation'], 'description': 'anonymous registration', 'properties': {'installationInformation': DefinitionsInstallationinformation}}
DefinitionsRecipientdetails = {'required': ['fullName'], 'type': 'object', 'description': 'When a "neighbour" hands over articles to "recipient", if user is unknown to TrustMile, neighbour shall provide email address.', 'properties': {'fullName': {'type': 'string'}, 'emailAddress': {'type': 'string'}, 'address': DefinitionsAccountaddress}}
DefinitionsAccountregister = {'required': ['emailAddress', 'password'], 'description': 'Content required for registering an account', 'properties': {'accountAddress': DefinitionsAccountaddress, 'fullName': {'type': 'string'}, 'password': {'type': 'string'}, 'emailAddress': {'type': 'string'}, 'installationInformation': DefinitionsInstallationinformation}}
DefinitionsAccountupdate = {'description': 'Users updated information, used for inputting name and address after initial register.', 'properties': {'accountAddress': DefinitionsAccountaddress, 'userPreferences': DefinitionsDictionary, 'trustmileNeighbour': {'type': 'boolean'}, 'fullName': {'type': 'string'}, 'installationInformation': DefinitionsInstallationinformation}}
DefinitionsNeighbourpickupinfo = {'required': ['neighbourName', 'neighbourAddress'], 'type': 'object', 'properties': {'recipientInfo': {'type': 'string'}, 'secretWord': {'type': 'string'}, 'neighbourPhone': {'type': 'string'}, 'courierName': {'type': 'string'}, 'neighbourAddress': DefinitionsAccountaddress, 'articleCount': {'type': 'integer'}, 'trackingNumber': {'type': 'string'}, 'packageDescription': {'type': 'string'}, 'neighbourName': {'type': 'string'}, 'correlationID': {'type': 'string'}}}
DefinitionsAccount = {'type': 'object', 'description': "An object corrosponding to a users 'account'", 'properties': {'userName': {'type': 'string'}, 'accountAddress': DefinitionsAccountaddress, 'emailAddress': {'type': 'string'}, 'installationInformation': DefinitionsInstallationinformation, 'emailVerified': {'type': 'boolean'}, 'fullName': {'type': 'string'}, 'userPreferences': DefinitionsDictionary}}
DefinitionsUserinfo = {'type': 'object', 'description': "An object corrosponding to a users 'account'", 'properties': {'accountAddress': DefinitionsAccountaddress, 'travelTimeText': {'type': 'string'}, 'travelTimeValue': {'type': 'integer'}, 'emailAddress': {'type': 'string'}, 'fullName': {'type': 'string'}, 'id': {'type': 'string'}}}
DefinitionsDelivery = {'required': ['articles'], 'type': 'object', 'properties': {'neighbour': DefinitionsUserinfo, 'articles': {'items': DefinitionsArticle, 'type': 'array'}, 'state': {'type': 'string'}, 'recipientInfo': DefinitionsRecipientinfo, 'deliveryId': {'type': 'string'}, 'lastUpdated': {'type': 'dateTime'}}}
DefinitionsNeighbourreceivelookup = {'type': 'object', 'description': 'Returned as a result of scanning the first item of a TMD', 'properties': {'articles': {'items': DefinitionsArticle, 'type': 'array'}, 'state': {'type': 'string'}, 'alternateRecipient': DefinitionsUserinfo, 'recipient': {'type': 'string'}, 'deliveryId': {'type': 'string'}, 'correlationID': {'type': 'string'}}}

validators = {
    ('deliveries_deliveryId', 'PUT'): {'json': {'properties': {'neighbourId': {'type': 'uuid'}}}},
    ('deliveries_deliveryId_articles', 'POST'): {'json': {'properties': {'trackingNumber': {'type': 'string', 'description': 'the tracking number scanned in from a barcode or typed in.'}}}},
    ('login', 'POST'): {'json': DefinitionsLogin},
    ('deliveries', 'POST'): {'json': DefinitionsCreatedelivery},
    ('deliveries', 'GET'): {'json': {'properties': {'history': {'type': 'boolean', 'description': 'set to true to retereive historical deliveries'}}}},
    ('login_password', 'POST'): {'json': {'properties': {'newPassword': {'type': 'string', 'description': 'The new password for the user'}, 'password': {'type': 'string', 'description': 'The users current password'}}}},
}

filters = {
    ('nearestNeighbours_latitude_longitude', 'GET'): {200: {'headers': None, 'schema': {'properties': {'alternateRecipients': {'items': DefinitionsUserinfo, 'type': 'array', 'description': 'an array of alternate recipients, ordered by proximity to the GPS coordinates stored against the delivery'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': None}, 404: {'headers': None, 'schema': {'properties': {'message': {'type': 'string', 'description': 'a text description of the failure reason'}, 'correlationID': {'type': 'string'}}}}},
    ('deliveries_deliveryId', 'PUT'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': None}},
    ('deliveries_deliveryId', 'GET'): {200: {'headers': None, 'schema': {'properties': {'delivery': DefinitionsDelivery, 'correlationID': {'type': 'string'}}}}},
    ('deliveries_deliveryId', 'DELETE'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': None}},
    ('deliveries_deliveryId_articles', 'POST'): {200: {'headers': None, 'schema': {'properties': {'parcels': {'items': DefinitionsArticle, 'type': 'array', 'description': 'an array of articles that are in this delivery'}, 'correlationID': {'type': 'string'}}}}, 409: {'headers': None, 'schema': {'properties': {'message': {'type': 'string', 'description': 'The message to display to the user'}, 'parcels': {'items': DefinitionsArticle, 'type': 'array', 'description': 'an array of articles that are in this delivery'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': None}},
    ('deliveries_deliveryId_articles', 'GET'): {200: {'headers': None, 'schema': {'properties': {'parcels': {'items': DefinitionsArticle, 'type': 'array', 'description': 'an array of articles that are in this delivery'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': None}},
    ('logout', 'POST'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('login', 'POST'): {200: {'headers': None, 'schema': {'properties': {'apiKey': {'type': 'string', 'format': 'uuid'}, 'userId': {'type': 'string', 'format': 'uuid'}, 'correlationID': {'type': 'string'}}}}, 403: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
    ('deliveries', 'POST'): {200: {'headers': None, 'schema': {'properties': {'deliveryID': {'type': 'string', 'format': 'uuid'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': None}},
    ('deliveries', 'GET'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}, 'deliveries': {'items': DefinitionsDelivery, 'type': 'array'}}}}, 401: {'headers': None, 'schema': None}},
    ('account', 'GET'): {200: {'headers': None, 'schema': {'properties': {'account': DefinitionsAccount, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}},
    ('account', 'DELETE'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 409: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': Definitions401}},
    ('deliveries_state_deliveryState', 'GET'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}, 'deliveries': {'items': DefinitionsDelivery, 'type': 'array'}}}}, 401: {'headers': None, 'schema': None}},
    ('articles_trackingNumber', 'GET'): {200: {'headers': None, 'schema': {'properties': {'article': DefinitionsArticle, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': None}, 404: {'headers': None, 'schema': {'properties': {'message': {'type': 'string', 'description': 'a text description of the failure reason, indicating if the deliveryID or trackingNumber was not found'}, 'correlationID': {'type': 'string'}}}}},
    ('articles_trackingNumber', 'DELETE'): {200: {'headers': None, 'schema': {'properties': {'articles': {'items': DefinitionsArticle, 'type': 'array'}, 'correlationID': {'type': 'string'}}}}, 409: {'headers': None, 'schema': {'properties': {'articles': {'items': DefinitionsArticle, 'type': 'array', 'description': 'a list of articles on the associated delivery'}, 'message': {'type': 'string', 'description': 'a text description of the failure reason'}, 'correlationID': {'type': 'string'}}}}, 404: {'headers': None, 'schema': {'properties': {'articles': {'items': DefinitionsArticle, 'type': 'array', 'description': 'a list of articles on the associated delivery'}, 'message': {'type': 'string', 'description': 'a text description of the failure reason, indicating if the deliveryID or trackingNumber was not found'}, 'correlationID': {'type': 'string'}}}}, 401: {'headers': None, 'schema': None}},
    ('login_password', 'POST'): {200: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 403: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}, 422: {'headers': None, 'schema': {'properties': {'correlationID': {'type': 'string'}}}}},
}

scopes = {
    ('nearestNeighbours_latitude_longitude', 'GET'): [],
    ('deliveries_deliveryId', 'PUT'): [],
    ('deliveries_deliveryId', 'GET'): [],
    ('deliveries_deliveryId', 'DELETE'): [],
    ('deliveries_deliveryId_articles', 'POST'): [],
    ('deliveries_deliveryId_articles', 'GET'): [],
    ('logout', 'POST'): [],
    ('deliveries', 'POST'): [],
    ('deliveries', 'GET'): [],
    ('account', 'GET'): [],
    ('account', 'DELETE'): [],
    ('deliveries_state_deliveryState', 'GET'): [],
    ('articles_trackingNumber', 'GET'): [],
    ('articles_trackingNumber', 'DELETE'): [],
    ('login_password', 'POST'): [],
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

