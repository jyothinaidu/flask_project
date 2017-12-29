from nose.tools import eq_

from app import db
from app.location.distances import NearestNeighbours
from app.model.meta.schema import Location, UserPresence
from app.users.model import ConsumerUser
import config
import googlemaps

from app.users.serialize import UserAddressSchema
from tests import TransactionalTest


class DistancesTest(TransactionalTest):

    @property
    def session(self):
        return self.__class__.db.session

    def test_distances(self):
        cons_user = ConsumerUser.create('james@trustmile.com', 'boundary', name='James O''Rourke')
        cons_user.trusted_neighbour = True
        self.gclient = googlemaps.Client(config.GOOGLE_LOCATION_KEY)
        results = self.gclient.geocode("12 Ithaca Rd, Eliabeth Bay")
        lat, lng = results[0][u'geometry'][u'location'][u'lat'], results[0][u'geometry'][u'location'][u'lng']
        cons1_user_location = Location(lat, lng)
        original_location = Location(lat, lng)

        addr_info = {'addressLine1': '12 Ithaca Rd', 'addressLine2': "", "countryCode": "AU", "suburb": "Elizabeth Bay", "postcode": "2011", "state": "NSW"}
        address_obj = UserAddressSchema().load(addr_info, partial=True).data
        cons_user.user.user_address.append(address_obj)
        address_obj.user_presence.append(UserPresence(True, lat, lng))
        cons_user.user.user_address[0].location =cons1_user_location

        cons_user2 = ConsumerUser.create('james+bogus@trustmile.com', 'boundary', name='Bruce Towers')
        cons_user2.trusted_neighbour = True
        results = self.gclient.geocode("184 Forbes St, Darlinghurst NSW 2011")
        lat, lng = results[0][u'geometry'][u'location'][u'lat'], results[0][u'geometry'][u'location'][u'lng']
        new_loc = Location(lat, lng)
        addr_info = {'addressLine1': '184 Forbes St', 'addressLine2': "", "countryCode": "AU", "suburb": "Darlinghurst", "postcode": "2010", "state": "NSW"}
        address_obj = UserAddressSchema().load(addr_info, partial=True).data


        cons_user2.user.user_address.append(address_obj)
        address_obj.user_presence.append(UserPresence(True, lat, lng))

        cons_user2.user.user_address[0].location = new_loc
        db.session.add(new_loc)
        db.session.add(original_location)

        db.session.commit()

        nn = NearestNeighbours(original_location)

        users = nn.get_user_distances()
        eq_(len(users), 2)
        eq_(users[0].user.get_user_details().email_address, cons_user.email_address)

        cons_user2 = ConsumerUser.query.filter(ConsumerUser.email_address == 'james+bogus@trustmile.com').one()
        address_obj = UserAddressSchema().load(addr_info, partial=True).data
        cons_user2.user.user_address.append(address_obj)
        address_obj.user_presence.append(UserPresence(False, lat, lng))

        db.session.commit()
        nn = NearestNeighbours(original_location)

        users = nn.get_user_distances()
        eq_(len(users), 1)
        eq_(users[0].user.get_user_details().email_address, cons_user.email_address)



