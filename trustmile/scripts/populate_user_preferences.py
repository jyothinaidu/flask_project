from app import util
from app.location.geocode import Geocoder
import config
import logging

from app.users.model import ConsumerUser, User
from app import db

logger = logging.getLogger()

def update_address_locations():
    wait_time = 0
    users = User.query.all()


    for user in users:
        user_addr = None
        if len(user.user_address) > 0:
            s_user_addresses = sorted(user.user_address, cmp=util.create_dates_asc_cmp, reverse=True)
            user_addr = s_user_addresses[0]
        if user_addr:
            logger.debug(u"Geocoding address with id {0}".format(str(user_addr.id)))
            str_address = "{0} {1}, {2}, {3}, {4}, {5}".format(user_addr.addressLine1, user_addr.addressLine2, user_addr.suburb,
                                                               user_addr.postcode, user_addr.state, user_addr.countryCode)
            geocoder = Geocoder(config.GOOGLE_LOCATION_KEY)
            loc = None
            try:
                loc = geocoder.geocode(str_address)
            except Exception, e:
                logger.error(u"could not geocode address {0}".format(str_address))
            if loc:
                logger.debug(u"Location is {0}".format(loc))
                user.preferences =  {'values': [{'key': 'courierHonesty', 'value': 'False'}, {'key': 'userLocation', 'value': '{0},{1}'.format(loc.latitude, loc.longitude)}]}
            else:
                user.preferences = {'values': [{'key': 'courierHonesty', 'value': 'False'}, {'key': 'userLocation', 'value': '0.000000,0.000000'}]}

        else:
            user.preferences = {'values': [{'key': 'courierHonesty', 'value': 'False'}, {'key': 'userLocation', 'value': '0.000000,0.000000'}]}

        logger.debug(u"set user preferences for id {0} to {1}".format(str(user.id), user.preferences))
        db.session.add(user)
        db.session.commit()

if __name__ == '__main__':
    update_address_locations()
