from app.async.tasks import *
import argparse
import pprint
import aftership

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--delivered', '-d', help="Get all tracking info", dest='delivered', action='store_true')
    parser.add_argument("--tn", help="tracking number. eg 123123123123")
    parser.add_argument("--slug", help="courier slug such as australia-post or toll-ipec")
    parser.add_argument('--retry', dest='retry', action='store_true')
    parser.set_defaults(retry=False)
    args = parser.parse_args()

    if args.delivered:
        api = aftership.APIv4(config.AFTERSHIP_API_KEY, datetime_convert=False)
        tracking_data = api.trackings.get()
        total_trackings = tracking_data[u'count']
        limit = tracking_data[u'limit']
        all_trackings = []
        for i in xrange((total_trackings/limit) + 1):
            all_trackings.append( api.trackings.get(page=i) )

        delivered_trackings = []
        for p in all_trackings:
            for t in p[u'trackings']:
                checkpoints = t.get(u'checkpoints', [])
                if checkpoints:
                    is_delivered = u'Delivered' in [c[u'tag'] for c in checkpoints]
                    if is_delivered:
                        delivered_trackings.append((t[u'tracking_number'], t[u'slug']))

        delivered_trackings = set(delivered_trackings)

        pprint.pprint(delivered_trackings)
    else:
        tracking_data = retrieve_tracking_info(args.slug, args.tn, retry=args.retry)
        pprint.pprint(tracking_data)

