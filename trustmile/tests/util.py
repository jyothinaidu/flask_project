import json
import config
import os
from app.deliveries.model import Courier
from app import db

def load_couriers():
    path = os.path.dirname(os.path.realpath(__file__))
    d = json.load(open(os.path.join(path, config.AFTERSHIP_COURIER_FILE)))
    couriers = d

    for c in couriers:
        courier = Courier(c['name'], c['slug'], c['phone'], c['web_url'], True)
        db.session.add(courier)