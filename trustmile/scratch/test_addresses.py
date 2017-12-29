from sqlalchemy import and_
from sqlalchemy.orm import aliased

from app import db
from app.model.meta.schema import Location, Address
from geoalchemy2 import functions
import config
import googlemaps
import logging

from app.users.model import User, ConsumerUser

original_location = Location(-33.87169563680316, 151.2290028670348)
alias_address = aliased(Address)
radius = 1600
nearby_locations = db.session.query(Location).join(alias_address, alias_address.id == Location.address_id).join(
    User, User.id == alias_address.tmuser_id).join(ConsumerUser).filter(
    and_(functions.ST_DWithin(Location.loc, original_location.loc, radius),
         User.at_home == True, ConsumerUser.trusted_neighbour == True)).all()

print nearby_locations

users = db.session.query(User).join(Address).filter(
                Address.id.in_(l.user_address.id for l in nearby_locations)).all()
result_locations = []
address_set = set(l.user_address.id for l in nearby_locations)
for u in users:
    #print u.user_address[0].id
    for i in xrange(len(u.user_address)):
        print 'Consumer user email {0}'.format(u.consumer_user.email_address)
        print 'Address id {0}'.format(str(u.user_address[i].id))
        print 'Address Line 1 {0}'.format(u.user_address[i].addressLine1)
        print 'Address location {0}'.format(u.user_address[i].location)
        #print "Latitude {0}, longitude {1}".format(u.user_address[i].location.latitude, u.user_address[i].location.longitude)

#print address_set
for u in users:
    if u.user_address[0].id in address_set:
        result_locations.append(u.user_address[0].location)


james  = ConsumerUser.query.filter(ConsumerUser.email_address == 'james@cloudadvantage.com.au').first()

for a in james.user.user_address:
    print str(a.id)