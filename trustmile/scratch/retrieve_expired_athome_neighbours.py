from app.users.model import User
from app.model.meta.schema import Address, UserPresence
import datetime
import pytz


now = datetime.datetime.utcnow()
now = now.replace(tzinfo=pytz.utc)

users = User.query.join(Address).join(UserPresence).filter(User.at_home == True)

for u in users:
    if u.user_address:
        up = u.user_address[0].user_presence
        if up:
            latest_up = up[0]
            diff =  now - latest_up.created_at
            if diff.seconds > 3600:
                print 'User {0}, {1} expired, last user_presence updated {2}'.format(u.id, u.consumer_user.email_address, latest_up.created_at)
            else:
                print  'User {0}, {1} still at home, last user_presence updated {2}'.format(u.id, u.consumer_user.email_address, latest_up.created_at)
