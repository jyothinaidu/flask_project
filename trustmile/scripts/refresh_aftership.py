__author__ = 'aaron'

from app.async import tasks

tasks.async_update_all_trackings.delay()
a