from geoalchemy2 import functions
from sqlalchemy import and_
from sqlalchemy.orm import aliased
from app import db
from app.model.meta.schema import Location, Address
from app.users.model import ConsumerUser, User

class LocationDict:

    def __init__(self, lat, lng):
        self.latitude = lat
        self.longitude = lng

    def __repr__(self):
        return str({'lat': self.latitude, 'lng': self.longitude})

    def __hash__(self):
        return hash(self.latitude) + hash(self.longitude)

    def __lt__(self, other):
        return self.latitude < other.latitude and self.longitude < other.longitude

    def __eq__(self, other):
        return self.latitude == other.latitude and self.longitude == other.longitude

radius = 100000000
alias_address = aliased(Address)
original_location = Location(-33.894283, 151.266900)
nearby_locations = db.session.query(Location).join(alias_address, alias_address.id == Location.address_id).join(
    User, User.id == alias_address.tmuser_id).join(ConsumerUser).filter(
    and_(functions.ST_DWithin(Location.loc, original_location.loc, radius),
         User.at_home == True, ConsumerUser.trusted_neighbour == True)).all()
locations_dicts = []
for n in nearby_locations:
    ld = LocationDict(n.latitude, n.longitude)
    if ld not in locations_dicts:
        locations_dicts.append(LocationDict(n.latitude, n.longitude))


print sorted(locations_dicts)
print len(locations_dicts)

