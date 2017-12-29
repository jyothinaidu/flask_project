import requests
import json
d =  {"recipientId":"","deliveryId":"","state":"COURIER_ABORTED","neighbourId":"c8c174df-a65c-40d8-80f4-640df15e6767","articles":[{"tracking_number":"34654"}],"location":{"longitude":151.211,"latitude":-33.8634}}
r = requests.post('https://devapi.trustmile.com/courier/v1/deliveries', headers = {"X-Consumer-apiKey": '80e03460a3de8af67a08218b780060cf16e18199b226af06ca7883c8ff81e246', "Content-Type" : "application/json"}, data = json.dumps(d))

print r
print r.content