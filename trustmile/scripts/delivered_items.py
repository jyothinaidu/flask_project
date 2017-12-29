
from app.deliveries.model import Consignment, TrackingInfo, DeliveryFeedback

rs = Consignment.query.all()

delivered_consignments = []
delivered_with_feedback = []
for r in rs:
    tis = TrackingInfo.items_from_tracking_dict(r.tracking_info)

    for t in tis:
        if t.tag == u'Delivered':
            delivered_consignments.append(r)

            df = DeliveryFeedback.query.filter(DeliveryFeedback.delivery_id == r.id).first()
            if df:
                delivered_with_feedback.append(r)

print 'Delivered items count {0}'.format(len(delivered_consignments))
print 'Delivered items with feedback count {0}'.format(len(delivered_with_feedback))

