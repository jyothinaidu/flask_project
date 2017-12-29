import json

import os
import requests
from geoalchemy2 import WKTElement
from geoalchemy2.elements import _SpatialElement
from sqlalchemy.sql import functions

import config
from app.exc import InvalidEmailException
from validate_email import validate_email as val_email


__author__ = 'james'


def validate_email(email_address):
    valid_address = val_email(email_address)
    if not valid_address:
        raise InvalidEmailException(u"Email not valid")
    return email_address

def create_dates_asc_cmp(item1, item2):
    if item1.created_at < item2.created_at:
        return -1
    elif item1.created_at > item2.created_at:
        return 1
    else:
        return 0

class WKTGeographyElement(WKTElement):
    """
    Instances of this class wrap a WKT value.

    Usage examples::

    wkt_element = WKTGeographyElement('POINT(4.1 52.0)') # long, lat in degrees

    """

    def __init__(self, *args, **kwargs):
        kwargs["srid"] = 4326
        _SpatialElement.__init__(self, *args, **kwargs)
        functions.Function.__init__(self, "ST_GeographyFromText",
                                     self.data)


def wkt_geog_element(longitude, latitude):
    return WKTGeographyElement('POINT({0} {1})'.format(str(longitude), str(latitude)))


def get_branch_link(data):
    result = requests.post(config.BRANCH_URL,
                           json={"branch_key": config.BRANCH_KEY, "data": data},
                           headers={'content-type': 'application/json'})
    js = json.loads(result.content)
    return js.get('url')


def gen_random_str(length):
    return "".join("%.2x" % ord(x) for x in os.urandom(length/2))