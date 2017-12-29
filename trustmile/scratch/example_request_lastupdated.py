import requests
import json
import datetime as dt
import re
headers  = {'content-type': 'application/json', 'X-consumer-apiKey': 'fd4dae05705801da7b34a13b3d1edeb8ee72fa40b7f0fdf21b52f373a9b9aac3'}
r = requests.get('https://devapi.trustmile.com/courier/v1/deliveries', headers = headers)
print r
d = json.loads(r.content)
print d
datetime_str = d['deliveries'][0]['lastUpdated']
m = re.match('(\S*)((-|\+)\d\d:\d\d)$', datetime_str)
print m.groups()
print m.group(0)
v = m.group(1)
print m.group(2)

mdt = dt.datetime.strptime(v, '%Y-%m-%dT%H:%M:%S.%f')
print mdt
# Prints example: Wednesday 27 April 2016, 02:08AM
print mdt.strftime('%A %d %B %Y, %I:%M%p')