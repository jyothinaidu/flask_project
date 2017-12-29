import config
import aftership

api = aftership.APIv4(config.AFTERSHIP_API_KEY, datetime_convert=False)
i = 1
trackings = api.trackings.get(page=i)['trackings']
expired_trackings = []

while len(trackings) > 0:
    for t in trackings:
        if not t.get(u'active'):
            expired_trackings.append((t.get(u'tracking_number'), t.get(u'slug')))
    i += 1
    trackings = api.trackings.get(page=i)['trackings']

for et in expired_trackings:
    api.trackings.post(et[1], et[0], u'retrack')
