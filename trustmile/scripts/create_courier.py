import argparse
from app import db
from app.deliveries.model import Courier

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--courier_name", "-n", help="Courier name eg. Allied Express", required=True)
    parser.add_argument("--slug", "-s", help="Slug for courier eg. allied-express", required=True)
    parser.add_argument("--web_url", "-w", help="Courier weburl eg. http://www.alliedexpress.com.au/", required=True)
    parser.add_argument("--phone", "-p", help="Courier phonenumber", required=True)
    parser.add_argument("--tracking_url", "-t", help="Tracking url for this courier eg. http://www.alliedexpress.com.au/", required=True)
    parser.add_argument("--tracking_info_supported", "-i", help="Is this an aftership supported courier",  dest='tracking_info_supported', action='store_true')

    args = parser.parse_args()
    tracking_info_supported = args.tracking_info_supported
    try:
        courier = Courier(args.courier_name, args.slug, args.phone, args.web_url, trustmile_courier=tracking_info_supported,
                          tracking_url=args.tracking_url, tracking_info_supported=tracking_info_supported)
        db.session.add(courier)
        db.session.commit()
        print u"Courier '{0}' created".format(args.courier_name)
    except Exception, e:
        db.session.rollback()
        print e.message
