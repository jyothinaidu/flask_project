from app.deliveries.model import Courier
from app.exc import NoCourierFoundException
from app.users.model import CourierUser
from app import db

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", help="username for courier such as jorourke, garronl etc.", required = True)
    parser.add_argument("--password", help="password for new courier user", required=True)
    parser.add_argument("--fullname", help="The name of the user", required=True)
    parser.add_argument("--courier", help="Courier slug of this courier users courier", required=True)

    args = parser.parse_args()
    try:
        courier = Courier.query.filter(Courier.courier_slug == args.courier).first()
        if not courier:
            raise NoCourierFoundException(u"cannot find courier {0}".format(args.courier))
        cuser = CourierUser.create(args.username, args.password, args.fullname, courier)
        db.session.commit()
    except Exception, e:
        db.session.rollback()
        print e.message
    print u"User {0} created".format(args.username)
