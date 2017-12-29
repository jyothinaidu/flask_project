import argparse
import requests
import json
import pprint


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--apikey", "-k", help="Key to use", required=True)
    parser.add_argument("--single", "-s", dest='single', action='store_true')
    parser.add_argument("--deliveryId", "-d", help="Delivery id to get if present", required=True)
    parser.add_argument("--environment", "-e", help="Which environment - prod/dev")

    args = parser.parse_args()
    url = 'https://api.trustmile.com/consumer/v1/deliveries'
    if args.environment:
        if args.environment == 'dev':
            url = 'https://devapi.trustmile.com/consumer_v1/deliveries'

    if args.single:
        url = url + '/' + args.deliveryId

    h = {'X-consumer-apiKey': args.apikey,
         'content-type': 'application/json'}

    result = requests.get(url, headers = h)

    pprint.pprint(json.loads(result.content))