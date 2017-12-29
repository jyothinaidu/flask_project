from app.users.model import ConsumerUser
import argparse
from app import db
from app.async import tasks

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", help="Email address for consumer user", required=True)

    args = parser.parse_args()

    try:
        print 'Starting for email {0}'.format(args.email)
        consumer_user = db.session.query(ConsumerUser).filter(ConsumerUser.email_address == args.email).one()
        user = consumer_user.user
        user.update_preferences({u'values': [{u'key': u'neighbourEnabled', u'value': True}, ]})
        tasks.send_push.delay(args.email, data={'account_changed': True})
        print u"Before commit"
        db.session.commit()
        print u"User {0} enabled as neighbour receiver".format(args.email)
    except Exception, e:
        db.session.rollback()
        print e.message