import requests

import json

cid = '4e6b025d-d81e-405e-8bca-43c6e65f9e2c'

response = requests.get('https://api.trustmile.com/' + 'consumer/v1/deliveries/' + cid,
                         headers = { 'content-type': 'application/json',
                                   'X-consumer-apiKey': 'a685b6ff501f06afcaedcf25ab323b2dc8f53666f642631afe0b78b1469f2acc'})

print response
print json.loads(response.content)