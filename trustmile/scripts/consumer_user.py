import requests
import argparse
import json
account_register = {
    "fullName": "James Bruceton",
    "password": "boundary1234",
    "emailAddress": "this_is_it2@cloudadvantage.com.au",
    "installationInformation": {
        "OSType": "iPhone OS",
        "OSMinorVersion": "0",
        "DeviceIdentifier": "E2C7518B-A346-4A1A-9A3E-D53F4CAA7AE3",
        "ApplicationVersion": "1.0",
        "OSMajorVersion": "9"
    }
}
headers = {
    'content-type' : 'application/json',
}

base_url = 'http://api.trustmile.com/consumer/v1/account/register'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", "-e", help="email for consumer such as james@cloudadvantage.com.au", required = True)
    parser.add_argument("--password", "-p", help="password for new courier user", required=True)
    parser.add_argument("--fullname", "-n", help="The name of the user", required=True)
    parser.add_argument('--test', dest='test', action='store_true')
    parser.add_argument('--local', dest='local', action='store_true')

    args = parser.parse_args()

    account_register['fullName'] = args.fullname
    account_register['emailAddress'] = args.email
    account_register['password'] = args.password

    if args.test:
        base_url = base_url.replace('api', 'devapi')
    elif args.local:
        base_url = base_url.replace('api.trustmile.com', '127.0.0.1:5000')

    print base_url

    result = requests.post(base_url, json = account_register, headers = headers)

    print u"Did register with result {0}".format(result)



