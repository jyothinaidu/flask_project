from sqlalchemy import and_
from sqlalchemy.orm import aliased

from app import db
from app.model.meta.schema import Location, Address
from geoalchemy2 import functions
import config
import googlemaps
import logging

from app.users.model import User, ConsumerUser

logger = logging.getLogger()


class UserDistance:

    def __init__(self, user, distance_info):
        self.user = user
        self.distance_info = distance_info


    @property
    def user(self):
        return self.user

    @property
    def duration_value(self):
        return self.distance_info.get(u'duration', {}).get(u'value')

    @property
    def duration_text(self):
        return self.distance_info.get(u'duration', {}).get(u'text')

    def to_json(self):
        json_result = self.user.user_details_data()
        json_result['travelTimeText'] = self.duration_text
        json_result['travelTimeValue'] = self.duration_value
        return json_result


class UserDistances:
    def __init__(self, user_distances):
        self.user_distances = user_distances

    def by_travel_time(self):

        def travel_time_cmp(item1, item2):
            return item1.duration_value - item2.duration_value

        self.user_distances = sorted(self.user_distances, travel_time_cmp)

        return self


class NearestNeighbours:
    def __init__(self, original_location, radius=config.DEFAULT_RADIUS):

        self.gclient = googlemaps.Client(config.GOOGLE_LOCATION_KEY)
        alias_address = aliased(Address)

        nearby_locations = db.session.query(Location).join(alias_address, alias_address.id == Location.address_id).join(
            User, User.id == alias_address.tmuser_id).join(ConsumerUser).filter(
            and_(functions.ST_DWithin(Location.loc, original_location.loc, radius),
                 User.at_home == True, ConsumerUser.trusted_neighbour == True)).all()
        logger.debug('Nearby locations count {0}'.format(len(nearby_locations)))
        result_locations = []
        if nearby_locations:
            users = db.session.query(User).join(Address).filter(
                Address.id.in_(l.user_address.id for l in nearby_locations)).all()
            logger.debug('Found {0} users with addresses in nearby locations'.format(len(users)))
            address_set = set(l.user_address.id for l in nearby_locations)
            for u in users:
                if u.user_address[0].id in address_set:
                    result_locations.append(u.user_address[0].location)

        #print result_locations
        logger.debug(u'Found {0} locations within {1}'.format(len(result_locations), radius))
        origin_loc = ((original_location.latitude, original_location.longitude))
        destinations = []
        for r in result_locations:
            destinations.append((r.latitude, r.longitude))
        user_distances = []
        if len(destinations) > 0:
            dmatrix = self.gclient.distance_matrix([origin_loc], destinations, mode="driving")

            logger.debug(u"dmatrix rows {0}".format(dmatrix[u'rows']))

            """ Build { user: {address: address,
                             location: coords,
                             nearest_location: nearest_loc
                    }
            """
            i = 0
            for l in result_locations:
                # Tuple makes more sense to me now.
                user_distances.append(UserDistance(l.user_address.user, dmatrix[u'rows'][0][u'elements'][i]))
                i += 1

        self.user_distances = UserDistances(user_distances)


    @property
    def distances(self):
        return self.user_distances

    def by_travel_time(self):
        self.user_distances = self.user_distances.by_travel_time()
        return self

    def get_user_distances(self):
        return self.user_distances.user_distances
