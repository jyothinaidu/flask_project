from app import db
from app.model.meta.schema import  Location
from geoalchemy2 import functions
from geopy import distance
from datetime import datetime
import time
import googlemaps
from googlemaps import distance_matrix


# lat, log = 27.685994,85.317815
# add = 0.100011
# points = []
# original_loc = LocationGeom(lat, log)
#
# db.session.rollback()
# for i in xrange(100):
#     lat = lat + add
#     log = log + add
#     #points.append('POINT({0}, {1}, 4326)'.format(str(lat + add), str(log + add)))
#     loc = LocationGeom(lat, log)
#     db.session.add(loc)
# #lg = LocationGeom(27.685994,85.317814)
# print original_loc.__dict__
# db.session.commit()
# #q = db.session.query(LocationGeom).order_by(LocationGeom.loc.distance_box('POINT(27.685995 85.317816 4326)')).limit(10)
# q = db.session.query(LocationGeom).filter(functions.ST_DFullyWithin(LocationGeom.loc, original_loc.loc,  1609)) # .order_by(LocationGeom.loc.distance_centroid(original_loc.loc)).limit(10)
# rs = q.all()
#
# print len(rs)
# for r in rs:
#     print r
#     print db.session.scalar(functions.ST_X(r.loc)), db.session.scalar(functions.ST_Y(r.loc))
#     #db.session.add(Location(db.session.scalar(functions.ST_X(r.loc)), db.session.scalar(functions.ST_Y(r.loc))))
#     print "Latitude {0}, longitude {1}".format(r.loc.x, r.loc.y)
#


# db.session.commit()
# rs2 = db.session.query(Location).all()

# for r2 in rs2:
#     print type(db.session.scalar(functions.ST_X(r2.loc)))
#     print "Location: {0}, {1}".format(db.session.scalar(functions.ST_X(r2.loc)), db.session.scalar(functions.ST_Y(r2.loc)))


gclient = googlemaps.Client('AIzaSyCSq6WKgNSjjU6nwC3ZhJmy7ZoHeJ4nMuk')
lat, log = -33.871755, 151.228769
add = 0.0034
points = []
original_loc = Location(lat, log)

db.session.rollback()
for i in xrange(100):
    lat = lat + add
    log = log + add
    # points.append('POINT({0}, {1}, 4326)'.format(str(lat + add), str(log + add)))
    loc = Location(lat, log)
    db.session.add(loc)
# lg = Location(27.685994,85.317814)
db.session.commit()
# q = db.session.query(Location).order_by(Location.loc.distance_box('POINT(27.685995 85.317816 4326)')).limit(10)
q = db.session.query(Location).filter(functions.ST_DWithin(Location.loc, original_loc.loc,
                                                           1609))  # .order_by(Location.loc.distance_centroid(original_loc.loc)).limit(10)

rs = q.all()

print len(rs)
distances = []
destinations = []
for r in rs:
    # print r
    # print db.session.scalar(functions.ST_Y(r.loc)), db.session.scalar(functions.ST_X(r.loc))
    loc1 = (db.session.scalar(functions.ST_Y(r.loc)), db.session.scalar(functions.ST_X(r.loc)))
    origin = (27.685994, 85.317815)
    d = distance.vincenty(loc1, origin).meters
    distances.append(d)

    destinations.append(loc1)


    # Latitude comes first and in PostGIS it's the Y coordinate!!
    print "Location ({0}, {1}) is {2} meters from origin {3}".format(db.session.scalar(functions.ST_Y(r.loc)), db.session.scalar(functions.ST_X(r.loc)),
                                                                         d, origin )
origins = [origin]

matrix = gclient.distance_matrix(origins, destinations, mode="driving")



distances = sorted(distances)

print distances[0:5]
    # db.session.add(Location(db.session.scalar(functions.ST_X(r.loc)), db.session.scalar(functions.ST_Y(r.loc))))
    # print "Latitude {0}, longitude {1}".format(r.loc.x, r.loc.y)
#
# results = db.session.query(Location).all()
# distances = []
# for r in xrange(len(results)):
#     for i in xrange(1, r):
#         loc1 = (db.session.scalar(functions.ST_X(results[r].loc)), db.session.scalar(functions.ST_Y(results[r].loc)))
#         loc2 = (db.session.scalar(functions.ST_X(results[i].loc)), db.session.scalar(functions.ST_Y(results[i].loc)))
#         d = distance.vincenty(loc1, loc2).meters
#         distances.append(d)
#         # d = db.session.query(functions.ST_Distance(results[r].loc, results[r+1].loc)).one()
#
# print sorted(distances)
# print len(distances)

count = db.session.query(Location).delete()
db.session.commit()
print count
