import requests
import config
import json

result = requests.post('https://api.branch.io/v1/url',
              json= {"branch_key": config.BRANCH_KEY, "data": {"url": "trustmile://delivery?123123123"}},
              headers = {'content-type': 'application/json'} )

print result
js = json.loads(result.content)
print js.get('url')
