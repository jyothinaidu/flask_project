__author__ = 'james'
from tests import AppTest
from app.location.geocode import Geocoder


class LocationTest(AppTest):

    def setUp(self):
        super(LocationTest, self).setUp()
        self.geocoder = Geocoder(api_key='AIzaSyCSq6WKgNSjjU6nwC3ZhJmy7ZoHeJ4nMuk')

    def tearDown(self):
        pass

    def test_my_location(self):
        str_address = "801/12 Ithaca Rd Elizabeth Bay 2011 NSW"
        loc = self.geocoder.geocode(str_address)
        assert loc is not None
        assert loc.latitude is not None
        print loc.latitude, loc.longitude
        assert loc.longitude is not None



