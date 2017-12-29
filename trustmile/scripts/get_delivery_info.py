import argparse
import pprint
from app.ops.consumer_operations import *
from app.async.tasks import retrieve_tracking_info

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", "-e", help="email for consumer such as james@cloudadvantage.com.au", required = True)
    parser.add_argument("--password", "-p", help="password for new courier user", required=True)
    args = parser.parse_args()

    AccountLoginOperation().perform({})

    tracking_data = retrieve_tracking_info(args.slug, args.tn, retry=args.retry)

    pprint.pprint(tracking_data)

