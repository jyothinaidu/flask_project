from app.exc import NoLocationFoundException

__author__ = 'james'
import logging
import googlemaps

logger = logging.getLogger()



class Geocoder(object):
    def __init__(self, api_key=None):

        self.api_key = api_key
        self.client = googlemaps.Client(self.api_key)

    def geocode(self, address_str):
        try:
            results = self.client.geocode(address_str)

        except Exception, e:
            logger.exception(e)
            raise e

        else:
            logger.debug('Found {0} results for address {1}'.format(len(results), address_str))
            return Location(results)


class Location(object):

    def __init__(self, results):

        if results and len(results) > 0:
            self.latitude = results[0].get(u'geometry').get(u'location').get(u'lat')
            self.longitude = results[0].get(u'geometry').get(u'location').get(u'lng')
        else:
            raise NoLocationFoundException(u"Geocoding failed for address")


if __name__ == '__main__':

    gc = Geocoder('AIzaSyCSq6WKgNSjjU6nwC3ZhJmy7ZoHeJ4nMuk')
    loc = gc.geocode("12 Ithaca Rd, Elizabeth Bay, Australia")

    print u'My address has coordinates lat: {0}, long: {1}'.format(loc.latitude, loc.longitude)


