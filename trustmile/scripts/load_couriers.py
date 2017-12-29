__author__ = 'james'

from app import db
from app.deliveries.model import Courier
import json
import os
import codecs



path = os.getcwd()
print path
d  = codecs.open(path + "/tests/couriers-aftership.json", 'r', 'utf-8')

d = json.load(d)

couriers = d

for c in couriers:
    try:
        courier = Courier.query.filter(Courier.courier_slug == c['slug']).first()
        if courier:
            courier.phone = c['phone']
            courier.web_url = c['web_url']
            courier.courier_name = c['name']
            print u"Updating courier {0} with slug {1}".format(c['name'], c['slug'])
        else:
            courier = Courier(c['name'], c['slug'], c['phone'], c['web_url'], trustmile_courier=True)
            print u"Added courier {0} with slug {1}".format(c['name'], c['slug'])

        db.session.add(courier)
    except Exception, e:
        print e

db.session.commit()




