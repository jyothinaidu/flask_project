__author__ = 'james'


class InsecurePasswordException(Exception):
    pass


class InvalidEmailException(Exception):
    pass


class EmailSendException(Exception):
    pass


class EntityNotFoundException(Exception):
    pass


class DeliveryNotFoundException(Exception):
    pass


class CourierNotFoundException(Exception):
    pass


class NoTrackingResultsException(Exception):
    pass


class LocationNotAvaiable(Exception):
    pass


class NoLocationFoundException(Exception):
    pass


class NoCourierFoundException(Exception):
    pass


class NoCheckpointsException(Exception):
    pass


class TrackingResultsRetryException(Exception):
    pass

class ShippingInfoUnsupportedException(Exception):
    pass

class NoAddressSetException(Exception):
    pass

class InvalidParameterException(Exception):
    pass