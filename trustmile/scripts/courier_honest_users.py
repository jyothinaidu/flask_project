from app.users.model import *

all_users = User.query(User.preferences).all()
courier_honest_users = []

for u in all_users:
    preferences = u.preferences
    if isinstance(preferences, dict):
        print "is dict"
        arr = preferences.get('values', [])
        for v in arr:
            if v.get(u'key') == 'courierHonesty':
                courier_honesty = v.get(u'value')
                if courier_honesty:
                    courier_honest_users.append(u)

print len(courier_honest_users)