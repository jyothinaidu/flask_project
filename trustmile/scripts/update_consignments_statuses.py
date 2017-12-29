from app.deliveries.model import Consignment
from app import db
cons = Consignment.query.all()

for c in cons:
    delivery_info = c.tracking_info
    if delivery_info:
        c.set_latest_status(delivery_info)

        c.set_is_delivered(delivery_info)
        print 'Did consignment {0}'.format(c.id)
        db.session.add(c)

db.session.commit()