from app import db
from app.model.meta.schema import UserPresence
from sqlalchemy import func
import json
rs = db.session.query(UserPresence.status, func.ST_AsGeoJSON(UserPresence.location)).all()
for r in rs:
    print r[0], json.loads(r[1])[u'coordinates']

