import json
import requests
import ascii85
import argparse

""" Example : python scripts/ingest_promotion.py
                  -r 523b7c1b-3db5-48b8-972c-8c484ee30890 -f promo_test.png
                  -n promot_test_2.png -d https://www.catchoftheday.com.au """


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--retailer_id", '-r', help="Retailer id for the promotion", required=True)
    parser.add_argument("--filepath", '-f', help="Banner image to post", required=True)
    parser.add_argument("--name", '-n', help="name of the image item", required=True)
    parser.add_argument("--destination_url", '-d', help="URL where the banner will redirect to", required=True)
    parser.add_argument("--environment", '-e', help="prod or dev", required=False)

    args = parser.parse_args()
    try:
        f = open(args.filepath)
        image_data = ascii85.b85encode(f.read())
        data = {'retailerId': args.retailer_id, 'promotionDestinationUrl': args.destination_url,
                'promotionImages': [{'imageFileData': image_data, 'name': args.name}]}
        api_url = 'https://devapi.trustmile.com/admin/promotion'
        if args.environment == 'prod':
            api_url = 'https://api.trustmile.com/admin/promotion'
        response = requests.post(api_url, data=json.dumps(data),
                                 headers={'content-type': 'application/json',
                                          'X-admin-apiKey':
                                              'apieufr392q45679q(@^*(%KJbglhgdshfbaepiu^%@$*^%@RFJHVBLKJB:LK'})
        print 'Posted new promotion with result {0}'.format(response.status_code)
    except Exception, e:
        print e.message
    else:
        print u"Promotion for reailer {0} created".format(args.retailer_id)
